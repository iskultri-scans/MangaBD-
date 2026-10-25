#!/usr/bin/env python3
r"""MANGABD-008 B1 Phase C — content module: CELL 10 patches, part 2.

The D-3 gates (horizontal + rotated), the rotated-path bold plumbing,
and the battery additions (Tests 9-12).

Every OLD anchor below is byte-copied from the base notebook
(main @ 73ca565) and unique-asserted by the build driver.
"""

# ── patch 10-3: horizontal gate in render_bengali_text ──────
CELL10_GATE_OLD = """    vertical_center = int(y + (h - total_text_height) // 2)
    start_y = max(int(y) + padding, vertical_center)

    for i, line in enumerate(lines):
        line_width, _ = measure_text(line, font, draw)

        line_x = int(x + (w - line_width) // 2)
        line_y = int(start_y + i * line_height)

        try:"""

CELL10_GATE_NEW = """    vertical_center = int(y + (h - total_text_height) // 2)
    start_y = max(int(y) + padding, vertical_center)

    # MANGABD-008 Phase C (D-3): per-run fallback gate — যে line-এ main font-এ
    # নেই এমন glyph আছে শুধু সেটাতেই fallback draw চালু; pure-Bengali text
    # আগের exact single-font path-ই follow করে (rendered bytes unchanged)।
    _needs_fb = any(not _main_font_ok(ch) for line in lines for ch in line)

    for i, line in enumerate(lines):
        line_width, _ = measure_text(line, font, draw)

        line_x = int(x + (w - line_width) // 2)
        line_y = int(start_y + i * line_height)

        if _needs_fb and any(not _main_font_ok(ch) for ch in line):
            _draw_runs_horizontal(
                draw, line, x, w, line_y, font, bold,
                text_color, stroke_color, stroke_width, padding,
            )
            continue

        try:"""

# ── patch 10-4: _render_rotated_text signature gains bold ────
CELL10_ROTSIG_OLD = """def _render_rotated_text(
    image_pil,
    lines,
    font,
    x,
    y,
    w,
    h,
    angle,
    text_color,
    stroke_color,
    stroke_width,
    line_height,
    padding,
):"""

CELL10_ROTSIG_NEW = """def _render_rotated_text(
    image_pil,
    lines,
    font,
    x,
    y,
    w,
    h,
    angle,
    text_color,
    stroke_color,
    stroke_width,
    line_height,
    padding,
    bold=False,
):"""

# ── patch 10-5: rotated call site passes bold ─────────────────
CELL10_ROTCALL_OLD = """        return _render_rotated_text(
            image_pil,
            lines,
            font,
            x,
            y,
            w,
            h,
            float(angle),
            text_color,
            stroke_color,
            stroke_width,
            line_height,
            padding,
        )"""

CELL10_ROTCALL_NEW = """        return _render_rotated_text(
            image_pil,
            lines,
            font,
            x,
            y,
            w,
            h,
            float(angle),
            text_color,
            stroke_color,
            stroke_width,
            line_height,
            padding,
            bold=bold,
        )"""

# ── patch 10-6: rotated loop gate ─────────────────────────────
CELL10_ROTLOOP_OLD = """        start_y = padding + (canvas_height - 2 * padding - total_text_height) // 2
        start_y = max(padding, int(start_y))

        for i, line in enumerate(lines):
            line_width, _ = measure_text(line, font, draw)

            line_x = int((canvas_width - line_width) // 2)
            line_y = int(start_y + i * line_height)

            try:"""

CELL10_ROTLOOP_NEW = """        start_y = padding + (canvas_height - 2 * padding - total_text_height) // 2
        start_y = max(padding, int(start_y))

        # MANGABD-008 Phase C (D-3): rotated path-এও একই per-run fallback —
        # শুধু fallback-দরকার line-এ; বাকি line আগের exact draw-ই।
        _needs_fb_rot = any(not _main_font_ok(ch) for line in lines for ch in line)

        for i, line in enumerate(lines):
            line_width, _ = measure_text(line, font, draw)

            line_x = int((canvas_width - line_width) // 2)
            line_y = int(start_y + i * line_height)

            if _needs_fb_rot and any(not _main_font_ok(ch) for ch in line):
                _draw_runs_horizontal(
                    draw, line, 0, canvas_width, line_y, font, bold,
                    text_color + (255,), stroke_color + (255,),
                    stroke_width, padding,
                )
                continue

            try:"""

# ── patch 10-7: battery — Tests 9-12 (glyph coverage) ─────────
CELL10_TESTS_OLD = """# Test 8: Bengali validation
try:
    ok = (
        render_validate_bengali("বাংলা") is True
        and render_validate_bengali("Hello") is False
    )

    run_test("Bengali validation", ok)
except Exception as exc:
    run_test("Bengali validation", False, str(exc)[:160])


print()"""

