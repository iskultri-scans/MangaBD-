#!/usr/bin/env python3
r"""MANGABD-009 B3.1 Phase C — cell 6 patch content.

Anchored OLD/NEW pairs against the B3-tip notebook @ cf01aef
(notebook sha256 c719feb6...4d6, cell extracts cells_b31_phaseC/).

Rulings implemented (Owner, on Phase A 13a6e02 — registered M9-B31-R):
  RB31-1  tau = 0.15 chromatic threshold (cluster law)
  RB31-2  raw-threshold locator ONLY for the per-line law (no close)
  RB31-3  line_colors key in detections.json (conditional, per-line)
  RB31-4  per-line chromatic-cluster median, i < min(n_orig, n_trans)
  RB31-5  V-3 vertical path unchanged (shapes skipped per-line)
  Owner phase-C addendum: NARROW BUBBLE FIX — skip close(5,5)x2 when
  region width < 80px (raw locator for narrow regions' orientation).
"""

# ── C6-P1: per-line law helpers (after _b3_sample_ink_color) ──────────
C6_P1_OLD = '''    return med_rgb, "colored"


def _b2_mask_orientation(ink_mask, x, y, w, h):'''

C6_P1_NEW = '''    return med_rgb, "colored"


_B31_LINE_TAU = 0.15   # RB31-1 (Owner ruling, binding)


def _b31_raw_ink_mask(raw_mask):
    """MANGABD-009 B3.1 (RB31-2): raw-threshold locator — thr + clean
    min_area=3, NO morphological close। close(5,5)×2-এর AA-fringe
    per-line population-কে contaminate করে (Phase A মাপা: achromatic
    median কালো থেকে gray-তে সরে, chromatic fraction কমে — R1-এর
    recovery raw-threshold-এ জ্বলে, closed mask-এ নয়), তাই per-line
    law আর narrow-bubble orientation-এর band-structure এই clean
    locator পায়। B3 region law-এর closed mask (_b3_undilated_ink_mask)
    অপরিবর্তিত। None → এই page-এ per-line skip (silent, no key)।"""
    if raw_mask is None or raw_mask.size == 0:
        return None
    thr = int(MANGABD_CONFIG["detection"].get("ctd_mask_threshold", 60))
    if int(np.sum(raw_mask > thr)) <= 0:
        return None
    m = clean_binary_mask(
        (raw_mask > thr).astype(np.uint8) * 255, min_area=3)
    if m is None or int(np.sum(m > 0)) <= 0:
        return None
    return m


def _b31_bands_from_profile(profile, lo, hi):
    """B3.1: _b2_mask_orientation-এর band law VERBATIM (histogram +
    [1,2,3,2,1]/9 smooth + 0.12*peak threshold + <2-bin merge) —
    Phase A instrument-এ 14/14 GT line split। min band thickness 3px।"""
    if hi - lo < 4.0:
        return []
    nb = max(8, int((hi - lo) // 2) + 1)
    hist, _ = np.histogram(profile, bins=nb, range=(lo, hi))
    k = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    sm = np.convolve(hist, k / k.sum(), mode="same")
    peak = float(sm.max())
    if peak <= 0:
        return []
    thr = max(0.5, 0.12 * peak)
    bands, s = [], None
    for i, val in enumerate(sm):
        if val >= thr and s is None:
            s = i
        elif val < thr and s is not None:
            bands.append([s, i])
            s = None
    if s is not None:
        bands.append([s, len(sm)])
    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] < 2:
            merged[-1] = [merged[-1][0], b[1]]
        else:
            merged.append(b)
    binw = (hi - lo) / nb
    out = []
    for bs, be in merged:
        v0 = lo + bs * binw
        v1 = lo + be * binw
        if v1 - v0 >= 3.0:
            out.append((v0, v1))
    return out


def _b31_line_bands(ink_mask, x, y, w, h):
    """B3.1: angle≈0 region-এর line boxes — window-এর ink-এর
    row-profile band split (v-axis = page Y); band intervals page
    coords-এ। Phase A-এর measured law (the instrument VERBATIM port)।"""
    H, W = ink_mask.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return []
    m = ink_mask[y1:y2, x1:x2] > 0
    if int(m.sum()) < 30:
        return []
    ys = np.nonzero(m)[0].astype(np.float64) + y1
    return _b31_bands_from_profile(
        ys, float(ys.min()), float(ys.max()))


def _b31_hue_unimodal(px_rgb):
    """B3.1: B3-এর bimodality gate (chromatic cluster-এ)। True =
    single hue (inherit করা নিরাপদ)। two-hue SFX → False (line-level
    RB3-5)।"""
    chr_sel = (px_rgb.max(axis=1) - px_rgb.min(axis=1)) >= 25
    if int(chr_sel.sum()) < 60:
        return True                       # too few chromatic px to split
    hsv = cv2.cvtColor(
        px_rgb[chr_sel].reshape(-1, 1, 3).astype(np.uint8),
        cv2.COLOR_RGB2HSV)[:, 0, 0].astype(np.float64) * 2.0
    hs = hsv[np.argsort(hsv)]
    n_h = len(hs)
    if n_h < 4:
        return True
    k = int(np.argmax(np.diff(hs)))
    arc_a, arc_b = hs[:k + 1], hs[k + 1:]

    def _cmean(a):
        return float(np.rad2deg(np.mean(np.deg2rad(a)))) % 360.0

    ma, mb = _cmean(arc_a), _cmean(arc_b)
    sep = abs(ma - mb) % 360.0
    sep = min(sep, 360.0 - sep)
    if (len(arc_a) / n_h >= 0.25 and len(arc_b) / n_h >= 0.25
            and sep >= 40.0):
        return False
    return True


def _b31_line_color(page_bgr, ink_mask, x, y, w, h, band, tau):
    """B3.1 (RB31-1/RB31-4): per-line chromatic-CLUSTER law — per-word
    emphasis corpus-এ whole-line median কালো হত (live-REJECT root
    cause), cluster median-ই আসল রঙ। black/white/gray/below_tau =
    silent None; gate_bimodal/gate_ring = None + WARN-যোগ্য (line-level
    RB3-5 — caller ঠিক করে)।"""
    H, W = ink_mask.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None, "no_window"
    by1 = max(y1, int(np.floor(band[0])))
    by2 = min(y2, int(np.ceil(band[1])))
    if by2 - by1 < 3:
        return None, "no_band_window"
    m = ink_mask[by1:by2, x1:x2] > 0
    n_px = int(m.sum())
    if n_px < 30:
        return None, "no_ink"
    px_rgb = page_bgr[by1:by2, x1:x2][m].astype(
        np.int16)[:, ::-1].copy()
    chroma_sel = (px_rgb.max(axis=1) - px_rgb.min(axis=1)) >= 25
    n_chr = int(chroma_sel.sum())
    frac = n_chr / float(n_px)
    if frac < tau:
        if frac < 0.02:
            mmed = np.median(px_rgb, axis=0)
            if int(mmed.max()) >= 215:
                return None, "white"
            if int(mmed.max()) <= 90:
                return None, "black"
            return None, "gray"
        return None, "below_tau"
    if not _b31_hue_unimodal(px_rgb):
        return None, "gate_bimodal"       # two hues in ONE line (SFX)
    try:                                   # ring gate (B3 law)
        m_u8 = m.astype(np.uint8) * 255
        dil = cv2.dilate(
            m_u8, cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (11, 11)))
        ring = (dil > 0) & (~m)
        if int(ring.sum()) >= 10:
            rmed = np.median(
                page_bgr[by1:by2, x1:x2][ring].astype(np.int16),
                axis=0)
            cmed = np.median(px_rgb[chroma_sel], axis=0)
            if int(round(float(np.linalg.norm(
                    cmed.astype(float)
                    - rmed.astype(float))))) < 40:
                return None, "gate_ring"
    except Exception:
        pass
    med = np.median(px_rgb[chroma_sel], axis=0)
    return [int(med[0]), int(med[1]), int(med[2])], "colored"


def _b31_line_colors_key(image_bgr, ink_mask, x, y, w, h, angle):
    """B3.1: per-region per-line orchestrator। Returns (line_colors,
    warns): line_colors = [color-or-None, ...] শুধু তখনই যখন ≥1 line
    colored (conditional-key law — committed corpus 0-key থাকে);
    len == band count == original line count (render-side guard)।
    V-3 vertical shapes (RB31-5 extension) আর |angle| ≥ 5° tilted
    regions কোনো key পায় না (row-profile band law-এর measured domain
    axis-aligned — Phase A; দুটোতেই silent, region-level ink_color
    নিজের আইনে চলে)। warns = [(line_idx, gate_note)] — line-level
    RB3-5 (gate শুধু তখনই যখন ওই line-এ chromatic cluster ছিল)।"""
    if w < 90 and h > 2 * max(1, w):        # V-3 vertical-note shape
        return None, []
    try:
        if abs(float(angle)) >= 5.0:        # tilted: bands need page-Y
            return None, []                 # profile — unmeasured domain
    except (TypeError, ValueError):
        return None, []
    bands = _b31_line_bands(ink_mask, x, y, w, h)
    if not bands:
        return None, []
    cols, warns = [], []
    for bi, band in enumerate(bands):
        c, note = _b31_line_color(
            image_bgr, ink_mask, x, y, w, h, band, _B31_LINE_TAU)
        cols.append(c)
        if c is None and note.startswith("gate_"):
            warns.append((bi, note))
    if not any(c is not None for c in cols):
        return None, warns                  # all-achromatic → no key
    return cols, warns


def _b2_mask_orientation(ink_mask, x, y, w, h):'''

