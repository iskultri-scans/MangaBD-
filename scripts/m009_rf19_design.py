#!/usr/bin/env python3
"""MANGABD-009 RF-19 — design-time preflight (repo instrument).

Owner fast-round ruling (id=4: angle=7.97 on straight text, area
31313px, single-tiny-line render). Two code fixes, both measured here
BEFORE the patch content is frozen:

  FIX 1  band-consistency gate (cell 6, inside _b2_mask_orientation):
         row-profile bands horizontal (per-band regression |tilt| <=
         2 deg) while minAreaRect says > 5 deg  ->  reject tilt, store
         0.0 (measured horizontal verdict). Genuine tilt (R6-class
         12 deg) must stay MEASURED-TILTED (gate silent).

  FIX 2  production tiny-guard (cell 10, render_page): rendered lines
         == 1 AND horizontal-bbox fit >= 2 lines AND area >= 2000px
         ->  re-layout via horizontal bbox path (no GT mirror) + WARN.
         The guard can structurally fire only via the b2gt/mask/quad
         paths (the plain-fit path renders exactly what the bbox fit
         computes); the T25c fixture must demonstrably collapse
         through the b2gt mirror.

Runs against the CURRENT (36faa98) cells — no patches applied yet.
"""
import contextlib
import io
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
sys.path.insert(0, str(REPO / "scripts"))

import cv2  # noqa: E402
import numpy as np  # noqa: E402

from m009_b2_rf14_repro import (  # noqa: E402
    install_pathlib_shim, make_torch_stub, restore_pathlib,
)

WORK = Path("/home/z/my-project/cells_b31_fix")   # 36faa98 pin
PREFIX = [1, 2, 3, 4, 5, 6, 7]

ns6 = {"__name__": "__mangabd__"}
from m009_b2_rf15_repro import seed_cell00_side_effects  # noqa: E402
seed_cell00_side_effects(ns6)
sys.modules["torch"] = make_torch_stub()
install_pathlib_shim()
try:
    for cid in PREFIX:
        src = (WORK / f"cell_{cid:02d}.py").read_text(encoding="utf-8")
        buf = io.StringIO()
        print(f"[preflight] exec cell_{cid:02d} ({len(src)} bytes)")
        try:
            with contextlib.redirect_stdout(buf):
                exec(compile(src, f"cell_{cid:02d}.py", "exec"), ns6)
        except RuntimeError as exc:
            if cid == 4 and "Cell 4 self-tests failed" in str(exc):
                print(f"[preflight] cell_04 torch-stub tolerance "
                      f"(RF-14 law): {str(exc)[:80]}")
            else:
                raise
        bad = [ln for ln in buf.getvalue().splitlines() if "❌" in ln]
        if bad:
            print(f"[preflight] cell_{cid:02d} FAIL lines:")
            for ln in bad[:5]:
                print("   ", ln[:140])
finally:
    restore_pathlib()
print("[preflight] cells 1-7 exec OK (cell-6 laws live)\n")

# ════════════════════════════════════════════════════════════════════
# FIX 1 — the gate prototype (EXACTLY the cell-6 patch text)
# ════════════════════════════════════════════════════════════════════
GATE_SRC = '''
_RF19_BAND_TILT_MAX = 2.0


def _rf19_band_tilt_max(m):
    """Returns (worst |tilt| deg or None, n_bands total)। bands >= 2 =
    crisp multi-line horizontal structure; merged single band (true
    tilt smears the row profile) -> gate must stay SILENT."""
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
        _xr = float(_bx.max() - _bx.min())
        if _xr < 24.0:
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


def _rf19_gate_fires(m):
    worst, n_bands = _rf19_band_tilt_max(m)
    return (worst is not None and n_bands >= 2
            and worst <= _RF19_BAND_TILT_MAX)
'''
exec(compile(GATE_SRC, "<gate prototype>", "exec"), ns6)


