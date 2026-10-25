#!/usr/bin/env python3
"""MANGABD-008 B1 PHASE A — Kana-tofu (N-D) minimal reproduction instrument.

Docs + instrument ONLY — reads the notebook, NEVER writes it. No source changes.

Provenance: MANGABD-008 B1 Phase A directive (Owner-authorized, PM relay).
Base: main @ 63259a8 (notebook blob md5 a48538b9830e26e350fcd6478eb3f0b5).

What this proves (the Phase A root-cause matrix):
  S1  vertical path (cells 11/12 QC patch) + NotoSansJP fallback present
      -> kana runs render as REAL (dark) glyphs; the trailing danda U+0964
         renders as a HOLLOW TOFU BOX because _main_font_ok() classifies
         U+0964 as non-main (it is in the Devanagari block, outside the
         0x0980-0x09FF check) and NotoSansJP has no U+0964 glyph.
         => reproduces the archived N-D signature on the CURRENT bytes.
  S2  vertical path + font_fallback file MISSING (simulated download
      failure: cell-11 sets the config key unconditionally, L20-26)
      -> get_font_fb() SILENTLY falls back to the Bengali font
         -> kana become hollow tofu; danda renders fine (Bengali font).
         => the silent-degrade hazard (no warning at render time).
  S3  horizontal path (cell-10 base render_bengali_text, w>=90 geometry)
      -> NO fallback exists on this path: kana render as hollow tofu
         through NotoSansBengali's .notdef; danda fine.
         => the directive's literal claim, latent (no archived kana
            region is horizontal yet).
  S4  danda-only control (vertical vs horizontal) — isolates the danda.
  X   archived-crop cross-check: S005_manual / S005_openrouter (repo
      samples/) + S007 (repo zip) R1 crops contain the same hollow-box
      template at the trailing-glyph position (multi-scale search).

Fonts required (NOT committed; fetch per the notebook's own URLs):
  NotoSansBengali-Regular.ttf
    https://github.com/notofonts/bengali/raw/main/fonts/NotoSansBengali/hinted/ttf/NotoSansBengali-Regular.ttf
    (alternate: https://cdn.jsdelivr.net/gh/notofonts/notofonts.github.io/fonts/NotoSansBengali/hinted/ttf/NotoSansBengali-Regular.ttf)
  NotoSansJP.ttf (variable, wght axis; cell-11's exact URL)
    https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf

Usage:
  python3 scripts/m008_b1_kana_repro.py --fonts-dir <dir> [--out-dir <dir>]
"""
import argparse
import ast
import hashlib
import json
import os
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(os.environ.get("MANGABD_REPO", Path(__file__).resolve().parent.parent))
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB = REPO / NB_NAME
BASE_MD5_EXPECT = "a48538b9830e26e350fcd6478eb3f0b5"

# ─────────────────────────────────────────────────────────────────
# 1. Byte-faithful code-path extraction from the notebook
# ─────────────────────────────────────────────────────────────────

def load_code_cells(nb_path):
    raw = nb_path.read_bytes()
    md5 = hashlib.md5(raw).hexdigest()
    if md5 != BASE_MD5_EXPECT:
        print(f"⚠️ notebook md5 {md5} != expected {BASE_MD5_EXPECT} "
              f"(base 63259a8) — results still extracted, provenance disclosed")
    nb = json.loads(raw.decode("utf-8"))
    return ["".join(c.get("source", [])) for c in nb["cells"]
            if c.get("cell_type") == "code"]


def extract_span(src, start_marker, end_marker):
    """Source lines from the line containing start_marker (exclusive of the
    marker line's own section banner? -> inclusive) up to the line containing
    end_marker (exclusive)."""
    lines = src.split("\n")
    si = next(i for i, l in enumerate(lines) if start_marker in l)
    ei = next(i for i, l in enumerate(lines) if end_marker in l and i > si)
    return "\n".join(lines[si:ei])


