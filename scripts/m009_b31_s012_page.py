#!/usr/bin/env python3
r"""MANGABD-009 B3.1 — S012_manhwa_emphasis page builder.

Synthesizes the OWNER-REJECT page class (per-word emphasis coloring —
the corpus style that made B3's region-level median inert) as a
committed regression fixture:

  R1 emphasis4   the owner case: 4-line bubble, black base + ONE red
                 emphasis word (line 1) + ONE blue emphasis word
                 (line 3) → GT line_colors [None, red, None, blue]
  R2 shout       full-line red text (2 lines) → [red, red] (+ the B3
                 region ink_color fires — whole population red)
  R3 sfx_twohue  ONE line, red left half + blue right half → line
                 gate_bimodal → NO key + WARN (line-level RB3-5)
  R4 black_ctrl  4-line all-black control → NO keys (byte-stability)
  R5 purple2     2 lines, line 0 carries one purple emphasis word →
                 [purple, None]
  R6 narrow_tilt 3 thin lines at 12 deg in a w<80 box (gap 14px —
                 raw-locator split regime) → b2gt lines=3 from the
                 NARROW FIX path (close(5,5)x2 would merge); black ink
  R7 tiny_id8    the Owner id=8 class: 51x62 box (area 3162px), 4
                 short lines → the tiny-text assertion pin @ 2000px
  R8 vertical    V-3 shape vertical note, gray-158 ink → no key, black
                 render (RB31-5)

Construction is FULLY deterministic (declared rng_seed 20261109 pins
future art-noise additions; today every element is fixed placement).
"""
import cv2
import numpy as np

PAGE_W, PAGE_H = 844, 1200
RNG_SEED = 20261109

INK_BLACK = (12, 12, 12)
COL_RED = (200, 30, 30)
COL_BLUE = (30, 30, 180)
COL_PURPLE = (96, 20, 170)
GRAY_NOTE = (158, 158, 158)
PAPER = (248, 248, 248)


def _words(page, raw, y, x0, words, h=34):
    """Draw a row of word boxes; words = [(text_w, rgb), ...]."""
    x = x0
    for w0, rgb in words:
        cv2.rectangle(page, (x, y), (x + w0 - 1, y + h - 1),
                      (rgb[2], rgb[1], rgb[0]), -1)
        cv2.rectangle(raw, (x, y), (x + w0 - 1, y + h - 1), 255, -1)
        x += w0 + 10
    return x


