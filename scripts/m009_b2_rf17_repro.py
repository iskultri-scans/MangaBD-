#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-17 — repro harness: layout parity on tilted bubbles.

Owner visual REJECT on 57ac480 (tilt inherits BUT layout broke):
  D1 burst bubble  — multi-line original renders as ONE line, steep
     angle, text clipped at the bubble edge (ink outside the bubble);
  D2 one tilted bubble renders COMPLETELY EMPTY (text lost);
  D3 tilted bubbles' line-break pattern / lean magnitude mismatch.

Arms (same S010 page, same boxes, same Bengali translations):
  post : WORKING-TREE bytes, knob ON — at RF-17 development time this
         was 57ac480 (the REJECT state: 0/7 inherit, D1 overflow, D2
         white-on-white; evidence preserved in this session log and
         samples/S010_burst/metadata.json owner_notes). On the FIXED
         tree this arm shows the healthy state.
  base : WORKING-TREE bytes, knob OFF — the B1-equivalent layout
         reference (angle 0 -> bbox fit dims; the A3 "lines(base)"
         column)
  fix  : alias of post on the fixed tree (kept for CLI compatibility
         with the development log)

The authoritative instrument is scripts/m009_b2_rf17_verify.py
(28 gates incl. the A1-A6 hard criteria on the S009 + S010 archives).

Measurements per region (matched to the builder's ground truth):
  stored angle + stored quad fit dims      (detections.json rows)
  visible rendered ink (final vs inpainted delta, dark-or-light)
  ink inside / outside the TRUE interior   (A1/A2 surface)
  rendered line count (projection bands on the ink, rotated frame)
  base line count (fit_font_size on bbox dims — what tilt-off does)
  text color chosen + interior brightness  (D2 surface)

The page comes from scripts/m009_b2_rf17_page.py (S010 owner-class:
3 bursts + 4 art-tight tilted ellipses + 2 H + 1 V-3).
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path("/home/z/my-project/MangaBD")
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
sys.path.insert(0, str(REPO / "scripts"))
from m009_b2_rf14_repro import (  # noqa: E402
    install_pathlib_shim, make_torch_stub, restore_pathlib,
    seed_cell00_side_effects,
)
from m009_b2_rf15_repro import exec_cells  # noqa: E402
from m009_b2_rf17_page import build_s010_page  # noqa: E402

WORK = Path("/home/z/my-project/cells_rf17_repro")
VISIBLE_INK_FLOOR = 50      # below this the bubble reads EMPTY (D2)
LINE_GAP_PX = 4             # projection gap that separates two lines


# ── page + chain ────────────────────────────────────────────────────
def build_page():
    full, clean, regions, ink, interiors = build_s010_page(str(REPO))
    return full, clean, regions, ink, interiors


def run_chain(full, clean, regions, knob_on):
    """Full production chain on the S010 page. Returns (ns, det_rows)."""
    WORK.mkdir(parents=True, exist_ok=True)
    nb = json.loads((REPO / NB_NAME).read_text(encoding="utf-8"))
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

    if not knob_on:
        ns["MANGABD_CONFIG"]["detection"]["b2_orientation_enable"] = False

    pid = ns["init_page"]("s010_burst.jpg", width=full.shape[1],
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
    ns["detect_page"](pid, full, force=True)

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

    det_rows = ns["load_json_artifact"](pid, "detections", default=[])
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
                      "language_score": {"en": 1.0, "bn": 0.0,
                                         "unknown": 0.0},
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
    return ns, pid, det_rows, match_gt


# ── measurements ────────────────────────────────────────────────────
def visible_ink(final_bgr, inpainted_bgr):
    """Rendered ink = pixels the render changed by a visible margin."""
    f = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2GRAY).astype(np.int16)
    i = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2GRAY).astype(np.int16)
    return np.abs(f - i) > 24


