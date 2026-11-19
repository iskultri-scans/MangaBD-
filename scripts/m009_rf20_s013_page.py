#!/usr/bin/env python3
r"""MANGABD-009 RF-20 — S013_dark_webtoon page builder.

Synthesizes the Owner's live 07.jpg page class (dark webtoon,
29 regions) as a committed regression fixture, BOTH failure
mechanisms in one deterministic page:

  DUPLICATE-DETECTION class (the Bengali-on-Bengali root cause):
    the RT-DETR stub emits BOTH the whole bubble AND a line
    fragment of the same bubble — the owner dump pairs
    (4,5)(7,8)(16,17)(20,21) reproduced as W/F pairs here.
  DARK-SPIKY-GHOST class: spiky thought bubbles whose detect-stage
    mask hugs only the spiky border — the interior ink is never
    inpainted away (the ghost).

Regions (page 844x1200, dark webtoon: near-black panels, light
interiors on the spiky thought bubbles, white name plates):

  R1  whole_dark    big dark thought bubble, 4 light-ink lines +
                    spiky border (whole region; W of pair W/F)
  R2  frag_line     the line-fragment of R1's second line — the
                    duplicate detection (F of pair W/F; suppressed
                    by RF-20)
  R3  whole_spiky2  second spiky bubble, 3 lines (W of pair 2)
  R4  frag_line2    R3's third-line fragment (F of pair 2)
  R5  adj_left      adjacent bubble, LEFT of the R6/R7 pair
  R6  adj_mid       adjacent bubble (the 12/13/14-class cluster)
  R7  adj_right     adjacent bubble — none of R5/R6/R7 may
                    suppress (containment law guards)
  R8  plate_kim     name plate (narrator box) — dark plate,
                    light text
  R9  plate_lee     name plate — must render (15/16/18-class)
  R10 dark_ghost    dark bubble whose mask covers ONLY the spiky
                    border → interior ink stays → RF-20 ghost wipe
  R11 white_ctrl    white-bg control bubble (dark ink, full mask,
                    clean inpaint) — dedup + ghost both no-op

Construction is FULLY deterministic (rng_seed 20261117 pins
future art-noise additions; today every element is fixed).
"""
import cv2
import numpy as np

PAGE_W, PAGE_H = 844, 1200
RNG_SEED = 20261117

DARK_BG = (16, 16, 16)          # near-black webtoon background
PANEL_EDGE = (52, 52, 52)
LIGHT_INK = (232, 232, 232)     # light text ink on dark interiors
DARK_INK = (18, 18, 18)         # dark text ink on white plates
WHITE = (250, 250, 250)
SPIKE = (150, 150, 150)         # spiky thought-bubble border


def _spiky_bubble(page, clean, cx, cy, rw, rh, n_spikes=26):
    """Spiky thought bubble: ellipse body + radial spikes; drawn on
    BOTH the full page (text inside) and the clean page (text
    removed — the synthesized inpaint result)."""
    for img in (page, clean):
        cv2.ellipse(img, (cx, cy), (rw, rh), 0, 0, 360,
                    SPIKE, 2, lineType=cv2.LINE_AA)
        for k in range(n_spikes):
            ang = 2.0 * np.pi * k / n_spikes
            x0 = int(cx + (rw - 2) * np.cos(ang))
            y0 = int(cy + (rh - 2) * np.sin(ang))
            x1 = int(cx + (rw + 12) * np.cos(ang))
            y1 = int(cy + (rh + 12) * np.sin(ang))
            cv2.line(img, (x0, y0), (x1, y1), SPIKE, 2,
                     lineType=cv2.LINE_AA)


def _words_light(page, y, x0, words, h=22):
    """Draw a row of light-ink word boxes (the original JP text).
    words = [(w0, _unused), ...] — S012-builder tuple shape."""
    x = x0
    for w0, _u in words:
        cv2.rectangle(page, (x, y), (x + w0 - 1, y + h - 1),
                      (LIGHT_INK[2], LIGHT_INK[1], LIGHT_INK[0]), -1)
        x += w0 + 10
    return x


def _words_dark(page, y, x0, words, h=22):
    """Dark-ink words on white plates. Same tuple shape."""
    x = x0
    for w0, _u in words:
        cv2.rectangle(page, (x, y), (x + w0 - 1, y + h - 1),
                      (DARK_INK[2], DARK_INK[1], DARK_INK[0]), -1)
        x += w0 + 10
    return x


