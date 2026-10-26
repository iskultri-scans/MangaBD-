#!/usr/bin/env python3
r"""MANGABD-008 B1 Phase C — content module: CELLS 11 + 12 patches (mirrored).

Cell 11 ("QUALITY CORE FINAL") and cell 12 ("QUALITY CORE", older
iteration) get byte-identical NEW text for every mirrored concern:
  * §2 — runtime download removed; refresh from cell-4's vendored
    registration (each cell keeps its own header comment, as before)
  * helpers — replaced by SHARED_BLOCK (byte-identical to cell 10)
  * _measure_line/draw loop — D-4 None-contract + D-5 clamp
  * §7.5 — NEW glyph-coverage self-checks (vertical path)

OLD anchors differ between the two cells only where the current
bytes differ (§2 headers; one blank line in cell 12's old helper
block; §7.5 insertion banners). Every OLD anchor is byte-copied
from the base notebook (main @ 73ca565).
"""

from m008_b1_phaseC_content10 import SHARED_BLOCK

# ── patch 11-1 / 12-1: §2 download removal ────────────────────
_S2_BODY_NEW = """# Cell-4 এখন JP fallback font resolve + sha256-verify করে (repo-vendored
# assets/fonts/ অথবা fonts dir) এবং CONFIG-এ set করে — এখানে শুধু refresh।
# Runtime download বাদ (MANGABD-008 Phase C, Owner decision)।
if not MANGABD_CONFIG["rendering"].get("font_fallback"):
    MANGABD_CONFIG["rendering"]["font_fallback"] = str(
        globals().get("MANGABD_ASSETS", {}).get("fonts", {}).get(
            "fallback_path", "assets/fonts/NotoSansJP[wght].ttf"))
MANGABD_CONFIG["rendering"].setdefault("vertical_rotate", -90)"""

CELL11_S2_OLD = """# ── 2) Fallback font ──
_fb_dir = Path(MANGABD_CONFIG["paths"].get("fonts", str(Path(MANGABD_CONFIG["paths"]["base"]) / "fonts")))
_fb_dir.mkdir(parents=True, exist_ok=True)
_fb_path = _fb_dir / "NotoSansJP.ttf"
if not _fb_path.exists() or _fb_path.stat().st_size < 1024:
    try:
        urllib.request.urlretrieve(
            "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf", _fb_path)
    except Exception as e:
        print(f"⚠️ fallback font failed: {str(e)[:80]}")
MANGABD_CONFIG["rendering"]["font_fallback"] = str(_fb_path)
MANGABD_CONFIG["rendering"].setdefault("vertical_rotate", -90)"""

CELL11_S2_NEW = """# ── 2) Fallback font (MANGABD-008 Phase C: vendored) ──
""" + _S2_BODY_NEW

CELL12_S2_OLD = """# ── 2) Fallback font (vertical note-এর CJK-এর জন্য) ──
_fb_dir = Path(MANGABD_CONFIG["paths"].get("fonts", str(Path(MANGABD_CONFIG["paths"]["base"]) / "fonts")))
_fb_dir.mkdir(parents=True, exist_ok=True)
_fb_path = _fb_dir / "NotoSansJP.ttf"
if not _fb_path.exists() or _fb_path.stat().st_size < 1024:
    try:
        urllib.request.urlretrieve(
            "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf", _fb_path)
    except Exception as e:
        print(f"⚠️ fallback font failed: {str(e)[:80]}")
MANGABD_CONFIG["rendering"]["font_fallback"] = str(_fb_path)
MANGABD_CONFIG["rendering"].setdefault("vertical_rotate", -90)"""

CELL12_S2_NEW = """# ── 2) Fallback font (vertical note-এর CJK-এর জন্য) (MANGABD-008 Phase C: vendored) ──
""" + _S2_BODY_NEW

# ── patch 11-2 / 12-2: helper block -> SHARED_BLOCK ────────────
CELL11_HELPERS_OLD = '''def _main_font_ok(ch):
    o = ord(ch)
    return (0x0980 <= o <= 0x09FF) or (0x0000 <= o <= 0x00FF) \\
        or (0x2000 <= o <= 0x206F) or (0x20B0 <= o <= 0x20BF) or ch in "→⇒➔➡—–…"
def _split_runs(text):
    runs, cur, cur_main = [], "", None
    for ch in text:
        m = _main_font_ok(ch)
        if cur and m == cur_main: cur += ch
        else:
            if cur: runs.append((cur, cur_main))
            cur, cur_main = ch, m
    if cur: runs.append((cur, cur_main))
    return runs
# MANGABD-003 V-1: CJK fallback visual-weight knobs (S001: kana ink ~50% of
# Bengali run height, mean ink luminance ~90 vs ~47.5 for the original note)
MANGABD_CONFIG["rendering"].setdefault("fallback_font_wght", 600)
MANGABD_CONFIG["rendering"].setdefault("fallback_cjk_scale", 1.25)
MANGABD_CONFIG["rendering"].setdefault("fallback_cjk_stroke", 1)
_FB_CACHE = {}
def get_font_fb(size, bold=False):
    key = (int(size), bool(bold))
    if key in _FB_CACHE: return _FB_CACHE[key]
    try: f = ImageFont.truetype(MANGABD_CONFIG["rendering"]["font_fallback"], int(size))
    except Exception: f = get_font(size, bold)
    # MANGABD-003 V-1: honor bold via the variable-font wght axis (the JP
    # fallback's default instance is wght=400); static fonts raise OSError
    # here -> fall through, the stroke compensation below carries the weight
    wght = int(MANGABD_CONFIG["rendering"].get("fallback_font_wght", 600))
    if bold: wght = max(wght, 700)
    try: f.set_variation_by_axes([wght])
    except OSError: pass
    _FB_CACHE[key] = f
    return f'''

