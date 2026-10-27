#!/usr/bin/env python3
r"""MANGABD-009 B1 Phase C — patch content, part 3 (cells 11/12: V-3 wrapper forward-threading).

C-1 (Phase C discovery, disclosed in the Phase C record): the V-3 vertical
wrapper that cells 11/12 install around render_bengali_text sits IN
render_page's call chain in every fresh sequential run. Its signature lacks
the new fit_result kwarg, so without this forward-only threading EVERY
bubble render after cell 12 would TypeError (render_page's except would
silently skip the region — a catastrophic regression). The change is
forward-only: signature + the fallback arm forward fit_result verbatim;
the vertical arm is byte-untouched (bubble_fill_decision guards the V-3
predicate upstream — w<90 and h>2*max(1,w) and |angle|<=1 — so a
vertical-note-class region NEVER carries a fit_result in production).
"""

# ── C11: cell 11 wrapper — signature + fallback forward ───────────────
C11_WRAP_OLD = """if not globals().get("_QC_FINAL_RENDER_PATCHED"):
    _base_render = globals().get("_qc_orig_render", render_bengali_text)
    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None):
        if text and str(text).strip() and w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0:
            b = bold if bold is not None else (region_type in ["sfx", "narrator"])
            return _qc_render_vertical(image_pil, text, x, y, w, h, b, (0,0,0), padding)
        return _base_render(image_pil, text, x, y, w, h, angle, region_type,
                            bold, stroke_width, text_color, padding)"""

C11_WRAP_NEW = """if not globals().get("_QC_FINAL_RENDER_PATCHED"):
    _base_render = globals().get("_qc_orig_render", render_bengali_text)
    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
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

# ── C12: cell 12 wrapper — signature + fallback forward ───────────────
C12_WRAP_OLD = """if not globals().get("_QC_RENDER_PATCHED"):
    _qc_orig_render = render_bengali_text
    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None):
        if text and str(text).strip() and w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0:
            b = bold if bold is not None else (region_type in ["sfx", "narrator"])
            return _qc_render_vertical(image_pil, text, x, y, w, h, b, (0, 0, 0), padding)
        return _qc_orig_render(image_pil, text, x, y, w, h, angle, region_type,
                               bold, stroke_width, text_color, padding)"""

C12_WRAP_NEW = """if not globals().get("_QC_RENDER_PATCHED"):
    _qc_orig_render = render_bengali_text
    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
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
