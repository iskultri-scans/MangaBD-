#!/usr/bin/env python3
"""MANGABD-009 RF-19 — cell-10 patch content (production tiny-guard).

Owner fast-round ruling: RB31-6 existed only as the Test 24 sentinel;
the render-side half is NOW ruled in. In render_page: if rendered
lines == 1 AND translated lines >= 2 (measured by the horizontal
bbox fit — the same fit_font_size call the re-layout itself uses)
AND region area >= 2000px -> re-layout via the horizontal bbox path
(no GT mirror), WARN logged.

Mechanism notes (design-time measured, scripts/m009_rf19_design.py):
  * The layout report travels via a MUTABLE namespace dict
    (_RF19_LAST_LAYOUT) — NOT a new kwarg: cells 11/12 own the
    global render_bengali_text name via the _QC_*_RENDER_PATCHED
    wrapper, and RF-19 scope is cells {6,10} ONLY. The wrapper's
    vertical arm never reaches the report -> stays None -> guard
    silent (RB31-5 law preserved). The fallback arm forwards to the
    cell-10 def, which writes the report after layout resolution.
  * The guard fires ONLY through the b2gt / mask-fit / rotated-quad
    paths: on the plain fit path the rendered lines ARE the bbox-fit
    lines (same call), so rendered==1 implies bbox-fit==1 -> no fire.
  * The primary render is snapshotted (canvas copy) only when
    area >= 2000px; on fire the snapshot is restored before the
    horizontal re-render (no double-draw). Non-firing regions leave
    bytes identical.
"""
import textwrap  # noqa: F401  (kept: content mirrors B3.1 module shape)

# ── P1: namespace report + census state, before the renderer def ───
C10_P1_OLD = """\
def render_bengali_text(
    image_pil,
    text,
    x,
    y,
    w,
    h,
    angle=0.0,\
"""

C10_P1_NEW = """\
# MANGABD-009 RF-19 (Owner fast round): layout report + guard census —
# mutable namespace state, কখনো rebind হয় না (signature অপরিবর্তিত —
# cells 11/12 wrapper + RF-15 law অক্ষত)। render_bengali_text layout
# resolve করেই report লেখে; render_page primary call-এর আগে None-এ
# reset করে, পরে পড়ে। vertical arm (_qc_render_vertical, cell 11)
# এখানে কখনো আসে না — ওই call-এ report None-ই থাকে → guard silent
# (RB31-5)। _RF19_GUARD_FIRES = পুরো namespace-এর fire census
# (battery Test 25-এর blast-radius freeze)।
_RF19_LAST_LAYOUT = {"lines": None}
_RF19_GUARD_FIRES = []


def render_bengali_text(
    image_pil,
    text,
    x,
    y,
    w,
    h,
    angle=0.0,\
"""

# ── P2: the report write, after layout resolution (before any draw) ─
C10_P2_OLD = """\
    line_height = (_b2_gt_lh if _b2_gt_lh is not None
                   else get_line_height(font))\
"""

C10_P2_NEW = """\
    line_height = (_b2_gt_lh if _b2_gt_lh is not None
                   else get_line_height(font))

    # MANGABD-009 RF-19: layout report — তিন layout path (mask /
    # b2gt / fit) যেটাই চলুক, resolved lines এক জায়গায় লেখা হয়
    # (rotated return-এর আগে, তাই দুই branch-ই cover)। render_page
    # production tiny-guard এটা পড়ে; বাকি সব caller-এর জন্য নীরব।
    try:
        _RF19_LAST_LAYOUT["lines"] = int(len(lines))
    except Exception:
        pass\
"""

# ── P3: per-page fire list, beside the render counters ─────────────
C10_P3_OLD = """\
    rendered_count = 0
    skipped_count = 0
    warning_count = 0\
"""

C10_P3_NEW = """\
    rendered_count = 0
    skipped_count = 0
    warning_count = 0

    # MANGABD-009 RF-19: এই page-এর tiny-guard fires (meta disclosure)।
    _rf19_fires = []\
"""

