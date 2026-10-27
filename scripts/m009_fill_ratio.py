#!/usr/bin/env python3
"""MANGABD-009 Phase A — fill-ratio measurement instrument (docs+instrument only).

Measures per-bubble text-fill ratios on the ARCHIVED sample runs and
simulates the proposed mask-aware adaptive layout (B1 design) so the
PM/Owner ruling is made on measured numbers, not impressions.

Inputs (read-only, never modified):
  - samples/S003_batch2/            (detections/translation/original/final)
  - S007_mangabd005_02.zip          (repo root; read in-place via zipfile)

What it reports per bubble region:
  artist_fill   original text-block extent / bubble area   (the artist's look)
  final_fill    rendered Bengali ink extent / bubble area  (archived BEFORE,
                measured from final.jpg pixels — ground truth)
  cur_fill      byte-faithful re-run of the current cell-10 fit_font_size
                (deterministic BEFORE; line-box extent / usable area)
  new_fill      simulated mask-aware adaptive layout (B1 core algorithm)
                under caps 48 (current) / 64 / 72 / 96
  cap_bound     True when the fill target is unreachable at the cap
  regression    guards: accepted size >= current size; regions at/above the
                trigger keep the exact current layout (byte-equal decisions)

Definitions (must match the B1 spec):
  bubble area   closed white-interior mask restricted to bbox±8 px
  usable area   bubble mask eroded by the margin band
                (margin = max(3, round(0.03 * min(bbox_w, bbox_h))) px,
                distance-transform >= margin)
  block fill    (max line-box width * total line-box height) / usable area
  extent fill   ink-pixel extent box area / bubble area  (artist/final only)

Font resolution (loud, never silent):
  $M009_BENGALI_FONT > repo assets/fonts/NotoSansBengali* > fonts/ dir >
  ~/.cache/mangabd_m009/ (downloaded once via the cell-4 §8 URL chain +
  jsdelivr mirrors; sha256 recorded in the results JSON). No font -> exit 2.

Run:  python3 scripts/m009_fill_ratio.py [--target 0.85] [--trigger 0.60]
      [--caps 48,64,72,96] [--samples S003,S007] [--out RESULTS.json]
Requires: python3 + Pillow (libraqm), opencv-python, numpy. No torch.
"""
import argparse
import hashlib
import io
import json
import sys
import urllib.request
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent

# ── current production constants (cell 1 L313-332 / cell 10 L60-79) ──
CFG = {
    "font_size_min": 8,
    "font_size_max": 48,
    "font_size_default": 24,
    "line_spacing_factor": 1.18,
    "padding_ratio": 0.08,
}

FONT_URLS = [
    # cell-4 §8 chain (L398-402), then the jsdelivr mirrors (§8.5 pattern)
    "https://github.com/notofonts/bengali/raw/main/fonts/NotoSansBengali/hinted/ttf/NotoSansBengali-Regular.ttf",
    "https://github.com/google/fonts/raw/main/ofl/notosansbengali/static/NotoSansBengali-Regular.ttf",
    "https://github.com/google/fonts/raw/main/ofl/notosansbengali/NotoSansBengali%5Bwdth%2Cwght%5D.ttf",
    "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansbengali/NotoSansBengali%5Bwdth%2Cwght%5D.ttf",
]

SAMPLES = {
    "S003": {"kind": "dir", "path": REPO / "samples" / "S003_batch2"},
    "S007": {"kind": "zip", "path": REPO / "S007_mangabd005_02.zip"},
}

RESULTS_PATH = Path(__file__).resolve().parent / "m009_fill_ratio_results.json"


