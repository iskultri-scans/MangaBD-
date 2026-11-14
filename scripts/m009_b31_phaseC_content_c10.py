#!/usr/bin/env python3
r"""MANGABD-009 B3.1 Phase C — cell 10 patch content.

Anchored OLD/NEW pairs against the B3-tip notebook @ cf01aef.
Implements: line_colors kwarg (RB31-3), per-line color/stroke apply on
all three render paths (horizontal / tilted / runs-fallback), i <
min(n_orig, n_trans) mapping with region-base fallback (RB31-4),
render_page strict parse + invalid-WARN (B3 P4 law), battery Test 24
(per-line end-to-end + knob-OFF byte-parity + tiny-text assertion @
2000px + narrow-bubble V5 arms + invalid-key + base kwarg).
"""

# ── C10-P1: render_bengali_text signature — line_colors kwarg ────────
C10_P1_OLD = '''    fit_w=None,
    fit_h=None,
    ink_color=None,
):
'''
C10_P1_NEW = '''    fit_w=None,
    fit_h=None,
    ink_color=None,
    line_colors=None,
):
'''

# ── C10-P2: per-line materialization + strokes ────────────────────────
C10_P2_OLD = '''    stroke_color = choose_stroke_color(text_color)

    # Rotated rendering
'''
C10_P2_NEW = '''    stroke_color = choose_stroke_color(text_color)

    # MANGABD-009 B3.1 (RB31-3/RB31-4): per-line colors — layout resolve
    # হওয়ার পরে materialize। entry i < min(n_orig, n_trans) non-null →
    # সেই রঙ; নাহলে region base (এই জায়গায় এসে text_color-এ আগেই
    # ink_color / choose_text_color apply হয়ে আছে — precedence
    # line_colors > ink_color > choose_text_color)। কোনো line-ই আলাদা
    # রঙ পায়নি → None → নিচের single-stroke path হুবহু আগের মতো
    # (None/absent = byte-exact, RF-15 kwarg law)।
    _b31_cols = None
    _b31_strokes = None
    if line_colors is not None:
        try:
            _b31_list = list(line_colors)
            _b31_cols = []
            for _b31_i in range(len(lines)):
                _b31_c = None
                if _b31_i < len(_b31_list):
                    _b31_v = _b31_list[_b31_i]
                    if (isinstance(_b31_v, (list, tuple))
                            and len(_b31_v) == 3
                            and all(isinstance(_b31_z, int)
                                    and 0 <= _b31_z <= 255
                                    for _b31_z in _b31_v)):
                        _b31_c = (int(_b31_v[0]), int(_b31_v[1]),
                                  int(_b31_v[2]))
                _b31_cols.append(_b31_c)
            if not any(_b31_c is not None
                       and tuple(_b31_c) != tuple(text_color)
                       for _b31_c in _b31_cols):
                _b31_cols = None
        except Exception:
            _b31_cols = None
    if _b31_cols is not None:
        _b31_strokes = []
        for _b31_c in _b31_cols:
            if _b31_c is None or tuple(_b31_c) == tuple(text_color):
                _b31_strokes.append(stroke_color)
            else:
                _b31_strokes.append(choose_stroke_color(_b31_c))

    # Rotated rendering
'''

# ── C10-P3: rotated branch forwards per-line colors ───────────────────
C10_P3_OLD = '''            gt_block_h=(int(_b2_gt_lh * len(lines))
                        if _b2_gt_lh is not None else None),
        )
'''
C10_P3_NEW = '''            gt_block_h=(int(_b2_gt_lh * len(lines))
                        if _b2_gt_lh is not None else None),
            line_colors=_b31_cols,
        )
'''

# ── C10-P4: horizontal loop per-line fill/stroke ──────────────────────
C10_P4_OLD = '''        if _needs_fb and any(not _main_font_ok(ch) for ch in line):
            _draw_runs_horizontal(
                draw, line, x, _b1_bw, line_y, font, bold,
                text_color, stroke_color, stroke_width, padding,
                center_x=_b1_c,
            )
            continue

        try:
            if stroke_width and stroke_width > 0:
                draw.text(
                    (line_x, line_y),
                    line,
                    font=font,
                    fill=text_color,
                    stroke_width=int(stroke_width),
                    stroke_fill=stroke_color,
                )
            else:
                draw.text(
                    (line_x, line_y),
                    line,
                    font=font,
                    fill=text_color,
                )

        except TypeError:
            # Older Pillow fallback
            if stroke_width and stroke_width > 0:
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        draw.text(
                            (line_x + dx, line_y + dy),
                            line,
                            font=font,
                            fill=stroke_color,
                        )

            draw.text(
                (line_x, line_y),
                line,
                font=font,
                fill=text_color,
            )

    return image_pil
'''

C10_P4_NEW = '''        # B3.1: এই line-এর রঙ — None → base (single-color/absent
        # path-এ _b31_cols None, তাই পুরো block আগের exact bytes)
        _b31_fill = (tuple(_b31_cols[i]) if (
            _b31_cols is not None and _b31_cols[i] is not None)
            else text_color)
        _b31_stroke = (_b31_strokes[i]
                       if _b31_strokes is not None else stroke_color)

        if _needs_fb and any(not _main_font_ok(ch) for ch in line):
            _draw_runs_horizontal(
                draw, line, x, _b1_bw, line_y, font, bold,
                _b31_fill, _b31_stroke, stroke_width, padding,
                center_x=_b1_c,
            )
            continue

        try:
            if stroke_width and stroke_width > 0:
                draw.text(
                    (line_x, line_y),
                    line,
                    font=font,
                    fill=_b31_fill,
                    stroke_width=int(stroke_width),
                    stroke_fill=_b31_stroke,
                )
            else:
                draw.text(
                    (line_x, line_y),
                    line,
                    font=font,
                    fill=_b31_fill,
                )

        except TypeError:
            # Older Pillow fallback
            if stroke_width and stroke_width > 0:
                for dx in range(-stroke_width, stroke_width + 1):
                    for dy in range(-stroke_width, stroke_width + 1):
                        draw.text(
                            (line_x + dx, line_y + dy),
                            line,
                            font=font,
                            fill=_b31_stroke,
                        )

            draw.text(
                (line_x, line_y),
                line,
                font=font,
                fill=_b31_fill,
            )

    return image_pil
'''