def build_namespace(cells, fonts_dir):
    """Exec the REAL cell-10 render core + cell-11 vertical/fallback core,
    verbatim, into an instrument namespace. Mirrors the notebook runtime:
    cell-10 defines render_bengali_text (base), then cell-11's guarded patch
    rebinds it (its base = cell-10's original, because _qc_orig_render does
    not exist until cell 12 — exactly the real cell-11 exec order)."""
    ns = {"__name__": "m008_repro_namespace"}

    # minimal runtime surface the spans expect
    ns["MANGABD_CONFIG"] = {
        "rendering": {
            "font_size_min": 8, "font_size_max": 48, "font_size_default": 24,
            "line_spacing_factor": 1.18, "padding_ratio": 0.08,
            "use_grapheme_safe_wrap": True, "use_background_aware_color": True,
            "allow_synthetic_bold": True,
            "stroke_width_bubble": 0, "stroke_width_thought": 0,
            "stroke_width_narrator": 0, "stroke_width_sfx": 1,
            "stroke_width_overlay": 1,
            "default_bubble_color": [0, 0, 0], "default_sfx_color": [255, 255, 255],
            "default_narrator_color": [0, 0, 0], "default_overlay_color": [255, 255, 255],
            "preview_max_width": 900,
            "font_regular": str(Path(fonts_dir) / "NotoSansBengali-Regular.ttf"),
            "font_bold": str(Path(fonts_dir) / "NotoSansBengali-Regular.ttf"),
            "font_fallback": str(Path(fonts_dir) / "NotoSansJP.ttf"),
            # cell-11 §2 L27 setdefault (span not exec'd; key value identical)
            "vertical_rotate": -90,
        },
        "detection": {}, "inpainting": {},
    }
    ns["log_event"] = lambda *a, **k: None
    # imports the cell sources rely on at module scope
    exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
         "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)

    # cell 10 §3-§8 (text helpers → main renderer), verbatim span
    span10 = extract_span(cells[10], "# 3. Text helpers", "# 9. Page rendering pipeline")
    exec(compile(span10, "<cell10 §3-§8>", "exec"), ns)

    # cell 11 §7 (vertical note render + guarded patch), verbatim span
    span11 = extract_span(cells[11], "# ── 7) vertical note render ──", "# ── 8) pipeline wrap ──")
    exec(compile(span11, "<cell11 §7>", "exec"), ns)
    return ns


# ─────────────────────────────────────────────────────────────────
# 2. Reference glyph bitmaps + template matching
# ─────────────────────────────────────────────────────────────────

def ref_bitmap(char, font_path, px, wght=None, stroke=0):
    """Render one char on white, crop to ink bbox. Returns (bitmap_uint8,
    ink_mask_bool, metrics dict)."""
    f = ImageFont.truetype(str(font_path), int(px))
    if wght is not None:
        try:
            f.set_variation_by_axes([wght])
        except OSError:
            pass
    pad = int(px) + 12
    im = Image.new("L", (pad * 3, pad * 3), 255)
    d = ImageDraw.Draw(im)
    kw = {"stroke_width": int(stroke), "stroke_fill": 0} if stroke else {}
    d.text((pad, pad), char, font=f, fill=0, **kw)
    a = np.array(im)
    mask = a < 128
    if not mask.any():
        return None, None, {"ink": 0}
    ys, xs = np.where(mask)
    sub = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return sub, (sub < 128), {
        "ink": int(mask.sum()), "w": sub.shape[1], "h": sub.shape[0],
        "inner_ink": int((sub[2:-2, 2:-2] < 128).sum()) if sub.shape[0] > 4 and sub.shape[1] > 4 else -1,
    }


