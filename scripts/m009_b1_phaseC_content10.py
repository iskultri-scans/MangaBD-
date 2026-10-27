#!/usr/bin/env python3
r"""MANGABD-009 B1 Phase C — patch content, part 1 (cell 10: config + N-1 + B1 engine).

Owner/PM ruling @ Phase A d394947 (4 rulings, relayed zai-web 2026-10-27):
  R1  batch sequence B1 -> B2 -> B3 (this commit = B1)
  R2  cap stays 48 (MANGABD-004 calibration preserved)
  R3  under-fill trigger 0.60 (Option A)
  R4  bubble_fill_target 0.85 = MAXIMIZATION GOAL, honest cap_bound fallback

B1 design = Phase A M9-A.1.4 (mask-aware adaptive layout), production port:
  - mask source = the INPAINTED canvas render_page already owns (zero extra
    I/O; text-free interiors flood-fill clean — Phase A M9-A.1.3 measured
    +4.0..+18.9% bubble area vs the original canvas)
  - per-line band widths from the mask (ellipse/narrow-top aware) replace
    fit_font_size's fixed aw = bbox_w - 2*padding rectangle
  - binary search the MAX size under cap 48 s.t. every wrapped line fits its
    band and the block fits the usable vertical extent
  - trigger guard: current block_fill_usable >= 0.60 keeps the EXACT current
    layout (fit_result=None -> render_bengali_text's original internal fit,
    byte-equal decisions on every kept region)
  - guards: accepted size >= current; font_size_min floor; mask empty /
    degenerate / no-white-interior -> current path; V-3 vertical-note
    predicate (w<90 and h>2*max(1,w) and |angle|<=1) guarded OUT (those
    regions belong to the cells-11/12 vertical renderer, B1 never touches)
  - N-1 (Phase A M9-A.4): get_font's silent ImageFont.load_default() arm is
    now loud (once-per-process WARN print + log_event ERROR) — the D-4
    WARN-never-silent philosophy applied to the main font.

Every OLD string below is unique-asserted against cell 10 @ d394947 by the
build driver (scripts/m009_b1_phaseC_build.py).
"""

# ── P1: §2 rendering config — B1 knobs (Rulings 2/3/4) ────────────────
C10_CFG_OLD = """MANGABD_CONFIG["rendering"].setdefault("font_size_min", 8)
MANGABD_CONFIG["rendering"].setdefault("font_size_max", 48)
MANGABD_CONFIG["rendering"].setdefault("font_size_default", 24)
MANGABD_CONFIG["rendering"].setdefault("line_spacing_factor", 1.18)
MANGABD_CONFIG["rendering"].setdefault("padding_ratio", 0.08)"""

C10_CFG_NEW = """MANGABD_CONFIG["rendering"].setdefault("font_size_min", 8)
MANGABD_CONFIG["rendering"].setdefault("font_size_max", 48)
MANGABD_CONFIG["rendering"].setdefault("font_size_default", 24)
MANGABD_CONFIG["rendering"].setdefault("line_spacing_factor", 1.18)
MANGABD_CONFIG["rendering"].setdefault("padding_ratio", 0.08)

# MANGABD-009 B1 (Phase C @ ruling d394947): smart bubble fill — mask-aware
# adaptive layout। Ruling-approved: trigger 0.60 (R3 Option A), cap 48
# অপরিবর্তিত (R2 — MANGABD-004 calibration), target 0.85 সর্বোচ্চ-সাধ্য-
# লক্ষ্য, গ্যারান্টি নয় (R4)। bubble_fill_enable = kill-switch: False করলে
# পুরো path বন্ধ, প্রতিটা region আগের exact fit_font_size পায়। (Phase A
# M9-A.1.6-এর "default OFF" preview ছিল ruling-পূর্ব নিরাপত্তা-ভঙ্গি;
# ruling এই প্যারামিটারগুলোকে production মান হিসেবে approve করায় path
# default-এ চালু — নাহলে Owner live gate কোনো উন্নতিই দেখতেন না।)
MANGABD_CONFIG["rendering"].setdefault("bubble_fill_enable", True)
MANGABD_CONFIG["rendering"].setdefault("bubble_fill_trigger", 0.60)
MANGABD_CONFIG["rendering"].setdefault("bubble_fill_target", 0.85)
MANGABD_CONFIG["rendering"].setdefault("bubble_fill_margin_ratio", 0.03)
MANGABD_CONFIG["rendering"].setdefault("bubble_fill_region_types",
                                       ["bubble", "thought"])
MANGABD_CONFIG["rendering"].setdefault("bubble_fill_max_rounds", 8)"""

