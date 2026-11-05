#!/usr/bin/env python3
"""MANGABD-009 B2 zero-ink repro — SCENARIO RUNNER.

Runs the verbatim render seam (cell-10 render_page) on synthetic pages under
live-like conditions, TIP vs BASE A/B, with per-region ink measurement.

Detection-side fixture: per-region verbatim `_estimate_region_angle` (cell-6
slice) + the verbatim B2 region-dict construction lines (quad overwrite).
OCR/translate stages are replaced by a translation_df fixture with the exact
build_ocr_row column set (cell-7 L969-992) — the render seam's real input.
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

JP_FONT = "/home/z/my-project/repo/assets/fonts/NotoSansJP[wght].ttf"


# ─────────────────────────── synthetic page ───────────────────────────

def make_page():
    """Horizontal manga page: white bubbles + JP ink, live-like geometry."""
    W, H = 1100, 1600
    page = PILImage.new("RGB", (W, H), (245, 240, 235))  # toned paper
    d = ImageDraw.Draw(page)

    def bubble(cx, cy, rx, ry):
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry],
                  fill=(255, 255, 255), outline=(30, 30, 30), width=3)

    font = ImageFont.truetype(JP_FONT, 30)
    font_s = ImageFont.truetype(JP_FONT, 26)

    regions = []  # (region_type, tight bbox of INK, list[(x,y,text,font)])

    def block(x0, y0, lines, f):
        y = y0
        for t in lines:
            d.text((x0, y), t, font=f, fill=(15, 15, 15))
            bb = f.getbbox(t)
            y += (bb[3] - bb[1]) + 14
        wmax = max(f.getbbox(t)[2] - f.getbbox(t)[0] for t in lines)
        regions.append(("bubble", (x0 - 6, y0 - 8, wmax + 12, y - y0 - 4)))

    # R1: 2-line bubble (upper-left)
    bubble(300, 300, 230, 120)
    block(140, 240, ["おはよう。", "今日も暑いね。"], font)
    # R2: 3-line bubble (upper-right)
    bubble(820, 340, 220, 130)
    block(660, 250, ["昨日の試合、", "見た？最後の", "ホームラン。"], font)
    # R3: narration box (left-middle)
    d.rectangle([90, 620, 520, 760], fill=(255, 255, 255),
                outline=(30, 30, 30), width=3)
    block(110, 640, ["その夜、街は静か", "だった。"], font_s)
    regions[-1] = ("narration", regions[-1][1])
    # R4: small bubble (lower-left)
    bubble(300, 950, 170, 90)
    block(180, 920, ["うん。"], font_s)
    # R5: vertical note (right-middle) — V-3 class
    vf = ImageFont.truetype(JP_FONT, 24)
    x0, y0 = 980, 700
    for i, ch in enumerate("台風が近づいている"):
        d.text((x0, y0 + i * 30), ch, font=vf, fill=(15, 15, 15))
    regions.append(("vertical_note", (x0 - 4, y0 - 6, 36, 8 * 30 + 12)))
    # R6: 2-line bubble (bottom)
    bubble(700, 1250, 240, 110)
    block(520, 1190, ["気をつけてね。", "また明日。"], font)

    bboxes = [(int(x), int(y), int(w), int(h)) for _, (x, y, w, h) in regions]
    types = [t for t, _ in regions]
    return np.asarray(page), bboxes, types


def make_inpainted(page_np, bboxes):
    """Simulate successful inpaint: regions wiped to clean white."""
    inp = page_np.copy()
    for (x, y, w, h) in bboxes:
        cv2.rectangle(inp, (x - 8, y - 8), (x + w + 8, y + h + 8),
                      (255, 255, 255), -1)
    return inp


# ─────────────── detection-side (verbatim cell-6 semantics) ───────────────

def detect_regions(ns, page_bgr, bboxes, types, b2=True):
    """Verbatim estimator + verbatim B2 region-dict construction.

    Mirrors cell-6 region-build: candidate boxes -> estimator call under the
    default-ON knob -> `angle`/`quad` overwrite -> regions.append({...}) ->
    sort_regions_by_reading_order -> id reassign -> save_json_artifact.
    b2=False reproduces BASE cell-6 semantics (no estimator block: angle=0,
    quad=bbox) — the base branch has no estimator to call.
    """
    MANGABD_CONFIG = ns["MANGABD_CONFIG"]
    est = ns.get("_estimate_region_angle")
    sort_fn = ns.get("sort_regions_by_reading_order")
    MANGABD_CONFIG["detection"].setdefault("b2_orientation_enable", True)

    regions = []
    b2_tilted = 0
    for i, ((x, y, w, h), rtype) in enumerate(zip(bboxes, types)):
        detector_score = 0.97
        quad = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                        dtype=np.int32)
        angle = 0.0
        if b2 and MANGABD_CONFIG["detection"].get(
                "b2_orientation_enable", True):
            try:
                b2_angle, b2_quad = est(page_bgr, x, y, w, h)
                if b2_angle != 0.0:
                    angle = float(b2_angle)
                    if b2_quad is not None:
                        quad = np.round(
                            np.asarray(b2_quad)).astype(np.int32)
                    b2_tilted += 1
                    print(f"    📐 B2: region inherits {angle:+.1f}° ({rtype})")
            except Exception as exc:
                print(f"    estimator raised: {exc!r}")
        regions.append({
            "id": i + 1,
            "page_id": "PLACEHOLDER",
            "x": x, "y": y, "width": w, "height": h,
            "quad": quad.tolist(),
            "angle": angle,
            "region_type": rtype,
            "detector_class": "synthetic",
            "detector_score": detector_score,
            "parent_bubble_id": None,
        })
    if sort_fn is not None:
        regions = sort_fn(regions)
        for new_id, region in enumerate(regions, start=1):
            region["id"] = new_id
    return regions, b2_tilted


# ─────────────────── translation fixture (cell-7 schema) ───────────────────

BN = ["ওকে, আজও খুব গরম।", "কালকের খেলাটা দেখেছিলে?",
      "সেই রাতে শহর ছিল ভীষণ শান্ত।", "হ্যাঁ।",
      "ঘূর্ণিঝড় কাছে আসছে।", "সাবধানে যেড়িও। আবার দেখা হবে।"]


def build_rows(page_id, regions):
    """build_ocr_row-exact column set with translations applied."""
    rows = []
    for r in regions:
        rows.append({
            "page_id": page_id,
            "page": page_id,
            "id": int(r["id"]),
            "reading_order": int(r["id"]) - 1,
            "region_type": str(r["region_type"]),
            "detector_class": str(r["detector_class"]),
            "detector_score": float(r["detector_score"]),
            "parent_bubble_id": r["parent_bubble_id"] or "",
            "x": int(r["x"]), "y": int(r["y"]),
            "width": int(r["width"]), "height": int(r["height"]),
            "angle": float(r["angle"]),
            "original_text": "synthetic",
            "translated_text": BN[int(r["id"]) - 1],
            "confidence": 0.99,
            "ocr_engine": "synthetic",
            "translator_engine": "synthetic",
            "quality_score": "",
            "is_english": False,
            "bengali_valid": False,
            "status": "ok",
        })
    return rows


# ─────────────────────────────── runner ───────────────────────────────

def run_variant(variant, page_bgr, inp_bgr, bboxes, types, tag=""):
    ns = build_env(variant, HERE / f"repro_env_{variant}.log")
    pid = "page_01.jpg"

    # register page + artifacts (verbatim storage layer)
    ns["init_page"](pid, width=page_bgr.shape[1],
                    height=page_bgr.shape[0], overwrite=True)
    ns["save_image_artifact"](pid, "original", page_bgr, quality=95)
    ns["save_image_artifact"](pid, "inpainted", inp_bgr, quality=95)

    # detection side (verbatim estimator + verbatim dict construction)
    regions, b2_tilted = detect_regions(
        ns, page_bgr, bboxes, types, b2=(variant == "tip"))
    for r in regions:
        r["page_id"] = pid
    ns["save_json_artifact"](pid, "detections", regions)

    # translation_df via verbatim cell-3 helpers (upsert mutates the
    # namespace's global translation_df)
    ns["translation_df"] = ns["empty_translation_df"]()
    rows = build_rows(pid, regions)
    ns["upsert_translation_rows"](pid, rows)
    df = ns["translation_df"]

    # VERBATIM render_page call
    final = ns["render_page"](pid)

    # per-region ink measurement (new ink = dark pixels in final that the
    # inpainted canvas did not have), inside bbox +- 12px window
    fin = np.asarray(final.convert("L")) if isinstance(final, PILImage.Image) \
        else cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
    inp = cv2.cvtColor(inp_bgr, cv2.COLOR_BGR2GRAY)
    per_region = []
    for r in regions:
        x, y, w, h = r["x"], r["y"], r["width"], r["height"]
        x0, y0 = max(0, x - 12), max(0, y - 12)
        x1, y1 = min(fin.shape[1], x + w + 12), min(fin.shape[0], y + h + 12)
        win_f = fin[y0:y1, x0:x1]
        win_i = inp[y0:y1, x0:x1]
        new_ink = int(((win_f < 128) & (win_i >= 128)).sum())
        per_region.append({
            "id": r["id"], "type": r["region_type"],
            "angle": r["angle"], "bbox": [x, y, w, h],
            "new_ink_px": new_ink,
        })
    total_new_ink = int(((fin < 128) & (inp >= 128)).sum())

    meta = ns["MANGABD_MANIFEST"]["pages"][pid]["stages"].get("render")
    return {
        "variant": variant,
        "b2_tilted_detected": b2_tilted,
        "per_region": per_region,
        "total_new_ink": total_new_ink,
        "render_stage_meta": meta,
        "final_path": str(ns["get_artifact_path"](pid, "final")),
        "regions": regions,
    }


def main():
    page = make_page()
    page_pil = PILImage.fromarray(page[0])
    page_bgr = cv2.cvtColor(np.asarray(page_pil), cv2.COLOR_RGB2BGR)
    inp_bgr = make_inpainted(page[0], page[1])
    bboxes, types = page[1], page[2]

    res = {}
    for v in ("tip", "base"):
        res[v] = run_variant(v, page_bgr, inp_bgr, bboxes, types)
        print(f"\n===== {v.upper()} =====")
        print(f"b2 tilted detected: {res[v]['b2_tilted_detected']}")
        for pr in res[v]["per_region"]:
            print(f"  r{pr['id']} [{pr['type']:13s}] angle={pr['angle']:+6.2f} "
                  f"bbox={pr['bbox']} new_ink={pr['new_ink_px']}")
        print(f"total new ink: {res[v]['total_new_ink']}")
        print(f"render meta: {res[v]['render_stage_meta']}")

    # byte A/B
    t = pathlib.Path(res["tip"]["final_path"]).read_bytes()
    b = pathlib.Path(res["base"]["final_path"]).read_bytes()
    print(f"\nfinal byte-identical tip==base: {t == b} "
          f"(tip {len(t)}B, base {len(b)}B)")
    (HERE / "repro_result.json").write_text(json.dumps(
        {k: {kk: vv for kk, vv in v.items() if kk != "regions"}
         for k, v in res.items()}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
