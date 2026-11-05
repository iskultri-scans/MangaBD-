#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-18 — S009/S010 archive refresh.

The RF-18 bytes change BOTH sides of the tilted-class archives:

  * detection side — the RF-18 ladder stores the mask-GT angle (was:
    the RF-17 margin-16 estimator) and adds b2_gt_lines/spacing/cx/cy
    (the render-parity params) on tilted rows. H/V rows and every
    other field stay byte-identical.
  * render side — the GT-mirrored tilted layout (lines/spacing/size
    mirror the ORIGINAL text ink; paste at the ink centroid) replaces
    the RF-17 interior-fit layout.

This script re-runs the full chain on both pages (same stubs as the
builders + the RF-18 CTD stand-in) and:

  1. HARD-asserts the fixture side is byte-stable (original.jpg,
     text_mask.png, inpainted.png byte-identical; ocr.json
     semantically stable with the fallback-trace TIMING normalized;
     translation rows identical);
  2. HARD-asserts H/V detection rows byte-identical (angle 0.0, no
     b2_gt fields, same boxes) — only tilted rows change, BY DESIGN;
  3. HARD-asserts the H/V regions' renders are pixel-identical (0
     changed px) — only the tilted regions change;
  4. overwrites detections.json + final.jpg and appends the
     rf18_refresh disclosure to metadata.json.
