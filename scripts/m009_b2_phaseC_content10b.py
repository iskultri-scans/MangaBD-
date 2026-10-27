#!/usr/bin/env python3
r"""MANGABD-009 B2 Phase C — cell-10 battery content (Tests 16-18).

Inserted immediately before the RF-13 fixture-hygiene block (after
B1's Tests 13-15). All three tests are self-contained (synthetic
crops only — no archive/model dependency, B1 battery discipline):

  Test 16  estimator semantics: PIL-rotate(beta) round-trip (V2 sign
           law), RB2-1 dev-from-nearest-cardinal (70° strip → −20°
           lean, NOT −70°), RB2-2 5° snap, truly-vertical band on a
           NON-V-3 block (88°), V-3 predicate, aniso gate (disc),
           RB2-4 quad extents ≈ the strip's true dims + corner bounds.
  Test 17  RB2-5 fit dims: same tight strip, bbox-dims fit vs
           quad-dims fit → less ink (no 2.08× oversize) + paste
           centering; RB2-7 mirror: ON passthrough / OFF zeroing /
           ABSENT default-ON — sentinel-restore discipline (Test 14).
  Test 18  end-to-end inheritance: estimator → (angle, quad) →
           render → নতুন Bengali কালির আবার PCA ≈ একই lean
           (estimator round-trip on the RENDERED output)।
"""

C10_BATT_OLD = '''# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।
'''

