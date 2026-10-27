#!/usr/bin/env python3
"""MANGABD-009 B2 zero-ink repro — HYPOTHESIS LADDER (scenarios S2..S7).

Each scenario runs the verbatim render seam under one live-like condition.
Ink measured as new dark pixels (final vs inpainted) per region + total.
"""
import json
import sys
import pathlib
import numpy as np
import cv2
from PIL import Image as PILImage, ImageDraw, ImageFont

HERE = pathlib.Path("/home/z/my-project/m009b2_repro")
sys.path.insert(0, str(HERE / "scripts"))
from b2_env import build_env  # noqa: E402
from repro_run import (make_page, make_inpainted, build_rows,  # noqa: E402
                       JP_FONT)


def setup_page(ns, page_bgr, inp_bgr, force_fresh=True):
    pid = "page_01.jpg"
    ns["init_page"](pid, width=page_bgr.shape[1],
                    height=page_bgr.shape[0], overwrite=True)
    ns["save_image_artifact"](pid, "original", page_bgr, quality=95)
    ns["save_image_artifact"](pid, "inpainted", inp_bgr, quality=95)
    return pid


def load_regions_artifact(ns, pid):
    return ns["load_json_artifact"](pid, "detections", default=[])


def measure(ns, pid, inp_bgr, regions=None):
    final = ns["render_page"](pid)
    fin = np.asarray(final.convert("L")) if isinstance(final, PILImage.Image) \
        else cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
    inp = cv2.cvtColor(inp_bgr, cv2.COLOR_BGR2GRAY)
    out = {"total_new_ink": int(((fin < 128) & (inp >= 128)).sum())}
    per = []
    for r in (regions or []):
        x, y, w, h = r["x"], r["y"], r["width"], r["height"]
        x0, y0 = max(0, x - 12), max(0, y - 12)
        x1 = min(fin.shape[1], x + w + 12)
        y1 = min(fin.shape[0], y + h + 12)
        per.append({
            "id": r["id"], "type": r["region_type"], "angle": r["angle"],
            "new_ink": int(((fin[y0:y1, x0:x1] < 128)
                            & (inp[y0:y1, x0:x1] >= 128)).sum()),
        })
    out["per_region"] = per
    out["render_meta"] = ns["MANGABD_MANIFEST"]["pages"][pid]["stages"].get(
        "render")
    return out, final


def rows_for(ns, pid, regions, angles=None):
    regs = json.loads(json.dumps(regions))
    if angles is not None:
        for r, a in zip(regs, angles):
            r["angle"] = a
    ns["translation_df"] = ns["empty_translation_df"]()
    ns["upsert_translation_rows"](pid, build_rows(pid, regs))
    return regs