# ── P2: §2 config print — smart-fill line ──────────────────────────────
C10_CFGPRINT_OLD = """print(f"     Grapheme wrap: {MANGABD_CONFIG['rendering']['use_grapheme_safe_wrap']}")
print(f"     BG color     : {MANGABD_CONFIG['rendering']['use_background_aware_color']}")
print()"""

C10_CFGPRINT_NEW = """print(f"     Grapheme wrap: {MANGABD_CONFIG['rendering']['use_grapheme_safe_wrap']}")
print(f"     BG color     : {MANGABD_CONFIG['rendering']['use_background_aware_color']}")
print(f"     Smart fill   : enable={MANGABD_CONFIG['rendering']['bubble_fill_enable']} "
      f"trigger={MANGABD_CONFIG['rendering']['bubble_fill_trigger']} "
      f"cap={MANGABD_CONFIG['rendering']['font_size_max']}")
print()"""

# ── P3: N-1 — get_font silent degradation hole made loud ─────────────
C10_N1_OLD = """_FONT_CACHE = {}


def get_font(size, bold=False):
    \"\"\"
    Font load করে, cache সহ।
    \"\"\"

    size = int(size)
    bold = bool(bold)

    key = (size, bold)

    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    regular_path = MANGABD_CONFIG["rendering"].get("font_regular", "")
    bold_path = MANGABD_CONFIG["rendering"].get("font_bold", "")

    path = regular_path

    if bold and bold_path:
        try:
            if Path(bold_path).exists():
                path = bold_path
        except Exception:
            path = regular_path

    try:
        font = ImageFont.truetype(path, size)
    except Exception:
        try:
            font = ImageFont.truetype(regular_path, size)
        except Exception:
            font = ImageFont.load_default()

    _FONT_CACHE[key] = font

    return font"""

C10_N1_NEW = """_FONT_CACHE = {}
# MANGABD-009 B1 (N-1): main font-এর silent degradation একবারই WARN করবে —
# per-process one-shot latch (D-4 WARN-never-silent philosophy, main-font arm)।
_FONT_DEGRADE_WARNED = {}


def get_font(size, bold=False):
    \"\"\"
    Font load করে, cache সহ।
    \"\"\"

    size = int(size)
    bold = bool(bold)

    key = (size, bold)

    if key in _FONT_CACHE:
        return _FONT_CACHE[key]

    regular_path = MANGABD_CONFIG["rendering"].get("font_regular", "")
    bold_path = MANGABD_CONFIG["rendering"].get("font_bold", "")

    path = regular_path

    if bold and bold_path:
        try:
            if Path(bold_path).exists():
                path = bold_path
        except Exception:
            path = regular_path

    try:
        font = ImageFont.truetype(path, size)
    except Exception:
        try:
            font = ImageFont.truetype(regular_path, size)
        except Exception as exc:
            # MANGABD-009 B1 (N-1, Phase A M9-A.4): আর চুপচাপ নয়। Corrupt /
            # HTML / missing font file আগে নীরবে PIL bitmap default-এ নেমে
            # যেত (বাংলা tofu/blank, শূন্য diagnostic)। এখন একবার loud WARN +
            # log_event ERROR, তারপর আগের মতোই load_default — render বাঁচে,
            # defect লুকায় না।
            if "main_load_default" not in _FONT_DEGRADE_WARNED:
                _FONT_DEGRADE_WARNED["main_load_default"] = True
                print(
                    "⚠️ Main font load failed (" + str(exc)[:80] + ") — "
                    "PIL load_default()-এ নামছি; বাংলা tofu/blank হবে। "
                    "Fix: font_regular path ঠিক করো (Cell 4 §8.6 দেখো)।"
                )
                log_event(
                    "main font load failed — degrading to PIL default "
                    "(Bengali will render as tofu)",
                    level="ERROR",
                )
            font = ImageFont.load_default()

    _FONT_CACHE[key] = font

    return font"""

# ── P4: §6 B1 engine after fit_font_size ─────────────────────────────
C10_ENGINE_OLD = """    # যদি কোনো size fit না করে, min_size-এ render করব
    # Truncation করব না — dialogue কাটা যাবে না
    if best_height == 0:
        font = get_font(min_size, bold=bold)
        best_lines = split_text_to_lines(text, font, draw, available_width)
        best_height = get_line_height(font) * len(best_lines)
        best_size = min_size

    return best_size, best_lines, best_height


print("  ✅ Font fitting ready")"""