def count_lines(ink_mask, angle_deg):
    """Line bands: project ink onto the axis perpendicular to the
    reading direction (angle), count bands separated by LINE_GAP_PX."""
    if ink_mask.sum() < 20:
        return 0
    t = np.radians(float(angle_deg))
    # reading direction u (text flows along u); project on v
    v = np.array([-np.sin(t), np.cos(t)])
    ys, xs = np.nonzero(ink_mask)
    proj = np.round(xs * v[0] + ys * v[1]).astype(int)
    lo, hi = int(proj.min()), int(proj.max())
    if hi - lo < 8:
        return 1 if ink_mask.sum() >= 20 else 0
    hist = np.zeros(hi - lo + 1, int)
    np.add.at(hist, proj - lo, 1)
    occ = hist >= 2
    # count runs of occupied bins separated by >= LINE_GAP_PX gaps
    bands, run, gap = 0, False, 0
    for o in occ:
        if o:
            if not run and gap >= LINE_GAP_PX:
                bands += 1
            elif not run:
                bands += 1 if bands == 0 else 0
            run, gap = True, 0
        else:
            if run:
                run, gap = False, 1
            else:
                gap += 1
    return max(bands, 1)


def region_report(ns, pid, det_rows, match_gt, interiors, inpainted):
    final = ns["load_image_artifact"](pid, "final")
    df = ns["translation_df"]
    rows = []
    for r in det_rows:
        g = match_gt(r)
        x, y, w, h = r["x"], r["y"], r["width"], r["height"]
        ang = float(r.get("angle", 0.0))
        quad = r.get("quad")
        ink = visible_ink(final, inpainted)
        win = np.zeros_like(ink)
        win[y:y + h, x:x + w] = True
        rink = ink & win
        inter = interiors[g["tag"]]
        inside = int((rink & inter).sum())
        outside = int((rink & ~inter).sum())
        # D2 surface: the RENDER's actual color decision, replicated
        # (interior path -> interior mean; else choose_text_color)
        bold = r["region_type"] in ["sfx", "narrator"]
        quad_r = r.get("quad")
        interior_res = None
        if abs(ang) > 1.0 and quad_r is not None:
            interior_res = ns["_b2_interior_fit"](
                inpainted, x, y, w, h, quad_r)
        if interior_res is not None:
            tc = _replicated_render_color(ns, interior_res[2],
                                          r["region_type"])
        else:
            tc = ns["choose_text_color"](inpainted, x, y, w, h,
                                         region_type=r["region_type"])
        ig = cv2.cvtColor(inpainted, cv2.COLOR_BGR2GRAY)
        imean = float(ig[inter].mean()) if inter.any() else -1.0
        # render's ACTUAL fit dims (interior -> quad -> bbox) + padding
        if interior_res is not None:
            rfw, rfh = interior_res[0], interior_res[1]
            rpad = max(4, int(min(rfw, rfh) * 0.08))
        else:
            qdims = None
            if quad is not None:
                q = np.asarray(quad, dtype=np.float64)
                if q.shape == (4, 2):
                    qdims = (
                        int(round(max(float(np.linalg.norm(q[0] - q[1])),
                                      float(np.linalg.norm(q[2] - q[3]))))),
                        int(round(max(float(np.linalg.norm(q[0] - q[3])),
                                      float(np.linalg.norm(q[1] - q[2]))))),
                    )
            if qdims is not None and qdims[0] >= 5 and qdims[1] >= 5:
                rfw, rfh = qdims
                rpad = max(4, int(min(w, h) * 0.08))
            else:
                rfw, rfh = w, h
                rpad = None
        # base line count: fit on bbox dims (what tilt-off does)
        trow = df[(df["page_id"] == pid) & (df["id"] == r["id"])]
        text = str(trow.iloc[0]["translated_text"]) if len(trow) else ""
        _, base_lines, _ = ns["fit_font_size"](
            text, w, h, bold=bold)
        # the render's actual line count (fit on the render's dims)
        fsize, flines, _ = ns["fit_font_size"](
            text, rfw, rfh, bold=bold, padding=rpad)
        rows.append({
            "tag": g["tag"], "class": g["class"], "gt": g["beta"],
            "lines_gt": g["lines"], "stored": ang, "fw": rfw, "fh": rfh,
            "visible_px": int(rink.sum()), "inside": inside,
            "outside": outside, "text_color": tc,
            "interior_mean": round(imean, 1),
            "lines_render": len(flines) if flines else 0,
            "lines_base": len(base_lines) if base_lines else 0,
            "fit_size": int(fsize), "fit_lines": len(flines) if flines else 0,
            "path": ("interior" if interior_res is not None
                     else ("quad" if quad is not None else "bbox")),
        })
    return rows, final


