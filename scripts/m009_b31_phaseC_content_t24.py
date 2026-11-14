#!/usr/bin/env python3
r"""MANGABD-009 B3.1 Phase C — cell 10 battery Test 24 content.

Inserted after Test 23's finally block, before the RF-13 fixture
hygiene block. Arms (Owner ruling RB31-6 + phase-C addendum):
  (a) detect-side per-line law: emphasis red/blue lines fire at
      tau=0.15 (cluster median), black lines silent; B3 region sampler
      still inert on the SAME region (the live-REJECT root cause, one
      assert); V-3/tilted domain skips;
  (b) render end-to-end: mixed red+black lines in ONE bubble + no-op
      key ([None, None]) == keyless twin bytes;
  (c) knob-OFF byte-parity both directions (Test 23 law);
  (d) tiny-text assertion @ 2000px: Owner id=8 class (51x62 = 3162px,
      original 4 lines) -> translated render >= 2 bands;
  (e) narrow-bubble V5: w<80 close-bridging repro (closed mask bands
      <= 2) vs raw locator (== 3) + raw-locator orientation GT >= 2
      lines on the narrow-tilted geometry -> render >= 2 de-rotated
      bands;
  (f) invalid stored line_colors -> WARN + keyless fallback bytes;
  (g) base line_colors kwarg: per-line apply + None default.
"""

C10_P8_OLD = '''        for _t23_p in ("__b3_t23__", "__b3_t23_nk__", "__b3_t23_bad__"):
            reset_page(_t23_p, delete_artifacts=True)
    except Exception:
        pass


# RF-13 fixture hygiene:'''

