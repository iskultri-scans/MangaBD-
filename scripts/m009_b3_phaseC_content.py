#!/usr/bin/env python3
r"""MANGABD-009 B3 Phase C — anchored patch content (RB3-1..RB3-7).

Branch mangabd-009-b3 @ 8fbde52 (B3 Phase A docs-only; the notebook
blob == main tip == 8926a2b3...7615).

Ruling (Owner, on the Phase A findings 8fbde52):
  RB3-1 APPROVE default ON       — kill-switch available
  RB3-2 APPROVE gray NO          — black render acceptable (3/41)
  RB3-3 APPROVE vertical as-is   — V-3 white stays hardcoded black
  RB3-4 APPROVE undilated only   — CTD raw mask ONLY; artifact
                                   fallback = skip, no key
  RB3-5 APPROVE skip + WARN      — multi-color/gradient SFX: no
                                   dominant-color pick
  RB3-6 APPROVE no render floor  — trust the sampled color (the
                                   mask-vs-ring law already gated it)
  RB3-7 APPROVE knob home        — MANGABD_CONFIG["rendering"]
                                   ["color_inherit_enable"]

Scope (the ruling's NEXT block): cells {6, 10, 11, 12} ONLY; battery
Test 23; every OFF/no-key path byte-identical to 8fbde52.

Patches (per cell, all manifest re-derivable):
  cell 6  P1 knob setdefault (rendering mirror law)
          P2 _b3_undilated_ink_mask + _b3_sample_ink_color (the
             Phase A instrument's validated sampler, runtime law)
          P3 per-page b3_ink_mask build (RB3-4 undilated-only)
          P4 region-loop conditional ink_color key (RF-18 law)
  cell 10 P1 render_bengali_text ink_color kwarg + apply
          P2 detections-parse b3_page_ink map (knob-gated, validated)
          P3 row lookup + choose_text_color override (single site)
          P4 render call forwards ink_color
          P5 battery Test 23 (end-to-end + kill-switch byte-parity)
  cell 11 P1 wrapper signature      P2 vertical arm ink_color
          P3 fallback forward       P4 wrapper self-check (7.5b)
  cell 12 P1 wrapper signature      P2 vertical arm ink_color
          P3 fallback forward       P4 full-chain check (7.7)
"""

# ════════════════════════════════════════════════════════════════════
# cell 6
# ════════════════════════════════════════════════════════════════════

C6_P1_OLD = """MANGABD_CONFIG["detection"].setdefault("b2_orientation_enable", True)

# RF-16: ring-margin (px)"""

C6_P1_NEW = """MANGABD_CONFIG["detection"].setdefault("b2_orientation_enable", True)

# MANGABD-009 B3 (RB3-1/RB3-7): ink-color inheritance kill-switch।
# rendering section-এ (render-intent home) — B2 mirror law-এর মতোই
# দুই প্রান্ত একই knob পড়ে: cell-6 sampling gate + cell-10 apply
# gate। default ON (Owner RB3-1): corpus-proven inert for black/
# white/gray (Phase A: 0/41 key fires), বিফল সব পথ RF-17 fallback।
MANGABD_CONFIG["rendering"].setdefault("color_inherit_enable", True)

# RF-16: ring-margin (px)"""


C6_P2_OLD = """    return None


def _b2_mask_orientation(ink_mask, x, y, w, h):"""

