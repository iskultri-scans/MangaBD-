#!/usr/bin/env python3
"""
MANGABD-009 B3 Phase A — ink-color inheritance measurement instrument.

Docs-only batch (NO source changes). Standalone; reads committed page
archives, writes JSON results. Measures feasibility/accuracy of the
proposed "sample original ink color per region, inherit at render"
design, plus synthetic known-color probes for the colored arm (the
committed corpus has NO colored text ink — proven by this instrument —
so the colored classifier can only be validated synthetically).

What it measures
  C1  Archive census — per-region ink sampling on the directive's five
      pages (S003/S007/S009/S010/S011) + supplementary repo archives
      (S001/S002/S005_manual/S005_openrouter). Disclosure baked into
      results: S001/S002/S005_manual/S005_openrouter/S007 are
      byte-identical re-archives of the S003 source page (original.jpg
      md5 ledger recorded per page).
  C2  Saved-mask character census — the archives carry two mask
      generations with OPPOSITE semantics, measured not assumed:
        * S003-family (B1-era): text_mask.png = INPAINT-AREA mask
          (82-100% of region bbox covered; sampling it returns the
          bubble paper, not ink — measured: median@mask 249-253 where
          true ink is 2-15);
        * S009/S010/S011 (RF-16/17/18 fixtures): text_mask.png =
          STROKE-precise mask (100% of mask px on dark ink,
          median@mask = 10) — but morphology close(5,5)x2 bridges the
          thin fixture strokes and triples the area with background
          (14,514 -> 42,376 px on S009), flipping the median to white.
      Design consequence recorded for the ruling: runtime ink-color
      sampling must use the UNDILATED CTD prob-map path (cell-6
      _b2_page_ink_mask first branch, L1198-1202); the artifact
      de-dilate fallback (L1207-1214) and close-with-large-SE are
      unusable for color (angle tolerated merged blobs; a median
      does not).
  C3  Synthetic classifier validation — known-ink probes (solid hues,
      white/black/gray, gradient, two-color split, low-contrast
      same-hue background, JPEG noise) drawn as anti-aliased bars
      (font-independent: reproducible without font assets), sampled
      through the runtime-undilated mask law (cleaned TRUE mask, no
      dilate/erode). PASS requires correct class AND correct
      fire/no-fire AND (for solid colors) median within L2 tolerance.
  C4  Manual-inspection accuracy — deterministic 10-region selection,
      contact sheet (crop + sampled swatch) written to --workdir;
      MANUAL_TRUTH records the eyeball verdicts; a maskless Otsu
      cross-check (numeric, reproducible) runs alongside as
      OTSU_CROSS so agreement is two-way (algorithm vs eyeball vs
      independent numeric).
  C5  Corpus verdict — would-key-fire distribution; feeds the B3 risk
      table (how inert the feature is on the current corpus).

Archive locator law (measurement-only; runtime uses ctd_raw_mask):
  The instrument cannot run CTD, so per region it picks an ink locator:
    (a) saved-mask trust test — mask-vs-ring contrast (mirrors the
        sampler's own ring logic): a stroke-precise mask sits on
        pixels that differ from its dilation ring by >= ring_delta_min;
        an area mask (inpaint coverage) matches its ring or fills the
        window entirely -> not trusted;
    (b) otherwise -> deviance locator: pixels with
        L2(color, window-bg-median) >= locator_deviance.
  Locator choice is recorded per region. Known miss: very light
  ink on white paper (small value AND chroma deviance) — the runtime
  CTD mask does not have this miss; disclosed as archive-side
  pessimism.

Runtime laws mirrored (cell citations at main HEAD 2a86000,
notebook sha256 8926a2b3...7615):
  - region window = axis-aligned bbox padded 2px, clipped
    (cell-6 _b2_mask_orientation L1234-1235)
  - ink px cap 60000 with rng(42) subsample (cell-6 L1242-1245)
  - min ink px 30 (cell-10 choose_text_color mask law L1071)
  - ring background = dilate(ink,5) - ink, median (the kill_residual
    ring technique, cell-11 L109-111)
  - clean_binary_mask min_area 3 (cell-6 L1196)

Proposed runtime thresholds UNDER TEST (B3 design, not yet ruled):
  chroma >= 45 -> colored; V >= 215 & chroma < 45 -> white;
  V < 90 & chroma < 45 -> black; else gray. Colored-key gates:
  MAD per channel < 40, ring ΔL2 >= 40, hue not bimodal
  (largest-internal-gap split, both arcs >= 25%, circular mean
  separation >= 40°). Chroma sensitivity arms 35/60 recorded.

Usage:
  python scripts/m009_b3_color_measure.py \
      [--samples-root <repo>/samples] [--extra-root DIR] \
      [--workdir DIR] [--out results.json]
"""

