#!/usr/bin/env python3
r"""MANGABD-009 B1 Phase C — patch content, part 2 (cell 10: renderer + render_page + battery)."""

# ── P5: render_bengali_text — fit_result param + conditional fit ─────
C10_RUNSIG_OLD = """def render_bengali_text(
    image_pil,
    text,
    x,
    y,
    w,
    h,
    angle=0.0,
    region_type="bubble",
    bold=None,
    stroke_width=None,
    text_color=None,
    padding=None,
):
    \"\"\"
    PIL image-এ Bengali text render করে।
    \"\"\"

    if not text or not str(text).strip():
        return image_pil

    cfg = MANGABD_CONFIG["rendering"]

    if bold is None:
        bold = region_type in ["sfx", "narrator"]

    if stroke_width is None:
        stroke_width = choose_stroke_width(region_type)

    font_size, lines, _ = fit_font_size(
        text,
        w,
        h,
        bold=bold,
        padding=padding,
    )"""

C10_RUNSIG_NEW = """def render_bengali_text(
    image_pil,
    text,
    x,
    y,
    w,
    h,
    angle=0.0,
    region_type="bubble",
    bold=None,
    stroke_width=None,
    text_color=None,
    padding=None,
    fit_result=None,
):
    \"\"\"
    PIL image-এ Bengali text render করে।

    MANGABD-009 B1: fit_result = bubble_fill_decision()-এর mode-"mask" ফল।
    None হলে (সব kept-current region + আগের সব caller) আগের exact
    fit_font_size path-ই চলে — rendered bytes অপরিবর্তিত।
    \"\"\"

    if not text or not str(text).strip():
        return image_pil

    cfg = MANGABD_CONFIG["rendering"]

    if bold is None:
        bold = region_type in ["sfx", "narrator"]

    if stroke_width is None:
        stroke_width = choose_stroke_width(region_type)

    # B1 defensive gate: mask layout শুধু horizontal path-এ, শুধু বৈধ
    # mode-"mask" dict-এ। rotated call বা ভাঙা dict হলে নীরবে নয় —
    # আগের current path-এ ফিরে যায় (trigger-guard এগুলো কখনো পাঠায় না)।
    if fit_result is not None and (
        not isinstance(fit_result, dict)
        or fit_result.get("mode") != "mask"
        or abs(float(angle)) > 1.0
    ):
        fit_result = None

    if fit_result is not None:
        font_size = int(fit_result["font_size"])
        lines = list(fit_result["lines"])
    else:
        font_size, lines, _ = fit_font_size(
            text,
            w,
            h,
            bold=bold,
            padding=padding,
        )"""

# ── P6: render_bengali_text — mask-mode positioning ───────────────────
C10_RUNPOS_OLD = """    total_text_height = line_height * len(lines)

    if padding is None:
        padding_ratio = float(cfg.get("padding_ratio", 0.08))
        padding = max(4, int(min(w, h) * padding_ratio))

    vertical_center = int(y + (h - total_text_height) // 2)
    start_y = max(int(y) + padding, vertical_center)"""

C10_RUNPOS_NEW = """    total_text_height = line_height * len(lines)

    if padding is None:
        padding_ratio = float(cfg.get("padding_ratio", 0.08))
        padding = max(4, int(min(w, h) * padding_ratio))

    if fit_result is not None:
        # B1 mask-aware positioning: ব্লকের top = usable extent-এ center করা
        # band block (bubble_fill_decision হিসাব করেছে), প্রতিটা line নিজ
        # band-এর span-center-এ। fit_font_size-এর bbox-centering এখানে নয়।
        start_y = int(fit_result["start_y"])
        band_centers = list(fit_result.get("band_centers") or [])
        band_widths = list(fit_result.get("band_widths") or [])
    else:
        vertical_center = int(y + (h - total_text_height) // 2)
        start_y = max(int(y) + padding, vertical_center)"""

# ── P7: _draw_runs_horizontal — center_x param (B1 band centering) ───
C10_FBX_OLD = """def _draw_runs_horizontal(
    draw, line, x, w, line_y, font, bold, text_color,
    stroke_color, stroke_width, padding,
):"""

