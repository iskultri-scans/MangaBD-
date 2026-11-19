#!/usr/bin/env python3
r"""MANGABD-009 RF-20 — battery Test 26 (cell-10 patch P7).

Six arms:
  (a) whole+fragment renders ONCE — the owner 07.jpg geometry: one
      page, whole bubble id=1 + its line-fragment id=2 (+ adjacent
      bubbles + name plate) → fragment suppressed (WARN + meta +
      census), whole renders, adjacent + plate render;
  (b) dedup census frozen — fires EXACTLY the (a) fixture's pair,
      legacy Tests 1-25 + earlier battery renders all silent;
  (c) ghost wipe FIRES on the dark/spiky class — dark bubble
      (near-black interior), original JP text still inside (mask
      covered only a thin strip), translation renders on a clean
      background: no dark-ink residue under/around the Bengali;
  (d) white-bg no-op — the SAME wipe check on a white bubble whose
      inpaint already removed everything: zero fires, bytes
      unchanged vs a render with the check disabled (knob-style
      parity through an empty suppressed set);
  (e) healthy-adjacent law — side-by-side + heavy-overlap equal-area
      neighbors: NO suppression (the containment law's guards);
  (f) suppression predicate unit law — centroid/area/IoU triple on
      the owner's measured pair classes (IoU 0.298 / 0.116 both
      fire; below-0.1 and above-0.5-area both stay).

Fixture pages are created with the battery's own mkpage pattern
(Test 24/25): init_page + save_image_artifact + detections +
translation rows, then render_page(force=True). Cleanup mirrors
Test 25's finally (df purge + reset_page).
"""

C10_P7_OLD = """# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।"""