def ncc_match(canvas_gray, ref_gray, ink_thr=200):
    """Normalized cross-correlation of a GRAYSCALE reference over the canvas
    (mean-subtracted windows — robust to anti-aliasing). Returns (best, xy)."""
    t = ref_gray.astype(np.float64)
    t = t - t.mean()
    tn = np.sqrt((t * t).sum())
    if tn == 0:
        return 0.0, (0, 0)
    c = canvas_gray.astype(np.float64)
    th, tw = t.shape
    H, W = c.shape
    best, bx, by = -2.0, 0, 0
    for y in range(0, H - th + 1):
        for x in range(0, W - tw + 1):
            win = c[y:y + th, x:x + tw]
            s = win - win.mean()
            sn = np.sqrt((s * s).sum())
            if sn == 0:
                continue
            score = float((t * s).sum() / (tn * sn))
            if score > best:
                best, bx, by = score, x, y
    return best, (bx, by)


def quick_ncc(canvas_gray, ref_gray, center, radius):
    """ncc_match restricted to a window around an expected center (x, y)."""
    H, W = canvas_gray.shape
    th, tw = ref_gray.shape
    x0 = max(0, int(center[0] - radius)); x1 = min(W - tw, int(center[0] + radius))
    y0 = max(0, int(center[1] - radius)); y1 = min(H - th, int(center[1] + radius))
    if x1 < x0 or y1 < y0:
        return -2.0, (0, 0)
    sub = canvas_gray[y0:y1 + th, x0:x1 + tw]
    s, xy = ncc_match(sub, ref_gray)
    return s, (xy[0] + x0, xy[1] + y0)


# ─────────────────────────────────────────────────────────────────
# 3. Vertical draw-position replication (from _qc_render_vertical arithmetic)
# ─────────────────────────────────────────────────────────────────

