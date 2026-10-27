#!/usr/bin/env python3
r"""MANGABD-009 B2 Phase C — cell-10 patch content (RB2-4/RB2-5/RB2-7).

Base = main @ 5fe8804 (notebook sha256 0858a1c9…). Cell 10 carries:
  - `_b2_render_angle` (render-side kill-switch mirror, RB2-7)
  - render_bengali_text / _render_rotated_text trailing kwargs
    `fit_w`/`fit_h` (RB2-5 quad-extents fit dims; None → bbox = exact
    previous behavior, callers untouched — cells 11/12 wrappers pass
    positionally up to fit_result and are byte-untouched)
  - render_page: quad lookup from the detections artifact (cell-07's
    build_ocr_row whitelist carries `angle` but NOT `quad` — Phase A's
    "row['quad'] already present" was WRONG; disclosed), fit-dims
    computation (the crop_region_rotated extents convention), est_size
    tracking dims, tilted counter + conditional meta disclosure
  - battery Tests 16-18 (estimator semantics / fit-dims + mirror /
    end-to-end inheritance round-trip)
"""

# ── helper insert: render-side kill-switch mirror (RB2-7) ───────────
C10_HELPER_OLD = '''print("  ✅ Main renderer ready")
print()


# ═══════════════════════════════════════════════════════════
# 9. Page rendering pipeline
'''

C10_HELPER_NEW = '''print("  ✅ Main renderer ready")
print()


def _b2_render_angle(raw_angle):
    """MANGABD-009 B2 (RB2-7): render-side kill-switch mirror।

    detection-side b2_orientation_enable False হলে cell-6 কখনোই
    non-zero angle store করে না; এটা দ্বিতীয় লাইন — re-detect ছাড়াই
    আগের exact render bytes ফেরায় (stored angle থাকলেও |angle| > 1
    হলে 0.0 হয়ে যায়)। key অনুপস্থিত হলে default-ON (cell-6 setdefault
    -এর মতোই); |angle| <= 1 সবসময় passthrough (rotated gate-ই পায় না)।
    """
    if abs(float(raw_angle)) > 1.0 and not bool(
        MANGABD_CONFIG.get("detection", {}).get(
            "b2_orientation_enable", True)
    ):
        return 0.0
    return float(raw_angle)


print("  ✅ B2 render-angle mirror ready (MANGABD-009 B2)")
print()


# ═══════════════════════════════════════════════════════════
# 9. Page rendering pipeline
'''

# ── render_bengali_text: trailing fit_w/fit_h kwargs (RB2-5) ─────────
C10_RUNSIG_OLD = '''    text_color=None,
    padding=None,
    fit_result=None,
):
    """
    PIL image-এ Bengali text render করে।
'''

C10_RUNSIG_NEW = '''    text_color=None,
    padding=None,
    fit_result=None,
    fit_w=None,
    fit_h=None,
):
    """
    PIL image-এ Bengali text render করে।

    MANGABD-009 B2 (RB2-5): fit_w/fit_h = tilted branch-এর fit dims
    (quad extents)। None হলে bbox w/h — আগের exact আচরণ, সব পুরনো
    caller-এর জন্য rendered bytes অপরিবর্তিত।
'''

# ── render_bengali_text: current-path fit dims (RB2-5) ───────────────
C10_RUNFIT_OLD = '''    if fit_result is not None:
        font_size = int(fit_result["font_size"])
        lines = list(fit_result["lines"])
    else:
        font_size, lines, _ = fit_font_size(
            text,
            w,
            h,
            bold=bold,
            padding=padding,
        )
'''

C10_RUNFIT_NEW = '''    if fit_result is not None:
        font_size = int(fit_result["font_size"])
        lines = list(fit_result["lines"])
    else:
        # MANGABD-009 B2 (RB2-5): tilted branch-এর fit dims = quad
        # extents (V5: bbox dims-এ 200x60@20° strip-এ ~2.08x oversize)।
        # None হলে bbox — আগের exact fit। B1 mask layout rotated-এ
        # কখনোই আসে না (guard "rotated"), তাই এটা শুধু current path।
        _b2_fw = int(fit_w) if fit_w is not None else w
        _b2_fh = int(fit_h) if fit_h is not None else h
        font_size, lines, _ = fit_font_size(
            text,
            _b2_fw,
            _b2_fh,
            bold=bold,
            padding=padding,
        )
'''

