#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-16 — repro harness: tilt estimator must see text ink only.

Modes:
  post  : estimator span from the BASE bytes (dc612d5, the LIVE-REJECT
          notebook) on the S009 page — must reproduce the Owner symptom:
          tilted bubbles measure a DILUTED tilt (ring + background + art
          pull the PCA toward axis-aligned), the 5 deg snap zeroes them,
          fewer than 6 of 7 tilted regions inherit.
  fix   : estimator span from the WORKING notebook bytes (post RF-16
          patch) on the SAME page + SAME boxes — >= 6 of 7 tilted within
          +/-3 deg of ground truth, horizontals 0.0, vertical V-3.

The page + boxes + ground truth come from scripts/m009_b2_rf16_page.py
(Owner-class geometry: near-upright rings, tilted text, screentone+art
background leaking inside the axis-aligned boxes — the LIVE REJECT
signature on dc612d5: 7 tilted bubbles, 1/7 inherited, df angles 0.00).

Estimator invocation is the PRODUCTION call shape:
  _estimate_region_angle(image_bgr, x, y, w, h)  (cell-6 region build)
"""
import json
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "dc612d5"
PAGE_MOD_DIR = REPO / "scripts"
sys.path.insert(0, str(PAGE_MOD_DIR))
from m009_b2_rf16_page import build_s009_page, ground_truth_angles  # noqa: E402

TOL = 3.0          # Owner acceptance: |stored - GT| <= 3 deg
NEED = 6           # ... for >= 6 of the 7 tilted regions


def cells_at(ref):
    raw = subprocess.run(["git", "-C", str(REPO), "show",
                          f"{ref}:{NB_NAME}"],
                         capture_output=True, check=True).stdout
    nb = json.loads(raw.decode("utf-8"))
    return ["".join(c.get("source", [])) for c in nb["cells"]]


def work_cells():
    nb = json.loads(NB.read_text(encoding="utf-8"))
    return ["".join(c.get("source", [])) for c in nb["cells"]]


def estimator_span(cells):
    """Cell-6 section 9b (config knob + _estimate_region_angle)."""
    lines = cells[6].split("\n")
    si = next(i for i, l in enumerate(lines)
              if "9b. MANGABD-009 B2" in l)
    ei = next(i for i, l in enumerate(lines)
              if "10. Visualization" in l and i > si)
    return "\n".join(lines[si:ei])


def make_ns():
    ns = {"__name__": "rf16_repro"}
    exec("import cv2\nimport numpy as np", ns)
    ns["MANGABD_CONFIG"] = {"detection": {}}
    ev = []

    def log_event(message, level="INFO", **extra):
        ev.append({"level": level, "message": message})

    ns["log_event"] = log_event
    return ns


def raw_all_ink_tilt(image_bgr, x, y, w, h):
    """The DILUTION EVIDENCE arm: PCA over ALL dark region pixels —
    exactly what the base estimator sees pre-fix. Returns (tilt, aniso)
    or None if unmeasurable."""
    H, W = image_bgr.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    crop = image_bgr[y1:y2, x1:x2]
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    ink = (gray < 100).astype(np.uint8) * 255
    if int(ink.sum() // 255) < 30:
        _otsu, _ = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        ink = (gray < max(int(_otsu), 40)).astype(np.uint8) * 255
    ys, xs = np.nonzero(ink)
    if len(xs) < 100:
        return None
    if len(xs) > 60000:
        _sel = np.random.default_rng(42).choice(len(xs), 60000,
                                                replace=False)
        xs, ys = xs[_sel], ys[_sel]
    pts = np.stack([xs.astype(np.float64), ys.astype(np.float64)], 1)
    centered = pts - pts.mean(axis=0)
    cov = centered.T @ centered / len(pts)
    ev_, evec = np.linalg.eigh(cov)
    if ev_[1] <= 0:
        return None
    theta = float(np.degrees(np.arctan2(evec[1, 1], evec[0, 1])))
    tilt = (theta + 180.0) % 180.0
    if tilt > 90.0:
        tilt -= 180.0
    return tilt, float(ev_[0] / ev_[1])


def run(mode):
    cells = cells_at(BASE_REF) if mode == "post" else work_cells()
    tag = "BASE dc612d5" if mode == "post" else "WORK (RF-16 fix)"
    ns = make_ns()
    exec(compile(estimator_span(cells), f"<{mode}:c6 9b>", "exec"), ns)
    est = ns["_estimate_region_angle"]

    full, clean, regions, ink_mask = build_s009_page(str(REPO))
    gt = ground_truth_angles(regions)

    print(f"== RF-16 repro [{mode}] estimator = {tag} ==")
    tilted_ok = 0
    rows = []
    for r in regions:
        x, y, w, h = r["box"]
        ang, quad = est(full, x, y, w, h)
        dil = raw_all_ink_tilt(full, x, y, w, h)
        dil_s = (f"{dil[0]:+.2f}(aniso {dil[1]:.2f})"
                 if dil else "n/a")
        if r["class"] == "tilted":
            ok = abs(ang - r["beta"]) <= TOL and quad is not None
            tilted_ok += ok
            rows.append((r["tag"], r["beta"], ang, dil_s, ok))
        else:
            ok = ang == 0.0
            rows.append((r["tag"], r["beta"], ang, dil_s, ok))
        print(f"  {r['tag']} [{r['class']:>10s}] GT={r['beta']:+6.1f} "
              f"stored={ang:+6.2f} quad={'Y' if quad else 'N'} "
              f"rawAllInkTilt={dil_s} {'OK' if ok else 'BAD'}")

    print(f"\ntilted within +-{TOL} deg of GT: {tilted_ok}/7 "
          f"(Owner gate: >= {NEED}/7)")

    # dilution evidence: on BASE, the raw all-ink tilt of truly tilted
    # regions collapses toward axis (|raw| < |GT| by a large factor)
    if mode == "post":
        dil_ok = all(abs(float(rows[i][3].split("(")[0])) <
                     abs(rows[i][1]) * 0.6
                     for i in range(7) if rows[i][3] != "n/a")
        verdict = (tilted_ok < NEED)
        print(f"raw all-ink tilt diluted to <60% of GT on all tilted: "
              f"{'YES' if dil_ok else 'NO'}")
        print(f"VERDICT {mode}: "
              + ("RF-16 LIVE REJECT SYMPTOM REPRODUCED "
                 f"({tilted_ok}/7 inherited < {NEED}; ring+background "
                 "dilution -> 5 deg snap -> 0.00)"
                 if verdict else "UNEXPECTED-PASS"))
        return 0 if verdict else 1
    else:
        h_ok = all(rows[i][2] == 0.0 for i in (7, 8))
        v_row = rows[9]
        print(f"horizontals stay 0: {'YES' if h_ok else 'NO'}; "
              f"vertical V1 stored={v_row[2]:+.2f} "
              f"(V-3 class, must be 0.0)")
        verdict = tilted_ok >= NEED and h_ok and v_row[2] == 0.0
        print(f"VERDICT {mode}: "
              + (f"RF-16 FIXED ({tilted_ok}/7 within +-{TOL} deg, "
                 "horizontals 0, vertical 0/V-3)"
                 if verdict else "STILL FAILING"))
        return 0 if verdict else 1


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "post"
    sys.exit(run(mode))