def vertical_run_positions(ns, text, w, h, bold, padding=4):
    """Replicate cell-11 _qc_render_vertical's run layout arithmetic to get
    each run's tc-canvas (pre-rotation) draw origin + font + size. Verbatim
    function is used for measurement calls; arithmetic mirrors L168-202."""
    R = ns["MANGABD_CONFIG"]["rendering"]
    size, lines, th = ns["fit_font_size"](text, h, w, bold=bold, padding=padding)
    lh = ns["get_line_height"](ns["get_font"](size, bold))
    fb_scale = float(R.get("fallback_cjk_scale", 1.25))
    fb_stroke = int(R.get("fallback_cjk_stroke", 1))
    asc_main = ns["get_font"](size, bold).getmetrics()[0]
    out = []
    dummy = Image.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    for i, line in enumerate(lines):
        runs = ns["_split_runs"](line)
        scale = fb_scale
        def measure(runs_, scale_):
            ws, tot = [], 0
            for t2, im_ in runs_:
                f = ns["get_font"](size, bold) if im_ else ns["get_font_fb"](int(size * scale_), bold)
                wv = draw.textlength(t2, font=f)
                ws.append(wv); tot += wv
            return ws, tot
        widths, total = measure(runs, scale)
        while any(not im_ for _, im_ in runs) and total > int(h) - 2 * padding and scale > 1.0:
            scale = 1.12 if scale > 1.12 else 1.0
            widths, total = measure(runs, scale)
        sy = max(padding, (int(w) - lh * len(lines)) // 2)
        lx = (int(h) - total) // 2
        ly = sy + i * lh
        for (t2, is_main), wv in zip(runs, widths):
            f = ns["get_font"](size, bold) if is_main else ns["get_font_fb"](int(size * scale), bold)
            out.append({
                "text": t2, "main": is_main, "size": size if is_main else int(size * scale),
                "tc_x": lx, "tc_y": ly if is_main else ly + asc_main - f.getmetrics()[0],
                "run_w": int(wv), "font": f.path if hasattr(f, "path") else "?",
                "line": i, "scale": scale if not is_main else 1.0,
                "stroke": 0 if is_main else fb_stroke,
            })
            lx += int(wv)
    return size, lines, out


def tc_to_final(px, py, tc_w, tc_h):
    """rotate(-90, expand=True) = 90° clockwise: (x,y) -> (tc_h-1-y, x)."""
    return (tc_h - 1 - py, px)


# ─────────────────────────────────────────────────────────────────
# 4. Scenarios
# ─────────────────────────────────────────────────────────────────

def scenario_vertical(ns, text, tag, out_dir, fallback_exists=True):
    """R1 geometry (61x298 @ 10,81), vertical predicate fires."""
    R = ns["MANGABD_CONFIG"]["rendering"]
    real_fb = R["font_fallback"]
    if not fallback_exists:
        R["font_fallback"] = str(Path(real_fb).parent / "MISSING-NotoSansJP.ttf")
        ns["_FB_CACHE"].clear()
    else:
        ns["_FB_CACHE"].clear()
    canvas = Image.new("RGB", (844, 1200), (255, 255, 255))
    ns["render_bengali_text"](canvas, text, 10, 81, 61, 298, angle=0.0,
                              region_type="overlay", bold=None, stroke_width=None,
                              text_color=None, padding=None)
    canvas.save(out_dir / f"{tag}.png")
    gray = np.array(canvas.convert("L"))
    R["font_fallback"] = real_fb
    ns["_FB_CACHE"].clear()
    return canvas, gray


def scenario_horizontal(ns, text, tag, out_dir):
    """Wide geometry -> cell-10 base path (no fallback logic at all)."""
    canvas = Image.new("RGB", (700, 200), (255, 255, 255))
    ns["render_bengali_text"](canvas, text, 20, 20, 660, 160, angle=0.0,
                              region_type="bubble", bold=False, stroke_width=0,
                              text_color=(0, 0, 0), padding=None)
    canvas.save(out_dir / f"{tag}.png")
    return canvas, np.array(canvas.convert("L"))


def classify_runs(ns, gray, text, fonts_dir, w=61, h=298, bold=False):
    """Classify the fallback-routed runs (kana / danda / CJK) of the vertical
    layout by template-matching each run's first char against BOTH font
    references at the fitted size. Main(Bengali)-routed runs are not the
    defect surface and are only counted."""
    ben = Path(fonts_dir) / "NotoSansBengali-Regular.ttf"
    jp = Path(fonts_dir) / "NotoSansJP.ttf"
    R = ns["MANGABD_CONFIG"]["rendering"]
    wght = int(R.get("fallback_font_wght", 600))
    size, lines, runs = vertical_run_positions(ns, text, w, h, bold)
    verdicts, main_count = [], 0
    for r in runs:
        if r["main"]:
            main_count += 1
            continue
        ch = r["text"][0]
        refA, _, _ = ref_bitmap(ch, jp, r["size"], wght=wght, stroke=r["stroke"])
        refB, _, _ = ref_bitmap(ch, ben, r["size"], wght=None, stroke=0)
        # tc origin -> final coords (rotate -90 CW: (x,y) -> (tc_h-1-y, x))
        fx = (w - 1) - r["tc_y"]            # final x (column-cross axis)
        fy = r["tc_x"]                       # final y (column-long axis)
        radius = max(14, int(r["size"]) + 10)
        sA = sB = None
        posA = None
        if refA is not None:
            sA, posA = quick_ncc(gray, refA, (fx, fy), radius=radius)
        if refB is not None:
            sB, _ = quick_ncc(gray, refB, (fx, fy), radius=radius)
        hollow = ""
        if posA is not None and sA is not None and sA > 0.5:
            y2, x2 = posA
            win = gray[max(0, y2):y2 + refA.shape[0], max(0, x2):x2 + refA.shape[1]]
            if win.size:
                wm = win < 200
                inner = wm[2:-2, 2:-2] if wm.shape[0] > 4 and wm.shape[1] > 4 else np.zeros((1, 1), bool)
                if inner.size and inner.sum() == 0 and wm.mean() > 0.10:
                    hollow = " HOLLOW(.notdef)"
        verdicts.append({
            "run": r["text"], "char": ch, "size": r["size"],
            "routed": "FALLBACK(JP)",
            "tc_y": r["tc_y"],
            "clip_risk": bool(r["tc_y"] < 0),
            "score_jp_ref": None if sA is None else round(sA, 3),
            "score_bengali_ref": None if sB is None else round(sB, 3),
            "match_pos_jp": posA,
            "note": (("CLIP(tc_y<0):baseline-align pushes glyph above canvas top" if r["tc_y"] < 0 else "") + " " +
                     (hollow.strip() or ("real-ink" if (sA is not None and (sB is None or sA >= sB)) else "bengali-font-wins"))).strip(),
        })
    return size, runs, {"fitted_size": size, "main_runs": main_count,
                         "fallback_runs": verdicts}


def char_inventory(fonts_dir):
    """Enumerate the glyph-coverage defect surface: every distinct char in the
    archived translated texts x both fonts' cmaps (deterministic fontTools)."""
    from fontTools.ttLib import TTFont
    ben = Path(fonts_dir) / "NotoSansBengali-Regular.ttf"
    jp = Path(fonts_dir) / "NotoSansJP.ttf"
    cb = TTFont(str(ben)).getBestCmap()
    cj = TTFont(str(jp)).getBestCmap()
    texts = {}
    for sub in ("S001_color_webtoon", "S002_batch1", "S003_batch2",
                "S005_manual", "S005_openrouter"):
        p = REPO / "samples" / sub / "translation.json"
        if p.exists():
            for t in json.loads(p.read_text(encoding="utf-8")):
                texts[f"{sub}#{t['id']}"] = t["translated_text"]
    zp = REPO / "S007_mangabd005_02.zip"
    if zp.exists():
        with zipfile.ZipFile(zp) as zf:
            tr = json.loads(zf.read(next(n for n in zf.namelist()
                                         if n.endswith("translation.json"))))
            for t in tr:
                texts[f"S007#{t['id']}"] = t["translated_text"]
    chars = set()
    for t in texts.values():
        chars |= set(t)
    missing_ben = sorted([c for c in chars if ord(c) not in cb], key=ord)
    missing_both = sorted([c for c in chars if ord(c) not in cb and ord(c) not in cj], key=ord)
    return {
        "distinct_chars": len(chars),
        "missing_from_bengali": [
            {"cp": f"U+{ord(c):04X}", "char": c, "in_jp": ord(c) in cj} for c in missing_ben],
        "missing_from_both": [
            {"cp": f"U+{ord(c):04X}", "char": c} for c in missing_both],
        "n_texts": len(texts),
    }


def archived_cross_check(fonts_dir, out_dir):
    """Search the archived finals' R1 crops for the JP-font .notdef box of
    । at multiple fitted-size scales (corroboration of the N-D signature)."""
    jp = Path(fonts_dir) / "NotoSansJP.ttf"
    results = {}
    targets = [
        ("S005_manual", REPO / "samples/S005_manual/final.jpg"),
        ("S005_openrouter", REPO / "samples/S005_openrouter/final.jpg"),
    ]
    # S007 from the repo zip
    zpath = REPO / "S007_mangabd005_02.zip"
    if zpath.exists():
        with zipfile.ZipFile(zpath) as zf:
            for n in zf.namelist():
                if n.endswith("final.jpg"):
                    p = out_dir / "S007_final.jpg"
                    p.write_bytes(zf.read(n))
                    targets.append(("S007", p))
                    break
    for tag, path in targets:
        if not path.exists():
            results[tag] = {"error": f"missing {path}"}
            continue
        im = Image.open(path).convert("L")
        crop = im.crop((10, 81, 71, 379))
        crop.save(out_dir / f"X_{tag}_R1_crop.png")
        gray = np.array(crop)
        best = (0.0, None, None)
        for px in range(7, 26):
            # stroke variants for the dark-weight CJK runs
            for stroke in (0, 1):
                ref2, _, _ = ref_bitmap("।", jp, px, wght=None, stroke=stroke)
                if ref2 is None:
                    continue
                s, pos = ncc_match(gray, ref2)
                if s > best[0]:
                    met = {"px": px, "stroke": stroke}
                    best = (s, pos, met)
        results[tag] = {
            "best_ncc_danda_notdef_box": round(best[0], 3),
            "pos_in_R1_crop": best[1], "probe_px_stroke": (best[2]["px"], best[2]["stroke"]) if best[2] else None,
        }
    return results


# ─────────────────────────────────────────────────────────────────
# 5. Classification probes (font coverage + routing)
# ─────────────────────────────────────────────────────────────────

def probes(ns, fonts_dir):
    ben = Path(fonts_dir) / "NotoSansBengali-Regular.ttf"
    jp = Path(fonts_dir) / "NotoSansJP.ttf"
    from fontTools.ttLib import TTFont
    def cmap(p):
        return TTFont(str(p)).getBestCmap()
    cb, cj = cmap(ben), cmap(jp)
    chars = {"।": 0x0964, "॥": 0x0965, "ক": 0x0995, "া": 0x09BE,
             "こ": 0x3053, "が": 0x304C, "ね": 0x306D, "い": 0x3044,
             "お": 0x304A, "て": 0x3066, "あ": 0x3042, "ら": 0x3089}
    cov = {c: {"bengali": cp in cb, "jp": cp in cj} for c, cp in chars.items()}
    routing = {c: {"_main_font_ok": bool(ns["_main_font_ok"](c)),
                   "routed_to": "MAIN(Bengali)" if ns["_main_font_ok"](c) else "FALLBACK(JP)"}
               for c in ["ক", "a", "।", "॥", "こ", "い", "—", "→"]}
    validate = {"kana_only": bool(ns["render_validate_bengali"]("こがねい")),
                "mixed": bool(ns["render_validate_bengali"]("টি নোট こがねই")),
                "bengali_only": bool(ns["render_validate_bengali"]("বাংলা"))}
    return cov, routing, validate


# ─────────────────────────────────────────────────────────────────
# 6. Main
# ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fonts-dir", required=True)
    ap.add_argument("--out-dir", default="m008_b1_repro_out")
    ap.add_argument("--repo", default=None, help="MangaBD repo root override")
    args = ap.parse_args()
    if args.repo:
        globals()["REPO"] = Path(args.repo)
    global NB
    NB = REPO / NB_NAME
    fonts_dir = Path(args.fonts_dir)
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    for f in ("NotoSansBengali-Regular.ttf", "NotoSansJP.ttf"):
        if not (fonts_dir / f).exists():
            sys.exit(f"missing font {fonts_dir / f} — see docstring URLs")

    cells = load_code_cells(NB)
    print(f"notebook: {NB_NAME} | code cells: {len(cells)}")
    ns = build_namespace(cells, fonts_dir)
    print("namespace: cell-10 §3-§8 + cell-11 §7 exec'd verbatim "
          f"({len(cells[10].splitlines())}/{len(cells[11].splitlines())}-line cells, base {BASE_MD5_EXPECT[:8]})")

    # archived R1 texts (from the repo)
    tr_s003 = json.loads((REPO / "samples/S003_batch2/translation.json").read_text(encoding="utf-8"))
    t_s003 = next(t["translated_text"] for t in tr_s003 if t["id"] == 1)
    with zipfile.ZipFile(REPO / "S007_mangabd005_02.zip") as zf:
        tr_s007 = json.loads(zf.read(next(n for n in zf.namelist() if n.endswith("translation.json"))))
    t_s007 = next(t["translated_text"] for t in tr_s007 if t["id"] == 1)
    print(f"S003 R1 text: {t_s003[:70]}...")
    print(f"S007 R1 text: {t_s007[:70]}...")

    report = {"scenarios": {}, "probes": {}}

    # probes
    cov, routing, validate = probes(ns, fonts_dir)
    inv = char_inventory(fonts_dir)
    report["probes"] = {"coverage": cov, "routing": routing,
                        "render_validate_bengali": validate,
                        "archived_text_char_inventory": inv}
    print("\n── probes: glyph coverage (fontTools cmap) ──")
    for c, v in cov.items():
        print(f"  U+{ord(c):04X} {c}: Bengali={'Y' if v['bengali'] else 'N'} JP={'Y' if v['jp'] else 'N'}")
    print("── probes: _main_font_ok routing (cells 11/12 L134-137) ──")
    for c, v in routing.items():
        print(f"  {c!r}: {v['_main_font_ok']} -> {v['routed_to']}")
    print(f"── probes: archived-text char inventory ({inv['n_texts']} texts, "
          f"{inv['distinct_chars']} distinct chars): missing from NotoSansBengali "
          f"= {len(inv['missing_from_bengali'])} chars, missing from BOTH fonts "
          f"= {len(inv['missing_from_both'])} ──")
    for m in inv["missing_from_bengali"]:
        print(f"  {m['cp']} {m['char']!r} (in JP: {m['in_jp']})")
    for m in inv["missing_from_both"]:
        print(f"  {m['cp']} {m['char']!r} — TOFU IN ANY SINGLE-FONT PATH")

    # S1: current bytes, vertical, fallback present (S007 text — the N-D live case)
    _, gray1 = scenario_vertical(ns, t_s007, "S1_vertical_fallback_OK", out_dir, fallback_exists=True)
    size1, runs1, v1 = classify_runs(ns, gray1, t_s007, fonts_dir)
    report["scenarios"]["S1_vertical_fallback_OK"] = {
        "fitted_size": size1, "runs": len(runs1), "verdicts": v1}
    print("\n── S1 vertical + fallback present (current bytes, S007 R1 text) ──")
    print(f"  fitted_size={size1}, main(Bengali) runs={v1['main_runs']}, fallback runs={len(v1['fallback_runs'])}")
    for v in v1["fallback_runs"]:
        print(f"  run {v['run'][:10]!r:14} routed={v['routed']} size={v['size']} "
              f"jp_ref={v['score_jp_ref']} bengali_ref={v['score_bengali_ref']} {v['note']}")

    # S1b: same but S003 text (pure kana runs こがねい / おてあらい, no danda)
    _, gray1b = scenario_vertical(ns, t_s003, "S1b_vertical_fallback_OK_S003text", out_dir, fallback_exists=True)
    size1b, runs1b, v1b = classify_runs(ns, gray1b, t_s003, fonts_dir)
    report["scenarios"]["S1b_vertical_fallback_OK_S003text"] = {
        "fitted_size": size1b, "runs": len(runs1b), "verdicts": v1b}
    print("── S1b same, S003 R1 text (pure kana runs, no danda) ──")
    print(f"  fitted_size={size1b}, main(Bengali) runs={v1b['main_runs']}, fallback runs={len(v1b['fallback_runs'])}")
    for v in v1b["fallback_runs"]:
        print(f"  run {v['run'][:10]!r:14} routed={v['routed']} size={v['size']} "
              f"jp_ref={v['score_jp_ref']} bengali_ref={v['score_bengali_ref']} {v['note']}")

    # S2: fallback file missing (simulated download failure)
    _, gray2 = scenario_vertical(ns, t_s007, "S2_vertical_fallback_MISSING", out_dir, fallback_exists=False)
    size2, runs2, v2 = classify_runs(ns, gray2, t_s007, fonts_dir)
    report["scenarios"]["S2_vertical_fallback_MISSING"] = {
        "fitted_size": size2, "runs": len(runs2), "verdicts": v2}
    print("\n── S2 vertical + fallback MISSING (silent get_font_fb degrade) ──")
    print(f"  fitted_size={size2}, main(Bengali) runs={v2['main_runs']}, fallback runs={len(v2['fallback_runs'])}")
    for v in v2["fallback_runs"]:
        print(f"  run {v['run'][:10]!r:14} routed={v['routed']} size={v['size']} "
              f"jp_ref={v['score_jp_ref']} bengali_ref={v['score_bengali_ref']} {v['note']}")

    # S3: horizontal path (cell-10 base, no fallback at all) — S007 text (kana + danda)
    _, gray3 = scenario_horizontal(ns, t_s007, "S3_horizontal_base", out_dir)
    hsize, hlines, h = ns["fit_font_size"](t_s007, 660, 160, bold=False, padding=None)
    hv = []
    for ch, fname in [("こ", "NotoSansJP.ttf"), ("こ", "NotoSansBengali-Regular.ttf"),
                      ("।", "NotoSansJP.ttf"), ("।", "NotoSansBengali-Regular.ttf")]:
        ref, mask, met = ref_bitmap(ch, fonts_dir / fname, hsize, wght=None, stroke=0)
        if ref is None:
            continue
        s, pos = ncc_match(gray3, ref)
        hv.append({"char": ch, "ref_font": fname, "ncc": round(s, 3), "pos": pos})
    report["scenarios"]["S3_horizontal_base"] = {"fitted_size": hsize, "lines": len(hlines), "matches": hv}
    print("\n── S3 horizontal base path (cell-10 only, S007 text) ──")
    for v in hv:
        print(f"  char {v['char']!r} ref={v['ref_font']}: ncc={v['ncc']} @ {v['pos']}")

    # S4: danda-only control — classify_runs on the vertical canvas (position-
    # windowed, scaled-size refs); horizontal control = full-canvas dual ref.
    t_ctl = "বাংলা বাক্য।"
    _, gray4v = scenario_vertical(ns, t_ctl, "S4a_danda_vertical", out_dir, fallback_exists=True)
    _, gray4h = scenario_horizontal(ns, t_ctl, "S4b_danda_horizontal", out_dir)
    _, _, v4v = classify_runs(ns, gray4v, t_ctl, fonts_dir)
    hsize_ctl, _, _ = ns["fit_font_size"](t_ctl, 660, 160, bold=False, padding=None)
    hv4 = {}
    for fname in ("NotoSansJP.ttf", "NotoSansBengali-Regular.ttf"):
        ref, _, _ = ref_bitmap("।", fonts_dir / fname, hsize_ctl, wght=None, stroke=0)
        if ref is None:
            continue
        s, pos = ncc_match(gray4h, ref)
        hv4[fname] = round(s, 3)
    v4 = {"vertical_classify": v4v,
          "horizontal": {"ref_px": hsize_ctl, "jp_notdef_ncc": hv4.get("NotoSansJP.ttf"),
                          "bengali_danda_ncc": hv4.get("NotoSansBengali-Regular.ttf")}}
    report["scenarios"]["S4_danda_control"] = v4
    print("\n── S4 danda-only control ──")
    print("  vertical (classify_runs):")
    for v in v4v["fallback_runs"]:
        print(f"    run {v['run']!r} size={v['size']} jp_ref={v['score_jp_ref']} "
              f"bengali_ref={v['score_bengali_ref']} {v['note']}")
    print(f"  horizontal: {v4['horizontal']}")

    # X: archived cross-check
    print("\n── X archived-crop cross-check (JP .notdef । template, multi-scale) ──")
    xres = archived_cross_check(fonts_dir, out_dir)
    report["archived_cross_check"] = xres
    for tag, r in xres.items():
        print(f"  {tag}: {r}")

    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"\nreport -> {out_dir / 'report.json'}")


def met_ok(m):
    return isinstance(m, dict) and m.get("ink", 0) > 0


if __name__ == "__main__":
    main()