import argparse
import hashlib
import json
import os
import sys

import cv2
import numpy as np

try:                                    # C3 probes only; census works
    from PIL import Image as PILImage, ImageDraw   # without PIL
    HAS_PIL = True
except Exception:                       # pragma: no cover
    HAS_PIL = False

# ── knobs under test ──────────────────────────────────────────
CHROMA_COLORED = 45          # max(R,G,B) - min(R,G,B) of the median
V_WHITE = 215                # brightness ceiling for "white ink"
V_BLACK = 90                 # brightness floor for "black ink"
MIN_INK_PX = 30              # cell-10 choose_text_color law
MAD_MAX = 40                 # per-channel median absolute deviation
RING_DELTA_MIN = 40          # L2 ink-vs-background separation
RING_DILATE = 5              # ring radius (kill_residual law)
BIMODAL_MIN_FRAC = 0.25      # both hue arcs must hold this share
BIMODAL_HUE_SEP_DEG = 40.0   # circular hue separation
CHROMA_SENS = (35, 60)       # sensitivity arms

# archive locator law
LOCATOR_DEVIANCE = 80        # L2(px, window-bg-median) ink threshold
RING_DILATE_LOCATOR = 5      # mask-vs-ring trust test radius
OTSU_CROSS_DELTA = 60        # gray-deviance for the numeric cross-check

# pages: logical name -> (subdirectory, source root)
# "repo" -> --samples-root; "extra" -> --extra-root
DIRECTIVE_PAGES = [
    ("S003", "S003_batch2", "repo"),
    ("S007", "S007", "extra"),
    ("S009", "S009_diagonal", "repo"),
    ("S010", "S010_burst", "repo"),
    ("S011", "S011_manhwa_ui", "repo"),
]
SUPPLEMENTARY_PAGES = [
    ("S001", "S001_color_webtoon", "repo"),
    ("S002", "S002_batch1", "repo"),
    ("S005m", "S005_manual", "repo"),
    ("S005o", "S005_openrouter", "repo"),
]

# C4: deterministic manual-inspection selection (page, region id).
# Spans: area-mask page (deviance locator), stroke-precise fixtures,
# tilted, the dark-bg-black-ink + white-art trap (S010 r5), and the
# genuine white-ink region (S011 r6).
MANUAL_SELECTION = [
    ("S003", 1), ("S003", 2), ("S003", 5),
    ("S001", 4),
    ("S009", 1),
    ("S010", 1), ("S010", 5),
    ("S011", 2), ("S011", 6), ("S011", 8),
]

# C4: eyeball verdicts (GLM-5.3, Phase A session, against the contact
# sheet regenerated deterministically at <workdir>/contact_sheet.png;
# cross-validated by the independent Otsu numeric check + VLM visual
# passes recorded below — see the Phase A report).
# class ∈ {black, white, gray, colored, mixed/gradient, no-visible-ink}
MANUAL_TRUTH = {
    ("S003", 1): "black",
    ("S003", 2): "black",
    ("S003", 5): "black",
    ("S001", 4): "black",
    ("S009", 1): "black",
    ("S010", 1): "black",
    ("S010", 5): "black",
    ("S011", 2): "black",
    ("S011", 6): "white",
    ("S011", 8): "gray",   # fixture vertical-note ink is gray 158
                          # (verified against the stroke-precise mask:
                          # med BGR 158 == sampler median 158)
}

# C4 record: VLM visual passes (GLM-5.3-flash via z-ai vision CLI,
# Phase A session). Recorded data, reproducible by regenerating the
# sheets with this script and re-asking; the verdicts below are the
# session's capture.
VLM_PASSES = {
    "full_sheet_130px": {
        "model": "glm-5.3-flash",
        "verdicts": {
            "S003 r1": "white", "S003 r2": "black",
            "S003 r5": "black", "S001 r4": "black",
            "S009 r1": "gray", "S010 r1": "black",
            "S010 r5": "black", "S011 r2": "black",
            "S011 r6": "white", "S011 r8": "white",
        },
        "agreement_with_sampler": "7/10",
    },
    "focus_2x_recheck": {
        "model": "glm-5.3-flash",
        "verdicts": {
            "S003 r1": "black", "S009 r1": "black",
            "S011 r8": "white",
        },
        "agreement_with_sampler": "2/3",
    },
    "adjudication": (
        "Full-sheet misreads at 130px tile height (S003 r1 tall "
        "narrow strip, S009 r1 thin tilted strokes) resolve to the "
        "sampler verdicts at 2x. S011 r8 remains perceptually "
        "ambiguous (gray 158 reads as white at a glance) but has "
        "exact numeric ground truth: the fixture's stroke-precise "
        "mask median is BGR 158 == sampler median 158, min 7 / max "
        "255 — gray ink by construction. Sampler holds 10/10 against "
        "numeric truth; VLM agrees 9/10 after the 2x re-check, the "
        "residual being the gray/white perceptual boundary."
    ),
}


