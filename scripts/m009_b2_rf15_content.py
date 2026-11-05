#!/usr/bin/env python3
"""MANGABD-009 B2 RF-15 — anchored patch content (cells {11,12} only).

Patches:
  C11_P1  cell-11 V-3 wrapper: signature accepts fit_w/fit_h; fallback
          arm forwards them to the wrapped base (forward-only)
  C12_P1  cell-12 V-3 wrapper: same fix (this is the wrapper that the
          global name points at after Run All order 11 -> 12)
  C12_P2  cell-12 tail battery Test 20: exec-order integration — after
          the wrappers rebind, render_page on a quad-carrying synthetic
          page in the SAME namespace; asserts rendered>0 (h/t/v ink)
          and zero "unexpected keyword argument" events; hard-raises on
          failure (fail-on-current-bytes contract)
"""
# ── cell 11: V-3 wrapper — accept + forward the B2 quad-fit dims ──
C11_P1_OLD = """    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None):
        # MANGABD-009 B1 (C-1): fit_result forward-only threading। Vertical
        # arm অপরিবর্তিত — bubble_fill_decision এই predicate-এর region-গুলোকে
        # upstream-এই guard করে (guard "vertical_note"), তাই এখানে কখনোই
        # fit_result আসে না; fallback arm সেটা হুবহু নিচে পাঠায়।
        if text and str(text).strip() and w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0:
            b = bold if bold is not None else (region_type in ["sfx", "narrator"])
            return _qc_render_vertical(image_pil, text, x, y, w, h, b, (0,0,0), padding)
        return _base_render(image_pil, text, x, y, w, h, angle, region_type,
                            bold, stroke_width, text_color, padding, fit_result)"""

C11_P1_NEW = """    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None):
        # MANGABD-009 B1 (C-1): fit_result forward-only threading। Vertical
        # arm অপরিবর্তিত — bubble_fill_decision এই predicate-এর region-গুলোকে
        # upstream-এই guard করে (guard "vertical_note"), তাই এখানে কখনোই
        # fit_result আসে না; fallback arm সেটা হুবহু নিচে পাঠায়।
        # MANGABD-009 B2 RF-15: cell-10 render_page এখন quad-fit dims
        # fit_w/fit_h সব region-তেই পাঠায় (RB2-5; tilted হলে quad
        # extents, নাহলে None — কিন্তু kwarg সবসময় যায়)। wrapper-এর
        # signature-তে এগুলো না থাকলে call-time TypeError-এ প্রতিটা
        # region silently fail (Owner live: rendered=0, warnings=8,
        # blank final)। এখন নিচে fallback arm হুবহু forward করে।
        # Vertical arm-এ fit dims-এর প্রশ্ন নেই — predicate |angle|<=1.0
        # মানে render_page ওই call-এ fit_w/fit_h কখনোই set করে না
        # (হিসাব শুধু |angle|>1 হলে), আর vertical নিজেই fit করে।
        if text and str(text).strip() and w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0:
            b = bold if bold is not None else (region_type in ["sfx", "narrator"])
            return _qc_render_vertical(image_pil, text, x, y, w, h, b, (0,0,0), padding)
        return _base_render(image_pil, text, x, y, w, h, angle, region_type,
                            bold, stroke_width, text_color, padding, fit_result,
                            fit_w, fit_h)"""

# ── cell 12: V-3 wrapper — accept + forward the B2 quad-fit dims ──
C12_P1_OLD = """    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None):
        # MANGABD-009 B1 (C-1): fit_result forward-only threading। Vertical
        # arm অপরিবর্তিত — bubble_fill_decision এই predicate-এর region-গুলোকে
        # upstream-এই guard করে (guard "vertical_note"), তাই এখানে কখনোই
        # fit_result আসে না; fallback arm সেটা হুবহু নিচে পাঠায়।
        if text and str(text).strip() and w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0:
            b = bold if bold is not None else (region_type in ["sfx", "narrator"])
            return _qc_render_vertical(image_pil, text, x, y, w, h, b, (0, 0, 0), padding)
        return _qc_orig_render(image_pil, text, x, y, w, h, angle, region_type,
                               bold, stroke_width, text_color, padding, fit_result)"""

