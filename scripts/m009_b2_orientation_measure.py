#!/usr/bin/env python3
r"""MANGABD-009 B2 Phase A — orientation inheritance measurement instrument.

Docs + instrument ONLY (Phase A discipline): NO notebook/source changes.

WHAT THIS MEASURES
------------------
The archived detections.json rows all carry angle=0.0 + bbox-reconstructed
quads (the B2 gap: cell-06 L1190-1212 hardcodes them; CTD textline pts are
collapsed to bbox at cell-06 L585-588 and CTD is fallback-only for boxes
anyway — cell-06 L1096). The archives therefore contain NO stored textline
geometry, so this instrument estimates each region's ink principal-axis
angle from the ORIGINAL page pixels (the artist's actual Japanese ink —
exactly the visual energy B2 wants the Bengali render to inherit).

Estimators (independent, all reported):
  E1 PCA          principal axis of ink-pixel coordinates (primary)
  E2 minAreaRect  cv2.minAreaRect long-side direction (OpenCV >=4.5 angles
                  mapped to the same convention)
  E3 Hough        length-weighted median of HoughLinesP segment angles on
                  the dilated ink mask (tertiary cross-check)

CONVENTIONS (proved by the built-in self-tests)
  theta_cw : angle of the principal axis from +x, in image coords (y DOWN)
             => positive = visually CLOCKWISE (text descends to the right).
  pil_angle: -theta_cw  (PIL Image.rotate() is CCW-positive; render chain
             cell-10 L1518 -> L1200 gate -> L1388 rotate(angle) consumes
             exactly this sign, so the production region["angle"] MUST be
             pil_angle for the dormant machinery to fire correctly).
  signed tilt: theta folded mod 180 into (-90, 90]  (a textline axis has no
             arrow: 0 == 180; "backwards" 170 deg == -10 deg visual tilt).

CLASSIFICATION (Owner bands, MANGABD-009 B2 Phase A directive):
  axis-aligned   |tilt| < 5
  truly-vertical 85 <= |tilt| <= 95
  tilted        5 <= |tilt| < 85        (95-180 folds back via mod 180)

ARCHIVES
  primary  : samples/S003_batch2 + S007_mangabd005_02.zip (the 12-region
             decision-class set of M009 Phase A / B1)
  secondary: S001_color_webtoon, S002_batch1, S005_manual, S005_openrouter
             (same-page duplicate pair noted in the results) — included for
             distribution breadth only.

SELF-TESTS (V-series) run BEFORE any archive measurement; a failure aborts
the instrument (no numbers without proofs).
  V1 angle_from_quad(): synthetic quads at known angles recovered <0.1 deg
  V2 sign convention: PIL-rotate a text canvas by beta, PCA must measure
     theta_cw ~= -beta (<1.5 deg) — the pil_angle = -theta_cw proof
  V3 classification bands: 0/12/88/92/178 deg land in the expected classes
  V4 bbox-vs-quad extents: for a W x H rect at angle t, bbox dims are
     bw = W|cos t| + H|sin t|, bh = W|sin t| + H|cos t| — numerically
     verified against constructed quads (quantifies why the rotated-path
     fit must use quad extents, not bbox: e.g. 200x60 @ 20 deg -> bbox
     208x125 = 2.08x the strip's true height).

OUTPUT
  console table + committed JSON results (scripts/m009_b2_orientation_results.json):
  per-region angle (theta_cw, pil_angle), estimator spread, anisotropy,
  classification, V-3 predicate cross-tab, region_type/bold applicability,
  production prediction (angle_to_store + expected machinery activation),
  and the per-archive class distribution.
"""
import json
import math
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
SAMPLES = REPO / "samples"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
RESULTS_PATH = REPO / "scripts" / "m009_b2_orientation_results.json"