def build_s012_page():
    """Returns (full, clean, regions, ink_mask)."""
    rng = np.random.default_rng(RNG_SEED)
    full = np.full((PAGE_H, PAGE_W, 3), PAPER, np.uint8)
    clean = full.copy()
    raw = np.zeros((PAGE_H, PAGE_W), np.uint8)

    # deterministic light art: panel + hatch strokes (both pages)
    cv2.rectangle(full, (20, 20), (PAGE_W - 21, PAGE_H - 21),
                  (210, 205, 200), 2)
    cv2.rectangle(clean, (20, 20), (PAGE_W - 21, PAGE_H - 21),
                  (210, 205, 200), 2)
    for i in range(40):
        x0 = int(rng.integers(30, PAGE_W - 60))
        y0 = int(rng.integers(30, PAGE_H - 60))
        cv2.line(full, (x0, y0), (x0 + 24, y0 + 10), (188, 182, 176), 1)
        cv2.line(clean, (x0, y0), (x0 + 24, y0 + 10),
                 (188, 182, 176), 1)

    def bubble(cx, cy, rw, rh, sfx=False):
        if sfx:
            cv2.rectangle(full, (cx - rw, cy - rh), (cx + rw, cy + rh),
                          (60, 60, 60), 3, lineType=cv2.LINE_AA)
            cv2.rectangle(clean, (cx - rw, cy - rh),
                          (cx + rw, cy + rh), (60, 60, 60), 3,
                          lineType=cv2.LINE_AA)
        else:
            cv2.ellipse(full, (cx, cy), (rw, rh), 0, 0, 360,
                        (60, 60, 60), 3, lineType=cv2.LINE_AA)
            cv2.ellipse(clean, (cx, cy), (rw, rh), 0, 0, 360,
                        (60, 60, 60), 3, lineType=cv2.LINE_AA)

    regions = []

    # ── R1 emphasis4 (the owner case) — left col, 4 lines ──
    bubble(230, 230, 200, 190)
    r1_lines = [
        (90, [(52, INK_BLACK), (44, INK_BLACK), (58, INK_BLACK)]),
        (170, [(44, INK_BLACK), (72, COL_RED), (50, INK_BLACK),
               (40, INK_BLACK)]),
        (250, [(58, INK_BLACK), (40, INK_BLACK), (62, INK_BLACK)]),
        (330, [(40, INK_BLACK), (48, INK_BLACK), (72, COL_BLUE),
               (36, INK_BLACK)]),
    ]
    for y, words in r1_lines:
        _words(full, raw, y, 90, words)
    regions.append({
        "tag": "R1", "class": "emphasis4",
        "box": (88, 88, 292, 278),
        "jp": "それは\nまさか\n冗談で\n言ってるのか",
        "bengali": ("এটা কি সত্যিই সত্যি হচ্ছে নাকি আমার সাথে "
                    "সুস্পষ্ট রসিকতা করছ বলো তো আমি বুঝতে চাই"),
        "gt_line_colors": [None, list(COL_RED), None, list(COL_BLUE)],
        "expect_line_colors": True,
        "expect_ink_color": None,
    })

    # ── R2 shout — right col, 2 full-red lines ──
    bubble(634, 118, 150, 80)
    _words(full, raw, 80, 520, [(60, COL_RED), (72, COL_RED),
                                (56, COL_RED)])
    _words(full, raw, 140, 530, [(52, COL_RED), (78, COL_RED)])
    regions.append({
        "tag": "R2", "class": "shout",
        "box": (518, 78, 204, 98),
        "jp": "うそだ\nと言ってくれ",
        "bengali": "মিথ্যা বলো এটা সব মিথ্যা",
        "gt_line_colors": [list(COL_RED), list(COL_RED)],
        "expect_line_colors": True,
        "expect_ink_color": list(COL_RED),
    })

    # ── R3 two-hue SFX — right col, ONE line red|blue ──
    bubble(634, 270, 130, 42, sfx=True)
    _words(full, raw, 254, 530, [(48, COL_RED), (44, COL_RED),
                                 (46, COL_BLUE), (42, COL_BLUE)])
    regions.append({
        "tag": "R3", "class": "sfx_twohue",
        "box": (528, 252, 216, 42),
        "jp": "ドカーーン",
        "bengali": "বুম ব্যাং কাবুম",
        "gt_line_colors": None,
        "expect_line_colors": False,
        "expect_ink_color": None,
        "expect_gate_warn": True,
    })

    # ── R4 black control — right col, 4 black lines ──
    bubble(634, 530, 150, 190)
    for y in (400, 470, 540, 610):
        _words(full, raw, y, 530, [(56, INK_BLACK), (44, INK_BLACK),
                                   (66, INK_BLACK)])
    regions.append({
        "tag": "R4", "class": "black_ctrl",
        "box": (528, 398, 204, 248),
        "jp": "黒い\n四行の\nテキスト\nです",
        "bengali": "এই চারটি লাইন সাধারণ কালো",
        "gt_line_colors": None,
        "expect_line_colors": False,
        "expect_ink_color": None,
    })

    # ── R5 purple emphasis — right col, 2 lines ──
    bubble(634, 820, 140, 90)
    _words(full, raw, 770, 540, [(62, COL_PURPLE), (54, INK_BLACK),
                                 (48, INK_BLACK)])
    _words(full, raw, 830, 540, [(50, INK_BLACK), (66, INK_BLACK)])
    regions.append({
        "tag": "R5", "class": "purple2",
        "box": (538, 768, 190, 98),
        "jp": "大事な\n言葉だよ",
        "bengali": "এই কথাটা খুব জরুরি কথা",
        "gt_line_colors": [list(COL_PURPLE), None],
        "expect_line_colors": True,
        "expect_ink_color": None,
    })

    # ── R6 narrow-tilted — left col, 3 thin lines @ 12deg (w<80) ──
    t = np.radians(12.0)
    u = np.array([np.cos(t), np.sin(t)])
    v = np.array([-np.sin(t), np.cos(t)])
    bc = np.array([200.0, 500.0])
    pts_all = []
    for bi in (-1, 0, 1):
        c = bc + bi * 17.0 * v          # pitch 17 = th 3 + gap 14
        cs = [c - 28 * u - 1.5 * v, c + 28 * u - 1.5 * v,
              c + 28 * u + 1.5 * v, c - 28 * u + 1.5 * v]
        pts_all.extend(cs)
        cv2.fillPoly(full, [np.round(cs).astype(np.int32)],
                     (INK_BLACK[2], INK_BLACK[1], INK_BLACK[0]))
        cv2.fillPoly(raw, [np.round(cs).astype(np.int32)], 255)
    arr = np.array(pts_all)
    r6_box = (int(arr[:, 0].min()), int(arr[:, 1].min()),
              int(np.ceil(arr[:, 0].max())) - int(arr[:, 0].min()),
              int(np.ceil(arr[:, 1].max())) - int(arr[:, 1].min()))
    regions.append({
        "tag": "R6", "class": "narrow_tilt",
        "box": r6_box,
        "jp": "せまい\nふきだし\n三行",
        "bengali": "সরু বুদবুদ তিন লাইন",
        "gt_line_colors": None,
        "expect_line_colors": False,
        "expect_ink_color": None,
        "expect_gt_lines": 3,           # the NARROW FIX pin (raw locator)
        "expect_tilted": True,
    })

    # ── R7 tiny id=8 class — left col, 52x60 box, 4 short lines ──
    for i, y in enumerate((660, 675, 690, 705)):
        _words(full, raw, y, 150, [(50, INK_BLACK)], h=8)
    regions.append({
        "tag": "R7", "class": "tiny_id8",
        "box": (148, 658, 52, 60),
        "jp": "ちいさい\nまほうの\nことばが\nならんでる",
        "bengali": "ছোট্ট জাদুর কথা এখানে",
        "gt_line_colors": None,
        "expect_line_colors": False,
        "expect_ink_color": None,
        "expect_gt_lines": None,        # axis-aligned: no b2gt by law
        "tiny_text_pin": True,          # area 3120 >= 2000, 4 lines
    })

    # ── R8 vertical note — left col, V-3 shape, gray ink ──
    for i in range(9):
        y = 790 + i * 36
        cv2.rectangle(full, (180, y), (216, y + 24),
                      (GRAY_NOTE[2], GRAY_NOTE[1], GRAY_NOTE[0]), -1)
        cv2.rectangle(raw, (180, y), (216, y + 24), 255, -1)
    regions.append({
        "tag": "R8", "class": "vertical",
        "box": (178, 788, 44, 336),
        "jp": "たてがきの\nテストです",
        "bengali": "নোট এখানে লম্বা লম্বা",
        "gt_line_colors": None,
        "expect_line_colors": False,
        "expect_ink_color": None,
        "expect_vertical": True,
    })

    ink_mask = raw
    return full, clean, regions, ink_mask


def region_boxes_payload(regions):
    return [{"x": r["box"][0], "y": r["box"][1],
             "w": r["box"][2], "h": r["box"][3],
             "score": 0.9,
             "detector_class": ("text_free" if r.get("expect_vertical")
                                else "text_bubble")}
            for r in regions]