def rect_tilt(pts):
    """minAreaRect long-side tilt, the law's own mod-180 framing."""
    box = cv2.boxPoints(cv2.minAreaRect(pts.astype(np.float32)))
    d01, d03 = box[1] - box[0], box[3] - box[0]
    dlong = d01 if (np.linalg.norm(d01) >= np.linalg.norm(d03)) else d03
    t = float(np.degrees(np.arctan2(dlong[1], dlong[0])))
    tilt = (t + 180.0) % 180.0
    if tilt > 90.0:
        tilt -= 180.0
    return tilt


def window(mask, x, y, w, h):
    H, W = mask.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    return mask[y1:y2, x1:x2] > 0


def law_verdict(mask, x, y, w, h):
    a, q, g, meas = ns6["_b2_mask_orientation"](mask, x, y, w, h)
    return {
        "angle": a, "quad": q is not None, "measured": meas,
        "gt": (None if g is None else
               {k: g[k] for k in ("lines", "spacing", "wu", "hv")}),
    }


print("── FIX 1 geometry candidates ──")
PAGE = np.full((560, 640, 3), 255, np.uint8)
RAWM = np.zeros((560, 640), np.uint8)


def bars(spec, deg=0.0, cx=None, cy=None):
    """spec = [(x0, x1, y0, y1), ...] drawn onto PAGE/RAWM (+rot)."""
    page = PAGE.copy()
    raw = np.zeros_like(RAWM)
    for (x0, x1, y0, y1) in spec:
        cv2.rectangle(page, (x0, y0), (x1, y1), (10, 10, 10), -1)
        cv2.rectangle(raw, (x0, y0), (x1, y1), 255, -1)
    if abs(deg) > 0:
        pts = np.array([[p[0], p[1]] for p in
                        [(s[0], s[1]) for s in spec]])
        xs_all = [v for s in spec for v in (s[0], s[1])]
        ys_all = [v for s in spec for v in (s[2], s[3])]
        cx = cx if cx is not None else float(np.mean(xs_all))
        cy = cy if cy is not None else float(np.mean(ys_all))
        M = cv2.getRotationMatrix2D((cx, cy), deg, 1.0)
        page = cv2.warpAffine(page, M, (640, 560),
                              flags=cv2.INTER_NEAREST,
                              borderValue=(255, 255, 255))
        raw = cv2.warpAffine(raw, M, (640, 560),
                             flags=cv2.INTER_NEAREST,
                             borderValue=0)
    ys, xs = np.nonzero(raw > 0)
    return page, raw, (int(xs.min()), int(ys.min()),
                       int(xs.max() - xs.min()) + 1,
                       int(ys.max() - ys.min()) + 1)


CANDIDATES = {
    # diagonal center-shift stacks — the asymmetric emphasis cloud
    "A4 diag3": [(90, 250, 60, 86), (110, 270, 116, 142),
                 (130, 290, 172, 198)],
    "A5 diag4": [(70, 230, 50, 76), (90, 250, 105, 131),
                 (110, 270, 160, 186), (130, 290, 215, 241)],
    "A6 emph-mix": [(80, 260, 60, 86), (100, 360, 116, 142),
                    (120, 300, 172, 198), (140, 280, 228, 254)],
    "A7 diag3-mild": [(90, 250, 60, 86), (105, 265, 116, 142),
                      (120, 280, 172, 198)],
}

results = {}
for name, spec in CANDIDATES.items():
    page, raw, (x, y, w, h) = bars(spec)
    m = window(raw, x, y, w, h)
    ys, xs = np.nonzero(m)
    pts = np.stack([xs.astype(np.float64), ys.astype(np.float64)], 1)
    rt = rect_tilt(pts)
    bt, nb = ns6["_rf19_band_tilt_max"](m)
    fires = ns6["_rf19_gate_fires"](m)
    v = law_verdict(raw, x, y, w, h)
    results[name] = (rt, bt, fires, v)
    print(f"  {name:16s} box=({x},{y},{w},{h}) area={w*h} "
          f"rect_tilt={rt:+.2f}° band_tilt={bt} n_bands={nb} "
          f"GATE={fires} "
          f"law={v['angle']:+.2f} measured={v['measured']} "
          f"quad={v['quad']} gt={v['gt']}")

