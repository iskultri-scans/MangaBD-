#!/usr/bin/env python3
r"""MANGABD-009 B2 Phase C — cell-06 patch content (RB2-1..RB2-7).

Base = main @ 5fe8804 (notebook blob == f218b35's, sha256 0858a1c9…).
Scope cell 6 carries: the 9b estimator section (knob + pixel-PCA
function) + region-build wiring + the conditional detect-meta key.
Every OLD string is anchor-unique in the pre cell (build asserts 1x).
"""

# ── 9b section insert: knob + estimator (RB2-3 source, RB2-1 semantic,
#    RB2-2 snap, RB2-4 quad recompute, RB2-7 kill-switch) ──────────────
C06_SECTION_OLD = '''print("  ✅ Crop helpers ready")
print()


# ═══════════════════════════════════════════════════════════
# 10. Visualization
'''

C06_SECTION_NEW = '''print("  ✅ Crop helpers ready")
print()


# ═══════════════════════════════════════════════════════════
# 9b. MANGABD-009 B2: orientation inheritance (pixel-PCA angle)
# ═══════════════════════════════════════════════════════════
# Phase A (5fe8804) + Owner ruling RB2-1..RB2-7: region-এর ink
# principal-axis angle পিক্সেল থেকেই মাপা হয় (slicer-proof — cell-24
# slicer CTD textlines ফেলে দেয়, তাই CTD-quad source বাতিল)। শুধুই
# tilted শ্রেণি (5° <= |tilt| < 85°) + confidence gates পাস করা,
# non-V-3 region dev-from-nearest-cardinal (RB2-1) পায়, |dev| < 5°
# snap (RB2-2); axis-aligned / truly-vertical / V-3 / low-conf সবই
# (0.0, None) — তাদের detections.json row আগের মতোই byte-identical।
# Corpus-proven (Phase A instrument + archives): 0/36 row-ই non-zero।
# Kill-switch: b2_orientation_enable (RB2-7 default-ON; False হলে
# region-build call-ই হয় না — full pipeline আগের exact bytes)।

MANGABD_CONFIG["detection"].setdefault("b2_orientation_enable", True)


def _estimate_region_angle(image_bgr, x, y, w, h):
    """MANGABD-009 B2 (RB2-1..RB2-4): pixel-PCA orientation inheritance।

    Region crop-এর dark-ink pixel-গুলোর PCA principal axis থেকে θcw
    মাপে; fold mod-180 → Owner classification bands; শুধু tilted
    শ্রেণির high-confidence non-V-3 region-ই dev-from-nearest-cardinal
    (RB2-1) পায়, |dev| < 5° snap (RB2-2)। pil_angle = −θcw (Phase A
    V2 sign proof) — cell-10-এর dormant render chain ঠিক এই sign-ই
    খায়। Returns (pil_angle, quad): non-inheriting হলে (0.0, None)।
    Inheriting হলে quad = PCA axes-এ বসানো সত্যি rotated rect (RB2-4
    — crop_region_rotated-এর OCR deskew + render fit dims দুটোই এটা
    খায়)।
    """
    # V-3 vertical-note predicate — cells-11/12 L305-এর হুবহু সূত্র।
    # সরু-লম্বা region কখনোই tilt পায় না; vertical arm byte-identical।
    if w < 90 and h > 2 * max(1, w):
        return 0.0, None

    # region + 2px context (Phase A instrument-এর একই crop window)
    H, W = image_bgr.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return 0.0, None
    crop = image_bgr[y1:y2, x1:x2]

    # ink mask: dark pixels + Otsu fallback + despeckle (instrument extract_ink)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    ink = (gray < 100).astype(np.uint8) * 255
    if int(ink.sum() // 255) < 30:
        _otsu, _ = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        ink = (gray < max(int(_otsu), 40)).astype(np.uint8) * 255
    _nl, _lab, _st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    if _nl > 1:
        _keep = np.zeros_like(ink)
        for _ci in range(1, _nl):
            if _st[_ci, cv2.CC_STAT_AREA] >= 6:
                _keep[_lab == _ci] = 255
        if int(_keep.sum() // 255) >= 30:
            ink = _keep

    ys, xs = np.nonzero(ink)
    if len(xs) < 100:                      # tiny region — unmeasurable
        return 0.0, None
    if len(xs) > 60000:                    # estimator-identical subsample
        _sel = np.random.default_rng(42).choice(
            len(xs), 60000, replace=False)
        xs, ys = xs[_sel], ys[_sel]
    pts = np.stack(
        [xs.astype(np.float64), ys.astype(np.float64)], axis=1)

    # E1: PCA principal axis + anisotropy (orientation certainty)
    centered = pts - pts.mean(axis=0)
    cov = centered.T @ centered / len(pts)
    ev, evec = np.linalg.eigh(cov)         # ascending eigenvalues
    if ev[1] <= 0:
        return 0.0, None
    aniso = float(ev[0] / ev[1])
    theta_cw = float(np.degrees(np.arctan2(evec[1, 1], evec[0, 1])))

    # fold mod-180 → signed tilt; Owner bands (axis <5 / vertical 85-95)
    tilt = (theta_cw + 180.0) % 180.0
    if tilt > 90.0:
        tilt -= 180.0
    a = abs(tilt)
    if a < 5.0 or a >= 85.0:               # axis-aligned / truly-vertical
        return 0.0, None
    if aniso > 0.70:                       # near-isotropic cloud — unstable
        return 0.0, None

    # E2: minAreaRect cross-check — mod-180 কৌণিক দূরত্বে (Phase A
    # instrument-এর signed diff ±90 fold-পার্শ্বে wrap করত; ওই quirk-এর
    # সংশোধন — corpus-এ শুধু vertical-class row-গুলোই ছুঁয়েছিল, যারা
    # কখনোই store করে না)
    _p32 = np.stack(
        [xs.astype(np.float32), ys.astype(np.float32)], axis=1)
    _box = cv2.boxPoints(cv2.minAreaRect(_p32))
    _d01 = _box[1] - _box[0]
    _d03 = _box[3] - _box[0]
    _d = _d01 if np.linalg.norm(_d01) >= np.linalg.norm(_d03) else _d03
    t_mar = (float(np.degrees(np.arctan2(_d[1], _d[0]))) + 180.0) % 180.0
    if t_mar > 90.0:
        t_mar -= 180.0
    _dist = abs(t_mar - tilt) % 180.0
    _dist = min(_dist, 180.0 - _dist)
    if _dist > 10.0:
        return 0.0, None

    # RB2-1: dev-from-nearest-cardinal; RB2-2: 5° snap; V2: pil = −θcw
    dev = tilt - 90.0 * round(tilt / 90.0)
    if abs(dev) < 5.0:
        return 0.0, None
    pil_angle = round(-dev, 2)

    # RB2-4: সত্যি rotated-rect quad — PCA axes-এর ফ্রেমে ink-এর
    # projection রেঞ্জই extents। theta-কে [−45°, 135°)-এ canonicalize
    # (u = reading direction: horizontal পড়া → ডানে, vertical পড়া →
    # নিচে — eigenvector sign arbitrary; এতে OCR crop মাথা-নিচে হয় না)।
    thq = (theta_cw + 45.0) % 180.0 - 45.0
    t = np.radians(thq)
    u = np.array([np.cos(t), np.sin(t)])
    v = np.array([-np.sin(t), np.cos(t)])
    center = pts.mean(axis=0)
    pu = (pts - center) @ u
    pv = (pts - center) @ v
    wu = float(pu.max() - pu.min())
    hv = float(pv.max() - pv.min())
    if wu < 5.0 or hv < 5.0:
        return 0.0, None
    qc = center + ((pu.max() + pu.min()) / 2.0) * u \\
                + ((pv.max() + pv.min()) / 2.0) * v
    hw, hh = wu / 2.0, hv / 2.0
    quad = [
        [round(float(qc[0] - hw * u[0] - hh * v[0]) + x1, 2),
         round(float(qc[1] - hw * u[1] - hh * v[1]) + y1, 2)],
        [round(float(qc[0] + hw * u[0] - hh * v[0]) + x1, 2),
         round(float(qc[1] + hw * u[1] - hh * v[1]) + y1, 2)],
        [round(float(qc[0] + hw * u[0] + hh * v[0]) + x1, 2),
         round(float(qc[1] + hw * u[1] + hh * v[1]) + y1, 2)],
        [round(float(qc[0] - hw * u[0] + hh * v[0]) + x1, 2),
         round(float(qc[1] - hw * u[1] + hh * v[1]) + y1, 2)],
    ]
    return pil_angle, quad


print("  ✅ B2 orientation estimator ready (MANGABD-009 B2, default ON)")
print()


# ═══════════════════════════════════════════════════════════
# 10. Visualization
'''

