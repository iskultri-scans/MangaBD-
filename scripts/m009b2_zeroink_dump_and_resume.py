#!/usr/bin/env python3
"""S6b (resume trap, clean check) + per-region DECISION DUMP (directive #2).

The dump wraps the verbatim tip render_page with a per-region observer:
angle/knob, quad lookup, fit dims, branch taken, paste box, exceptions —
captured WITHOUT modifying branch bytes (observer monkeypatches the env's
own function objects at runtime, outside the repo).
"""
import json
import sys
import pathlib
import numpy as np
import cv2
from PIL import Image as PILImage

HERE = pathlib.Path("/home/z/my-project/m009b2_repro")
sys.path.insert(0, str(HERE / "scripts"))
from b2_env import build_env  # noqa: E402
from repro_run import make_page, make_inpainted, build_rows  # noqa: E402


def main():
    page = make_page()
    page_bgr = cv2.cvtColor(np.asarray(PILImage.fromarray(page[0])),
                            cv2.COLOR_RGB2BGR)
    inp_bgr = make_inpainted(page[0], page[1])
    bboxes, types = page[1], page[2]
    pid = "page_01.jpg"

    ns = build_env("tip", HERE / "dump_env.log")
    ns["init_page"](pid, width=1100, height=1600, overwrite=True)
    ns["save_image_artifact"](pid, "original", page_bgr, quality=95)
    ns["save_image_artifact"](pid, "inpainted", inp_bgr, quality=95)

    # detection side (verbatim estimator) + artifact
    est = ns["_estimate_region_angle"]
    regions = []
    for i, ((x, y, w, h), rtype) in enumerate(zip(bboxes, types)):
        quad = np.array([[x, y], [x + w, y], [x + w, y + h], [x, y + h]],
                        dtype=np.int32)
        angle = 0.0
        a, q = est(page_bgr, x, y, w, h)
        if a != 0.0:
            angle = float(a)
            if q is not None:
                quad = np.round(np.asarray(q)).astype(np.int32)
        regions.append({"id": i + 1, "page_id": pid, "x": x, "y": y,
                        "width": w, "height": h, "quad": quad.tolist(),
                        "angle": angle, "region_type": rtype,
                        "detector_class": "synthetic",
                        "detector_score": 0.97,
                        "parent_bubble_id": None})
    ns["save_json_artifact"](pid, "detections", regions)
    ns["translation_df"] = ns["empty_translation_df"]()
    ns["upsert_translation_rows"](pid, build_rows(pid, regions))

    # ── per-region decision dump: wrap the env's own functions ──
    dump = []
    state = {"current": None}

    orig_rrt = ns["_render_rotated_text"]
    orig_rbt = ns["render_bengali_text"]
    orig_fit = ns["fit_font_size"]
    orig_est = ns["_estimate_region_angle"]
    orig_log = ns["log_event"]
    orig_rr = ns["_b2_render_angle"]

    def obs_rrt(image_pil, lines, font, x, y, w, h, angle, tc, sc, sw, lh,
                padding, bold=False, fit_w=None, fit_h=None):
        cw = int(fit_w) if fit_w is not None else int(w)
        ch = int(fit_h) if fit_h is not None else int(h)
        canvas_w = max(cw + 4 * (padding or 8), 200)
        canvas_h = max(ch + 4 * (padding or 8), 100)
        rot_w = canvas_w * abs(np.cos(np.radians(angle))) + \
            canvas_h * abs(np.sin(np.radians(angle)))
        rot_h = canvas_w * abs(np.sin(np.radians(angle))) + \
            canvas_h * abs(np.cos(np.radians(angle)))
        paste = (int(x + w // 2) - int(rot_w) // 2,
                 int(y + h // 2) - int(rot_h) // 2)
        state["current"].update({
            "branch": "rotated", "fit_w": fit_w, "fit_h": fit_h,
            "canvas": [canvas_w, canvas_h], "angle": angle,
            "rotated_wh_approx": [int(rot_w), int(rot_h)],
            "paste_xy": list(paste),
            "on_page": bool(paste[0] < 1100 and paste[1] < 1600),
        })
        return orig_rrt(image_pil, lines, font, x, y, w, h, angle, tc, sc,
                        sw, lh, padding, bold=bold, fit_w=fit_w, fit_h=fit_h)

    def obs_rbt(image_pil, text, x, y, w, h, angle=0.0, **kw):
        state["current"].update({
            "call": "render_bengali_text", "text_head": str(text)[:24],
            "bbox": [x, y, w, h], "angle_in": angle,
        })
        return orig_rbt(image_pil, text, x, y, w, h, angle=angle, **kw)

    def obs_fit(text, tw, th, **kw):
        r = orig_fit(text, tw, th, **kw)
        state["current"].update({
            "fit_target": [tw, th], "font_size": r[0], "n_lines": len(r[1]),
        })
        return r

    def obs_est(image_bgr, x, y, w, h):
        r = orig_est(image_bgr, x, y, w, h)
        state["current"].update({"est_angle": r[0],
                                 "est_quad": "Y" if r[1] else "N"})
        return r

    def obs_rra(raw):
        r = orig_rr(raw)
        state["current"].update({"raw_angle": float(raw), "knob_angle": r})
        return r

    def obs_log(msg, level="INFO", **kw):
        if state["current"] is not None and level in ("WARN", "ERROR"):
            state["current"].setdefault("events", []).append(
                f"{level}: {str(msg)[:120]}")
        return orig_log(msg, level=level, **kw)

    ns["_render_rotated_text"] = obs_rrt
    ns["render_bengali_text"] = obs_rbt
    ns["fit_font_size"] = obs_fit
    ns["_estimate_region_angle"] = obs_est
    ns["_b2_render_angle"] = obs_rra
    ns["log_event"] = obs_log

    # drive the per-region loop manually to scope `current`
    df = ns["translation_df"]
    page_rows = df[df["page_id"] == pid].sort_values("id")
    b2q = {}
    for qr in ns["load_json_artifact"](pid, "detections", default=[]):
        b2q[int(qr.get("id", -1))] = qr.get("quad")
    canvas = PILImage.fromarray(
        cv2.cvtColor(inp_bgr, cv2.COLOR_BGR2RGB)).copy()
    MANGABD_CONFIG = ns["MANGABD_CONFIG"]

    for _, row in page_rows.iterrows():
        rid = int(row.get("id", 0))
        state["current"] = {"region_id": rid}
        entry = state["current"]
        x, y = int(row.get("x", 0)), int(row.get("y", 0))
        w, h = int(row.get("width", 0)), int(row.get("height", 0))
        angle = ns["_b2_render_angle"](row.get("angle", 0.0))
        fit_w = fit_h = None
        if abs(angle) > 1.0:
            q = np.asarray(b2q.get(rid) or [], dtype=np.float64)
            entry["quad_shape"] = list(q.shape)
            if q.shape == (4, 2):
                fit_w = int(round(max(
                    float(np.linalg.norm(q[0] - q[1])),
                    float(np.linalg.norm(q[2] - q[3])))))
                fit_h = int(round(max(
                    float(np.linalg.norm(q[0] - q[3])),
                    float(np.linalg.norm(q[1] - q[2])))))
                entry["quad_dims_fit"] = [fit_w, fit_h]
                if fit_w < 5 or fit_h < 5:
                    entry["quad_guard"] = "fit<5 -> None"
                    fit_w = fit_h = None
        entry["fit_dims_used"] = [fit_w, fit_h]
        txt = str(row.get("translated_text", "")).strip()
        entry["text_head"] = txt[:18]
        try:
            canvas = ns["render_bengali_text"](
                canvas, txt, x, y, w, h, angle=angle,
                region_type=str(row.get("region_type", "overlay")),
                text_color=(0, 0, 0), stroke_width=None,
                fit_w=fit_w, fit_h=fit_h)
            entry["status"] = "rendered"
        except Exception as exc:
            entry["status"] = "EXCEPTION"
            entry["exception"] = repr(exc)[:200]
        dump.append(dict(entry))
        state["current"] = None

    print(json.dumps(dump, indent=2, ensure_ascii=False))
    (HERE / "region_dump.json").write_text(
        json.dumps(dump, indent=2, ensure_ascii=False))

    # ── S6b: resume trap, clean check ──
    ns["save_image_artifact"](pid, "final", np.full_like(inp_bgr, 255),
                              quality=100)
    ns["mark_stage_done"](pid, "render", meta={"sim": "blank"})
    final = ns["render_page"](pid)   # force=False -> expect CACHE hit
    arr = np.asarray(final.convert("L")) if isinstance(
        final, PILImage.Image) else cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
    s6 = {
        "returned_mean_brightness": round(float(arr.mean()), 3),
        "is_blank_white": bool(arr.mean() > 253),
        "stage_meta": ns["MANGABD_MANIFEST"]["pages"][pid]["stages"].get(
            "render"),
    }
    print("S6b resume-trap:", json.dumps(s6))
    (HERE / "s6b_result.json").write_text(json.dumps(s6, indent=2))


if __name__ == "__main__":
    main()
