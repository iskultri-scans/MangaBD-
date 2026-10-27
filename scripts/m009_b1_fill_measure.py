#!/usr/bin/env python3
"""MANGABD-009 Phase A — v2 fill-ratio measurement instrument (docs+instrument ONLY).

Supersedes scripts/m009_fill_ratio.py (v1, left in place as evidence). v1's
numbers were split across incompatible denominators (line-box extent / usable
area vs ink extent / bubble area) and its bubble masks were flood-filled from
the ORIGINAL canvas, where text strokes punch holes in the interior — so the
bubble area came out UNDERSHOT and the ratios were misleading (the v1 "new"
path never activated: new == current everywhere). v2 fixes both defects:

  MASK SOURCE — the INPAINTED canvas (inpainted.png): the exact image
      render_page already loads as its rendering base (cell 10 L1023-1046),
      so a production B1 gets the mask at zero extra I/O. Text-free interiors
      give clean, solid masks. Measured on the archives: bubble area
      +4%..+19% vs the original-canvas mask (R3: 39,210 -> 46,588 px).
  METRICS — one unified family, every ratio against the SAME bubble mask:
      ink_fill     = dark ink pixel count / bubble_area
      extent_fill  = ink extent-box area / bubble_area
      block_fill   = layout block (max line width x total line-box height)
                     / bubble_area ; block_fill_usable = same / usable_area
      artist (original.jpg) / current (final.jpg archive + byte-faithful
      fit_font_size re-sim) / proposed B1 (mask-aware adaptive layout) are
      all reported in these same units — apples to apples.

B1 core algorithm simulated here (design spec; NO notebook changes):
  1. bubble mask = flood-fill interior of the inpainted canvas, bbox+-8 px
  2. usable mask = bubble mask eroded by the margin band
       (margin = max(3, round(0.03 * min(bbox_w, bbox_h))) px)
  3. per-line widths from the mask: line i occupies a vertical band of the
     vertically-centered block; band width = MIN row-span width across the
     band (ellipse / narrow-top aware — the fixed aw = bbox_w - 2*padding of
     fit_font_size L577 is replaced by shape-aware limits)
  4. maximize font size s.t. every line fits its band width and the block
     fits the usable vertical extent (binary search under the cap)
  5. fill target = 0.85 of usable area (rendering.bubble_fill_target,
     proposed); cap_bound = True when even the cap cannot reach it
  6. regression guards: accepted size >= current size; regions whose current
     block_fill_usable >= trigger (0.60) keep the EXACT current layout —
     MANGABD-004 small-bubble calibration untouched

Also measures the SYNTHETIC worst case (short text in a 380x320 ellipse) that
quantifies the Owner's under-fill complaint: current-path fill vs proposed
fill under caps 48/64/72/96/128/160 (v1 measured current = 0.186 @ cap 48).

Font resolution here is LOUD, never silent (the N-1 disclosure): sha256 +
PIL load + tofu-scan of probe glyphs before any measuring. During the probe
session this caught m009_work/fonts/NotoSansBengali-Regular.ttf and -Bold.ttf
being HTML error pages (failed downloads) — only the VF is a real font. That
is exactly the silent-degradation class cell-10 get_font L204-210 hides:
ImageFont.truetype() failure -> ImageFont.load_default(), NO warning, NO
log_event — Bengali would render as bitmap-font tofu/blank.

Inputs (read-only, never modified):
  samples/S003_batch2/            archived run (detections/translation/
                                  original/inpainted/final/text_mask)
  S007_mangabd005_02.zip          repo root, read in-place via zipfile
                                 (same archive m009_work/S007 was unpacked
                                 from for the probe scripts)
  assets/fonts/... is NOT used; the measuring font is m009_work/fonts/
  NotoSansBengali-VF.ttf sha256 dcd42978094e584a849c84a51450eeac40c88260
  7d566ea6d4b9627a403a05a (the same bytes v1 recorded; probe-verified loadable
  and Bengali-complete). Production renders may use a different font file —
  sizes may shift by a px or two, ratios are robust.

Output: printed tables + scripts/m009_b1_fill_measure_results.json.
"""

import hashlib
import json
import zipfile
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[1]
OUT_JSON = REPO / "scripts" / "m009_b1_fill_measure_results.json"
NOTEBOOK = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
S003_DIR = REPO / "samples" / "S003_batch2"
FONT_PATH = Path("/home/z/my-project/m009_work/fonts/NotoSansBengali-VF.ttf")

