#!/usr/bin/env python3
"""MANGABD-009 RF-19 — cell-10 battery Test 25 content.

Arms (Owner fast-round scope: "battery Test 25 (false-tilt reject +
production guard fires on id=4-class geometry)"):
  (a) false-tilt reject   — asymmetric emphasis cloud (straight text,
      minAreaRect tilt > 5 deg, the id=4 mechanism) -> gate rejects,
      law stores 0.0 measured, no quad/GT
  (b) genuine-tilt keep   — 12 deg block -> gate SILENT, measured
      tilt + GT lines=3 preserved (B2 RF-18 law intact)
  (c) guard FIRES         — id=4-class render page (angle 7.97,
      thin skewed quad, b2gt lines=1 -> GT-mirror collapses to 1
      line while the horizontal bbox fit needs 2): WARN + horizontal
      re-layout (>= 2 bands, no de-rotation needed) + render-meta
      disclosure + census entry
  (d) healthy single line — short text, wide region: guard SILENT
      (meta clean, output stays 1 band)
  (e) healthy multi-line  — normal region: guard SILENT (>= 2 bands)
  (f) battery census      — _RF19_GUARD_FIRES EXACTLY the (c) fixture
      (blast radius frozen: legacy Tests 1-24 + (d)/(e) all silent)

Geometry is the design-time measured set (scripts/m009_rf19_design.py):
A5 diag4 -> rect_tilt +70.02 deg => law dev -19.98 => +19.98 false
tilt with quad + gt lines=1, band_tilt 0.0, 4 bands; B2 12deg-3bars-240
-> law +12.00 measured, gt lines=3, n_bands=1 (merged) -> silent.
Quad construction uses np trig (cell 10 has no math import).
"""

# ── P6: Test 25, inserted before the RF-13 fixture-hygiene block ────
C10_P6_OLD = """\
# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।\
"""