C10_BATT_NEW = '''# ── MANGABD-009 B2: orientation inheritance self-tests ──
# Phase A (5fe8804) + ruling RB2-1..RB2-7: dev-from-nearest-cardinal,
# 5° snap, pixel-PCA source, PCA-quad recompute, quad-extents fit dims,
# skip-emphasis (RB2-6 — bold/stroke region_type-driven, untouched),
# kill-switch b2_orientation_enable। Corpus honesty: archived 0/36 row
# non-zero হওয়ায় আসল validation = এই synthetic fixture-গুলোই।

# Test 16: B2 estimator — synthetic tilt semantics + gates।
try:
    _b2t_font = get_font(28, bold=False)
    _b2t_line = "বাংলা টেস্ট লাইন বাংলা টেস্ট লাইন"
    try:
        while (_b2t_font.getbbox(_b2t_line)[2]
               - _b2t_font.getbbox(_b2t_line)[0]) < 320:
            _b2t_line += " বাংলা টেস্ট"
    except Exception:
        _b2t_line = "TEST LINE 123 TEST LINE 123 TEST LINE 123"
        try:
            while (_b2t_font.getbbox(_b2t_line)[2]
                   - _b2t_font.getbbox(_b2t_line)[0]) < 320:
                _b2t_line += " TEST 123"
        except Exception:
            pass

    def _b2t_page(beta, lines=1):
        # beta ঘোরানো এক/তিন-লাইনের কালির strip-block — ink bbox-ই
        # region (detector-এর মতোই টাইট box)।
        _c = PILImage.new("L", (780, 42 * max(1, lines) + 80), 255)
        _d = ImageDraw.Draw(_c)
        for _li in range(max(1, lines)):
            _d.text((12, 16 + _li * 42), _b2t_line,
                    font=_b2t_font, fill=0)
        _g0 = np.asarray(_c)
        _uy, _ux = np.nonzero(_g0 < 128)
        _uw = int(_ux.max() - _ux.min()) + 1
        _uh = int(_uy.max() - _uy.min()) + 1
        # fillcolor=255: PIL rotate(expand=True)-এর ডিফল্ট fill কালো —
        # সাদা canvas-এ corner-ত্রিভুজগুলো সে-ই হয়ে যেত, PCA তখন কালি
        # নয় ওই diagonal-ই মাপত (Phase A instrument-এর V2 কালো canvas
        # দিয়ে এড়িয়েছিল; এখানে সাদা + স্পষ্ট fill)।
        _r = _c.rotate(beta, expand=True, resample=PILImage.BICUBIC,
                       fillcolor=255)
        _pg = np.full((_r.height + 40, _r.width + 40, 3), 255, np.uint8)
        _pg[20:20 + _r.height, 20:20 + _r.width] = cv2.cvtColor(
            np.asarray(_r), cv2.COLOR_GRAY2BGR)
        _g = cv2.cvtColor(_pg, cv2.COLOR_BGR2GRAY)
        _ys, _xs = np.nonzero(_g < 128)
        return _pg, (int(_xs.min()), int(_ys.min()),
                     int(_xs.max() - _xs.min()) + 1,
                     int(_ys.max() - _ys.min()) + 1), (_uw, _uh)

    _b2t_cases = []

    def _b2t_chk(label, ok, detail):
        _b2t_cases.append((label, bool(ok), detail))

    # 1: round-trip sign law + RB2-4 quad extents ≈ strip-এর সত্যি dims
    _pg1, _bx1, _dim1 = _b2t_page(-20.0)
    _a1, _q1 = _estimate_region_angle(_pg1, *_bx1)
    _ok1 = abs(_a1 + 20.0) <= 1.5 and _q1 is not None
    if _ok1:
        _qa = np.asarray(_q1, dtype=np.float64)
        _fw = float(max(np.linalg.norm(_qa[0] - _qa[1]),
                        np.linalg.norm(_qa[2] - _qa[3])))
        _fh = float(max(np.linalg.norm(_qa[0] - _qa[3]),
                        np.linalg.norm(_qa[1] - _qa[2])))
        _ok1 = (
            abs(_fw - _dim1[0]) <= 8
            and abs(_fh - _dim1[1]) <= 8
            and _qa[:, 0].min() >= _bx1[0] - 8
            and _qa[:, 0].max() <= _bx1[0] + _bx1[2] + 8
            and _qa[:, 1].min() >= _bx1[1] - 8
            and _qa[:, 1].max() <= _bx1[1] + _bx1[3] + 8
        )
        _dt1 = f"pil={_a1} fw={_fw:.0f}/uw={_dim1[0]} fh={_fh:.0f}/uh={_dim1[1]}"
    else:
        _dt1 = f"pil={_a1} quad={'Y' if _q1 else 'N'}"
    _b2t_chk("beta-20 roundtrip+quad", _ok1, _dt1)

    # 2: +15 পর্যন্ত একই law
    _pg, _bx, _ = _b2t_page(15.0)
    _a, _q = _estimate_region_angle(_pg, *_bx)
    _b2t_chk("beta+15 roundtrip", abs(_a - 15.0) <= 1.5 and _q is not None,
             f"pil={_a}")

    # 3: RB2-2 snap — 3° কাঁচা tilt থাকলেও 0.0
    _pg, _bx, _ = _b2t_page(3.0)
    _a, _q = _estimate_region_angle(_pg, *_bx)
    _b2t_chk("beta+3 snap->0", _a == 0.0 and _q is None, f"pil={_a}")

    # 4: RB2-1 dev-semantic — 70° strip কখনোই কাঁচা 70° পায় না, পায়
    #    nearest-cardinal deviation −20° (Option A; vertical safety)
    _pg, _bx, _ = _b2t_page(70.0)
    _a, _q = _estimate_region_angle(_pg, *_bx)
    _b2t_chk("beta+70 dev->-20", abs(_a + 20.0) <= 1.5 and _q is not None,
             f"pil={_a} (raw হলে -70 হত)")

    # 5: truly-vertical band — non-V-3 3-line block at 88°
    _pg, _bx, _ = _b2t_page(88.0, lines=3)
    _a, _q = _estimate_region_angle(_pg, *_bx)
    _b2t_chk("beta+88 vertical-band->0 (w=" + str(_bx[2]) + ")",
             _a == 0.0 and _q is None, f"pil={_a}")

    # 6: V-3 predicate — gate pixel-দেখার আগেই; w<90, h>2w
    _pg, _bx, _ = _b2t_page(-20.0)
    _a, _q = _estimate_region_angle(_pg, 10, 10, 60, 160)
    _b2t_chk("V-3 shape->0", _a == 0.0 and _q is None, f"pil={_a}")

    # 7: aniso gate — প্রায়-isotropic disc cloud unstable → 0
    _pg7 = np.full((260, 260, 3), 255, np.uint8)
    cv2.circle(_pg7, (130, 130), 55, (0, 0, 0), -1)
    _a, _q = _estimate_region_angle(_pg7, 70, 70, 120, 120)
    _b2t_chk("isotropic disc->0", _a == 0.0 and _q is None, f"pil={_a}")

    _b2t_ok = all(ok for _, ok, _ in _b2t_cases)
    _b2t_detail = "; ".join(
        f"{lb}:{'OK' if ok else 'BAD(' + dt + ')'}"
        for lb, ok, dt in _b2t_cases)
    run_test("B2 estimator: synthetic tilt semantics (RB2-1/2/3/4 + gates)",
             _b2t_ok, _b2t_detail)
except Exception as exc:
    run_test("B2 estimator: synthetic tilt semantics (RB2-1/2/3/4 + gates)",
             False, str(exc)[:160])


# Test 17: B2 render side — RB2-5 quad-extents fit dims + RB2-7
# render-side kill-switch mirror।
try:
    _b2s_txt = "এই কী হয়েছে বলো তো!"
    _b2s_base = PILImage.new("RGB", (700, 520), (255, 255, 255))

    # (a) একই 200x60@20° strip-ক্লাস region (Phase A V5 মিটার):
    #     bbox-dims fit (208x125) বনাম quad-dims fit (180x40) —
    #     quad-dims-এর ফন্ট ছোট, কালি কম।
    _b2s_a = render_bengali_text(
        _b2s_base.copy(), _b2s_txt, 240, 200, 208, 125,
        angle=-20.0, region_type="bubble", text_color=(0, 0, 0),
        stroke_width=0)
    _b2s_b = render_bengali_text(
        _b2s_base.copy(), _b2s_txt, 240, 200, 208, 125,
        angle=-20.0, region_type="bubble", text_color=(0, 0, 0),
        stroke_width=0, fit_w=180, fit_h=40)
    _b2s_ia = int((np.asarray(_b2s_a).sum(axis=2) < 300).sum())
    _b2s_ib = int((np.asarray(_b2s_b).sum(axis=2) < 300).sum())
    _okA = _b2s_ia > 0 and _b2s_ib > 0 and _b2s_ib < _b2s_ia

    # (b) paste centering — quad-dims render-এর কালির centroid ≈
    #     region bbox center (x+w//2, y+h//2)
    _b2s_mask = np.asarray(_b2s_b.convert("L")) < 200
    _b2s_ys, _b2s_xs = np.nonzero(_b2s_mask)
    _okB = (abs(float(_b2s_xs.mean()) - (240 + 104)) <= 30
            and abs(float(_b2s_ys.mean()) - (200 + 62)) <= 30)

    # (c) kill-switch mirror: ON passthrough / OFF zeroing / ABSENT
    #     default-ON — sentinel-restore discipline (Test 14 pattern)।
    _b2s_parent_absent = "detection" not in MANGABD_CONFIG
    _b2s_prev = (MANGABD_CONFIG.get("detection") or {}).get(
        "b2_orientation_enable", "ABSENT")
    try:
        MANGABD_CONFIG.setdefault("detection", {})
        MANGABD_CONFIG["detection"]["b2_orientation_enable"] = False
        _off = (_b2_render_angle(-20.0) == 0.0
                and _b2_render_angle(20.0) == 0.0
                and _b2_render_angle(1.0) == 1.0)
        MANGABD_CONFIG["detection"]["b2_orientation_enable"] = True
        _on = (_b2_render_angle(-20.0) == -20.0
               and _b2_render_angle(20.0) == 20.0
               and _b2_render_angle(1.0) == 1.0
               and _b2_render_angle(0.0) == 0.0)
        del MANGABD_CONFIG["detection"]["b2_orientation_enable"]
        _absent = _b2_render_angle(-20.0) == -20.0
    finally:
        if _b2s_prev == "ABSENT":
            MANGABD_CONFIG.get("detection", {}).pop(
                "b2_orientation_enable", None)
        else:
            MANGABD_CONFIG.setdefault("detection", {})[
                "b2_orientation_enable"] = _b2s_prev
        if _b2s_parent_absent:
            MANGABD_CONFIG.pop("detection", None)

    run_test(
        "B2 render: quad-extents fit + kill-switch mirror",
        _okA and _okB and _off and _on and _absent,
        f"ink bbox-fit={_b2s_ia} quad-fit={_b2s_ib}; "
        f"centroid=({float(_b2s_xs.mean()):.0f},"
        f"{float(_b2s_ys.mean()):.0f}); "
        f"mirror on/off/absent={'Y' if _on else 'N'}/"
        f"{'Y' if _off else 'N'}/{'Y' if _absent else 'N'}",
    )
except Exception as exc:
    run_test("B2 render: quad-extents fit + kill-switch mirror",
             False, str(exc)[:160])


# Test 18: B2 end-to-end — estimator → (angle, quad) → render →
# নতুন Bengali কালি একই lean বহন করে (rendered output-এর উপর আবার
# estimator — পুরো চেইনের round-trip প্রমাণ)।
try:
    _b2e_font = get_font(28, bold=False)
    _b2e_line = "বাংলা টেস্ট লাইন বাংলা টেস্ট লাইন"
    try:
        while (_b2e_font.getbbox(_b2e_line)[2]
               - _b2e_font.getbbox(_b2e_line)[0]) < 320:
            _b2e_line += " বাংলা টেস্ট"
    except Exception:
        _b2e_line = "TEST LINE 123 TEST LINE 123 TEST LINE 123"

    def _b2e_page(beta):
        _c = PILImage.new("L", (780, 130), 255)
        ImageDraw.Draw(_c).text((12, 40), _b2e_line,
                                font=_b2e_font, fill=0)
        # fillcolor=255 — corner-ত্রিভুজ কালো হলে PCA সে-ই মাপত (V2 নোট)
        _r = _c.rotate(beta, expand=True, resample=PILImage.BICUBIC,
                       fillcolor=255)
        _pg = np.full((_r.height + 40, _r.width + 40, 3), 255, np.uint8)
        _pg[20:20 + _r.height, 20:20 + _r.width] = cv2.cvtColor(
            np.asarray(_r), cv2.COLOR_GRAY2BGR)
        _g = cv2.cvtColor(_pg, cv2.COLOR_BGR2GRAY)
        _ys, _xs = np.nonzero(_g < 128)
        return _pg, (int(_xs.min()), int(_ys.min()),
                     int(_xs.max() - _xs.min()) + 1,
                     int(_ys.max() - _ys.min()) + 1)

    _b2e_pg, _b2e_bx = _b2e_page(-25.0)
    _b2e_ang, _b2e_quad = _estimate_region_angle(_b2e_pg, *_b2e_bx)
    _b2e_ok0 = abs(_b2e_ang + 25.0) <= 1.5 and _b2e_quad is not None

    # render_page-এর হুবহু extents সূত্র (cell-06 L944-952 convention)
    _b2e_q = np.asarray(_b2e_quad, dtype=np.float64)
    _b2e_fw = int(round(max(
        float(np.linalg.norm(_b2e_q[0] - _b2e_q[1])),
        float(np.linalg.norm(_b2e_q[2] - _b2e_q[3])),
    )))
    _b2e_fh = int(round(max(
        float(np.linalg.norm(_b2e_q[0] - _b2e_q[3])),
        float(np.linalg.norm(_b2e_q[1] - _b2e_q[2])),
    )))

    _b2e_src = PILImage.fromarray(cv2.cvtColor(_b2e_pg, cv2.COLOR_BGR2RGB))
    _b2e_out = render_bengali_text(
        _b2e_src.copy(), "এই কী হয়েছে বলো তো?!", _b2e_bx[0], _b2e_bx[1],
        _b2e_bx[2], _b2e_bx[3], angle=_b2e_ang,
        region_type="bubble", text_color=(0, 0, 0), stroke_width=0,
        fit_w=_b2e_fw, fit_h=_b2e_fh)

    _b2e_new = ((np.asarray(_b2e_out.convert("L")) < 128)
                & (np.asarray(_b2e_src.convert("L")) >= 128))
    _b2e_n = int(_b2e_new.sum())

    # নতুন Bengali কালির আবার PCA — একই lean (±2.5°)
    _b2e_diff = np.full(_b2e_pg.shape, 255, np.uint8)
    _b2e_diff[_b2e_new] = 0
    _b2e_ys, _b2e_xs = np.nonzero(_b2e_new)
    _b2e_rbox = (int(_b2e_xs.min()) - 6, int(_b2e_ys.min()) - 6,
                 int(_b2e_xs.max() - _b2e_xs.min()) + 12,
                 int(_b2e_ys.max() - _b2e_ys.min()) + 12)
    _b2e_rt, _ = _estimate_region_angle(_b2e_diff, *_b2e_rbox)

    run_test(
        "B2 end-to-end: estimator -> render inherits the lean",
        _b2e_ok0 and _b2e_n > 200 and abs(_b2e_rt + 25.0) <= 2.5,
        f"angle={_b2e_ang} quad-fit={_b2e_fw}x{_b2e_fh} "
        f"newink={_b2e_n} lean-roundtrip={_b2e_rt}",
    )
except Exception as exc:
    run_test("B2 end-to-end: estimator -> render inherits the lean",
             False, str(exc)[:160])


# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।
'''