# ── C6-P2: page-level raw locator build (after the b3_ink_mask build) ─
C6_P2_OLD = '''    b3_ink_mask = None
    if MANGABD_CONFIG["rendering"].get("color_inherit_enable", True):
        try:
            b3_ink_mask = _b3_undilated_ink_mask(ctd_raw_mask)
        except Exception as exc:
            log_event(
                f"B3 ink-mask build failed [{page_id}]: "
                f"{str(exc)[:120]}",
                level="WARN",
            )

    # Build regions'''

C6_P2_NEW = '''    b3_ink_mask = None
    if MANGABD_CONFIG["rendering"].get("color_inherit_enable", True):
        try:
            b3_ink_mask = _b3_undilated_ink_mask(ctd_raw_mask)
        except Exception as exc:
            log_event(
                f"B3 ink-mask build failed [{page_id}]: "
                f"{str(exc)[:120]}",
                level="WARN",
            )

    # MANGABD-009 B3.1 (RB31-2): raw-threshold locator (NO close) —
    # per-line color law + narrow-bubble orientation fix-এর source।
    # color knob বা orientation knob যেকোনো একটা চালু থাকলেই build
    # (narrow fix B2-path-এর, per-line law color-path-এর — আলাদা
    # knob-এ আটকানো অর্থহীন); দুটোই OFF → build-ই হয় না — zero cost।
    b31_raw_ink = None
    if (MANGABD_CONFIG["detection"].get("b2_orientation_enable", True)
            or MANGABD_CONFIG["rendering"].get(
                "color_inherit_enable", True)):
        try:
            b31_raw_ink = _b31_raw_ink_mask(ctd_raw_mask)
        except Exception as exc:
            log_event(
                f"B3.1 raw ink-mask build failed [{page_id}]: "
                f"{str(exc)[:120]}",
                level="WARN",
            )

    # Build regions'''