# ── region-build counter init ────────────────────────────────────────
C06_COUNT_OLD = '''    # Build regions
    regions = []
'''

C06_COUNT_NEW = '''    # Build regions
    regions = []

    b2_tilted_count = 0
'''

# ── region build: kill-switch gate + estimation call (RB2-3) ────────
C06_BUILD_OLD = '''        quad = np.array([
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h],
        ], dtype=np.int32)

        angle = 0.0
'''

C06_BUILD_NEW = '''        quad = np.array([
            [x, y],
            [x + w, y],
            [x + w, y + h],
            [x, y + h],
        ], dtype=np.int32)

        angle = 0.0

        # MANGABD-009 B2 (RB2-3): pixel-PCA orientation inheritance।
        # kill-switch বন্ধ হলে এই কলই হয় না — angle/quad আগের মতোই
        # 0.0/bbox, detections.json byte-identical (full rollback)।
        # tilted শ্রেণির high-confidence region-ই একমাত্র angle + সত্যি
        # quad পায় — বাকি সবার row হুবহু আগের মতো।
        if MANGABD_CONFIG["detection"].get("b2_orientation_enable", True):
            try:
                b2_angle, b2_quad = _estimate_region_angle(
                    image_bgr, x, y, w, h)
                if b2_angle != 0.0:
                    angle = float(b2_angle)
                    if b2_quad is not None:
                        quad = np.round(
                            np.asarray(b2_quad)).astype(np.int32)
                    b2_tilted_count += 1
                    print(
                        f"    📐 B2: region inherits "
                        f"{angle:+.1f}° ({region_type})"
                    )
            except Exception as exc:
                log_event(
                    f"B2 orientation estimation failed [{page_id}]: "
                    f"{str(exc)[:120]}",
                    level="WARN",
                )
'''

