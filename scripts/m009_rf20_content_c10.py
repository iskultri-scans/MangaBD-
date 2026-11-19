#!/usr/bin/env python3
r"""MANGABD-009 RF-20 — cell-10 patch content (FIX A + FIX B).

Anchored string pairs, verbatim from the 7d0a58e cell-10 source.
FIX A (containment dedup): P1 helper+census before render_page, P2
pre-render row-group scan, P3 row-level skip, P4 meta disclosure.
FIX B (ghost): P5 helper, P6 canvas wipe before the primary render,
P6B per-page list init, P6C meta disclosure.
Test 26 lives in m009_rf20_content_t26.py (P7).

Patch application order (build driver): P1, P5, P2, P6B, P3, P6,
P4, P6C, P7. P1/P5 share the same base anchor (both end by
re-emitting it); P6B anchors text re-emitted by P2; P6C anchors
text created by P4 — sequential replace keeps each unique.
"""

# ── FIX A P1: containment-dedup helpers + census (before render_page)
C10_P1_OLD = """def render_page(page_id, force=False):
    \"\"\"
    একটা page-এর final Bengali image render করে।
"""

C10_P1_NEW = """# MANGABD-009 RF-20 (Owner fast targeted — live merged-main 7d0a58e,
# page 07.jpg, 29 regions: Bengali-on-Bengali double text): detector
# একই bubble-এর জন্য whole-bubble region আর line-fragment region
# দুটোই দেয় (owner dump pairs (4,5)(7,8)(16,17)(20,21)); দুটোই
# translation পায়, দুটোই render হয়। IoU NMS এগুলো ধরতে পারে না —
# (4,5) IoU=0.298, (7,8) IoU=0.116, দুটোই dedupe_iou_threshold-এর
# নিচে। এই corpus-এর আইন তাই containment, overlap নয়: fragment-এর
# centroid whole-এর bbox-এর ভেতরে AND area < 0.5×whole AND
# IoU > 0.1 — তিনটাই মিললে fragment-এর render row চাপা পড়ে (whole
# থাকে); একটাও না মিললে আগের exact পথ। ছয় committed archive-এ
# এই আইনে একটাও pair নেই (zero false suppression, প্রতিটাতেই
# সংলগ্ন/পার্শ্ববর্তী bubble-র centroid অন্যের bbox-এর বাইরে বা
# area-ratio অর্ধেকের বেশি)।
_RF20_AREA_RATIO = 0.5
_RF20_MIN_IOU = 0.1

# RF-20 fire census (namespace-level, _RF19_GUARD_FIRES-এর প্যাটার্ন):
# battery Test 26-এর blast-radius freeze।
_RF20_DEDUP_FIRES = []
_RF20_GHOST_FIRES = []


def _rf20_pair_law(box_a, box_b):
    \"\"\"RF-20: (A=whole, B=fragment) containment রায়। True হলে B
    চাপা পড়ে: centroid(B) ∈ bbox(A) AND area(B) < 0.5×area(A)
    AND IoU(A,B) > 0.1।\"\"\"
    ax, ay, aw, ah = box_a
    bx, by, bw, bh = box_b
    if aw <= 0 or ah <= 0 or bw <= 0 or bh <= 0:
        return False
    a_area = float(aw * ah)
    b_area = float(bw * bh)
    if b_area >= _RF20_AREA_RATIO * a_area:
        return False
    ix = max(0, min(ax + aw, bx + bw) - max(ax, bx))
    iy = max(0, min(ay + ah, by + bh) - max(ay, by))
    inter = float(ix * iy)
    if inter <= 0:
        return False
    union = a_area + b_area - inter
    if union <= 0 or inter / union <= _RF20_MIN_IOU:
        return False
    cx = bx + bw / 2.0
    cy = by + bh / 2.0
    return (ax <= cx <= ax + aw) and (ay <= cy <= ay + ah)


def _rf20_suppressed_regions(page_rows):
    \"\"\"RF-20: এই page-এর render-eligible row-দের ভেতরের
    containment-fragment id → whole-id map। শুধু সেই row-রাই দেখে
    যারা এখনই render হতে যাচ্ছে (non-empty translation +
    non-marker + Bengali-valid + w,h >= 5) — বাকিগুলো নিজেরাই নিচে
    skip হয়, dedup তাদের নিয়ে ভাবেই না। whole প্রার্থী = আগের id
    (reading order-এ আগে = বড় প্যানেল/whole; tie হলে বড় area)।
    প্রতিটা fragment প্রথম-মেলা whole-এর (সবচেয়ে ছোট id) নাম
    নেয় — deterministic।\"\"\"
    eligible = []
    for _, _r in page_rows.iterrows():
        _txt = str(_r.get("translated_text", "") or "").strip()
        if not _txt:
            continue
        if render_is_special_marker(_txt):
            continue
        if not render_validate_bengali(_txt):
            continue
        _w = int(_r.get("width", 0) or 0)
        _h = int(_r.get("height", 0) or 0)
        if _w < 5 or _h < 5:
            continue
        eligible.append((int(_r.get("id", 0)), (
            int(_r.get("x", 0) or 0), int(_r.get("y", 0) or 0),
            _w, _h)))
    suppressed = {}
    for _i, (_id_b, _box_b) in enumerate(eligible):
        for _j, (_id_a, _box_a) in enumerate(eligible):
            if _i == _j:
                continue
            _a_area = _box_a[2] * _box_a[3]
            _b_area = _box_b[2] * _box_b[3]
            if _id_a > _id_b or (_id_a == _id_b
                                 and _a_area <= _b_area):
                continue
            if _rf20_pair_law(_box_a, _box_b):
                suppressed[_id_b] = _id_a
                break
    return suppressed


def render_page(page_id, force=False):
    \"\"\"
    একটা page-ের final Bengali image render করে।
"""

