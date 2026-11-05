#!/usr/bin/env python3
"""MANGABD-009 B2 RF-17 — S010-class owner-style page builder (shared).

The Owner's visual REJECT on 57ac480 named three defects:
  D1 burst bubble  — multi-line original renders as ONE line, steep
     angle, text clipped at the bubble edge (ink outside the bubble);
  D2 one tilted bubble renders COMPLETELY EMPTY (text lost);
  D3 tilted bubbles' line-break pattern / lean magnitude does not
     visually match the original ("অনেক তফাৎ").

This module draws the OWNER-STYLE page class that exercises them:

  * BURST bubbles — near-upright base ellipse ring + outward triangular
    spikes (10-24px thick, 24-46px long, 12-16 of them) + beta-tilted
    multi-line text clipped to the base-ellipse interior. The tight ink
    bbox includes the spike tips, so the axis-aligned region box is much
    larger than the interior — the D1 surface (spike-inflated bboxes;
    interior-blind fit dims and bbox-mean color sampling).
  * ELLIPSE bubbles — as S009, but pasted art-tight (masked composite:
    the page art runs right up to the ring; no protective white margin),
    so region bboxes catch background art — part of the D1/D2 surface.
  * E3 sits over a HATCHED DARK PANEL with a white halo separating the
    bubble from the art (standard manga separation over dark
    backgrounds): the detector sees a dark cluster and returns a sloppy
    box the size of the panel, the box mean on the inpainted page drops
    below the 160 white-text threshold while the bubble interior stays
    white -> white text on white interior (invisible) — the hard D2
    case. The hatch strokes are 22px thick on a 26px pitch (4px light
    gaps): dark enough to flip the color decision, yet each stroke core
    is <= 2x14px so the RF-17 ring-margin swallow eats it and the light
    gaps keep the estimator's border flood connected through the panel.
  * Horizontal ellipses + a V-3 vertical note — stability controls.

Fixture laws learned the hard way (v2/v3 lessons, kept so the fixture
keeps measuring the PIPELINE and not the fixture):
  * ring strokes are drawn at INK_GRAY 20 in a 7px band — a 4px band
    at gray 96 leaked after the shape/interior composite AA + BICUBIC
    ring tilt, the border flood poured into every bubble and all
    angles snapped to 0.00;
  * every bubble carries EXPLICIT jp lines sized so the fitted font
    stays >= ~26px (small text fragments under the estimator's
    despeckle and the ink cloud degrades);
  * text strips are 0.70-0.78 of the bubble width so the rotated
    strip's corners stay INSIDE the interior ellipse (0.80+ clipped
    the line ends and biased the ink-cloud PCA);
  * no cross-hatching (crossing strokes form locally-thicker blobs
    that survive the margin swallow and contaminate the PCA).

Ground-truth law (unchanged): a text strip drawn horizontal then
rotated with PIL .rotate(beta, expand=True) measures pil == beta
(cell-10 battery Test 16 law).

Shared by:
  * scripts/m009_b2_rf17_repro.py      (D1/D2/D3 pre/post-fix proof)
  * cell-10 battery Test 21            (compact inline variant)
  * scripts/m009_b2_rf17_s010_build.py (samples/S010_burst archive)
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

from m009_b2_rf16_page import (
    LOCAL_JP_COPY, _fit_font, _jp_font, _page_canvas,
    _vertical_note_block,
)

INK_GRAY = 20            # solid manga line-ink: safely under the
                         # pipeline's gray<100 ink threshold, even
                         # after the double AA of the shape/interior
                         # composite + BICUBIC ring tilt (S009 law)
TEXT_GRAY = 10
PAGE_W, PAGE_H = 1300, 2000
RNG_SEED = 20261102
RING_BAND = 7            # ring band thickness: the RGBA composite
                         # (dark shape + white interior) costs ~2px of
                         # threshold-solid band to AA on BOTH edges,
                         # and the ring tilt one more — 7px drawn keeps
                         # a closed ~3px ink core (a 4px band leaked
                         # in v2: flood poured in, enclosed ink =
                         # glyph-center crumbs only)

# ── the S010 owner-style page: 3 bursts + 4 tilted ellipses + 2 H + 1 V ──
# Fixture laws (v2-v4 lessons, kept so the fixture measures the
# PIPELINE and not the fixture):
#  * jp = ONE line per bubble, repeated to the line count (S009 law:
#    identical centered lines form a perfect rectangle whose ink-cloud
#    PCA == the strip rotation angle EXACTLY; distinct line lengths
#    bias the PCA by up to ~5 deg — v3 lesson);
#  * 2-line blocks on tilted bubbles (3-line blocks in ~1.3-aspect
#    ellipses always poke their corners out and the interior clip
#    biases the cloud — v3 lesson);
#  * the fitted font stays >= ~25px (small text fragments under the
#    estimator's despeckle — v2 lesson);
#  * strips are 0.70 (bursts) / 0.78 (ellipses) of the bubble width so
#    the rotated strip corners stay inside the interior ellipse
#    (0.80+ clipped the line ends — v2 lesson).
S010_BURSTS = [
    {"tag": "BU1", "beta": -12.0, "cx": 320, "cy": 250, "bw": 330,
     "bh": 250, "jp": "うわああ！！", "lines": 2,
     "n_spikes": 14, "spike_len": (26, 42), "spike_th": (10, 16)},
    {"tag": "BU2", "beta": 16.0, "cx": 960, "cy": 250, "bw": 330,
     "bh": 230, "jp": "逃げろー！！", "lines": 2,
     "n_spikes": 12, "spike_len": (28, 46), "spike_th": (10, 16)},
    {"tag": "BU3", "beta": -20.0, "cx": 320, "cy": 640, "bw": 280,
     "bh": 240, "jp": "何だこれ！？", "lines": 2,
     "n_spikes": 16, "spike_len": (24, 40), "spike_th": (14, 24)},
]
S010_ELLIPSES = [
    {"tag": "E1", "beta": -15.0, "cx": 950, "cy": 640, "bw": 380,
     "bh": 300, "jp": "待って、話が違う！", "lines": 2},
    {"tag": "E2", "beta": 10.0, "cx": 320, "cy": 1010, "bw": 400,
     "bh": 270, "jp": "そういうことだったのか…", "lines": 2},
    {"tag": "E3", "beta": -22.0, "cx": 950, "cy": 1025, "bw": 270,
     "bh": 215, "jp": "来てくれ！", "lines": 2,
     "heavy_art": True, "pad": 90},  # the D2 bubble
    {"tag": "E4", "beta": 18.0, "cx": 500, "cy": 1380, "bw": 410,
     "bh": 310, "jp": "絶対におかしい！", "lines": 2},
]
S010_HORIZONTAL = [
    {"tag": "H1", "cx": 950, "cy": 1380, "bw": 390, "bh": 260,
     "jp": ["おはよう、元気だった？", "その通りだ、間違いない"]},
    {"tag": "H2", "cx": 500, "cy": 1740, "bw": 420, "bh": 280,
     "jp": ["間違いない！", "そう思う！", "よし、行こう！"]},
]
S010_VERTICAL = [
    {"tag": "V1", "cx": 1130, "cy": 1740, "bw": 64, "bh": 420,
     "columns": 2},
]

# legacy pools (kept for the compact battery Test-21 variant)
JP_BURST_LINES = [
    "うわあ！！",
    "逃げろー！！",
    "ドカーン！",
]
JP_VERTICAL_CHARS = "縦書きのテストです"

BENGALI_BURSTS = [
    "এই কী হয়েছে বলো তো? আমি কিছুই বুঝতে পারছি না!",
    "সবাই পালাও! তাড়াতাড়ি এদিকে আয়!",
    "বিকট শব্দ করে বিস্ফোরণ হলো দেখে সবাই জমে গেল!",
]
BENGALI_ELLIPSES = [
    "থামো তো, কথাটা তো আগে বলিনি এমন লাগছে!",
    "আচ্ছা, তাহলে ব্যাপারটা এমন ছিল কি…",
    "জলদি এদিকে এসো, একা থেকো না যেন!",
    "মাপ করো কিন্তু, এতে একটা গরমিল আছে!",
]
BENGALI_HORIZONTAL = [
    "সকাল হলো, ভালো ঘুম হয়েছে তো?",
    "ঠিক ধরেছ, এতে কোনো সন্দেহ নেই",
]
BENGALI_VERTICAL = "এটি লম্বালম্বি লেখার পরীক্ষা"


def _ellipse_pt(a, bw, bh):
    """Point on the base-ellipse boundary at angle a (ellipse param)."""
    return (np.cos(a) * (bw / 2.0), np.sin(a) * (bh / 2.0))


def _burst_shape_mask(W, H, pad, bw, bh, n_spikes, spike_len, spike_th,
                      rng):
    """Burst ring: closed spike polygon around the base ellipse.

    Returns (shape_mask, interior_mask): shape = everything the bubble
    paints (base ellipse fill + ring stroke + spikes); interior = the
    base ellipse eroded RING_BAND px (text-allowed area, spikes
    excluded).
    """
    import math
    shape = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shape)
    cx, cy = pad + bw / 2.0, pad + bh / 2.0
    # one closed polygon: ellipse sampled densely, spikes inserted as
    # base(t0)-tip(t)-base(t1) triples — connected ink, closed ring.
    pts = []
    n_ell = 180
    spike_at = {}
    for s in range(n_spikes):
        t = (2 * math.pi * s) / n_spikes + rng.uniform(-0.06, 0.06)
        ln = rng.uniform(*spike_len)
        half = rng.uniform(*spike_th) / 2.0
        spike_at[t] = (ln, half)
    t = 0.0
    while t <= 2 * math.pi + 1e-9:
        for ts, (ln, half) in sorted(spike_at.items()):
            if abs(ts - t) < (2 * math.pi / n_ell) / 2:
                bx, by = _ellipse_pt(ts - 0.10, bw, bh)
                ex, ey = _ellipse_pt(ts + 0.10, bw, bh)
                tx, ty = _ellipse_pt(ts, bw, bh)
                nrm = math.hypot(tx, ty) or 1.0
                ux, uy = tx / nrm, ty / nrm
                tipx, tipy = tx + ux * ln, ty + uy * ln
                b0 = (cx + bx * 1.03, cy + by * 1.03)
                b1 = (cx + ex * 1.03, cy + ey * 1.03)
                pts.extend([b0, (cx + tipx, cy + tipy), b1])
                t = ts + 0.11
                break
        x, y = _ellipse_pt(t, bw, bh)
        pts.append((cx + x, cy + y))
        t += 2 * math.pi / n_ell
    d.polygon(pts, fill=255)
    interior = Image.new("L", (W, H), 0)
    ImageDraw.Draw(interior).ellipse(
        [pad + RING_BAND, pad + RING_BAND,
         pad + bw - RING_BAND, pad + bh - RING_BAND], fill=255)
    return shape, interior


def _burst_block(bw, bh, ring_tilt, text_lines, beta, font_path,
                 base_size, n_spikes, spike_len, spike_th, rng, pad=60):
    """Burst bubble block (white-filled, spikes out) + tilted text.

    Returns (block_rgba, bands, ink_mask, interior_mask): block_rgba is
    RGBA with alpha = the burst shape (art-tight composite ready); ink
    = ellipse-clipped text ink; interior = the base-ellipse text-allowed
    area (block coords).
    """
    W, H = bw + 2 * pad, bh + 2 * pad
    shape, interior = _burst_shape_mask(
        W, H, pad, bw, bh, n_spikes, spike_len, spike_th, rng)
    # white-filled burst with dark outline: draw the shape dark, then
    # the interior white on top — the ring band is the shape-minus-
    # interior gap (RING_BAND px by construction).
    dark = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dark.paste((INK_GRAY, INK_GRAY, INK_GRAY, 255), (0, 0), shape)
    white = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    white.paste((255, 255, 255, 255), (0, 0),
                interior.filter(ImageFilter.MinFilter(1)))
    block = Image.alpha_composite(dark, white)
    if abs(ring_tilt) > 0.05:
        block = block.rotate(ring_tilt, expand=False,
                             resample=Image.BICUBIC)
        interior = interior.rotate(ring_tilt, expand=False,
                                   resample=Image.BICUBIC, fillcolor=0)
        shape = shape.rotate(ring_tilt, expand=False,
                             resample=Image.BICUBIC, fillcolor=0)
    if not text_lines:
        return block, [], Image.new("L", (W, H), 0), interior
    strip_w = int(bw * 0.70)
    font, size = _fit_font(font_path, text_lines, strip_w - 10, base_size)
    lh = int(size * 1.55)
    strip = Image.new("L", (strip_w, lh * len(text_lines) + 12), 255)
    sd = ImageDraw.Draw(strip)
    for i, ln in enumerate(text_lines):
        wpx = sd.textlength(ln, font=font)
        sd.text(((strip_w - wpx) / 2, 6 + i * lh), ln, font=font,
                fill=TEXT_GRAY)
    rot = strip.rotate(beta, expand=True, resample=Image.BICUBIC,
                       fillcolor=255)
    ink_mask = rot.point(lambda p: 255 if p < 140 else 0)
    im_full = Image.new("L", (W, H), 0)
    ox, oy = int((W - rot.width) / 2), int((H - rot.height) / 2)
    im_full.paste(ink_mask, (ox, oy))
    ink_mask = ImageChops.multiply(im_full, interior)
    block.paste((TEXT_GRAY, TEXT_GRAY, TEXT_GRAY, 255), (0, 0), ink_mask)
    # per-line rotated-rect bands (block coords) — ground-truth bookkeeping
    import math
    t = math.radians(beta)
    ca, sa = math.cos(t), math.sin(t)
    scx, scy = strip_w / 2.0, strip.height / 2.0
    bands = []
    for i, ln in enumerate(text_lines):
        bx0, by0, bx1, by1 = sd.textbbox(
            ((strip_w - sd.textlength(ln, font=font)) / 2, 6 + i * lh),
            ln, font=font)
        corners = np.array([[bx0, by0], [bx1, by0], [bx1, by1],
                            [bx0, by1]], dtype=np.float64)
        corners = corners - np.array([scx, scy])
        rc = np.stack([corners[:, 0] * ca + corners[:, 1] * sa,
                       -corners[:, 0] * sa + corners[:, 1] * ca], axis=1)
        rc = rc + np.array([scx, scy]) + np.array([ox, oy])
        bands.append(rc)
    return block, bands, ink_mask, interior


def _ellipse_block_arttight(bw, bh, ring_tilt, text_lines, beta,
                            font_path, base_size, pad=26):
    """Ellipse bubble as RGBA (alpha = filled ellipse + ring) — the
    art-tight S010 variant of S009's _tilted_bubble_block."""
    W, H = bw + 2 * pad, bh + 2 * pad
    shape = Image.new("L", (W, H), 0)
    ImageDraw.Draw(shape).ellipse([pad, pad, pad + bw, pad + bh],
                                  fill=255)
    interior = Image.new("L", (W, H), 0)
    ImageDraw.Draw(interior).ellipse(
        [pad + RING_BAND, pad + RING_BAND,
         pad + bw - RING_BAND, pad + bh - RING_BAND], fill=255)
    block = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    block.paste((INK_GRAY, INK_GRAY, INK_GRAY, 255), (0, 0), shape)
    block.paste((255, 255, 255, 255), (0, 0),
                interior.filter(ImageFilter.MinFilter(1)))
    if abs(ring_tilt) > 0.05:
        block = block.rotate(ring_tilt, expand=False,
                             resample=Image.BICUBIC)
        interior = interior.rotate(ring_tilt, expand=False,
                                   resample=Image.BICUBIC, fillcolor=0)
        shape = shape.rotate(ring_tilt, expand=False,
                             resample=Image.BICUBIC, fillcolor=0)
    if not text_lines:
        return block, [], Image.new("L", (W, H), 0), interior
    strip_w = int(bw * 0.78)
    font, size = _fit_font(font_path, text_lines, strip_w - 10, base_size)
    lh = int(size * 1.55)
    strip = Image.new("L", (strip_w, lh * len(text_lines) + 12), 255)
    sd = ImageDraw.Draw(strip)
    for i, ln in enumerate(text_lines):
        wpx = sd.textlength(ln, font=font)
        sd.text(((strip_w - wpx) / 2, 6 + i * lh), ln, font=font,
                fill=TEXT_GRAY)
    rot = strip.rotate(beta, expand=True, resample=Image.BICUBIC,
                       fillcolor=255)
    ink_mask = rot.point(lambda p: 255 if p < 140 else 0)
    im_full = Image.new("L", (W, H), 0)
    ox, oy = int((W - rot.width) / 2), int((H - rot.height) / 2)
    im_full.paste(ink_mask, (ox, oy))
    ink_mask = ImageChops.multiply(im_full, interior)
    block.paste((TEXT_GRAY, TEXT_GRAY, TEXT_GRAY, 255), (0, 0), ink_mask)
    return block, [], ink_mask, interior