CELL12_HELPERS_OLD = '''def _main_font_ok(ch):
    o = ord(ch)
    return (0x0980 <= o <= 0x09FF) or (0x0000 <= o <= 0x00FF) \\
        or (0x2000 <= o <= 0x206F) or (0x20B0 <= o <= 0x20BF) or ch in "→⇒➔➡—–…"

def _split_runs(text):
    runs, cur, cur_main = [], "", None
    for ch in text:
        m = _main_font_ok(ch)
        if cur and m == cur_main: cur += ch
        else:
            if cur: runs.append((cur, cur_main))
            cur, cur_main = ch, m
    if cur: runs.append((cur, cur_main))
    return runs

# MANGABD-003 V-1: CJK fallback visual-weight knobs (S001: kana ink ~50% of
# Bengali run height, mean ink luminance ~90 vs ~47.5 for the original note)
MANGABD_CONFIG["rendering"].setdefault("fallback_font_wght", 600)
MANGABD_CONFIG["rendering"].setdefault("fallback_cjk_scale", 1.25)
MANGABD_CONFIG["rendering"].setdefault("fallback_cjk_stroke", 1)
_FB_CACHE = {}
def get_font_fb(size, bold=False):
    key = (int(size), bool(bold))
    if key in _FB_CACHE: return _FB_CACHE[key]
    try: f = ImageFont.truetype(MANGABD_CONFIG["rendering"]["font_fallback"], int(size))
    except Exception: f = get_font(size, bold)
    # MANGABD-003 V-1: honor bold via the variable-font wght axis (the JP
    # fallback's default instance is wght=400); static fonts raise OSError
    # here -> fall through, the stroke compensation below carries the weight
    wght = int(MANGABD_CONFIG["rendering"].get("fallback_font_wght", 600))
    if bold: wght = max(wght, 700)
    try: f.set_variation_by_axes([wght])
    except OSError: pass
    _FB_CACHE[key] = f
    return f'''

CELL11_HELPERS_NEW = SHARED_BLOCK
CELL12_HELPERS_NEW = SHARED_BLOCK

# ── patch 11-3 / 12-3: _measure_line D-4 None-contract ────────
QC_MEASURE_OLD = """    def _measure_line(runs, scale):
        ws, tot = [], 0
        for t2, im in runs:
            f = get_font(size, bold) if im else get_font_fb(int(size*scale), bold)
            ws.append(draw.textlength(t2, font=f)); tot += ws[-1]
        return ws, tot"""

QC_MEASURE_NEW = """    def _measure_line(runs, scale):
        ws, tot = [], 0
        for t2, im in runs:
            # MANGABD-008 Phase C (D-4): get_font_fb None হলে (load fail)
            # main font-এ measure — WARN আগেই বেজেছে, silent নয়
            f = get_font(size, bold) if im else (get_font_fb(int(size*scale), bold) or get_font(size, bold))
            ws.append(draw.textlength(t2, font=f)); tot += ws[-1]
        return ws, tot"""

# ── patch 11-4 / 12-4: draw loop — D-4 None-contract + D-5 clamp ──
QC_DRAW_OLD = """        for (t2, im), ww in zip(runs, widths):
            f = get_font(size, bold) if im else get_font_fb(int(size*scale), bold)
            # MANGABD-003 V-1: scale + stroke for CJK runs; Flash amendment 2:
            # baseline-align fallback runs via font metrics (ascent difference)
            ly_run = ly if im else ly + asc_main - f.getmetrics()[0]
            sw = 0 if im else _fb_stroke"""