# ── FIX B P5: ghost-wipe helpers (module scope, after P1 helpers)
C10_P5_OLD = """def render_page(page_id, force=False):
    \"\"\"
    একটা page-ের final Bengali image render করে।
"""

C10_P5_NEW = """# MANGABD-009 RF-20 (Owner live 07.jpg, dark webtoon): inpaint mask
# যখন শুধু spiky সীমানা/line-fragment ঘিরেছিল, region-এর ভেতরের
# original কালি কখনো মোছেইনি — render তার উপরে বসে → আসল লেখার
# ghost ভেতরে থেকে যায়। এই helper-জোড়া: region window-এ আজও
# দাঁড়িয়ে থাকা কালির (background থেকে আলাদা pixel) উপর mask-এর
# (dilated) coverage মাপে; কম হলে (dark/spiky case) mask-কে
# region-এর border-safe ভেতরটা পর্যন্ত বাড়িয়ে canvas-এ সেই অংশ
# bubble-এর নিজের background রঙে ফেরানো হয়। White-bg archive-এ
# কালি থাকেই না (inpaint সব নিয়েছে) → no-op → একটাও byte বদলায়
# না; ঘন art-stroke (hatch/panel রেখা) density-gate-এ বাদ পড়ে।
_RF20_GHOST_COVERAGE = 0.5
_RF20_GHOST_MIN_INK = 40
_RF20_GHOST_MIN_FRAC = 0.015
_RF20_TRIM = 3


def _rf20_original_ink_mask(canvas_pil, x, y, w, h):
    \"\"\"RF-20: render canvas-এর এই region window-এ আজও দাঁড়িয়ে
    থাকা আসল কালি। background = window-এর per-channel median
    (dark bubble হলে সেটাই অন্ধকার); ink = |px-bg| এর L1 >= 60।
    3px border band বাদ (bubble-এর নিজের সীমানা-রেখা/panel edge
    কখনো 'কালি' হিসেবে গোনা হয় না)। Returns (bg_rgb_int32,
    ink_bool_trimmed) বা None।\"\"\"
    try:
        _arr = np.array(canvas_pil)
        _H, _W = _arr.shape[:2]
        _x0, _y0 = max(0, int(x)), max(0, int(y))
        _x1, _y1 = min(_W, int(x) + int(w)), min(_H, int(y) + int(h))
        if _x1 - _x0 < 2 * _RF20_TRIM + 8 \\
                or _y1 - _y0 < 2 * _RF20_TRIM + 8:
            return None
        _win = _arr[_y0:_y1, _x0:_x1]
        _bg = np.median(
            _win.reshape(-1, _win.shape[2]), axis=0).astype(np.int32)
        _dist = np.abs(_win.astype(np.int32) - _bg).sum(axis=2)
        _ink = _dist >= 60
        _ink[:_RF20_TRIM, :] = False
        _ink[-_RF20_TRIM:, :] = False
        _ink[:, :_RF20_TRIM] = False
        _ink[:, -_RF20_TRIM:] = False
        return _bg, _ink
    except Exception:
        return None


def _rf20_expand_mask_region(mask, x, y, w, h, ink):
    \"\"\"RF-20: কালির উপর mask coverage < 0.5 (এবং কালি আসল
    signal: >= 40px AND >= 1.5% window) হলে region-এর border-safe
    ভেতরটা mask-এ যোগ। Returns নতুন mask (bool full-canvas) বা
    None (কিছু বদলানোর মতো নয়)।\"\"\"
    try:
        _m = np.asarray(mask)
        if _m.ndim != 2:
            return None
        _m = _m > 0
        _n_ink = int(ink.sum())
        if _n_ink < _RF20_GHOST_MIN_INK:
            return None
        _win_area = float(ink.shape[0] * ink.shape[1])
        if _n_ink < _RF20_GHOST_MIN_FRAC * _win_area:
            return None
        _k = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (5, 5))
        _md = cv2.dilate(_m.astype(np.uint8) * 255, _k) > 0
        _ys, _xs = np.nonzero(ink)
        if float(_md[_ys, _xs].mean()) >= _RF20_GHOST_COVERAGE:
            return None
        _full = np.zeros_like(_m)
        _x0 = max(0, int(x))
        _y0 = max(0, int(y))
        _x1 = min(_m.shape[1], int(x) + int(w))
        _y1 = min(_m.shape[0], int(y) + int(h))
        if _x1 - _x0 < 2 * _RF20_TRIM + 8 \\
                or _y1 - _y0 < 2 * _RF20_TRIM + 8:
            return None
        _full[_y0 + _RF20_TRIM:_y1 - _RF20_TRIM,
              _x0 + _RF20_TRIM:_x1 - _RF20_TRIM] = True
        _new = _m | _full
        if _new.sum() == _m.sum():
            return None
        return _new
    except Exception:
        return None


def render_page(page_id, force=False):
    \"\"\"
    একটা page-ের final Bengali image render করে।
"""