C10_FBX_NEW = """def _draw_runs_horizontal(
    draw, line, x, w, line_y, font, bold, text_color,
    stroke_color, stroke_width, padding, center_x=None,
):"""

C10_FBPEN_OLD = """    pen_x = int(x + (int(w) - int(total)) // 2)"""

C10_FBPEN_NEW = """    if center_x is not None:
        # MANGABD-009 B1: mask-aware mode — run-sequence নিজ band-এর
        # span-center-এ বসে; x/w তখন ladder-এর band-width বাক্স মাত্র
        pen_x = int(center_x) - int(total) // 2
    else:
        pen_x = int(x + (int(w) - int(total)) // 2)"""

# ── P8: render_bengali_text draw loop — band centering + fb box ──────
C10_LOOP_OLD = """    for i, line in enumerate(lines):
        line_width, _ = measure_text(line, font, draw)

        line_x = int(x + (w - line_width) // 2)
        line_y = int(start_y + i * line_height)

        if _needs_fb and any(not _main_font_ok(ch) for ch in line):
            _draw_runs_horizontal(
                draw, line, x, w, line_y, font, bold,
                text_color, stroke_color, stroke_width, padding,
            )
            continue"""

C10_LOOP_NEW = """    for i, line in enumerate(lines):
        line_width, _ = measure_text(line, font, draw)

        if fit_result is not None:
            _b1_c = (band_centers[i]
                     if i < len(band_centers) else int(x + w // 2))
            _b1_bw = (band_widths[i]
                      if i < len(band_widths) else int(w))
            line_x = int(_b1_c - line_width // 2)
        else:
            _b1_c, _b1_bw = None, int(w)
            line_x = int(x + (w - line_width) // 2)
        line_y = int(start_y + i * line_height)

        if _needs_fb and any(not _main_font_ok(ch) for ch in line):
            _draw_runs_horizontal(
                draw, line, x, _b1_bw, line_y, font, bold,
                text_color, stroke_color, stroke_width, padding,
                center_x=_b1_c,
            )
            continue"""

# ── P9: render_page — B1 context (gray once per page) ────────────────
C10_RPCTX_OLD = """    # Canvas
    inpainted_rgb = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
    canvas_pil = PILImage.fromarray(inpainted_rgb).copy()"""

C10_RPCTX_NEW = """    # Canvas
    inpainted_rgb = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2RGB)
    canvas_pil = PILImage.fromarray(inpainted_rgb).copy()

    # MANGABD-009 B1: smart-fill context। Mask source = এই inpainted
    # canvas-ই (render যার উপরে আঁকে) — আলাদা I/O শূন্য; gray একবারই।
    bf_cfg = MANGABD_CONFIG["rendering"]
    bf_enabled = bool(bf_cfg.get("bubble_fill_enable", True))
    bf_gray = None
    bf_regions = {}
    if bf_enabled:
        try:
            bf_gray = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2GRAY)
        except Exception:
            bf_gray = inpainted_bgr"""

# ── P10: render_page region loop — decision + fit_result threading ───
C10_RPLOOP_OLD = """            bold = region_type in ["sfx", "narrator"]

            stroke_width = choose_stroke_width(region_type)

            # Font size tracking
            estimated_size, _, _ = fit_font_size(
                translated_text,
                w,
                h,
                bold=bold,
            )

            font_sizes_used.append(estimated_size)

            canvas_pil = render_bengali_text(
                canvas_pil,
                translated_text,
                x,
                y,
                w,
                h,
                angle=angle,
                region_type=region_type,
                bold=bold,
                stroke_width=stroke_width,
                text_color=text_color,
            )"""