print("\n  genuine-tilt contrast (must stay MEASURED-TILTED):")
GENUINE = {
    "B1 12deg-3bars-200": ([(60, 260, 60, 84), (60, 260, 120, 144),
                            (60, 260, 180, 204)], 12.0),
    "B2 12deg-3bars-240": ([(60, 300, 60, 84), (60, 300, 120, 144),
                            (60, 300, 180, 204)], 12.0),
    "B3 7deg-3bars-240": ([(60, 300, 60, 84), (60, 300, 120, 144),
                           (60, 300, 180, 204)], 7.0),
    "B4 6deg-3bars-240": ([(60, 300, 60, 84), (60, 300, 120, 144),
                           (60, 300, 180, 204)], 6.0),
    "B5 12deg-widepitch": ([(60, 300, 40, 64), (60, 300, 130, 154),
                            (60, 300, 220, 244)], 12.0),
}
for name, (spec, deg) in GENUINE.items():
    page, raw, (x, y, w, h) = bars(spec, deg=deg)
    m = window(raw, x, y, w, h)
    ys, xs = np.nonzero(m)
    pts = np.stack([xs.astype(np.float64), ys.astype(np.float64)], 1)
    rt = rect_tilt(pts)
    bt, nb = ns6["_rf19_band_tilt_max"](m)
    fires = ns6["_rf19_gate_fires"](m)
    v = law_verdict(raw, x, y, w, h)
    print(f"  {name:20s} box=({x},{y},{w},{h}) w>=80:{w >= 80} "
          f"rect_tilt={rt:+.2f}° band_tilt={bt} n_bands={nb} "
          f"GATE={fires} law={v['angle']:+.2f} "
          f"measured={v['measured']} gt={v['gt']}")

print("\n  symmetric horizontal (law must stay 0.0 measured):")
page, raw, (x, y, w, h) = bars([(60, 360, 60, 86), (60, 360, 116, 142),
                                (60, 360, 172, 198)])
m = window(raw, x, y, w, h)
bt, nb = ns6["_rf19_band_tilt_max"](m)
print(f"  C1 sym3           rect_tilt={rect_tilt(np.stack([np.nonzero(m)[1], np.nonzero(m)[0]], 1)):+.2f}° "
      f"band_tilt={bt} n_bands={nb} GATE={ns6['_rf19_gate_fires'](m)} "
      f"law={law_verdict(raw, x, y, w, h)}")

print("\n  committed-corpus angle census (five archives + S012):")
import json as _json
_arch = {
    "S003": REPO / "samples" / "S003_batch2",
    "S007": None, "S009": REPO / "samples" / "S009_diagonal",
    "S010": REPO / "samples" / "S010_burst",
    "S011": REPO / "samples" / "S011_manhwa_ui",
    "S012": REPO / "samples" / "S012_manhwa_emphasis",
}
import zipfile as _zf
for sid, p in _arch.items():
    if sid == "S007":
        with _zf.ZipFile(REPO / "S007_mangabd005_02.zip") as z:
            cand = [n for n in z.namelist()
                    if n.endswith("detections.json")][0]
            det = _json.loads(z.read(cand))
    else:
        det = _json.load(open(p / "detections.json"))
    angs = [float(d.get("angle") or 0.0) for d in det]
    risk = [a for a in angs if 1.0 < abs(a) <= 8.0]
    print(f"  {sid}: {len(angs)} regions, angles>1°: "
          f"{sorted(set(round(a, 2) for a in angs if abs(a) > 1.0))} "
          f"| risk-zone (1,8]: {risk}")

print("\n  V-3 vertical sanity (gate never reached):")
rawv = np.zeros_like(RAWM)
cv2.rectangle(rawv, (100, 60), (140, 280), 255, -1)
v = law_verdict(rawv, 96, 56, 48, 228)
print(f"  D1 vert           law={v}")