CELL10_TESTS_NEW = """# Test 8: Bengali validation
try:
    ok = (
        render_validate_bengali("বাংলা") is True
        and render_validate_bengali("Hello") is False
    )

    run_test("Bengali validation", ok)
except Exception as exc:
    run_test("Bengali validation", False, str(exc)[:160])


# Test 9: glyph-coverage routing (MANGABD-008 D-1/D-2)
try:
    ok = (
        _main_font_ok("ক") is True
        and _main_font_ok("।") is True      # danda: main font-এ আছে (D-1)
        and _main_font_ok("a") is False     # ASCII: JP fallback-এ (D-2)
        and _main_font_ok('"') is False
        and _main_font_ok("—") is False
        and _main_font_ok("こ") is False     # kana: JP fallback-এ
    )

    run_test("glyph-coverage routing (D-1/D-2)", ok)
except Exception as exc:
    run_test("glyph-coverage routing (D-1/D-2)", False, str(exc)[:160])


# Test 10: JP fallback font loads + WARN-never-silent (MANGABD-008 D-4)
try:
    import io as _m8_io
    import contextlib as _m8_cl

    fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    _FB_CACHE.clear()
    fb_font = get_font_fb(24)

    try:
        MANGABD_CONFIG["rendering"]["font_fallback"] = str(
            Path(fb_real).parent / "MISSING-NotoSansJP.ttf")
        _FB_CACHE.clear()
        _FONT_ROUTE_WARNED.pop("fb_load", None)
        _m8_buf = _m8_io.StringIO()
        with _m8_cl.redirect_stdout(_m8_buf):
            fb_missing = get_font_fb(24)
        warned = "JP fallback font unavailable" in _m8_buf.getvalue()
    finally:
        MANGABD_CONFIG["rendering"]["font_fallback"] = fb_real
        _FB_CACHE.clear()

    run_test(
        "JP fallback WARN-never-silent (D-4)",
        fb_font is not None and fb_missing is None and warned,
    )
except Exception as exc:
    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])


# Test 11: horizontal mixed-script render — fallback glyphs real (MANGABD-008 D-3)
try:
    _m8_text = 'নোট: "কোগানেই" — こがねই।'

    canvas_a = PILImage.new("RGB", (400, 120), (255, 255, 255))
    render_bengali_text(
        canvas_a, _m8_text, 10, 10, 380, 100,
        region_type="bubble", bold=False, stroke_width=0,
        text_color=(0, 0, 0), padding=None,
    )

    fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    try:
        MANGABD_CONFIG["rendering"]["font_fallback"] = str(
            Path(fb_real).parent / "MISSING-NotoSansJP.ttf")
        _FB_CACHE.clear()
        canvas_b = PILImage.new("RGB", (400, 120), (255, 255, 255))
        render_bengali_text(
            canvas_b, _m8_text, 10, 10, 380, 100,
            region_type="bubble", bold=False, stroke_width=0,
            text_color=(0, 0, 0), padding=None,
        )
    finally:
        MANGABD_CONFIG["rendering"]["font_fallback"] = fb_real
        _FB_CACHE.clear()

    arr_a = np.array(canvas_a)
    ink_a = int((arr_a < 128).sum())
    differ = not np.array_equal(arr_a, np.array(canvas_b))
    run_test(
        "horizontal mixed render: fallback glyphs real (D-3)",
        ink_a > 40 and differ,
        f"ink={ink_a}, differ={differ}",
    )
except Exception as exc:
    run_test(
        "horizontal mixed render: fallback glyphs real (D-3)",
        False, str(exc)[:160],
    )


# Test 12: tofu detector — JP solid glyph vs main-font .notdef hollow (D-2)
try:
    def _m8_hollow(font, ch):
        probe = PILImage.new("L", (160, 160), 255)
        pd = ImageDraw.Draw(probe)
        pd.text((30, 30), ch, font=font, fill=0)
        pa = np.array(probe)
        ys, xs = np.where(pa < 128)
        if not len(ys):
            return None
        sub = pa[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
        if sub.shape[0] < 6 or sub.shape[1] < 6:
            return None
        # hollow .notdef box: 2px-eroded ভেতরে প্রায় কালি থাকে না (anti-alias
        # stray সহ্য করার জন্য ratio) — solid glyph-এ ratio অনেক বড়
        inner = sub[2:-2, 2:-2] < 128
        frac = int(inner.sum()) / max(1, int(inner.size))
        return frac < 0.05

    fb_solid = _m8_hollow(get_font_fb(48), "H") is False
    main_hollow = _m8_hollow(get_font(48, False), "H") is True
    run_test(
        "tofu detector: JP solid glyph vs main .notdef (D-2)",
        fb_solid and main_hollow,
    )
except Exception as exc:
    run_test(
        "tofu detector: JP solid glyph vs main .notdef (D-2)",
        False, str(exc)[:160],
    )


print()"""
