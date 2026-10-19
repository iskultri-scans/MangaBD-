#!/usr/bin/env python3
"""MANGABD-006 Phase A Extension / RF-5 -- baberu runner.

Engine: genshiai-daichi/baberu-ocr v1.1 (115M DINOv2 vision + 6-layer GQA
char-level decoder, 14,630-symbol vocab; ONNX build 243 MB =
vision_fp16.onnx 173 MB + decoder_prefill_int8.onnx 35 MB +
decoder_step_int8.onnx 35 MB; Apache-2.0).

Measured as-shipped: the inference class below is the model repo's
self-contained onnx_infer.py (onnxruntime + numpy + pillow only, greedy
decode + repetition_penalty 1.2 + run caps 12/16, max_new_tokens 256)
embedded VERBATIM -- see the "shipped code" marker. The harness around it
follows the Phase A / A.1.0 conventions:

  - crops + GT derived from repository bytes: samples/S003_batch2
    original.jpg + detections.json boxes + translation.json original_text
    (byte-verified against the archived m006_bench/crops when present);
  - R1 (vertical mixed EN+kana) runs the V-3 ladder variants
    upright + rot90cw (the 224x224 whole-crop input squashes the tall
    note; rot90cw is the measured-best variant); best-variant selection
    happens in scripts/m006_phaseA_ext_metrics.py;
  - output: m006_bench/results/baberu_results.json (Phase A per-engine
    JSON schema + provenance block).

Provenance: original 2026-10-18 run outputs were lost to the sandbox
recycle (Flash ext-review P0). This script re-measures deterministically
on CPU (onnxruntime) against sha-pinned re-downloaded weights; see the
provenance block in the result JSON and the RF-5 record in
agents/GLM_5_3.md.

Usage:  python3 scripts/m006_phaseA_ext_baberu.py [--out FILE]
Weights: env M006_EXT/baberu (default /home/z/my-project/m006_ext/baberu
if present, else huggingface_hub download).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import resource
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "samples" / "S003_batch2"
RESULTS = REPO / "m006_bench" / "results"
WORK_CROPS = Path("/home/z/my-project/m006_bench/crops")  # optional cross-check

ONNX_FILES = [
    "onnx/vision_fp16.onnx",
    "onnx/decoder_prefill_int8.onnx",
    "onnx/decoder_step_int8.onnx",
]
TOK_FILES = ["tokenizer/vocab.json", "tokenizer/tokenizer_config.json"]
INFER_REF = "onnx_infer.py"
REF_SHA = "fdf292a15dae9f5af37dd76bb408679dc4bcdfe4"  # genshiai-daichi/baberu-ocr revision (api-verified)


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_weights() -> Path:
    cand = Path(os.environ.get("M006_EXT", "/home/z/my-project/m006_ext")) / "baberu"
    need = ONNX_FILES + TOK_FILES
    if all((cand / f).exists() for f in need):
        return cand
    from huggingface_hub import hf_hub_download

    for fn in need:
        hf_hub_download("genshiai-daichi/baberu-ocr", fn, local_dir=cand)
    return cand


def load_regions():
    """Derive the 6 region crops (PIL) + GT from repository bytes."""
    det = json.loads((SAMPLE / "detections.json").read_text())
    tr = {
        t["id"]: t["original_text"]
        for t in json.loads((SAMPLE / "translation.json").read_text())
    }
    page = Image.open(SAMPLE / "original.jpg")
    regions = []
    for d in sorted(det, key=lambda r: r["id"]):
        x, y, w, h = d["x"], d["y"], d["width"], d["height"]
        crop = page.crop((x, y, x + w, y + h))
        regions.append(
            {"region_id": d["id"], "crop": crop, "gt": tr[d["id"]],
             "vertical": d["region_type"] == "overlay"}
        )
    return regions


def verify_against_archived_crops(regions):
    """Optional: byte-verify the derived crops against archived PNGs."""
    import io

    ok = []
    for r in regions:
        p = WORK_CROPS / f"R{r['region_id']}.png"
        if not p.exists():
            continue
        buf = io.BytesIO()
        r["crop"].save(buf, format="PNG")
        ok.append(buf.getvalue() == p.read_bytes())
    return ok


# ---------------------------------------------------------------------------
# shipped code: genshiai-daichi/baberu-ocr onnx_infer.py (Apache-2.0),
# embedded verbatim below -- only the argparse main() is omitted.
# ---------------------------------------------------------------------------
_PAST = [f"past_k{i}" for i in range(6)] + [f"past_v{i}" for i in range(6)]

_B_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
_B_STD = np.array([0.229, 0.224, 0.225], np.float32)


def _b_preprocess(image: Image.Image) -> np.ndarray:
    img = image.convert("RGB").resize((224, 224), Image.BICUBIC)
    x = (np.asarray(img, np.float32) / 255.0 - _B_MEAN) / _B_STD
    return x.transpose(2, 0, 1)[None]  # [1,3,224,224]


class _BaberuVocab:
    """Char-level vocab. ids 0..3 = <pad>/<bos>/<eos>/<unk>; id>=4 -> charset[id-4]."""

    def __init__(self, vocab_json: Path):
        import unicodedata

        charset = json.loads(Path(vocab_json).read_text(encoding="utf-8"))
        self.id2ch = {0: "", 1: "", 2: "", 3: ""}
        for i, ch in enumerate(charset):
            self.id2ch[i + 4] = ch
        self.bos, self.eos = 1, 2
        self.vocab_size = len(charset) + 4
        self.content_ids = {
            i + 4 for i, ch in enumerate(charset)
            if len(ch) == 1 and ch not in "ーｰ〜~" and unicodedata.category(ch)[0] in "LN"
        }

    def decode(self, ids) -> str:
        return "".join(self.id2ch.get(i, "") for i in ids if i >= 4)


class BaberuOnnxOCR:
    """Verbatim port of the shipped onnx_infer.BaberuOnnxOCR (as-shipped decode)."""

    def __init__(self, onnx_dir, tokenizer_dir, vision="vision_fp16.onnx"):
        d = Path(onnx_dir)
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        mk = lambda p: ort.InferenceSession(str(p), so, providers=["CPUExecutionProvider"])
        self.vis = mk(d / vision)
        self.pre = mk(d / "decoder_prefill_int8.onnx")
        self.stp = mk(d / "decoder_step_int8.onnx")
        self.vocab = _BaberuVocab(Path(tokenizer_dir) / "vocab.json")

    def __call__(self, image, max_new_tokens=256, repetition_penalty=1.2, max_content_run=12,
                 max_symbol_run=16):
        v = self.vocab
        vis = self.vis.run(["vision_embeds"], {"pixel_values": _b_preprocess(image)})[0]
        out = self.pre.run(None, {"vision_embeds": vis, "input_ids": np.array([[v.bos]], np.int64)})
        logits, present = out[0][0, -1].astype(np.float64), out[1:]
        seq, toks, pos = [v.bos], [], vis.shape[1] + 1
        for _ in range(max_new_tokens):
            if repetition_penalty != 1.0:
                for tid in set(seq):
                    s = logits[tid]
                    logits[tid] = s * repetition_penalty if s < 0 else s / repetition_penalty
            last = toks[-1] if toks else 0
            cap = max_content_run if last in v.content_ids else max_symbol_run if last > 3 else 0
            if cap:
                run = 0
                for t in reversed(toks):
                    if t == last:
                        run += 1
                    else:
                        break
                if run >= cap:
                    logits[last] = -np.inf
            nxt = int(np.argmax(logits))
            if nxt == v.eos:
                break
            toks.append(nxt)
            seq.append(nxt)
            if len(toks) >= max_new_tokens:
                break
            feed = {"input_ids": np.array([[nxt]], np.int64), "position_ids": np.array([[pos]], np.int64)}
            feed.update({nm: t for nm, t in zip(_PAST, present)})
            out = self.stp.run(None, feed)
            logits, present = out[0][0, -1].astype(np.float64), out[1:]
            pos += 1
        return v.decode(toks)
# --------------------------- end of shipped code ---------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(RESULTS / "baberu_results.json"))
    args = ap.parse_args()

    weights = resolve_weights()
    regions = load_regions()
    vok = verify_against_archived_crops(regions)

    t0 = time.perf_counter()
    ocr = BaberuOnnxOCR(weights / "onnx", weights / "tokenizer")
    cold_load_s = time.perf_counter() - t0

    rows = []
    for r in regions:
        variants = ["upright", "rot90cw"] if r["vertical"] else ["upright"]
        for v in variants:
            img = r["crop"]
            if v == "rot90cw":
                img = img.rotate(-90, expand=True)  # PIL: negative angle = clockwise
            t0 = time.perf_counter()
            text = ocr(img)
            s = time.perf_counter() - t0
            rows.append({"region_id": r["region_id"], "variant": v, "text": text, "s": round(s, 3)})
            print(f"R{r['region_id']} {v:8s} ({s:5.2f}s): {text[:80]!r}")

    out = {
        "engine": "baberu",
        "started": _dt.datetime.now().isoformat(timespec="seconds"),
        "regions": rows,
        "page": {
            "file": "samples/S003_batch2/original.jpg",
            "source_md5": "446b357560122e97a28f2709d057bc69",
            "crop_derivation": "detections.json [x,y,w,h] boxes; byte-verified vs archived m006_bench/crops"
            + (f" ({sum(vok)}/{len(vok)} identical)" if vok else ""),
        },
        "notes": [
            "shipped onnx_infer.py inference embedded verbatim (as-shipped decode: greedy + rep-penalty 1.2 + run caps 12/16, max_new_tokens 256)",
            "224x224 whole-crop input (do_center_crop=False) -- squashes the tall R1 note; R1 ladder variants upright+rot90cw",
            "best-variant selection in m006_phaseA_ext_metrics.py",
        ],
        "cold_load_s": round(cold_load_s, 3),
        "model": "genshiai-daichi/baberu-ocr v1.1 (onnx/vision_fp16.onnx + decoder_prefill/step_int8.onnx, 243 MB build, onnxruntime CPU)",
        "det_model": None,
        "line_boxes": False,
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "provenance": {
            "run": "RF-5 re-measurement 2026-10-19: original 2026-10-18 outputs lost to sandbox recycle "
            "(Flash ext-review P0, A8); deterministic ONNX CPU inference re-run",
            "weights_sha256": {f: sha256_of(weights / f) for f in ONNX_FILES},
            "tokenizer_sha256": {f: sha256_of(weights / f) for f in TOK_FILES},
            "hub_revision": REF_SHA,
            "shipped_runner": INFER_REF,
            "runtime": f"onnxruntime {ort.__version__} CPU, numpy {np.__version__}, pillow {Image.__version__}",
        },
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=1)
    print("\n->", args.out)


if __name__ == "__main__":
    main()