C6_P2_NEW = """    return None


def _b3_undilated_ink_mask(raw_mask):
    \"\"\"MANGABD-009 B3 (RB3-4): `_b2_page_ink_mask`-এর undilated CTD
    raw branch-টুকুই হুবহু (threshold > ctd_mask_threshold +
    close(5,5)×2 + clean min_area=3) — কালির রঙ নমুনার একমাত্র বৈধ
    source। saved text_mask.png artifact (inpaint-area / close-
    bridged — Phase A C2-এ মাপা) fallback এখানে নিষিদ্ধ: angle-
    estimator merged blob সহ্য করলেও median কাগজ/ব্যাকগ্রাউন্ড
    ফিরিয়ে দিতে পারে। None → এই page-এ sampling skip (no key,
    silent — reprocessing-without-CTD পথ)।\"\"\"
    if raw_mask is None or raw_mask.size == 0:
        return None
    thr = int(MANGABD_CONFIG["detection"].get("ctd_mask_threshold", 60))
    if int(np.sum(raw_mask > thr)) <= 0:
        return None
    m = cv2.morphologyEx(
        (raw_mask > thr).astype(np.uint8) * 255,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        iterations=2)
    m = clean_binary_mask(m, min_area=3)
    if m is None or int(np.sum(m > 0)) <= 0:
        return None
    return m


def _b3_sample_ink_color(image_bgr, ink_mask, x, y, w, h):
    \"\"\"MANGABD-009 B3: window ∩ undilated ink mask থেকে median
    কালির রঙ + শ্রেণী + colored-key gates।

    Phase A M9-B3-A.3 হুবহু — instrument
    scripts/m009_b3_color_measure.py-এর sample_window (16/16
    probe-validated) runtime-পোর্ট; window law = _b2_mask_orientation-এরটাই
    (bbox ±2, clip)। Returns (ink_color, note): ink_color = [r, g, b]
    শুধু তখনই যখন class colored আর সব gate পাস; নাহলে None + note —
    black/white/gray/no_ink/no_window = silent normal (RF-17-এর হাতে),
    gate_mad/gate_ring/gate_bimodal = WARN-যোগ্য (caller ঠিক করে,
    RB3-5 skip+WARN)।\"\"\"
    H, W = ink_mask.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    if x2 - x1 < 4 or y2 - y1 < 4:
        return None, "no_window"
    win_mask = ink_mask[y1:y2, x1:x2] > 0
    n_px = int(win_mask.sum())
    if n_px < 30:                      # cell-10 choose_text_color mask law
        return None, "no_ink"
    if n_px > 60000:                   # cap law (rng(42) subsample)
        _sel = np.random.default_rng(42).choice(
            n_px, 60000, replace=False)
        _ys, _xs = np.nonzero(win_mask)
        _ys, _xs = _ys[_sel], _xs[_sel]
        px = image_bgr[y1:y2, x1:x2][_ys, _xs].astype(np.int16)
    else:
        px = image_bgr[y1:y2, x1:x2][win_mask].astype(np.int16)
    med_bgr = np.median(px, axis=0)
    med_rgb = [int(med_bgr[2]), int(med_bgr[1]), int(med_bgr[0])]
    mad_bgr = np.median(np.abs(px - med_bgr), axis=0)
    chroma = int(max(med_rgb) - min(med_rgb))
    v_top = int(max(med_rgb))
    if chroma < 45:
        if v_top >= 215:               # white → RF-17 (RB3-3 vertical
            return None, "white"       # arm-এ পৌঁছায়ই না — key নেই)
        if v_top <= 90:
            return None, "black"
        return None, "gray"            # RB3-2: gray inherit NO
    # colored — gates (সব পাস লাগবে, নাহলে no key + WARN)
    if any(int(_m) >= 40 for _m in mad_bgr):
        return None, "gate_mad"        # gradient / multi-value ink
    try:                               # ring: dilate(ink,5) − ink
        _dil = cv2.dilate(
            win_mask.astype(np.uint8) * 255,
            cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (11, 11)))
        _ring = (_dil > 0) & (~win_mask)
        if int(_ring.sum()) >= 10:
            _rmed = np.median(
                image_bgr[y1:y2, x1:x2][_ring].astype(np.int16),
                axis=0)
            if int(round(float(np.linalg.norm(
                    med_bgr.astype(float)
                    - _rmed.astype(float))))) < 40:
                return None, "gate_ring"
    except Exception:
        pass                           # ring নেই → gate pass (instrument law)
    try:                               # hue bimodality (two-color SFX)
        _chr_sel = (px.max(axis=1) - px.min(axis=1)) >= 25
        if int(_chr_sel.sum()) >= 60:
            _hsv = cv2.cvtColor(
                px[_chr_sel].reshape(-1, 1, 3).astype(np.uint8),
                cv2.COLOR_BGR2HSV)[:, 0, 0].astype(np.float64) * 2.0
            _hs = _hsv[np.argsort(_hsv)]
            _n_h = len(_hs)
            if _n_h >= 4:
                _k = int(np.argmax(np.diff(_hs)))
                _arc_a, _arc_b = _hs[:_k + 1], _hs[_k + 1:]

                def _cmean(_arr):
                    return float(np.rad2deg(
                        np.mean(np.deg2rad(_arr)))) % 360.0

                _ma, _mb = _cmean(_arc_a), _cmean(_arc_b)
                _sep = abs(_ma - _mb) % 360.0
                _sep = min(_sep, 360.0 - _sep)
                if (len(_arc_a) / _n_h >= 0.25
                        and len(_arc_b) / _n_h >= 0.25
                        and _sep >= 40.0):
                    return None, "gate_bimodal"
    except Exception:
        pass                           # unimodal ধরে নাও (instrument law)
    return med_rgb, "colored"


def _b2_mask_orientation(ink_mask, x, y, w, h):"""


C6_P3_OLD = """    b2_ink_mask = None
    if MANGABD_CONFIG["detection"].get("b2_orientation_enable", True):
        try:
            b2_ink_mask = _b2_page_ink_mask(
                page_id, image_bgr, ctd_raw_mask)
        except Exception as exc:
            log_event(
                f"B2 ink-mask build failed [{page_id}]: "
                f"{str(exc)[:120]}",
                level="WARN",
            )
"""

C6_P3_NEW = """    b2_ink_mask = None
    if MANGABD_CONFIG["detection"].get("b2_orientation_enable", True):
        try:
            b2_ink_mask = _b2_page_ink_mask(
                page_id, image_bgr, ctd_raw_mask)
        except Exception as exc:
            log_event(
                f"B2 ink-mask build failed [{page_id}]: "
                f"{str(exc)[:120]}",
                level="WARN",
            )

    # MANGABD-009 B3 (RB3-1 default-ON / RB3-4 undilated-only):
    # রঙ উত্তরাধিকারের sampling mask। b2_ink_mask-এর source দুই
    # শাখার যেকোনোটি হতে পারে (raw বা artifact de-dilate) — RB3-4
    # আইনে শুধু undilated CTD raw branch বৈধ, তাই নিজের mask
    # (orientation-ON + raw থাকলে ফলাফল b2_ink_mask-এর সমানই —
    # deterministic একই ops; বাড়তি খরচ একটি morphology build,
    # tens-of-ms)। raw না থাকলে None → এই page-এ কোনো sampling
    # নেই (silent, no key)। knob OFF → build-ই হয় না — zero cost।
    b3_ink_mask = None
    if MANGABD_CONFIG["rendering"].get("color_inherit_enable", True):
        try:
            b3_ink_mask = _b3_undilated_ink_mask(ctd_raw_mask)
        except Exception as exc:
            log_event(
                f"B3 ink-mask build failed [{page_id}]: "
                f"{str(exc)[:120]}",
                level="WARN",
            )
"""