# ── FIX A P2: pre-render scan after page_rows is built
C10_P2_OLD = """    rendered_count = 0
    skipped_count = 0
    warning_count = 0

    # MANGABD-009 RF-19: এই page-এর tiny-guard fires (meta disclosure)।
    _rf19_fires = []
"""

C10_P2_NEW = """    rendered_count = 0
    skipped_count = 0
    warning_count = 0

    # MANGABD-009 RF-20: pre-render containment dedup — এই page-এর
    # whole+fragment duplicate row-দের fragment-id map (একবারই
    # হিসাব; row loop শুধু সেটা দেখে ছাড়িয়ে যায়)। empty হলে কোনো
    # row-ই বাদ যায় না — ছয় committed archive-এর অবস্থা।
    _rf20_suppressed = _rf20_suppressed_regions(page_rows)
    if _rf20_suppressed:
        for _rf20_fid, _rf20_wid in sorted(_rf20_suppressed.items()):
            _RF20_DEDUP_FIRES.append((page_id, _rf20_fid))
            log_event(
                f"RF-20 whole+fragment dedup: region "
                f"{_rf20_fid} suppressed (inside region "
                f"{_rf20_wid}) — rendered once",
                level="WARN",
                page_id=page_id,
            )
            print(
                f"    ⚠️ RF-20 dedup: region {_rf20_fid} is a "
                f"fragment of region {_rf20_wid} — skipped"
            )

    # MANGABD-009 RF-19: এই page-এর tiny-guard fires (meta disclosure)।
    _rf19_fires = []
"""

# ── FIX B P6B: per-page ghost list init (after P2 re-emits the
#    RF-19 fires line)
C10_P6B_OLD = """    # MANGABD-009 RF-19: এই page-এর tiny-guard fires (meta disclosure)।
    _rf19_fires = []
"""

C10_P6B_NEW = """    # MANGABD-009 RF-19: এই page-এর tiny-guard fires (meta disclosure)।
    _rf19_fires = []

    # MANGABD-009 RF-20: এই page-এর ghost-wipe regions (meta
    # disclosure — শুধু সত্যি wipe হলেই লেখা হয়)।
    _rf20_ghost_regions = []
"""

# ── FIX A P3: row-level skip (after the w<5 guard, before B3 ink)
C10_P3_OLD = """        if w < 5 or h < 5:
            skipped_count += 1
            warning_count += 1
            continue

        # MANGABD-009 B3: এই row-এর inherited ink (knob OFF বা key
"""

C10_P3_NEW = """        if w < 5 or h < 5:
            skipped_count += 1
            warning_count += 1
            continue

        # MANGABD-009 RF-20: whole-bubble region-এর ভেতরের
        # line-fragment row — ওর whole row এই page-এই render হচ্ছে,
        # তাই এটা বাদ (দুবার আঁকা = Bengali-on-Bengali)।
        if region_id in _rf20_suppressed:
            skipped_count += 1
            continue

        # MANGABD-009 B3: এই row-এর inherited ink (knob OFF বা key
"""