C10_RPLOOP_NEW = """            bold = region_type in ["sfx", "narrator"]

            stroke_width = choose_stroke_width(region_type)

            # MANGABD-009 B1: smart-fill সিদ্ধান্ত (disabled / rotated /
            # vertical_note / অন্য region_type হলে নিজেই mode "current"
            # ফেরে — কোনো mask হিসাব হয় না)। mode "mask" হলে সেই layout
            # render_bengali_text-এ যায়; "current" হলে fit_result None —
            # ভেতরের fit_font_size call হুবহু আগের মতোই চলে।
            bf_decision = None
            if bf_enabled:
                try:
                    bf_decision = bubble_fill_decision(
                        translated_text,
                        x,
                        y,
                        w,
                        h,
                        image_gray=bf_gray,
                        bold=bold,
                        angle=angle,
                        region_type=region_type,
                    )
                except Exception as exc:
                    warning_count += 1
                    log_event(
                        f"Bubble fill decision failed [{page_id}:{region_id}]:"
                        f" {str(exc)[:120]} — current path",
                        level="WARN",
                    )
                    bf_decision = None

            bf_fit = None
            if bf_decision is not None:
                bf_regions[region_id] = {
                    k: bf_decision.get(k)
                    for k in ("mode", "guard", "cur_size", "font_size",
                              "cur_block_fill_usable", "block_fill_usable",
                              "cap_bound", "margin_px")
                }
                if bf_decision.get("mode") == "mask":
                    bf_fit = bf_decision
                    est_size = int(bf_decision["font_size"])
                else:
                    est_size = bf_decision.get("cur_size")
            else:
                est_size = None

            if est_size is None:
                # Font size tracking (B1 বন্ধ / exception — আগের মতোই)
                estimated_size, _, _ = fit_font_size(
                    translated_text,
                    w,
                    h,
                    bold=bold,
                )
                est_size = estimated_size

            font_sizes_used.append(int(est_size))

            canvas_pil = render_bengali_text(
                canvas_pil,
                translated_text,
                x,
                y,
                w,
                h,
                angle=angle,
                region_type=region_type,
                bold=bold,
                stroke_width=stroke_width,
                text_color=text_color,
                fit_result=bf_fit,
            )"""

# ── P11: render_page meta — B1 disclosure (Ruling 4) ──────────────────
C10_META_OLD = """    meta = {
        "rendered_regions": rendered_count,
        "skipped_regions": skipped_count,
        "render_warnings": warning_count,
    }"""

C10_META_NEW = """    meta = {
        "rendered_regions": rendered_count,
        "skipped_regions": skipped_count,
        "render_warnings": warning_count,
    }

    # MANGABD-009 B1: per-region smart-fill disclosure (Ruling 4 —
    # cap_bound honest fallback; trigger-guard regions kept-current স্পষ্ট)
    if bf_enabled:
        meta["bubble_fill"] = {
            "enabled": True,
            "mask_regions": sum(
                1 for v in bf_regions.values() if v.get("mode") == "mask"
            ),
            "kept_current": sum(
                1 for v in bf_regions.values() if v.get("mode") != "mask"
            ),
            "regions": bf_regions,
        }"""

# ── P12: battery — Tests 13/14/15 (B1 + N-1) ─────────────────────────
C10_BATT_OLD = """# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।"""