C6_P4_OLD = """        if b2_gt is not None and angle != 0.0:
            regions[-1]["b2_gt_lines"] = int(b2_gt["lines"])
            regions[-1]["b2_gt_spacing"] = round(
                float(b2_gt["spacing"]), 2)
            regions[-1]["b2_gt_cx"] = round(float(b2_gt["cx"]), 2)
            regions[-1]["b2_gt_cy"] = round(float(b2_gt["cy"]), 2)
"""

C6_P4_NEW = """        if b2_gt is not None and angle != 0.0:
            regions[-1]["b2_gt_lines"] = int(b2_gt["lines"])
            regions[-1]["b2_gt_spacing"] = round(
                float(b2_gt["spacing"]), 2)
            regions[-1]["b2_gt_cx"] = round(float(b2_gt["cx"]), 2)
            regions[-1]["b2_gt_cy"] = round(float(b2_gt["cy"]), 2)

        # MANGABD-009 B3 (RB3-2/RB3-4/RB3-5): conditional ink_color
        # key — RF-18 b2_gt_* law-এর মতোই শুধু উত্তীর্ণ row-এ যায়,
        # বাকি সবার detections.json bytes হুবহু আগের মতো। black/
        # white/gray/no-ink = silent (corpus-স্বাভাবিক); gate-fail
        # (gradient/multi-color SFX, low-contrast) = no key + WARN
        # (RB3-5 skip+WARN); sampling exception = WARN + no key
        # (RB21-2 fail-open law)। b3_ink_mask None (knob OFF / raw
        # নেই / build-fail) → block-ই চলে না — zero events।
        if b3_ink_mask is not None:
            try:
                _b3_c, _b3_note = _b3_sample_ink_color(
                    image_bgr, b3_ink_mask, x, y, w, h)
                if _b3_c is not None:
                    regions[-1]["ink_color"] = _b3_c
                elif _b3_note.startswith("gate_"):
                    log_event(
                        f"B3 ink-color gate skip [{page_id} "
                        f"r{i + 1}]: {_b3_note}",
                        level="WARN",
                    )
            except Exception as exc:
                log_event(
                    f"B3 ink-color sampling failed [{page_id} "
                    f"r{i + 1}]: {str(exc)[:120]}",
                    level="WARN",
                )
"""

# ════════════════════════════════════════════════════════════════════
# cell 10
# ════════════════════════════════════════════════════════════════════

C10_P1_OLD = """    text_color=None,
    padding=None,
    fit_result=None,
    fit_w=None,
    fit_h=None,
):
"""

C10_P1_NEW = """    text_color=None,
    padding=None,
    fit_result=None,
    fit_w=None,
    fit_h=None,
    ink_color=None,
):
"""


C10_P2_OLD = """    if text_color is None:
        text_color = (0, 0, 0)
"""

C10_P2_NEW = """    # MANGABD-009 B3 (RB3-1): ink_color = detect-side sampled কালি।
    # None → নিচের exact আগের আচরণ (kwarg-always-sent, None = previous
    # — RF-15 fit_w/fit_h law)। বসালে text_color override — horizontal
    # আর tilted দুটো branch-এই প্রযোজ্য (_render_rotated_text এই
    # text_color-ই পায়)। choose_text_color-এর রায় থেকে আলাদা রাখতে
    # আলাদা kwarg: RF-17 legitimately pure white/black ফেরায়, sampled
    # white/black সেখানে আলাদা করা যেত না (vertical arm সরাসরি এটা
    # পড়ে — cells 11/12)।
    if ink_color is not None:
        text_color = tuple(ink_color)

    if text_color is None:
        text_color = (0, 0, 0)
"""


C10_P3_OLD = """    b2_page_quads = {}
    b2_page_gt = {}
    try:
"""

C10_P3_NEW = """    b2_page_quads = {}
    b2_page_gt = {}
    # MANGABD-009 B3 (RB3-1/RB3-7): knob mirror — cell-6-এর একই
    # rendering.color_inherit_enable (B2 mirror law)। OFF → map-এ
    # কিছুই ঢোকে না, override অসম্ভব — exact current bytes + zero
    # events।
    _b3_inherit = bool(
        MANGABD_CONFIG["rendering"].get("color_inherit_enable", True))
    b3_page_ink = {}
    try:
"""


C10_P4_OLD = """                        \"cx\": _b2_qr.get("b2_gt_cx"),
                        \"cy\": _b2_qr.get("b2_gt_cy"),
                    }
            except (TypeError, ValueError):
                continue
"""

C10_P4_NEW = """                        \"cx\": _b2_qr.get("b2_gt_cx"),
                        \"cy\": _b2_qr.get("b2_gt_cy"),
                    }
                # MANGABD-009 B3 (RB3-4): conditional ink_color key —
                # শুধু colored row-এই থাকে (cell-6 RF-18 law), তাই
                # key-নেই archive-এ এই পথ inert। invalid stored
                # color (3×uint8 নয়) → WARN + ignore → RF-17 fallback।
                if _b3_inherit:
                    _b3_ic = _b2_qr.get("ink_color")
                    if _b3_ic is not None:
                        if (isinstance(_b3_ic, (list, tuple))
                                and len(_b3_ic) == 3
                                and all(
                                    isinstance(_b3_v, int)
                                    and not isinstance(_b3_v, bool)
                                    and 0 <= _b3_v <= 255
                                    for _b3_v in _b3_ic)):
                            b3_page_ink[_b2_rid] = (
                                int(_b3_ic[0]), int(_b3_ic[1]),
                                int(_b3_ic[2]))
                        else:
                            log_event(
                                f"Invalid ink_color ignored "
                                f"[{page_id} r{_b2_rid}] — "
                                f"RF-17 fallback",
                                level="WARN",
                            )
            except (TypeError, ValueError):
                continue
"""