# ═══════════════════════════════════════════════════════════
# font resolution
# ═══════════════════════════════════════════════════════════

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_font():
    import os
    cands = []
    env = os.environ.get("M009_BENGALI_FONT")
    if env:
        cands.append(Path(env))
    cands += sorted((REPO / "assets" / "fonts").glob("NotoSansBengali*.ttf"))
    cands.append(REPO / "fonts" / "NotoSansBengali-Regular.ttf")
    cache = Path.home() / ".cache" / "mangabd_m009" / "NotoSansBengali-Regular.ttf"
    cands.append(cache)
    for c in cands:
        if c.is_file() and c.stat().st_size > 100_000:
            return c, "local"
    # download once
    cache.parent.mkdir(parents=True, exist_ok=True)
    for url in FONT_URLS:
        try:
            print(f"  ⬇️ font download try: {url[:88]}")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = resp.read()
            if not data.startswith((b"\x00\x01\x00\x00", b"OTTO", b"true")):
                print(f"     not a font ({len(data)} bytes, magic {data[:4]!r}) — next URL")
                continue
            cache.write_bytes(data)
            return cache, url
        except Exception as exc:
            print(f"     failed: {str(exc)[:80]}")
    print("❌ No NotoSansBengali font available — set $M009_BENGALI_FONT")
    sys.exit(2)


# ═══════════════════════════════════════════════════════════
# byte-faithful cell-10 helpers (fit path re-run offline)
# ═══════════════════════════════════════════════════════════

try:
    import regex as _regex

    def grapheme_clusters(word):
        return _regex.findall(r"\X", str(word))
except ImportError:
    def grapheme_clusters(word):
        return list(str(word))


class Fit:
    """Byte-faithful re-implementation of the cell-10 §4-§6 fit path."""

    def __init__(self, font_path):
        self.font_path = str(font_path)
        self._cache = {}
        self._dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))

    def get_font(self, size, bold=False):
        key = (int(size), bool(bold))
        if key not in self._cache:
            self._cache[key] = ImageFont.truetype(self.font_path, key[0])
        return self._cache[key]

    def line_height(self, font):
        # cell 10 get_line_height L421-435
        asc, desc = font.getmetrics()
        return int((asc + desc) * CFG["line_spacing_factor"])

    def measure(self, text, font):
        # cell 10 measure_text L395-418 (textbbox, NOT textlength)
        if not text:
            return 0, 0
        bbox = self._dummy.textbbox((0, 0), str(text), font=font)
        return max(0, bbox[2] - bbox[0]), max(0, bbox[3] - bbox[1])

    def split_long_word(self, word, font, max_width):
        # cell 10 L446-476
        word = str(word)
        w, _ = self.measure(word, font)
        if w <= max_width:
            return [word]
        parts, current = [], ""
        for cluster in grapheme_clusters(word):
            test = current + cluster
            if self.measure(test, font)[0] <= max_width or not current:
                current = test
            else:
                parts.append(current)
                current = cluster
        if current:
            parts.append(current)
        return parts

    def split_text_to_lines(self, text, font, max_width):
        # cell 10 L479-532
        if not text:
            return []
        text = str(text).strip()
        words = text.split()
        lines, current = [], ""
        for word in words:
            if not word:
                continue
            ww, _ = self.measure(word, font)
            if ww > max_width:
                if current:
                    lines.append(current)
                    current = ""
                parts = self.split_long_word(word, font, max_width)
                if len(parts) > 1:
                    lines.extend(parts[:-1])
                    current = parts[-1]
                elif parts:
                    current = parts[0]
                continue
            test = (current + " " + word) if current else word
            if self.measure(test, font)[0] <= max_width:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    def fit_font_size(self, text, tw, th, bold=False, min_size=None,
                      max_size=None, padding=None):
        # cell 10 L543-621
        if not text:
            return CFG["font_size_default"], [], 0
        if min_size is None:
            min_size = CFG["font_size_min"]
        if max_size is None:
            max_size = CFG["font_size_max"]
        if padding is None:
            padding = max(4, int(min(tw, th) * CFG["padding_ratio"]))
        aw = max(10, int(tw) - 2 * padding)
        ah = max(10, int(th) - 2 * padding)
        best_size, best_lines, best_height = min_size, [str(text)], 0
        lo, hi = min_size, max_size
        while lo <= hi:
            mid = (lo + hi) // 2
            font = self.get_font(mid, bold=bold)
            lines = self.split_text_to_lines(text, font, aw)
            total = self.line_height(font) * len(lines)
            mw = max((self.measure(ln, font)[0] for ln in lines), default=0)
            if total <= ah and mw <= aw:
                best_size, best_lines, best_height = mid, lines, total
                lo = mid + 1
            else:
                hi = mid - 1
        if best_height == 0:
            font = self.get_font(min_size, bold=bold)
            best_lines = self.split_text_to_lines(text, font, aw)
            best_height = self.line_height(font) * len(best_lines)
            best_size = min_size
        return best_size, best_lines, best_height

    def block_extent(self, size, lines):
        """max line width x total line-box height (the B1 fill metric)."""
        font = self.get_font(size)
        lh = self.line_height(font)
        mw = max((self.measure(ln, font)[0] for ln in lines), default=0)
        return int(mw), lh * len(lines)