C10_P6_NEW = '''\
# Test 25: MANGABD-009 RF-19 (Owner fast round — live re-accept id=4:
# angle=7.97 on straight text, area 31313px, single tiny line)।
# (1) band-consistency gate: cell-6 RF-18 law-এ per-word emphasis-এর
# asymmetric ink cloud minAreaRect-কে খালি tilt বলায়; bands horizontal
# (≤2°, ≥2 crisp band) হলে tilt reject → 0.0। (2) production
# tiny-guard: RB31-6 এখন শুধু sentinel নয় — rendered==1 + bbox-fit>=2
# + area>=2000px → horizontal bbox re-layout (no GT mirror) + WARN।
try:
    _t25_knob_prev = MANGABD_CONFIG["rendering"].get(
        "color_inherit_enable", True)
    _t25_pids = ["__rf19_t25_guard__", "__rf19_t25_ok1__",
                 "__rf19_t25_ok2__"]

    # ── (a) false-tilt reject (id=4 class, detection-side) ──
    _t25_page = np.full((560, 640, 3), 255, np.uint8)
    _t25_raw = np.zeros((560, 640), np.uint8)
    for _t25_b in ((70, 230, 50, 76), (90, 250, 105, 131),
                   (110, 270, 160, 186), (130, 290, 215, 241)):
        cv2.rectangle(_t25_page, (_t25_b[0], _t25_b[2]),
                      (_t25_b[1], _t25_b[3]), (10, 10, 10), -1)
        cv2.rectangle(_t25_raw, (_t25_b[0], _t25_b[2]),
                      (_t25_b[1], _t25_b[3]), 255, -1)
    _t25_ys, _t25_xs = np.nonzero(_t25_raw > 0)
    _t25_x, _t25_y = int(_t25_xs.min()), int(_t25_ys.min())
    _t25_w = int(_t25_xs.max()) - _t25_x + 1
    _t25_h = int(_t25_ys.max()) - _t25_y + 1
    # pre-condition: the cloud REALLY fools minAreaRect (>5°) —
    # straight horizontal text, skewed rect frame (id=4 mechanism)
    _t25_pts = np.stack(
        [_t25_xs.astype(np.float64), _t25_ys.astype(np.float64)], 1)
    _t25_rbox = cv2.boxPoints(
        cv2.minAreaRect(_t25_pts.astype(np.float32)))
    _t25_rd01 = _t25_rbox[1] - _t25_rbox[0]
    _t25_rd03 = _t25_rbox[3] - _t25_rbox[0]
    _t25_rdl = (_t25_rd01 if (np.linalg.norm(_t25_rd01)
                              >= np.linalg.norm(_t25_rd03))
                else _t25_rd03)
    _t25_rtilt = float(np.degrees(np.arctan2(
        _t25_rdl[1], _t25_rdl[0])))
    _t25_rtilt = (_t25_rtilt + 180.0) % 180.0
    if _t25_rtilt > 90.0:
        _t25_rtilt -= 180.0
    _t25_worst, _t25_nb = _rf19_band_tilt_max(
        _t25_raw[max(0, _t25_y - 2):_t25_y + _t25_h + 2,
                 max(0, _t25_x - 2):_t25_x + _t25_w + 2] > 0)
    _t25_ga, _t25_gq, _t25_ggt, _t25_gm = _b2_mask_orientation(
        _t25_raw, _t25_x, _t25_y, _t25_w, _t25_h)
    run_test(
        "RF-19 false-tilt gate: asymmetric emphasis cloud (straight "
        "text, minAreaRect > 5°) → bands horizontal → tilt REJECTED, "
        "angle 0.0 stored",
        (abs(_t25_rtilt) > 5.0
         and _t25_worst is not None and _t25_worst <= 2.0
         and _t25_nb >= 2
         and _t25_gm and _t25_ga == 0.0
         and _t25_gq is None and _t25_ggt is None),
        f"rect_tilt={_t25_rtilt:+.2f}° band_tilt={_t25_worst} "
        f"n_bands={_t25_nb} law={_t25_ga}",
    )

    # ── (b) genuine-tilt contrast — gate must stay SILENT ──
    _t25_gb = np.zeros((560, 640), np.uint8)
    for _t25_b in ((60, 300, 60, 84), (60, 300, 120, 144),
                   (60, 300, 180, 204)):
        cv2.rectangle(_t25_gb, (_t25_b[0], _t25_b[2]),
                      (_t25_b[1], _t25_b[3]), 255, -1)
    _t25_gM = cv2.getRotationMatrix2D((180.0, 132.0), 12.0, 1.0)
    _t25_gb = cv2.warpAffine(_t25_gb, _t25_gM, (640, 560),
                             flags=cv2.INTER_NEAREST, borderValue=0)
    _t25_ys2, _t25_xs2 = np.nonzero(_t25_gb > 0)
    _t25_x2, _t25_y2 = int(_t25_xs2.min()), int(_t25_ys2.min())
    _t25_w2 = int(_t25_xs2.max()) - _t25_x2 + 1
    _t25_h2 = int(_t25_ys2.max()) - _t25_y2 + 1
    _t25_ga2, _t25_gq2, _t25_ggt2, _t25_gm2 = _b2_mask_orientation(
        _t25_gb, _t25_x2, _t25_y2, _t25_w2, _t25_h2)
    run_test(
        "RF-19 genuine tilt preserved: 12° block → gate SILENT, "
        "measured tilt + GT kept (B2 RF-18 law intact)",
        (_t25_gm2 and abs(_t25_ga2) > 1.0
         and _t25_gq2 is not None
         and _t25_ggt2 is not None
         and int(_t25_ggt2.get("lines") or 0) == 3),
        f"law={_t25_ga2:+.2f} gt={(_t25_ggt2 or {}).get('lines')} "
        f"box=({_t25_x2},{_t25_y2},{_t25_w2},{_t25_h2})",
    )

    # ── (c) production tiny-guard FIRES on id=4-class geometry ──
    _t25_canvas = np.full((400, 620, 3), 255, np.uint8)

    def _t25_bands(arr):
        _g = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        _p = (_g < 120).sum(axis=1)
        if _p.max() <= 0:
            return 0
        return len(_b31_bands_from_profile(
            np.nonzero(_p >= max(1.0, 0.10 * float(_p.max()))
                       )[0].astype(float), 0.0, float(len(_p))))

    def _t25_mkpage(pid, box, det_extra, text):
        x0, y0, w0, h0 = box
        init_page(pid, width=620, height=400,
                  image_np=_t25_canvas, overwrite=True)
        save_image_artifact(pid, "inpainted", _t25_canvas, quality=95)
        _t25_det = {"id": 1, "page_id": pid, "x": x0, "y": y0,
                    "width": w0, "height": h0,
                    "quad": [[x0, y0], [x0 + w0, y0],
                             [x0 + w0, y0 + h0], [x0, y0 + h0]],
                    "angle": 0.0, "region_type": "bubble",
                    "detector_class": "text_bubble",
                    "detector_score": 0.9, "parent_bubble_id": None}
        _t25_det.update(det_extra)
        save_json_artifact(pid, "detections", [_t25_det])
        mark_stage_done(pid, "detect", meta={"region_count": 1})
        _t25_row = {c: "" for c in TRANSLATION_DF_COLUMNS}
        _t25_row.update({
            "page_id": pid, "page": pid, "id": 1,
            "region_type": "bubble",
            "detector_class": "text_bubble",
            "detector_score": 0.9, "parent_bubble_id": "",
            "x": x0, "y": y0, "width": w0, "height": h0,
            "angle": float(_t25_det["angle"]),
            "original_text": "テスト",
            "translated_text": text,
            "confidence": 0.9, "ocr_engine": "t25", "is_english": True,
            "bengali_valid": True, "status": "ok", "reading_order": -1,
        })
        upsert_translation_rows(pid, [_t25_row])

    # the id=4-class skewed thin quad (wu=208, hv=62 @ 7.97°) + the
    # false-frame merged GT (lines=1) — the single-tiny-line source
    _t25_cx, _t25_cy = 60 + 190 / 2.0, 80 + 165 / 2.0
    _t25_th = np.radians(7.97)
    _t25_u = (float(np.cos(_t25_th)), float(np.sin(_t25_th)))
    _t25_v = (float(-np.sin(_t25_th)), float(np.cos(_t25_th)))
    _t25_hw, _t25_hh = 104.0, 31.0

    def _t25_qcor(su, sv):
        return [round(_t25_cx + su * _t25_hw * _t25_u[0]
                      + sv * _t25_hh * _t25_v[0], 2),
                round(_t25_cy + su * _t25_hw * _t25_u[1]
                      + sv * _t25_hh * _t25_v[1], 2)]

    _t25_quad = [_t25_qcor(-1, -1), _t25_qcor(1, -1),
                 _t25_qcor(1, 1), _t25_qcor(-1, 1)]
    _t25_mkpage("__rf19_t25_guard__", (60, 80, 190, 165), {
        "angle": 7.97, "quad": _t25_quad,
        "b2_gt_lines": 1, "b2_gt_spacing": 0.0,
        "b2_gt_cx": _t25_cx, "b2_gt_cy": _t25_cy,
    }, "এই কী হয়েছে বলো তো?!")
    _t25_ev0 = len(MANGABD_EVENTS)
    _t25_out_g = render_page("__rf19_t25_guard__", force=True)
    _t25_gwarns = [
        e for e in MANGABD_EVENTS[_t25_ev0:]
        if e.get("level") == "WARN"
        and "RF-19 tiny-guard" in str(e.get("message", ""))]
    _t25_gmeta = dict(
        (get_page("__rf19_t25_guard__", required=True)
         .get("meta") or {}))
    run_test(
        "RF-19 tiny-guard FIRES: id=4-class (7.97° + thin quad + "
        "merged GT → single line) → WARN + horizontal re-layout "
        "(≥2 bands, no GT mirror) + meta disclosure",
        (len(_t25_gwarns) >= 1
         and _t25_bands(_t25_out_g[80:245, 60:250]) >= 2
         and _t25_gmeta.get("rf19_tiny_guard") == {"regions": [1]}
         and ("__rf19_t25_guard__", 1) in _RF19_GUARD_FIRES),
        f"warns={len(_t25_gwarns)} "
        f"bands={_t25_bands(_t25_out_g[80:245, 60:250])} "
        f"meta={_t25_gmeta.get('rf19_tiny_guard')}",
    )

    # ── (d) healthy single line — guard SILENT ──
    _t25_mkpage("__rf19_t25_ok1__", (60, 80, 260, 80), {},
                "লাল")
    _t25_ev1 = len(MANGABD_EVENTS)
    _t25_out_1 = render_page("__rf19_t25_ok1__", force=True)
    _t25_w1 = [e for e in MANGABD_EVENTS[_t25_ev1:]
               if e.get("level") == "WARN"
               and "RF-19 tiny-guard" in str(e.get("message", ""))]
    _t25_m1 = dict((get_page("__rf19_t25_ok1__", required=True)
                    .get("meta") or {}))
    run_test(
        "RF-19 healthy single line: short text on a wide region → "
        "guard SILENT (no WARN, meta clean, stays 1 band)",
        (not _t25_w1
         and "rf19_tiny_guard" not in _t25_m1
         and _t25_bands(_t25_out_1[80:160, 60:320]) == 1),
        f"warns={len(_t25_w1)} bands="
        f"{_t25_bands(_t25_out_1[80:160, 60:320])}",
    )

    # ── (e) healthy multi-line — guard SILENT ──
    _t25_mkpage("__rf19_t25_ok2__", (60, 80, 220, 110), {},
                "এই প্রথম লাল লাইনটি এখানে আর এই দ্বিতীয় লাইনটি কালো")
    _t25_ev2 = len(MANGABD_EVENTS)
    _t25_out_2 = render_page("__rf19_t25_ok2__", force=True)
    _t25_w2 = [e for e in MANGABD_EVENTS[_t25_ev2:]
               if e.get("level") == "WARN"
               and "RF-19 tiny-guard" in str(e.get("message", ""))]
    _t25_m2 = dict((get_page("__rf19_t25_ok2__", required=True)
                    .get("meta") or {}))
    run_test(
        "RF-19 healthy multi-line: normal region renders ≥2 lines → "
        "guard SILENT (no WARN, meta clean)",
        (not _t25_w2
         and "rf19_tiny_guard" not in _t25_m2
         and _t25_bands(_t25_out_2[80:190, 60:280]) >= 2),
        f"warns={len(_t25_w2)} bands="
        f"{_t25_bands(_t25_out_2[80:190, 60:280])}",
    )

    # ── (f) battery guard census — blast radius frozen ──
    run_test(
        "RF-19 battery guard census: fires EXACTLY on the id=4-class "
        "fixture (legacy Tests 1-24 + healthy T25d/e all silent)",
        list(_RF19_GUARD_FIRES) == [("__rf19_t25_guard__", 1)],
        f"fires={list(_RF19_GUARD_FIRES)}",
    )
except Exception as _t25_exc:
    run_test("RF-19 Test 25 (unexpected exception)", False,
             str(_t25_exc)[:160])
finally:
    try:
        MANGABD_CONFIG["rendering"]["color_inherit_enable"] = \\
            _t25_knob_prev
        _t25_df = globals().get("translation_df")
        if _t25_df is not None and len(_t25_df):
            _t25_keep = _t25_df[~_t25_df["page_id"].isin(_t25_pids)]
            globals()["translation_df"] = _t25_keep
            save_translation_df(_t25_keep)
        for _t25_p in _t25_pids:
            reset_page(_t25_p, delete_artifacts=True)
    except Exception:
        pass


# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।\
'''

assert C10_P6_OLD != C10_P6_NEW