C10_P8_NEW = '''        for _t23_p in ("__b3_t23__", "__b3_t23_nk__", "__b3_t23_bad__"):
            reset_page(_t23_p, delete_artifacts=True)
    except Exception:
        pass


# Test 24: B3.1 — per-line color inheritance end-to-end (RB31-1..RB31-7
# + Owner phase-C addendum: V5 narrow fix + tiny-text assertion @
# 2000px)। fail-on-current-bytes contract: B3-tip notebook-এ (a) cell-6
# কোনো line_colors key লেখে না, (b) render side সেটা পড়ে না, (c)
# render_bengali_text-এ line_colors kwarg নেই — নিচের প্রতিটা arm তাই
# FAIL করত।
try:
    _t24_knob_prev = MANGABD_CONFIG["rendering"].get(
        "color_inherit_enable", True)

    # (a) detect-side per-line law — per-word emphasis 4-line region
    _t24_page = np.full((560, 640, 3), 255, np.uint8)
    _t24_raw = np.zeros((560, 640), np.uint8)

    def _t24_ink(x0, y0, w0, h0, rgb):
        cv2.rectangle(_t24_page, (x0, y0),
                      (x0 + w0 - 1, y0 + h0 - 1),
                      (rgb[2], rgb[1], rgb[0]), -1)
        cv2.rectangle(_t24_raw, (x0, y0),
                      (x0 + w0 - 1, y0 + h0 - 1), 255, -1)

    # R1 (owner case): 4-line region — black base + line1-এ red
    # emphasis শব্দ + line3-এ blue emphasis শব্দ
    for _t24_ly in (48, 92, 136, 180):
        _t24_ink(50, _t24_ly, 280, 26, (10, 10, 10))
    _t24_ink(200, 92, 80, 26, (200, 30, 30))    # line1 red word
    _t24_ink(200, 180, 80, 26, (30, 30, 180))   # line3 blue word
    _t24_rawloc = _b31_raw_ink_mask(_t24_raw)
    _t24_closed = _b3_undilated_ink_mask(_t24_raw)
    _t24_lc, _t24_wn = _b31_line_colors_key(
        _t24_page, _t24_rawloc, 40, 40, 340, 200, 0.0)
    _t24_b3c, _t24_b3n = _b3_sample_ink_color(
        _t24_page, _t24_closed, 40, 40, 340, 200)
    run_test(
        "B3.1 per-line law: emphasis red/blue lines fire, black lines "
        "silent (tau=0.15 cluster median, RB31-1/2/4)",
        (_t24_rawloc is not None and _t24_lc is not None
         and len(_t24_lc) == 4
         and _t24_lc[0] is None and _t24_lc[2] is None
         and _t24_lc[1] is not None
         and max(abs(_t24_lc[1][0] - 200), abs(_t24_lc[1][1] - 30),
                 abs(_t24_lc[1][2] - 30)) <= 10
         and _t24_lc[3] is not None
         and max(abs(_t24_lc[3][0] - 30), abs(_t24_lc[3][1] - 30),
                 abs(_t24_lc[3][2] - 180)) <= 10),
        f"lc={_t24_lc} warns={len(_t24_wn)}",
    )
    run_test(
        "B3.1 law contrast: B3 region sampler এখনো inert (median "
        "black) — per-line law-ই এই corpus-এর fix",
        (_t24_b3c is None and _t24_b3n in ("black", "gray")),
        f"b3={_t24_b3c} note={_t24_b3n}",
    )
    run_test(
        "B3.1 law domain: V-3 vertical shapes + tilted regions → "
        "no key (RB31-5 extension)",
        (_b31_line_colors_key(_t24_page, _t24_rawloc,
                              40, 300, 60, 260, 0.0) == (None, [])
         and _b31_line_colors_key(_t24_page, _t24_rawloc,
                                  40, 40, 340, 200, 14.0) == (None, [])),
        "vertical + tilted → silent (None, [])",
    )

    # (b) render end-to-end — mixed per-line colors + no-op key law
    _t24_pid = "__b31_t24__"
    _t24_pid2 = "__b31_t24_nk__"
    _t24_pid3 = "__b31_t24_bad__"
    _t24_pid4 = "__b31_t24_null__"
    _t24_pid5 = "__b31_t24_tiny__"
    _t24_pid6 = "__b31_t24_nw__"
    _t24_canvas = np.full((400, 620, 3), 255, np.uint8)

    def _t24_mkpage(pid, box, lc_key, text):
        x0, y0, w0, h0 = box
        init_page(pid, width=620, height=400,
                  image_np=_t24_canvas, overwrite=True)
        save_image_artifact(pid, "inpainted", _t24_canvas, quality=95)
        _t24_det = {"id": 1, "page_id": pid, "x": x0, "y": y0,
                    "width": w0, "height": h0,
                    "quad": [[x0, y0], [x0 + w0, y0],
                             [x0 + w0, y0 + h0], [x0, y0 + h0]],
                    "angle": 0.0, "region_type": "bubble",
                    "detector_class": "text_bubble",
                    "detector_score": 0.9, "parent_bubble_id": None}
        if lc_key is not None:
            _t24_det["line_colors"] = lc_key
        save_json_artifact(pid, "detections", [_t24_det])
        mark_stage_done(pid, "detect", meta={"region_count": 1})
        _t24_row = {c: "" for c in TRANSLATION_DF_COLUMNS}
        _t24_row.update({
            "page_id": pid, "page": pid, "id": 1,
            "region_type": "bubble",
            "detector_class": "text_bubble",
            "detector_score": 0.9, "parent_bubble_id": "",
            "x": x0, "y": y0, "width": w0, "height": h0,
            "angle": 0.0, "original_text": "テスト",
            "translated_text": text,
            "confidence": 0.9, "ocr_engine": "t24", "is_english": True,
            "bengali_valid": True, "status": "ok", "reading_order": -1,
        })
        upsert_translation_rows(pid, [_t24_row])

    def _t24_redpx(arr):
        return int((np.abs(arr.astype(int) - [30, 30, 200])
                    .sum(axis=2) < 90).sum())

    def _t24_blackpx(arr):
        return int((np.abs(arr.astype(int) - [0, 0, 0])
                    .sum(axis=2) < 90).sum())

    def _t24_row_bands(arr):
        # de-rotated row-profile band count (Phase A PART C law)
        gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        prof = (gray < 120).sum(axis=1)
        if prof.max() <= 0:
            return 0
        thr = max(1.0, 0.10 * float(prof.max()))
        return len(_b31_bands_from_profile(
            np.nonzero(prof >= thr)[0].astype(float),
            0.0, float(len(prof))))

    _t24_text = "এই প্রথম লাল লাইনটি এখানে আর এই দ্বিতীয় লাইনটি কালো"
    _t24_mkpage(_t24_pid, (60, 80, 220, 110), [[200, 30, 30], None],
                _t24_text)                     # line0 red, rest base
    _t24_mkpage(_t24_pid2, (60, 80, 220, 110), None, _t24_text)
    _t24_mkpage(_t24_pid3, (60, 80, 220, 110), [200, 30], _t24_text)
    _t24_mkpage(_t24_pid4, (60, 80, 220, 110), [None, None], _t24_text)
    # (d) tiny-text: id=8 class 51x62 (area 3162 >= 2000), 4 original
    _t24_mkpage(_t24_pid5, (320, 240, 51, 62),
                [None, [200, 30, 30], None, None],
                "এই কী হয়েছে বলো তো?!")

    MANGABD_CONFIG["rendering"]["color_inherit_enable"] = True
    _t24_out_on = render_page(_t24_pid, force=True)
    _t24_out_nk = render_page(_t24_pid2, force=True)
    _t24_out_null = render_page(_t24_pid4, force=True)
    _t24_on_red = _t24_redpx(_t24_out_on[70:200, 50:290])
    _t24_on_black = _t24_blackpx(_t24_out_on[70:200, 50:290])
    _t24_nk_bytes = (get_page_dir(_t24_pid2)
                     / "final.jpg").read_bytes()
    _t24_null_bytes = (get_page_dir(_t24_pid4)
                       / "final.jpg").read_bytes()
    run_test(
        "B3.1 render: per-line mixed — red line + black line একই "
        "bubble-এ + no-op key ([None,None]) == keyless bytes",
        (_t24_on_red >= 40 and _t24_on_black >= 40
         and _t24_redpx(_t24_out_nk[70:200, 50:290]) == 0
         and _t24_null_bytes == _t24_nk_bytes),
        f"red={_t24_on_red} black={_t24_on_black} "
        f"null==nk:{_t24_null_bytes == _t24_nk_bytes}",
    )

    # (c) knob-OFF byte-parity (both directions, Test 23 law)
    MANGABD_CONFIG["rendering"]["color_inherit_enable"] = False
    _t24_out_off = render_page(_t24_pid, force=True)
    _t24_out_nk_off = render_page(_t24_pid2, force=True)
    _t24_off_red = _t24_redpx(_t24_out_off[70:200, 50:290])
    _t24_off_bytes = (get_page_dir(_t24_pid)
                      / "final.jpg").read_bytes()
    _t24_nk_off_bytes = (get_page_dir(_t24_pid2)
                         / "final.jpg").read_bytes()
    run_test(
        "B3.1 kill-switch: OFF → per-line override নেই + byte-parity "
        "(knob-OFF == no-key bytes, দুই দিক থেকেই)",
        (_t24_off_red == 0
         and _t24_off_bytes == _t24_nk_bytes
         and _t24_nk_bytes == _t24_nk_off_bytes),
        f"red_off={_t24_off_red} off==nk_on:"
        f"{_t24_off_bytes == _t24_nk_bytes} "
        f"nk_on==nk_off:{_t24_nk_bytes == _t24_nk_off_bytes}",
    )
    MANGABD_CONFIG["rendering"]["color_inherit_enable"] = True

    # (d) tiny-text assertion (RB31-6 @ 2000px) — id=8 class
    _t24_out_tiny = render_page(_t24_pid5, force=True)
    _t24_tiny_bands = _t24_row_bands(_t24_out_tiny[230:315, 310:385])
    run_test(
        "B3.1 tiny-text assertion: original lines >= 2 AND area >= "
        "2000px → translated >= 2 bands (id=8 class: 51x62=3162px)",
        (_t24_tiny_bands >= 2),
        f"bands={_t24_tiny_bands} (area=3162, orig_lines=4)",
    )

    # (e) narrow-bubble V5 — Owner phase-C addendum। দুইটা narrow
    # block (w<80, 12 deg): TIGHT (gap 8px) = merge-মেকানিজম repro —
    # raw locator-এ ৩টে আলাদা line-component, closed mask-এ ১টে
    # merged blob (close(5,5)x2 bridging — V5-এর উৎস, Owner-এর
    # নিজের rationale) + closed-এর orientation GT lines=1 (merged);
    # SPLIT (gap 14px) = raw-locator orientation-এর আসল GT (lines=3)
    # → সেটা দিয়ে render → de-rotated bands >= 2।
    def _t24_nblock(cx, cy, gap, th=3.0, L=28.0, deg=12.0):
        _nb_t = np.radians(deg)
        _nb_u = np.array([np.cos(_nb_t), np.sin(_nb_t)])
        _nb_v = np.array([-np.sin(_nb_t), np.cos(_nb_t)])
        _nb_pitch = th + gap
        _nb_pts = []
        for _nb_bi in (-1, 0, 1):
            _nb_c = np.array([float(cx), float(cy)]) \\
                + _nb_bi * _nb_pitch * _nb_v
            _nb_cs = [_nb_c - L * _nb_u - th / 2 * _nb_v,
                      _nb_c + L * _nb_u - th / 2 * _nb_v,
                      _nb_c + L * _nb_u + th / 2 * _nb_v,
                      _nb_c - L * _nb_u + th / 2 * _nb_v]
            _nb_pts.extend(_nb_cs)
            cv2.fillPoly(_t24_page,
                         [np.round(_nb_cs).astype(np.int32)],
                         (10, 10, 10))
            cv2.fillPoly(_t24_raw,
                         [np.round(_nb_cs).astype(np.int32)], 255)
        _nb_arr = np.array(_nb_pts)
        _nb_x = int(_nb_arr[:, 0].min())
        _nb_y = int(_nb_arr[:, 1].min())
        _nb_w = int(np.ceil(_nb_arr[:, 0].max())) - _nb_x
        _nb_h = int(np.ceil(_nb_arr[:, 1].max())) - _nb_y
        return _nb_x, _nb_y, _nb_w, _nb_h

    def _t24_win_components(mask, bx, by, bw, bh):
        _wc = mask[max(0, by - 2):by + bh + 2,
                   max(0, bx - 2):bx + bw + 2]
        _n, _ = cv2.connectedComponents((_wc > 0).astype(np.uint8))
        return _n - 1

    # TIGHT block: close bridges the 8px gaps + merged GT (V5 source)
    _t24_tx, _t24_ty, _t24_tw, _t24_thh = _t24_nblock(150, 400, 8)
    # SPLIT block: raw-locator GT (lines=3) → the render end-to-end
    _t24_nx, _t24_ny, _t24_nw, _t24_nh = _t24_nblock(480, 330, 14)
    _t24_rawloc2 = _b31_raw_ink_mask(_t24_raw)
    _t24_closed2 = _b3_undilated_ink_mask(_t24_raw)
    _t24_c_ang, _, _t24_c_gt, _t24_c_meas = _b2_mask_orientation(
        _t24_closed2, _t24_tx, _t24_ty, _t24_tw, _t24_thh)
    _t24_comp_raw = _t24_win_components(
        _t24_rawloc2, _t24_tx, _t24_ty, _t24_tw, _t24_thh)
    _t24_comp_closed = _t24_win_components(
        _t24_closed2, _t24_tx, _t24_ty, _t24_tw, _t24_thh)
    run_test(
        "B3.1 narrow V5 mechanism: close(5,5)x2 merges narrow lines "
        "(raw 3 components vs closed 1) + closed GT merged (lines<=1)",
        (_t24_tw < 80
         and _t24_comp_raw == 3 and _t24_comp_closed == 1
         and _t24_c_meas and _t24_c_gt is not None
         and int(_t24_c_gt.get("lines") or 0) <= 1),
        f"w={_t24_tw} comps raw/closed={_t24_comp_raw}/"
        f"{_t24_comp_closed} closed_gt_lines="
        f"{(_t24_c_gt or {}).get('lines')}",
    )
    _t24_ang_r, _t24_quad_r, _t24_gt_r, _t24_meas_r = \\
        _b2_mask_orientation(
            _t24_rawloc2, _t24_nx, _t24_ny, _t24_nw, _t24_nh)
    run_test(
        "B3.1 narrow law: raw-locator orientation on w<80 — measured "
        "tilt + true GT lines (== 3)",
        (_t24_nw < 80 and _t24_meas_r and abs(_t24_ang_r) > 1.0
         and _t24_gt_r is not None
         and int(_t24_gt_r.get("lines") or 0) == 3),
        f"w={_t24_nw} ang={_t24_ang_r} gt={_t24_gt_r}",
    )
    # end-to-end: the FIXED narrow-tilted det row (raw-locator GT) →
    # render → de-rotated bands >= 2
    _t24_pid6 = "__b31_t24_nw__"
    init_page(_t24_pid6, width=620, height=400,
              image_np=_t24_canvas, overwrite=True)
    save_image_artifact(_t24_pid6, "inpainted", _t24_canvas, quality=95)
    _t24_det6 = {"id": 1, "page_id": _t24_pid6,
                 "x": _t24_nx, "y": _t24_ny,
                 "width": _t24_nw, "height": _t24_nh,
                 "quad": [[round(float(p[0]), 2), round(float(p[1]), 2)]
                          for p in (_t24_quad_r or [])],
                 "angle": float(_t24_ang_r), "region_type": "bubble",
                 "detector_class": "text_bubble",
                 "detector_score": 0.9, "parent_bubble_id": None,
                 "b2_gt_lines": int(_t24_gt_r["lines"]),
                 "b2_gt_spacing": round(float(_t24_gt_r["spacing"]), 2),
                 "b2_gt_cx": round(float(_t24_gt_r["cx"]), 2),
                 "b2_gt_cy": round(float(_t24_gt_r["cy"]), 2)}
    save_json_artifact(_t24_pid6, "detections", [_t24_det6])
    mark_stage_done(_t24_pid6, "detect", meta={"region_count": 1})
    _t24_row6 = {c: "" for c in TRANSLATION_DF_COLUMNS}
    _t24_row6.update({
        "page_id": _t24_pid6, "page": _t24_pid6, "id": 1,
        "region_type": "bubble", "detector_class": "text_bubble",
        "detector_score": 0.9, "parent_bubble_id": "",
        "x": _t24_nx, "y": _t24_ny, "width": _t24_nw,
        "height": _t24_nh, "angle": float(_t24_ang_r),
        "original_text": "テスト",
        "translated_text": "এই সরু বুদবুদে তিনটি লাইন আছে",
        "confidence": 0.9, "ocr_engine": "t24", "is_english": True,
        "bengali_valid": True, "status": "ok", "reading_order": -1,
    })
    upsert_translation_rows(_t24_pid6, [_t24_row6])
    _t24_out_nw = render_page(_t24_pid6, force=True)
    _t24_nwx1 = max(0, _t24_nx - 60)
    _t24_nwy1 = max(0, _t24_ny - 60)
    _t24_nwx2 = min(620, _t24_nx + _t24_nw + 60)
    _t24_nwy2 = min(400, _t24_ny + _t24_nh + 60)
    _t24_roi = _t24_out_nw[_t24_nwy1:_t24_nwy2,
                           _t24_nwx1:_t24_nwx2].copy()
    _t24_mmat = cv2.getRotationMatrix2D(
        ((_t24_nx + _t24_nw / 2.0) - _t24_nwx1,
         (_t24_ny + _t24_nh / 2.0) - _t24_nwy1),
        -float(_t24_ang_r), 1.0)
    _t24_roi = cv2.warpAffine(
        _t24_roi, _t24_mmat,
        (_t24_roi.shape[1], _t24_roi.shape[0]),
        flags=cv2.INTER_LINEAR, borderValue=(255, 255, 255))
    _t24_nw_bands = _t24_row_bands(_t24_roi)
    run_test(
        "B3.1 narrow V5 end-to-end: raw-locator GT → render ≥ 2 "
        "de-rotated bands (merged-GT single-tiny আর নেই)",
        (_t24_nw_bands >= 2),
        f"bands={_t24_nw_bands} ang={_t24_ang_r} "
        f"gt_lines={_t24_gt_r['lines']}",
    )

    # (f) invalid stored line_colors → WARN + keyless fallback bytes
    _t24_ev0 = len(MANGABD_EVENTS)
    _t24_out_bad = render_page(_t24_pid3, force=True)
    _t24_bad_warns = [
        e for e in MANGABD_EVENTS[_t24_ev0:]
        if e.get("level") == "WARN"
        and "Invalid line_colors ignored" in str(e.get("message", ""))
    ]
    _t24_bad_bytes = (get_page_dir(_t24_pid3)
                      / "final.jpg").read_bytes()
    run_test(
        "B3.1 invalid stored line_colors → WARN + RF-17 fallback bytes",
        (len(_t24_bad_warns) >= 1
         and _t24_redpx(_t24_out_bad[70:200, 50:290]) == 0
         and _t24_bad_bytes == _t24_nk_bytes),
        f"warns={len(_t24_bad_warns)} bytes==nk:"
        f"{_t24_bad_bytes == _t24_nk_bytes}",
    )

    # (g) base line_colors kwarg — per-line apply + None default
    _t24_kw_ok = True
    try:
        _t24_dc = PILImage.new("RGB", (300, 140), (255, 255, 255))
        render_bengali_text(_t24_dc, _t24_text, 20, 20, 260, 100,
                            region_type="bubble",
                            text_color=(0, 0, 0),
                            line_colors=[(200, 30, 30), None])
        _t24_dc2 = PILImage.new("RGB", (300, 140), (255, 255, 255))
        render_bengali_text(_t24_dc2, _t24_text, 20, 20, 260, 100,
                            region_type="bubble",
                            text_color=(0, 0, 0),
                            line_colors=None)
    except TypeError as _t24_texc:
        _t24_kw_ok = False
        print(f"     {_t24_texc}")
    _t24_dc_red = int((np.abs(np.array(_t24_dc).astype(int)
                              - [200, 30, 30]).sum(axis=2) < 90).sum())
    _t24_dc_black = int((np.abs(np.array(_t24_dc).astype(int)
                                - [0, 0, 0]).sum(axis=2) < 90).sum())
    run_test(
        "B3.1 base kwarg: line_colors per-line apply; None = previous "
        "path (RF-15 base arm)",
        (_t24_kw_ok and _t24_dc_red >= 30 and _t24_dc_black >= 30
         and int((np.abs(np.array(_t24_dc2).astype(int)
                         - [200, 30, 30]).sum(axis=2) < 90).sum()) == 0),
        f"kw_ok={_t24_kw_ok} red={_t24_dc_red} black={_t24_dc_black}",
    )
except Exception as _t24_exc:
    run_test("B3.1 Test 24 (unexpected exception)", False,
             str(_t24_exc)[:160])
finally:
    try:
        MANGABD_CONFIG["rendering"]["color_inherit_enable"] = \\
            _t24_knob_prev
        _t24_df = globals().get("translation_df")
        _t24_pids = ["__b31_t24__", "__b31_t24_nk__", "__b31_t24_bad__",
                     "__b31_t24_null__", "__b31_t24_tiny__",
                     "__b31_t24_nw__"]
        if _t24_df is not None and len(_t24_df):
            _t24_keep = _t24_df[~_t24_df["page_id"].isin(_t24_pids)]
            globals()["translation_df"] = _t24_keep
            save_translation_df(_t24_keep)
        for _t24_p in _t24_pids:
            reset_page(_t24_p, delete_artifacts=True)
    except Exception:
        pass


# RF-13 fixture hygiene:'''
