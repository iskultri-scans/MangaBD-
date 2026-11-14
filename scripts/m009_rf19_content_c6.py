#!/usr/bin/env python3
"""MANGABD-009 RF-19 — cell-6 patch content (band-consistency gate).

Owner fast-round ruling (id=4: angle=7.97 on STRAIGHT text, area
31313px): RF-18 minAreaRect law misfires when per-word emphasis ink
makes the cloud asymmetric. FIX: band-consistency gate — row-profile
bands horizontal (every measurable band |tilt| <= 2 deg, >= 2 bands)
while minAreaRect says > 5 deg (structural: this point is only
reached past the |tilt| >= 5 / dev >= 5 returns) -> reject the tilt,
store 0.0 as a MEASURED horizontal verdict (same form as the law's
own horizontal returns — no quad, no GT).

Gate selectivity (design-time measured, scripts/m009_rf19_design.py):
  separate bands measure the TRUE tilt accurately (7 deg -> 6.86,
  6 deg -> 5.87, 12 deg -> 11.83) -> silent; merged bands (true tilt
  smears the row profile) drop n_bands to 1 -> the >= 2-band
  requirement keeps the gate SILENT. A genuine tilt can therefore
  only be falsely rejected if >= 2 crisp bands EACH regress <= 2 deg
  while the rect tilt is >= 5 deg — not constructible on straight
  bars at any tilt (measured 6/7/12 deg) and not present in the
  committed corpus (angle census: S009 +7.97 is a genuine 137k-px
  diagonal bubble, S011 +5.86 likewise; archives never re-detect).
"""
import textwrap

# ── P1: the gate helper, before _b2_mask_orientation ────────────────
C6_P1_OLD = """\
        return None, warns                  # all-achromatic → no key
    return cols, warns


def _b2_mask_orientation(ink_mask, x, y, w, h):\
"""

C6_P1_NEW = """\
        return None, warns                  # all-achromatic → no key
    return cols, warns


# MANGABD-009 RF-19 (Owner fast round — live id=4: angle=7.97 on
# STRAIGHT text): band-consistency gate-এর মাপক। row-profile bands
# (এই window-এর হুবহু _b31_bands_from_profile law) প্রতিটার
# regression tilt — bands সব সমানে horizontal কি না, সেটাই এর রায়।
_RF19_BAND_TILT_MAX = 2.0


def _rf19_band_tilt_max(m):
    \"\"\"RF-19: window ink-এর row-profile bands-এর per-band regression
    tilt-এর max |deg|। Returns (worst, n_bands): worst=None হলে কোনো
    band-ই measurable নয়। n_bands >= 2 = crisp multi-line horizontal
    structure; true tilt row-profile কে smear করে merge করে ফেলে
    (n_bands 1-এ নামে) — সেই ক্ষেত্রে gate অবশ্যই silent থাকবে।
    আলাদা (unmerged) band নিজের সত্যি tilt-ই মাপে (design-time:
    7°→6.86, 6°→5.87, 12°→11.83), তাই genuine tilt কখনো <= 2° পড়ে
    না। band খুব ছোট (<30 px বা x-span < 24px) হলে measurable নয়।\"\"\"
    try:
        H, W = m.shape[:2]
        if W < 24 or H < 8:
            return None, 0
        ys, xs = np.nonzero(m)
        if len(ys) < 30:
            return None, 0
        bands = _b31_bands_from_profile(
            ys.astype(np.float64),
            float(ys.min()), float(ys.max()))
        if not bands:
            return None, 0
        worst = None
        for _v0, _v1 in bands:
            _sel = ((ys >= int(np.floor(_v0)))
                    & (ys < int(np.ceil(_v1))))
            _bx = xs[_sel].astype(np.float64)
            _by = ys[_sel].astype(np.float64)
            if len(_bx) < 30:
                continue
            if float(_bx.max() - _bx.min()) < 24.0:
                continue
            _vx = _bx - _bx.mean()
            _vy = _by - _by.mean()
            _sxx = float((_vx * _vx).sum())
            if _sxx <= 1e-9:
                continue
            _t = float(np.degrees(np.arctan(
                float((_vx * _vy).sum()) / _sxx)))
            if worst is None or abs(_t) > worst:
                worst = abs(_t)
        return worst, len(bands)
    except Exception:
        return None, 0


def _b2_mask_orientation(ink_mask, x, y, w, h):\
"""

# ── P2: the gate call, right after the tilted verdict is formed ────
C6_P2_OLD = """\
    pil_angle = round(-dev, 2)

    # RB2-4 convention-এ quad: canonicalized u (reading dir) + v-তে\
"""

C6_P2_NEW = """\
    pil_angle = round(-dev, 2)

    # MANGABD-009 RF-19 (Owner fast round, id=4): band-consistency
    # gate। এই পর্যন্ত পৌঁছেছি মানে minAreaRect নিজে |tilt| >= 5° +
    # dev >= 5° বলেছে। per-word emphasis ink-এর asymmetric cloud-এ
    # সেটা খালি হতে পারে (live id=4: straight text-এ 7.97°)।
    # row-profile bands সব horizontal (>= 2 crisp band, সব
    # measurable band-এর |tilt| <= 2°) হলে tilted verdict REJECT —
    # measured horizontal 0.0 store হয় (নিজের horizontal return-এর
    # হুবহু ফর্ম: quad/GT নেই)। bands measurable না হলে বা merge
    # করে থাকলে silent — আসল tilted region (R6-class 12°) অপরিবর্তিত।
    _rf19_worst, _rf19_nbands = _rf19_band_tilt_max(m)
    if (_rf19_worst is not None and _rf19_nbands >= 2
            and _rf19_worst <= _RF19_BAND_TILT_MAX):
        return 0.0, None, None, True

    # RB2-4 convention-এ quad: canonicalized u (reading dir) + v-তে\
"""

assert C6_P1_OLD != C6_P1_NEW and C6_P2_OLD != C6_P2_NEW