C10_P5_OLD = """        try:
            text_color = choose_text_color(
                inpainted_bgr,
"""

C10_P5_NEW = """        # MANGABD-009 B3: এই row-এর inherited ink (knob OFF বা key
        # না থাকলে None — নিচের পুরো পথ হুবহু আগের মতো)।
        _b3_row_ink = b3_page_ink.get(region_id)

        try:
            text_color = choose_text_color(
                inpainted_bgr,
"""


C10_P6_OLD = """                region_type=region_type,
                mask=b2_gt_mask,
            )

            bold = region_type in ["sfx", "narrator"]
"""

C10_P6_NEW = """                region_type=region_type,
                mask=b2_gt_mask,
            )

            # MANGABD-009 B3 (RB3-1): validated ink-color key থাকলে
            # choose_text_color-এর binary রায় ভেঙে মূল কালির রঙই
            # বসে (horizontal + tilted দুটোতেই — দুটোই এই
            # text_color পায়)। contrast floor নেই (RB3-6): sampled
            # রঙ detection-এ mask-vs-ring আইনে যাচাই হয়ে আসছে।
            # key নেই → একদম আগের মতো।
            if _b3_row_ink is not None:
                text_color = _b3_row_ink

            bold = region_type in ["sfx", "narrator"]
"""


C10_P7_OLD = """                stroke_width=stroke_width,
                text_color=text_color,
                fit_result=(b2_gt_fr
"""

C10_P7_NEW = """                stroke_width=stroke_width,
                text_color=text_color,
                ink_color=_b3_row_ink,
                fit_result=(b2_gt_fr
"""


C10_P8_OLD = """# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।"""