# ═══════════════════════════════════════════════════════════
# bubble geometry (the render-time mask inventory)
# ═══════════════════════════════════════════════════════════

def bubble_interior_mask(gray, x, y, w, h, pad=8, thresh=200):
    """Flood-fill the white interior (the cell-11 _snap_white_box probe set)."""
    H, W = gray.shape
    _, white = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)
    seeds = [(x + w // 2, y + h // 2), (x + w // 2, y + h // 3),
             (x + w // 2, y + 2 * h // 3), (x + w // 3, y + h // 2),
             (x + 2 * w // 3, y + h // 2)]
    best = None
    for (px, py) in seeds:
        px, py = max(0, min(W - 1, px)), max(0, min(H - 1, py))
        if white[py, px] == 0:
            continue
        ff = np.zeros((H + 2, W + 2), np.uint8)
        comp = cv2.floodFill(white.copy(), ff, (px, py), 128)[1]
        comp = (comp == 128).astype(np.uint8) * 255
        # close text holes so area/rows describe the INTERIOR, not ink holes
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        comp = cv2.morphologyEx(comp, cv2.MORPH_CLOSE, k)
        keep = np.zeros_like(comp)
        y1, y2 = max(0, y - pad), min(H, y + h + pad)
        x1, x2 = max(0, x - pad), min(W, x + w + pad)
        keep[y1:y2, x1:x2] = comp[y1:y2, x1:x2]
        area = int((keep > 0).sum())
        if best is None or area > best[0]:
            best = (area, keep)
    return best[1] if best else None


def usable_rows(mask, x, y, w, h, margin):
    """Per-row usable width profile inside bbox+pad window.

    Returns dict: rel_y (int, row index in the padded window) -> usable width
    of the contiguous mask run containing the row's bbox-center column, minus
    2*margin; rows with no run -> 0. Plus (usable_area, row_min, row_max).
    """
    ys, xs = np.where(mask > 0)
    if not len(ys):
        return None
    y0, y1 = int(ys.min()), int(ys.max())
    cx = x + w // 2
    dist = cv2.distanceTransform((mask > 0).astype(np.uint8), cv2.DIST_L2, 5)
    usable = (dist >= margin)
    usable_area = int(usable.sum())
    widths = {}
    for yy in range(y0, y1 + 1):
        row = usable[yy]
        if not row.any():
            widths[yy - y0] = 0
            continue
        # widest contiguous usable run containing the center column,
        # else the widest run (irregular/thought shapes)
        runs, best_run, cur_start = [], None, None
        xs_row = np.where(row)[0]
        splits = np.where(np.diff(xs_row) > 1)[0]
        starts = [int(xs_row[0])] + [int(xs_row[i + 1]) for i in splits]
        ends = [int(xs_row[i]) for i in splits] + [int(xs_row[-1])]
        for s, e in zip(starts, ends):
            if s <= cx <= e:
                best_run = (s, e)
        if best_run is None:
            s, e = max(zip(starts, ends), key=lambda se: se[1] - se[0])
            best_run = (s, e)
        widths[yy - y0] = max(0, best_run[1] - best_run[0] + 1)
    return {"widths": widths, "y0": y0, "y1": y1,
            "usable_area": usable_area, "n_rows": y1 - y0 + 1}


# ═══════════════════════════════════════════════════════════
# B1 core: mask-aware adaptive layout (design simulation)
# ═══════════════════════════════════════════════════════════

def mask_aware_layout(fit, text, profile, size, center_col_bias=True):
    """Greedy sequential variable-width wrap against the row-band profile.

    Line i's allowed width = min usable width across the rows its line box
    will occupy. Placement is vertically centered on the usable row span,
    then refined once (<=2 outer iterations). Ellipse poles naturally get
    shorter lines; the equator gets the widest line.
    Returns (lines, block_w, block_h, feasible, rows_used).
    """
    font = fit.get_font(size)
    lh = fit.line_height(font)
    widths, y0, y1 = profile["widths"], profile["y0"], profile["y1"]
    n_rows = profile["n_rows"]
    max_w = max(widths.values()) if widths else 0
    if max_w <= 0 or lh <= 0:
        return None

    # initial line count estimate: wrap to the max width
    est = fit.split_text_to_lines(text, font, max_w)
    for _ in range(2):
        n = max(1, len(est))
        th = lh * n
        top = y0 + max(0, (n_rows - th) // 2)
        lines, placed, ok = [], [], True
        remaining = str(text).strip().split()
        i = 0
        while i < len(remaining) or (placed and len(lines) < n and False):
            if not remaining and not placed:
                break
            band_top = top + len(lines) * lh
            band_rows = range(band_top - y0, band_top - y0 + lh)
            bw = min((widths.get(r, 0) for r in band_rows), default=0)
            if bw <= 0:
                ok = False
                break
            # greedy fill this band
            cur = ""
            while remaining:
                nxt = (cur + " " + remaining[0]) if cur else remaining[0]
                if fit.measure(nxt, font)[0] <= bw or not cur:
                    # single word wider than band -> long-word split
                    if not cur and fit.measure(remaining[0], font)[0] > bw:
                        parts = fit.split_long_word(remaining[0], font, bw)
                        cur = parts[0]
                        remaining = [ " ".join(parts[1:])] + remaining[1:]
                        remaining[0] = remaining[0].strip() or None
                        remaining = [r for r in remaining if r]
                        break
                    cur = nxt
                    remaining.pop(0)
                else:
                    break
            if not cur:
                ok = False
                break
            if fit.measure(cur, font)[0] > bw:
                ok = False
                break
            lines.append(cur)
            if band_top + lh - y0 > n_rows:
                ok = False
                break
            if not remaining:
                break
        if not ok or not lines:
            est = fit.split_text_to_lines(text, font, max_w)
            continue
        if len(lines) == n or _ == 1:
            break
        est = lines
    if not lines or not ok:
        return None
    bw_max = max(fit.measure(ln, font)[0] for ln in lines)
    total = lh * len(lines)
    if top + total - y0 > n_rows:
        return None
    return lines, int(bw_max), total, True, (top, top + total)


def adaptive_fill(fit, text, profile, usable_area, current_size,
                  target, trigger, cap, tol=0.03):
    """The B1 decision ladder, per region.

    1. cur layout (byte-faithful fit_font_size at the bbox) -> cur_fill
    2. cur_fill >= trigger  -> keep EXACT current layout (no change)
    3. else search s = cap .. current_size (monotone: never below current):
       mask-aware layout; feasible + fill <= target+tol -> accept (largest s)
    4. nothing feasible    -> keep current layout
    """
    size, lines, th = fit.fit_font_size(text, profile["bbox_w"], profile["bbox_h"])
    cur_w, cur_h = fit.block_extent(size, lines)
    cur_fill = (cur_w * cur_h) / max(1, usable_area)
    result = {
        "current_size": size, "current_lines": len(lines),
        "current_fill": round(cur_fill, 4),
        "new_size": size, "new_lines": len(lines),
        "new_fill": round(cur_fill, 4), "activated": False,
        "cap_bound": False, "kept_current": cur_fill < trigger,
    }
    if cur_fill >= trigger:
        return result
    best = None
    s = cap
    while s >= size:
        lay = mask_aware_layout(fit, text, profile, s)
        if lay:
            lines_s, w_s, h_s, _, _ = lay
            fill_s = (w_s * h_s) / max(1, usable_area)
            if fill_s <= target + tol:
                best = (s, lines_s, w_s, h_s, fill_s)
                break
        s -= 1
    if best:
        s, lines_s, w_s, h_s, fill_s = best
        result.update({
            "new_size": s, "new_lines": len(lines_s),
            "new_fill": round(fill_s, 4), "activated": True,
            "cap_bound": fill_s < target - tol,
        })
        if s < size:  # monotonicity guard (must never happen)
            result["regression"] = True
    else:
        result["kept_current"] = True
    result.setdefault("regression", False)
    return result


# ═══════════════════════════════════════════════════════════
# sample loading
# ═══════════════════════════════════════════════════════════

def load_member(kind, path, name):
    if kind == "dir":
        p = path / name
        return cv2.imread(str(p)) if name.endswith((".jpg", ".png")) \
            else json.loads(p.read_text())
    with open(path, "rb") as zf:
        data = zf.read() if False else None
    import zipfile
    with zipfile.ZipFile(path) as z:
        member = [n for n in z.namelist() if n.endswith("/" + name) or n == name][0]
        raw = z.read(member)
    if name.endswith((".jpg", ".png")):
        arr = np.frombuffer(raw, np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_UNCHANGED if name.endswith(".png") else cv2.IMREAD_COLOR)
    return json.loads(raw.decode())


# ═══════════════════════════════════════════════════════════
# main
# ═══════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", type=float, default=0.85)
    ap.add_argument("--trigger", type=float, default=0.60)
    ap.add_argument("--caps", default="48,64,72,96")
    ap.add_argument("--samples", default="S003,S007")
    ap.add_argument("--out", default=str(RESULTS_PATH))
    args = ap.parse_args()
    caps = [int(c) for c in args.caps.split(",")]

    print("MANGABD-009 Phase A — fill-ratio instrument")
    font_path, font_src = resolve_font()
    font_sha = sha256_file(font_path)
    print(f"  font: {font_path} ({font_src})")
    print(f"  sha256: {font_sha}")
    fit = Fit(font_path)

    results = {
        "instrument": "scripts/m009_fill_ratio.py",
        "notebook_md5_at_design": "9deaa3a622048d4b763c93839335220d",
        "font": {"path": str(font_path), "sha256": font_sha, "source": font_src},
        "config": {"target": args.target, "trigger": args.trigger,
                    "caps": caps, "prod_cfg": CFG},
        "regions": [],
    }

    for sid in args.samples.split(","):
        spec = SAMPLES[sid]
        kind, base = spec["kind"], spec["path"]
        det = load_member(kind, base, "detections.json")
        tr = load_member(kind, base, "translation.json")
        rows = tr if isinstance(tr, list) else tr.get("rows", tr.get("regions", []))
        tr_by_id = {int(r["id"]): r for r in rows}
        img = load_member(kind, base, "original.jpg")
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        final = load_member(kind, base, "final.jpg")
        fgray = cv2.cvtColor(final, cv2.COLOR_BGR2GRAY)
        print(f"\n===== {sid} =====")
        hdr = (f"{'R':>3} {'bbox':>10} {'cur':>4} {'curFill':>8} "
               + "".join(f"{'@'+str(c):>8}" for c in caps) + "  artist  final  act")
        print(hdr)

        for r in det:
            if r["region_type"] == "overlay":  # V-3 vertical path — out of B1 scope
                continue
            rid = r["id"]
            x, y, w, h = r["x"], r["y"], r["width"], r["height"]
            text = str(tr_by_id[rid].get("translated_text", "")).strip()
            if not text or w < 5 or h < 5:
                continue
            bm = bubble_interior_mask(gray, x, y, w, h)
            if bm is None:
                print(f"R{rid:<2} {w:>4}x{h:<5} — no bubble interior (skip)")
                continue
            margin = max(3, round(0.03 * min(w, h)))
            prof = usable_rows(bm, x, y, w, h, margin)
            if prof is None or prof["usable_area"] <= 0:
                continue
            prof["bbox_w"], prof["bbox_h"] = w, h
            bub = bm > 0
            bub_area = int(bub.sum())
            # artist + final extent fills (reference / ground truth)
            def extent_fill(mask2d):
                ys, xs = np.where(mask2d)
                if not len(ys):
                    return None
                return (xs.max() - xs.min() + 1) * (ys.max() - ys.min() + 1) / bub_area
            artist_fill = extent_fill((gray < 100) & bub)
            final_fill = extent_fill((fgray < 100) & bub)
            # adaptive fill under each cap
            per_cap, row = {}, None
            for cap in caps:
                res = adaptive_fill(fit, text, prof, prof["usable_area"],
                                   None, args.target, args.trigger, cap)
                per_cap[cap] = res
                if cap == caps[0]:
                    row = res
            cells = "".join(f"{per_cap[c]['new_fill']:>8.3f}" for c in caps)
            act = "A" if per_cap[caps[0]]["activated"] else "-"
            print(f"R{rid:<2} {w:>4}x{h:<5} {row['current_size']:>4} "
                  f"{row['current_fill']:>8.3f} {cells} "
                  f"{artist_fill:>7.3f} {final_fill:>6.3f} {act:>3}")
            results["regions"].append({
                "sample": sid, "region_id": rid, "bbox": [x, y, w, h],
                "region_type": r["region_type"],
                "text_len_chars": len(text),
                "bubble_area": bub_area, "usable_area": prof["usable_area"],
                "margin_px": margin,
                "artist_extent_fill": round(artist_fill, 4) if artist_fill else None,
                "final_extent_fill": round(final_fill, 4) if final_fill else None,
                "per_cap": {str(c): per_cap[c] for c in caps},
            })

    # ── synthetic cap-bound demonstration (labeled synthetic) ──
    print("\n----- SYNTHETIC cap demonstration (short text, large bubble) -----")
    print(f"{'case':>28} {'bbox':>10} " + "".join(f"{'@'+str(c):>8}" for c in caps))
    synth_cases = [
        ("short text, large bubble", 380, 320, "কী হয়েছে?"),
        ("medium text, large bubble", 380, 320, "আমি জানি না, তুমি কী বলতে চাও?"),
        ("long text, large bubble", 380, 320,
         "আমি ভেবেছিলাম সে আর কখনো ফিরে আসবে না, কিন্তু আজ সে এখানে দাঁড়িয়ে আছে।"),
    ]
    for label, sw, sh, text in synth_cases:
        yy, xx = np.mgrid[0:sh, 0:sw]
        ellipse = (((xx - sw / 2) / (sw / 2)) ** 2 + ((yy - sh / 2) / (sh / 2)) ** 2) <= 1
        bm = (ellipse * 255).astype(np.uint8)
        margin = max(3, round(0.03 * min(sw, sh)))
        prof = usable_rows(bm, 0, 0, sw, sh, margin)
        prof["bbox_w"], prof["bbox_h"] = sw, sh
        cells = []
        for cap in caps:
            res = adaptive_fill(fit, text, prof, prof["usable_area"],
                                None, args.target, args.trigger, cap)
            cells.append(f"{res['new_fill']:>8.3f}")
        print(f"{label:>28} {sw:>4}x{sh:<5} " + "".join(cells))
        results["regions"].append({
            "sample": "SYNTHETIC", "label": label, "bbox": [0, 0, sw, sh],
            "text": text, "per_cap": {},
            "fills": [adaptive_fill(fit, text,
                                    usable_rows(bm, 0, 0, sw, sh, margin)
                                    | {"bbox_w": sw, "bbox_h": sh},
                                    prof["usable_area"], None,
                                    args.target, args.trigger, c)["new_fill"]
                      for c in caps],
        })

    Path(args.out).write_text(json.dumps(results, indent=1, ensure_ascii=False))
    print(f"\nresults -> {args.out}")

    # ── no-regression verdict ──
    reg = [g for g in results["regions"] if g.get("sample") != "SYNTHETIC"]
    bad = [g for g in reg
           for c, v in g["per_cap"].items() if v.get("regression")]
    kept = [g for g in reg
            for c, v in g["per_cap"].items() if v.get("kept_current")]
    act = [g for g in reg
           for c, v in g["per_cap"].items() if v.get("activated")]
    print(f"\nno-regression: {len(bad) == 0} (monotone size guard: "
          f"{len(bad)} violations); kept-current (fill>=trigger or no "
          f"feasible better): {len(kept)}; activated: {len(act)}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