# ── render_bengali_text: thread fit dims into the rotated branch ────
C10_ROTGATE_OLD = '''    # Rotated rendering
    if abs(float(angle)) > 1.0:
        return _render_rotated_text(
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
        )
'''

C10_ROTGATE_NEW = '''    # Rotated rendering
    if abs(float(angle)) > 1.0:
        return _render_rotated_text(
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
            fit_w=fit_w,
            fit_h=fit_h,
        )
'''

# ── _render_rotated_text: trailing fit_w/fit_h kwargs ────────────────
C10_ROTSIG_OLD = '''    stroke_width,
    line_height,
    padding,
    bold=False,
):
    """
    Rotated text render করে transparent canvas ব্যবহার করে।
    """
'''

C10_ROTSIG_NEW = '''    stroke_width,
    line_height,
    padding,
    bold=False,
    fit_w=None,
    fit_h=None,
):
    """
    Rotated text render করে transparent canvas ব্যবহার করে।

    MANGABD-009 B2 (RB2-5): fit_w/fit_h = canvas/fit dims (quad
    extents); None হলে bbox w,h — আগের exact আচরণ। paste center
    সবসময় bbox center (quad centroid == bbox center, Phase A proof)।
    """
'''

# ── _render_rotated_text: canvas dims from quad extents (RB2-5) ──────
C10_ROTCANVAS_OLD = '''        if padding is None:
            padding = 8

        canvas_width = max(int(w) + 4 * padding, 200)
        canvas_height = max(int(h) + 4 * padding, 100)
'''

C10_ROTCANVAS_NEW = '''        if padding is None:
            padding = 8

        # MANGABD-009 B2 (RB2-5): canvas dims = quad extents (strip-এর
        # সত্যি W,H); None হলে bbox — আগের exact আচরণ। rotate expand
        # =True নিজেই rotated bbox auto-compute করে (PIL — V4 formula),
        # paste center আগের মতোই bbox center।
        _cw = int(fit_w) if fit_w is not None else int(w)
        _ch = int(fit_h) if fit_h is not None else int(h)

        canvas_width = max(_cw + 4 * padding, 200)
        canvas_height = max(_ch + 4 * padding, 100)
'''

# ── render_page: quad lookup (artifact source) + B2 counter ──────────
C10_RPPAGE_OLD = '''    page_rows = translation_df[
        translation_df["page_id"] == page_id
    ].sort_values("id")

    rendered_count = 0
    skipped_count = 0
    warning_count = 0

    font_sizes_used = []
'''

C10_RPPAGE_NEW = '''    page_rows = translation_df[
        translation_df["page_id"] == page_id
    ].sort_values("id")

    # MANGABD-009 B2 (RB2-4/RB2-5): তির্যক branch-এর fit dims-এর quad
    # দরকার — df row-এ quad নেই (cell-07 build_ocr_row whitelist শুধু
    # angle নেয়), তাই detections artifact-ই সত্যি source; key = B2-এর
    # cell-6 region id-ই। lookup miss হলে fit dims None — আগের exact
    # rotated আচরণ।
    b2_page_quads = {}
    try:
        for _b2_qr in (load_json_artifact(page_id, "detections", default=[])
                       or []):
            try:
                b2_page_quads[int(_b2_qr.get("id", -1))] = _b2_qr.get("quad")
            except (TypeError, ValueError):
                continue
    except Exception:
        b2_page_quads = {}

    rendered_count = 0
    skipped_count = 0
    warning_count = 0

    # MANGABD-009 B2: সত্যি tilted-render হওয়া region-এর সংখ্যা (meta)
    b2_tilted_rendered = 0

    font_sizes_used = []
'''

# ── render_page loop: mirror + fit dims from the quad ────────────────
C10_RPANGLE_OLD = '''        x = int(row.get("x", 0))
        y = int(row.get("y", 0))
        w = int(row.get("width", 0))
        h = int(row.get("height", 0))
        angle = float(row.get("angle", 0.0))
'''