# production cell-10 §6 rendering knobs (main @ 5bde06b) — kept byte-faithful
PROD_CFG = {
    "font_size_min": 8,
    "font_size_max": 48,
    "font_size_default": 24,
    "line_spacing_factor": 1.18,
    "padding_ratio": 0.08,
}
# proposed B1 knobs under ruling (NOT production — this is the Phase A design)
B1_CFG = {
    "bubble_fill_target": 0.85,   # of usable area
    "underfill_trigger": 0.60,    # current block_fill_usable at/above -> keep current
    "margin_ratio": 0.03,         # usable-area erosion band
    "caps": [48, 64, 72, 96, 128, 160],
}
SYNTH = {"w": 380, "h": 320, "text": "কী হয়েছে?"}

_font_cache = {}
_draw = ImageDraw.Draw(Image.new("RGB", (1, 1)))


# ── loud font resolution (N-1: never silent) ─────────────────────────
def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def probe_font(path):
    """Loud font validation: PIL load + ink scan of Bengali + danda probes."""
    try:
        f = ImageFont.truetype(str(path), 40)
    except Exception as exc:
        raise RuntimeError(f"FONT LOAD FAILED {path}: {exc!r}") from exc
    missing = []
    for ch in "কািী।ক্য":  # consonant, matra, i-sign, danda, cluster
        img = Image.new("L", (60, 60), 255)
        ImageDraw.Draw(img).text((4, 4), ch, font=f, fill=0)
        if int((np.asarray(img) < 128).sum()) == 0:
            missing.append(ch)
    if missing:
        raise RuntimeError(f"FONT TOFU for probes {missing!r}: {path}")
    return f


def get_font(size):
    if size not in _font_cache:
        _font_cache[size] = ImageFont.truetype(str(FONT_PATH), int(size))
    return _font_cache[size]


def line_height(font):
    a, d = font.getmetrics()
    return int((a + d) * PROD_CFG["line_spacing_factor"])


