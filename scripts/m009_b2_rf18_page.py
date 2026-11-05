#!/usr/bin/env python3
"""MANGABD-009 B2 RF-18 — S011 manhwa-UI page builder (shared).

The Owner's product ruling (RF-18): readable != professional — EXACT
orientation parity with the original, pinning the Korean-manhwa /
game-system-window class the Owner named: tilted UI text in system
windows, a dark UI panel, heavy art crowding a light panel.

Page census (9 regions):
  * U1-U5  light SYSTEM-WINDOW panels — rounded-rect double border
    (3px outer + 1px inner accent at 8px inset), near-white fill,
    beta-tilted text. U1/U2/U4 mass-symmetric (one line repeated —
    the S009/S010 law: identical centered lines => the ink-cloud
    measurement is unbiased); U3 sits in a HEAVY-ART cluster (dense
    deterministic strokes + paper-white halo, the S010 E3 law) — the
    bbox-mean color surface; U5 is the ASYMMETRIC two-line block
    (short + long line) that pins the measurement-surface verdict
    (report-only class);
  * U6     DARK system window (fill 62, light border) with WHITE
    text — the D2 color-decision surface (quad-mask brightness must
    pick white);
  * H1/H2  horizontal ellipses + V1 vertical note — stability
    controls.

Fixture laws inherited from S009/S010 (v2-v4 lessons):
  * ring/border strokes at INK_GRAY 20 (threshold-safe even after
    composite AA + BICUBIC tilt);
  * text strips 0.70-0.78 of the panel width so the rotated strip's
    corners stay inside the interior;
  * fitted font stays >= ~26px;
  * one repeated line per symmetric bubble (distinct line lengths
    bias the ink-cloud PCA by up to ~5 deg);
  * no cross-hatching inside the halo.

Ground-truth law (unchanged): a text strip drawn horizontal then
rotated with PIL .rotate(beta, expand=True) measures pil == beta.

Shared by:
  * scripts/m009_b2_rf18_s011_build.py (samples/S011_manhwa_ui)
  * scripts/m009_b2_rf18_verify.py     (parity tables + overlays)
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from m009_b2_rf16_page import (
    LOCAL_JP_COPY, _fit_font, _jp_font, _page_canvas,
    _vertical_note_block,
)

INK_GRAY = 20
TEXT_GRAY = 10
DARK_FILL = 62          # dark UI panel fill (light text goes on top)
DARK_BORDER = 150
PAGE_W, PAGE_H = 1300, 2000
RNG_SEED = 20261104
BORDER_W = 3            # outer system-window border
ACCENT_INSET = 8        # inner 1px accent border inset
PANEL_RADIUS = 18

# ── the S011 manhwa-UI page: 5 light UI + 1 dark UI + 2 H + 1 V ──────
# beta = ground-truth TEXT tilt (deg), all |beta| in [6, 25]: inside
# the tilted band, clear of the 5 deg snap on both sides of +/-2 tol.
# "lines": U5 carries EXPLICIT distinct lines (the asymmetric class).
S011_PANELS = [
    {"tag": "U1", "beta": -8.0, "cx": 330, "cy": 260, "bw": 430,
     "bh": 300, "jp": "システム警告：敵接近", "lines": 3},
    {"tag": "U2", "beta": 12.0, "cx": 960, "cy": 250, "bw": 400,
     "bh": 260, "jp": "スキル発動！", "lines": 2},
    {"tag": "U3", "beta": -18.0, "cx": 330, "cy": 660, "bw": 420,
     "bh": 280, "jp": "クエスト更新：到達", "lines": 2, "heavy_art": True},
    {"tag": "U4", "beta": 6.0, "cx": 960, "cy": 650, "bw": 440,
     "bh": 300, "jp": "レベルアップ！魔力上昇", "lines": 3},
    {"tag": "U5", "beta": -25.0, "cx": 330, "cy": 1060, "bw": 430,
     "bh": 300, "jp": ["警告！", "緊急事態発生！！全員撤退せよ！！"],
     "lines": 2, "asymmetric": True},
    {"tag": "U6", "beta": -14.0, "cx": 960, "cy": 1050, "bw": 420,
     "bh": 300, "jp": "システム：接続断絶", "lines": 3, "dark": True},
]
S011_HORIZONTAL = [
    {"tag": "H1", "cx": 500, "cy": 1420, "bw": 430, "bh": 280,
     "jp": ["おはよう、元気だった？", "その通りだ、間違いない"]},
    {"tag": "H2", "cx": 950, "cy": 1760, "bw": 420, "bh": 280,
     "jp": ["間違いない！", "そう思う！", "よし、行こう！"]},
]
S011_VERTICAL = [
    {"tag": "V1", "cx": 180, "cy": 1760, "bw": 64, "bh": 420,
     "columns": 2},
]

JP_VERTICAL_CHARS = "縦書きのテストです"

BENGALI_PANELS = [
    "সিস্টেম সতর্কতা: শত্রু কাছে এসে গেছে, সবাই প্রস্তুত হও!",
    "দক্ষ ছড়িয়ে পড়ল!",
    "অভিযান হালনাগাদ: গন্তব্যে পৌঁছে গেছি",
    "স্তর বেড়েছে! জাদুর শক্তি বেড়েছে",
    "সাবধান! জরুরি পরিস্থিতি, সবাই সরে যাও!",
    "সিস্টেম বার্তা: সংযোগ বিচ্ছিন্ন হয়েছে",
]
BENGALI_HORIZONTAL = [
    "সকাল হলো, ভালো ঘুম হয়েছে তো?",
    "ঠিক ধরেছ, এতে কোনো সন্দেহ নেই",
]
BENGALI_VERTICAL = "এটি লম্বালম্বি লেখার পরীক্ষা"


def _rounded_panel_mask(W, H, pad, bw, bh, radius=PANEL_RADIUS):
    """System-window shape mask (rounded rect)."""
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [pad, pad, pad + bw, pad + bh], radius=radius, fill=255)
    return m


def _panel_interior_mask(W, H, pad, bw, bh):
    """Text-allowed area: rounded rect inset by the border + accent."""
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        [pad + BORDER_W + ACCENT_INSET, pad + BORDER_W + ACCENT_INSET,
         pad + bw - BORDER_W - ACCENT_INSET,
         pad + bh - BORDER_W - ACCENT_INSET],
        radius=max(4, PANEL_RADIUS - BORDER_W - ACCENT_INSET), fill=255)
    return m


def _ui_panel_block(bw, bh, text_lines, beta, font_path, base_size,
                    dark=False, pad=40):
    """System-window panel (light or dark) + beta-tilted text.

    Returns (block_rgba, ink_mask, interior_mask, line_extents):
    block_rgba is the art-tight RGBA panel; ink_mask = interior-
    clipped text ink; line_extents = per-line textlength px with the
    FITTED font (the symmetry surface for the fixture's own class
    bookkeeping).
    """
    W, H = bw + 2 * pad, bh + 2 * pad
    shape = _rounded_panel_mask(W, H, pad, bw, bh)
    interior = _panel_interior_mask(W, H, pad, bw, bh)

    fill = (DARK_FILL, DARK_FILL, DARK_FILL, 255) if dark else \
        (250, 250, 250, 255)
    border = (DARK_BORDER, DARK_BORDER, DARK_BORDER, 255) if dark else \
        (INK_GRAY, INK_GRAY, INK_GRAY, 255)
    block = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    block.paste(fill, (0, 0), shape)
    # border ring = shape minus interior-side erosion; accent = thin
    ring = ImageChops.subtract(shape, interior)
    block.paste(border, (0, 0), ring)
    if dark:
        # dark panel: thin light accent INSIDE the border band
        acc = ImageChops.subtract(
            interior.filter(ImageFilter.MinFilter(3)),
            interior.filter(ImageFilter.MinFilter(5)))
        block.paste((DARK_BORDER, DARK_BORDER, DARK_BORDER, 255),
                    (0, 0), acc)

    if not text_lines:
        return block, Image.new("L", (W, H), 0), interior, []

    strip_w = int(bw * 0.74)
    font, size = _fit_font(font_path, text_lines, strip_w - 10, base_size)
    lh = int(size * 1.55)
    strip = Image.new("L", (strip_w, lh * len(text_lines) + 12), 255)
    sd = ImageDraw.Draw(strip)
    exts = []
    for i, ln in enumerate(text_lines):
        wpx = sd.textlength(ln, font=font)
        exts.append(int(wpx))
        sd.text(((strip_w - wpx) / 2, 6 + i * lh), ln, font=font,
                fill=TEXT_GRAY)
    rot = strip.rotate(beta, expand=True, resample=Image.BICUBIC,
                       fillcolor=255)
    ink_mask = rot.point(lambda p: 255 if p < 140 else 0)
    im_full = Image.new("L", (W, H), 0)
    ox, oy = int((W - rot.width) / 2), int((H - rot.height) / 2)
    im_full.paste(ink_mask, (ox, oy))
    ink_mask = ImageChops.multiply(im_full, interior)
    tcol = (245, 245, 245, 255) if dark else (TEXT_GRAY,) * 3 + (255,)
    block.paste(tcol, (0, 0), ink_mask)
    return block, ink_mask, interior, exts


def build_s011_page(repo_root: str, jp_size: int = 30):
    """Draw the S011 page. Returns (full, clean, regions, ink_mask,
    interiors): full/clean are BGR pages (clean = panels only, text
    removed); regions carry tag/class/beta/box/jp/bengali/lines/
    line_extents (the symmetry surface); interiors = per-tag
    page-coord BOOL masks of each panel's text-allowed interior."""
    import cv2
    rng = np.random.default_rng(RNG_SEED)
    _jp_font(repo_root, jp_size)
    font_path = LOCAL_JP_COPY
    vfont = ImageFont.truetype(font_path, 22)

    bg = _page_canvas(PAGE_W, PAGE_H, rng)

    # U3's heavy-art cluster + paper-white halo (S010 E3 law): dense
    # horizontal hatch (18px strokes on a 22px pitch -> 4px light
    # gaps; every stroke core stays under the de-dilate radius) and
    # a halo rounded-rect around the panel so no art stroke touches
    # the panel border.
    import cv2 as _cv2
    u3 = next(s for s in S011_PANELS if s.get("heavy_art"))
    hx0, hx1 = int(u3["cx"] - 300), int(u3["cx"] + 300)
    hy0, hy1 = int(u3["cy"] - 210), int(u3["cy"] + 200)
    yy = hy0
    while yy < hy1:
        _cv2.line(bg, (hx0, yy), (hx1, yy), (48, 48, 48), 18)
        yy += 22
    _cv2.rectangle(bg, (int(u3["cx"] - u3["bw"] / 2) - 14,
                        int(u3["cy"] - u3["bh"] / 2) - 14),
                   (int(u3["cx"] + u3["bw"] / 2) + 14,
                    int(u3["cy"] + u3["bh"] / 2) + 14),
                   (240, 240, 240), -1)

    pil_full = Image.fromarray(_cv2.cvtColor(bg, _cv2.COLOR_BGR2RGB))
    pil_clean = pil_full.copy()
    pil_ink = Image.new("L", (PAGE_W, PAGE_H), 0)
    interiors = {}
    regions = []

    def paste_rgba(pil, block, cx, cy):
        pil.paste(block, (int(cx - block.width / 2),
                          int(cy - block.height / 2)), block)

    def paste_ink(ink_mask, cx, cy, W, H):
        pil_ink.paste(ink_mask, (int(cx - W / 2), int(cy - H / 2)))

    def tight_box(cx, cy, W, H):
        """Tight axis-aligned box of the pasted panel's ink (page
        coords). Light panels: border stroke (INK_GRAY 20); dark
        panels: the dark fill itself (DARK_FILL 62) — both are the
        panel outline, so every UI region boxes like a detector
        seeing the window."""
        arr = np.asarray(pil_full.convert("L"))
        x0 = max(0, int(cx - W / 2) - 2)
        y0 = max(0, int(cy - H / 2) - 2)
        x1 = min(pil_full.width, int(cx + W / 2) + 2)
        y1 = min(pil_full.height, int(cy + H / 2) + 2)
        sub = arr[y0:y1, x0:x1]
        ys, xs = np.nonzero(sub < 128)
        return (int(xs.min()) + x0, int(ys.min()) + y0,
                int(xs.max() - xs.min()) + 1,
                int(ys.max() - ys.min()) + 1)

    def interior_page_mask(interior, cx, cy, W, H):
        m = np.zeros((PAGE_H, PAGE_W), bool)
        blk = np.asarray(interior) > 0
        x0, y0 = int(cx - W / 2), int(cy - H / 2)
        m[y0:y0 + H, x0:x0 + W] = blk
        return m

    for k, spec in enumerate(S011_PANELS):
        dark = bool(spec.get("dark"))
        if isinstance(spec["jp"], list):
            lines = list(spec["jp"])
        else:
            lines = [spec["jp"]] * spec["lines"]
        blk, ink, interior, exts = _ui_panel_block(
            spec["bw"], spec["bh"], lines, spec["beta"], font_path,
            jp_size, dark=dark)
        W, H = blk.width, blk.height
        paste_rgba(pil_full, blk, spec["cx"], spec["cy"])
        paste_ink(ink, spec["cx"], spec["cy"], W, H)
        interiors[spec["tag"]] = interior_page_mask(
            interior, spec["cx"], spec["cy"], W, H)
        blk2, _, _, _ = _ui_panel_block(
            spec["bw"], spec["bh"], [], spec["beta"], font_path,
            jp_size, dark=dark)
        paste_rgba(pil_clean, blk2, spec["cx"], spec["cy"])
        box = tight_box(spec["cx"], spec["cy"], W, H)
        regions.append({
            "tag": spec["tag"], "box": box, "beta": spec["beta"],
            "class": "ui_dark" if dark else "ui",
            "lines": len(lines), "line_extents": exts,
            "jp": "\n".join(lines), "bengali": BENGALI_PANELS[k],
        })

    for k, spec in enumerate(S011_HORIZONTAL):
        lines = list(spec["jp"])
        W, H = spec["bw"] + 52, spec["bh"] + 52
        shape = Image.new("L", (W, H), 0)
        ImageDraw.Draw(shape).ellipse([26, 26, 26 + spec["bw"],
                                       26 + spec["bh"]], fill=255)
        interior = Image.new("L", (W, H), 0)
        ImageDraw.Draw(interior).ellipse(
            [26 + 7, 26 + 7, 26 + spec["bw"] - 7, 26 + spec["bh"] - 7],
            fill=255)
        blk = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        blk.paste((INK_GRAY, INK_GRAY, INK_GRAY, 255), (0, 0), shape)
        blk.paste((255, 255, 255, 255), (0, 0),
                  interior.filter(ImageFilter.MinFilter(1)))
        strip_w = int(spec["bw"] * 0.78)
        font, size = _fit_font(font_path, lines, strip_w - 10, jp_size)
        lh = int(size * 1.55)
        strip = Image.new("L", (strip_w, lh * len(lines) + 12), 255)
        sd = ImageDraw.Draw(strip)
        for i, ln in enumerate(lines):
            wpx = sd.textlength(ln, font=font)
            sd.text(((strip_w - wpx) / 2, 6 + i * lh), ln, font=font,
                    fill=TEXT_GRAY)
        im_full = Image.new("L", (W, H), 0)
        im_full.paste(strip, (int((W - strip_w) / 2),
                              int((H - strip.height) / 2)))
        ink = ImageChops.multiply(im_full, interior)
        blk.paste((TEXT_GRAY, TEXT_GRAY, TEXT_GRAY, 255), (0, 0), ink)
        paste_rgba(pil_full, blk, spec["cx"], spec["cy"])
        paste_ink(ink, spec["cx"], spec["cy"], W, H)
        interiors[spec["tag"]] = interior_page_mask(
            interior, spec["cx"], spec["cy"], W, H)
        blk2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        blk2.paste((INK_GRAY, INK_GRAY, INK_GRAY, 255), (0, 0), shape)
        blk2.paste((255, 255, 255, 255), (0, 0),
                   interior.filter(ImageFilter.MinFilter(1)))
        paste_rgba(pil_clean, blk2, spec["cx"], spec["cy"])
        box = tight_box(spec["cx"], spec["cy"], W, H)
        regions.append({
            "tag": spec["tag"], "box": box, "beta": 0.0,
            "class": "horizontal", "lines": len(lines),
            "line_extents": [int(sd.textlength(ln, font=font))
                             for ln in lines],
            "jp": "\n".join(lines), "bengali": BENGALI_HORIZONTAL[k],
        })

    for spec in S011_VERTICAL:
        blk, vmask = _vertical_note_block(
            spec["bw"], spec["bh"], JP_VERTICAL_CHARS, spec["columns"],
            vfont, 22)
        W, H = blk.width, blk.height
        pil_full.paste(blk, (int(spec["cx"] - W / 2),
                             int(spec["cy"] - H / 2)))
        pil_clean.paste(blk, (int(spec["cx"] - W / 2),
                              int(spec["cy"] - H / 2)))
        paste_ink(vmask, spec["cx"], spec["cy"], W, H)
        box = tight_box(spec["cx"], spec["cy"], W, H)
        m = np.zeros((PAGE_H, PAGE_W), bool)
        m[int(spec["cy"] - H / 2) + 20:int(spec["cy"] + H / 2) - 20,
          int(spec["cx"] - W / 2) + 20:int(spec["cx"] + W / 2) - 20] = \
            True
        interiors[spec["tag"]] = m
        regions.append({
            "tag": spec["tag"], "box": box, "beta": 0.0,
            "class": "vertical", "lines": 1, "line_extents": [],
            "jp": JP_VERTICAL_CHARS, "bengali": BENGALI_VERTICAL,
        })

    full_bgr = _cv2.cvtColor(np.asarray(pil_full), _cv2.COLOR_RGB2BGR)
    clean_bgr = _cv2.cvtColor(np.asarray(pil_clean), _cv2.COLOR_RGB2BGR)
    text_ink_mask = np.asarray(pil_ink)
    return full_bgr, clean_bgr, regions, text_ink_mask, interiors


def ground_truth_angles(regions):
    return {r["tag"]: r["beta"] for r in regions}
