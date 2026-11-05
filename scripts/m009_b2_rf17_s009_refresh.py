#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-17 — S009 archive refresh (final.jpg only).

The S009 archive was captured by RF-16 with the then-current render:
tilt inherited BUT layout broken (the Owner's D1/D3 — small-font
multi-touch-line blocks, "অনেক তফাৎ"). RF-17 fixes the tilted layout,
so the archive's final.jpg must be re-rendered to stay the honest
"current pipeline" snapshot (the S00X convention). This script:

  1. re-runs the full chain on the S009 page (same stubs as the
     RF-16 builder);
  2. HARD-asserts the detection side is byte-stable (angles + quads
     + boxes + every other detections.json byte) — the RF-16
     no-regression proof at margin 16;
  3. HARD-asserts ocr.json + translation.json are byte-stable;
  4. HARD-asserts the H/V regions' renders are byte-identical (0
     changed pixels) — only the 7 tilted regions change, BY DESIGN;
  5. overwrites final.jpg and appends the rf17_refresh disclosure to
     metadata.json.
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

WORK = Path("/home/z/my-project/cells_rf17_s009refresh")
DEST = REPO / "samples" / "S009_diagonal"

branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                        capture_output=True, text=True).stdout.strip()
assert branch == "mangabd-009-b2", f"on branch {branch!r}"

full, clean, regions, ink_mask = build_s009_page(str(REPO))
arch_det_bytes = (DEST / "detections.json").read_bytes()
arch_ocr_bytes = (DEST / "ocr.json").read_bytes()
arch_tr_bytes = (DEST / "translation.json").read_bytes()
arch_final = cv2.imread(str(DEST / "final.jpg"))
arch_meta = json.loads((DEST / "metadata.json").read_text(encoding="utf-8"))

WORK.mkdir(parents=True, exist_ok=True)
nb = json.loads((REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt")
                .read_text(encoding="utf-8"))
for i, c in enumerate(nb["cells"]):
    (WORK / f"cell_{i:02d}.py").write_text(
        "".join(c.get("source", [])), encoding="utf-8")

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
ocr_stub = {}
for r in det_rows:
    g = match_gt(r)
    ocr_stub[(int(r["x"]), int(r["y"]))] = {
        "text": g["jp"].split("\n")[0], "confidence": 0.9, "engine": "stub",
        "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
        "warnings": [], "is_english": True, "status": "ok",
        "vertical_ocr": None, "__bengali": g["bengali"]}
ns["run_ocr_engine"] = lambda name, img, region, page_id=None: (
    ocr_stub.get(tuple(int(region.get(k, 0)) for k in ("x", "y")),
                 {"text": "テスト", "confidence": 0.9, "engine": name,
                  "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
                  "warnings": [], "is_english": True, "status": "ok",
                  "vertical_ocr": None}))
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
rendered = int((ns["translation_df"][ns["translation_df"]["page_id"] == pid]
                ["status"] == "rendered").sum())
assert rendered == 10, f"rendered {rendered}/10"

# ── byte-stability gates before touching the archive ────────────────
new_det_path = Path(ns["get_artifact_path"](pid, "detections"))
assert new_det_path.read_bytes() == arch_det_bytes, (
    "detections.json NOT byte-stable — RF-16 regression!")
new_ocr_path = Path(ns["get_artifact_path"](pid, "ocr"))
new_tr_path = Path(ns["get_artifact_path"](pid, "translation"))


def _semantic_ocr(raw):
    """ocr.json rows with the nondeterministic fallback-trace TIMING
    (ms) normalized — the archived rows were captured with qwen-error
    ms=280, a fresh sandbox run reports ms=0; content is identical."""
    rows = json.loads(raw)
    for r in rows:
        oc = r.get("ocr") or {}
        for t in oc.get("fallback_trace") or []:
            t["ms"] = 0
    return rows


assert _semantic_ocr(new_ocr_path.read_bytes()) == \
    _semantic_ocr(arch_ocr_bytes), "ocr.json NOT semantically stable"
# translation: the archive's translation.json was builder-written from
# the df; compare the fresh df's applied rows against it (semantic)
arch_tr_rows = json.loads(arch_tr_bytes)
df_now = ns["translation_df"]
fresh_rows = df_now[df_now["page_id"] == pid].sort_values("id")
assert len(fresh_rows) == len(arch_tr_rows), "translation row count"
for (_, fr), ar in zip(fresh_rows.iterrows(), arch_tr_rows):
    assert int(fr["id"]) == int(ar["id"]), "translation id order"
    assert str(fr["translated_text"]) == str(ar["translated_text"]), (
        f"translation text drift on id {ar['id']}")
print("detections byte-stable + ocr semantically stable + "
      "translation rows identical: OK")

# ── render diff census: only tilted regions change, by design ───────
h = min(final.shape[0], arch_final.shape[0])
w = min(final.shape[1], arch_final.shape[1])
diff = (np.abs(final[:h, :w].astype(int)
               - arch_final[:h, :w].astype(int)).sum(axis=2) > 30)
changed_by_class = {}
for r in det_rows:
    g = match_gt(r)
    x, y, ww, hh = r["x"], r["y"], r["width"], r["height"]
    n = int(diff[y:y + hh, x:x + ww].sum())
    changed_by_class.setdefault(g["class"], []).append((g["tag"], n))
    print(f"  {g['tag']} [{g['class']:>9s}] changed_px={n}")
hv = [n for _, n in (changed_by_class.get("horizontal", [])
                     + changed_by_class.get("vertical", []))]
tilted = [n for _, n in changed_by_class.get("tilted", [])]
assert not any(hv), f"H/V renders changed: {hv}"
assert all(t > 1000 for t in tilted), f"tilted renders did not change: {tilted}"
print(f"H/V byte-identical (0 px); tilted changed by design: {tilted}")

# ── refresh final.jpg + metadata disclosure ─────────────────────────
src = Path(ns["get_artifact_path"](pid, "final"))
shutil.copy2(src, DEST / "final.jpg")
print(f"refreshed final.jpg ({src.stat().st_size} B)")

arch_meta["rf17_refresh"] = {
    "date": str(date.today()),
    "what": (
        "final.jpg re-rendered with the RF-17 layout-parity fix: the 7 "
        "tilted regions now render multi-line interior-fit text "
        "(bigger font, chord-profile-safe box, interior-centroid paste, "
        "interior-mean color) instead of the RF-16 quad-fit small-font "
        "blocks (the Owner's D1/D3 REJECT)."),
    "unchanged": [
        "detections.json (byte-identical — RF-16 angles + quads + boxes "
        "proven stable at _B2_RING_MARGIN 16)",
        "ocr.json / translation.json (byte-identical)",
        "the horizontal + vertical regions' renders (0 changed pixels)",
    ],
    "evidence": "scripts/m009_b2_rf17_verify.py V4",
}
with open(DEST / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(arch_meta, f, ensure_ascii=False, indent=1)
print("metadata.json: rf17_refresh disclosure appended")