# ── shared helpers ────────────────────────────────────────────

def md5_file(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def clean_binary_mask(mask, min_area=3):
    """cell-6 clean_binary_mask law (L1196): drop tiny components."""
    n, labels, stats, _ = cv2.connectedComponentsWithStats(
        (mask > 0).astype(np.uint8), 8)
    out = np.zeros_like(mask)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            out[labels == i] = 255
    return out


def window_box(shape, x, y, w, h, pad=2):
    """cell-6 _b2_mask_orientation window law (L1234-1235)."""
    H, W = shape[:2]
    x1, y1 = max(0, x - pad), max(0, y - pad)
    x2, y2 = min(W, x + w + pad), min(H, y + h + pad)
    return x1, y1, x2, y2


def deviance_mask(window_bgr, delta=LOCATOR_DEVIANCE):
    """Ink candidates = px far (L2, RGB) from the window bg median."""
    bg = np.median(window_bgr.reshape(-1, 3), axis=0)
    d = np.linalg.norm(
        window_bgr.astype(np.float32) - bg.astype(np.float32),
        axis=2)
    return d >= delta, bg


def archive_locator(saved_mask_win, window_bgr):
    """Pick the per-region ink locator (measurement-only law).

    Trust test = mask-vs-ring contrast (mirrors the sampler's own ring
    logic, self-contained — no deviance dependency): a stroke-precise
    mask sits on pixels that DIFFER from its dilation ring (the local
    background); an area mask (inpaint coverage) sits on pixels that
    MATCH the surroundings, and a window-filling mask has no ring at
    all. Deviance locator is the fallback for area-type masks.

    Returns (bool_mask, source, diagnostics).
    """
    diag = {}
    saved = saved_mask_win > 0
    n_saved = int(saved.sum())
    diag["saved_px"] = n_saved
    if n_saved >= MIN_INK_PX:
        dil = cv2.dilate(
            saved.astype(np.uint8) * 255,
            cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (2 * RING_DILATE + 1, 2 * RING_DILATE + 1)))
        ring = (dil > 0) & (~saved)
        if int(ring.sum()) >= 10:
            m_med = np.median(
                window_bgr[saved].astype(np.int16), axis=0)
            r_med = np.median(
                window_bgr[ring].astype(np.int16), axis=0)
            delta = int(round(float(np.linalg.norm(
                m_med.astype(float) - r_med.astype(float)))))
            diag["mask_ring_delta_l2"] = delta
            if delta >= RING_DELTA_MIN:
                return saved, "saved-mask (stroke-precise)", diag
        else:
            diag["mask_ring_delta_l2"] = None   # mask fills window
    dev, bg = deviance_mask(window_bgr)
    diag["bg_med_rgb"] = [int(bg[2]), int(bg[1]), int(bg[0])]
    diag["deviant_px"] = int(dev.sum())
    return dev, "deviance-locator (saved mask area-type/starved)", diag