# ── detect meta: conditional disclosure key (0 tilt → key absent) ────
C06_META_OLD = '''    mark_stage_done(
        page_id,
        "detect",
        meta={
            "region_count": len(regions),
            "rtdetr_text_bubble": len(text_bubble_boxes),
            "rtdetr_text_free": len(text_free_boxes),
            "rtdetr_bubble": len(bubble_boxes),
            "ctd_fallback_used": ctd_result is not None and not text_bubble_boxes and not text_free_boxes,
            "ctd_mask_used": ctd_raw_mask is not None,
        },
    )
'''

C06_META_NEW = '''    detect_meta = {
        "region_count": len(regions),
        "rtdetr_text_bubble": len(text_bubble_boxes),
        "rtdetr_text_free": len(text_free_boxes),
        "rtdetr_bubble": len(bubble_boxes),
        "ctd_fallback_used": ctd_result is not None and not text_bubble_boxes and not text_free_boxes,
        "ctd_mask_used": ctd_raw_mask is not None,
    }

    # MANGABD-009 B2: শুধু সত্যি কেউ tilt inherit করলেই meta-তে যায় —
    # 0 হলে key নেই (kill-switch/all-axis-aligned archive-এর detect
    # meta আগের মতোই byte-identical)।
    if b2_tilted_count:
        detect_meta["b2_tilted_regions"] = int(b2_tilted_count)

    mark_stage_done(
        page_id,
        "detect",
        meta=detect_meta,
    )
'''