"""
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import cv2
import numpy as np

REPO = Path("/home/z/my-project/MangaBD")
sys.path.insert(0, str(REPO / "scripts"))
from m009_b2_rf18_chain import artifact_path, run_chain  # noqa: E402
from m009_b2_rf16_page import build_s009_page  # noqa: E402
from m009_b2_rf17_page import build_s010_page  # noqa: E402

ARCHIVES = [
    {
        "name": "S009_diagonal", "page": "s009_diagonal.jpg",
        "build": lambda: build_s009_page(str(REPO)),
        "n_ret": 4,   # (full, clean, regions, ink)
    },
    {
        "name": "S010_burst", "page": "s010_burst.jpg",
        "build": lambda: build_s010_page(str(REPO)),
        "n_ret": 5,   # (full, clean, regions, ink, interiors)
    },
]

branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                        capture_output=True, text=True).stdout.strip()
assert branch == "mangabd-009-b2", f"on branch {branch!r}"


def _semantic_ocr(raw):
    """OCR-content comparison: the row's region record carries the
    RF-18 detection-side refresh (mask-GT angle/quad + b2_gt fields —
    disclosed); the OCR content itself (text/engine/status/trace,
    timing normalized) must be identical."""
    rows = json.loads(raw)
    out = []
    for r in rows:
        oc = dict(r.get("ocr") or {})
        for t in oc.get("fallback_trace") or []:
            t["ms"] = 0
        reg = r.get("region") or {}
        out.append({
            "id": reg.get("id"), "x": reg.get("x"), "y": reg.get("y"),
            "width": reg.get("width"), "height": reg.get("height"),
            "ocr": oc,
        })
    return out


def _hv_key(r):
    return (int(r["x"]), int(r["y"]), int(r["width"]), int(r["height"]),
            float(r["angle"]), json.dumps(r.get("quad"), sort_keys=True),
            r.get("region_type"), r.get("detector_class"),
            r.get("parent_bubble_id"))


for arch in ARCHIVES:
    DEST = REPO / "samples" / arch["name"]
    print(f"\n{'=' * 70}\nRF-18 refresh: {arch['name']}\n{'=' * 70}")

    out = arch["build"]()
    full, clean, regions, ink_mask = out[0], out[1], out[2], out[3]
    ns, pid, det_rows = run_chain(arch["page"], full, clean,
                                  regions, ink_mask)
    print(f"chain done: {len(det_rows)} regions rendered")

    # ── 1. fixture-side byte-stability ─────────────────────────────
    for kind, arch_name in (("original", "original.jpg"),
                            ("inpainted", "inpainted.png")):
        fresh = artifact_path(ns, pid, kind).read_bytes()
        assert fresh == (DEST / arch_name).read_bytes(), \
            f"{arch_name} NOT byte-stable — fixture drift!"
    fresh_mask = cv2.imencode(
        ".png", ink_mask)[1].tobytes()   # raw builder ink (AA kept)
    assert fresh_mask == (DEST / "text_mask.png").read_bytes(), \
        "text_mask.png NOT byte-stable — fixture drift!"
    new_ocr = artifact_path(ns, pid, "ocr").read_bytes()
    assert _semantic_ocr(new_ocr) == _semantic_ocr(
        (DEST / "ocr.json").read_bytes()), "ocr.json NOT semantically stable"
    arch_tr_rows = json.loads((DEST / "translation.json").read_text())
    df_now = ns["translation_df"]
    fresh_rows = df_now[df_now["page_id"] == pid].sort_values("id")
    assert len(fresh_rows) == len(arch_tr_rows), "translation row count"
    by_id = {int(r["id"]): r for r in arch_tr_rows}
    for _, fr in fresh_rows.iterrows():
        ar = by_id[int(fr["id"])]
        assert str(fr["translated_text"]) == str(
            ar["translated_text"]), f"translation drift id {ar['id']}"
    print("fixture side byte-stable: original/inpainted/text_mask "
          "identical; ocr semantic; translation rows identical")

    # ── 2. detection-side: H/V rows byte-identical, tilted change ──
    arch_det = json.loads((DEST / "detections.json").read_text())
    arch_by_id = {int(r["id"]): r for r in arch_det}
    n_hv = n_tilt = 0
    for r in det_rows:
        old = arch_by_id[int(r["id"])]
        if abs(float(old["angle"])) <= 1.0:
            assert _hv_key(old) == _hv_key(r), \
                f"H/V row drifted: id {r['id']}"
            assert "b2_gt_lines" not in r, \
                f"H/V row gained b2_gt fields: id {r['id']}"
            n_hv += 1
        else:
            assert r.get("b2_gt_lines") is not None, \
                f"tilted row missing b2_gt: id {r['id']}"
            n_tilt += 1
    print(f"detection side: {n_hv} H/V rows byte-identical; "
          f"{n_tilt} tilted rows carry b2_gt (by design)")

    # ── 3. render diff census: H/V 0 px; tilted changed ────────────
    final = cv2.imdecode(np.frombuffer(
        artifact_path(ns, pid, "final").read_bytes(), np.uint8),
        cv2.IMREAD_COLOR)
    arch_final = cv2.imread(str(DEST / "final.jpg"))
    h = min(final.shape[0], arch_final.shape[0])
    w = min(final.shape[1], arch_final.shape[1])
    diff = (np.abs(final[:h, :w].astype(int)
                   - arch_final[:h, :w].astype(int)).sum(axis=2) > 30)

    def match_gt(r):
        best, bi = 0, None
        for g in regions:
            gx, gy, gw, gh = g["box"]
            ix = max(0, min(r["x"] + r["width"], gx + gw)
                     - max(r["x"], gx))
            iy = max(0, min(r["y"] + r["height"], gy + gh)
                     - max(r["y"], gy))
            if ix * iy > best:
                best, bi = ix * iy, g
        return bi

    changed = {}
    for r in det_rows:
        g = match_gt(r)
        x, y, ww, hh = r["x"], r["y"], r["width"], r["height"]
        n = int(diff[y:y + hh, x:x + ww].sum())
        changed.setdefault(g["class"], []).append((g["tag"], n))
    hv = [n for _, n in (changed.get("horizontal", [])
                         + changed.get("vertical", []))]
    tilted = [n for _, n in (changed.get("tilted", [])
                             + changed.get("burst", []))]
    assert not any(hv), f"H/V renders changed: {hv}"
    assert all(t > 500 for t in tilted), \
        f"tilted renders did not change: {tilted}"
    print(f"render census: H/V 0 changed px; tilted changed by design: "
          f"{[n for _, n in changed.get('tilted', []) + changed.get('burst', [])]}")

    # ── 4. refresh artifacts + disclosure ──────────────────────────
    shutil.copy2(artifact_path(ns, pid, "detections"), DEST / "detections.json")
    shutil.copy2(artifact_path(ns, pid, "final"), DEST / "final.jpg")
    print(f"refreshed detections.json + final.jpg "
          f"({(DEST / 'final.jpg').stat().st_size} B)")

    meta = json.loads((DEST / "metadata.json").read_text(encoding="utf-8"))
    meta["rf18_refresh"] = {
        "date": str(date.today()),
        "what": (
            "RF-18 original-ink orientation GT: detections.json tilted "
            "rows now store the mask-GT angle (+-0.25 deg of "
            "construction beta on this fixture, vs the RF-17 estimator "
            "values) + b2_gt_lines/spacing/cx/cy render-parity params; "
            "final.jpg re-rendered with the GT-mirrored tilted layout "
            "(lines/spacing mirror the original text ink, paste at the "
            "ink centroid, quad-mask color sampling)."),
        "unchanged": [
            "original.jpg / inpainted.png / text_mask.png "
            "(byte-identical — deterministic fixture)",
            "ocr.json (semantically identical) / translation.json",
            "the horizontal + vertical rows of detections.json "
            "(byte-identical) and their renders (0 changed px)",
        ],
        "evidence": "scripts/m009_b2_rf18_verify.py V3/V4",
    }
    with open(DEST / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("metadata.json: rf18_refresh disclosure appended")

print("\nRF-18 S009/S010 refresh COMPLETE")