def sample_window(window_bgr, win_locator):
    """Core sampler on a window image + window locator (bool, same
    shape). Returns the measurement dict or the no-ink short-circuit."""
    win_mask = win_locator > 0                     # normalize to bool
    n_px = int(win_mask.sum())
    if n_px < MIN_INK_PX:
        return {"ink_px": n_px, "class": "no-ink", "key_fires": False}

    ys, xs = np.nonzero(win_mask)
    if n_px > 60000:                                      # cap law
        sel = np.random.default_rng(42).choice(n_px, 60000,
                                               replace=False)
        ys, xs = ys[sel], xs[sel]
    px = window_bgr[ys, xs].astype(np.int16)              # BGR

    med_bgr = np.median(px, axis=0)
    med_rgb = [int(med_bgr[2]), int(med_bgr[1]), int(med_bgr[0])]
    mad_bgr = np.median(np.abs(px - med_bgr), axis=0)
    mad_rgb = [int(mad_bgr[2]), int(mad_bgr[1]), int(mad_bgr[0])]

    chroma = int(max(med_rgb) - min(med_rgb))
    V = int(max(med_rgb))

    def classify(ch_thr):
        if chroma >= ch_thr:
            return "colored"
        if V >= V_WHITE:
            return "white"
        if V <= V_BLACK:
            return "black"
        return "gray"

    cls = classify(CHROMA_COLORED)
    cls_sens = {f"chroma{c}": classify(c) for c in CHROMA_SENS}

    # ring background (kill_residual technique)
    ring_px = None
    ring_rgb = None
    ring_delta = None
    try:
        dil = cv2.dilate(
            win_mask.astype(np.uint8) * 255,
            cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE,
                (2 * RING_DILATE + 1, 2 * RING_DILATE + 1)))
        ring = (dil > 0) & (~win_mask)
        if int(ring.sum()) >= 10:
            rpx = window_bgr[ring].astype(np.int16)
            rmed = np.median(rpx, axis=0)
            ring_rgb = [int(rmed[2]), int(rmed[1]), int(rmed[0])]
            ring_delta = int(round(float(np.linalg.norm(
                np.array(med_rgb, float) - np.array(ring_rgb, float)))))
            ring_px = int(ring.sum())
    except Exception:
        pass

    # hue bimodality (chromatic px only): split the sorted circular hue
    # sequence at the largest INTERNAL gap (the wrap gap is not a split
    # candidate); separation = circular distance between arc means —
    # not the gap size itself (350°/10° are 20° apart, not 340°).
    bimodal = False
    hue_detail = None
    try:
        chr_sel = (px.max(axis=1) - px.min(axis=1)) >= 25
        if int(chr_sel.sum()) >= 60:
            hsv = cv2.cvtColor(
                px[chr_sel].reshape(-1, 1, 3).astype(np.uint8),
                cv2.COLOR_BGR2HSV)[:, 0, 0].astype(np.float64)
            hues = hsv * 2.0  # OpenCV 0-179 -> degrees
            hs = hues[np.argsort(hues)]
            n_h = len(hs)
            if n_h >= 4:
                k = int(np.argmax(np.diff(hs)))
                arc_a, arc_b = hs[:k + 1], hs[k + 1:]

                def _cmean(a):
                    return float(np.rad2deg(
                        np.mean(np.deg2rad(a)))) % 360.0

                ma, mb = _cmean(arc_a), _cmean(arc_b)
                sep = abs(ma - mb) % 360.0
                sep = min(sep, 360.0 - sep)
                if (len(arc_a) / n_h >= BIMODAL_MIN_FRAC
                        and len(arc_b) / n_h >= BIMODAL_MIN_FRAC
                        and sep >= BIMODAL_HUE_SEP_DEG):
                    bimodal = True
                hue_detail = {
                    "sep_deg": round(sep, 1),
                    "arc_share_a": round(len(arc_a) / n_h, 3),
                    "arc_share_b": round(len(arc_b) / n_h, 3),
                    "chromatic_px": int(n_h),
                }
    except Exception:
        pass

    mad_ok = all(m < MAD_MAX for m in mad_rgb)
    ring_ok = (ring_delta is None) or (ring_delta >= RING_DELTA_MIN)
    key_fires = (cls == "colored" and mad_ok and ring_ok and not bimodal)

    return {
        "ink_px": n_px,
        "med_rgb": med_rgb,
        "chroma": chroma,
        "V": V,
        "class": cls,
        "class_sensitivity": cls_sens,
        "mad_rgb": mad_rgb,
        "ring_bg_rgb": ring_rgb,
        "ring_px": ring_px,
        "ring_delta_l2": ring_delta,
        "hue_bimodal": bimodal,
        "hue_detail": hue_detail,
        "gates": {
            "mad_ok": mad_ok,
            "ring_ok": ring_ok,
            "not_bimodal": not bimodal,
        },
        "key_fires": bool(key_fires),
    }


def sample_region(image_bgr, ink_mask, x, y, w, h):
    """Page-shaped wrapper: window the page image + page-shaped ink
    mask (bool or uint8), then run the core sampler."""
    x1, y1, x2, y2 = window_box(ink_mask.shape, x, y, w, h)
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None
    return sample_window(image_bgr[y1:y2, x1:x2],
                         ink_mask[y1:y2, x1:x2])


# ── C1/C2: archive census + saved-mask character ──────────────

def resolve_page(sub, root_kind, samples_root, extra_root):
    base = samples_root if root_kind == "repo" else extra_root
    path = os.path.join(base, sub)
    return path if os.path.isdir(path) else None