def build_s013_page():
    """Returns (full, clean, regions, ink_mask, mask_override).

    full: the raw page (original.jpg) — text present.
    clean: the synthesized inpaint result — for every region whose
      detect-stage mask COVERS the text, text is removed; for the
      ghost class (R10) the text STAYS (the mask missed it — that
      is the bug being pinned).
    regions: the fixture ledger (box + jp + bengali + expects).
    ink_mask: the TRUE text-ink mask (all text, both colors).
    mask_override: per-region detect-stage mask shapes — the
      spiky-border-only masks for the ghost class; None elsewhere
      (mask = the true ink, the normal archive law).
    """
    rng = np.random.default_rng(RNG_SEED)
    full = np.full((PAGE_H, PAGE_W, 3), DARK_BG, np.uint8)
    clean = np.full((PAGE_H, PAGE_W, 3), DARK_BG, np.uint8)
    raw = np.zeros((PAGE_H, PAGE_W), np.uint8)

    # dark-panel hatching (deterministic art noise)
    for i in range(60):
        x0 = int(rng.integers(30, PAGE_W - 60))
        y0 = int(rng.integers(30, PAGE_H - 60))
        for img in (full, clean):
            cv2.line(img, (x0, y0), (x0 + 18, y0 + 8),
                     (34, 34, 34), 1)
    cv2.rectangle(full, (16, 16), (PAGE_W - 17, PAGE_H - 17),
                  PANEL_EDGE, 2)
    cv2.rectangle(clean, (16, 16), (PAGE_W - 17, PAGE_H - 17),
                  PANEL_EDGE, 2)

    regions = []
    mask_override = {}

    # ── R1 whole_dark + R2 frag_line (duplicate pair 1) ──
    _spiky_bubble(full, clean, 230, 220, 190, 150)
    r1_lines = [(100, [(54, 46), (40, 44), (58, 48)]),
                (150, [(48, 44), (60, 50), (36, 40)]),
                (200, [(52, 48), (44, 42), (56, 46)]),
                (250, [(40, 44), (58, 48), (46, 42)])]
    for y, words in r1_lines:
        _words_light(full, y, 100, words)
        cv2.rectangle(clean, (98, y - 2), (330, y + 24),
                      DARK_BG, -1)          # inpainted away
        for w0, _ in words:
            pass
    for y, words in r1_lines:
        x = 100
        for w0, _ in words:
            cv2.rectangle(raw, (x, y), (x + w0 - 1, y + 21), 255, -1)
            x += w0 + 10
    regions.append({
        "tag": "R1", "class": "whole_dark",
        "box": (88, 62, 284, 208),
        "jp": "これは\n暗いウェブトゥーン\nのセリフ\nです",
        "bengali": "এই অন্ধকার ওয়েবটুনের কথা এখানে লেখা আছে",
        "expect_rendered": True,
    })
    # the duplicate detection: R1's second line as its own region
    regions.append({
        "tag": "R2", "class": "frag_line",
        "box": (98, 148, 232, 26),          # inside R1's box
        "jp": "暗いウェブトゥーン",
        "bengali": "অন্ধকার ওয়েবটুনের ডুপ্লিকেট লাইন",
        "expect_rendered": False,           # RF-20 suppresses it
        "expect_suppressed_by": 1,
    })

    # ── R3 whole_spiky2 + R4 frag_line2 (duplicate pair 2) ──
    _spiky_bubble(full, clean, 620, 240, 160, 120)
    r3_lines = [(190, [(44, 40), (56, 46)]),
                (230, [(50, 42), (48, 44)]),
                (270, [(42, 40), (52, 46), (38, 38)])]
    for y, words in r3_lines:
        _words_light(full, y, 500, words)
        cv2.rectangle(clean, (498, y - 2), (740, y + 24),
                      DARK_BG, -1)
    for y, words in r3_lines:
        x = 500
        for w0, _ in words:
            cv2.rectangle(raw, (x, y), (x + w0 - 1, y + 21), 255, -1)
            x += w0 + 10
    regions.append({
        "tag": "R3", "class": "whole_spiky2",
        "box": (448, 118, 344, 188),
        "jp": "二つ目の\n尖った吹き出し\n三行",
        "bengali": "দ্বিতীয় কাঁটাওয়ালা বুদবুদের কথা",
        "expect_rendered": True,
    })
    regions.append({
        "tag": "R4", "class": "frag_line2",
        "box": (496, 262, 222, 40),         # R3's third line (fatter:
        # IoU 0.131 > 0.1 — the owner (7,8)-class low-IoU pair)
        "jp": "三行",
        "bengali": "তৃতীয় লাইনের ডুপ্লিকেট",
        "expect_rendered": False,
        "expect_suppressed_by": 3,
    })

    # ── R5/R6/R7 adjacent cluster (12/13/14-class — NO dedup) ──
    for idx, (bx, by, tag) in enumerate(
            ((60, 480, "R5"), (300, 480, "R6"), (540, 480, "R7"))):
        cv2.ellipse(full, (bx + 120, by + 90), (110, 80), 0, 0,
                    360, SPIKE, 2, lineType=cv2.LINE_AA)
        cv2.ellipse(clean, (bx + 120, by + 90), (110, 80), 0, 0,
                    360, SPIKE, 2, lineType=cv2.LINE_AA)
        for y in (by + 40, by + 90):
            _words_light(full, y, bx + 30,
                         [(56, 48), (48, 44), (60, 50)])
            cv2.rectangle(clean, (bx + 28, y - 2),
                          (bx + 230, y + 24), DARK_BG, -1)
            x = bx + 30
            for w0, _ in [(56, 0), (48, 0), (60, 0)]:
                cv2.rectangle(raw, (x, y),
                              (x + w0 - 1, y + 21), 255, -1)
                x += w0 + 10
        regions.append({
            "tag": tag, "class": f"adj_{chr(97 + idx)}",
            "box": (bx + 8, by + 8, 224, 164),
            "jp": "隣同士の\n吹き出し",
            "bengali": "পাশাপাশি বুদবুদের কথা নম্বর "
                       + "এক দুই তিন".split()[idx],
            "expect_rendered": True,
        })

    # ── R8/R9 name plates (15/16/18-class — must render) ──
    for idx, (px, py, tag, name) in enumerate(
            ((90, 760, "R8", "キム"), (500, 760, "R9", "リ"))):
        cv2.rectangle(full, (px, py), (px + 180, py + 70),
                      WHITE, -1)
        cv2.rectangle(full, (px, py), (px + 180, py + 70),
                      (60, 60, 60), 3)
        cv2.rectangle(clean, (px, py), (px + 180, py + 70),
                      WHITE, -1)
        cv2.rectangle(clean, (px, py), (px + 180, py + 70),
                      (60, 60, 60), 3)
        _words_dark(full, py + 22, px + 40, [(100, 26)])
        cv2.rectangle(raw, (px + 40, py + 22),
                      (px + 139, py + 47), 255, -1)
        regions.append({
            "tag": tag, "class": "name_plate",
            "box": (px - 4, py - 4, 188, 78),
            "jp": name,
            "bengali": "নামফলক " + name,
            "expect_rendered": True,
            "region_type": "narrator",
        })

    # ── R10 dark_ghost (spiky-border-only mask — the ghost pin) ──
    _spiky_bubble(full, clean, 240, 1030, 170, 120)
    r10_lines = [(980, [(50, 44), (58, 48)]),
                 (1020, [(46, 42), (62, 50)]),
                 (1060, [(52, 46), (48, 44)])]
    for y, words in r10_lines:
        _words_light(full, y, 120, words)
        # clean: text STAYS — the synthesized inpaint MISSED it
        _words_light(clean, y, 120, words)
        x = 120
        for w0, _ in words:
            cv2.rectangle(raw, (x, y), (x + w0 - 1, y + 21), 255, -1)
            x += w0 + 10
    regions.append({
        "tag": "R10", "class": "dark_ghost",
        "box": (58, 908, 364, 244),
        "jp": "消えていない\n幽霊の文字\n三行",
        "bengali": "না মোছা ভূতুড়ে লেখা এখানে",
        "expect_rendered": True,
        "expect_ghost_wipe": True,
    })
    # the detect-stage mask for R10: spiky border ONLY (the bug)
    _m10 = np.zeros((PAGE_H, PAGE_W), np.uint8)
    for k in range(26):
        ang = 2.0 * np.pi * k / 26
        x0 = int(240 + 165 * np.cos(ang))
        y0 = int(1030 + 115 * np.sin(ang))
        x1 = int(240 + 185 * np.cos(ang))
        y1 = int(1030 + 135 * np.sin(ang))
        cv2.line(_m10, (x0, y0), (x1, y1), 255, 4)
    mask_override["R10"] = _m10

    # ── R11 white_ctrl (both fixes no-op) ──
    cv2.rectangle(full, (600, 950), (800, 1120), WHITE, -1)
    cv2.rectangle(clean, (600, 950), (800, 1120), WHITE, -1)
    for y in (990, 1030, 1070):
        _words_dark(full, y, 630, [(60, 50), (52, 46)])
        # clean: removed (full mask covered it)
        x = 630
        for w0, _ in [(60, 0), (52, 0)]:
            cv2.rectangle(raw, (x, y), (x + w0 - 1, y + 21),
                          255, -1)
            x += w0 + 10
    regions.append({
        "tag": "R11", "class": "white_ctrl",
        "box": (596, 946, 208, 178),
        "jp": "白い背景の\n対照実験\nです",
        "bengali": "সাদা পটভূমির কন্ট্রোল বুদবুদ",
        "expect_rendered": True,
    })

    return full, clean, regions, raw, mask_override


def region_boxes_payload(regions):
    """The RT-DETR stub payload — includes the DUPLICATE fragment
    boxes (the owner's live detector behavior on 07.jpg)."""
    out = []
    for r in regions:
        out.append({
            "x": r["box"][0], "y": r["box"][1],
            "w": r["box"][2], "h": r["box"][3],
            "score": (0.82 if r["class"].startswith("frag_")
                      else 0.9),
            "detector_class": (
                "text_free" if r.get("region_type") == "narrator"
                else "text_bubble"),
        })
    return out