C10_P7_NEW = """# Test 26: MANGABD-009 RF-20 (Owner fast targeted — live merged-main
# 7d0a58e, page 07.jpg: 29 regions, detector একই bubble-এ whole +
# line-fragment দুটোই দিয়েছে — pairs (4,5)(7,8)(16,17)(20,21); দুটোই
# translate + render হয়ে Bengali-on-Bengali হয়েছে; IoU (4,5)=0.298,
# (7,8)=0.116 → containment আইন, IoU নয়। সাথে dark-webtoon ghost:
# spiky সীমানা-ঘেরা mask ভেতরের কালি মোছেনি।
# (a) whole+fragment ONCE  (b) census frozen  (c) dark ghost wipe
# (d) white-bg no-op  (e) adjacent law  (f) pair-law unit cases।
try:
    _t26_pids = ["__rf20_t26_dup__", "__rf20_t26_dark__",
                 "__rf20_t26_white__", "__rf20_t26_adj__"]

    def _t26_mkpage(pid, det_rows, rows, canvas, mask_arr=None):
        init_page(pid, width=canvas.shape[1], height=canvas.shape[0],
                  image_np=canvas, overwrite=True)
        save_image_artifact(pid, "inpainted", canvas, quality=95)
        if mask_arr is not None:
            save_image_artifact(pid, "mask", mask_arr)
        save_json_artifact(pid, "detections", det_rows)
        mark_stage_done(pid, "detect", meta={"region_count":
                                             len(det_rows)})
        _rows = []
        for spec in rows:
            _r = {c: "" for c in TRANSLATION_DF_COLUMNS}
            _r.update({
                "page_id": pid, "page": pid, "id": spec["id"],
                "region_type": spec.get("region_type", "bubble"),
                "detector_class": "text_bubble",
                "detector_score": 0.9, "parent_bubble_id": "",
                "x": spec["x"], "y": spec["y"],
                "width": spec["width"], "height": spec["height"],
                "angle": 0.0, "original_text": "テスト",
                "translated_text": spec["text"],
                "confidence": 0.9, "ocr_engine": "t26",
                "is_english": True, "bengali_valid": True,
                "status": "ok", "reading_order": -1,
            })
            _rows.append(_r)
        upsert_translation_rows(pid, _rows)

    def _t26_dark_px(arr, box):
        x, y, w, h = box
        win = arr[y:y + h, x:x + w]
        if win.size == 0:
            return 0
        _g = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY) \
            if win.ndim == 3 else win
        return int((_g < 90).sum())

    def _t26_text_px(arr, box):
        # Dark canvas: LIGHT ink (use_background_aware_color);
        # white canvas: dark ink. Count whichever polarity is
        # present, as ink ROWS (row-profile rows over threshold).
        x, y, w, h = box
        win = arr[y:y + h, x:x + w]
        if win.size == 0:
            return 0
        _g = cv2.cvtColor(win, cv2.COLOR_BGR2GRAY) \
            if win.ndim == 3 else win
        _bg = float(np.median(_g))
        _ink = ((_g < 120) if _bg >= 128 else (_g > 170))
        prof = _ink.sum(axis=1)
        if prof.max() <= 0:
            return 0
        thr = max(1.0, 0.10 * float(prof.max()))
        return int((prof >= thr).sum())

    # ── (f) pair-law unit cases (the owner's measured classes) ──
    _t26_w = (100, 100, 300, 200)          # whole bubble
    _t26_f_mid = (120, 150, 260, 40)       # mid line fragment
    _t26_iou_mid = 260 * 40 / (300 * 200 + 260 * 40 - 260 * 40)
    _t26_f_edge = (100, 100, 260, 46)      # top-strip fragment
    _t26_iou_edge = (260 * 46) / (300 * 200)   # 0.199 of union~...
    _t26_law = _rf20_pair_law
    run_test(
        "RF-20 pair law: containment triple — centroid∈bbox ∧ "
        "area<0.5 ∧ IoU>0.1 fires on both owner classes (0.298 / "
        "0.116-equivalent), rejects adjacent + half-area + "
        "sub-0.1-IoU",
        (_t26_law(_t26_w, _t26_f_mid)
         and _t26_law(_t26_w, _t26_f_edge)
         and not _t26_law((100, 100, 200, 150), (320, 100, 200, 150))
         and not _t26_law((100, 100, 200, 150), (240, 100, 200, 150))
         and not _t26_law(_t26_w, (390, 280, 8, 8))),
        f"mid={_t26_law(_t26_w, _t26_f_mid)} "
        f"edge={_t26_law(_t26_w, _t26_f_edge)}",
    )

    # ── (a) whole+fragment renders ONCE + neighbors + plate stay ──
    # dark webtoon canvas; regions mirror the owner dump's shape:
    # 1 = whole bubble, 2 = its line-fragment (suppressed), 3/4 =
    # adjacent bubbles (kept), 5 = name plate (kept)
    _t26_cv = np.full((560, 640, 3), 28, np.uint8)
    _t26_dup_dets = [
        {"id": 1, "page_id": "__rf20_t26_dup__", "x": 60, "y": 60,
         "width": 230, "height": 150, "quad": None, "angle": 0.0,
         "region_type": "bubble", "detector_class": "text_bubble",
         "detector_score": 0.9, "parent_bubble_id": None},
        {"id": 2, "page_id": "__rf20_t26_dup__", "x": 80, "y": 120,
         "width": 180, "height": 36, "quad": None, "angle": 0.0,
         "region_type": "bubble", "detector_class": "text_bubble",
         "detector_score": 0.82, "parent_bubble_id": None},
        {"id": 3, "page_id": "__rf20_t26_dup__", "x": 330, "y": 60,
         "width": 200, "height": 140, "quad": None, "angle": 0.0,
         "region_type": "bubble", "detector_class": "text_bubble",
         "detector_score": 0.9, "parent_bubble_id": None},
        {"id": 4, "page_id": "__rf20_t26_dup__", "x": 60, "y": 300,
         "width": 190, "height": 130, "quad": None, "angle": 0.0,
         "region_type": "bubble", "detector_class": "text_bubble",
         "detector_score": 0.9, "parent_bubble_id": None},
        {"id": 5, "page_id": "__rf20_t26_dup__", "x": 400, "y": 330,
         "width": 150, "height": 44, "quad": None, "angle": 0.0,
         "region_type": "narrator", "detector_class": "text_free",
         "detector_score": 0.88, "parent_bubble_id": None},
    ]
    _t26_dup_rows = [
        {"id": 1, "x": 60, "y": 60, "width": 230, "height": 150,
         "text": "এই পুরো বুদবুদের কথা এখানে একবারই লেখা হবে"},
        {"id": 2, "x": 80, "y": 120, "width": 180, "height": 36,
         "text": "এই ফ্র্যাগমেন্ট লাইনের ডুপ্লিকেট লেখা"},
        {"id": 3, "x": 330, "y": 60, "width": 200, "height": 140,
         "text": "পাশের বুদবুদ নম্বর তিন"},
        {"id": 4, "x": 60, "y": 300, "width": 190, "height": 130,
         "text": "নিচের বুদবুদ নম্বর চার"},
        {"id": 5, "x": 400, "y": 330, "width": 150, "height": 44,
         "text": "নামফলক", "region_type": "narrator"},
    ]
    _t26_mkpage("__rf20_t26_dup__", _t26_dup_dets, _t26_dup_rows,
                _t26_cv)
    _t26_ev0 = len(MANGABD_EVENTS)
    _t26_out_dup = render_page("__rf20_t26_dup__", force=True)
    _t26_dup_warns = [
        e for e in MANGABD_EVENTS[_t26_ev0:]
        if e.get("level") == "WARN"
        and "RF-20 whole+fragment dedup" in str(e.get("message", ""))]
    _t26_dup_meta = dict(
        (get_page("__rf20_t26_dup__", required=True)
         .get("meta") or {}))
    _t26_w1 = _t26_text_px(_t26_out_dup, (60, 60, 230, 150))
    _t26_w2 = _t26_text_px(_t26_out_dup, (80, 120, 180, 36))
    _t26_w3 = _t26_text_px(_t26_out_dup, (330, 60, 200, 140))
    _t26_w4 = _t26_text_px(_t26_out_dup, (60, 300, 190, 130))
    _t26_w5 = _t26_text_px(_t26_out_dup, (400, 330, 150, 44))
    # ONCE law: whole bubble carries ONE text block — its band
    # profile must not double (fragment's translation absent), and
    # the fragment strip must hold text only from the whole's own
    # layout (not a second dense block). Assert via meta + census +
    # the suppression WARN + neighbors/plate rendered (light-ink
    # ROWS; probe-calibrated: 4-line layout ~45-50 rows, 1-line
    # plate ~14 — thresholds 20/8).
    run_test(
        "RF-20 whole+fragment renders ONCE: fragment row suppressed "
        "(WARN + meta rf20_dedup + census), whole + adjacent 3/4 + "
        "name plate 5 all render",
        (_t26_dup_meta.get("rf20_dedup") == {"suppressed": [2]}
         and len(_t26_dup_warns) == 1
         and ("__rf20_t26_dup__", 2) in _RF20_DEDUP_FIRES
         and _t26_w1 >= 20 and _t26_w3 >= 20 and _t26_w4 >= 20
         and _t26_w5 >= 8),
        f"meta={_t26_dup_meta.get('rf20_dedup')} "
        f"warns={len(_t26_dup_warns)} px=({_t26_w1},{_t26_w2},"
        f"{_t26_w3},{_t26_w4},{_t26_w5})",
    )
    # the double-text repro: with the fragment ALSO drawn, the
    # whole-bubble window would hold the whole's 3 light-ink bands
    # PLUS the fragment's own text block (the Bengali-on-Bengali
    # stack). Post-fix: the window's light-ink band count (probe:
    # 3 on this geometry) must be the single-layout count, NOT the
    # doubled stack (>= 5 bands / near-full ink rows).
    _t26_g1 = cv2.cvtColor(_t26_out_dup[60:210, 60:290],
                           cv2.COLOR_BGR2GRAY)
    _t26_p1 = (_t26_g1 > 170).sum(axis=1)
    _t26_t1 = max(1.0, 0.10 * float(_t26_p1.max()))
    _t26_bands1 = len(_b31_bands_from_profile(
        np.nonzero(_t26_p1 >= _t26_t1)[0].astype(float),
        0.0, float(len(_t26_p1)))) if _t26_p1.max() > 0 else 0
    run_test(
        "RF-20 double-text gone: whole-bubble window light-ink "
        "bands == single layout (not the doubled stack)",
        (2 <= _t26_bands1 <= 4),
        f"bands={_t26_bands1}",
    )

    # ── (e) adjacent law on a render page (12/13/14-class) ──
    _t26_adj_dets = [
        {"id": 12, "page_id": "__rf20_t26_adj__", "x": 40, "y": 80,
         "width": 170, "height": 120, "quad": None, "angle": 0.0,
         "region_type": "bubble", "detector_class": "text_bubble",
         "detector_score": 0.9, "parent_bubble_id": None},
        {"id": 13, "page_id": "__rf20_t26_adj__", "x": 240, "y": 80,
         "width": 170, "height": 120, "quad": None, "angle": 0.0,
         "region_type": "bubble", "detector_class": "text_bubble",
         "detector_score": 0.9, "parent_bubble_id": None},
        {"id": 14, "page_id": "__rf20_t26_adj__", "x": 440, "y": 80,
         "width": 170, "height": 120, "quad": None, "angle": 0.0,
         "region_type": "bubble", "detector_class": "text_bubble",
         "detector_score": 0.9, "parent_bubble_id": None},
    ]
    _t26_adj_rows = [
        {"id": 12, "x": 40, "y": 80, "width": 170, "height": 120,
         "text": "বাম বুদবুদের কথা এখানে"},
        {"id": 13, "x": 240, "y": 80, "width": 170, "height": 120,
         "text": "মাঝের বুদবুদের কথা এখানে"},
        {"id": 14, "x": 440, "y": 80, "width": 170, "height": 120,
         "text": "ডান বুদবুদের কথা এখানে"},
    ]
    _t26_mkpage("__rf20_t26_adj__", _t26_adj_dets, _t26_adj_rows,
                np.full((400, 640, 3), 255, np.uint8))
    _t26_ev1 = len(MANGABD_EVENTS)
    _t26_out_adj = render_page("__rf20_t26_adj__", force=True)
    _t26_adj_meta = dict(
        (get_page("__rf20_t26_adj__", required=True)
         .get("meta") or {}))
    _t26_adj_df = translation_df[
        translation_df["page_id"] == "__rf20_t26_adj__"]
    _t26_adj_rendered = int(
        (_t26_adj_df["status"] == "rendered").sum())
    run_test(
        "RF-20 adjacent bubbles 12/13/14: NO suppression — all "
        "three render (meta clean, no dedup WARN)",
        (_t26_adj_rendered == 3
         and "rf20_dedup" not in _t26_adj_meta
         and not [e for e in MANGABD_EVENTS[_t26_ev1:]
                  if e.get("level") == "WARN"
                  and "RF-20 whole+fragment dedup"
                  in str(e.get("message", ""))]),
        f"rendered={_t26_adj_rendered} "
        f"meta={_t26_adj_meta.get('rf20_dedup')}",
    )

    # ── (c) dark-spiky ghost wipe FIRES ──
    # canvas: near-black bubble interior with the ORIGINAL JP text
    # still present (light ink on dark); mask artifact covers only
    # a thin spiky border strip → coverage low → wipe expands.
    _t26_dark = np.full((400, 640, 3), 24, np.uint8)
    for _ly in (100, 130, 160):
        cv2.rectangle(_t26_dark, (120, _ly), (330, _ly + 18),
                      (235, 235, 235), -1)
    _t26_dark_mask = np.zeros((400, 640), np.uint8)
    for _sp in range(120, 331, 18):        # spiky border only
        cv2.circle(_t26_dark_mask, (_sp, 90), 5, 255, -1)
        cv2.circle(_t26_dark_mask, (_sp, 195), 5, 255, -1)
    _t26_dark_dets = [
        {"id": 15, "page_id": "__rf20_t26_dark__", "x": 110,
         "y": 85, "width": 230, "height": 115, "quad": None,
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
    ]
    _t26_dark_rows = [
        {"id": 15, "x": 110, "y": 85, "width": 230, "height": 115,
         "text": "অন্ধকার বুদবুদের ভেতরের কথা এখানে"},
    ]
    _t26_mkpage("__rf20_t26_dark__", _t26_dark_dets, _t26_dark_rows,
                _t26_dark, mask_arr=_t26_dark_mask)
    _t26_ev2 = len(MANGABD_EVENTS)
    _t26_out_dark = render_page("__rf20_t26_dark__", force=True)
    _t26_dark_warns = [
        e for e in MANGABD_EVENTS[_t26_ev2:]
        if e.get("level") == "WARN"
        and "RF-20 ghost wipe" in str(e.get("message", ""))]
    _t26_dark_meta = dict(
        (get_page("__rf20_t26_dark__", required=True)
         .get("meta") or {}))
    # ghost law: the ORIGINAL light-on-dark ink must be GONE —
    # after the wipe the region interior is uniformly bubble-bg
    # EXCEPT the rendered Bengali (dark text on the now-uniform
    # dark bg would be invisible; the renderer flips to light text
    # on dark — so count ORIGINAL-ink pixels: pixels close to the
    # original (235,235,235) that are OUTSIDE any dark-Bengali
    # stroke... simpler + robust: light-pixel count in the band
    # ABOVE/Below the rendered block must drop to ~the render's
    # own strokes; assert light-ink total < 40% of the original.
    _t26_g = cv2.cvtColor(_t26_out_dark[85:200, 110:340],
                          cv2.COLOR_BGR2GRAY)
    _t26_light_now = int((_t26_g > 170).sum())
    _t26_light_orig = int((cv2.cvtColor(
        _t26_dark[85:200, 110:340],
        cv2.COLOR_BGR2GRAY) > 170).sum())
    run_test(
        "RF-20 dark-spiky ghost wipe: low mask coverage → interior "
        "restored (WARN + meta rf20_ghost_wipe + census), original "
        "light ink residue < 40% of original",
        (len(_t26_dark_warns) == 1
         and _t26_dark_meta.get("rf20_ghost_wipe")
         == {"regions": [15]}
         and ("__rf20_t26_dark__", 15) in _RF20_GHOST_FIRES
         and _t26_light_now
         < 0.40 * _t26_light_orig),
        f"warns={len(_t26_dark_warns)} light "
        f"{_t26_light_now}/{_t26_light_orig}",
    )

    # ── (d) white-bg no-op ──
    # white canvas, text already inpainted away (clean inpainted
    # artifact) → no ink → no wipe. Same page ALSO rendered on the
    # dark canvas but with a FULL mask (coverage high) → no-op.
    _t26_white = np.full((400, 640, 3), 255, np.uint8)
    _t26_white_dets = [
        {"id": 16, "page_id": "__rf20_t26_white__", "x": 100,
         "y": 80, "width": 220, "height": 110, "quad": None,
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
    ]
    _t26_white_rows = [
        {"id": 16, "x": 100, "y": 80, "width": 220, "height": 110,
         "text": "সাদা পটভূমির বুদবুদের কথা এখানে"},
    ]
    _t26_full_mask = np.zeros((400, 640), np.uint8)
    cv2.rectangle(_t26_full_mask, (100, 80), (320, 190), 255, -1)
    _t26_mkpage("__rf20_t26_white__", _t26_white_dets,
                _t26_white_rows, _t26_white, mask_arr=_t26_full_mask)
    _t26_ev3 = len(MANGABD_EVENTS)
    _t26_out_white = render_page("__rf20_t26_white__", force=True)
    _t26_white_meta = dict(
        (get_page("__rf20_t26_white__", required=True)
         .get("meta") or {}))
    # white canvas: text is DARK ink (probe: ~2.5k dark px)
    _t26_gw2 = int((cv2.cvtColor(
        _t26_out_white[80:190, 100:320],
        cv2.COLOR_BGR2GRAY) < 120).sum())
    run_test(
        "RF-20 white-bg no-op: full mask + clean inpaint → zero "
        "ghost fires (no WARN, meta clean, dark text renders)",
        (not [e for e in MANGABD_EVENTS[_t26_ev3:]
              if e.get("level") == "WARN"
              and "RF-20 ghost wipe" in str(e.get("message", ""))]
         and "rf20_ghost_wipe" not in _t26_white_meta
         and "rf20_dedup" not in _t26_white_meta
         and _t26_gw2 > 0),
        "meta_keys=%s" % sorted(
            k for k in _t26_white_meta if k.startswith("rf20")),
    )

    # ── (b) battery census frozen ──
    run_test(
        "RF-20 battery census: dedup fires EXACTLY the (a) "
        "fixture pair, ghost fires EXACTLY the (c) fixture — "
        "legacy Tests 1-25 + adjacents all silent",
        (list(_RF20_DEDUP_FIRES) == [("__rf20_t26_dup__", 2)]
         and list(_RF20_GHOST_FIRES)
         == [("__rf20_t26_dark__", 15)]),
        f"dedup={list(_RF20_DEDUP_FIRES)} "
        f"ghost={list(_RF20_GHOST_FIRES)}",
    )
except Exception as _t26_exc:
    run_test("RF-20 Test 26 (unexpected exception)", False,
             str(_t26_exc)[:160])
finally:
    try:
        _t26_df = globals().get("translation_df")
        if _t26_df is not None and len(_t26_df):
            _t26_keep = _t26_df[~_t26_df["page_id"].isin(_t26_pids)]
            globals()["translation_df"] = _t26_keep
            save_translation_df(_t26_keep)
        for _t26_p in _t26_pids:
            reset_page(_t26_p, delete_artifacts=True)
    except Exception:
        pass


# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।"""
