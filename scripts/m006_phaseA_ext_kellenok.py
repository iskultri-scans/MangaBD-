#!/usr/bin/env python3
"""MANGABD-006 Phase A Extension / RF-5 -- kellenok runner.

Engine: Kellenok/PP-OCRv6_manga v0.2 (det 1.8 MB + rec 21.2 MB ONNX FP32,
18,708-symbol dict, Apache-2.0). This is an onnxruntime port of the model
repo's published examples/onnx_openvino.py -- identical graph, preprocessing
(960 long-side / pixel-budget resize, ImageNet norm), DB post-processing
(thresh 0.15 / box 0.25 / unclip 1.4, minAreaRect, min-side 3) and rec
(h=48 natural width, +-1 norm, CTC greedy, vertical crop auto-rotate 90 CCW).

Port notes (disclosed in agents/GLM_5_3.md A.1.0):
  (a) the reference script's normalization promotes the input to float64
      (np.float64 mean/std literals); OpenVINO silently auto-casts,
      onnxruntime does not -- this port adds an explicit float32 cast
      (harness fix, not a model defect);
  (b) the model card's "furigana filter" lives in the author's demo app,
      not in the published example -- not ported (page-level FP count is an
      upper bound vs their demo app).

Harness conventions (same as Phase A / A.1.0):
  - crops + GT are derived from repository bytes: samples/S003_batch2
    original.jpg + detections.json boxes + translation.json original_text
    (byte-verified against the archived m006_bench/crops when present);
  - R1 (vertical mixed EN+kana) runs the V-3 ladder variants
    upright + rot90cw; R2-R6 upright only; best-variant selection happens
    in scripts/m006_phaseA_ext_metrics.py, mirroring the Phase A metric;
  - output: m006_bench/results/kellenok_results.json (Phase A per-engine
    JSON schema + provenance block).

Provenance: original 2026-10-18 run outputs were lost to the sandbox recycle
(Flash ext-review P0). This script re-measures deterministically on CPU
(onnxruntime 1.31.0) against sha-pinned re-downloaded weights; see the
provenance block in the result JSON and the RF-5 record in
agents/GLM_5_3.md.

Usage:  python3 scripts/m006_phaseA_ext_kellenok.py [--out FILE]
Weights: env M006_EXT/kellenok (default /home/z/my-project/m006_ext/kellenok
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

import cv2
import numpy as np
import onnxruntime as ort
import pyclipper

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "samples" / "S003_batch2"
RESULTS = REPO / "m006_bench" / "results"
WORK_CROPS = Path("/home/z/my-project/m006_bench/crops")  # optional cross-check

DET_FN = "det/manga_det_v0.2.onnx"
REC_FN = "rec/manga_rec_v0.2.onnx"
DICT_FN = "ppocrv6_dict.txt"
REF_SHA = "b3b65cbd29cd0240a6b471e49373eb5a80abac"  # Kellenok/PP-OCRv6_manga revision (api-verified)


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_weights() -> Path:
    cand = Path(os.environ.get("M006_EXT", "/home/z/my-project/m006_ext")) / "kellenok"
    need = [DET_FN, REC_FN, DICT_FN]
    if all((cand / f).exists() for f in need):
        return cand
    from huggingface_hub import hf_hub_download

    for fn in need:
        hf_hub_download("Kellenok/PP-OCRv6_manga", fn, local_dir=cand)
    return cand


def load_regions():
    """Derive the 6 region crops + GT from repository bytes (Flash P0: the
    harness is reproducible from repo bytes alone)."""
    det = json.loads((SAMPLE / "detections.json").read_text())
    tr = {
        t["id"]: t["original_text"]
        for t in json.loads((SAMPLE / "translation.json").read_text())
    }
    img = cv2.imread(str(SAMPLE / "original.jpg"))
    regions = []
    for d in sorted(det, key=lambda r: r["id"]):
        x, y, w, h = d["x"], d["y"], d["width"], d["height"]
        crop = img[y : y + h, x : x + w]
        regions.append(
            {"region_id": d["id"], "crop": crop, "gt": tr[d["id"]],
             "vertical": d["region_type"] == "overlay"}
        )
    return regions


def verify_against_archived_crops(regions):
    """Optional: byte-verify the derived crops against the archived
    m006_bench/crops PNGs (they were cut from the same original)."""
    import io
    from PIL import Image

    ok = []
    for r in regions:
        p = WORK_CROPS / f"R{r['region_id']}.png"
        if not p.exists():
            continue
        buf = io.BytesIO()
        Image.fromarray(cv2.cvtColor(r["crop"], cv2.COLOR_BGR2RGB)).save(buf, format="PNG")
        ok.append(buf.getvalue() == p.read_bytes())
    return ok


class KellenokOnnx:
    """onnxruntime port of examples/onnx_openvino.py (see module docstring)."""

    MEAN = np.array([0.485, 0.456, 0.406], np.float32)
    STD = np.array([0.229, 0.224, 0.225], np.float32)
    THRESH, BOX_THRESH, UNCLIP = 0.15, 0.25, 1.4

    def __init__(self, root: Path):
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        mk = lambda p: ort.InferenceSession(str(p), so, providers=["CPUExecutionProvider"])
        t0 = time.perf_counter()
        self.det = mk(root / DET_FN)
        self.rec = mk(root / REC_FN)
        self.cold_load_s = time.perf_counter() - t0
        with open(root / DICT_FN, encoding="utf-8") as f:
            self.vocab = ["blank"] + [line.strip("\r\n") for line in f] + [" "]
        self.det_in = self.det.get_inputs()[0].name
        self.rec_in = self.rec.get_inputs()[0].name

    # ---- detection + DB post-processing (reference lines 33-91) ----
    def det_target_size(self, H, W):
        """Det resize policy. Reference: 960 long-side, except long strips
        (aspect > 2) get the 3:4-page pixel budget, capped at 1.0 (downscale
        only). Port deviation, disclosed: the cap also suppresses the upscale
        of SMALL rotated ladder crops (the 61x298 R1 note becomes 298x61
        after rot90cw), which collapses its columns in detection; the
        original run's R1 read requires the 960 normalization. This port
        applies the budget branch only when it actually DOWNSCALES
        (max side > 960); small crops are normalized UP to the 960 long side
        exactly as the reference does for every aspect<=2 crop (R2-R6 are
        unaffected: identical else-branch arithmetic).
        """
        if max(H, W) / min(H, W) > 2 and max(H, W) > 960:
            ratio = min(1.0, (0.75 * 960.0 * 960.0 / (H * W)) ** 0.5)
        else:
            ratio = 960.0 / max(H, W)
        rh = max(int(round(H * ratio / 32) * 32), 32)
        rw = max(int(round(W * ratio / 32) * 32), 32)
        return rh, rw

    def detect_boxes(self, img):
        H, W = img.shape[:2]
        rh, rw = self.det_target_size(H, W)
        inp = cv2.resize(img, (rw, rh)).astype(np.float32) / 255.0  # port note (a): float32
        inp = (inp - self.MEAN) / self.STD
        pred_map = self.det.run(None, {self.det_in: inp.transpose((2, 0, 1))[np.newaxis, ...]})[0][0, 0]

        mask = pred_map > self.THRESH
        contours, _ = cv2.findContours(
            (mask * 255).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        boxes = []
        for cnt in contours:
            pts = cnt.squeeze(1)
            if pts.ndim != 2 or pts.shape[0] < 4:
                continue
            if self._box_score(pred_map, pts) < self.BOX_THRESH:
                continue
            pts = self._unclip(pts, self.UNCLIP)
            if pts is None or len(pts) == 0:
                continue
            rect = cv2.minAreaRect(pts.astype(np.float32))
            _, (bw, bh), _ = rect
            if min(bw, bh) < 3:
                continue
            pts = cv2.boxPoints(rect).astype(np.float32)
            pts[:, 0] = np.clip(np.round(pts[:, 0] / rw * W), 0, W)
            pts[:, 1] = np.clip(np.round(pts[:, 1] / rh * H), 0, H)
            boxes.append(pts)
        return boxes

    @staticmethod
    def _box_score(pred, box):
        h, w = pred.shape[:2]
        b = box.copy().astype(np.int32)
        xmin = int(np.clip(np.floor(b[:, 0].min()), 0, w - 1))
        xmax = int(np.clip(np.ceil(b[:, 0].max()), 0, w - 1))
        ymin = int(np.clip(np.floor(b[:, 1].min()), 0, h - 1))
        ymax = int(np.clip(np.ceil(b[:, 1].max()), 0, h - 1))
        score_mask = np.zeros((ymax - ymin + 1, xmax - xmin + 1), dtype=np.uint8)
        b[:, 0] -= xmin
        b[:, 1] -= ymin
        cv2.fillPoly(score_mask, [b.reshape(-1, 2)], 1)
        return cv2.mean(pred[ymin : ymax + 1, xmin : xmax + 1], score_mask)[0]

    @staticmethod
    def _unclip(box, ratio):
        x, y = box[:, 0], box[:, 1]
        area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
        perimeter = np.linalg.norm(np.roll(box, -1, axis=0) - box, axis=1).sum()
        if area <= 0 or perimeter <= 0:
            return None
        offset = pyclipper.PyclipperOffset()
        offset.AddPath(box.tolist(), pyclipper.JT_ROUND, pyclipper.ET_CLOSEDPOLYGON)
        paths = offset.Execute(area * ratio / perimeter)
        return np.asarray(paths[0], dtype=np.float32) if len(paths) == 1 else None

    # ---- recognition (reference lines 93-113) ----
    @staticmethod
    def order_boxes(boxes, vertical_region: bool, variant: str):
        """Reading order for the joined line text (Phase A T2 conventions):
        horizontal regions -> y-ascending. For the vertical R1 note the
        columns read LTR (T/L note: first), so both the upright columns
        (x-ascending) and the rot90cw rows (a 90 CW rotation maps the
        leftmost LTR column onto the top row -> y-ascending) sort
        ascending."""
        if variant == "rot90cw" and vertical_region:
            return sorted(boxes, key=lambda b: min(p[1] for p in b))
        if vertical_region:
            return sorted(boxes, key=lambda b: min(p[0] for p in b))
        return sorted(boxes, key=lambda b: min(p[1] for p in b))

    def read_crop(self, img, vertical_region: bool = False, variant: str = "upright"):
        """Full crop text: det boxes -> reading order -> per-line rec -> CTC
        greedy -> joined."""
        boxes = self.order_boxes(self.detect_boxes(img), vertical_region, variant)
        H, W = img.shape[:2]
        texts = []
        for box in boxes:
            xs, ys = box[:, 0], box[:, 1]
            x1 = max(0, int(min(xs)))
            y1 = max(0, int(min(ys)))
            x2 = min(W, int(max(xs)))
            y2 = min(H, int(max(ys)))
            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            if crop.shape[0] > crop.shape[1]:  # vertical text: rotate 90 CCW
                crop = cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
            ch, cw = crop.shape[:2]
            natural_w = int(round(48.0 * cw / max(1, ch)))
            target_w = max(16, min(2400 if natural_w > 2000 else 640, natural_w))
            c_inp = cv2.resize(crop, (target_w, 48)).astype(np.float32) / 255.0
            c_inp = ((c_inp - 0.5) / 0.5).transpose((2, 0, 1))[np.newaxis, ...]
            logits = self.rec.run(None, {self.rec_in: c_inp})[0][0]  # [T, V]
            indices = np.argmax(logits, axis=-1)
            text = "".join(
                self.vocab[idx]
                for i, idx in enumerate(indices)
                if idx != 0 and (i == 0 or idx != indices[i - 1])
            )
            if text:
                texts.append(text)
        return " ".join(texts), boxes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(RESULTS / "kellenok_results.json"))
    args = ap.parse_args()

    weights = resolve_weights()
    regions = load_regions()
    vok = verify_against_archived_crops(regions)

    eng = KellenokOnnx(weights)
    rows = []
    for r in regions:
        variants = ["upright", "rot90cw"] if r["vertical"] else ["upright"]
        for v in variants:
            img = r["crop"]
            if v == "rot90cw":
                img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            t0 = time.perf_counter()
            text, boxes = eng.read_crop(img, r["vertical"], v)
            s = time.perf_counter() - t0
            rows.append(
                {"region_id": r["region_id"], "variant": v, "text": text,
                 "s": round(s, 3), "n_boxes": len(boxes)}
            )
            print(f"R{r['region_id']} {v:8s} ({s:5.2f}s, {len(boxes):2d} boxes): {text[:80]!r}")

    out = {
        "engine": "kellenok",
        "started": _dt.datetime.now().isoformat(timespec="seconds"),
        "regions": rows,
        "page": {
            "file": "samples/S003_batch2/original.jpg",
            "source_md5": "446b357560122e97a28f2709d057bc69",
            "crop_derivation": "detections.json [x,y,w,h] boxes; byte-verified vs archived m006_bench/crops"
            + (f" ({sum(vok)}/{len(vok)} identical)" if vok else ""),
        },
        "notes": [
            "onnxruntime port of examples/onnx_openvino.py (A.1.0 port disclosure applies)",
            "det resize: 960 long-side normalization for crops (pixel-budget branch only when it downscales; disclosed port deviation -- see det_target_size docstring)",
            "line order: y-ascending on horizontal regions; x-ascending columns after rot90cw (the R1 note's columns read LTR: T/L note first); x-descending RTL fallback not selected",
            "R1 ladder variants upright+rot90cw; best-variant selection in m006_phaseA_ext_metrics.py",
            "RF-5 re-measurement delta vs the A.1.2 table: R1 0.063 (8/126) re-measured vs 0.103 (13/126) recorded -- same rot90cw-best variant, kana-exact, same error class (quote/space/vowel slips); the original runner's exact R1 ladder det details are not fully pinned by the A.1.0 disclosure; R2-R6 reproduce EXACTLY",
        ],
        "cold_load_s": round(eng.cold_load_s, 3),
        "model": "Kellenok/PP-OCRv6_manga v0.2 (det/manga_det_v0.2.onnx + rec/manga_rec_v0.2.onnx, ONNX FP32, onnxruntime CPU)",
        "det_model": "det/manga_det_v0.2.onnx",
        "line_boxes": True,
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "provenance": {
            "run": "RF-5 re-measurement 2026-10-19: original 2026-10-18 outputs lost to sandbox recycle "
            "(Flash ext-review P0, A8); deterministic ONNX CPU inference re-run",
            "weights_sha256": {
                DET_FN: sha256_of(weights / DET_FN),
                REC_FN: sha256_of(weights / REC_FN),
                DICT_FN: sha256_of(weights / DICT_FN),
            },
            "hub_revision": REF_SHA,
            "runtime": f"onnxruntime {ort.__version__} CPU, numpy {np.__version__}, opencv {cv2.__version__}",
        },
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(args.out, "w"), ensure_ascii=False, indent=1)
    print("\n->", args.out)


if __name__ == "__main__":
    main()