C10_RPANGLE_NEW = '''        x = int(row.get("x", 0))
        y = int(row.get("y", 0))
        w = int(row.get("width", 0))
        h = int(row.get("height", 0))
        # MANGABD-009 B2 (RB2-7): kill-switch mirror — stored angle
        # থাকলেও knob বন্ধ থাকলে এখানেই 0.0।
        angle = _b2_render_angle(row.get("angle", 0.0))

        # MANGABD-009 B2 (RB2-5): tilted branch-এর fit/canvas dims =
        # quad extents — crop_region_rotated-এর হুবহু convention
        # (cell-06 L944-952)। non-tilted region-এ None — আগের exact path।
        fit_w = fit_h = None
        if abs(angle) > 1.0:
            try:
                _b2_q = np.asarray(
                    b2_page_quads.get(region_id) or [], dtype=np.float64)
                if _b2_q.shape == (4, 2):
                    fit_w = int(round(max(
                        float(np.linalg.norm(_b2_q[0] - _b2_q[1])),
                        float(np.linalg.norm(_b2_q[2] - _b2_q[3])),
                    )))
                    fit_h = int(round(max(
                        float(np.linalg.norm(_b2_q[0] - _b2_q[3])),
                        float(np.linalg.norm(_b2_q[1] - _b2_q[2])),
                    )))
                    if fit_w < 5 or fit_h < 5:
                        fit_w = fit_h = None
            except Exception:
                fit_w = fit_h = None
'''

# ── render_page: est_size tracking uses the render's real dims ───────
C10_RPEST_OLD = '''            if est_size is None:
                # Font size tracking (B1 বন্ধ / exception — আগের মতোই)
                estimated_size, _, _ = fit_font_size(
                    translated_text,
                    w,
                    h,
                    bold=bold,
                )
                est_size = estimated_size
'''

C10_RPEST_NEW = '''            if est_size is None:
                # Font size tracking (B1 বন্ধ / exception — আগের মতোই;
                # B2 tilted branch-এর আসল render dims = quad extents)
                estimated_size, _, _ = fit_font_size(
                    translated_text,
                    fit_w if fit_w is not None else w,
                    fit_h if fit_h is not None else h,
                    bold=bold,
                )
                est_size = estimated_size
'''

# ── render_page: pass fit dims to the render call ─────────────────────
C10_RPCALL_OLD = '''            canvas_pil = render_bengali_text(
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
            )
'''

C10_RPCALL_NEW = '''            canvas_pil = render_bengali_text(
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
                fit_w=fit_w,
                fit_h=fit_h,
            )
'''

# ── render_page: tilted counter after a successful render ────────────
C10_RPCOUNT_OLD = '''            # DataFrame update
            translation_df.at[idx, "bengali_valid"] = True
            translation_df.at[idx, "status"] = "rendered"

            rendered_count += 1
'''

C10_RPCOUNT_NEW = '''            # DataFrame update
            translation_df.at[idx, "bengali_valid"] = True
            translation_df.at[idx, "status"] = "rendered"

            rendered_count += 1

            # MANGABD-009 B2: rotated branch-এ গেছে কি না (meta-র জন্য)
            if abs(angle) > 1.0:
                b2_tilted_rendered += 1
'''

# ── render_page: conditional B2 meta disclosure ───────────────────────
C10_RPMETA_OLD = '''    meta = {
        "rendered_regions": rendered_count,
        "skipped_regions": skipped_count,
        "render_warnings": warning_count,
    }
'''

C10_RPMETA_NEW = '''    meta = {
        "rendered_regions": rendered_count,
        "skipped_regions": skipped_count,
        "render_warnings": warning_count,
    }

    # MANGABD-009 B2: orientation-inheritance disclosure — শুধু সত্যি কেউ
    # tilted render হলে (kill-switch/all-axis-aligned পেজের render meta
    # আগের মতোই byte-identical)।
    if b2_tilted_rendered:
        meta["b2_orientation"] = {
            "tilted_rendered": int(b2_tilted_rendered),
        }
'''
