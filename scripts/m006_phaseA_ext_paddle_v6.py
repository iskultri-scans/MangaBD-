#!/usr/bin/env python3
"""MANGABD-006 Phase A Extension / RF-5 -- PP-OCRv6 medium runner.

Engine: PaddlePaddle/PP-OCRv6_medium_det (15.5M, LCNetV4+RepLKFPN+DBHead)
+ PP-OCRv6_medium_rec (19M, LCNetV4+LightSVTR CTC+NRTR multi-head),
Apache-2.0, run via paddlepaddle 3.3.1 CPU + paddleocr 3.7.0 with the
models pinned by name (auto-downloaded to ~/.paddlex/official_models).

Two det policies are measured, one per process invocation (isolated
per-process runners, mirroring A.1.0):

  --policy default   paddleocr 3.7 defaults (max-type det limit: small
                     crops are never upscaled -- the R6 131x204 crop
                     returns EMPTY, CER 1.000, F11)
  --policy 960min    text_det_limit_type='min', text_det_limit_side_len=960
                     (the 960/min upscale sensitivity row)

Harness conventions (same as Phase A / A.1.0):
  - crops + GT derived from repository bytes: samples/S003_batch2
    original.jpg + detections.json boxes + translation.json original_text;
  - R1 (vertical mixed EN+kana) runs the V-3 ladder variants
    upright + rot90cw; best-variant selection happens in
    scripts/m006_phaseA_ext_metrics.py;
  - output merged into m006_bench/results/paddle_v6_results.json under
    "policies": {"default": ..., "960min": ...} (Phase A per-region row
    schema + provenance block).

M2 workarounds retained: use_doc_orientation_classify /
use_doc_unwarping / use_textline_orientation off, enable_mkldnn=False
(the oneDNN-PIR sandbox workaround), text extracted from the nested
result.json["res"]["rec_texts"].

Provenance: original 2026-10-18 run outputs were lost to the sandbox
recycle (Flash ext-review P0). This script re-measures on re-downloaded
official model files; see the provenance block in the result JSON and the
RF-5 record in agents/GLM_5_3.md.

Usage:
  python3 scripts/m006_phaseA_ext_paddle_v6.py --policy default
  python3 scripts/m006_phaseA_ext_paddle_v6.py --policy 960min
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import resource
import time
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[1]
SAMPLE = REPO / "samples" / "S003_batch2"
RESULTS = REPO / "m006_bench" / "results"
OUT = RESULTS / "paddle_v6_results.json"

DET_NAME = "PP-OCRv6_medium_det"
REC_NAME = "PP-OCRv6_medium_rec"
PADDLEX_CACHE = Path.home() / ".paddlex" / "official_models"


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_regions():
    det = json.loads((SAMPLE / "detections.json").read_text())
    tr = {t["id"]: t["original_text"]
          for t in json.loads((SAMPLE / "translation.json").read_text())}
    page = Image.open(SAMPLE / "original.jpg")
    regions = []
    for d in sorted(det, key=lambda r: r["id"]):
        x, y, w, h = d["x"], d["y"], d["width"], d["height"]
        regions.append({"region_id": d["id"], "crop": page.crop((x, y, x + w, y + h)),
                        "gt": tr[d["id"]], "vertical": d["region_type"] == "overlay"})
    return regions


def model_hashes() -> dict:
    out = {}
    for name in (DET_NAME, REC_NAME):
        d = PADDLEX_CACHE / name
        if d.exists():
            for f in sorted(d.rglob("*")):
                if f.is_file() and f.suffix in {".pdmodel", ".pdiparams", ".pdiparams.info", ".txt", ".json"}:
                    out[str(f.relative_to(d))] = sha256_of(f)
    return out


def build_ocr(policy: str):
    from paddleocr import PaddleOCR

    kwargs = dict(
        text_detection_model_name=DET_NAME,
        text_recognition_model_name=REC_NAME,
        lang="en",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
        enable_mkldnn=False,
    )
    if policy == "960min":
        kwargs["text_det_limit_type"] = "min"
        kwargs["text_det_limit_side_len"] = 960
    return PaddleOCR(**kwargs)


def run_policy(policy: str, regions):
    t0 = time.perf_counter()
    ocr = build_ocr(policy)
    cold_load_s = time.perf_counter() - t0

    rows = []
    det_params_seen = None
    for r in regions:
        variants = ["upright", "rot90cw"] if r["vertical"] else ["upright"]
        for v in variants:
            img = r["crop"]
            if v == "rot90cw":
                img = img.rotate(-90, expand=True)  # PIL: negative angle = clockwise
            arr = np.array(img.convert("RGB"))
            t0 = time.perf_counter()
            res = ocr.predict(arr)
            s = time.perf_counter() - t0
            inner = res[0].json.get("res", res[0].json)
            texts = inner.get("rec_texts") or []
            if det_params_seen is None:
                det_params_seen = inner.get("text_det_params")
            text = " ".join(t.strip() for t in texts if t and t.strip())
            rows.append({"region_id": r["region_id"], "policy": policy, "variant": v,
                         "text": text, "s": round(s, 3), "n_lines": len(texts)})
            print(f"R{r['region_id']} {policy:7s} {v:8s} ({s:5.2f}s, {len(texts):2d} lines): {text[:70]!r}")
    return rows, cold_load_s, det_params_seen


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--policy", choices=["default", "960min"], required=True)
    args = ap.parse_args()

    regions = load_regions()
    rows, cold_load_s, det_params = run_policy(args.policy, regions)

    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    data.setdefault("engine", "paddle_v6")
    data.setdefault("started", _dt.datetime.now().isoformat(timespec="seconds"))
    policies = data.setdefault("policies", {})
    policies[args.policy] = {
        "regions": rows,
        "cold_load_s": round(cold_load_s, 3),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "effective_text_det_params": det_params,
        "line_boxes": True,
    }
    data["model"] = (f"PaddlePaddle/{DET_NAME} + {REC_NAME} (paddlepaddle 3.3.1 CPU + "
                     "paddleocr 3.7.0, lang=en, mkldnn off)")
    data["det_model"] = DET_NAME
    data["notes"] = [
        "two det policies measured, one process each (isolated per-process runners, A.1.0): default (max-type limit; small crops never upscaled) and 960min (min-type 960 upscale sensitivity row)",
        "M2 workarounds retained: doc-orientation/unwarping/textline-orientation off, enable_mkldnn=False, text from nested result json res.rec_texts",
        "R1 ladder variants upright+rot90cw; best-variant selection in m006_phaseA_ext_metrics.py",
        "empty det result -> empty text (R6 default-policy CER 1.000, F11)",
    ]
    data["page"] = {
        "file": "samples/S003_batch2/original.jpg",
        "source_md5": "446b357560122e97a28f2709d057bc69",
        "crop_derivation": "detections.json [x,y,w,h] boxes (same derivation as the kellenok/baberu runners)",
    }
    data["provenance"] = {
        "run": "RF-5 re-measurement 2026-10-19: original 2026-10-18 outputs lost to sandbox recycle "
        "(Flash ext-review P0, A8); official model files re-downloaded by paddleocr 3.7 auto-download",
        "official_model_files_sha256": model_hashes(),
        "runtime": "paddlepaddle 3.3.1 CPU, paddleocr 3.7.0, paddlex 3.7.2",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("\n->", OUT, f"(policies present: {sorted(policies)})")


if __name__ == "__main__":
    main()
