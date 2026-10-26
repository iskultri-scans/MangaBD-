#!/usr/bin/env python3
r"""MANGABD-008 B1 Phase C — content module: CELL 10 patches.

Cell 10 = the base renderer's per-run fallback extension (D-3):
  * SHARED_BLOCK — cmap-coverage font routing (D-1/D-2) + the
    WARN-never-silent get_font_fb (D-4). Byte-identical text is
    also patched into cells 11/12 (content1112 imports it) so all
    three cells carry the same routing/fallback helpers.
  * _draw_runs_horizontal — the run-splitting draw for horizontal
    lines (V-1 knobs + amendment-1 overflow ladder + amendment-2
    baseline align with the D-5 clamp).
  * gates in render_bengali_text + _render_rotated_text — pure-
    Bengali lines keep the exact original single-font draw.
  * Tests 9-12 — glyph-coverage battery additions.

Every OLD anchor below is byte-copied from the base notebook
(main @ 73ca565) and unique-asserted by the build driver.
"""

# ─────────────────────────────────────────────────────────────
# SHARED BLOCK (byte-identical in cells 10/11/12)
# ─────────────────────────────────────────────────────────────
SHARED_BLOCK = '''# ── MANGABD-008 Phase C: cmap-coverage font routing (D-1/D-2 fix) ──
# পুরনো hardcoded range check টা দুইদিকে ভুল করত: danda U+0964 (Devanagari
# block, 0x0980-0x09FF-এর বাইরে) JP fallback-এ চলে যেত — যে font-এ ওই glyph
# নেই (tofu); আর ASCII/em-dash NotoSansBengali-তে যেত — যেখানে basic Latin-ই
# নেই। এখন route হয় দুই font-এর আসল cmap দেখে: main font-এ glyph থাকলে MAIN;
# না থাকলে fallback-এ থাকলে FALLBACK; দুটোতেই না থাকলে MAIN (আগের আচরণ)
# + একবার WARN — কখনো silent নয়।
_FONT_COVERAGE_CACHE = {}
_FONT_ROUTE_WARNED = {}
_ROUTE_QUIET = frozenset(
    {0xA0, 0xAD, 0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x202A, 0x202B,
     0x202C, 0x202D, 0x202E, 0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF}
)


def _font_cmap_codepoints(path):
    """
    Font-এর cmap codepoint set (fontTools — matplotlib-এর সাথে আসে)।
    না পারলে None — তখন _main_font_ok-এর degraded range arm কাজ করে।
    """
    p = str(path)
    if p in _FONT_COVERAGE_CACHE:
        return _FONT_COVERAGE_CACHE[p]
    cov = None
    try:
        from fontTools.ttLib import TTFont

        tf = TTFont(p)
        try:
            cov = frozenset(tf.getBestCmap().keys())
        finally:
            tf.close()
    except Exception as exc:
        print(f"⚠️ cmap coverage পাওয়া যায়নি ({p}): {str(exc)[:80]} — range routing")
        log_event(f"font cmap coverage unavailable: {p}", level="WARN")
    _FONT_COVERAGE_CACHE[p] = cov
    return cov


def _main_font_cov():
    _p = MANGABD_CONFIG["rendering"].get("font_regular", "")
    return _font_cmap_codepoints(_p) if _p else None


def _fb_font_cov():
    _p = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    return _font_cmap_codepoints(_p) if _p else None


def _main_font_ok(ch):
    o = ord(ch)
    cov = _main_font_cov()
    if cov is not None:
        if o in cov:
            return True
        fbcov = _fb_font_cov()
        if fbcov is None or o in fbcov:
            # main-এ নেই: fallback-এ route। fb cmap অজানা হলেও optimistic
            # route — loader-ই load fail হলে loud WARN (D-4) + caller main-এ
            # আঁকবে; তাই missing-font case-এও warning render-time-এ বাজে।
            return False
        # দুই font-এই glyph নেই: MAIN-এ আঁকা হবে (আগের মতোই) + একবার WARN;
        # zero-width/format chars নীরব — cmap-এ ওরা কখনোই থাকে না
        if o >= 0x20 and o not in _ROUTE_QUIET and ch not in _FONT_ROUTE_WARNED:
            _FONT_ROUTE_WARNED[ch] = True
            print(f"⚠️ U+{o:04X} {ch!r} দুই font-এই নেই — MAIN font-এ আঁকা হবে (tofu হতে পারে)")
            log_event(f"glyph missing from both fonts: U+{o:04X}", level="WARN")
        return True
    # fontTools না থাকলে degraded range routing — Devanagari block যোগ
    # (danda ঠিক); বাকি আগের মতোই। Colab-এ fontTools থাকে (matplotlib)।
    return (0x0980 <= o <= 0x09FF) or (0x0900 <= o <= 0x097F) \\
        or (0x0000 <= o <= 0x00FF) or (0x2000 <= o <= 0x206F) \\
        or (0x20B0 <= o <= 0x20BF) or ch in "→⇒➔➡—–…"


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
    f = None
    try: f = ImageFont.truetype(MANGABD_CONFIG["rendering"]["font_fallback"], int(size))
    except Exception as exc:
        # MANGABD-008 Phase C (D-4): silent Bengali degrade বাদ। Loud ERROR +
        # None return — caller main font দিয়েই আঁকে, কিন্তু defect আর লুকায় না।
        if "fb_load" not in _FONT_ROUTE_WARNED:
            _FONT_ROUTE_WARNED["fb_load"] = True
            print(
                "⚠️ JP fallback font unavailable (" + str(exc)[:80] + ")। "
                "ASCII/কানা tofu হবে। Fix: repo-র assets/fonts/NotoSansJP[wght].ttf "
                "অথবা fonts dir-এ NotoSansJP.ttf রাখো।"
            )
            log_event("JP fallback font unavailable — ASCII/kana will tofu", level="ERROR")
        _FB_CACHE[key] = None
        return None
    # MANGABD-003 V-1: honor bold via the variable-font wght axis (the JP
    # fallback's default instance is wght=400); static fonts raise OSError
    # here -> fall through, the stroke compensation below carries the weight
    wght = int(MANGABD_CONFIG["rendering"].get("fallback_font_wght", 600))
    if bold: wght = max(wght, 700)
    try: f.set_variation_by_axes([wght])
    except OSError: pass
    _FB_CACHE[key] = f
    return f'''


