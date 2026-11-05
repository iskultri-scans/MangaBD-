#!/usr/bin/env python3
"""Real-corpus estimator sweep: verbatim _estimate_region_angle over the
repo's archived pages (REAL detector boxes, REAL manga art).

For each archived (original.jpg, detections.json): run the estimator per
region bbox, count non-zero angles + quad presence, and for any firing
region measure the render-side quad-fit dims vs bbox.
"""
import json
import sys
import pathlib
import numpy as np
import cv2

HERE = pathlib.Path("/home/z/my-project/m009b2_repro")
sys.path.insert(0, str(HERE / "scripts"))
from b2_env import build_env  # noqa: E402

ns = build_env("tip", HERE / "sweep_env.log")
est = ns["_estimate_region_angle"]

CORPUS = [
    HERE / "real_corpus" / "S007",
    *([p for p in pathlib.Path("/home/z/my-project/repo/samples").iterdir()
       if p.is_dir()]),
]

grand = {"pages": 0, "regions": 0, "fired": 0}
details = []
for d in CORPUS:
    orig = d / "original.jpg"
    det = d / "detections.json"
    if not orig.exists() or not det.exists():
        continue
    img = cv2.imread(str(orig))
    regs = json.loads(det.read_text(encoding="utf-8"))
    page_name = d.name
    grand["pages"] += 1
    for r in regs:
        x, y = int(r["x"]), int(r["y"])
        w, h = int(r["width"]), int(r["height"])
        grand["regions"] += 1
        try:
            a, q = est(img, x, y, w, h)
        except Exception as exc:
            details.append({"page": page_name, "id": r.get("id"),
                            "EXC": repr(exc)[:120]})
            continue
        if a != 0.0:
            grand["fired"] += 1
            entry = {
                "page": page_name, "id": r.get("id"),
                "type": r.get("region_type"), "bbox": [x, y, w, h],
                "angle": a, "quad": "Y" if q is not None else "N",
            }
            if q is not None:
                qq = np.asarray(q, dtype=np.float64)
                fw = max(np.linalg.norm(qq[0] - qq[1]),
                         np.linalg.norm(qq[2] - qq[3]))
                fh = max(np.linalg.norm(qq[0] - qq[3]),
                         np.linalg.norm(qq[1] - qq[2]))
                entry["fit_dims"] = [round(fw, 1), round(fh, 1)]
                entry["fit_vs_bbox"] = [round(fw / max(w, 1), 2),
                                        round(fh / max(h, 1), 2)]
            details.append(entry)

print(json.dumps(grand, indent=2))
print(json.dumps(details, indent=2, ensure_ascii=False))
(HERE / "real_corpus_sweep.json").write_text(json.dumps(
    {"grand": grand, "details": details}, indent=2, ensure_ascii=False))