# ── bubble geometry from the INPAINTED canvas ─────────────────────────
def interior_mask(gray, x, y, w, h, pad=8):
    """Flood-fill the white interior from bbox probes; keep bbox+pad window."""
    H, W = gray.shape
    _, white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
    seeds = [(x + w // 2, y + h // 2), (x + w // 2, y + h // 3),
             (x + w // 2, y + 2 * h // 3), (x + w // 3, y + h // 2),
             (x + 2 * w // 3, y + h // 2)]
    best = None
    for (px, py) in seeds:
        px, py = max(0, min(W - 1, px)), max(0, min(H - 1, py))
        if white[py, px] == 0:
            continue
        ff = np.zeros((H + 2, W + 2), np.uint8)
        m = cv2.floodFill(white.copy(), ff, (px, py), 128)[1]
        comp = (m == 128).astype(np.uint8) * 255
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (9, 9))
        comp = cv2.morphologyEx(comp, cv2.MORPH_CLOSE, k)
        keep = np.zeros_like(comp)
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(W, x + w + pad), min(H, y + h + pad)
        keep[y1:y2, x1:x2] = comp[y1:y2, x1:x2]
        a = int((keep > 0).sum())
        if best is None or a > best[0]:
            best = (a, keep)
    return best[1] if best else None


def usable_mask(bubble_bool, margin):
    dist = cv2.distanceTransform(bubble_bool.astype(np.uint8), cv2.DIST_L2, 5)
    return dist >= margin


def ink_stats(dark_bool):
    """(ink_px, extent_w, extent_h) of a boolean ink mask."""
    n = int(dark_bool.sum())
    if n == 0:
        return 0, 0, 0
    ys, xs = np.where(dark_bool)
    return n, int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1)


# ── current path: byte-faithful fit_font_size re-sim (cell 10 L543-621) ──
def wrap_flat(text, font, maxw):
    words = str(text).split()
    lines, cur = [], ""
    for word in words:
        wl = _draw.textlength(word, font=font)
        if wl > maxw:
            if cur:
                lines.append(cur)
                cur = ""
            part = ""
            for ch in word:
                t = part + ch
                if _draw.textlength(t, font=font) <= maxw or not part:
                    part = t
                else:
                    lines.append(part)
                    part = ch
            cur = part
            continue
        t = (cur + " " + word) if cur else word
        if _draw.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def current_fit(text, tw, th):
    """fit_font_size: padding -> aw/ah from the BBOX only; binary-search max size."""
    pad = max(4, int(min(tw, th) * PROD_CFG["padding_ratio"]))
    aw, ah = max(10, int(tw) - 2 * pad), max(10, int(th) - 2 * pad)
    bs, bl, bh = PROD_CFG["font_size_min"], [str(text)], 0
    lo, hi = PROD_CFG["font_size_min"], PROD_CFG["font_size_max"]
    while lo <= hi:
        mid = (lo + hi) // 2
        f = get_font(mid)
        ln = wrap_flat(text, f, aw)
        th_ = line_height(f) * len(ln)
        mw = max((_draw.textlength(l, font=f) for l in ln), default=0)
        if th_ <= ah and mw <= aw:
            bs, bl, bh = mid, ln, th_
            lo = mid + 1
        else:
            hi = mid - 1
    if bh == 0:
        f = get_font(PROD_CFG["font_size_min"])
        bl = wrap_flat(text, f, aw)
        bh = line_height(f) * len(bl)
        bs = PROD_CFG["font_size_min"]
    return bs, bl, bh, aw, ah


# ── proposed B1: mask-aware adaptive layout ────────────────────────────
def band_widths(win, n, lh):
    """Widths for n vertically-centered line bands inside the usable window.
    Returns None when the block cannot fit vertically."""
    rows_any = np.where(win.any(axis=1))[0]
    if len(rows_any) == 0:
        return None
    v_top, v_bot = int(rows_any[0]), int(rows_any[-1])
    V = v_bot - v_top + 1
    total = n * lh
    if total > V:
        return None
    top = v_top + (V - total) // 2
    widths = []
    for i in range(n):
        r0, r1 = top + i * lh, top + (i + 1) * lh - 1
        band_w = None
        for r in range(r0, r1 + 1):
            xs = np.where(win[r])[0]
            w = int(xs.max() - xs.min() + 1) if len(xs) else 0
            band_w = w if band_w is None else min(band_w, w)
        widths.append(max(10, band_w))  # production floor (fit L577) preserved
    return widths


def wrap_bands(text, font, widths):
    """Greedy word wrap where line i is limited to widths[i]. None = overflow."""
    words = str(text).split()
    if not words:
        return None
    lines, cur, i = [], "", 0
    for word in words:
        while True:
            limit = widths[i]
            if cur:
                t = cur + " " + word
                if _draw.textlength(t, font=font) <= limit:
                    cur = t
                    break
                lines.append(cur)
                cur = ""
                i += 1
                if i >= len(widths):
                    return None
                continue
            wl = _draw.textlength(word, font=font)
            if wl <= limit:
                cur = word
                break
            # single word wider than the band: grapheme-safe split
            part = ""
            for ch in word:
                t = part + ch
                if _draw.textlength(t, font=font) <= widths[i] or not part:
                    part = t
                else:
                    lines.append(part)
                    i += 1
                    if i >= len(widths):
                        return None
                    part = ch
            cur = part
            break
    if cur:
        lines.append(cur)
    if len(lines) > len(widths):
        return None
    for j, ln in enumerate(lines):
        if _draw.textlength(ln, font=font) > widths[j]:
            return None
    return lines


def mask_aware_fit(text, win, cap, min_size=None):
    """Max size s.t. the wrapped block fits the per-band widths + vertical
    extent of the usable mask. Returns (size, lines, lh) or None."""
    min_size = PROD_CFG["font_size_min"] if min_size is None else min_size
    rows_any = np.where(win.any(axis=1))[0]
    if len(rows_any) == 0:
        return None

    def layout(size):
        f = get_font(size)
        lh = line_height(f)
        V = int(rows_any[-1]) - int(rows_any[0]) + 1
        max_lines = max(1, V // lh)
        # seed with the widest band layout (single band = widest span)
        seed_w = band_widths(win, 1, lh)
        if seed_w is None:
            return None
        lines = wrap_bands(text, f, seed_w)
        n = max(1, len(lines)) if lines else 1
        for _ in range(8):  # stabilize n <-> bands
            if n > max_lines:
                return None
            W = band_widths(win, n, lh)
            if W is None:
                return None
            lines = wrap_bands(text, f, W)
            if lines is None:
                if (n + 1) <= max_lines:
                    n += 1
                    continue
                return None
            if len(lines) == n:
                return size, lines, lh
            n = len(lines)
        return None

    lo, hi = min_size, cap
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        r = layout(mid)
        if r is not None:
            best = r
            lo = mid + 1
        else:
            hi = mid - 1
    return best


# ── rendering the simulated blocks (unified ink metrics) ───────────────
def render_block(lines, size):
    f = get_font(size)
    lh = line_height(f)
    mw = max((_draw.textlength(l, font=f) for l in lines), default=0)
    W, H = max(16, int(mw) + 8), lh * max(1, len(lines)) + 8
    img = Image.new("L", (W, H), 255)
    d = ImageDraw.Draw(img)
    yy = 4
    for ln in lines:
        d.text((4, yy), ln, font=f, fill=0)
        yy += lh
    arr = np.asarray(img)
    ink, ew, eh = ink_stats(arr < 128)
    return {
        "block_w": int(mw), "block_h": int(lh * len(lines)),
        "ink_px": ink, "ink_extent_w": ew, "ink_extent_h": eh,
    }


# ── archive loaders ─────────────────────────────────────────────────────
def load_sample(sid):
    """Returns (detections, translation_rows, images dict of np gray arrays)."""
    if sid == "S003":
        base = S003_DIR
        files = {
            "original": cv2.cvtColor(cv2.imread(str(base / "original.jpg")), cv2.COLOR_BGR2GRAY),
            "inpainted": cv2.cvtColor(cv2.imread(str(base / "inpainted.png")), cv2.COLOR_BGR2GRAY),
            "final": cv2.cvtColor(cv2.imread(str(base / "final.jpg")), cv2.COLOR_BGR2GRAY),
        }
    else:  # S007 from the repo zip, in place
        with zipfile.ZipFile(S007_ZIP) as z:
            def rd(name, gray=True):
                data = z.read(f"S007/{name}" if f"S007/{name}" in z.namelist() else name)
                arr = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                return cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
            files = {"original": rd("original.jpg"), "inpainted": rd("inpainted.png"),
                     "final": rd("final.jpg")}
            det = json.loads(z.read("detections.json" if "detections.json" in z.namelist() else "S007/detections.json"))
            tr = json.loads(z.read("translation.json" if "translation.json" in z.namelist() else "S007/translation.json"))
            rows = tr if isinstance(tr, list) else tr.get("rows", [])
            return det, {int(r["id"]): r for r in rows}, files
    det = json.load(open(base / "detections.json"))
    tr = json.load(open(base / "translation.json"))
    rows = tr if isinstance(tr, list) else tr.get("rows", [])
    return det, {int(r["id"]): r for r in rows}, files


# ── main measurement ────────────────────────────────────────────────────
def measure_region(sid, region, tr_by_id, imgs):
    rid = int(region["id"])
    x, y, w, h = (int(region[k]) for k in ("x", "y", "width", "height"))
    text = str(tr_by_id.get(rid, {}).get("translated_text", "")).strip()
    if not text or w < 5 or h < 5:
        return None

    # 1. bubble mask from the INPAINTED canvas
    mask = interior_mask(imgs["inpainted"], x, y, w, h)
    if mask is None:
        return {"sample": sid, "region_id": rid, "error": "no white interior on inpainted canvas"}
    bub = mask > 0
    bubble_area = int(bub.sum())
    # original-canvas mask for the mask-source evidence block
    mo = interior_mask(imgs["original"], x, y, w, h)
    orig_area = int((mo > 0).sum()) if mo is not None else 0

    # 2. usable mask (margin band erosion)
    margin = max(3, int(round(B1_CFG["margin_ratio"] * min(w, h))))
    use = usable_mask(bub, margin)
    usable_area = int(use.sum())
    x0, y0 = max(0, x - 8), max(0, y - 8)
    x1, y1 = min(mask.shape[1], x + w + 8), min(mask.shape[0], y + h + 8)
    win = use[y0:y1, x0:x1]

    # 3. artist + archived-current ink (same mask, same thresholds)
    art_ink, a_ew, a_eh = ink_stats((imgs["original"] < 100) & bub)
    fin_ink, f_ew, f_eh = ink_stats((imgs["final"] < 100) & bub)

    # 4. current sim (byte-faithful fit_font_size on the bbox)
    c_size, c_lines, c_bh, aw, ah = current_fit(text, w, h)
    c_blk = render_block(c_lines, c_size)
    c_block_area = c_blk["block_w"] * c_blk["block_h"]
    cur = {
        "size": c_size, "lines": len(c_lines), "aw": aw, "ah": ah,
        "block_w": c_blk["block_w"], "block_h": c_blk["block_h"],
        "block_fill": round(c_block_area / bubble_area, 4),
        "block_fill_usable": round(c_block_area / usable_area, 4),
        "ink_fill": round(c_blk["ink_px"] / bubble_area, 4),
        "extent_fill": round(c_blk["ink_extent_w"] * c_blk["ink_extent_h"] / bubble_area, 4),
    }

    # 5. proposed B1 per cap (+ guards)
    triggered = cur["block_fill_usable"] < B1_CFG["underfill_trigger"]
    proposed = {}
    for cap in B1_CFG["caps"]:
        r = mask_aware_fit(text, win, cap)
        if r is None:
            proposed[str(cap)] = {"feasible": False}
            continue
        p_size, p_lines, p_lh = r
        p_blk = render_block(p_lines, p_size)
        p_block_area = p_blk["block_w"] * p_blk["block_h"]
        p_bu = p_block_area / usable_area
        entry = {
            "feasible": True,
            "size": p_size, "lines": len(p_lines),
            "block_w": p_blk["block_w"], "block_h": p_blk["block_h"],
            "block_fill": round(p_block_area / bubble_area, 4),
            "block_fill_usable": round(p_bu, 4),
            "ink_fill": round(p_blk["ink_px"] / bubble_area, 4),
            "extent_fill": round(p_blk["ink_extent_w"] * p_blk["ink_extent_h"] / bubble_area, 4),
            "cap_bound": bool(p_bu < B1_CFG["bubble_fill_target"]),
            "activated": bool(triggered and p_size >= c_size),
            "size_guard_kept_current": bool(p_size < c_size),
        }
        proposed[str(cap)] = entry

    return {
        "sample": sid, "region_id": rid, "region_type": region["region_type"],
        "bbox": [x, y, w, h], "text_len_chars": len(text),
        "orig_canvas_mask_area": orig_area,
        "bubble_area": bubble_area, "usable_area": usable_area, "margin_px": margin,
        "mask_source_gain_pct": round(100.0 * (bubble_area - orig_area) / orig_area, 1) if orig_area else None,
        "artist": {"ink_fill": round(art_ink / bubble_area, 4),
                   "extent_fill": round(a_ew * a_eh / bubble_area, 4)},
        "final_archive": {"ink_fill": round(fin_ink / bubble_area, 4),
                          "extent_fill": round(f_ew * f_eh / bubble_area, 4)},
        "current_sim": cur,
        "underfill_triggered": bool(triggered),
        "proposed": proposed,
    }


def measure_synthetic():
    """Short text in a large 380x320 ellipse: the Owner's complaint quantified."""
    w, h, text = SYNTH["w"], SYNTH["h"], SYNTH["text"]
    yy, xx = np.mgrid[0:h, 0:w]
    ell = (((xx - w / 2 + 0.5) / (w / 2)) ** 2 + ((yy - h / 2 + 0.5) / (h / 2)) ** 2) <= 1.0
    bubble_area = int(ell.sum())
    margin = max(3, int(round(B1_CFG["margin_ratio"] * min(w, h))))
    use = usable_mask(ell, margin)
    usable_area = int(use.sum())

    out = {"bbox": [0, 0, w, h], "text": text, "bubble_area": bubble_area,
           "usable_area": usable_area, "margin_px": margin, "per_cap": {}}

    for cap in B1_CFG["caps"]:
        # current path: bbox-only fit at this cap
        c_size, c_lines, c_bh, aw, ah = current_fit(text, w, h)
        c_blk = render_block(c_lines, c_size)
        c_area = c_blk["block_w"] * c_blk["block_h"]
        # proposed: mask-aware at this cap
        r = mask_aware_fit(text, use, cap)
        if r is None:
            out["per_cap"][str(cap)] = {"current": {"size": c_size, "lines": len(c_lines),
                                                    "block_fill_usable": round(c_area / usable_area, 4)},
                                        "proposed": {"feasible": False}}
            continue
        p_size, p_lines, _ = r
        p_blk = render_block(p_lines, p_size)
        p_area = p_blk["block_w"] * p_blk["block_h"]
        out["per_cap"][str(cap)] = {
            "current": {"size": c_size, "lines": len(c_lines),
                        "block_fill_usable": round(c_area / usable_area, 4),
                        "ink_fill": round(c_blk["ink_px"] / bubble_area, 4)},
            "proposed": {"feasible": True, "size": p_size, "lines": len(p_lines),
                         "block_fill_usable": round(p_area / usable_area, 4),
                         "ink_fill": round(p_blk["ink_px"] / bubble_area, 4),
                         "cap_bound": bool(p_area / usable_area < B1_CFG["bubble_fill_target"])},
        }
    return out


def main():
    font_sha = sha256_file(FONT_PATH)
    probe = probe_font(FONT_PATH)  # loud: raises on silent-degradation class

    results = {
        "instrument": "scripts/m009_b1_fill_measure.py",
        "design": "MANGABD-009 Phase A v2 — inpainted-mask source + unified ink metrics",
        "notebook_md5": sha256_file(NOTEBOOK) if NOTEBOOK.exists() else None,
        "notebook_design_target": "main @ 5bde06b (cell 10 L543-621 fit_font_size; L1023-1046 render_page)",
        "font": {"path": str(FONT_PATH), "sha256": font_sha, "probe": "load+Bengali ink scan OK"},
        "prod_cfg": PROD_CFG, "b1_cfg": B1_CFG,
        "regions": [], "synthetic": None,
    }

    for sid in ("S003", "S007"):
        det, tr_by_id, imgs = load_sample(sid)
        for region in det:
            if region.get("region_type") == "overlay":
                continue
            r = measure_region(sid, region, tr_by_id, imgs)
            if r is not None:
                results["regions"].append(r)

    results["synthetic"] = measure_synthetic()

    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=1, ensure_ascii=False)

    # ── printed report ──
    print("MANGABD-009 Phase A — v2 fill measurement (inpainted mask + unified metrics)")
    print(f"font sha256 {font_sha[:16]}…  notebook md5 {results['notebook_md5']}")
    print(f"bubble mask = inpainted-canvas interior; usable = mask eroded by margin band")
    print(f"target block_fill_usable = {B1_CFG['bubble_fill_target']}; "
          f"underfill trigger = {B1_CFG['underfill_trigger']}\n")

    hdr = (f"{'reg':>9} {'bbox':>9} {'bubA':>6} {'gain%':>6} | {'artist':>13} "
           f"| {'final(arch)':>13} | {'current sim':>26} | proposed@48 / @96 / @160 (size, blkFillU)")
    print(hdr)
    for r in results["regions"]:
        if "error" in r:
            print(f"{r['sample']}-R{r['region_id']}: {r['error']}")
            continue
        art = r["artist"]; fin = r["final_archive"]; cur = r["current_sim"]
        def pc(cap, key):
            e = r["proposed"].get(str(cap), {})
            if not e.get("feasible"):
                return "n/f"
            return f"{e['size']},{e[key]:.3f}" + ("*" if e.get("cap_bound") else "")
        print(f"{r['sample']}-R{r['region_id']:<3} {r['bbox'][2]}x{r['bbox'][3]:<5} "
              f"{r['bubble_area']:>6} {r['mask_source_gain_pct']:>6} | "
              f"ink {art['ink_fill']:.3f} ext {art['extent_fill']:.3f} | "
              f"ink {fin['ink_fill']:.3f} ext {fin['extent_fill']:.3f} | "
              f"sz {cur['size']:>2} ln {cur['lines']} blkU {cur['block_fill_usable']:.3f} "
              f"ink {cur['ink_fill']:.3f} | "
              f"{pc(48, 'block_fill_usable')} / {pc(96, 'block_fill_usable')} / {pc(160, 'block_fill_usable')}"
              + ("" if r["underfill_triggered"] else "  [kept-current: at/above trigger]"))

    print("\nSYNTHETIC under-fill worst case (short text, 380x320 ellipse):")
    sy = results["synthetic"]
    for cap in B1_CFG["caps"]:
        e = sy["per_cap"][str(cap)]
        c, p = e["current"], e["proposed"]
        ps = f"sz {p['size']} blkU {p['block_fill_usable']:.3f} ink {p['ink_fill']:.3f}" \
             + (" [cap-bound]" if p.get("cap_bound") else "") if p.get("feasible") else "infeasible"
        print(f"  cap {cap:>3}: current sz {c['size']} blkU {c['block_fill_usable']:.3f}"
              f"  ->  proposed {ps}")

    print(f"\nresults -> {OUT_JSON}")


if __name__ == "__main__":
    main()