# ════════════════════════════════════════════════════════════════════
# FIX 2 — guard statics on the cell-10 spans (cfg+core, no battery)
# ════════════════════════════════════════════════════════════════════
print("\n── FIX 2 guard statics (cell-10 spans) ──")
FONTS = Path("/home/z/my-project/rf14_home/mangabd/fonts")
ns10 = {"__name__": "rf19_preflight"}
ns10["MANGABD_CONFIG"] = {
    "rendering": {
        "font_size_min": 8, "font_size_max": 48,
        "font_size_default": 24,
        "line_spacing_factor": 1.18, "padding_ratio": 0.08,
        "use_grapheme_safe_wrap": True,
        "use_background_aware_color": True,
        "allow_synthetic_bold": True,
        "stroke_width_bubble": 0, "stroke_width_thought": 0,
        "stroke_width_narrator": 0, "stroke_width_sfx": 1,
        "stroke_width_overlay": 1,
        "default_bubble_color": [0, 0, 0],
        "default_sfx_color": [255, 255, 255],
        "default_narrator_color": [0, 0, 0],
        "default_overlay_color": [255, 255, 255],
        "preview_max_width": 900,
        "font_regular": str(FONTS / "NotoSansBengali-Regular.ttf"),
        "font_bold": str(FONTS / "NotoSansBengali-Regular.ttf"),
        "font_fallback": str(FONTS / "NotoSansJP.ttf"),
        "vertical_rotate": -90,
    },
    "detection": {}, "inpainting": {},
}
ev = []
ns10["log_event"] = lambda message, level="INFO", **extra: ev.append(
    {"level": level, "message": message, "extra": extra})
ns10["MANGABD_EVENTS"] = ev
exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
     "from PIL import Image as PILImage\n"
     "from PIL import ImageDraw, ImageFont\n"
     "from PIL import features\nimport pandas as pd", ns10)


def extract_span(src, start, end):
    i = src.index(start)
    j = src.index(end, i)
    return src[i:j]


c10 = (WORK / "cell_10.py").read_text(encoding="utf-8")
cfg_span = extract_span(c10, "# 2. Rendering config defaults",
                        "# 3. Text helpers")
core_span = extract_span(c10, "# 3. Text helpers", "# 10. Self-tests")
exec(compile(cfg_span, "<c10 cfg>", "exec"), ns10)
exec(compile(core_span, "<c10 core>", "exec"), ns10)
print("[preflight] cell-10 spans exec OK")

TEXTS = {
    "T25c dialogue": "এই কী হয়েছে বলো তো?!",
    "T25d short": "লাল",
    "T24 long": "এই প্রথম লাল লাইনটি এখানে আর এই দ্বিতীয় লাইনটি কালো",
    "t19 text": "এই কী হয়েছে বলো তো?!",
    "s012 R7 tiny": "ছোট্ট জাদুর কথা এখানে",
}
CASES = [
    # (label, text, region w, h, quad wu, hv, gt lines)
    ("T25c id4-class", "T25c dialogue", 190, 165, 208, 62, 1),
    ("T25d healthy-1", "T25d short", 260, 80, None, None, None),
    ("T24-main class", "T24 long", 220, 110, None, None, None),
    ("t19 r1 class", "t19 text", 200, 90, None, None, None),
    ("t19 r2 tilt-nogt", "t19 text", 210, 160, None, None, None),
    ("s012 R7 tiny", "s012 R7 tiny", 51, 62, None, None, None),
]
for label, tkey, w, h, wu, hv, n_gt in CASES:
    text = TEXTS[tkey]
    fs_bbox, lines_bbox, _ = ns10["fit_font_size"](text, w, h, bold=False)
    row = (f"  {label:18s} bbox_fit=({fs_bbox}, {len(lines_bbox)}L)")
    if n_gt is not None:
        gt = {"lines": n_gt, "spacing": 0.0, "cx": 0.0, "cy": 0.0}
        lay = ns10["_b2_gt_tilted_layout"](text, gt, wu, hv, bold=False)
        if lay is None:
            row += "  gt_mirror=None(fallback fit)"
        else:
            row += f"  gt_mirror=({lay[0]}, {len(lay[1])}L)"
    print(row)

print("\n[preflight] DONE — freeze the winning geometry into Test 25")