def main():
    page = make_page()
    page_bgr = cv2.cvtColor(np.asarray(PILImage.fromarray(page[0])),
                            cv2.COLOR_RGB2BGR)
    inp_bgr = make_inpainted(page[0], page[1])
    bboxes, types = page[1], page[2]
    results = {}

    ns = build_env("tip", HERE / "ladder_env.log")

    # ---------- S2: true diagonal strip (estimator + full render) ----------
    pid = setup_page(ns, page_bgr, inp_bgr)
    diag = PILImage.new("RGB", page_bgr.shape[1::-1], (255, 255, 255))
    dd = ImageDraw.Draw(diag)
    f = ImageFont.truetype(JP_FONT, 34)
    strip = PILImage.new("L", (700, 60), 255)
    ImageDraw.Draw(strip).text((10, 8), " सेक्सी ডাইনামাইট বিস্ফোরণ! ", font=f,
                               fill=0)
    rot = strip.rotate(-25, expand=True, resample=PILImage.BICUBIC,
                       fillcolor=255)
    diag.paste(PILImage.merge("RGB", (rot, rot, rot)), (200, 780))
    dd = ImageDraw.Draw(diag)
    diag_bgr = cv2.cvtColor(np.asarray(diag), cv2.COLOR_RGB2BGR)
    g = cv2.cvtColor(diag_bgr, cv2.COLOR_BGR2GRAY)
    ys, xs = np.nonzero(g < 128)
    bx = (int(xs.min()), int(ys.min()),
          int(xs.max() - xs.min()) + 1, int(ys.max() - ys.min()) + 1)
    est = ns["_estimate_region_angle"]
    ang, quad = est(diag_bgr, *bx)
    print(f"S2 diagonal: estimator angle={ang} quad={'Y' if quad else 'N'} "
          f"bbox={bx}")
    regs = [{"id": 1, "page_id": pid, "x": bx[0], "y": bx[1],
             "width": bx[2], "height": bx[3],
             "quad": (np.round(np.asarray(quad)).astype(np.int32).tolist()
                      if quad is not None else
                      [[bx[0], bx[1]], [bx[0] + bx[2], bx[1]],
                       [bx[0] + bx[2], bx[1] + bx[3]],
                       [bx[0], bx[1] + bx[3]]]),
             "angle": float(ang), "region_type": "sfx",
             "detector_class": "synthetic", "detector_score": 0.97,
             "parent_bubble_id": None}]
    ns["save_json_artifact"](pid, "detections", regs)
    rows_for(ns, pid, regs)
    m, _ = measure(ns, pid, diag_bgr, regs)
    results["S2_diagonal"] = m

    # fresh page for remaining scenarios
    ns2 = build_env("tip", HERE / "ladder_env2.log")
    pid = setup_page(ns2, page_bgr, inp_bgr)
    est = ns2["_estimate_region_angle"]
    regions = []
    b2_tilted = 0
    ns2["MANGABD_CONFIG"]["detection"].setdefault(
        "b2_orientation_enable", True)
    for i, ((x, y, w, h), rtype) in enumerate(zip(bboxes, types)):
        quad = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                        dtype=np.int32)
        angle = 0.0
        a, q = est(page_bgr, x, y, w, h)
        if a != 0.0:
            angle = float(a)
            if q is not None:
                quad = np.round(np.asarray(q)).astype(np.int32)
            b2_tilted += 1
        regions.append({
            "id": i + 1, "page_id": pid, "x": x, "y": y, "width": w,
            "height": h, "quad": quad.tolist(), "angle": angle,
            "region_type": rtype, "detector_class": "synthetic",
            "detector_score": 0.97, "parent_bubble_id": None,
        })
    ns2["save_json_artifact"](pid, "detections", regions)
    print(f"baseline estimator fires on {b2_tilted}/6 regions")

    # ---------- S3: ALL regions forced angle=-45 (worst-case misfire) ------
    rows_for(ns2, pid, regions, angles=[-45.0] * len(regions))
    m, _ = measure(ns2, pid, inp_bgr, regions)
    results["S3_all_-45"] = m

    # ---------- S4: detections artifact MISSING at render -------------------
    import os
    art = ns2["get_artifact_path"](pid, "detections")
    os.rename(art, str(art) + ".bak")
    ns2["init_page"](pid, overwrite=False)  # keep manifest
    rows_for(ns2, pid, regions, angles=[-45.0] * len(regions))
    ns2["MANGABD_MANIFEST"]["pages"][pid]["stages"]["render"] = False
    m, _ = measure(ns2, pid, inp_bgr, regions)
    os.rename(str(art) + ".bak", str(art))
    results["S4_no_artifact"] = m

    # ---------- S5: NaN angle rows ------------------------------------------
    rows_for(ns2, pid, regions, angles=[float("nan")] * len(regions))
    ns2["MANGABD_MANIFEST"]["pages"][pid]["stages"]["render"] = False
    m, _ = measure(ns2, pid, inp_bgr, regions)
    results["S5_nan_angle"] = m

    # ---------- S6: cached render checkpoint (resume trap) ------------------
    # mark render done + save a BLANK final, then call render_page(force=False)
    blank = np.full_like(inp_bgr, 255)
    ns2["save_image_artifact"](pid, "final", blank, quality=95)
    ns2["mark_stage_done"](pid, "render", meta={"simulated": True})
    rows_for(ns2, pid, regions)  # real angles
    try:
        final = ns2["render_page"](pid)  # NOT forced -> should hit cache
        cached = ns2["load_image_artifact"](pid, "final")
        m = {"cache_returned_blank": bool(
            (np.asarray(cached.convert("L")) == 255).all()
            if isinstance(cached, PILImage.Image) else False)}
    except Exception as exc:
        m = {"cache_path_raised": repr(exc)[:200]}
    results["S6_cached_resume"] = m

    # ---------- S7: OCR deskew crop sanity on a B2 quad ---------------------
    # r1's B2 quad (estimator false-fired -8deg) -> crop_region_rotated
    r1 = next(r for r in regions if r["id"] == 1)
    crr = ns2.get("crop_region_rotated")
    crop = crr(page_bgr, r1) if crr else None
    if crop is not None and crop.size:
        # readable crop = ink present, aspect close to strip dims
        cg = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        results["S7_deskew_crop"] = {
            "shape": list(crop.shape[:2]),
            "ink_px": int((cg < 128).sum()),
            "expected_aspect": round(r1["width"] / max(1, r1["height"]), 2),
            "actual_aspect": round(crop.shape[1] / max(1, crop.shape[0]), 2),
        }
        cv2.imwrite(str(HERE / "render_eyeball" / "s7_deskew_r1.png"), crop)
    else:
        results["S7_deskew_crop"] = {"crop": None}

    print(json.dumps(results, indent=2, ensure_ascii=False))
    (HERE / "ladder_result.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