def census(samples_root, extra_root):
    pages = []
    seen_md5 = {}
    for name, sub, kind in DIRECTIVE_PAGES + SUPPLEMENTARY_PAGES:
        entry = {"name": name, "dir": sub, "source": kind}
        path = resolve_page(sub, kind, samples_root, extra_root)
        if path is None:
            entry["status"] = (
                "missing-dir (S007 extra-root absent; byte-identical "
                "to S003 — see md5 ledger)")
            pages.append(entry)
            continue
        img = cv2.imread(os.path.join(path, "original.jpg"))
        saved_mask = cv2.imread(os.path.join(path, "text_mask.png"), 0)
        with open(os.path.join(path, "detections.json")) as f:
            dets = json.load(f)
        md5 = md5_file(os.path.join(path, "original.jpg"))
        entry.update({
            "status": "ok",
            "original_md5": md5,
            "duplicate_of": seen_md5.get(md5),
            "regions": len(dets),
            "image_wh": [img.shape[1], img.shape[0]],
        })
        seen_md5.setdefault(md5, name)

        # C2: saved-mask character (page level)
        cover_total = 0
        bbox_total = 0
        saved_med_gray = []
        for d in dets:
            x1, y1, x2, y2 = window_box(
                img.shape, int(d["x"]), int(d["y"]),
                int(d["width"]), int(d["height"]))
            bbox_total += (x2 - x1) * (y2 - y1)
            cover_total += int((saved_mask[y1:y2, x1:x2] > 0).sum())
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            sel = saved_mask[y1:y2, x1:x2] > 0
            if int(sel.sum()) > 30:
                saved_med_gray.append(float(np.median(gray[y1:y2,
                                                          x1:x2][sel])))
        entry["saved_mask_character"] = {
            "coverage_of_region_bboxes": round(
                cover_total / max(1, bbox_total), 3),
            "median_gray_at_saved_mask": (
                round(float(np.median(saved_med_gray)), 1)
                if saved_med_gray else None),
            "verdict": (
                "area-mask (inpaint coverage; unusable as ink locator)"
                if cover_total / max(1, bbox_total) > 0.5
                else "stroke-precise (usable as ink locator)"),
        }

        rows = []
        for d in dets:
            rid = int(d.get("id", 0))
            x, y = int(d["x"]), int(d["y"])
            w, h = int(d["width"]), int(d["height"])
            x1, y1, x2, y2 = window_box(img.shape, x, y, w, h)
            window = img[y1:y2, x1:x2]
            locator, loc_src, loc_diag = archive_locator(
                saved_mask[y1:y2, x1:x2], window)
            s = sample_window(window, locator)
            rec = {
                "id": rid,
                "region_type": d.get("region_type"),
                "xywh": [x, y, w, h],
                "angle": d.get("angle", 0.0),
                "locator_source": loc_src,
                "locator_diag": loc_diag,
            }
            if s is not None:
                rec.update(s)
            else:
                rec.update({"class": "empty-window",
                            "key_fires": False})
            rows.append(rec)
        entry["region_rows"] = rows

        eff = [r for r in rows if "class" in r]
        entry["summary"] = {
            "classes": {
                c: sum(1 for r in eff if r.get("class") == c)
                for c in ("colored", "white", "black", "gray",
                          "no-ink", "empty-window")},
            "key_fires": sum(1 for r in eff if r.get("key_fires")),
            "locator_sources": {
                src: sum(1 for r in rows
                         if r["locator_source"] == src)
                for src in {r["locator_source"] for r in rows}},
        }
        pages.append(entry)
    return pages


# ── C3: synthetic probes (runtime-undilated mask law) ─────────

def draw_probe(ink_rgb, bg_rgb, ink2_rgb=None, mode="solid", jpeg=False):
    """Anti-aliased text-line bars on a 240x90 canvas.

    Drawn at 4x and downscaled (LANCZOS) for a realistic AA fringe;
    font-independent so results reproduce without font assets.
    mode: solid | gradient | split. Returns (image_bgr, true_mask)
    where true_mask = cleaned TRUE stroke mask (the runtime
    undilated-CTD-prob-map analogue: close + clean, no dilation).
    """
    S = 4
    W, H = 240 * S, 90 * S
    canvas = PILImage.new("RGB", (W, H), tuple(bg_rgb))
    draw = ImageDraw.Draw(canvas)
    bar_h, gap = 8 * S, 14 * S
    y0 = 8 * S
    x0, x1 = 18 * S, 222 * S
    ink2 = ink2_rgb if ink2_rgb is not None else ink_rgb
    for li in range(4):
        yy = y0 + li * (bar_h + gap)
        if mode == "solid":
            color = tuple(ink_rgb)
        elif mode == "gradient":
            t = li / 3.0
            color = tuple(int(round(ink_rgb[c] * (1 - t)
                                    + ink2[c] * t)) for c in range(3))
        elif mode == "split":
            half = (x0 + x1) // 2
            draw.rectangle([x0, yy, half, yy + bar_h],
                           fill=tuple(ink_rgb))
            draw.rectangle([half, yy, x1, yy + bar_h],
                           fill=tuple(ink2))
            continue
        draw.rectangle([x0, yy, x1, yy + bar_h], fill=color)
    img = canvas.resize((240, 90), PILImage.LANCZOS)
    mcanvas = PILImage.new("L", (W, H), 0)
    mdraw = ImageDraw.Draw(mcanvas)
    for li in range(4):
        yy = y0 + li * (bar_h + gap)
        mdraw.rectangle([x0, yy, x1, yy + bar_h], fill=255)
    mm = np.array(mcanvas.resize((240, 90), PILImage.LANCZOS))
    true_mask = clean_binary_mask(((mm > 127) * 255).astype(np.uint8))
    arr = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    if jpeg:
        ok, buf = cv2.imencode(".jpg", arr,
                               [cv2.IMWRITE_JPEG_QUALITY, 85])
        arr = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    return arr, true_mask


