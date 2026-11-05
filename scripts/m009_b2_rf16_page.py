#!/usr/bin/env python3
"""MANGABD-009 B2 RF-16 — S009-class diagonal test page builder (shared).

Owner-class geometry (the LIVE REJECT signature on dc612d5: 7 tilted
bubbles, 1/7 inherited, df angles 0.00 on truly tilted regions):

  * bubble rings are NEARLY-UPRIGHT ellipses (tilt ~0 +/- 3 deg,
    aspect 1.2-1.5, 4px stroke) — the classic manga look of calm
    bubbles carrying DYNAMIC (tilted) dialogue;
  * the TEXT inside is tilted at beta (the ground-truth orientation
    the B2 feature must inherit);
  * background screentone + art strokes leak inside the axis-aligned
    region boxes (the "ring + background" dilution surface).

Ground-truth law (same construction as the cell-10 battery's
_b2t_page, Test 16): a text strip drawn horizontal then rotated with
PIL .rotate(beta, expand=True) measures pil_angle == beta for
|beta| < 45.

This module is shared by:
  * scripts/m009_b2_rf16_repro.py    (base-bytes failure proof)
  * scripts/m009_b2_rf16_verify.py    (fixed-bytes gate: census +
                                      full-chain render)
  * scripts/m009_b2_rf16_s009_build.py (samples/S009_diagonal archive)
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO_ASSET_JP = "assets/fonts/NotoSansJP[wght].ttf"
LOCAL_JP_COPY = "/tmp/m009_rf16_NotoSansJP.ttf"     # PIL dislikes [wght] in path
LOCAL_BENGALI = "/home/z/my-project/m009_work/fonts/NotoSansBengali-Regular.ttf"

# ── the Owner's diagonal test page: 7 tilted + 2 horizontal + 1 vertical ──
# beta = ground-truth TEXT tilt (deg). All |beta| in [8, 25]: safely inside
# the tilted band, clear of the 5 deg snap on both sides of the +/-3 tol.
S009_TILTED = [
    {"tag": "T1", "beta": -15.0, "cx": 300, "cy": 230,  "bw": 400, "bh": 280, "lines": 3},
    {"tag": "T2", "beta": 12.0,  "cx": 950, "cy": 230,  "bw": 380, "bh": 260, "lines": 2},
    {"tag": "T3", "beta": -9.0,  "cx": 300, "cy": 590,  "bw": 420, "bh": 290, "lines": 3},
    {"tag": "T4", "beta": 20.0,  "cx": 950, "cy": 590,  "bw": 370, "bh": 250, "lines": 2},
    {"tag": "T5", "beta": -18.0, "cx": 300, "cy": 950,  "bw": 400, "bh": 280, "lines": 3},
    {"tag": "T6", "beta": 8.0,   "cx": 950, "cy": 950,  "bw": 430, "bh": 290, "lines": 3},
    {"tag": "T7", "beta": -25.0, "cx": 300, "cy": 1310, "bw": 390, "bh": 260, "lines": 2},
]
S009_HORIZONTAL = [
    {"tag": "H1", "cx": 950, "cy": 1310, "bw": 400, "bh": 270, "lines": 2},
    {"tag": "H2", "cx": 500, "cy": 1670, "bw": 430, "bh": 280, "lines": 3},
]
S009_VERTICAL = [
    {"tag": "V1", "cx": 1150, "cy": 1670, "bw": 64, "bh": 420, "columns": 2},
]

PAGE_W, PAGE_H = 1300, 2000
RNG_SEED = 20261031

# Each bubble repeats ONE identical line (mass-symmetric typesetting:
# pixel-PCA of the text ink then tracks the baseline to ~1 deg — the
# Test-16 construction class; varied per-bubble content). S009 is a
# SYNTHESIZED regression fixture (disclosed in metadata.json): its job
# is to pin the estimator class, not to imitate art.
JP_TILTED_LINES = [
    "危ない！早く逃げろ！！",
    "待って、話を聞いて！",
    "そういうことだったのか",
    "冗談じゃないだろ？！",
    "急いで！時間がない！！",
    "大丈夫、私がいるから",
    "まさか、そんな馬鹿な…",
]
JP_HORIZONTAL_LINES = [
    "おはよう、元気だった？",
    "その通りだ、間違いない",
]
JP_VERTICAL_CHARS = "縦書きのテストです"

BENGALI_TILTED = [
    "চুপ করে শোনো, কী বলছি!",
    "এটা কী সব হচ্ছে বলো তো?",
    "আমি বুঝতে পারছি না কিছুই!",
    "দাঁড়াও! পিছিয়ে যেও না!",
    "সবাই সরে যাও এখনই!",
    "কী সাংঘাতিক ব্যাপার এটা!",
    "আর এক মিনিট দাঁড়াও না!",
]
BENGALI_HORIZONTAL = [
    "শুভ সকাল! আজ খুব ভালো লাগছে।",
    "ঠিক তাই, আমিও তা ভাবছিলাম।",
]
BENGALI_VERTICAL = "এটা একটা লম্বা উল্লেখ।"

RING_GRAY = 20
RING_TILT_MAX = 3.0      # ring ellipse itself stays near-upright (+/- 3 deg)


def _jp_font(repo_root: str, size: int) -> ImageFont.FreeTypeFont:
    import os
    import shutil
    src = os.path.join(repo_root, REPO_ASSET_JP)
    if not os.path.exists(LOCAL_JP_COPY) or \
            os.path.getmtime(LOCAL_JP_COPY) < os.path.getmtime(src):
        shutil.copy(src, LOCAL_JP_COPY)
    return ImageFont.truetype(LOCAL_JP_COPY, size)


def _page_canvas(w: int, h: int, rng) -> np.ndarray:
    """Light-art background: gray paper + screentone + art strokes."""
    import cv2
    bg = np.full((h, w, 3), 238, np.uint8)
    for yy in range(0, h, 8):
        for xx in range(0, w, 8):
            if (xx // 8 + yy // 8) % 2 == 0:
                bg[yy, xx] = 205
    for _ in range(30):
        x1, y1 = int(rng.uniform(0, w)), int(rng.uniform(0, h))
        x2 = x1 + int(rng.uniform(-170, 170))
        y2 = y1 + int(rng.uniform(-170, 170))
        cv2.line(bg, (x1, y1), (x2, y2), (60, 60, 60),
                 int(rng.uniform(2, 5)))
    return bg


def _fit_font(font_path, text_lines, max_w, base_size):
    """Largest size <= base_size whose longest line fits max_w."""
    from PIL import ImageDraw as _ID
    probe = _ID.Draw(Image.new("L", (8, 8)))
    size = int(base_size)
    while size > 13:
        f = ImageFont.truetype(font_path, size)
        if max(probe.textlength(ln, font=f) for ln in text_lines) <= max_w:
            return f, size
        size -= 1
    return ImageFont.truetype(font_path, 13), 13


def _tilted_bubble_block(bw, bh, ring_tilt, text_lines, beta, font_path,
                          base_size, pad=26):
    """Ellipse ring (near-upright) + beta-tilted text, on a white block.

    Returns (block, bands, ink_mask): ink_mask = the final ellipse-clipped
    text-ink L-mask (block coords) — the ideal text surface for CTD
    stand-ins and the archive text_mask; bands = per-LINE rotated quads
    of each line's tight ink bbox (documentation / visualization).
    """
    W, H = bw + 2 * pad, bh + 2 * pad
    block = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(block)
    # near-upright ring: slight tilt for realism
    rt = ring_tilt
    d.ellipse([pad, pad, pad + bw, pad + bh], fill=(255, 255, 255),
              outline=(RING_GRAY, RING_GRAY, RING_GRAY), width=4)
    # ellipse-interior mask (3px inside the ring stroke), same rotation as
    # the ring — the text ink is CLIPPED to it: typesetters keep dialogue
    # inside the bubble, and the estimator's enclosed-interior math assumes
    # exactly that.
    from PIL import ImageChops
    interior = Image.new("L", (W, H), 0)
    ImageDraw.Draw(interior).ellipse(
        [pad + 3, pad + 3, pad + bw - 3, pad + bh - 3], fill=255)
    if abs(rt) > 0.05:
        block = block.rotate(rt, expand=False, resample=Image.BICUBIC,
                             fillcolor=(255, 255, 255))
        interior = interior.rotate(rt, expand=False,
                                   resample=Image.BICUBIC, fillcolor=0)
    # text: horizontal strip, rotated by beta, pasted at ring center.
    # INK-ONLY paste (mask): the strip rectangle must never overwrite the
    # ring stroke (a broken ring changes the estimator's ink geometry).
    strip_w = int(bw * 0.85)
    if not text_lines:
        return block, [], Image.new("L", (W, H), 0)
    font, size = _fit_font(font_path, text_lines, strip_w - 10, base_size)
    lh = int(size * 1.55)
    strip = Image.new("L", (strip_w, lh * len(text_lines) + 12), 255)
    sd = ImageDraw.Draw(strip)
    for i, ln in enumerate(text_lines):
        wpx = sd.textlength(ln, font=font)
        sd.text(((strip_w - wpx) / 2, 6 + i * lh), ln, font=font, fill=0)
    rot = strip.rotate(beta, expand=True, resample=Image.BICUBIC,
                       fillcolor=255)
    ink_mask = rot.point(lambda p: 255 if p < 140 else 0)
    # clip text ink to the ellipse interior (never crosses the ring)
    im_full = Image.new("L", (W, H), 0)
    ox, oy = int((W - rot.width) / 2), int((H - rot.height) / 2)
    im_full.paste(ink_mask, (ox, oy))
    ink_mask = ImageChops.multiply(im_full, interior)
    block.paste((10, 10, 10), (0, 0), ink_mask)

    # per-line rotated-rect bands (block coords): each line's TIGHT INK
    # bbox (textbbox — what a CTD textline quad hugs), rotated by beta
    # about the strip center, offset to block. PIL .rotate(beta) turns a
    # direction theta into theta - beta in this y-down frame (empirical
    # Test-16 law: strip(beta) ink tilt == -beta), so the point map is
    # (x, y) -> (x*c + y*s, -x*s + y*c).
    t = np.radians(beta)
    ca, sa = np.cos(t), np.sin(t)
    scx, scy = strip_w / 2.0, strip.height / 2.0
    bands = []
    for i, ln in enumerate(text_lines):
        bx0, by0, bx1, by1 = sd.textbbox(
            ((strip_w - sd.textlength(ln, font=font)) / 2, 6 + i * lh),
            ln, font=font)
        corners = np.array([
            [bx0, by0], [bx1, by0], [bx1, by1], [bx0, by1]],
            dtype=np.float64)
        corners = corners - np.array([scx, scy])
        rc = np.stack([
            corners[:, 0] * ca + corners[:, 1] * sa,
            -corners[:, 0] * sa + corners[:, 1] * ca], axis=1)
        rc = rc + np.array([scx, scy]) + np.array([ox, oy])
        bands.append(rc)
    return block, bands, ink_mask


def _vertical_note_block(bw: int, bh: int, chars: str, columns: int,
                         font: ImageFont.FreeTypeFont, size: int,
                         pad: int = 18):
    """Tall-narrow vertical note: box border + vertical JP columns.

    Returns (block, ink_mask): ink_mask = the drawn characters only
    (the box border is NOT text ink — same ring-vs-text split as the
    bubbles), block coords.
    """
    W, H = bw + 2 * pad, bh + 2 * pad
    block = Image.new("RGB", (W, H), (255, 255, 255))
    ink_mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(block)
    dm = ImageDraw.Draw(ink_mask)
    d.rectangle([pad, pad, pad + bw, pad + bh], fill=(255, 255, 255),
                outline=(RING_GRAY, RING_GRAY, RING_GRAY), width=3)
    step = int(size * 1.35)
    per = (bh - 24) // step
    chars = chars[: per * columns]
    for c in range(columns):
        x = pad + 14 + c * step
        for i in range(per):
            ch = chars[c * per + i] if c * per + i < len(chars) else ""
            if ch:
                d.text((x, pad + 12 + i * step), ch, font=font,
                       fill=(10, 10, 10))
                dm.text((x, pad + 12 + i * step), ch, font=font,
                        fill=255)
    return block, ink_mask


def build_s009_page(repo_root: str, jp_size: int = 26, rng_seed: int = RNG_SEED):
    """Build the S009-class page.

    Returns (full_bgr, clean_bgr, regions, text_ink_mask):
      full_bgr      — the page as drawn (art + rings + JP text)
      clean_bgr     — same page, text inpainted away (rings stay)
      regions       — per-region dicts: tag, box (detector-style
                      axis-aligned dark-ink bbox), beta (ground-truth
                      text tilt; 0.0 for horizontal/vertical), class,
                      line_bands (per-line rotated quads, page coords),
                      jp, bengali
      text_ink_mask — uint8 page mask of the TRUE text ink (255=ink;
                      the archive text_mask and the ideal CTD surface)
    """
    import cv2
    rng = np.random.default_rng(rng_seed)
    _jp_font(repo_root, jp_size)          # ensure the local copy exists
    font_path = LOCAL_JP_COPY
    vfont = ImageFont.truetype(font_path, 22)

    # ONE canvas, two copies: full (with text) and clean (text inpainted
    # away) must differ ONLY in text ink — identical art + rings.
    bg = _page_canvas(PAGE_W, PAGE_H, rng)
    full = bg.copy()
    clean = bg.copy()
    pil_full = Image.fromarray(cv2.cvtColor(full, cv2.COLOR_BGR2RGB))
    pil_clean = Image.fromarray(cv2.cvtColor(clean, cv2.COLOR_BGR2RGB))
    pil_ink = Image.new("L", (PAGE_W, PAGE_H), 0)
    regions = []

    def paste_block(pil, block, cx, cy):
        pil.paste(block, (int(cx - block.width / 2),
                          int(cy - block.height / 2)))

    def ring_box_after_paste(pil, block, cx, cy):
        """Axis-aligned dark-ink bbox of the pasted area (detector-style)."""
        arr = np.asarray(pil.convert("L"))
        x0 = max(0, int(cx - block.width / 2) - 2)
        y0 = max(0, int(cy - block.height / 2) - 2)
        x1 = min(pil.width, int(cx + block.width / 2) + 2)
        y1 = min(pil.height, int(cy + block.height / 2) + 2)
        sub = arr[y0:y1, x0:x1]
        ys, xs = np.nonzero(sub < 128)
        return (int(xs.min()) + x0, int(ys.min()) + y0,
                int(xs.max() - xs.min()) + 1, int(ys.max() - ys.min()) + 1)

    def paste_ink(ink_mask, cx, cy, block_w, block_h):
        pil_ink.paste(ink_mask, (int(cx - block_w / 2),
                                 int(cy - block_h / 2)))

    for k, spec in enumerate(S009_TILTED):
        ring_tilt = float(rng.uniform(-RING_TILT_MAX, RING_TILT_MAX))
        lines = [JP_TILTED_LINES[k % len(JP_TILTED_LINES)]] * spec["lines"]
        blk, bands, ink = _tilted_bubble_block(
            spec["bw"], spec["bh"], ring_tilt, lines, spec["beta"],
            font_path, jp_size)
        paste_block(pil_full, blk, spec["cx"], spec["cy"])
        paste_ink(ink, spec["cx"], spec["cy"], blk.width, blk.height)
        # clean page: ring only (text inpainted away)
        blk_ring, _, _ = _tilted_bubble_block(
            spec["bw"], spec["bh"], ring_tilt, [], spec["beta"],
            font_path, jp_size)
        paste_block(pil_clean, blk_ring, spec["cx"], spec["cy"])
        box = ring_box_after_paste(pil_full, blk, spec["cx"], spec["cy"])
        off = np.array([spec["cx"] - blk.width / 2,
                        spec["cy"] - blk.height / 2])
        regions.append({
            "tag": spec["tag"], "box": box, "beta": spec["beta"],
            "class": "tilted", "line_bands": [b + off for b in bands],
            "jp": "\n".join(lines), "bengali": BENGALI_TILTED[k],
        })

    for k, spec in enumerate(S009_HORIZONTAL):
        lines = [JP_HORIZONTAL_LINES[k % len(JP_HORIZONTAL_LINES)]] * spec["lines"]
        blk, bands, ink = _tilted_bubble_block(spec["bw"], spec["bh"], 0.0,
                                               lines, 0.0, font_path,
                                               jp_size)
        paste_block(pil_full, blk, spec["cx"], spec["cy"])
        paste_ink(ink, spec["cx"], spec["cy"], blk.width, blk.height)
        blk_ring, _, _ = _tilted_bubble_block(spec["bw"], spec["bh"], 0.0, [],
                                              0.0, font_path, jp_size)
        paste_block(pil_clean, blk_ring, spec["cx"], spec["cy"])
        box = ring_box_after_paste(pil_full, blk, spec["cx"], spec["cy"])
        off = np.array([spec["cx"] - blk.width / 2,
                        spec["cy"] - blk.height / 2])
        regions.append({
            "tag": spec["tag"], "box": box, "beta": 0.0,
            "class": "horizontal", "line_bands": [b + off for b in bands],
            "jp": "\n".join(lines), "bengali": BENGALI_HORIZONTAL[k],
        })

    for spec in S009_VERTICAL:
        blk, vmask = _vertical_note_block(spec["bw"], spec["bh"],
                                          JP_VERTICAL_CHARS,
                                          spec["columns"], vfont, 22)
        paste_block(pil_full, blk, spec["cx"], spec["cy"])
        paste_block(pil_clean, blk, spec["cx"], spec["cy"])  # border stays
        paste_ink(vmask, spec["cx"], spec["cy"], blk.width, blk.height)
        box = ring_box_after_paste(pil_full, blk, spec["cx"], spec["cy"])
        regions.append({
            "tag": spec["tag"], "box": box, "beta": 0.0,
            "class": "vertical", "line_bands": [],
            "jp": JP_VERTICAL_CHARS, "bengali": BENGALI_VERTICAL,
        })

    full_bgr = cv2.cvtColor(np.asarray(pil_full), cv2.COLOR_RGB2BGR)
    clean_bgr = cv2.cvtColor(np.asarray(pil_clean), cv2.COLOR_RGB2BGR)
    text_ink_mask = np.asarray(pil_ink)
    return full_bgr, clean_bgr, regions, text_ink_mask


def ground_truth_angles(regions):
    """Per-region expected pil_angle (hand-tool = construction law:
    rotated strip measures pil == beta)."""
    return {r["tag"]: r["beta"] for r in regions}