def _replicated_render_color(ns, imean, region_type):
    """The RF-17 interior-path color decision (cell-10 mirror)."""
    cfg = ns["MANGABD_CONFIG"]["rendering"]
    if region_type in ["bubble", "thought"]:
        return (tuple(cfg.get("default_bubble_color", [0, 0, 0]))
                if imean > 160 else (255, 255, 255))
    if region_type == "narrator":
        return (tuple(cfg.get("default_narrator_color", [0, 0, 0]))
                if imean > 140 else (255, 255, 255))
    return (tuple(cfg.get("default_sfx_color", [255, 255, 255]))
            if imean < 160 else
            tuple(cfg.get("default_overlay_color", [0, 0, 0])))


def print_table(title, rows):
    print(f"\n== {title} ==")
    hdr = (f"{'tag':>4s} {'class':>10s} {'GT':>6s} {'stored':>7s} "
           f"{'path':>8s} {'fitW':>4s} {'fitH':>4s} {'lGT':>3s} {'lBase':>5s} "
           f"{'lRend':>5s} {'fitS':>4s} {'inpx':>5s} "
           f"{'outpx':>5s} {'color':>9s} {'iMean':>6s}")
    print(hdr)
    for r in rows:
        print(f"{r['tag']:>4s} {r['class']:>10s} {r['gt']:+6.1f} "
              f"{r['stored']:+7.2f} {r['path']:>8s} "
              f"{r['fw']:>4d} {r['fh']:>4d} "
              f"{r['lines_gt']:>3d} {r['lines_base']:>5d} "
              f"{r['lines_render']:>5d} {r['fit_size']:>4d} {r['inside']:>5d} "
              f"{r['outside']:>5d} {str(r['text_color']):>9s} "
              f"{r['interior_mean']:>6.1f}")


def defect_summary(rows):
    """D1/D2/D3 booleans on the measurement rows (render-replicated
    decisions + true-interior ink audit)."""
    d = {"D1": [], "D2": [], "D3": []}
    for r in rows:
        if r["class"] == "burst":
            bad = (r["lines_render"] < max(2, r["lines_base"])
                   or r["outside"] > 0
                   or abs(r["stored"] - r["gt"]) > 3.0)
            d["D1"].append((r["tag"], bad))
        if r["class"] == "tilted":
            # D2 = invisible text: white ink on a light interior
            # (contrast-dead, pixel count irrelevant) or no ink at all
            empty = (
                (tuple(r["text_color"]) == (255, 255, 255)
                 and r["interior_mean"] > 200.0)
                or r["inside"] < VISIBLE_INK_FLOOR
            )
            d["D2"].append((r["tag"], empty))
            mm = (r["lines_render"] < r["lines_base"]
                  or abs(r["stored"] - r["gt"]) > 3.0 or r["outside"] > 0)
            d["D3"].append((r["tag"], mm))
    return d


def run(arm, knob_on, full, clean, regions, interiors):
    ns, pid, det_rows, match_gt = run_chain(full, clean, regions, knob_on)
    rows, final = region_report(ns, pid, det_rows, match_gt, interiors,
                                clean)
    print_table(f"RF-17 arm [{arm}]", rows)
    d = defect_summary(rows)
    for k, v in d.items():
        fired = [t for t, bad in v if bad]
        print(f"  {k} fired: {fired if fired else 'none'}")
    out = Path(f"/home/z/my-project/rf17_final_{arm}.png")
    cv2.imwrite(str(out), final)
    print(f"  final image -> {out}")
    return rows, ns, final


def main():
    arm = sys.argv[1] if len(sys.argv) > 1 else "post"
    full, clean, regions, ink, interiors = build_page()
    if arm == "both":
        rows_post, _, _ = run("post", True, full, clean, regions,
                              interiors)
        rows_base, _, _ = run("base", False, full, clean, regions,
                              interiors)
        merged = []
        for p, b in zip(rows_post, rows_base):
            m = dict(p)
            m["lines_base"] = b["lines_base"]
            merged.append(m)
        print_table("RF-17 merged (post lines + base lines)", merged)
    else:
        knob = arm != "base"
        rows, _, _ = run(arm, knob, full, clean, regions, interiors)
    return 0


if __name__ == "__main__":
    sys.exit(main())