def run_probes():
    if not HAS_PIL:
        return {"status": "skipped — PIL unavailable"}

    # (name, ink, ink2, bg, mode, jpeg, expect_class, expect_fire,
    #  color_tolerance_l2 or None)
    probe_defs = [
        ("red_on_white",       (255, 0, 0), None, (255, 255, 255), "solid", False, "colored", True, 30),
        ("blue_on_white",      (0, 0, 255), None, (255, 255, 255), "solid", False, "colored", True, 30),
        ("green_on_white",     (0, 128, 0), None, (255, 255, 255), "solid", False, "colored", True, 30),
        ("yellow_on_white",    (255, 220, 0), None, (255, 255, 255), "solid", False, "colored", True, 30),
        ("cyan_on_white",      (0, 220, 220), None, (255, 255, 255), "solid", False, "colored", True, 30),
        ("magenta_on_white",   (220, 0, 220), None, (255, 255, 255), "solid", False, "colored", True, 30),
        ("darkred_on_white",   (170, 30, 30), None, (255, 255, 255), "solid", False, "colored", True, 30),
        ("lightblue_on_white", (120, 170, 255), None, (255, 255, 255), "solid", False, "colored", True, 30),
        ("white_on_black",     (255, 255, 255), None, (0, 0, 0), "solid", False, "white", False, None),
        ("black_on_white",     (0, 0, 0), None, (255, 255, 255), "solid", False, "black", False, None),
        ("gray_on_white",      (128, 128, 128), None, (255, 255, 255), "solid", False, "gray", False, None),
        ("red_on_white_jpeg",  (255, 0, 0), None, (255, 255, 255), "solid", True, "colored", True, 35),
        ("red_on_pink",        (200, 0, 0), None, (240, 200, 200), "solid", False, "colored", True, 35),
        ("red_on_red_lowc",    (255, 40, 40), None, (230, 60, 60), "solid", False, "colored", False, None),
        ("gradient_red_blue",  (255, 0, 0), (0, 0, 255), (255, 255, 255), "gradient", False, "colored", False, None),
        ("split_red_blue",     (255, 0, 0), (0, 0, 255), (255, 255, 255), "split", False, "colored", False, None),
    ]

    results = []
    for (name, ink, ink2, bg, mode, jpeg,
         exp_cls, exp_fire, tol) in probe_defs:
        img, mask = draw_probe(ink, bg, ink2_rgb=ink2,
                               mode=mode, jpeg=jpeg)
        s = sample_region(img, mask, 0, 0, 240, 90)
        got_cls = s.get("class") if s else None
        got_fire = s.get("key_fires") if s else None
        color_err = None
        if tol is not None and s and "med_rgb" in s:
            color_err = int(round(float(np.linalg.norm(
                np.array(s["med_rgb"], float)
                - np.array(ink, float)))))
        verdict = "PASS" if (
            got_cls == exp_cls and got_fire == exp_fire
            and (tol is None or (color_err is not None
                                 and color_err <= tol))) else "FAIL"
        results.append({
            "probe": name,
            "expected_class": exp_cls,
            "expected_key_fires": exp_fire,
            "got_class": got_cls,
            "got_key_fires": got_fire,
            "sampled_med_rgb": s.get("med_rgb") if s else None,
            "color_err_l2": color_err,
            "tolerance": tol,
            "gates": s.get("gates") if s else None,
            "verdict": verdict,
        })
    passed = sum(1 for r in results if r["verdict"] == "PASS")
    return {"status": "ok", "passed": passed, "total": len(results),
            "probes": results}


# ── C4: manual inspection + Otsu numeric cross-check ─────────