AXIS_ALIGNED_BAND = 5.0    # |tilt| < 5  -> axis-aligned (Owner band)
VERTICAL_BAND_LO = 85.0    # 85 <= |tilt| <= 95 -> truly-vertical
VERTICAL_BAND_HI = 95.0
V3_W = 90                  # V-3 predicate: w < 90 and h > 2*max(1, w) (cells 11/12)
CONF_SPREAD_DEG = 10.0     # |E1-E2| must be <= this for "agree"
CONF_ANISO = 0.70          # lambda2/lambda1 above this => near-isotropic => low conf

# V2 self-test font: any renderable font proves the sign convention (the
# glyph set is irrelevant — the ink axis is what is measured). Ordered
# candidates keep the committed instrument runnable in the Colab env (the
# §8-downloaded NotoSansBengali), in the repo workspace (m008_probe pair —
# the M008-verified real fonts; the m009_work downloads are HTML error
# pages, the N-1 evidence), and on any bare host (DejaVu / PIL default).
FONT_CANDIDATES = [
    "/home/z/my-project/m008_probe/fonts/NotoSansBengali-Regular.ttf",
    "/content/mangabd/fonts/NotoSansBengali-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "NotoSansBengali-Regular.ttf",
]


# ══════════════════════════════════════════════════════════════════
# Geometry core (the B2 math, shared with the future Phase C)
# ══════════════════════════════════════════════════════════════════

def angle_from_quad(quad):
    """Angle (deg, theta_cw convention) of a 4-point textline quad.

    Quad order per the CTD/manga-translator convention:
    pts[0..3] = top-left, top-right, bottom-right, bottom-left in the
    TEXTLINE's local frame. The long side defines the reading direction:
    for horizontal-ish lines that is pts[1]-pts[0] (the top edge), for
    vertical text it is pts[3]-pts[0] (the left edge). Using the long
    side makes the estimator aspect-invariant, then mod-180 folding
    removes the axis arrow ambiguity.
    """
    p = np.asarray(quad, dtype=np.float64)
    top = p[1] - p[0]   # local "width" direction
    left = p[3] - p[0]   # local "height" direction
    d = top if np.linalg.norm(top) >= np.linalg.norm(left) else left
    return math.degrees(math.atan2(d[1], d[0]))


def fold_tilt(theta_deg):
    """Fold an undirected-axis angle into signed tilt in (-90, 90]."""
    t = (theta_deg + 180.0) % 180.0     # [0, 180)
    if t > 90.0:
        t -= 180.0                       # (-90, 0)
    return t


def classify_tilt(tilt_deg):
    """Owner classification bands on the folded signed tilt."""
    a = abs(tilt_deg)
    if a < AXIS_ALIGNED_BAND:
        return "axis-aligned"
    if VERTICAL_BAND_LO <= a <= VERTICAL_BAND_HI:
        return "truly-vertical"
    return "tilted"


def dev_from_nearest_cardinal(tilt_deg):
    """OPTION-A render-angle semantic: the ink's lean relative to the
    NEAREST cardinal axis (0 or 90), folded into (-45, 45].

    Why: the archived page proves the dominant ink orientation is STANDARD
    VERTICAL Japanese text (all six unique regions measure |tilt| ~ 82-94
    deg). Storing the raw tilt there would rotate standard bubbles ~90 deg
    and destroy the live-accepted rendering; the nearest-cardinal deviation
    maps every near-cardinal measurement (incl. the noisy 82-85 deg band and
    square-cloud PCA jitter) to a small lean that the <5 deg snap absorbs,
    while genuine diagonal shouts still inherit their full energy up to
    +-45 deg. Option B (raw tilt, capped) is reported alongside for the
    ruling to choose."""
    return tilt_deg - 90.0 * round(tilt_deg / 90.0)


def option_b_raw_tilt_capped(tilt_deg, cap=60.0):
    """OPTION-B render-angle semantic: the raw diagonal itself (manga SFX
    convention - translated shouts follow the same diagonal), capped."""
    a = abs(tilt_deg)
    if a <= cap:
        return tilt_deg
    return (cap if tilt_deg > 0 else -cap)