C10_BATT_NEW = """# ── MANGABD-009 B1: smart bubble fill self-tests ──
# Phase A (d394947) M9-A.1.4 + ruling: trigger 0.60, cap 48, target 0.85
# maximization-goal। Test 13 synthetic worst-case ধরে (ছোট text, বড়
# 380x320 ellipse — Owner-complaint class): trigger অবশ্যই লাগে, mask mode
# চালু হয়, cap 48-এ ভরাট না-বাড়াটা cap_bound disclosure হিসেবে স্পষ্ট থাকে
# (Ruling 4: honest fallback), আর render করা কালি bubble-এর ভেতরেই থাকে।

# Test 13: B1 mask fill — synthetic ellipse (decision + containment render)
try:
    _bf_w, _bf_h = 380, 320
    _bf_img = np.full((_bf_h + 40, _bf_w + 40, 3), 255, dtype=np.uint8)
    cv2.ellipse(
        _bf_img, (_bf_w // 2 + 20, _bf_h // 2 + 20),
        (_bf_w // 2, _bf_h // 2), 0, 0, 360, (0, 0, 0), 3,
    )
    _bf_gray = cv2.cvtColor(_bf_img, cv2.COLOR_BGR2GRAY)
    _bf_dec = bubble_fill_decision(
        "কী হয়েছে?", 20, 20, _bf_w, _bf_h,
        image_gray=_bf_gray, bold=False, angle=0.0, region_type="bubble",
    )
    _bf_ok = (
        _bf_dec.get("mode") == "mask"
        and _bf_dec.get("font_size", 0) >= _bf_dec.get("cur_size", 10 ** 6)
        and _bf_dec.get("cur_block_fill_usable", 1.0) < 0.60
        and isinstance(_bf_dec.get("cap_bound"), bool)
    )
    _bf_detail = (
        f"mode={_bf_dec.get('mode')} guard={_bf_dec.get('guard')} "
        f"cur={_bf_dec.get('cur_size')}px blkU={_bf_dec.get('cur_block_fill_usable')} "
        f"-> new={_bf_dec.get('font_size')}px blkU={_bf_dec.get('block_fill_usable')} "
        f"cap_bound={_bf_dec.get('cap_bound')}"
    )
    if _bf_ok:
        _bf_mm = _bubble_interior_mask(_bf_gray, 20, 20, _bf_w, _bf_h)
        _bf_bub = _bf_mm[0]
        _bf_ren = render_bengali_text(
            PILImage.fromarray(cv2.cvtColor(_bf_img, cv2.COLOR_BGR2RGB)),
            "কী হয়েছে?", 20, 20, _bf_w, _bf_h,
            region_type="bubble", text_color=(0, 0, 0), stroke_width=0,
            fit_result=_bf_dec,
        )
        _bf_arr = cv2.cvtColor(np.array(_bf_ren), cv2.COLOR_RGB2BGR)
        _bf_diff = np.any(_bf_arr != _bf_img, axis=2)
        _bf_leak = int((_bf_diff & ~_bf_bub).sum())
        _bf_inside = int((_bf_diff & _bf_bub).sum())
        _bf_ok = (_bf_leak == 0) and (_bf_inside > 0)
        _bf_detail += f" | ink inside={_bf_inside} leak={_bf_leak}"
    run_test("B1 mask fill: synthetic ellipse (decision+render)", _bf_ok,
             _bf_detail)
except Exception as exc:
    run_test("B1 mask fill: synthetic ellipse (decision+render)", False,
             str(exc)[:160])


# Test 14: B1 guards — trigger-এর উপরের region আর kill-switch দুটোই
# EXACT current layout পায় (mode "current", কোনো mask হিসাব নয়)।
# trigger খুব নিচে নামালে (0.05) ellipse-এর current blkU (~0.14) তার
# উপরেই — সেই guard-ই ধরবে; enable=False হলে প্রথম guard-ই "disabled"।
try:
    _bg_img = np.full((360, 420, 3), 255, dtype=np.uint8)
    cv2.ellipse(_bg_img, (210, 180), (190, 160), 0, 0, 360, (0, 0, 0), 3)
    _bg_gray = cv2.cvtColor(_bg_img, cv2.COLOR_BGR2GRAY)
    _bg_trig = MANGABD_CONFIG["rendering"].get(
        "bubble_fill_trigger", "ABSENT")
    _bg_en = MANGABD_CONFIG["rendering"].get(
        "bubble_fill_enable", "ABSENT")
    try:
        MANGABD_CONFIG["rendering"]["bubble_fill_trigger"] = 0.05
        _bg_d1 = bubble_fill_decision(
            "কী হয়েছে?", 20, 20, 380, 320,
            image_gray=_bg_gray, bold=False, angle=0.0, region_type="bubble",
        )
        _bg_trig_ok = (
            _bg_d1.get("mode") == "current"
            and _bg_d1.get("guard") == "trigger"
            and _bg_d1.get("cur_size", 0) > 0
            and _bg_d1.get("cur_block_fill_usable", 0.0) >= 0.05
        )
        MANGABD_CONFIG["rendering"]["bubble_fill_enable"] = False
        _bg_d2 = bubble_fill_decision(
            "কী হয়েছে?", 20, 20, 380, 320,
            image_gray=_bg_gray, bold=False, angle=0.0, region_type="bubble",
        )
        _bg_dis_ok = (
            _bg_d2.get("mode") == "current"
            and _bg_d2.get("guard") == "disabled"
        )
        run_test(
            "B1 guards: trigger + kill-switch keep current",
            _bg_trig_ok and _bg_dis_ok,
            f"trigger: guard={_bg_d1.get('guard')} "
            f"blkU={_bg_d1.get('cur_block_fill_usable')}; "
            f"disabled: guard={_bg_d2.get('guard')}",
        )
    finally:
        # ABSENT-sentinel restore: §2 না চলা পরিবেশেও key-হীন অবস্থা
        # ঠিক রাখে (গার্হহীন লিক RF-12/RF-13 হাইজিন discipline)
        if _bg_trig == "ABSENT":
            MANGABD_CONFIG["rendering"].pop("bubble_fill_trigger", None)
        else:
            MANGABD_CONFIG["rendering"]["bubble_fill_trigger"] = _bg_trig
        if _bg_en == "ABSENT":
            MANGABD_CONFIG["rendering"].pop("bubble_fill_enable", None)
        else:
            MANGABD_CONFIG["rendering"]["bubble_fill_enable"] = _bg_en
except Exception as exc:
    run_test("B1 guards: trigger + kill-switch keep current", False,
             str(exc)[:160])


# Test 15: N-1 — get_font silent degradation আর নীরব নয় (M9-A.4)।
# Missing main font এখন একবার loud WARN + log_event(ERROR) দেয়, তারপর
# আগের মতোই load_default-এ নামে (render বাঁচে, defect লুকায় না)।
try:
    import io as _io
    import contextlib as _ctx
    _n1_reg = MANGABD_CONFIG["rendering"].get("font_regular", "")
    _n1_bold = MANGABD_CONFIG["rendering"].get("font_bold", "")
    _n1_key = (33, False)
    _FONT_CACHE.pop(_n1_key, None)
    _FONT_DEGRADE_WARNED.pop("main_load_default", None)
    _n1_ok = False
    _n1_detail = ""
    try:
        MANGABD_CONFIG["rendering"]["font_regular"] = "/tmp/MISSING-m009-n1.ttf"
        MANGABD_CONFIG["rendering"]["font_bold"] = ""
        _n1_buf = _io.StringIO()
        with _ctx.redirect_stdout(_n1_buf):
            _n1_font = get_font(33, bold=False)
        _n1_txt = _n1_buf.getvalue()
        # Pillow-সংস্করণ-নিরপেক্ষ সংজ্ঞা: এই মুহূর্তে config-এ শুধুই missing
        # path আছে — তাই সফল return মানেই default থেকে এসেছে (load_default
        # পুরনো Pillow-এ bitmap ImageFont, নতুনটায় embedded FreeType —
        # isinstance নির্ভর ধরা ঠিক নয়; loud-WARN + latch + non-None-ই N-1)।
        _n1_ok = (
            _n1_font is not None
            and "Main font load failed" in _n1_txt
            and _FONT_DEGRADE_WARNED.get("main_load_default") is True
        )
        _n1_detail = (
            f"font={type(_n1_font).__name__} "
            f"warn={'YES' if 'Main font load failed' in _n1_txt else 'NO'} "
            f"latch={_FONT_DEGRADE_WARNED.get('main_load_default')}"
        )
    finally:
        MANGABD_CONFIG["rendering"]["font_regular"] = _n1_reg
        MANGABD_CONFIG["rendering"]["font_bold"] = _n1_bold
        _FONT_CACHE.pop(_n1_key, None)
        _FONT_DEGRADE_WARNED.pop("main_load_default", None)
    run_test("get_font loud degradation (N-1)", _n1_ok, _n1_detail)
except Exception as exc:
    run_test("get_font loud degradation (N-1)", False, str(exc)[:160])


# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।"""