C10_ENGINE_NEW = """    # যদি কোনো size fit না করে, min_size-এ render করব
    # Truncation করব না — dialogue কাটা যাবে না
    if best_height == 0:
        font = get_font(min_size, bold=bold)
        best_lines = split_text_to_lines(text, font, draw, available_width)
        best_height = get_line_height(font) * len(best_lines)
        best_size = min_size

    return best_size, best_lines, best_height


# ── MANGABD-009 B1 Phase C: smart bubble fill — mask-aware adaptive layout ──
# Phase A (d394947) M9-A.1.4 design + 4-ruling production parameters।
# fit_font_size bbox-rectangle ধরে শুধু "এঁটে যায়" দেখে — fill বাড়ায় না,
# আর ellipse-এর সরু উপরে/নিচের সারি দেখে না। B1: inpainted canvas থেকে
# bubble mask, তার থেকে per-line band width, তারপর MAX size binary search
# (trigger-এর নিচের under-filled region-গুলোতেই শুধু)। Kept-current region
# এখানে কিছুই বদলায় না — mode "current" ফিরলে render_bengali_text আগের
# exact internal fit_font_size path-ই চালায়।

_B1_PAD = 8  # mask window = bbox ± 8 px (Phase A instrument-এর মান)


def _bubble_interior_mask(image_gray, x, y, w, h, pad=_B1_PAD):
    \"\"\"
    Inpainted canvas-এর white interior flood-fill করে bubble mask।
    Phase A instrument (scripts/m009_b1_fill_measure.py) interior_mask-এর
    production পোর্ট: threshold 200, ৫টা probe seed (center + thirds),
    best-by-area, 9x9 close, bbox±pad window।

    Returns:
        (bubble_mask_bool_fullcanvas, x0, y0, x1, y1) — window কোঅর্ড,
        বা None (সাদা interior পাওয়া যায়নি / degenerate)।
    \"\"\"
    try:
        arr = np.asarray(image_gray)
    except Exception:
        return None
    if arr.ndim == 3:
        try:
            arr = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
        except Exception:
            return None
    if arr.ndim != 2 or arr.size == 0 or w < 5 or h < 5:
        return None

    H, W = arr.shape[:2]
    _, white = cv2.threshold(arr, 200, 255, cv2.THRESH_BINARY)
    seeds = [
        (x + w // 2, y + h // 2),
        (x + w // 2, y + h // 3),
        (x + w // 2, y + 2 * h // 3),
        (x + w // 3, y + h // 2),
        (x + 2 * w // 3, y + h // 2),
    ]
    best = None
    for (px, py) in seeds:
        px = max(0, min(W - 1, px))
        py = max(0, min(H - 1, py))
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
        area = int((keep > 0).sum())
        if best is None or area > best[0]:
            best = (area, keep, x1, y1, x2, y2)
    if best is None or best[0] <= 0:
        return None
    # best = (area, keep_mask, clip_x1, clip_y1, clip_x2, clip_y2) —
    # ফেরত সেটাই (mask, x0, y0, x1, y1): origin আগে, end পরে
    return best[1] > 0, best[2], best[3], best[4], best[5]


def _bubble_band_widths(win, n, lh):
    \"\"\"
    Vertically-centered n-টা line-band-এর প্রতিটার MIN row-span width
    (ellipse / narrow-top aware — fit_font_size-এর fixed aw-এর বদলে)।
    Phase A band_widths-এর পোর্ট, floor 10 px (fit L577) সংরক্ষিত।

    Returns:
        (widths, top_row) — window-কোঅর্ডে ব্লকের top সহ, বা None।
    \"\"\"
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
            rw = int(xs.max() - xs.min() + 1) if len(xs) else 0
            band_w = rw if band_w is None else min(band_w, rw)
        widths.append(max(10, band_w))
    return widths, top


def _wrap_text_to_bands(text, font, draw, widths):
    \"\"\"
    Word-level + grapheme-safe wrap যেখানে line i-এর limit widths[i]।
    Phase A wrap_bands-এর production রূপ: textlength-এর বদলে এই cell-এর
    measure_text, আর char-split-এর বদলে grapheme_clusters (যুক্তাক্ষর/কার
    ভাঙে না — split_long_word discipline)।

    Returns:
        lines list, বা None (band-গুলোতে ধরে না)।
    \"\"\"
    words = str(text).split()
    if not words:
        return None
    lines, cur, i = [], "", 0
    for word in words:
        while True:
            limit = widths[i]
            if cur:
                test = cur + " " + word
                tw, _ = measure_text(test, font, draw)
                if tw <= limit:
                    cur = test
                    break
                lines.append(cur)
                cur = ""
                i += 1
                if i >= len(widths):
                    return None
                continue
            ww, _ = measure_text(word, font, draw)
            if ww <= limit:
                cur = word
                break
            # এক word-ই band-এর চেয়ে চওড়া: grapheme-safe ভাগ
            part = ""
            for cl in grapheme_clusters(word):
                test = part + cl
                tw, _ = measure_text(test, font, draw)
                if tw <= widths[i] or not part:
                    part = test
                else:
                    lines.append(part)
                    i += 1
                    if i >= len(widths):
                        return None
                    part = cl
            cur = part
            break
    if cur:
        lines.append(cur)
    if len(lines) > len(widths):
        return None
    for j, ln in enumerate(lines):
        lw, _ = measure_text(ln, font, draw)
        if lw > widths[j]:
            return None
    return lines


def _mask_aware_fit(text, win, bold=False, min_size=None, max_size=None):
    \"\"\"
    MAX font size খোঁজে যাতে wrapped block প্রতিটা band width + usable
    vertical extent মেনে চলে (binary search, cap = font_size_max — Ruling 2)।
    wrap<->band re-stabilization <= bubble_fill_max_rounds রাউন্ড।
    Phase A mask_aware_fit-এর পোর্ট।

    Returns:
        (size, lines, line_height, top_row, widths) বা None।
    \"\"\"
    cfg = MANGABD_CONFIG["rendering"]
    if min_size is None:
        min_size = int(cfg.get("font_size_min", 8))
    if max_size is None:
        max_size = int(cfg.get("font_size_max", 48))
    rounds = int(cfg.get("bubble_fill_max_rounds", 8))
    rows_any = np.where(win.any(axis=1))[0]
    if len(rows_any) == 0:
        return None
    dummy = PILImage.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)

    def _layout(size):
        font = get_font(size, bold=bold)
        lh = get_line_height(font)
        V = int(rows_any[-1]) - int(rows_any[0]) + 1
        max_lines = max(1, V // lh)
        seed = _bubble_band_widths(win, 1, lh)
        if seed is None:
            return None
        n = 1
        lines = _wrap_text_to_bands(text, font, draw, seed[0])
        if lines:
            n = max(1, len(lines))
        for _ in range(rounds):
            if n > max_lines:
                return None
            bw = _bubble_band_widths(win, n, lh)
            if bw is None:
                return None
            lines = _wrap_text_to_bands(text, font, draw, bw[0])
            if lines is None:
                if (n + 1) <= max_lines:
                    n += 1
                    continue
                return None
            if len(lines) == n:
                return size, lines, lh, bw[1], bw[0]
            n = len(lines)
        return None

    lo, hi = min_size, max_size
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        r = _layout(mid)
        if r is not None:
            best = r
            lo = mid + 1
        else:
            hi = mid - 1
    return best


def bubble_fill_decision(text, x, y, w, h, image_gray=None, bold=False,
                         angle=0.0, region_type="bubble"):
    \"\"\"
    MANGABD-009 B1: একটা region-এর current-vs-mask-aware layout সিদ্ধান্ত।

    Guards (Phase A M9-A.1.4 §6, ক্রমানুসারে):
      disabled / rotated(|angle|>1 — B2-এর জিনিস) / vertical_note (V-3
      predicate, cells-11/12 wrapper-এর একই সূত্র) / region_type অন্য /
      degenerate -> mode "current" (কোনো হিসাবই হয় না);
      তারপর current fit + mask; trigger-এর নেই-ওঠা (>= 0.60) ->
      mode "current" + guard "trigger" (EXACT current layout থাকে);
      mask ফাঁকা -> "mask_empty"; mask fit infeasible -> "infeasible";
      size < current -> "size_guard"। বাকি হলে mode "mask" — সেই layout
      render_bengali_text(fit_result=...) খায়।

    Returns:
        dict — mode "mask" হলে font_size/lines/line_height/start_y/
        band_centers/band_widths + fill metrics; সব ক্ষেত্রেই mode/guard/
        cur_size/cur_block_fill_usable disclosure সহ।
    \"\"\"
    cfg = MANGABD_CONFIG["rendering"]
    out = {"mode": "current", "guard": None, "region_type": region_type}

    if not cfg.get("bubble_fill_enable", True):
        out["guard"] = "disabled"
        return out
    if abs(float(angle)) > 1.0:
        out["guard"] = "rotated"
        return out
    if w < 90 and h > 2 * max(1, w) and abs(float(angle)) <= 1.0:
        # V-3 vertical-note predicate — cells-11/12 wrapper-এর একই সূত্র;
        # ওই region-গুলো vertical renderer-এ যায়, B1-এর এখানে স্থান নেই
        out["guard"] = "vertical_note"
        return out
    allowed = cfg.get("bubble_fill_region_types", ["bubble", "thought"])
    if region_type not in allowed:
        out["guard"] = "region_type"
        return out
    if not text or not str(text).strip() or w < 5 or h < 5:
        out["guard"] = "degenerate"
        return out
    text = str(text).strip()

    # current fit + block metrics — trigger-এর ভিত্তি (render path-এর
    # হুবহু একই fit_font_size, একই default padding)
    cur_size, cur_lines, _ = fit_font_size(text, w, h, bold=bold)
    dummy = PILImage.new("RGB", (1, 1))
    draw = ImageDraw.Draw(dummy)
    cur_font = get_font(cur_size, bold=bold)
    cur_lh = get_line_height(cur_font)
    max_w = 0
    for ln in cur_lines:
        lw, _ = measure_text(ln, cur_font, draw)
        max_w = max(max_w, lw)

    # bubble mask (inpainted canvas) + usable window
    mm = _bubble_interior_mask(image_gray, x, y, w, h)
    if mm is None:
        out["guard"] = "mask_empty"
        out["cur_size"] = int(cur_size)
        out["cur_lines"] = len(cur_lines)
        return out
    bub, x0, y0, x1, y1 = mm
    margin_ratio = float(cfg.get("bubble_fill_margin_ratio", 0.03))
    margin = max(3, int(round(margin_ratio * min(w, h))))
    dist = cv2.distanceTransform(bub.astype(np.uint8), cv2.DIST_L2, 5)
    use = dist >= margin
    usable_area = int(use.sum())
    win = use[y0:y1, x0:x1]
    if usable_area <= 0 or not win.any():
        out["guard"] = "mask_empty"
        out["cur_size"] = int(cur_size)
        out["cur_lines"] = len(cur_lines)
        return out

    cur_block_area = int(max_w) * cur_lh * max(1, len(cur_lines))
    cur_bfu = cur_block_area / float(usable_area)
    out["cur_size"] = int(cur_size)
    out["cur_lines"] = len(cur_lines)
    out["cur_block_fill_usable"] = round(float(cur_bfu), 4)

    trigger = float(cfg.get("bubble_fill_trigger", 0.60))
    if cur_bfu >= trigger:
        out["guard"] = "trigger"
        return out

    r = _mask_aware_fit(text, win, bold=bold)
    if r is None:
        out["guard"] = "infeasible"
        return out
    p_size, p_lines, p_lh, p_top, p_widths = r
    p_font = get_font(p_size, bold=bold)
    p_max_w = 0
    for ln in p_lines:
        lw, _ = measure_text(ln, p_font, draw)
        p_max_w = max(p_max_w, lw)
    p_block_area = int(p_max_w) * p_lh * max(1, len(p_lines))
    p_bfu = p_block_area / float(usable_area)

    if p_size < cur_size:
        out["guard"] = "size_guard"
        out["prop_size"] = int(p_size)
        out["prop_block_fill_usable"] = round(float(p_bfu), 4)
        return out

    # positioning: ব্লক usable extent-এ vertically center (window row
    # p_top -> absolute y), প্রতিটা line নিজ band-এর usable span-এ center
    band_centers = []
    for i in range(len(p_lines)):
        r0 = max(0, min(win.shape[0] - 1, p_top + i * p_lh))
        r1 = max(0, min(win.shape[0] - 1, p_top + (i + 1) * p_lh - 1))
        xs = np.where(win[r0:r1 + 1].any(axis=0))[0]
        if len(xs) == 0:
            band_centers.append(int(x0 + (x1 - x0) // 2))
        else:
            band_centers.append(int(x0 + (int(xs[0]) + int(xs[-1])) // 2))

    out.update({
        "mode": "mask",
        "guard": None,
        "font_size": int(p_size),
        "lines": list(p_lines),
        "line_height": int(p_lh),
        "start_y": int(y0 + p_top),
        "band_centers": band_centers,
        "band_widths": [int(bw) for bw in p_widths],
        "block_fill_usable": round(float(p_bfu), 4),
        "cap_bound": bool(
            p_bfu < float(cfg.get("bubble_fill_target", 0.85))
        ),
        "usable_area": usable_area,
        "margin_px": int(margin),
    })
    return out


print("  ✅ Smart bubble fill (MANGABD-009 B1) ready")


print("  ✅ Font fitting ready")"""
