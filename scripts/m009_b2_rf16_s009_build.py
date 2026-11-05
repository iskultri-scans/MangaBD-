#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-16 — S009 regression archive builder.

Commits the Owner's diagonal test-page CLASS permanently into the
corpus (RF-16 directive #2). The Owner's live page bytes are not in
the repo (Colab session), so S009 is a SYNTHESIZED Owner-signature
page (disclosed in metadata.json): 7 tilted dialogue bubbles (text
tilt ±8-25 deg) inside NEAR-UPRIGHT ellipse rings (±3 deg, 4px
stroke) over screentone+art background that leaks inside the
axis-aligned region boxes — the exact dilution surface of the
dc612d5 LIVE REJECT (7 tilted bubbles, 1/7 inherited, df angles
0.00) — plus 2 horizontal bubbles and 1 vertical V-3 note.

Archive contents (samples/S009_diagonal/):
  original.jpg   — the page as drawn (rings + JP text + background)
  inpainted.png  — clean page (text inpainted away, rings stay)
  text_mask.png  — TRUE text-ink mask (the ideal CTD surface)
  detections.json— production-schema rows from the REAL detect path
                   on the RF-16-fixed bytes (detector boxes = true
                   dark-ink bboxes; sandbox has no onnxruntime, so
                   RT-DETR is stubbed to the true boxes — disclosed)
  ocr.json       — the harness OCR stub rows (real artifact shape)
  translation.json — the applied Bengali translations
  final.jpg      — the RF-16-fixed full-chain render
  metadata.json  — provenance + per-region ground truth (construction
                   beta + hand-tool-style measurement on the archived
                   text_mask bytes) + acceptance rule + disclosures

Ground-truth law (hand-tool): a text strip drawn horizontal then
rotated with PIL .rotate(beta, expand=True) measures pil == beta
(cell-10 battery Test 16 law); cross-checked by PCA on the archived
text_ink mask per region (image-space, from the archive bytes).
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
from m009_b2_rf14_repro import (  # noqa: E402
    install_pathlib_shim, make_torch_stub, restore_pathlib,
    seed_cell00_side_effects,
)
from m009_b2_rf15_repro import exec_cells  # noqa: E402
from m009_b2_rf16_page import build_s009_page  # noqa: E402

WORK = Path("/home/z/my-project/cells_rf16_work")
DEST = REPO / "samples" / "S009_diagonal"
TOL = 3.0

# ── 0. preconditions ────────────────────────────────────────────────
branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                        capture_output=True, text=True).stdout.strip()
assert branch == "mangabd-009-b2", f"on branch {branch!r}"
nb_sha = subprocess.run(
    ["git", "-C", str(REPO), "hash-object",
     str(REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt")],
    capture_output=True, text=True, check=True).stdout.strip()
print(f"notebook blob: {nb_sha[:12]}...")
assert not DEST.exists(), f"{DEST} already exists"

full, clean, regions, ink_mask = build_s009_page(str(REPO))

# ── 1. run the fixed pipeline on S009 (verbatim cells + stubs) ──────
sys.modules["torch"] = make_torch_stub()
install_pathlib_shim()
try:
    ns, logs, battery_failed = exec_cells(WORK, battery_must_fail=False)
finally:
    restore_pathlib()
assert battery_failed is None
assert "Cell 10 result: SUCCESS" in logs[10]

pid = ns["init_page"]("s009_diagonal.jpg", width=full.shape[1],
                      height=full.shape[0], image_np=full, overwrite=True)
boxes = [{"x": r["box"][0], "y": r["box"][1], "w": r["box"][2],
          "h": r["box"][3], "score": 0.9,
          "detector_class": "text_bubble" if r["class"] != "vertical"
          else "text_free"} for r in regions]
ns["rtdetr_detect"] = lambda img: {
    "text_bubble_boxes": [b for b in boxes
                          if b["detector_class"] == "text_bubble"],
    "text_free_boxes": [b for b in boxes
                        if b["detector_class"] == "text_free"],
    "bubble_boxes": [],
}
ns["detect_page"](pid, full, force=True)


def match_gt(r):
    best, bi = 0, None
    for g in regions:
        gx, gy, gw, gh = g["box"]
        ix = max(0, min(r["x"] + r["width"], gx + gw) - max(r["x"], gx))
        iy = max(0, min(r["y"] + r["height"], gy + gh) - max(r["y"], gy))
        if ix * iy > best:
            best, bi = ix * iy, g
    return bi


det_rows = ns["load_json_artifact"](pid, "detections", default=[])
print(f"detect rows: {len(det_rows)}")

ocr_stub = {}
for r in det_rows:
    g = match_gt(r)
    ocr_stub[(int(r["x"]), int(r["y"]))] = {
        "text": g["jp"].split("\n")[0], "confidence": 0.9,
        "engine": "stub", "language_score": {"en": 1.0, "bn": 0.0,
                                             "unknown": 0.0},
        "warnings": [], "is_english": True, "status": "ok",
        "vertical_ocr": None, "__bengali": g["bengali"],
    }
ns["run_ocr_engine"] = lambda name, img, region, page_id=None: (
    ocr_stub.get(tuple(int(region.get(k, 0)) for k in ("x", "y")),
                 {"text": "テスト", "confidence": 0.9, "engine": name,
                  "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
                  "warnings": [], "is_english": True, "status": "ok",
                  "vertical_ocr": None})
)
ns["ocr_page"](pid, full, force=True)
ns["save_image_artifact"](pid, "inpainted", clean, quality=95)
ns["mark_stage_done"](pid, "inpaint", meta={"inpaint_engine": "synthetic"})

df = ns["translation_df"]
for idx, row in df[df["page_id"] == pid].iterrows():
    key = (int(row["x"]), int(row["y"]))
    df.at[idx, "translated_text"] = ocr_stub.get(key, {}).get(
        "__bengali", "এই কী হয়েছে বলো তো!")
ns["save_translation_df"]()
ns["sync_translate_stage"]()
ns["run_render_all"](force=True, require_translation=True)

final = ns["load_image_artifact"](pid, "final")
df_now = ns["translation_df"]  # re-read: save_translation_df rebinds it
rendered = int((df_now[df_now["page_id"] == pid]["status"]
                == "rendered").sum())
print(f"rendered: {rendered}/{len(det_rows)}")
assert rendered == len(det_rows) == 10

# ── 2. collect the session artifacts ────────────────────────────────
DEST.mkdir(parents=True)
kinds = ("original", "detections", "ocr", "inpainted", "final")
for kind in kinds:
    src = Path(ns["get_artifact_path"](pid, kind))
    assert src.exists(), f"artifact {kind} missing: {src}"
    shutil.copy2(src, DEST / src.name)
    print(f"  archived {src.name} ({src.stat().st_size} B)")
# text_mask.png = the TRUE synthesized text ink (ground-truth surface,
# the ideal CTD input) — NOT the pipeline detect-stage box mask; the
# hand-tool measurement below reads exactly these bytes
cv2.imwrite(str(DEST / "text_mask.png"), ink_mask)
print(f"  archived text_mask.png (TRUE ink, "
      f"{int((ink_mask > 0).sum())} px)")

# translation.json (the applied translations, S00X archive shape)
gt_by_id = {}
for r in det_rows:
    g = match_gt(r)
    gt_by_id[int(r["id"])] = g
trans_rows = []
for r in det_rows:
    g = gt_by_id[int(r["id"])]
    trans_rows.append({
        "id": int(r["id"]), "region_type": r["region_type"],
        "original_text": g["jp"],
        "translated_text": g["bengali"],
        "translator_engine": "synthetic (RF-16 fixture)",
        "bengali_valid": True, "status": "rendered",
    })
with open(DEST / "translation.json", "w", encoding="utf-8") as f:
    json.dump(trans_rows, f, ensure_ascii=False, indent=1)
print(f"  archived translation.json ({len(trans_rows)} rows)")

# ── 3. ground truth (hand-tool: construction beta + archive-bytes PCA)
arch_ink = cv2.imread(str(DEST / "text_mask.png"), cv2.IMREAD_GRAYSCALE)
gt_table = []
for r in det_rows:
    g = gt_by_id[int(r["id"])]
    x, y, w, h = r["x"], r["y"], r["width"], r["height"]
    m = arch_ink[y:y + h, x:x + w] > 0
    n_ink = int(m.sum())
    ys, xs = np.nonzero(m)
    pil_meas = None
    if len(xs) >= 30:
        pts = np.stack([xs, ys], 1).astype(np.float64)
        pts -= pts.mean(0)
        cov = pts.T @ pts / len(pts)
        ev_, evec = np.linalg.eigh(cov)
        ang = np.degrees(np.arctan2(evec[1, 1], evec[0, 1]))
        tilt = (ang + 180) % 180
        if tilt > 90:
            tilt -= 180
        pil_meas = round(-(tilt - 90 * round(tilt / 90)), 2)
    entry = {
        "id": int(r["id"]), "tag": g["tag"], "class": g["class"],
        "box": {"x": x, "y": y, "width": w, "height": h},
        "ground_truth_beta_deg": g["beta"],
        "measured_ink_pil_deg": pil_meas,
        "stored_angle_deg": float(r["angle"]),
        "stored_quad": r.get("quad"),
        "true_text_ink_px": n_ink,
    }
    if g["class"] == "tilted":
        entry["acceptance"] = (
            f"|stored - beta| <= {TOL} (and quad present)")
        entry["pass"] = bool(abs(r["angle"] - g["beta"]) <= TOL
                             and r.get("quad") is not None)
    elif g["class"] == "horizontal":
        entry["acceptance"] = "stored == 0.0"
        entry["pass"] = bool(r["angle"] == 0.0)
    else:
        entry["acceptance"] = "stored == 0.0 (V-3 vertical class by shape)"
        entry["pass"] = bool(r["angle"] == 0.0)
    gt_table.append(entry)
    print(f"  GT {g['tag']}: beta={g['beta']:+.1f} meas={pil_meas} "
          f"stored={r['angle']:+.2f} pass={entry['pass']}")

tilted_pass = sum(1 for e in gt_table
                  if e["class"] == "tilted" and e["pass"])
assert tilted_pass >= 6, f"only {tilted_pass}/7 tilted pass"

metadata = {
    "sample_id": "S009_diagonal",
    "captured_at": str(date.today()),
    "branch": "mangabd-009-b2",
    "notebook_blob_sha": nb_sha,
    "notebook_sha256": __import__("hashlib").sha256(
        (REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt").read_bytes()
    ).hexdigest(),
    "pipeline_variant": (
        "MANGABD-009 B2 RF-16 regression fixture — synthesized "
        "Owner-class diagonal page, full chain (detect -> ocr -> "
        "inpaint -> translate -> render) on the RF-16-fixed bytes"),
    "translation_engine": "synthetic (RF-16 fixture)",
    "source_page": (
        "synthesized by scripts/m009_b2_rf16_page.py "
        "(rng_seed 20261031) — NOT an Owner Colab upload"),
    "provenance": (
        "RF-16 directive #2: commit the Owner's diagonal test page so "
        "the tilted-bubble class is permanently in the corpus. The "
        "Owner's live page bytes never left their Colab session, so "
        "this archive pins the CLASS: 7 tilted dialogue bubbles (text "
        "tilt beta in [-25, +20]) inside near-upright ellipse rings "
        "(tilt +/-3 deg, 4px stroke, aspect 1.2-1.5) over screentone + "
        "art strokes that leak inside the axis-aligned region boxes — "
        "the exact dilution surface of the dc612d5 LIVE REJECT (7 "
        "tilted bubbles, 1/7 inherited, df angles 0.00). Ground truth "
        "= construction beta (PIL rotate law, cell-10 Test 16) "
        "cross-checked per region by PCA on this archive's own "
        "text_mask.png bytes (measured_ink_pil_deg)."),
    "disclosures": [
        "SYNTHESIZED fixture (not Owner-produced art); its job is to "
        "pin the estimator class, not to imitate art.",
        "Sandbox has no onnxruntime/torch GPU: RT-DETR is stubbed to "
        "the TRUE dark-ink bboxes of the drawn bubbles (detector "
        "stand-in); the region build, RF-16 estimator, quads, angles, "
        "reading-order sort and every render byte after the boxes are "
        "the REAL production path.",
        "OCR is stubbed to the drawn JP text; translations are the "
        "builder's Bengali strings; inpainted.png is the synthesized "
        "clean page (rings stay, text removed).",
        "text_mask.png is the TRUE synthesized text ink (ground-truth "
        "surface for the hand-tool measurement), not the pipeline "
        "detect-stage box mask.",
        "The Owner's live diagonal page remains the final visual "
        "gate for the B2 merge (Owner re-accept on the same test "
        "page).",
    ],
    "acceptance_rule": (
        "RF-16 directive #3: on S009, >= 6 of 7 tilted regions store "
        "|angle| within +/-3 deg of ground truth AND rendered ink "
        "orientation matches; horizontal regions stay 0; verticals "
        "stay V-3."),
    "ground_truth": gt_table,
    "owner_notes": (
        "RF-16 LIVE REJECT fix evidence: base bytes dc612d5 store 0.00 "
        f"on all 7 tilted regions here (repro: scripts/"
        "m009_b2_rf16_repro.py post); RF-16 bytes store "
        f"{tilted_pass}/7 within +/-3 deg."),
}
with open(DEST / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=1)
print(f"  archived metadata.json ({tilted_pass}/7 tilted pass)")

print(f"\nS009 archive -> {DEST}")
for p in sorted(DEST.iterdir()):
    print(f"  {p.name:18s} {p.stat().st_size:>9,d} B")