C10_P8_NEW = """# Test 23: B3 — ink color inheritance end-to-end (RB3-1..RB3-7)।
# fail-on-current-bytes contract: pre-B3 notebook-এ (a) cell-6 কোনো
# ink_color key লেখে না, (b) render side কখনোই সেটা পড়ে না, (c) base
# render_bengali_text-এ ink_color kwarg নেই — নিচের প্রতিটা arm তাই
# FAIL করত। Arms: (a) detect-side sampler (undilated-mask law +
# classifier + gates, Phase A instrument-এর runtime-পোর্ট); (b) render
# end-to-end: key→red, no-key→black, knob-OFF byte-parity (kill-switch
# law — B2 V7 precedent); (c) invalid stored color → WARN + RF-17
# fallback bytes; (d) base ink_color kwarg: apply + None default
# (RF-15 pattern-এর base প্রান্ত; wrapper প্রান্ত cell-11/12-এ)।
try:
    _t23_knob_prev = MANGABD_CONFIG["rendering"].get(
        "color_inherit_enable", True)

    # (a) detect-side sampler — synthetic ink page + prob map
    _t23_page = np.full((300, 900, 3), 255, np.uint8)
    _t23_raw = np.zeros((300, 900), np.uint8)

    def _t23_ink(x0, y0, w0, h0, rgb):
        cv2.rectangle(_t23_page, (x0, y0), (x0 + w0 - 1, y0 + h0 - 1),
                      (rgb[2], rgb[1], rgb[0]), -1)
        cv2.rectangle(_t23_raw, (x0, y0), (x0 + w0 - 1, y0 + h0 - 1),
                      255, -1)

    _t23_ink(40, 40, 100, 30, (200, 30, 30))     # r1 red solid
    _t23_ink(200, 40, 100, 30, (10, 10, 10))     # r2 black
    _t23_ink(360, 40, 100, 30, (158, 158, 158))  # r3 gray (RB3-2)
    _t23_ink(520, 40, 100, 30, (250, 250, 250))  # r4 white
    _t23_ink(40, 150, 90, 30, (255, 0, 0))       # r5 gradient half red
    _t23_ink(130, 150, 90, 30, (0, 0, 255))      #        half blue
    # r6 red-on-red low-contrast: bg + ink (ring gate) — bg আগে
    cv2.rectangle(_t23_page, (250, 120), (549, 259), (60, 60, 230), -1)
    _t23_ink(270, 150, 180, 24, (255, 40, 40))

    _t23_mask = _b3_undilated_ink_mask(_t23_raw)
    _t23_c1, _t23_n1 = _b3_sample_ink_color(
        _t23_page, _t23_mask, 40, 40, 100, 30)
    _t23_c2, _t23_n2 = _b3_sample_ink_color(
        _t23_page, _t23_mask, 200, 40, 100, 30)
    _t23_c3, _t23_n3 = _b3_sample_ink_color(
        _t23_page, _t23_mask, 360, 40, 100, 30)
    _t23_c4, _t23_n4 = _b3_sample_ink_color(
        _t23_page, _t23_mask, 520, 40, 100, 30)
    _t23_c5, _t23_n5 = _b3_sample_ink_color(
        _t23_page, _t23_mask, 40, 150, 180, 30)
    _t23_c6, _t23_n6 = _b3_sample_ink_color(
        _t23_page, _t23_mask, 270, 150, 180, 24)
    _t23_c7, _t23_n7 = _b3_sample_ink_color(
        _t23_page, _t23_mask, 650, 40, 100, 30)   # no ink → silent

    run_test(
        "B3 sampler: colored fires + median exact (undilated law)",
        (_t23_mask is not None and _t23_c1 == [200, 30, 30]
         and _t23_n1 == "colored"),
        f"mask={_t23_mask is not None} c1={_t23_c1} n1={_t23_n1}",
    )
    run_test(
        "B3 sampler: black/white/gray/no-ink = no key (RB3-2 gray NO)",
        (_t23_c2 is None and _t23_n2 == "black"
         and _t23_c3 is None and _t23_n3 == "gray"
         and _t23_c4 is None and _t23_n4 == "white"
         and _t23_c7 is None and _t23_n7 == "no_ink"),
        f"n2={_t23_n2} n3={_t23_n3} n4={_t23_n4} n7={_t23_n7}",
    )
    run_test(
        "B3 sampler: gates — gradient MAD + red-on-red ring (RB3-5)",
        (_t23_c5 is None and _t23_n5.startswith("gate_")
         and _t23_c6 is None and _t23_n6.startswith("gate_")),
        f"n5={_t23_n5} n6={_t23_n6}",
    )
    run_test(
        "B3 mask law: raw absent / below-threshold → None (RB3-4)",
        (_b3_undilated_ink_mask(None) is None
         and _b3_undilated_ink_mask(
             np.zeros((300, 900), np.uint8)) is None),
        "artifact fallback নিষিদ্ধ — raw নেই মানে skip",
    )

    # (b) render end-to-end — key→red / no-key→black / knob-OFF parity
    _t23_pid = "__b3_t23__"
    _t23_pid2 = "__b3_t23_nk__"
    _t23_pid3 = "__b3_t23_bad__"
    _t23_canvas = np.full((400, 600, 3), 255, np.uint8)

    def _t23_mkpage(pid, ink_key):
        init_page(pid, width=600, height=400,
                  image_np=_t23_canvas, overwrite=True)
        save_image_artifact(pid, "inpainted", _t23_canvas, quality=95)
        _t23_det = {"id": 1, "page_id": pid, "x": 60, "y": 80,
                    "width": 200, "height": 90,
                    "quad": [[60, 80], [260, 80], [260, 170],
                             [60, 170]],
                    "angle": 0.0, "region_type": "bubble",
                    "detector_class": "text_bubble",
                    "detector_score": 0.9, "parent_bubble_id": None}
        if ink_key is not None:
            _t23_det["ink_color"] = ink_key
        save_json_artifact(pid, "detections", [_t23_det])
        mark_stage_done(pid, "detect", meta={"region_count": 1})
        _t23_row = {c: "" for c in TRANSLATION_DF_COLUMNS}
        _t23_row.update({
            "page_id": pid, "page": pid, "id": 1,
            "region_type": "bubble",
            "detector_class": "text_bubble",
            "detector_score": 0.9, "parent_bubble_id": "",
            "x": 60, "y": 80, "width": 200, "height": 90,
            "angle": 0.0, "original_text": "テスト",
            "translated_text": "এই কী হয়েছে বলো তো?!",
            "confidence": 0.9, "ocr_engine": "t23", "is_english": True,
            "bengali_valid": True, "status": "ok", "reading_order": -1,
        })
        upsert_translation_rows(pid, [_t23_row])

    def _t23_redpx(arr):
        # BGR arrays (render_page output / saved finals)
        return int((np.abs(arr.astype(int) - [30, 30, 200])
                    .sum(axis=2) < 90).sum())

    def _t23_redpx_rgb(arr):
        # PIL RGB canvases (direct base-call returns)
        return int((np.abs(arr.astype(int) - [200, 30, 30])
                    .sum(axis=2) < 90).sum())

    def _t23_blackpx(arr):
        return int((np.abs(arr.astype(int) - [0, 0, 0])
                    .sum(axis=2) < 90).sum())

    _t23_mkpage(_t23_pid, [200, 30, 30])     # valid key
    _t23_mkpage(_t23_pid2, None)             # no key (twin)
    _t23_mkpage(_t23_pid3, [300, -5, "x"])   # invalid key

    MANGABD_CONFIG["rendering"]["color_inherit_enable"] = True
    _t23_out_on = render_page(_t23_pid, force=True)
    _t23_out_nk = render_page(_t23_pid2, force=True)
    _t23_red_on = _t23_redpx(_t23_out_on[80:170, 60:260])
    _t23_red_nk = _t23_redpx(_t23_out_nk[80:170, 60:260])
    _t23_black_nk = _t23_blackpx(_t23_out_nk[80:170, 60:260])
    _t23_nk_on_bytes = (get_page_dir(_t23_pid2) / "final.jpg").read_bytes()

    MANGABD_CONFIG["rendering"]["color_inherit_enable"] = False
    _t23_out_off = render_page(_t23_pid, force=True)
    _t23_out_nk_off = render_page(_t23_pid2, force=True)
    _t23_red_off = _t23_redpx(_t23_out_off[80:170, 60:260])
    _t23_off_bytes = (get_page_dir(_t23_pid) / "final.jpg").read_bytes()
    _t23_nk_off_bytes = (get_page_dir(_t23_pid2)
                         / "final.jpg").read_bytes()

    run_test(
        "B3 render: key→red ink, no-key→black (choose override)",
        (_t23_red_on >= 50 and _t23_red_nk == 0 and _t23_black_nk >= 50),
        f"red_on={_t23_red_on} red_nk={_t23_red_nk} "
        f"black_nk={_t23_black_nk}",
    )
    run_test(
        "B3 kill-switch: OFF → override নেই + byte-parity "
        "(knob-OFF == no-key bytes, দুই দিক থেকেই)",
        (_t23_red_off == 0
         and _t23_off_bytes == _t23_nk_on_bytes
         and _t23_nk_on_bytes == _t23_nk_off_bytes),
        f"red_off={_t23_red_off} off==nk_on:"
        f"{_t23_off_bytes == _t23_nk_on_bytes} "
        f"nk_on==nk_off:{_t23_nk_on_bytes == _t23_nk_off_bytes}",
    )

    # (c) invalid stored color → WARN + RF-17 fallback bytes
    MANGABD_CONFIG["rendering"]["color_inherit_enable"] = True
    _t23_ev0 = len(MANGABD_EVENTS)
    _t23_out_bad = render_page(_t23_pid3, force=True)
    _t23_bad_warns = [
        e for e in MANGABD_EVENTS[_t23_ev0:]
        if e.get("level") == "WARN"
        and "Invalid ink_color ignored" in str(e.get("message", ""))
    ]
    _t23_bad_bytes = (get_page_dir(_t23_pid3)
                      / "final.jpg").read_bytes()
    run_test(
        "B3 invalid stored color → WARN + RF-17 fallback bytes",
        (len(_t23_bad_warns) >= 1 and _t23_redpx(
            _t23_out_bad[80:170, 60:260]) == 0
         and _t23_bad_bytes == _t23_nk_on_bytes),
        f"warns={len(_t23_bad_warns)} bytes==nk:"
        f"{_t23_bad_bytes == _t23_nk_on_bytes}",
    )

    # (d) base ink_color kwarg — apply + None default (RF-15 base arm)
    _t23_kw_ok = True
    try:
        _t23_dc = PILImage.new("RGB", (300, 120), (255, 255, 255))
        render_bengali_text(_t23_dc, "লাল", 20, 20, 260, 80,
                            region_type="bubble",
                            text_color=(0, 0, 0),
                            ink_color=(200, 30, 30))
        _t23_dc2 = PILImage.new("RGB", (300, 120), (255, 255, 255))
        render_bengali_text(_t23_dc2, "লাল", 20, 20, 260, 80,
                            region_type="bubble",
                            text_color=(0, 0, 0),
                            ink_color=None)
    except TypeError as _t23_texc:
        _t23_kw_ok = False
        print(f"     {_t23_texc}")
    run_test(
        "B3 base kwarg: ink_color applies; None = previous path",
        (_t23_kw_ok and _t23_redpx_rgb(np.array(_t23_dc)) >= 30
         and _t23_redpx_rgb(np.array(_t23_dc2)) == 0
         and _t23_blackpx(np.array(_t23_dc2)) >= 30),
        f"kw_ok={_t23_kw_ok} "
        f"red={_t23_redpx_rgb(np.array(_t23_dc))} "
        f"red_none={_t23_redpx_rgb(np.array(_t23_dc2))}",
    )
except Exception as _t23_exc:
    run_test("B3 Test 23 (unexpected exception)", False, str(_t23_exc)[:160])
finally:
    try:
        MANGABD_CONFIG["rendering"]["color_inherit_enable"] = \\
            _t23_knob_prev
        _t23_df = globals().get("translation_df")
        if _t23_df is not None and len(_t23_df):
            _t23_keep = _t23_df[~_t23_df["page_id"].isin(
                ["__b3_t23__", "__b3_t23_nk__", "__b3_t23_bad__"])]
            globals()["translation_df"] = _t23_keep
            save_translation_df(_t23_keep)
        for _t23_p in ("__b3_t23__", "__b3_t23_nk__", "__b3_t23_bad__"):
            reset_page(_t23_p, delete_artifacts=True)
    except Exception:
        pass


# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।"""