QC_DRAW_NEW = """        for (t2, im), ww in zip(runs, widths):
            f = get_font(size, bold) if im else (get_font_fb(int(size*scale), bold) or get_font(size, bold))
            # MANGABD-003 V-1: scale + stroke for CJK runs; Flash amendment 2:
            # baseline-align fallback runs via font metrics (ascent difference)
            # MANGABD-008 Phase C (D-5): anchor ঋণাত্মক হলে 0-এ clamp —
            # নাহলে বড় fitted size-এ glyph canvas-এর উপরে কাটা পড়ত
            ly_run = ly if im else max(0, ly + asc_main - f.getmetrics()[0])
            sw = 0 if im else _fb_stroke"""

# ── patch 11-5 / 12-5: §7.5 glyph-coverage self-checks ────────
VCHECK = '''# ── 7.5) MANGABD-008 Phase C: glyph-coverage self-checks (vertical path) ──
_m8_vtests = []


def _m8_check(name, cond, details=""):
    ok = bool(cond)
    print(("  ✅ " if ok else "  ❌ ") + name + ("" if ok or not details else f" ({details})"))
    _m8_vtests.append(ok)


# D-1: danda এখন MAIN font-এ route হয় — vertical note-এও আর tofu নয়
_m8_runs = _split_runs("বাক্য।")
_m8_check("danda routes MAIN (D-1)", _m8_runs[-1][1] is True)

# D-2/D-3: kana + ASCII এখন fallback-এ route হয়
_m8_check(
    "kana + ASCII route fallback (D-2)",
    _main_font_ok("こ") is False and _main_font_ok('"') is False,
)

# D-4: fallback font আসলেই লোড হয় (না হলে উপরে loud WARN দেখা যেত)
_m8_check("JP fallback font loads", get_font_fb(24) is not None)

# vertical mixed render: danda + kana + ASCII সবই ink দেয়
_m8_canvas = PILImage.new("RGB", (844, 1200), (255, 255, 255))
_qc_render_vertical(_m8_canvas, 'নোট: こがねই "আই"।', 10, 81, 61, 298, False, (0, 0, 0), None)
_m8_arr = np.array(_m8_canvas.convert("L"))
_m8_check("vertical mixed render ink", int((_m8_arr < 128).sum()) > 60)

# D-5: বড় fitted size-এ fallback glyph পুরোটাই canvas-এ (clamp)
_m8_sz, _m8_lines, _ = fit_font_size("こ", 298, 61, bold=False, padding=4)
_m8_canvas2 = PILImage.new("RGB", (844, 1200), (255, 255, 255))
_qc_render_vertical(_m8_canvas2, "こ", 10, 81, 61, 298, False, (0, 0, 0), None)
_m8_arr2 = np.array(_m8_canvas2.convert("L"))
_m8_ink2 = _m8_arr2 < 128
_m8_fbfont = get_font_fb(
    int(_m8_sz * float(MANGABD_CONFIG["rendering"].get("fallback_cjk_scale", 1.25))),
    False,
)
if _m8_ink2.any() and _m8_fbfont is not None:
    _m8_ref = PILImage.new("L", (400, 400), 255)
    _m8_rd = ImageDraw.Draw(_m8_ref)
    _m8_rd.text((40, 40), "こ", font=_m8_fbfont, fill=0, stroke_width=1, stroke_fill=0)
    _m8_ra = np.array(_m8_ref)
    _m8_rys, _m8_rxs = np.where(_m8_ra < 128)
    _m8_ref_h = int(_m8_rys.max() - _m8_rys.min() + 1)
    _m8_xcols = np.where(_m8_ink2.any(axis=0))[0]
    _m8_drawn_h = int(_m8_xcols.max() - _m8_xcols.min() + 1)
    _m8_check(
        "baseline clamp keeps full glyph (D-5)",
        _m8_drawn_h >= _m8_ref_h - 2,
        f"drawn={_m8_drawn_h} ref={_m8_ref_h}",
    )
else:
    _m8_check("baseline clamp keeps full glyph (D-5)", False, "no ink or no fb font")

print(f"  QUALITY CORE glyph-coverage: {sum(_m8_vtests)}/{len(_m8_vtests)}")'''

CELL11_VCHECK_OLD = """    globals()["render_bengali_text"] = render_bengali_text
    globals()["_QC_FINAL_RENDER_PATCHED"] = True

# ── 8) pipeline wrap ──"""

CELL11_VCHECK_NEW = """    globals()["render_bengali_text"] = render_bengali_text
    globals()["_QC_FINAL_RENDER_PATCHED"] = True

""" + VCHECK + """

# ── 8) pipeline wrap ──"""

CELL12_VCHECK_OLD = """    globals()["render_bengali_text"] = render_bengali_text
    globals()["_QC_RENDER_PATCHED"] = True

# ── 6) UI button-এর জন্য pipeline wrap ──"""

CELL12_VCHECK_NEW = """    globals()["render_bengali_text"] = render_bengali_text
    globals()["_QC_RENDER_PATCHED"] = True

""" + VCHECK + """

# ── 6) UI button-এর জন্য pipeline wrap ──"""