C12_P1_NEW = """    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None):
        # MANGABD-009 B1 (C-1): fit_result forward-only threading। Vertical
        # arm অপরিবর্তিত — bubble_fill_decision এই predicate-এর region-গুলোকে
        # upstream-এই guard করে (guard "vertical_note"), তাই এখানে কখনোই
        # fit_result আসে না; fallback arm সেটা হুবহু নিচে পাঠায়।
        # MANGABD-009 B2 RF-15: cell-10 render_page এখন quad-fit dims
        # fit_w/fit_h সব region-তেই পাঠায় (RB2-5; tilted হলে quad
        # extents, নাহলে None — কিন্তু kwarg সবসময় যায়)। wrapper-এর
        # signature-তে এগুলো না থাকলে call-time TypeError-এ প্রতিটা
        # region silently fail (Owner live: rendered=0, warnings=8,
        # blank final)। এখন নিচে fallback arm হুবহু forward করে।
        # Vertical arm-এ fit dims-এর প্রশ্ন নেই — predicate |angle|<=1.0
        # মানে render_page ওই call-এ fit_w/fit_h কখনোই set করে না
        # (হিসাব শুধু |angle|>1 হলে), আর vertical নিজেই fit করে।
        if text and str(text).strip() and w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0:
            b = bold if bold is not None else (region_type in ["sfx", "narrator"])
            return _qc_render_vertical(image_pil, text, x, y, w, h, b, (0, 0, 0), padding)
        return _qc_orig_render(image_pil, text, x, y, w, h, angle, region_type,
                               bold, stroke_width, text_color, padding, fit_result,
                               fit_w, fit_h)"""

# ── cell 12 tail: RF-15 integration battery (exec-order simulation) ──
C12_P2_OLD = """globals()["run_inpaint_render_all"] = run_inpaint_render_all

print("✅ QUALITY CORE active: box-snap + clean-box restore + vertical note + safe mask")"""

