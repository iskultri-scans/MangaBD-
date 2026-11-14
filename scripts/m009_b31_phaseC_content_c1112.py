#!/usr/bin/env python3
r"""MANGABD-009 B3.1 Phase C — cells 11/12 patch content.

Wrapper threading per the RF-15 forwarding law (the B3 ink_color
pattern): signatures gain line_colors=None; the fallback (horizontal)
arm forwards it; the V-3 vertical arm ACCEPTS but never consumes it
(RB31-5 — the vertical render path stays hardcoded black; the Phase A
draft's vertical per-column coloring half was REJECTED by the ruling).
Self-checks: cell 11 7.5c (wrapper arms), cell 12 7.7b (full chain
through render_page — horizontal per-line red, tilted per-line red,
vertical-with-key BLACK, keyless vertical black, 0 TypeError).
"""

# ── C11-P1: wrapper signature (cell 11) ───────────────────────────────
C11_P1_OLD = '''    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None, ink_color=None):'''
C11_P1_NEW = '''    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None, ink_color=None,
                            line_colors=None):'''

# ── C11-P2: vertical arm ignores line_colors (RB31-5) + forward ──────
C11_P2_OLD = '''            return _qc_render_vertical(image_pil, text, x, y, w, h, b,
                                       tuple(ink_color) if ink_color is not None else (0,0,0),
                                       padding)
        return _base_render(image_pil, text, x, y, w, h, angle, region_type,
                            bold, stroke_width, text_color, padding, fit_result,
                            fit_w, fit_h, ink_color=ink_color)'''
C11_P2_NEW = '''            # MANGABD-009 B3.1 (RB31-5): line_colors vertical arm-এ
            # consume হয় না — V-3 hardcoded black আইন বহাল (ruling-এ
            # Phase A draft-এর vertical per-column coloring বাতিল);
            # kwarg শুধু accept — TypeError-মুক্ত signature।
            return _qc_render_vertical(image_pil, text, x, y, w, h, b,
                                       tuple(ink_color) if ink_color is not None else (0,0,0),
                                       padding)
        return _base_render(image_pil, text, x, y, w, h, angle, region_type,
                            bold, stroke_width, text_color, padding, fit_result,
                            fit_w, fit_h, ink_color=ink_color,
                            line_colors=line_colors)'''