def otsu_cross(pages_census, samples_root, extra_root):
    """Maskless numeric cross-check: Otsu threshold inside each
    selected region window; ink = the side farther from the window
    median. Independent of both locator and sampler."""
    by_name = {p["name"]: p for p in pages_census
               if p.get("status") == "ok"}
    out = []
    for (pname, rid) in MANUAL_SELECTION:
        p = by_name.get(pname)
        if not p:
            continue
        row = next((r for r in p["region_rows"]
                    if r["id"] == rid), None)
        if not row:
            continue
        path = resolve_page(p["dir"], p["source"],
                            samples_root, extra_root)
        img = cv2.imread(os.path.join(path, "original.jpg"))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        x, y, w, h = row["xywh"]
        x1, y1, x2, y2 = window_box(gray.shape, x, y, w, h)
        roi = gray[y1:y2, x1:x2]
        thr, _ = cv2.threshold(roi, 0, 255,
                               cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        med = float(np.median(roi))
        ink_sel = (roi < thr) if med > thr else (roi > thr)
        if int(ink_sel.sum()) < 10:
            cls = "no-visible-ink"
            med_rgb = None
        else:
            px = img[y1:y2, x1:x2][ink_sel].astype(np.int16)
            m = np.median(px, axis=0)
            med_rgb = [int(m[2]), int(m[1]), int(m[0])]
            chroma = max(med_rgb) - min(med_rgb)
            V = max(med_rgb)
            cls = ("colored" if chroma >= CHROMA_COLORED
                   else "white" if V >= V_WHITE
                   else "black" if V <= V_BLACK else "gray")
        out.append({"page": pname, "region_id": rid,
                    "otsu_class": cls, "otsu_med_rgb": med_rgb})
    return out


def manual_check(pages_census, workdir, samples_root, extra_root):
    by_name = {p["name"]: p for p in pages_census
               if p.get("status") == "ok"}
    picks = []
    for (pname, rid) in MANUAL_SELECTION:
        p = by_name.get(pname)
        if not p:
            continue
        row = next((r for r in p["region_rows"]
                    if r["id"] == rid), None)
        if not row:
            continue
        picks.append((pname, rid, p, row))

    os.makedirs(workdir, exist_ok=True)
    tile_h = 130
    tiles = []
    for (pname, rid, p, row) in picks:
        path = resolve_page(p["dir"], p["source"],
                            samples_root, extra_root)
        img = cv2.imread(os.path.join(path, "original.jpg"))
        x, y, w, h = row["xywh"]
        x1, y1 = max(0, x - 6), max(0, y - 6)
        x2 = min(img.shape[1], x + w + 6)
        y2 = min(img.shape[0], y + h + 6)
        crop = img[y1:y2, x1:x2]
        scale = tile_h / crop.shape[0]
        crop = cv2.resize(crop, (max(1, int(crop.shape[1] * scale)),
                                 tile_h))
        med = row.get("med_rgb") or [0, 0, 0]
        bgr = (int(med[2]), int(med[1]), int(med[0]))
        swatch = np.full((tile_h, 60, 3), bgr, np.uint8)
        tile = np.concatenate([crop, swatch], axis=1)
        label = np.full((26, tile.shape[1], 3), 255, np.uint8)
        cv2.putText(label, f"{pname} r{rid} cls={row.get('class')}",
                    (6, 19), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (0, 0, 0), 1, cv2.LINE_AA)
        tiles.append(np.concatenate([label, tile], axis=0))

    sheet_path = None
    if tiles:
        width = max(t.shape[1] for t in tiles)
        sheet = np.full((sum(t.shape[0] for t in tiles)
                         + 8 * (len(tiles) - 1), width, 3),
                        240, np.uint8)
        yy = 0
        for t in tiles:
            sheet[yy:yy + t.shape[0], :t.shape[1]] = t
            yy += t.shape[0] + 8
        sheet_path = os.path.join(workdir, "contact_sheet.png")
        cv2.imwrite(sheet_path, sheet)

    records = []
    correct = 0
    graded = 0
    for (pname, rid, p, row) in picks:
        truth = MANUAL_TRUTH.get((pname, rid))
        algo = row.get("class")
        def norm(c):
            return "gray*" if c in ("gray", "mixed/gradient") else c
        ok = (truth is not None and norm(truth) == norm(algo))
        if truth is not None:
            graded += 1
            correct += 1 if ok else 0
        records.append({
            "page": pname, "region_id": rid,
            "algorithm_class": algo,
            "manual_class": truth,
            "agree": bool(ok),
        })
    return {
        "sheet": sheet_path,
        "selection": [f"{p} r{r}" for (p, r) in MANUAL_SELECTION],
        "records": records,
        "agreement": (f"{correct}/{graded}") if graded else "ungraded",
        "accuracy": round(correct / graded, 3) if graded else None,
    }


# ── main ──────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--samples-root",
                    default=os.path.join(repo_root, "samples"))
    ap.add_argument("--extra-root",
                    default="/home/z/my-project/m009_work")
    ap.add_argument("--workdir",
                    default="/home/z/my-project/m009_b3_work")
    ap.add_argument("--out",
                    default=os.path.join(
                        repo_root, "scripts",
                        "m009_b3_color_measure_results.json"))
    args = ap.parse_args()

    print("MANGABD-009 B3 Phase A — ink-color measurement")
    print(f"  samples_root : {args.samples_root}")
    print(f"  extra_root   : {args.extra_root}")
    print(f"  workdir      : {args.workdir}")
    print()

    pages = census(args.samples_root, args.extra_root)
    for p in pages:
        if p.get("status") != "ok":
            print(f"  [{p['name']}] {p['status']}")
            continue
        s = p["summary"]
        mc = p["saved_mask_character"]
        print(f"  [{p['name']}] regions={p['regions']} "
              f"md5={p['original_md5'][:8]} "
              f"dup_of={p.get('duplicate_of')} "
              f"mask={mc['verdict']} "
              f"classes={s['classes']} key_fires={s['key_fires']}")

    probes = run_probes()
    print(f"  probes: {probes.get('passed')}/{probes.get('total')} PASS")

    otsu = otsu_cross(pages, args.samples_root, args.extra_root)
    manual = manual_check(pages, args.workdir,
                          args.samples_root, args.extra_root)
    # otsu-vs-algorithm agreement
    alg = {r["page"] + f" r{r['region_id']}": r
           for r in manual["records"]}
    otsu_agree = 0
    otsu_graded = 0
    for o in otsu:
        key = f"{o['page']} r{o['region_id']}"
        a = alg.get(key)
        if a and o["otsu_class"] not in (None,):
            otsu_graded += 1
            same = (o["otsu_class"] == a["algorithm_class"]
                    or (o["otsu_class"] == "no-visible-ink"
                        and a["algorithm_class"] in ("no-ink",
                                                     "gray")))
            otsu_agree += 1 if same else 0
    print(f"  manual agreement: {manual['agreement']}")
    print(f"  otsu cross-check agreement: "
          f"{otsu_agree}/{otsu_graded}")

    # C5 corpus verdict
    directive_ok = [p for p in pages
                    if p.get("status") == "ok"
                    and p["name"] in {n for n, _, _ in DIRECTIVE_PAGES}]
    total_regions = sum(p["regions"] for p in directive_ok)
    total_fires = sum(p["summary"]["key_fires"] for p in directive_ok)
    distinct_md5 = sorted({p["original_md5"] for p in pages
                           if p.get("status") == "ok"})

    out = {
        "instrument": "scripts/m009_b3_color_measure.py",
        "batch": "MANGABD-009 B3 Phase A (docs-only, NO source changes)",
        "notebook_sha256_pin": "8926a2b313f655369cb5bac1e0bf3164"
                               "54082d8eac01d197cd52cd4aff8c7615",
        "knobs_under_test": {
            "chroma_colored": CHROMA_COLORED,
            "v_white": V_WHITE, "v_black": V_BLACK,
            "min_ink_px": MIN_INK_PX, "mad_max": MAD_MAX,
            "ring_delta_min": RING_DELTA_MIN,
            "bimodal_min_frac": BIMODAL_MIN_FRAC,
            "bimodal_hue_sep_deg": BIMODAL_HUE_SEP_DEG,
            "chroma_sensitivity": list(CHROMA_SENS),
            "locator_deviance": LOCATOR_DEVIANCE,
            "locator_trust": "mask-vs-ring contrast >= ring_delta_min",
        },
        "pages": pages,
        "synthetic_probes": probes,
        "otsu_cross_check": otsu,
        "otsu_cross_agreement": f"{otsu_agree}/{otsu_graded}",
        "otsu_cross_note": (
            "The Otsu cross-check is the naive maskless baseline; its "
            "3 misses are exactly the hard windows where the locator "
            "law wins: S010 r5 (dark window + large white burst art — "
            "Otsu calls the art the ink; the stroke-precise mask "
            "correctly samples the black text strokes), S011 r6 "
            "(2.4% white strokes on a dark window), S011 r8 (gray 158 "
            "strokes vs Otsu's dark-side pick). Recorded as evidence "
            "for the mask-based locator, not as sampler error."
        ),
        "vlm_visual_passes": VLM_PASSES,
        "manual_inspection": manual,
        "corpus_verdict": {
            "directive_pages": [n for n, _, _ in DIRECTIVE_PAGES],
            "directive_regions_total": total_regions,
            "directive_key_fires_total": total_fires,
            "distinct_source_images": len(distinct_md5),
            "distinct_md5": distinct_md5,
            "colored_ink_in_committed_corpus": bool(total_fires > 0),
            "note": "Committed corpus text ink is black/white/gray "
                    "only. The 'S001_color_webtoon' archive is a "
                    "misleading name: its original.jpg is "
                    "byte-identical to the S003 family source page "
                    "(md5 ledger above) — a B&W page. The colored arm "
                    "therefore validates synthetically (C3) + on "
                    "future Owner pages; on the current corpus the "
                    "feature is inert by construction (0 keys).",
        },
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print(f"\n  results -> {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