# ════════════════════════════════════════════════════════════════════
# cell 11
# ════════════════════════════════════════════════════════════════════

C11_P1_OLD = """    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None):
"""

C11_P1_NEW = """    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None, ink_color=None):
"""


C11_P2_OLD = """            return _qc_render_vertical(image_pil, text, x, y, w, h, b, (0,0,0), padding)
"""

C11_P2_NEW = """            # MANGABD-009 B3 (RB3-1): vertical arm-এর hardcoded কালির
            # জায়গায় এখন ink_color (None → আগের exact (0,0,0) —
            # choose_text_color-এর pure white/black রায় থেকে sampled
            # রঙ আলাদা রাখতেই আলাদা kwarg; white-on-vertical key-ই
            # হয় না, RB3-3)। tuple() — fill=text_color+(255,) concat।
            return _qc_render_vertical(image_pil, text, x, y, w, h, b,
                                       tuple(ink_color) if ink_color is not None else (0,0,0),
                                       padding)
"""


C11_P3_OLD = """        return _base_render(image_pil, text, x, y, w, h, angle, region_type,
                            bold, stroke_width, text_color, padding, fit_result,
                            fit_w, fit_h)
"""

C11_P3_NEW = """        return _base_render(image_pil, text, x, y, w, h, angle, region_type,
                            bold, stroke_width, text_color, padding, fit_result,
                            fit_w, fit_h, ink_color=ink_color)
"""


C11_P4_OLD = """print(f"  QUALITY CORE glyph-coverage: {sum(_m8_vtests)}/{len(_m8_vtests)}")

# ── 8) pipeline wrap ──"""