# ── C11-P3: 7.5c wrapper line_colors self-check ──────────────────────
C11_P3_OLD = '''if not _m9b3_ok:
    raise RuntimeError(
        "Cell 11 B3 ink_color check failed: wrapper-এর vertical arm "
        "ink_color নিচ্ছে না / None-path বদলে গেছে / fallback kwarg "
        "forward হচ্ছে না। Fix করে তারপর পরের cell-এ যাও।"
    )

# ── 8) pipeline wrap ──'''
C11_P3_NEW = '''if not _m9b3_ok:
    raise RuntimeError(
        "Cell 11 B3 ink_color check failed: wrapper-এর vertical arm "
        "ink_color নিচ্ছে না / None-path বদলে গেছে / fallback kwarg "
        "forward হচ্ছে না। Fix করে তারপর পরের cell-ে যাও।"
    )

# ── 7.5c) MANGABD-009 B3.1: wrapper line_colors threading (RB31-3/5) ──
# line_colors kwarg-এর দুই দিক: fallback arm base-এ forward করে
# (per-line apply ওখানে), vertical arm accept করে কিন্তু consume করে
# না (RB31-5 — V-3 hardcoded black)।
_m9b31_ok = False
try:
    # horizontal fallback arm: forward → line0 red, rest black
    _m9b31_ch = PILImage.new("RGB", (400, 600), (255, 255, 255))
    render_bengali_text(_m9b31_ch, "লাল লাইন এখানে আর কালো লাইন এখানে",
                        20, 40, 240, 90, region_type="bubble",
                        text_color=(0, 0, 0),
                        line_colors=[(200, 30, 30), None])
    _m9b31_a = np.array(_m9b31_ch).astype(int)
    _m9b31_red_h = int((np.abs(_m9b31_a - [200, 30, 30])
                        .sum(axis=2) < 90).sum())
    _m9b31_black_h = int((np.abs(_m9b31_a - [0, 0, 0])
                          .sum(axis=2) < 90).sum())
    # vertical arm: line_colors থাকলেও hardcoded black (RB31-5)
    _m9b31_cv = PILImage.new("RGB", (400, 600), (255, 255, 255))
    render_bengali_text(_m9b31_cv, "নোট", 20, 40, 60, 300,
                        region_type="bubble", text_color=(0, 0, 0),
                        line_colors=[(200, 30, 30)])
    _m9b31_a2 = np.array(_m9b31_cv).astype(int)
    _m9b31_red_v = int((np.abs(_m9b31_a2 - [200, 30, 30])
                        .sum(axis=2) < 90).sum())
    _m9b31_black_v = int((np.abs(_m9b31_a2 - [0, 0, 0])
                          .sum(axis=2) < 90).sum())
    _m9b31_ok = (_m9b31_red_h >= 40 and _m9b31_black_h >= 40
                 and _m9b31_red_v == 0 and _m9b31_black_v >= 40)
except Exception as _m9b31_exc:
    print(f"     {_m9b31_exc}")
    _m9b31_ok = False
print(("  ✅ " if _m9b31_ok else "  ❌ ")
      + "B3.1 wrapper line_colors threading (fallback per-line + "
        "vertical ignores — RB31-5)")
if not _m9b31_ok:
    raise RuntimeError(
        "Cell 11 B3.1 line_colors check failed: fallback arm per-line "
        "রঙ নিচ্ছে না / vertical arm line_colors consume করছে (RB31-5 "
        "ভাঙছে)। Fix করে তারপর পরের cell-এ যাও।"
    )

# ── 8) pipeline wrap ──'''

# ── C12-P1: wrapper signature (cell 12) ───────────────────────────────
C12_P1_OLD = '''    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None, ink_color=None):'''
C12_P1_NEW = '''    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None, ink_color=None,
                            line_colors=None):'''

# ── C12-P2: vertical arm ignores line_colors (RB31-5) + forward ──────
C12_P2_OLD = '''            return _qc_render_vertical(image_pil, text, x, y, w, h, b,
                                       tuple(ink_color) if ink_color is not None else (0, 0, 0),
                                       padding)
        return _qc_orig_render(image_pil, text, x, y, w, h, angle, region_type,
                               bold, stroke_width, text_color, padding, fit_result,
                               fit_w, fit_h, ink_color=ink_color)'''
C12_P2_NEW = '''            # MANGABD-009 B3.1 (RB31-5): line_colors vertical arm-এ
            # consume হয় না — V-3 hardcoded black আইন বহাল; kwarg
            # শুধু accept (TypeError-মুক্ত signature)।
            return _qc_render_vertical(image_pil, text, x, y, w, h, b,
                                       tuple(ink_color) if ink_color is not None else (0, 0, 0),
                                       padding)
        return _qc_orig_render(image_pil, text, x, y, w, h, angle, region_type,
                               bold, stroke_width, text_color, padding, fit_result,
                               fit_w, fit_h, ink_color=ink_color,
                               line_colors=line_colors)'''

# ── C12-P3: 7.7b line_colors full-chain integration ──────────────────
C12_P3_OLD = '''if not _b3c_ok:
    raise RuntimeError(
        "Cell 12 B3 ink-color chain failed: render_page-এর ink_color "
        "kwarg wrapper-চেইন দিয়ে যাচ্ছে না / vertical arm রঙ নিচ্ছে "
        "না / keyless vertical বদলে গেছে। Fix করে তারপর পরের cell-এ যাও।"
    )

print("✅ QUALITY CORE active: box-snap + clean-box restore + vertical note + safe mask")'''