# ── C10-P5: _render_rotated_text — signature + per-line draw loop ────
C10_P5A_OLD = '''    gt_cx=None,
    gt_cy=None,
    gt_block_h=None,
):
'''
C10_P5A_NEW = '''    gt_cx=None,
    gt_cy=None,
    gt_block_h=None,
    line_colors=None,
):
'''

C10_P5B_OLD = '''        for i, line in enumerate(lines):
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

            try:
                if stroke_width and stroke_width > 0:
                    draw.text(
                        (line_x, line_y),
                        line,
                        font=font,
                        fill=text_color + (255,),
                        stroke_width=int(stroke_width),
                        stroke_fill=stroke_color + (255,),
                    )
                else:
                    draw.text(
                        (line_x, line_y),
                        line,
                        font=font,
                        fill=text_color + (255,),
                    )

            except TypeError:
                draw.text(
                    (line_x, line_y),
                    line,
                    font=font,
                    fill=text_color + (255,),
                )
'''

C10_P5B_NEW = '''        for i, line in enumerate(lines):
            line_width, _ = measure_text(line, font, draw)

            line_x = int((canvas_width - line_width) // 2)
            line_y = int(start_y + i * line_height)

            # MANGABD-009 B3.1 (RB31-3): per-line color — None → base
            # (absent path-এ line_colors None, আগের exact bytes)
            _b31_lc = (line_colors[i] if (line_colors is not None
                        and i < len(line_colors)) else None)
            _b31_fill = (tuple(_b31_lc) if _b31_lc is not None
                         else text_color)
            _b31_stroke = (stroke_color if (
                _b31_lc is None or tuple(_b31_lc) == tuple(text_color))
                else choose_stroke_color(_b31_lc))

            if _needs_fb_rot and any(not _main_font_ok(ch) for ch in line):
                _draw_runs_horizontal(
                    draw, line, 0, canvas_width, line_y, font, bold,
                    _b31_fill + (255,), _b31_stroke + (255,),
                    stroke_width, padding,
                )
                continue

            try:
                if stroke_width and stroke_width > 0:
                    draw.text(
                        (line_x, line_y),
                        line,
                        font=font,
                        fill=_b31_fill + (255,),
                        stroke_width=int(stroke_width),
                        stroke_fill=_b31_stroke + (255,),
                    )
                else:
                    draw.text(
                        (line_x, line_y),
                        line,
                        font=font,
                        fill=_b31_fill + (255,),
                    )

            except TypeError:
                draw.text(
                    (line_x, line_y),
                    line,
                    font=font,
                    fill=_b31_fill + (255,),
                )
'''

# ── C10-P6a: render_page parse-init — b31 map ─────────────────────────
C10_P6A_OLD = '''    b3_page_ink = {}
    try:
'''
C10_P6A_NEW = '''    b3_page_ink = {}
    b31_page_line_colors = {}
    try:
'''

# ── C10-P6b: render_page detections parse — line_colors read ─────────
C10_P6B_OLD = '''                        else:
                            log_event(
                                f"Invalid ink_color ignored "
                                f"[{page_id} r{_b2_rid}] — "
                                f"RF-17 fallback",
                                level="WARN",
                            )
            except (TypeError, ValueError):
                continue
'''

C10_P6B_NEW = '''                        else:
                            log_event(
                                f"Invalid ink_color ignored "
                                f"[{page_id} r{_b2_rid}] — "
                                f"RF-17 fallback",
                                level="WARN",
                            )
                # MANGABD-009 B3.1 (RB31-3): per-line colors — strict
                # validate (list, entry null বা 3×uint8); invalid →
                # WARN + treat-as-absent (B3 P4 law)।
                if _b3_inherit:
                    _b31_lk = _b2_qr.get("line_colors")
                    if _b31_lk is not None:
                        _b31_ok = (isinstance(_b31_lk, list)
                                   and all(
                                       (lc is None)
                                       or (isinstance(lc, (list, tuple))
                                           and len(lc) == 3
                                           and all(
                                               isinstance(v, int)
                                               and not isinstance(v, bool)
                                               and 0 <= v <= 255
                                               for v in lc))
                                       for lc in _b31_lk))
                        if _b31_ok:
                            b31_page_line_colors[_b2_rid] = [
                                ([int(v) for v in lc]
                                 if lc is not None else None)
                                for lc in _b31_lk]
                        else:
                            log_event(
                                f"Invalid line_colors ignored "
                                f"[{page_id} r{_b2_rid}] — "
                                f"RF-17 fallback",
                                level="WARN",
                            )
            except (TypeError, ValueError):
                continue
'''

# ── C10-P7: render call forwards line_colors (always-sent kwarg) ─────
C10_P7_OLD = '''                text_color=text_color,
                ink_color=_b3_row_ink,
'''
C10_P7_NEW = '''                text_color=text_color,
                ink_color=_b3_row_ink,
                line_colors=b31_page_line_colors.get(region_id),
'''