def build_s010_page(repo_root: str, jp_size: int = 30):
    """Draw the S010 page. Returns (full, clean, regions, ink_mask,
    interiors): full/clean are BGR pages (clean = rings only); regions
    carry tag/class/beta/box/jp/bengali/lines; interiors = per-tag
    page-coord BOOL masks of each bubble's text-allowed interior (the
    A2 audit surface)."""
    import cv2
    rng = np.random.default_rng(RNG_SEED)
    _jp_font(repo_root, jp_size)
    font_path = LOCAL_JP_COPY
    vfont = ImageFont.truetype(font_path, 22)

    bg = _page_canvas(PAGE_W, PAGE_H, rng)
    # E3's hatched dark panel + halo (deterministic): HORIZONTAL hatch
    # strokes (22px thick on a 26px pitch -> 4px light gaps) over the
    # panel zone, then a paper-white halo ellipse around the E3 bubble
    # (standard manga separation over dark art). The halo kills any
    # ring-hatch junction so the enclosed-ink isolation sees a clean
    # closed ring; the 4px gaps keep the estimator's border flood
    # connected through the panel; every stroke core is <= 2x14px so
    # the RF-17 ring-margin swallow eats it (the estimator keeps
    # seeing text ink only).
    import cv2 as _cv2
    e3 = next(s for s in S010_ELLIPSES if s.get("heavy_art"))
    hx0, hx1 = int(e3["cx"] - 260), int(e3["cx"] + 260)
    hy0, hy1 = int(e3["cy"] - 185), int(e3["cy"] + 170)
    yy = hy0
    while yy < hy1:
        _cv2.line(bg, (hx0, yy), (hx1, yy), (50, 50, 50), 22)
        yy += 26
    _cv2.ellipse(bg, (int(e3["cx"]), int(e3["cy"])),
                 (int(e3["bw"] / 2) + 16, int(e3["bh"] / 2) + 16),
                 0, 0, 360, (238, 238, 238), -1)

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

    def box_after_paste(cx, cy, W, H):
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

    for k, spec in enumerate(S010_BURSTS):
        ring_tilt = float(rng.uniform(-3.0, 3.0))
        lines = [spec["jp"]] * spec["lines"]
        blk, bands, ink, interior = _burst_block(
            spec["bw"], spec["bh"], ring_tilt, lines, spec["beta"],
            font_path, jp_size, spec["n_spikes"], spec["spike_len"],
            spec["spike_th"], rng)
        W, H = blk.width, blk.height
        paste_rgba(pil_full, blk, spec["cx"], spec["cy"])
        paste_ink(ink, spec["cx"], spec["cy"], W, H)
        interiors[spec["tag"]] = interior_page_mask(
            interior, spec["cx"], spec["cy"], W, H)
        # clean page: burst without text
        blk2, _, _, interior2 = _burst_block(
            spec["bw"], spec["bh"], ring_tilt, [], spec["beta"],
            font_path, jp_size, spec["n_spikes"], spec["spike_len"],
            spec["spike_th"], rng)
        paste_rgba(pil_clean, blk2, spec["cx"], spec["cy"])
        box = box_after_paste(spec["cx"], spec["cy"], W, H)
        off = np.array([spec["cx"] - W / 2, spec["cy"] - H / 2])
        regions.append({
            "tag": spec["tag"], "box": box, "beta": spec["beta"],
            "class": "burst", "lines": len(lines),
            "line_bands": [b + off for b in bands],
            "jp": "\n".join(lines), "bengali": BENGALI_BURSTS[k],
        })

    for k, spec in enumerate(S010_ELLIPSES):
        ring_tilt = float(rng.uniform(-3.0, 3.0))
        lines = [spec["jp"]] * spec["lines"]
        blk, bands, ink, interior = _ellipse_block_arttight(
            spec["bw"], spec["bh"], ring_tilt, lines, spec["beta"],
            font_path, jp_size, pad=spec.get("pad", 26))
        W, H = blk.width, blk.height
        paste_rgba(pil_full, blk, spec["cx"], spec["cy"])
        paste_ink(ink, spec["cx"], spec["cy"], W, H)
        interiors[spec["tag"]] = interior_page_mask(
            interior, spec["cx"], spec["cy"], W, H)
        blk2, _, _, _ = _ellipse_block_arttight(
            spec["bw"], spec["bh"], ring_tilt, [], spec["beta"],
            font_path, jp_size, pad=spec.get("pad", 26))
        paste_rgba(pil_clean, blk2, spec["cx"], spec["cy"])
        box = box_after_paste(spec["cx"], spec["cy"], W, H)
        regions.append({
            "tag": spec["tag"], "box": box, "beta": spec["beta"],
            "class": "tilted", "lines": len(lines),
            "line_bands": [], "jp": "\n".join(lines),
            "bengali": BENGALI_ELLIPSES[k],
        })

    for k, spec in enumerate(S010_HORIZONTAL):
        lines = list(spec["jp"])
        blk, _, ink, interior = _ellipse_block_arttight(
            spec["bw"], spec["bh"], 0.0, lines, 0.0, font_path, jp_size)
        W, H = blk.width, blk.height
        paste_rgba(pil_full, blk, spec["cx"], spec["cy"])
        paste_ink(ink, spec["cx"], spec["cy"], W, H)
        interiors[spec["tag"]] = interior_page_mask(
            interior, spec["cx"], spec["cy"], W, H)
        blk2, _, _, _ = _ellipse_block_arttight(
            spec["bw"], spec["bh"], 0.0, [], 0.0, font_path, jp_size)
        paste_rgba(pil_clean, blk2, spec["cx"], spec["cy"])
        box = box_after_paste(spec["cx"], spec["cy"], W, H)
        regions.append({
            "tag": spec["tag"], "box": box, "beta": 0.0,
            "class": "horizontal", "lines": len(lines),
            "line_bands": [], "jp": "\n".join(lines),
            "bengali": BENGALI_HORIZONTAL[k],
        })

    for spec in S010_VERTICAL:
        blk, vmask = _vertical_note_block(
            spec["bw"], spec["bh"], JP_VERTICAL_CHARS, spec["columns"],
            vfont, 22)
        W, H = blk.width, blk.height
        pil_full.paste(blk, (int(spec["cx"] - W / 2),
                             int(spec["cy"] - H / 2)))
        pil_clean.paste(blk, (int(spec["cx"] - W / 2),
                              int(spec["cy"] - H / 2)))
        paste_ink(vmask, spec["cx"], spec["cy"], W, H)
        box = box_after_paste(spec["cx"], spec["cy"], W, H)
        # interior = the note-box inside area (border excluded)
        m = np.zeros((PAGE_H, PAGE_W), bool)
        m[int(spec["cy"] - H / 2) + 20:int(spec["cy"] + H / 2) - 20,
          int(spec["cx"] - W / 2) + 20:int(spec["cx"] + W / 2) - 20] = \
            True
        interiors[spec["tag"]] = m
        regions.append({
            "tag": spec["tag"], "box": box, "beta": 0.0,
            "class": "vertical", "lines": 1, "line_bands": [],
            "jp": JP_VERTICAL_CHARS, "bengali": BENGALI_VERTICAL,
        })

    full_bgr = _cv2.cvtColor(np.asarray(pil_full), _cv2.COLOR_RGB2BGR)
    clean_bgr = _cv2.cvtColor(np.asarray(pil_clean), _cv2.COLOR_RGB2BGR)
    text_ink_mask = np.asarray(pil_ink)
    return full_bgr, clean_bgr, regions, text_ink_mask, interiors


def ground_truth_angles(regions):
    return {r["tag"]: r["beta"] for r in regions}