# ── FIX B P6: ghost wipe before the primary render call
C10_P6_OLD = """            font_sizes_used.append(int(est_size))

            # MANGABD-009 RF-19: snapshot শুধু area >= 2000px হলে
"""

C10_P6_NEW = """            font_sizes_used.append(int(est_size))

            # MANGABD-009 RF-20: ghost wipe — dark/spiky bubble-এ
            # inpaint mask ভেতরের কালি না মুছলে আসল লেখা রয়ে
            # যায় (render তার উপরে বসে)। চেক: region window-এর
            # বাকি কালির উপর detect-stage mask (dilated) coverage
            # < 0.5 হলে mask-এর ভেতরটা বাড়িয়ে canvas সেখানে
            # bubble-এর background-এ ফেরে। White-bg archive-এ
            # কালি থাকে না → no-op → bytes অপরিবর্তিত; mask
            # artifact না থাকলেও no-op।
            try:
                _rf20_gmask = load_image_artifact(page_id, "mask")
                _rf20_gh = _rf20_original_ink_mask(
                    canvas_pil, int(x), int(y), int(w), int(h))
                if _rf20_gmask is not None and _rf20_gh is not None:
                    _rf20_bg, _rf20_ink = _rf20_gh
                    _rf20_exp = _rf20_expand_mask_region(
                        _rf20_gmask, int(x), int(y), int(w), int(h),
                        _rf20_ink)
                    if _rf20_exp is not None:
                        _rf20_arr = np.array(canvas_pil)
                        _rf20_y0 = max(0, int(y))
                        _rf20_x0 = max(0, int(x))
                        _rf20_win = _rf20_arr[
                            _rf20_y0:_rf20_y0 + int(h),
                            _rf20_x0:_rf20_x0 + int(w)]
                        _rf20_sel = _rf20_exp[
                            _rf20_y0:_rf20_y0 + int(h),
                            _rf20_x0:_rf20_x0 + int(w)]
                        if _rf20_sel.shape[:2] \\
                                == _rf20_win.shape[:2]:
                            _rf20_win[_rf20_sel] = \\
                                _rf20_bg.astype(np.uint8)
                            canvas_pil = PILImage.fromarray(_rf20_arr)
                            warning_count += 1
                            _rf20_ghost_regions.append(int(region_id))
                            _RF20_GHOST_FIRES.append(
                                (page_id, int(region_id)))
                            log_event(
                                f"RF-20 ghost wipe: region "
                                f"{region_id} mask coverage < "
                                f"{_RF20_GHOST_COVERAGE} — interior "
                                f"restored to bubble background",
                                level="WARN",
                                page_id=page_id,
                            )
                            print(
                                f"    ⚠️ RF-20 ghost wipe: region "
                                f"{region_id} (mask coverage low)"
                            )
            except Exception as _rf20_gexc:
                log_event(
                    f"RF-20 ghost check failed "
                    f"[{page_id}:{region_id}]: "
                    f"{str(_rf20_gexc)[:100]} — skipped",
                    level="WARN",
                    page_id=page_id,
                )

            # MANGABD-009 RF-19: snapshot শুধু area >= 2000px হলে
"""

# ── FIX A P4 + FIX B P6C: meta disclosures
C10_P4_OLD = """    if _rf19_fires:
        meta["rf19_tiny_guard"] = {"regions": _rf19_fires}

    # MANGABD-009 B1: per-region smart-fill disclosure (Ruling 4 —
"""

C10_P4_NEW = """    if _rf19_fires:
        meta["rf19_tiny_guard"] = {"regions": _rf19_fires}

    # MANGABD-009 RF-20: dedup disclosure — শুধু সত্যি suppress হলে
    # (healthy page-এর render meta byte-identical — RF-19 law-এর
    # একই প্যাটার্ন)।
    if _rf20_suppressed:
        meta["rf20_dedup"] = {
            "suppressed": sorted(_rf20_suppressed.keys()),
        }

    # MANGABD-009 B1: per-region smart-fill disclosure (Ruling 4 —
"""

C10_P6C_OLD = """    if _rf20_suppressed:
        meta["rf20_dedup"] = {
            "suppressed": sorted(_rf20_suppressed.keys()),
        }
"""

C10_P6C_NEW = """    if _rf20_suppressed:
        meta["rf20_dedup"] = {
            "suppressed": sorted(_rf20_suppressed.keys()),
        }

    # MANGABD-009 RF-20: ghost-wipe disclosure — শুধু সত্যি wipe
    # হলে (white-bg archive: key নেই, meta byte-identical)।
    if _rf20_ghost_regions:
        meta["rf20_ghost_wipe"] = {
            "regions": _rf20_ghost_regions}
"""