# ─────────────────────────────────────────────────────────────
# cell-10 insert: SHARED_BLOCK + _draw_runs_horizontal (after get_font)
# ─────────────────────────────────────────────────────────────

DRAW_RUNS = '''def _draw_runs_horizontal(
    draw, line, x, w, line_y, font, bold, text_color,
    stroke_color, stroke_width, padding,
):
    """
    MANGABD-008 Phase C (D-3): horizontal line-এর per-run fallback draw।
    শুধু যে line-এ main font-এ নেই এমন glyph আছে (ASCII/em-dash/কানা) সেটাতেই
    এই helper ডাকা হয় — pure-Bengali line আগের exact single-font path-ই
    follow করে। Main run-গুলো একই font, একই stroke, একই baseline; fallback
    run V-1 knobs (wght 600 + scale + stroke) মেনে চলে, ascent-পার্থক্যে
    baseline-align হয় (D-5 clamp সহ)।
    """
    cfg = MANGABD_CONFIG["rendering"]
    size = int(getattr(font, "size", 12))
    fb_scale = float(cfg.get("fallback_cjk_scale", 1.25))
    fb_stroke = int(cfg.get("fallback_cjk_stroke", 1))
    asc_main = font.getmetrics()[0]
    runs = _split_runs(line)

    def _measure(scale):
        ws, tot = [], 0
        for t2, im in runs:
            f = font if im else (get_font_fb(int(size * scale), bold) or font)
            ws.append(draw.textlength(t2, font=f))
            tot += ws[-1]
        return ws, tot

    scale = fb_scale
    widths, total = _measure(scale)
    pad = int(padding or 0)
    # V-1 Flash amendment-1-এর horizontal mirror: scaled fallback run box-এ
    # overflow করলে scale ধাপে ধাপে কমে (1.12 -> 1.0)
    while any(not im for _, im in runs) and total > int(w) - 2 * pad and scale > 1.0:
        scale = 1.12 if scale > 1.12 else 1.0
        widths, total = _measure(scale)

    pen_x = int(x + (int(w) - int(total)) // 2)

    for (t2, im), ww in zip(runs, widths):
        f = font if im else (get_font_fb(int(size * scale), bold) or font)
        # D-5: fb run-এর baseline anchor ঋণাত্মক হলে 0-এ clamp
        ty = line_y if im else max(0, int(line_y) + asc_main - f.getmetrics()[0])
        sw = int(stroke_width) if im else fb_stroke
        if sw > 0:
            draw.text(
                (pen_x, ty),
                t2,
                font=f,
                fill=text_color,
                stroke_width=sw,
                stroke_fill=stroke_color,
            )
        else:
            draw.text((pen_x, ty), t2, font=f, fill=text_color)
        pen_x += ww
'''

CELL10_HELPERS_OLD = """    _FONT_CACHE[key] = font

    return font


def measure_text(text, font, draw=None):"""

CELL10_HELPERS_NEW = """    _FONT_CACHE[key] = font

    return font


""" + SHARED_BLOCK + """


""" + DRAW_RUNS + """

def measure_text(text, font, draw=None):"""