def v3_predicate(w, h):
    """The V-3 vertical-note claim, byte-equal to cells 11/12 L305
    (w < 90 and h > 2*max(1, w)); B2 production keeps angle 0.0 for
    these so the vertical path stays byte-identical."""
    return w < V3_W and h > 2 * max(1, w)


def quad_extents(quad):
    """(W, H) of the rotated rect: W = long-pair mean, H = short-pair mean
    (crop_region_rotated's exact convention, cell-06 L944-952)."""
    p = np.asarray(quad, dtype=np.float64)
    w = max(np.linalg.norm(p[0] - p[1]), np.linalg.norm(p[2] - p[3]))
    h = max(np.linalg.norm(p[0] - p[3]), np.linalg.norm(p[1] - p[2]))
    return w, h


# ══════════════════════════════════════════════════════════════════
# Pixel-side estimators (the production-candidate source: works for
# RT-DETR regions, sliced pages, and archives alike — no CTD dependency)
# ══════════════════════════════════════════════════════════════════

def extract_ink(crop_bgr):
    """Dark-ink mask of a region crop: grayscale < 100 (the pipeline's own
    ctd_mask_threshold class), despeckled; Otsu fallback if too empty."""
    gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)
    ink = (gray < 100).astype(np.uint8) * 255
    if int(ink.sum() // 255) < 30:
        otsu, _ = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV
                               + cv2.THRESH_OTSU)
        ink = (gray < max(int(otsu), 40)).astype(np.uint8) * 255
    # despeckle: drop connected components < 6 px (screentone/dust)
    n, lab, stats, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    if n > 1:
        keep = np.zeros_like(ink)
        for i in range(1, n):
            if stats[i, cv2.CC_STAT_AREA] >= 6:
                keep[lab == i] = 255
        if int(keep.sum() // 255) >= 30:
            ink = keep
    return ink


def pca_angle(ink):
    """E1: principal-axis angle (theta_cw deg) + anisotropy lambda2/lambda1."""
    ys, xs = np.nonzero(ink)
    if len(xs) < 30:
        return None, None, len(xs)
    if len(xs) > 60000:                       # subsample, estimator-identical
        sel = np.random.default_rng(42).choice(len(xs), 60000, replace=False)
        xs, ys = xs[sel], ys[sel]
    pts = np.stack([xs.astype(np.float64), ys.astype(np.float64)], axis=1)
    pts -= pts.mean(axis=0)
    cov = pts.T @ pts / len(pts)
    ev, evec = np.linalg.eigh(cov)            # ascending
    lam1, lam2 = ev[1], ev[0]                 # lambda1 = major
    major = evec[:, 1]
    theta = math.degrees(math.atan2(major[1], major[0]))
    aniso = float(lam2 / lam1) if lam1 > 0 else 1.0
    return theta, aniso, len(xs)


def minarearect_angle(ink):
    """E2: cv2.minAreaRect long-side direction (theta_cw deg).
    OpenCV >=4.5: rect = ((cx,cy),(w,h),angle in (0,90]); we re-derive the
    direction from the box points directly — convention-free."""
    ys, xs = np.nonzero(ink)
    if len(xs) < 30:
        return None
    pts = np.stack([xs.astype(np.float32), ys.astype(np.float32)], axis=1)
    box = cv2.boxPoints(cv2.minAreaRect(pts))       # 4 corners, ordered
    d01 = box[1] - box[0]
    d03 = box[3] - box[0]
    d = d01 if np.linalg.norm(d01) >= np.linalg.norm(d03) else d03
    return math.degrees(math.atan2(float(d[1]), float(d[0])))


def hough_angle(ink):
    """E3: length-weighted median of HoughLinesP segment angles (deg)."""
    dil = cv2.dilate(ink, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)))
    n_px = int(dil.sum() // 255)
    min_len = max(20, int(min(dil.shape) // 3))
    lines = cv2.HoughLinesP(dil, 1, np.pi / 360,
                            threshold=max(30, n_px // 20),
                            minLineLength=min_len, maxLineGap=4)
    if lines is None or len(lines) == 0:
        return None
    angles, weights = [], []
    for l in lines[:, 0]:
        dx, dy = l[2] - l[0], l[3] - l[1]
        angles.append(fold_tilt(math.degrees(math.atan2(dy, dx))))
        weights.append(math.hypot(dx, dy))
    angles, weights = np.asarray(angles), np.asarray(weights)
    order = np.argsort(angles)
    a, w = angles[order], weights[order]
    c = np.cumsum(w) / w.sum()
    return float(a[np.searchsorted(c, 0.5)])


def measure_region(original_bgr, region):
    """Full per-region measurement. Returns a plain dict for the results JSON."""
    x, y = int(region["x"]), int(region["y"])
    w, h = int(region["width"]), int(region["height"])
    H, W = original_bgr.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    crop = original_bgr[y1:y2, x1:x2]

    ink = extract_ink(crop)
    theta, aniso, n_ink = pca_angle(ink)
    t_mar = minarearect_angle(ink)
    t_hough = hough_angle(ink)

    out = {
        "id": int(region.get("id", 0)),
        "bbox": [x, y, w, h],
        "aspect_w_over_h": round(w / max(1, h), 3),
        "region_type": region.get("region_type"),
        "detector_class": region.get("detector_class"),
        "ink_px": int(n_ink),
        "v3_vertical_predicate": bool(v3_predicate(w, h)),
        "bold_applies": region.get("region_type") in ("sfx", "narrator"),
    }

    if theta is None:
        out.update(theta_cw=None, pil_angle=None, anisotropy=None,
                   minarearect_cw=None, hough_cw=None,
                   estimator_spread_deg=None, tilt=None,
                   classification="unmeasured", confidence="low",
                   angle_to_store_pil=0.0)
        return out

    tilt = fold_tilt(theta)
    ests = [tilt, fold_tilt(t_mar) if t_mar is not None else None,
            t_hough]
    live = [e for e in ests if e is not None]
    spread = (max(live) - min(live)) if len(live) > 1 else 0.0
    agree = (t_mar is None or abs(fold_tilt(t_mar) - tilt) <= CONF_SPREAD_DEG)
    conf = "high" if (agree and aniso is not None and aniso <= CONF_ANISO
                      and n_ink >= 100) else "low"

    cls = classify_tilt(tilt)
    dev = round(dev_from_nearest_cardinal(tilt), 2)
    # Production predictions — PROPOSED rules for the ruling, NOT implemented:
    #   gate (all options): V-3 class / axis-aligned / truly-vertical /
    #   low confidence -> angle stays 0.0 (V-3 + horizontal + standard-vertical
    #   paths byte-identical).
    #   OPTION A (recommended): tilted class stores dev-from-nearest-cardinal.
    #   OPTION B (alternative): tilted class stores the raw tilt, capped +-60.
    store_a = store_b = 0.0
    if (cls == "tilted" and conf == "high"
            and not out["v3_vertical_predicate"]):
        store_a = dev if abs(dev) >= AXIS_ALIGNED_BAND else 0.0
        store_b = round(option_b_raw_tilt_capped(tilt), 2)
    out.update({
        "theta_cw": round(theta, 2),
        "pil_angle": round(-theta, 2),
        "dev_from_nearest_cardinal_deg": dev,
        "anisotropy_lambda2_over_lambda1": round(aniso, 3) if aniso else None,
        "minarearect_cw": round(t_mar, 2) if t_mar is not None else None,
        "hough_cw": round(t_hough, 2) if t_hough is not None else None,
        "estimator_spread_deg": round(spread, 2),
        "tilt_signed_deg": round(tilt, 2),
        "classification": cls,
        "confidence": conf,
        "angle_to_store_option_a_dev_pil": round(store_a, 2),
        "angle_to_store_option_b_rawtilt_pil": round(store_b, 2),
        "machinery_if_stored": (
            "render-tilt + OCR-deskew" if (store_a != 0.0 or store_b != 0.0)
            else "none (byte-identical to current pipeline)"),
    })
    return out


# ══════════════════════════════════════════════════════════════════
# Self-tests (V-series) — proofs, then measurements
# ══════════════════════════════════════════════════════════════════

def make_quad(cx, cy, W, H, theta_deg):
    """Axis-order quad (tl, tr, br, bl) of a W x H rect rotated by theta
    (theta_cw convention) about (cx, cy)."""
    t = math.radians(theta_deg)
    c, s = math.cos(t), math.sin(t)
    # local frame: x' along the "width" (top edge), y' along "height".
    # Image coords y-down: a positive theta tilts the top edge downward.
    def rot(dx, dy):
        return [cx + dx * c - dy * s, cy + dx * s + dy * c]
    return [rot(-W / 2, -H / 2), rot(W / 2, -H / 2),
            rot(W / 2, H / 2), rot(-W / 2, H / 2)]


def selftest():
    results = {}

    # V1 — angle_from_quad recovers synthetic quads.
    # make_quad(theta) rotates the LOCAL frame by theta; the quad's long
    # axis (what angle_from_quad measures) is the local horizontal for
    # wide rects (abs dir = theta) and the local vertical for tall rects
    # (abs dir = 90 + theta). Expected value = fold of the absolute dir.
    worst = 0.0
    cases = [(0, 300, 60), (12, 260, 70), (-17.5, 240, 55),   # horizontal-ish
             (45, 150, 40), (170, 200, 50),                    # incl. 170 -> -10
             (0, 60, 300), (2, 60, 300), (-75, 90, 260)]       # tall: 90+theta
    for th, W, H in cases:
        q = make_quad(400, 400, W, H, th)
        abs_dir = th if W >= H else th + 90.0
        rec = fold_tilt(angle_from_quad(q))
        worst = max(worst, abs(rec - fold_tilt(abs_dir)))
    results["V1_quad_angle_recovery_worst_deg"] = round(worst, 3)
    assert worst < 0.1, f"V1 failed: {worst}"

    # V2 — sign convention: PIL rotate(beta) [CCW visual] then PCA =>
    #      theta_cw ~= -beta  =>  pil_angle = -theta_cw reproduces beta
    font = None
    for cand in FONT_CANDIDATES:
        try:
            font = ImageFont.truetype(cand, 28)
            break
        except OSError:
            continue
    if font is None:
        font = ImageFont.load_default()
        print("  [V2] no candidate font — PIL default (sign proof unaffected)")
    sample_text = "বাংলা টেস্ট লাইন"
    try:
        font.getmask(sample_text).getbbox()  # glyph coverage probe
    except Exception:
        pass
    probe = font.getbbox(sample_text)
    if probe is None or probe[2] - probe[0] < 20:  # tofu/empty fallback
        sample_text = "BANGLA TEST LINE 123"
    worst2 = 0.0
    for beta in (-25.0, -10.0, 10.0, 25.0):
        canvas = PILImage.new("L", (400, 160), 0)
        d = ImageDraw.Draw(canvas)
        d.text((20, 50), sample_text, font=font, fill=255)
        rot = canvas.rotate(beta, expand=True, resample=PILImage.BICUBIC)
        ink = (np.asarray(rot) > 128).astype(np.uint8) * 255
        theta, aniso, n = pca_angle(ink)
        # black-on-white flip: our estimators want ink=255 mask — done.
        worst2 = max(worst2, abs(fold_tilt(theta) - (-beta)))
    results["V2_pil_sign_convention_worst_deg"] = round(worst2, 2)
    assert worst2 < 1.5, f"V2 failed: {worst2}"

    # V3 — classification bands
    bands = [(0, "axis-aligned"), (2, "axis-aligned"), (12, "tilted"),
             (45, "tilted"), (84, "tilted"), (88, "truly-vertical"),
             (90, "truly-vertical"), (178, "axis-aligned"), (-92, "truly-vertical")]
    for t, expect in bands:
        got = classify_tilt(fold_tilt(t))
        assert got == expect, f"V3 failed: {t} -> {got} != {expect}"
    results["V3_classification_bands"] = "9/9 OK"

    # V4 — bbox-vs-quad extents: bw = W|c|+H|s|, bh = W|s|+H|c|
    import numpy.testing as npt
    for W, H, th in [(200, 60, 20), (260, 70, 12), (60, 300, 88),
                     (150, 40, 45), (240, 55, -17.5)]:
        q = np.asarray(make_quad(1000, 1000, W, H, th))
        bw = q[:, 0].max() - q[:, 0].min()
        bh = q[:, 1].max() - q[:, 1].min()
        t = math.radians(th)
        ebw = W * abs(math.cos(t)) + H * abs(math.sin(t))
        ebh = W * abs(math.sin(t)) + H * abs(math.cos(t))
        npt.assert_allclose([bw, bh], [ebw, ebh], atol=0.51)
        # and the quad extents ARE the true strip dims:
        qw, qh = quad_extents(q)
        npt.assert_allclose([qw, qh], [W, H], atol=0.51)
    results["V4_bbox_vs_quad_extents"] = "5/5 OK (bbox overestimates; quad exact)"

    # V5 — bbox overshoot quantified for the record
    W, H, th = 200, 60, 20
    t = math.radians(th)
    overshoot = ((W * abs(math.sin(t)) + H * abs(math.cos(t))) / H)
    results["V5_bbox_height_overshoot_200x60_at_20deg"] = round(overshoot, 2)

    print("── Self-tests (V1-V5) ALL PASS ──")
    for k, v in results.items():
        print(f"  {k}: {v}")
    return results


# ══════════════════════════════════════════════════════════════════
# Archive measurement (M-series)
# ══════════════════════════════════════════════════════════════════

def load_archive(name):
    """(archive_name, original_bgr, regions) for every archived sample."""
    if name == "S007_mangabd005_02":
        with zipfile.ZipFile(S007_ZIP) as z:
            img = cv2.imdecode(
                np.frombuffer(z.read("original.jpg"), np.uint8),
                cv2.IMREAD_COLOR)
            regions = json.loads(z.read("detections.json").decode())
        return img, regions
    d = SAMPLES / name
    img = cv2.imread(str(d / "original.jpg"), cv2.IMREAD_COLOR)
    regions = json.loads((d / "detections.json").read_text())
    return img, regions


def main():
    st = selftest()

    archives = ["S003_batch2", "S007_mangabd005_02",
                "S001_color_webtoon", "S002_batch1",
                "S005_manual", "S005_openrouter"]

    all_out = {"self_tests": st, "conventions": {
        "theta_cw": "image coords y-down; positive = visually clockwise",
        "pil_angle": "-theta_cw (PIL rotate is CCW-positive)",
        "bands": {"axis-aligned": "|tilt| < 5",
                  "truly-vertical": "85 <= |tilt| <= 95",
                  "tilted": "5 <= |tilt| < 85 (95-180 folds via mod 180)"},
    }, "archives": {}}

    for name in archives:
        img, regions = load_archive(name)
        rows = [measure_region(img, r) for r in regions]
        dist = {}
        for r in rows:
            dist[r["classification"]] = dist.get(r["classification"], 0) + 1
        summary = {
            "page": regions[0].get("page_id") if regions else None,
            "regions": len(rows),
            "class_distribution": dist,
        }
        all_out["archives"][name] = {"summary": summary, "regions": rows}

        print(f"\n══ {name} — {summary['page']} ({len(rows)} regions) ══")
        hdr = (f"  {'id':>2} {'type':<9} {'w×h':>9} {'ink':>6} "
               f"{'θcw':>7} {'tilt':>7} {'dev':>6} {'MAR':>7} {'Hough':>6} "
               f"{'spread':>6} {'aniso':>5} {'class':<13} "
               f"{'conf':<5} {'V-3':>3} {'A':>5} {'B':>6}")
        print(hdr)
        for r in rows:
            print(f"  {r['id']:>2} {str(r['region_type']):<9} "
                  f"{r['bbox'][2]:>4}×{r['bbox'][3]:<4} {r['ink_px']:>6} "
                  f"{fmt(r.get('theta_cw')):>7} {fmt(r.get('tilt_signed_deg')):>7} "
                  f"{fmt(r.get('dev_from_nearest_cardinal_deg')):>6} "
                  f"{fmt(r.get('minarearect_cw')):>7} {fmt(r.get('hough_cw')):>6} "
                  f"{fmt(r.get('estimator_spread_deg')):>6} "
                  f"{fmt(r.get('anisotropy_lambda2_over_lambda1')):>5} "
                  f"{r['classification']:<13} {r['confidence']:<5} "
                  f"{('Y' if r['v3_vertical_predicate'] else '-'):>3} "
                  f"{fmt(r.get('angle_to_store_option_a_dev_pil')):>5} "
                  f"{fmt(r.get('angle_to_store_option_b_rawtilt_pil')):>6}")

    # Grand summary — UNIQUE-page dedup: all six archives share the same
    # original (sha256-verified at runtime), so the corpus is 6 unique
    # regions, not 36. Identical copies must not count as distribution
    # evidence (the per-archive rows stay in the JSON for provenance).
    import hashlib as _hl
    oshas = set()
    for name in archives:
        img, _ = load_archive(name)
        oshas.add(_hl.sha256(np.asarray(img).tobytes()).hexdigest())
    same_page = len(oshas) == 1
    tot = {}
    n_store_a = n_store_b = 0
    n_regions = 0
    seen_unique = set()
    uniq_rows = []
    for a in all_out["archives"].values():
        for k, v in a["summary"]["class_distribution"].items():
            tot[k] = tot.get(k, 0) + v
        n_store_a += sum(1 for r in a["regions"]
                         if r.get("angle_to_store_option_a_dev_pil", 0.0) != 0.0)
        n_store_b += sum(1 for r in a["regions"]
                         if r.get("angle_to_store_option_b_rawtilt_pil", 0.0) != 0.0)
        n_regions += a["summary"]["regions"]
        if same_page:
            for r in a["regions"]:
                key = tuple(r["bbox"])
                if key not in seen_unique:
                    seen_unique.add(key)
                    uniq_rows.append(r)
    uniq_dist = {}
    for r in uniq_rows:
        uniq_dist[r["classification"]] = uniq_dist.get(r["classification"], 0) + 1
    all_out["grand_summary"] = {
        "archives": len(archives),
        "regions_total": n_regions,
        "unique_originals": len(oshas),
        "same_source_page_all_archives": same_page,
        "class_distribution_all_copies": tot,
        "class_distribution_unique_regions": uniq_dist,
        "would_store_nonzero_angle_option_a": n_store_a,
        "would_store_nonzero_angle_option_b": n_store_b,
    }
    print(f"\n══ GRAND ({n_regions} region rows / {len(uniq_rows)} unique "
          f"across {len(archives)} archives; same-source-page: {same_page}) ══")
    print(f"  unique-region distribution: {uniq_dist}")
    print(f"  B2 would tilt (option A dev / option B raw): "
          f"{n_store_a} / {n_store_b} rows; rest byte-identical")

    RESULTS_PATH.write_text(json.dumps(all_out, indent=2, ensure_ascii=False))
    print(f"\nresults -> {RESULTS_PATH}")


def fmt(v):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)


if __name__ == "__main__":
    main()