C11_P4_NEW = """print(f"  QUALITY CORE glyph-coverage: {sum(_m8_vtests)}/{len(_m8_vtests)}")

# ── 7.5b) MANGABD-009 B3: wrapper ink_color threading (RB3-1) ──
# এই মুহূর্তে render_bengali_text == এই cell-এর wrapper (base ভেতরে)।
# vertical arm আজ (0,0,0) hardcode করত + text_color ফেলে দিত; B3 law:
# ink_color দিলে সেটাই, None দিলে আগের exact (0,0,0)। horizontal
# fallback arm kwarg-টা base-এ forward করে (RF-15 forwarding law —
# না থাকলে call-time TypeError-এ প্রতিটা region silently blank)।
_m9b3_ok = False
try:
    # vertical arm: V-3 shape (w<90, h>2w) + ink_color → red ink
    _m9b3_cv = PILImage.new("RGB", (400, 600), (255, 255, 255))
    render_bengali_text(_m9b3_cv, "নোট", 20, 40, 60, 300,
                        region_type="bubble", text_color=(0, 0, 0),
                        ink_color=(200, 30, 30))
    _m9b3_red_v = int((np.abs(np.array(_m9b3_cv).astype(int)
                              - [200, 30, 30]).sum(axis=2) < 90).sum())
    # vertical arm, ink_color নেই → আগের মতো exact black
    _m9b3_cv2 = PILImage.new("RGB", (400, 600), (255, 255, 255))
    render_bengali_text(_m9b3_cv2, "নোট", 20, 40, 60, 300,
                        region_type="bubble", text_color=(0, 0, 0))
    _m9b3_a2 = np.array(_m9b3_cv2).astype(int)
    _m9b3_red_v2 = int((np.abs(_m9b3_a2 - [200, 30, 30])
                        .sum(axis=2) < 90).sum())
    _m9b3_black_v2 = int((np.abs(_m9b3_a2 - [0, 0, 0])
                          .sum(axis=2) < 90).sum())
    # horizontal fallback arm: kwarg forward → base apply → red ink
    _m9b3_ch = PILImage.new("RGB", (400, 600), (255, 255, 255))
    render_bengali_text(_m9b3_ch, "লাল", 20, 40, 200, 90,
                        region_type="bubble", text_color=(0, 0, 0),
                        ink_color=(200, 30, 30))
    _m9b3_red_h = int((np.abs(np.array(_m9b3_ch).astype(int)
                              - [200, 30, 30]).sum(axis=2) < 90).sum())
    _m9b3_ok = (_m9b3_red_v >= 40 and _m9b3_red_v2 == 0
                and _m9b3_black_v2 >= 40 and _m9b3_red_h >= 40)
except Exception as _m9b3_exc:
    print(f"     {_m9b3_exc}")
    _m9b3_ok = False
print(("  ✅ " if _m9b3_ok else "  ❌ ")
      + "B3 wrapper ink_color threading (vertical arm + fallback kwarg)")
if not _m9b3_ok:
    raise RuntimeError(
        "Cell 11 B3 ink_color check failed: wrapper-এর vertical arm "
        "ink_color নিচ্ছে না / None-path বদলে গেছে / fallback kwarg "
        "forward হচ্ছে না। Fix করে তারপর পরের cell-এ যাও।"
    )

# ── 8) pipeline wrap ──"""

# ════════════════════════════════════════════════════════════════════
# cell 12
# ════════════════════════════════════════════════════════════════════

C12_P1_OLD = """    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None):
"""

C12_P1_NEW = """    def render_bengali_text(image_pil, text, x, y, w, h, angle=0.0,
                            region_type="bubble", bold=None, stroke_width=None,
                            text_color=None, padding=None, fit_result=None,
                            fit_w=None, fit_h=None, ink_color=None):
"""


C12_P2_OLD = """            return _qc_render_vertical(image_pil, text, x, y, w, h, b, (0, 0, 0), padding)
"""

C12_P2_NEW = """            # MANGABD-009 B3 (RB3-1): vertical arm-এর hardcoded কালির
            # জায়গায় এখন ink_color (None → আগের exact (0,0,0); white-
            # on-vertical key হয় না — RB3-3)।
            return _qc_render_vertical(image_pil, text, x, y, w, h, b,
                                       tuple(ink_color) if ink_color is not None else (0, 0, 0),
                                       padding)
"""


C12_P3_OLD = """        return _qc_orig_render(image_pil, text, x, y, w, h, angle, region_type,
                               bold, stroke_width, text_color, padding, fit_result,
                               fit_w, fit_h)
"""

C12_P3_NEW = """        return _qc_orig_render(image_pil, text, x, y, w, h, angle, region_type,
                               bold, stroke_width, text_color, padding, fit_result,
                               fit_w, fit_h, ink_color=ink_color)
"""


C12_P4_OLD = """if not _t20_ok:
    raise RuntimeError(
        "Cell 12 RF-15 integration battery failed: V-3 wrapper-গুলো "
        "render_page-এর fit_w/fit_h নিতে পারছে না — Run All-এ প্রতিটা "
        "region নীরবে blank হয়ে যায়। Fix করে তারপর পরের cell-এ যাও।"
    )
"""

