#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-18 — S011 regression archive builder.

Commits the MANHWA-UI page class permanently into the corpus (RF-18
directive: "S011_manhwa_ui 新归档" — the Korean-manhwa / game-system-
window class the Owner's product ruling named). Like S009/S010, the
Owner's live page bytes are not in the repo, so S011 is a SYNTHESIZED
owner-signature page (disclosed in metadata.json):

  * 5 light SYSTEM-WINDOW panels (rounded-rect double border) with
    beta-tilted text — U3 sits in a heavy-art hatch cluster with a
    paper-white halo (the bbox-mean color surface), U5 is the
    ASYMMETRIC two-line block (the measurement-surface verdict
    class);
  * U6 = DARK system window with WHITE text (the D2 color surface);
  * 2 horizontal ellipses + 1 V-3 vertical note — stability controls.

Archive contents (samples/S011_manhwa_ui/): original.jpg /
inpainted.png / text_mask.png / detections.json / ocr.json /
translation.json / final.jpg / metadata.json — same shape as
S009/S010 (production-schema rows from the REAL detect/OCR/render
path on the RF-18 bytes; the sandbox has no onnxruntime so RT-DETR
is stubbed to the true boxes and CTD to the true text-ink prob map —
disclosed).
"""
import hashlib
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
from m009_b2_rf18_page import build_s011_page  # noqa: E402

DEST = REPO / "samples" / "S011_manhwa_ui"
TOL = 2.0

# ── 0. preconditions ────────────────────────────────────────────────
branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                        capture_output=True, text=True).stdout.strip()
assert branch == "mangabd-009-b2", f"on branch {branch!r}"
nb_sha = subprocess.run(
    ["git", "-C", str(REPO), "hash-object",
     str(REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt")],
    capture_output=True, text=True, check=True).stdout.strip()
nb_sha256 = hashlib.sha256(
    (REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt").read_bytes()).hexdigest()
print(f"notebook blob: {nb_sha[:12]}... sha256 {nb_sha256[:16]}...")
assert not DEST.exists(), f"{DEST} already exists"

full, clean, regions, ink_mask, interiors = build_s011_page(str(REPO))
print(f"page drawn: {full.shape[1]}x{full.shape[0]}, "
      f"{len(regions)} regions, ink {int((ink_mask > 0).sum())} px")

# ── 1. run the full chain on the RF-18 bytes ────────────────────────
ns, pid, det_rows = run_chain("s011_manhwa_ui.jpg", full, clean,
                              regions, ink_mask)
print(f"chain done: {len(det_rows)} regions rendered")

gt_by_id = {}
for r in det_rows:
    best, bt = 0, None
    for g in regions:
        gx, gy, gw, gh = g["box"]
        ix = max(0, min(r["x"] + r["width"], gx + gw) - max(r["x"], gx))
        iy = max(0, min(r["y"] + r["height"], gy + gh) - max(r["y"], gy))
        if ix * iy > best:
            best, bt = ix * iy, g
    gt_by_id[int(r["id"])] = bt

# ── 2. collect the session artifacts ────────────────────────────────
DEST.mkdir(parents=True)
for kind in ("original", "detections", "ocr", "inpainted", "final"):
    src = artifact_path(ns, pid, kind)
    assert src.exists(), f"artifact {kind} missing: {src}"
    shutil.copy2(src, DEST / src.name)
    print(f"  archived {src.name} ({src.stat().st_size} B)")
cv2.imwrite(str(DEST / "text_mask.png"), ink_mask)
print(f"  archived text_mask.png (TRUE ink, "
      f"{int((ink_mask > 0).sum())} px)")

trans_rows = []
for r in det_rows:
    g = gt_by_id[int(r["id"])]
    trans_rows.append({
        "id": int(r["id"]), "region_type": r["region_type"],
        "original_text": g["jp"],
        "translated_text": g["bengali"],
        "translator_engine": "synthetic (RF-18 fixture)",
        "bengali_valid": True, "status": "rendered",
    })
with open(DEST / "translation.json", "w", encoding="utf-8") as f:
    json.dump(trans_rows, f, ensure_ascii=False, indent=1)
print(f"  archived translation.json ({len(trans_rows)} rows)")

# ── 3. ground-truth table + per-region acceptance ───────────────────
gt_table = []
for r in det_rows:
    g = gt_by_id[int(r["id"])]
    exts = g.get("line_extents") or []
    sym = bool(exts) and (max(exts) / max(1, min(exts)) < 1.5)
    entry = {
        "id": int(r["id"]), "tag": g["tag"], "class": g["class"],
        "box": {"x": r["x"], "y": r["y"], "width": r["width"],
                "height": r["height"]},
        "ground_truth_beta_deg": g["beta"],
        "stored_angle_deg": float(r["angle"]),
        "stored_quad": r.get("quad"),
        "b2_gt_lines": r.get("b2_gt_lines"),
        "b2_gt_spacing": r.get("b2_gt_spacing"),
        "gt_lines": int(g["lines"]),
        "line_extents_px": exts,
        "symmetric": sym,
        "true_text_ink_px": int((ink_mask[
            r["y"]:r["y"] + r["height"],
            r["x"]:r["x"] + r["width"]] > 0).sum()),
    }
    if g["class"] in ("ui", "ui_dark"):
        entry["acceptance"] = (
            f"|stored - beta| <= {TOL} (RF-18 mask-GT law); "
            f"lines |post - GT| <= 1; rendered-ink re-measure <= {TOL} "
            "on symmetric blocks (asymmetric blocks REPORT-ONLY — "
            "measurement-surface verdict, RF-18 disclosure)")
        entry["pass"] = bool(abs(r["angle"] - g["beta"]) <= TOL)
    elif g["class"] == "horizontal":
        entry["acceptance"] = "stored == 0.0"
        entry["pass"] = bool(r["angle"] == 0.0)
    else:
        entry["acceptance"] = "stored == 0.0 (V-3 vertical class by shape)"
        entry["pass"] = bool(r["angle"] == 0.0)
    gt_table.append(entry)
    print(f"  GT {g['tag']}: beta={g['beta']:+.1f} "
          f"stored={r['angle']:+.2f} gt_lines={g['lines']} "
          f"b2_gt={r.get('b2_gt_lines')} pass={entry['pass']}")

tilted_pass = sum(1 for e in gt_table
                  if e["class"] in ("ui", "ui_dark") and e["pass"])
assert tilted_pass == 6, f"only {tilted_pass}/6 UI panels pass"

metadata = {
    "sample_id": "S011_manhwa_ui",
    "captured_at": str(date.today()),
    "branch": "mangabd-009-b2",
    "notebook_blob_sha": nb_sha,
    "notebook_sha256": nb_sha256,
    "pipeline_variant": (
        "MANGABD-009 B2 RF-18 regression fixture — synthesized "
        "manhwa-UI page (game-system windows + dark panel + heavy "
        "art), full chain (detect -> ocr -> inpaint -> translate -> "
        "render) on the RF-18 bytes"),
    "translation_engine": "synthetic (RF-18 fixture)",
    "source_page": (
        "synthesized by scripts/m009_b2_rf18_page.py "
        "(rng_seed 20261104) — NOT an Owner Colab upload"),
    "provenance": (
        "RF-18 directive: archive the manhwa-UI class (tilted system-"
        "window text, dark UI panel, art-crowded light panel). Ground "
        "truth = construction beta (PIL rotate law, cell-10 Test 16) "
        "+ the builder's own true-ink mask (text_mask.png); the "
        "pipeline's mask-GT ladder must reproduce both."),
    "disclosures": [
        "SYNTHESIZED fixture (not Owner-produced art); its job is to "
        "pin the manhwa-UI orientation-parity class, not to imitate "
        "art.",
        "Sandbox has no onnxruntime/torch GPU: RT-DETR is stubbed to "
        "the TRUE region boxes and CTD to the TRUE text-ink prob map "
        "(detector stand-ins, RF-16/17 pattern + the RF-18 CTD "
        "extension); the region build, RF-18 ladder, quads, angles, "
        "reading-order sort and every render byte after the boxes are "
        "the REAL production path.",
        "OCR is stubbed to the drawn JP text; translations are the "
        "builder's Bengali strings; inpainted.png is the synthesized "
        "clean page (panels + art stay, text removed).",
        "text_mask.png is the TRUE synthesized text ink (the RF-18 "
        "orientation ground truth), not the pipeline detect-stage "
        "mask.",
        "U5 is deliberately ASYMMETRIC (short + long line): its "
        "rendered-ink re-measurement deviation is REPORT-ONLY "
        "(measurement-surface verdict) — see the RF-18 record.",
        "The Owner's live manhwa page remains the final visual gate "
        "for the B2 merge.",
    ],
    "acceptance_rule": (
        "RF-18 hard criteria on S011: stored angle within +/-2 deg of "
        "GT for all 6 UI panels (mask-GT law); lines |post - GT| <= 1; "
        "rendered-ink re-measure within +/-2 deg on SYMMETRIC blocks "
        "(asymmetric REPORT-ONLY); oriented-bbox IoU >= 0.6 or side "
        "parity <= 15%; zero rendered ink outside the panel interior; "
        "horizontals 0, vertical V-3; per-region parity table + "
        "overlay printed by scripts/m009_b2_rf18_verify.py V4/V5."),
    "ground_truth": gt_table,
}
with open(DEST / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=1)
print(f"  archived metadata.json ({tilted_pass}/6 UI panels pass)")

print(f"\nS011 archive -> {DEST}")
for p in sorted(DEST.iterdir()):
    print(f"  {p.name:18s} {p.stat().st_size:>9,d} B")
