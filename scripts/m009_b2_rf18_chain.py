#!/usr/bin/env python3
"""MANGABD-009 B2 RF-18 — shared full-chain runner (fresh namespace).

Runs the verbatim RF-18 cells (exec_cells, RF-15 harness) and drives
ONE page through the production chain detect -> ocr -> inpaint ->
translate -> render, with the SAME disclosed sandbox stubs the
S009/S010 archive builders have used since RF-16/17:

  * torch        : inert stub (no CUDA) — RT-DETR inference stubbed;
  * rtdetr_detect: the fixture's TRUE region boxes (detector
                   stand-in);
  * ctd_detect_boxes_and_mask: the fixture's TRUE text-ink mask as
                   the CTD raw prob map (NEW in RF-18 — the mask-GT
                   rung needs the original text ink; in production
                   this comes from the real CTD model);
  * run_ocr_engine: the drawn JP text (engine "stub");
  * inpaint      : the synthesized clean page (rings/panels stay,
                   text removed).

Everything AFTER the boxes and the mask — the region build, the
RF-18 ladder (mask GT -> 9b estimator -> 0), quads, angles, reading
order, wrap/layout, render bytes — is the REAL production path.

Returns (ns, pid, det_rows) with the page fully rendered.
"""
import json
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
sys.path.insert(0, str(REPO / "scripts"))

WORK = Path("/home/z/my-project/cells_rf18_chain")


def run_chain(page_name, full, clean, regions, ink_mask, extra_seed=None):
    """Full chain on one synthesized page. extra_seed: optional
    dict merged into the namespace BEFORE detect (test knobs)."""
    from m009_b2_rf14_repro import (
        install_pathlib_shim, make_torch_stub, restore_pathlib,
    )
    from m009_b2_rf15_repro import exec_cells

    nb = json.loads(
        (REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt")
        .read_text(encoding="utf-8"))
    WORK.mkdir(parents=True, exist_ok=True)
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
    assert "Cell 10 result: SUCCESS" in logs[10], \
        f"cell-10 battery failed:\n{logs[10][-2000:]}"
    assert "❌" not in logs[10], "cell-10 battery has failures"
    assert "❌" not in logs[12], "cell-12 battery has failures"

    if extra_seed:
        ns.update(extra_seed)

    pid = ns["init_page"](page_name, width=full.shape[1],
                          height=full.shape[0], image_np=full,
                          overwrite=True)

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

    ink_u8 = (ink_mask > 0).astype("uint8") * 255
    ns["ctd_detect_boxes_and_mask"] = lambda img: {
        "boxes": [], "raw_mask": ink_u8.copy(), "textlines": [],
    }

    ocr_stub = {}

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

    det_rows = ns["detect_page"](pid, full, force=True)[0]
    for r in det_rows:
        g = match_gt(r)
        ocr_stub[(int(r["x"]), int(r["y"]))] = {
            "text": g["jp"].split("\n")[0], "confidence": 0.9,
            "engine": "stub",
            "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
            "warnings": [], "is_english": True, "status": "ok",
            "vertical_ocr": None, "__bengali": g["bengali"],
        }
    ns["run_ocr_engine"] = lambda name, img, region, page_id=None: (
        ocr_stub.get(tuple(int(region.get(k, 0)) for k in ("x", "y")),
                     {"text": "テスト", "confidence": 0.9, "engine": name,
                      "language_score": {"en": 1.0, "bn": 0.0,
                                         "unknown": 0.0},
                      "warnings": [], "is_english": True, "status": "ok",
                      "vertical_ocr": None}))
    ns["ocr_page"](pid, full, force=True)
    ns["save_image_artifact"](pid, "inpainted", clean, quality=95)
    ns["mark_stage_done"](pid, "inpaint", meta={"inpaint_engine": "synthetic"})

    df = ns["translation_df"]
    for idx, row in df[df["page_id"] == pid].iterrows():
        key = (int(row["x"]), int(row["y"]))
        df.at[idx, "translated_text"] = ocr_stub.get(
            key, {}).get("__bengali", "এই কী হয়েছে বলো তো!")
    ns["save_translation_df"]()
    ns["sync_translate_stage"]()
    ns["run_render_all"](force=True, require_translation=True)

    det_rows = ns["load_json_artifact"](pid, "detections", default=[])
    df_now = ns["translation_df"]
    rendered = int((df_now[df_now["page_id"] == pid]["status"]
                    == "rendered").sum())
    assert rendered == len(det_rows), \
        f"rendered {rendered}/{len(det_rows)}"
    return ns, pid, det_rows


def artifact_path(ns, pid, kind):
    return Path(ns["get_artifact_path"](pid, kind))