C12_P4_NEW = """if not _t20_ok:
    raise RuntimeError(
        "Cell 12 RF-15 integration battery failed: V-3 wrapper-গুলো "
        "render_page-এর fit_w/fit_h নিতে পারছে না — Run All-এ প্রতিটা "
        "region নীরবে blank হয়ে যায়। Fix করে তারপর পরের cell-এ যাও।"
    )

# ── 7.7) MANGABD-009 B3: ink-color full-chain integration ──
# Test 20-এর একই আইন, নতুন kwarg-এ: এই মুহূর্তে global
# render_bengali_text == এই cell-এর wrapper → cell-11 wrapper →
# cell-10 base (exec order)। render_page-এর ink_color kwarg এই
# পুরো চেইন দিয়ে গুজরে যেতে হবে — এখানেই ধরা পড়ে (RF-15 seam)।
# তিনটা region: colored horizontal (key → red), colored vertical
# (key → red — V-3 arm এখন রঙ নেয়), keyless vertical (আগের exact
# black)। zero TypeError, তিনটাতেই ink।
_b3c_ok = False
try:
    _b3c_pid = "__b3_chain__"
    _b3c_canvas = np.full((760, 880, 3), 255, np.uint8)
    init_page(_b3c_pid, width=880, height=760,
              image_np=_b3c_canvas, overwrite=True)
    save_image_artifact(_b3c_pid, "inpainted", _b3c_canvas, quality=95)
    save_json_artifact(_b3c_pid, "detections", [
        {"id": 1, "page_id": _b3c_pid, "x": 60, "y": 80,
         "width": 200, "height": 90,
         "quad": [[60, 80], [260, 80], [260, 170], [60, 170]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None,
         "ink_color": [200, 30, 30]},
        {"id": 2, "page_id": _b3c_pid, "x": 380, "y": 60,
         "width": 60, "height": 300,
         "quad": [[380, 60], [440, 60], [440, 360], [380, 360]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None,
         "ink_color": [200, 30, 30]},
        {"id": 3, "page_id": _b3c_pid, "x": 660, "y": 60,
         "width": 60, "height": 300,
         "quad": [[660, 60], [720, 60], [720, 360], [660, 360]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
    ])
    mark_stage_done(_b3c_pid, "detect", meta={"region_count": 3})

    def _b3c_row(rid, x, y, w, h):
        _row = {c: "" for c in TRANSLATION_DF_COLUMNS}
        _row.update({
            "page_id": _b3c_pid, "page": _b3c_pid, "id": int(rid),
            "region_type": "bubble",
            "detector_class": "text_bubble",
            "detector_score": 0.9, "parent_bubble_id": "",
            "x": int(x), "y": int(y),
            "width": int(w), "height": int(h),
            "angle": 0.0, "original_text": "テスト",
            "translated_text": "এই কী হয়েছে বলো তো?!",
            "confidence": 0.9, "ocr_engine": "b3c",
            "is_english": True, "bengali_valid": False,
            "status": "ok", "reading_order": -1,
        })
        return _row

    upsert_translation_rows(_b3c_pid, [
        _b3c_row(1, 60, 80, 200, 90),
        _b3c_row(2, 380, 60, 60, 300),
        _b3c_row(3, 660, 60, 60, 300),
    ])

    _b3c_ev0 = len(MANGABD_EVENTS)
    _b3c_out = render_page(_b3c_pid, force=True)
    _b3c_typerr = sum(
        1 for _b3c_e in MANGABD_EVENTS[_b3c_ev0:]
        if "unexpected keyword argument" in str(_b3c_e.get("message", ""))
    )
    _b3c_reds, _b3c_black3 = [], 0
    for _b3c_rid, (_b3c_x, _b3c_y, _b3c_w, _b3c_h) in (
            (1, (60, 80, 200, 90)), (2, (380, 60, 60, 300)),
            (3, (660, 60, 60, 300))):
        _b3c_roi = np.abs(
            _b3c_out[_b3c_y:_b3c_y + _b3c_h,
                     _b3c_x:_b3c_x + _b3c_w].astype(int)
            - [30, 30, 200]).sum(axis=2)
        _b3c_reds.append(int((_b3c_roi < 90).sum()))
        if _b3c_rid == 3:
            _b3c_blk = np.abs(
                _b3c_out[_b3c_y:_b3c_y + _b3c_h,
                         _b3c_x:_b3c_x + _b3c_w].astype(int)
                - [0, 0, 0]).sum(axis=2)
            _b3c_black3 = int((_b3c_blk < 90).sum())
    _b3c_df = translation_df[translation_df["page_id"] == _b3c_pid]
    _b3c_rend = int((_b3c_df["status"] == "rendered").sum())
    _b3c_ok = (_b3c_typerr == 0 and _b3c_rend == 3
               and _b3c_reds[0] >= 40 and _b3c_reds[1] >= 40
               and _b3c_reds[2] == 0 and _b3c_black3 >= 40)
    print(("  ✅ " if _b3c_ok else "  ❌ ")
          + "B3 ink-color full-chain integration "
          + f"(red h/v={_b3c_reds[:2]} keyless-v black="
          + f"{_b3c_black3} typerr={_b3c_typerr} "
          + f"rendered={_b3c_rend}/3)")
except Exception as _b3c_exc:
    print(f"     {_b3c_exc}")
    _b3c_ok = False
finally:
    try:
        _b3c_df2 = globals().get("translation_df")
        if _b3c_df2 is not None and len(_b3c_df2):
            _b3c_keep = _b3c_df2[_b3c_df2["page_id"] != "__b3_chain__"]
            globals()["translation_df"] = _b3c_keep
            save_translation_df(_b3c_keep)
        reset_page("__b3_chain__", delete_artifacts=True)
    except Exception:
        pass

if not _b3c_ok:
    raise RuntimeError(
        "Cell 12 B3 ink-color chain failed: render_page-এর ink_color "
        "kwarg wrapper-চেইন দিয়ে যাচ্ছে না / vertical arm রঙ নিচ্ছে "
        "না / keyless vertical বদলে গেছে। Fix করে তারপর পরের cell-এ যাও।"
    )
"""
