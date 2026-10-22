#!/usr/bin/env python3
"""MANGABD-006 B1 — re-measure the VENDORED baberu int4 bundle on the S003 corpus.

The directive's vendored set is the author-swept smallest build
(vision_int4 + decoder int8, 121.3 MB) because vision_fp16 (172.9 MB)
exceeds GitHub's 100 MB hard push limit. The A.1.2-measured baberu rows
were produced with vision_fp16, so this script re-measures the int4 bundle
on the SAME corpus (samples/S003_batch2 crops + GT) with the SAME
methodology (committed runner class verbatim, committed metric functions
verbatim) to keep the provenance honest. Output:
scripts/m006_b1_baberu_int4_results.json + console CER table vs the
committed fp16 rows.
"""
import importlib.util
import json
import resource
import sys
import time
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
MODELS = REPO / "models" / "baberu"
OUT = Path("/home/z/my-project/scripts/m006_b1_baberu_int4_results.json")


def load_mod(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    runner = load_mod("baberu_runner", REPO / "scripts" / "m006_phaseA_ext_baberu.py")
    metrics = load_mod("ext_metrics", REPO / "scripts" / "m006_phaseA_ext_metrics.py")

    regions = runner.load_regions()
    t0 = time.perf_counter()
    ocr = runner.BaberuOnnxOCR(MODELS / "onnx", MODELS / "tokenizer",
                               vision="vision_int4.onnx")
    cold = time.perf_counter() - t0
    print(f"cold load (int4): {cold:.2f}s")

    rows = []
    for r in regions:
        variants = ["upright", "rot90cw"] if r["vertical"] else ["upright"]
        for v in variants:
            img = r["crop"]
            if v == "rot90cw":
                img = img.rotate(-90, expand=True)
            t0 = time.perf_counter()
            text = ocr(img)
            s = time.perf_counter() - t0
            rows.append({"region_id": r["region_id"], "variant": v,
                         "text": text, "s": round(s, 3)})
            print(f"R{r['region_id']} {v:8s} ({s:5.2f}s): {text[:80]!r}")

    detail = []
    scored = metrics.score_engine("baberu_int4", metrics.texts_from_regions(rows), detail)
    print("\nint4 bundle scored rows:")
    print(json.dumps(scored, indent=1, ensure_ascii=False))
    for d in detail:
        print(f"  R{d['region_id']} [{d['variant']}] cer={d['cer']} match={d['n2_match']}")

    # committed fp16 rows for comparison (RF-5 re-measurement, A.1.2 table)
    committed = json.loads((REPO / "m006_bench" / "results" / "metrics_ext.json").read_text())
    fp16_row = next(r for r in committed["rows"] if r.get("engine") == "baberu")
    print("\ncommitted fp16 bundle rows (A.1.2 / RF-5):")
    print(json.dumps(fp16_row, indent=1, ensure_ascii=False))

    out = {
        "engine": "baberu_int4_vendored",
        "purpose": "M6-B1 vendored-bundle provenance re-measurement (vision_int4 + decoder int8)",
        "regions": rows,
        "scored": scored,
        "detail": detail,
        "cold_load_s": round(cold, 3),
        "committed_fp16_scored": fp16_row,
        "weights": {
            "vision": "onnx/vision_int4.onnx (sha256 9526bcf99eb8de805df7ea2f66b385cfcbcb5dff0e99a5dcfb02bdb2d4182bde)",
            "decoders": "onnx/decoder_prefill_int8.onnx + onnx/decoder_step_int8.onnx (RF-5 pins 91de16d4... / f6164e9d...)",
            "hub_revision": "fdf292a15dae9f5af37dd76bb408679dc4bcdfe4",
        },
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print("\n->", OUT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