C12_P2_NEW = """globals()["run_inpaint_render_all"] = run_inpaint_render_all

# ── 7.6) MANGABD-009 B2 RF-15: full-chain render integration battery ──
# Owner live (2026-10-31): Run All-এর প্রথম full-chain 10→11→12→15-এ
# প্রতিটা region-এ "render_bengali_text() got an unexpected keyword
# argument 'fit_w'" — cell-10 render_page-এর quad-fit dims (RB2-5) এই
# wrapper-এ পৌঁছানোর আগেই call-time TypeError, প্রতিটা per-row except
# সেটা WARN হিসেবে গিলে ফেলে (rendered=0, warnings=8, blank final)।
# Cell-10 battery এটা ধরতে পারেনি — wrapper সেখানে এখনো bind হয়নি;
# chain test-গুলো wrapper-কে সরাসরি ডাকত। এই test-টাই সেই ফাঁক বন্ধ
# করে: wrapper rebind-এর পরে, একই namespace-এ, quad-carrying page-এ
# render_page চালিয়ে প্রমাণ করে rendered>0 (h/t/v তিন ক্লাসেই ink)
# এবং কোনো "unexpected keyword argument" event নেই। ব্যর্থ হলে
# hard-raise — নীরব blank final আর কখনোই নয়।
_t20_ok = False
try:
    _t20_pid = "__b2_rf15_t20__"
    _t20_canvas = np.full((760, 880, 3), 255, np.uint8)
    init_page(_t20_pid, width=880, height=760,
              image_np=_t20_canvas, overwrite=True)
    save_image_artifact(_t20_pid, "inpainted", _t20_canvas, quality=95)

    # ৩টা region class — RF-14 Test 19-এর geometry-ই: horizontal /
    # tilted(-12°, true quad) / vertical V-3। quad-carrying বলেই
    # render_page-এর fit_w/fit_h arm (RF-15-এর পুরো বিষয়) চালু হয়।
    _t20_quad2 = [[371, 96], [566, 54], [589, 164], [394, 206]]
    save_json_artifact(_t20_pid, "detections", [
        {"id": 1, "page_id": _t20_pid, "x": 60, "y": 80,
         "width": 200, "height": 90,
         "quad": [[60, 80], [260, 80], [260, 170], [60, 170]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
        {"id": 2, "page_id": _t20_pid, "x": 380, "y": 50,
         "width": 210, "height": 160,
         "quad": _t20_quad2,
         "angle": -12.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
        {"id": 3, "page_id": _t20_pid, "x": 660, "y": 200,
         "width": 60, "height": 240,
         "quad": [[660, 200], [720, 200], [720, 440], [660, 440]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
    ])
    mark_stage_done(_t20_pid, "detect", meta={"region_count": 3})

    def _t20_row(rid, x, y, w, h, angle):
        _row = {c: "" for c in TRANSLATION_DF_COLUMNS}
        _row.update({
            "page_id": _t20_pid, "page": _t20_pid, "id": int(rid),
            "region_type": "bubble",
            "detector_class": "text_bubble",
            "detector_score": 0.9, "parent_bubble_id": "",
            "x": int(x), "y": int(y),
            "width": int(w), "height": int(h),
            "angle": float(angle), "original_text": "テスト",
            "translated_text": "এই কী হয়েছে বলো তো?!", "confidence": 0.9,
            "ocr_engine": "t20", "is_english": True,
            "bengali_valid": False, "status": "ok",
            "reading_order": -1,
        })
        return _row

    upsert_translation_rows(_t20_pid, [
        _t20_row(1, 60, 80, 200, 90, 0.0),
        _t20_row(2, 380, 50, 210, 160, -12.0),
        _t20_row(3, 660, 200, 60, 240, 0.0),
    ])

    # THE seam: এই মুহূর্তে global render_bengali_text == এই cell-এর
    # wrapper (cell-11-এর wrapper-টাও নিচে bind হয়ে আছে) — render_page-এর
    # fit_w/fit_h kwargs এই চেইন দিয়েই গুজরে যেতে হবে
    _t20_ev0 = len(MANGABD_EVENTS)
    _t20_out = render_page(_t20_pid, force=True)
    _t20_typerr = sum(
        1 for _t20_e in MANGABD_EVENTS[_t20_ev0:]
        if "unexpected keyword argument" in str(_t20_e.get("message", ""))
    )
    _t20_inks = []
    for _t20_r in load_json_artifact(_t20_pid, "detections", default=[]):
        _x, _y = int(_t20_r["x"]), int(_t20_r["y"])
        _w, _h = int(_t20_r["width"]), int(_t20_r["height"])
        _roi = np.abs(
            _t20_out[_y:_y + _h, _x:_x + _w].astype(int)
            - _t20_canvas[_y:_y + _h, _x:_x + _w].astype(int)
        ).sum(axis=2)
        _t20_inks.append(int((_roi > 30).sum()))
    _t20_df = translation_df[translation_df["page_id"] == _t20_pid]
    _t20_rend = int((_t20_df["status"] == "rendered").sum())
    _t20_ok = (
        len(_t20_inks) == 3 and all(v >= 50 for v in _t20_inks)
        and _t20_typerr == 0 and _t20_rend == 3
    )

    run_test(
        "B2 RF-15: full-chain render integration (wrapper kwarg seam)",
        _t20_ok,
        f"inks(h/t/v)={_t20_inks} typerr={_t20_typerr} "
        f"rendered={_t20_rend}/3",
    )
except Exception as exc:
    run_test(
        "B2 RF-15: full-chain render integration (wrapper kwarg seam)",
        False,
        str(exc)[:160],
    )
finally:
    try:
        _t20_df2 = globals().get("translation_df")
        if _t20_df2 is not None and len(_t20_df2):
            _t20_keep = _t20_df2[
                _t20_df2["page_id"] != "__b2_rf15_t20__"
            ]
            globals()["translation_df"] = _t20_keep
            save_translation_df(_t20_keep)
        reset_page("__b2_rf15_t20__", delete_artifacts=True)
    except Exception:
        pass

if not _t20_ok:
    raise RuntimeError(
        "Cell 12 RF-15 integration battery failed: V-3 wrapper-গুলো "
        "render_page-এর fit_w/fit_h নিতে পারছে না — Run All-এ প্রতিটা "
        "region নীরবে blank হয়ে যায়। Fix করে তারপর পরের cell-এ যাও।"
    )

print("✅ QUALITY CORE active: box-snap + clean-box restore + vertical note + safe mask")"""