# ── C6-P3: narrow-bubble fix at the orientation call site ────────────
C6_P3_OLD = '''                b2_angle, b2_quad, b2_measured = 0.0, None, False
                if b2_ink_mask is not None:
                    b2_angle, b2_quad, b2_gt, b2_measured = \\
                        _b2_mask_orientation(b2_ink_mask, x, y, w, h)'''

C6_P3_NEW = '''                b2_angle, b2_quad, b2_measured = 0.0, None, False
                if b2_ink_mask is not None:
                    # MANGABD-009 B3.1 (Owner phase-C addendum, V5
                    # fix): w < 80-এর narrow region-এ close(5,5)×2
                    # পাশাপাশি লাইনগুলো bridge করে merged blob বানায়
                    # (merged-GT → single tiny line — Owner id=8
                    # live-REJECT); সেখানে band-structure-এর source
                    # raw locator (committed corpus-এ শূন্য প্রভাব —
                    # পাঁচ archive-এ w<80 non-vertical region নেই,
                    # Phase C মাপা)।
                    _b2_src = b2_ink_mask
                    if w < 80 and b31_raw_ink is not None:
                        _b2_src = b31_raw_ink
                    b2_angle, b2_quad, b2_gt, b2_measured = \\
                        _b2_mask_orientation(_b2_src, x, y, w, h)'''

# ── C6-P4: region-loop conditional line_colors key ────────────────────
C6_P4_OLD = '''            except Exception as exc:
                log_event(
                    f"B3 ink-color sampling failed [{page_id} "
                    f"r{i + 1}]: {str(exc)[:120]}",
                    level="WARN",
                )

    # Sort'''

C6_P4_NEW = '''            except Exception as exc:
                log_event(
                    f"B3 ink-color sampling failed [{page_id} "
                    f"r{i + 1}]: {str(exc)[:120]}",
                    level="WARN",
                )

        # MANGABD-009 B3.1 (RB31-1..RB31-5): conditional per-line
        # line_colors key — RF-18/ink_color law-এর মতোই শুধু উত্তীর্ণ
        # row-এ যায় (≥1 colored line), বাকি সবার detections.json bytes
        # হুবহু আগের মতো (committed corpus 0-key)। len == original
        # line count (render-side guard); entries = color-or-null।
        # V-3/tilted → no key (RB31-5 / measured domain); line gate =
        # null + WARN (line-level RB3-5); exception = WARN + no key
        # (RB21-2 fail-open)। color knob OFF → block-ই চলে না —
        # kill-switch byte-parity (Test 24)।
        if (b31_raw_ink is not None
                and MANGABD_CONFIG["rendering"].get(
                    "color_inherit_enable", True)):
            try:
                _b31_lc, _b31_warns = _b31_line_colors_key(
                    image_bgr, b31_raw_ink, x, y, w, h, angle)
                if _b31_lc is not None:
                    regions[-1]["line_colors"] = _b31_lc
                for _b31_wi, _b31_wnote in _b31_warns:
                    log_event(
                        f"B3.1 line-color gate skip [{page_id} "
                        f"r{i + 1} line{_b31_wi + 1}]: {_b31_wnote}",
                        level="WARN",
                    )
            except Exception as exc:
                log_event(
                    f"B3.1 line-color sampling failed [{page_id} "
                    f"r{i + 1}]: {str(exc)[:120]}",
                    level="WARN",
                )

    # Sort'''