# ── P4: the guard, wrapped around the primary region render ────────
C10_P4_OLD = """\
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
                ink_color=_b3_row_ink,
                line_colors=b31_page_line_colors.get(region_id),
                fit_result=(b2_gt_fr
                            if b2_gt_fr is not None else bf_fit),
                fit_w=fit_w,
                fit_h=fit_h,
            )\
"""

C10_P4_NEW = """\
            font_sizes_used.append(int(est_size))

            # MANGABD-009 RF-19: snapshot শুধু area >= 2000px হলে
            # (fire হলে restore করে horizontal re-render হবে —
            # double-draw নেই; non-firing region-এ bytes অপরিবর্তিত)।
            _rf19_area_ok = int(w) * int(h) >= 2000
            _rf19_snap = canvas_pil.copy() if _rf19_area_ok else None
            _RF19_LAST_LAYOUT["lines"] = None

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
                ink_color=_b3_row_ink,
                line_colors=b31_page_line_colors.get(region_id),
                fit_result=(b2_gt_fr
                            if b2_gt_fr is not None else bf_fit),
                fit_w=fit_w,
                fit_h=fit_h,
            )

            # MANGABD-009 RF-19: production tiny-guard (Owner fast
            # round — RB31-6-এর render-side অর্ধেক এবার ruling)।
            # rendered == 1 AND translation horizontal-bbox তে >= 2
            # line নেয় AND area >= 2000px → render collapse হয়েছে
            # (false-tilt quad / merged GT / mask-fit যে পথ থেকেই
            # হোক) → horizontal bbox path-এ re-layout (no GT mirror)
            # + WARN। plain-fit path-এ এটা কখনো fire করে না —
            # ওখানে rendered == bbox-fit lines (একই call)।
            if (_rf19_area_ok
                    and _RF19_LAST_LAYOUT.get("lines") == 1):
                _rf19_fs, _rf19_lines, _ = fit_font_size(
                    translated_text, int(w), int(h), bold=bold)
                if len(_rf19_lines) >= 2:
                    canvas_pil = _rf19_snap
                    _RF19_LAST_LAYOUT["lines"] = None
                    canvas_pil = render_bengali_text(
                        canvas_pil,
                        translated_text,
                        x,
                        y,
                        w,
                        h,
                        angle=0.0,
                        region_type=region_type,
                        bold=bold,
                        stroke_width=stroke_width,
                        text_color=text_color,
                        ink_color=_b3_row_ink,
                        line_colors=b31_page_line_colors.get(
                            region_id),
                        fit_result=None,
                        fit_w=None,
                        fit_h=None,
                    )
                    font_sizes_used[-1] = int(_rf19_fs)
                    warning_count += 1
                    _rf19_fires.append(int(region_id))
                    _RF19_GUARD_FIRES.append((page_id, region_id))
                    log_event(
                        f"RF-19 tiny-guard re-layout "
                        f"[{page_id}:{region_id}] — rendered 1 line, "
                        f"horizontal bbox fit {len(_rf19_lines)} "
                        f"lines (no GT mirror)",
                        level="WARN",
                        page_id=page_id,
                    )
                    print(
                        f"    ⚠️ RF-19 tiny-guard: region "
                        f"{region_id} re-laid out horizontally "
                        f"({len(_rf19_lines)} lines)"
                    )\
"""

# ── P5: render-meta disclosure (only when the page actually fired) ─
C10_P5_OLD = """\
    if b2_tilted_rendered:
        meta["b2_orientation"] = {
            "tilted_rendered": int(b2_tilted_rendered),
        }\
"""

C10_P5_NEW = """\
    if b2_tilted_rendered:
        meta["b2_orientation"] = {
            "tilted_rendered": int(b2_tilted_rendered),
        }

    # MANGABD-009 RF-19: tiny-guard disclosure — শুধু সত্যি fire হলে
    # (healthy page-এর render meta byte-identical — B2 disclosure
    # law-এর একই প্যাটার্ন)।
    if _rf19_fires:
        meta["rf19_tiny_guard"] = {"regions": _rf19_fires}\
"""

for _n in ("P1", "P2", "P3", "P4", "P5"):
    _old, _new = globals()[f"C10_{_n}_OLD"], globals()[f"C10_{_n}_NEW"]
    assert _old != _new, _n