C12_P3_NEW = '''if not _b3c_ok:
    raise RuntimeError(
        "Cell 12 B3 ink-color chain failed: render_page-এর ink_color "
        "kwarg wrapper-চেইন দিয়ে যাচ্ছে না / vertical arm রঙ নিচ্ছে "
        "না / keyless vertical বদলে গেছে। Fix করে তারপর পরের cell-এ যাও।"
    )

# ── 7.7b) MANGABD-009 B3.1: line_colors full-chain integration ──
# Test 20/7.7-এর একই আইন, নতুন kwarg-এ: render_page-এর line_colors
# এই wrapper-চেইন দিয়ে গুজরে যায় (RF-15 seam)। চারটা region:
# colored horizontal (line0 red), colored tilted 14° (line0 red —
# rotated canvas-এ per-line), vertical + line_colors (BLACK — RB31-5:
# vertical arm consume করে না), keyless vertical (আগের exact black)।
# zero TypeError, চারটাতেই render।
_b31c_ok = False
try:
    _b31c_pid = "__b31_chain__"
    _b31c_canvas = np.full((760, 940, 3), 255, np.uint8)
    init_page(_b31c_pid, width=940, height=760,
              image_np=_b31c_canvas, overwrite=True)
    save_image_artifact(_b31c_pid, "inpainted", _b31c_canvas, quality=95)
    _b31c_t = np.radians(14.0)
    _b31c_u = np.array([np.cos(_b31c_t), np.sin(_b31c_t)])
    _b31c_v = np.array([-np.sin(_b31c_t), np.cos(_b31c_t)])
    _b31c_c = np.array([480.0, 150.0])
    _b31c_hw, _b31c_hh = 100.0, 70.0
    _b31c_quad = [[round(float(p[0]), 2), round(float(p[1]), 2)]
                  for p in (_b31c_c - _b31c_hw * _b31c_u - _b31c_hh * _b31c_v,
                            _b31c_c + _b31c_hw * _b31c_u - _b31c_hh * _b31c_v,
                            _b31c_c + _b31c_hw * _b31c_u + _b31c_hh * _b31c_v,
                            _b31c_c - _b31c_hw * _b31c_u + _b31c_hh * _b31c_v)]
    save_json_artifact(_b31c_pid, "detections", [
        {"id": 1, "page_id": _b31c_pid, "x": 60, "y": 80,
         "width": 200, "height": 90,
         "quad": [[60, 80], [260, 80], [260, 170], [60, 170]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None,
         "line_colors": [[200, 30, 30], None]},
        {"id": 2, "page_id": _b31c_pid, "x": 380, "y": 80,
         "width": 200, "height": 140,
         "quad": _b31c_quad,
         "angle": -14.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None,
         "line_colors": [[200, 30, 30], None]},
        {"id": 3, "page_id": _b31c_pid, "x": 660, "y": 60,
         "width": 60, "height": 300,
         "quad": [[660, 60], [720, 60], [720, 360], [660, 360]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None,
         "line_colors": [[200, 30, 30]]},
        {"id": 4, "page_id": _b31c_pid, "x": 800, "y": 60,
         "width": 60, "height": 300,
         "quad": [[800, 60], [860, 60], [860, 360], [800, 360]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
    ])
    mark_stage_done(_b31c_pid, "detect", meta={"region_count": 4})

    def _b31c_row(rid, x, y, w, h, angle=0.0):
        _row = {c: "" for c in TRANSLATION_DF_COLUMNS}
        _row.update({
            "page_id": _b31c_pid, "page": _b31c_pid, "id": int(rid),
            "region_type": "bubble",
            "detector_class": "text_bubble",
            "detector_score": 0.9, "parent_bubble_id": "",
            "x": int(x), "y": int(y),
            "width": int(w), "height": int(h),
            "angle": float(angle), "original_text": "テスト",
            "translated_text": "এই লাল লাইনটি আর এই কালো লাইনটি",
            "confidence": 0.9, "ocr_engine": "b31c",
            "is_english": True, "bengali_valid": False,
            "status": "ok", "reading_order": -1,
        })
        return _row

    upsert_translation_rows(_b31c_pid, [
        _b31c_row(1, 60, 80, 200, 90),
        _b31c_row(2, 380, 80, 200, 140, -14.0),
        _b31c_row(3, 660, 60, 60, 300),
        _b31c_row(4, 800, 60, 60, 300),
    ])

    _b31c_ev0 = len(MANGABD_EVENTS)
    _b31c_out = render_page(_b31c_pid, force=True)
    _b31c_typerr = sum(
        1 for _b31c_e in MANGABD_EVENTS[_b31c_ev0:]
        if "unexpected keyword argument" in str(_b31c_e.get("message", ""))
    )
    _b31c_reds, _b31c_blacks = [0, 0, 0, 0], [0, 0, 0, 0]
    for _b31c_rid, (_b31c_x, _b31c_y, _b31c_w, _b31c_h) in (
            (1, (60, 80, 200, 90)), (2, (330, 20, 300, 260)),
            (3, (660, 60, 60, 300)), (4, (800, 60, 60, 300))):
        _b31c_roi = _b31c_out[_b31c_y:_b31c_y + _b31c_h,
                              _b31c_x:_b31c_x + _b31c_w].astype(int)
        _b31c_i = _b31c_rid - 1
        _b31c_reds[_b31c_i] = int((np.abs(
            _b31c_roi - [30, 30, 200]).sum(axis=2) < 90).sum())
        _b31c_blacks[_b31c_i] = int((np.abs(
            _b31c_roi - [0, 0, 0]).sum(axis=2) < 90).sum())
    _b31c_df = translation_df[translation_df["page_id"] == _b31c_pid]
    _b31c_rend = int((_b31c_df["status"] == "rendered").sum())
    _b31c_ok = (_b31c_typerr == 0 and _b31c_rend == 4
                and _b31c_reds[0] >= 40 and _b31c_blacks[0] >= 20
                and _b31c_reds[1] >= 40 and _b31c_blacks[1] >= 20
                and _b31c_reds[2] == 0 and _b31c_blacks[2] >= 40
                and _b31c_reds[3] == 0 and _b31c_blacks[3] >= 40)
    print(("  ✅ " if _b31c_ok else "  ❌ ")
          + "B3.1 line_colors full-chain integration "
          + f"(red h/tilt={_b31c_reds[:2]} v-with-key red="
          + f"{_b31c_reds[2]} keyless-v black={_b31c_blacks[3]} "
          + f"typerr={_b31c_typerr} rendered={_b31c_rend}/4)")
except Exception as _b31c_exc:
    print(f"     {_b31c_exc}")
    _b31c_ok = False
finally:
    try:
        _b31c_df2 = globals().get("translation_df")
        if _b31c_df2 is not None and len(_b31c_df2):
            _b31c_keep = _b31c_df2[_b31c_df2["page_id"] != "__b31_chain__"]
            globals()["translation_df"] = _b31c_keep
            save_translation_df(_b31c_keep)
        reset_page("__b31_chain__", delete_artifacts=True)
    except Exception:
        pass

if not _b31c_ok:
    raise RuntimeError(
        "Cell 12 B3.1 line_colors chain failed: render_page-এর "
        "line_colors kwarg wrapper-চেইন দিয়ে যাচ্ছে না / tilted "
        "per-line নেয় না / vertical arm line_colors consume করছে "
        "(RB31-5 ভাঙছে)। Fix করে তারপর পরের cell-এ যাও।"
    )

print("✅ QUALITY CORE active: box-snap + clean-box restore + vertical note + safe mask")'''
