#!/usr/bin/env python3
"""MANGABD-009 B3.1 Phase A — per-line color inheritance measurement
instrument (docs-only batch; NO source changes).

Owner live-REJECT on B3 @ cf01aef (real colored manhwa page): ALL colored
bubbles rendered black; one 4-line bubble rendered as a single tiny line.
Diagnostic (owner Colab, direct sampling bypassing gates): ink colored and
trivially detectable — region dark-pixel RGB means [38,6,6] red / [18,17,76]
blue / [57,14,112] purple / [28,14,117] blue; sat>0.3 chromatic counts
1k-2.5k px per region; color_inherit_enable=True yet ink_color=None on ALL
colored regions. ROOT CAUSE (design): corpus style = per-word EMPHASIS
coloring (black base + 1-3 chromatic words per bubble) — the region-level
median is black => class black => no key; RB3-5 region gates skip the rest.

This instrument measures, on a deterministic OWNER-GEOMETRY REPLICA +
S012-prototype geometry (workspace-only builder output):

  PART A  B3 behavior reproduction on the replica (live-REJECT root cause:
          region-level sampler returns no key on every emphasis region) +
          B2 orientation behavior on emphasis ink (spurious-angle check —
          the bridge to the tiny-text quad hypotheses).
  PART B  The PROPOSED per-line color law (line bands via row-profile of
          the undilated ink mask; per-line chromatic-cluster law; region
          base fallback) — per-line recovery vs builder GT, tau sweep
          0.10/0.20/0.30/0.50, false-color check on all-black lines,
          band-split fidelity close(5,5)x2-bridged vs raw-threshold mask.
  PART C  Tiny-text reproduction matrix: render_page (B3-tip bytes, cells
          01-07+10+11+12 VERBATIM, the disclosed harness stub set) on
          controlled geometries V0..V5 — which mechanism renders a 4-line
          bubble's translation as a SINGLE TINY LINE.
  PART D  Results JSON (committed) with all pins/tables/verdicts.

Cells source: the B3-tip notebook sha256
  c719feb6e4f6f12d267952c17b0fa380d0292b6d9a8fbec1290964714d7384d6
  (origin/mangabd-009-b3 @ cf01aef — UNMERGED, hold intact).
The instrument accepts --cells-dir (a directory of extracted cell_XX.py at
that pin). When run inside the repo with the B3 branch checked out, the
working notebook matches the pin and can be extracted with --from-notebook.
NO notebook/sample/source bytes are modified by this instrument.
"""
import argparse
import contextlib
import hashlib
import io
import json
import os
import shutil
import sys
import types
from pathlib import PosixPath, PurePosixPath, Path as _RealPath

import cv2
import numpy as np
from PIL import Image as PILImage, ImageDraw, ImageFont

ROOT = _RealPath("/home/z/my-project")
REPO = ROOT / "MangaBD"
FONTS = ROOT / "m008_probe" / "fonts"
HARNESS = ROOT / "b31_home"
WORK = ROOT / "m009_b31_work"
RESULTS_PATH = REPO / "scripts" / "m009_b31_perline_results.json"
NB_PIN = ("c719feb6e4f6f12d267952c17b0fa380d0292b6d9a"
          "8fbec1290964714d7384d6")
CELL_IDS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12]
PAGE_W, PAGE_H = 844, 1200
TR_TEXT = ("এই কী হয়েছে বলো তো আমি জানি না কেন "
           "এমন হয়েছে বলো তো আমি জানি না")

# ─────────────────────────────────────────────────────────────────
# 1. Harness (disclosed stub set — m009_b3_phaseC_harness.py law)
# ─────────────────────────────────────────────────────────────────

def make_torch_stub():
    stub = types.ModuleType("torch")

    class _NoGradCtx:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def no_grad(fn=None):
        if fn is not None:
            return fn

        def deco(f):
            return f
        return deco

    stub.no_grad = no_grad
    stub.Tensor = object
    stub.tensor = None
    stub.float16 = "float16"
    stub.float32 = "float32"
    cuda = types.ModuleType("torch.cuda")
    cuda.is_available = lambda: False
    cuda.empty_cache = lambda: None
    cuda.synchronize = lambda: None
    stub.cuda = cuda
    stub.__getattr__ = lambda name: (_ for _ in ()).throw(
        AttributeError(f"torch-stub: {name} unavailable"))
    return stub


def _rewrite_content(a0):
    for prefix in ("/content", "/root"):
        if isinstance(a0, str) and a0.startswith(prefix):
            return str(HARNESS / a0[len(prefix):].lstrip("/"))
        if isinstance(a0, PurePosixPath):
            s = str(a0)
            for prefix in ("/content", "/root"):
                if s.startswith(prefix):
                    return str(HARNESS / s[len(prefix):].lstrip("/"))
    return None


class ShimPath(PosixPath):
    def __init__(self, *args, **kw):
        if args:
            fixed = _rewrite_content(args[0])
            if fixed is not None:
                args = (fixed,) + tuple(args[1:])
        super().__init__(*args, **kw)


def install_pathlib_shim():
    proxy = types.ModuleType("pathlib_shim")
    import pathlib as real_pathlib
    proxy.__dict__.update(real_pathlib.__dict__)
    proxy.Path = ShimPath
    proxy.PosixPath = ShimPath
    sys.modules["pathlib_shim_saved"] = real_pathlib
    sys.modules["pathlib"] = proxy
    return proxy


def restore_pathlib():
    saved = sys.modules.pop("pathlib_shim_saved", None)
    if saved is not None:
        sys.modules["pathlib"] = saved


def seed_cell00_side_effects(ns):
    from PIL import features as _feat
    ns["MANGABD_ENV"] = {
        "version": "12.0.0", "timestamp": "b31-instrument",
        "python": sys.version.split()[0], "platform": sys.platform,
        "cuda_available": False, "gpu_name": None, "gpu_memory_gb": None,
        "torch_version": "stub", "pip_ok": True,
        "libraqm_ok": bool(_feat.check("raqm")),
        "critical_imports": {"harness": True},
        "errors": [], "warnings": [],
    }
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["MANGABD_VERSION"] = "12.0.0"


def exec_cells(cell_dir):
    ns = {"__name__": "__mangabd__"}
    logs = {}
    seed_cell00_side_effects(ns)
    install_pathlib_shim()
    sha_manifest = {}
    try:
        for cid in CELL_IDS:
            src = (cell_dir / f"cell_{cid:02d}.py").read_text(
                encoding="utf-8")
            sha_manifest[f"cell_{cid:02d}"] = hashlib.sha256(
                src.encode()).hexdigest()
            code = compile(src, f"cell_{cid:02d}.py", "exec")
            buf = io.StringIO()
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code, ns)
            except RuntimeError as exc:
                # DISCLOSED tolerance, cell_04 only (RF-14 rule — the
                # m009_b3_phaseC_harness.py law): inert torch stub cannot
                # feed the zyddnys import chain (CTD/LaMa = inpaint deps,
                # out of the render path under test).
                txt = buf.getvalue()
                fail_lines = [ln for ln in txt.splitlines() if "❌" in ln]
                zyddnys_only = fail_lines and all(
                    ("ComicTextDetector" in ln or "LamaLargeInpainter" in ln)
                    for ln in fail_lines)
                render_green = all(
                    marker in txt for marker in (
                        "Bengali font render test passed",
                        "libraqm available",
                        "Bengali render test",
                    ))
                if (cid == 4 and "Cell 4 self-tests failed" in str(exc)
                        and zyddnys_only and render_green):
                    pass
                else:
                    logs[cid] = buf.getvalue()
                    (HARNESS / "logs").mkdir(parents=True, exist_ok=True)
                    (HARNESS / "logs" / f"cell_{cid:02d}.txt").write_text(
                        logs[cid], encoding="utf-8")
                    raise
            logs[cid] = buf.getvalue()
    finally:
        restore_pathlib()
    return ns, logs, sha_manifest


# ─────────────────────────────────────────────────────────────────
# 2. Owner-geometry replica builder (deterministic; GT ledger)
# ─────────────────────────────────────────────────────────────────

INK_BLACK = (12, 12, 12)
COL_RED = (200, 30, 30)
COL_BLUE = (30, 30, 180)
COL_PURPLE = (96, 20, 170)


def build_replica(font_path):
    """844x1200 page, five regions, per-word emphasis GT ledger.

    Geometry grounded in the corpus: B1-era working res 844x1200 (S003
    family); manhwa bubble sizes from the S011 detections census
    (~300-510 x ~150-360). Colored-word ink targets the owner diagnostic
    (dark saturated hues, 1k-2.5k chromatic px per region).
    """
    page_pil = PILImage.new("RGB", (PAGE_W, PAGE_H), (250, 250, 250))
    raw_pil = PILImage.new("L", (PAGE_W, PAGE_H), 0)
    d_page = ImageDraw.Draw(page_pil)
    d_raw = ImageDraw.Draw(raw_pil)
    ledger = []

    def draw_region(rid, rx, ry, lines_spec, size, lh):
        """lines_spec: list of (stagger_x, [(word, rgb), ...])."""
        font = ImageFont.truetype(str(font_path), size)
        reg = {"id": rid, "x": rx, "y": ry, "w": 0, "h": 0,
               "lines": [], "size": size, "lh": lh}
        y = ry
        max_w = 0
        for stagger, words in lines_spec:
            pen = rx + stagger
            line_y0 = y
            gt_words = []
            for word, rgb in words:
                d_page.text((pen, y), word, font=font, fill=rgb)
                d_raw.text((pen, y), word, font=font, fill=255)
                gt_words.append({"word": word,
                                 "rgb": list(rgb),
                                 "colored": rgb != INK_BLACK})
                pen += font.getlength(word + " ")
            max_w = max(max_w, int(pen - rx - stagger))
            reg["lines"].append({
                "y0": line_y0, "y1": line_y0 + size + 8,
                "words": gt_words,
                "gt_color": next(
                    (w["rgb"] for w in gt_words if w["colored"]), None),
            })
            y += lh
        reg["w"] = max_w
        reg["h"] = y - ry
        ledger.append(reg)

    # R1 — THE OWNER'S FAILING CASE: 4-line bubble, black base,
    #      one red word (L2), one blue word (L3), ragged line starts.
    draw_region(1, 60, 80, [
        (0, [("আমি", INK_BLACK), ("জানি", INK_BLACK),
             ("না", INK_BLACK), ("এটা", INK_BLACK),
             ("কী", INK_BLACK), ("করে", INK_BLACK),
             ("হলো", INK_BLACK)]),
        (-12, [("এই", INK_BLACK), ("কাজটা", COL_RED),
               ("তোমার", INK_BLACK), ("করার", INK_BLACK),
               ("ছিল", INK_BLACK), ("না", INK_BLACK)]),
        (8, [("কিন্তু", INK_BLACK), ("আমি", INK_BLACK),
             ("তোমাকে", COL_BLUE), ("বলেছিলাম", INK_BLACK),
             ("যে", INK_BLACK)]),
        (-6, [("সবাই", INK_BLACK), ("চলে", INK_BLACK),
              ("গেছে", INK_BLACK), ("এখন", INK_BLACK)]),
    ], 30, 44)

    # R2 — full-line red shout + black lines.
    draw_region(2, 470, 90, [
        (0, [("এই", COL_RED), ("কী", COL_RED),
             ("হয়েছে", COL_RED), ("বলো", COL_RED),
             ("তো?!", COL_RED)]),
        (0, [("আমি", INK_BLACK), ("কিছুই", INK_BLACK),
             ("বুঝতে", INK_BLACK), ("পারছি", INK_BLACK),
             ("না", INK_BLACK)]),
        (0, [("এখনই", INK_BLACK), ("কথা", INK_BLACK),
             ("বলো", INK_BLACK)]),
    ], 28, 42)

    # R3 — SFX: two hues WITHIN one line (line-level bimodal candidate).
    draw_region(3, 60, 360, [
        (0, [("উঁহুঁ", COL_RED), ("উঁহুঁ", COL_RED),
             ("হাঃ", COL_BLUE), ("হাঃ", COL_BLUE)]),
    ], 34, 48)

    # R4 — all-black 4-line control (false-color check) at SMALLER
    #      font/gap (close(5,5)x2 bridge-fidelity probe).
    draw_region(4, 60, 500, [
        (0, [("এটা", INK_BLACK), ("একটা", INK_BLACK),
             ("সাধারণ", INK_BLACK), ("কালো", INK_BLACK)]),
        (0, [("টেক্সট", INK_BLACK), ("বাবল", INK_BLACK),
             ("যার", INK_BLACK), ("রঙ", INK_BLACK)]),
        (0, [("নেই", INK_BLACK), ("এমনিই", INK_BLACK),
             ("আছে", INK_BLACK), ("যেমন", INK_BLACK)]),
        (0, [("আগে", INK_BLACK), ("ছিল", INK_BLACK),
             ("সবসময়", INK_BLACK)]),
    ], 24, 34)

    # R5 — purple emphasis word, 2-line bubble.
    draw_region(5, 470, 420, [
        (0, [("তুমি", INK_BLACK), ("কি", INK_BLACK),
             ("সত্যিই", INK_BLACK), ("ভাবো", INK_BLACK)]),
        (0, [("যে", INK_BLACK), ("জাদুটা", COL_PURPLE),
             ("সত্যি", INK_BLACK), ("ছিল", INK_BLACK)]),
    ], 28, 42)

    page_np = np.array(page_pil)                    # RGB
    page_bgr = page_np[:, :, ::-1].copy()           # BGR for cells
    raw = np.array(raw_pil)                         # uint8 prob map
    return page_bgr, raw, ledger


# ─────────────────────────────────────────────────────────────────
# 3. PROTOTYPE per-line law (Phase C ports this into cell 6 anchors)
# ─────────────────────────────────────────────────────────────────

def _b31_win(ink_mask, x, y, w, h):
    H, W = ink_mask.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return None
    return x1, y1, x2, y2


def _b31_bands_from_profile(profile, lo, hi):
    """_b2_mask_orientation's band law VERBATIM (cell 6 L1419-1443):
    histogram, [1,2,3,2,1]/9 smooth, 0.12*peak threshold, <2-bin merge."""
    if hi - lo < 4.0:
        return []
    nb = max(8, int((hi - lo) // 2) + 1)
    hist, _ = np.histogram(profile, bins=nb, range=(lo, hi))
    k = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    sm = np.convolve(hist, k / k.sum(), mode="same")
    peak = float(sm.max())
    if peak <= 0:
        return []
    thr = max(0.5, 0.12 * peak)
    bands, s = [], None
    for i, val in enumerate(sm):
        if val >= thr and s is None:
            s = i
        elif val < thr and s is not None:
            bands.append([s, i])
            s = None
    if s is not None:
        bands.append([s, len(sm)])
    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] < 2:
            merged[-1] = [merged[-1][0], b[1]]
        else:
            merged.append(b)
    binw = (hi - lo) / nb
    out = []
    for bs, be in merged:
        v0 = lo + bs * binw
        v1 = lo + be * binw
        if v1 - v0 >= 3.0:                      # min band thickness
            out.append((v0, v1))
    return out


def _b31_line_bands(ink_mask, x, y, w, h):
    """Line boxes for angle≈0 regions: row-profile of the window's ink
    (v-axis = (0,1)); returns band intervals in PAGE coords."""
    win = _b31_win(ink_mask, x, y, w, h)
    if win is None:
        return []
    x1, y1, x2, y2 = win
    m = ink_mask[y1:y2, x1:x2] > 0
    if int(m.sum()) < 30:
        return []
    ys = np.nonzero(m)[0].astype(np.float64) + y1
    return _b31_bands_from_profile(ys, float(ys.min()), float(ys.max()))


def _b31_hue_unimodal(px_rgb):
    """B3's bimodality gate (cell 6 L1309-1331) on the chromatic cluster.
    True = single hue (safe to inherit)."""
    chr_sel = (px_rgb.max(axis=1) - px_rgb.min(axis=1)) >= 25
    if int(chr_sel.sum()) < 60:
        return True                       # too few chromatic px to split
    hsv = cv2.cvtColor(
        px_rgb[chr_sel].reshape(-1, 1, 3).astype(np.uint8),
        cv2.COLOR_RGB2HSV)[:, 0, 0].astype(np.float64) * 2.0
    hs = hsv[np.argsort(hsv)]
    n_h = len(hs)
    if n_h < 4:
        return True
    k = int(np.argmax(np.diff(hs)))
    arc_a, arc_b = hs[:k + 1], hs[k + 1:]

    def cmean(a):
        return float(np.rad2deg(np.mean(np.deg2rad(a)))) % 360.0

    ma, mb = cmean(arc_a), cmean(arc_b)
    sep = abs(ma - mb) % 360.0
    sep = min(sep, 360.0 - sep)
    if (len(arc_a) / n_h >= 0.25 and len(arc_b) / n_h >= 0.25
            and sep >= 40.0):
        return False                      # two hues => RB3-5 line skip
    return True


def _b31_line_color(page_bgr, ink_mask, x, y, w, h, band, tau):
    """Per-line chromatic-cluster law. Returns (color, note).

    black/white/gray/no-ink => (None, note) silent; colored cluster
    fraction >= tau AND single hue AND ring-contrast => the cluster's
    median. NOTE: the cluster median (not the whole-line median) is the
    B3.1 fix for per-word emphasis corpora."""
    x1, y1, x2, y2 = _b31_win(ink_mask, x, y, w, h)
    by1 = max(y1, int(np.floor(band[0])))
    by2 = min(y2, int(np.ceil(band[1])))
    if by2 - by1 < 3:
        return None, "no_band_window"
    m = ink_mask[by1:by2, x1:x2] > 0
    n_px = int(m.sum())
    if n_px < 30:
        return None, "no_ink"
    px = page_bgr[by1:by2, x1:x2][m].astype(np.int16)
    px_rgb = px[:, ::-1].copy()
    chroma_sel = (px_rgb.max(axis=1) - px_rgb.min(axis=1)) >= 25
    n_chr = int(chroma_sel.sum())
    frac = n_chr / float(n_px)
    if frac < tau:
        med_v = int(px_rgb.max(axis=0).max()) if len(px_rgb) else 0
        if frac < 0.02:
            mmed = np.median(px_rgb, axis=0)
            if int(mmed.max()) >= 215:
                return None, "white"
            if int(mmed.max()) <= 90:
                return None, "black"
            return None, "gray"
        return None, "below_tau"
    chr_px = px_rgb[chroma_sel]
    if not _b31_hue_unimodal(px_rgb):
        return None, "gate_bimodal"       # RB3-5 at LINE level
    try:                                   # ring gate (B3 law)
        m_u8 = m.astype(np.uint8) * 255
        dil = cv2.dilate(
            m_u8, cv2.getStructuringElement(
                cv2.MORPH_ELLIPSE, (11, 11)))
        ring = (dil > 0) & (~m)
        if int(ring.sum()) >= 10:
            rmed = np.median(
                page_bgr[by1:by2, x1:x2][ring].astype(np.int16), axis=0)
            cmed = np.median(chr_px, axis=0)
            if int(round(float(np.linalg.norm(
                    cmed.astype(float)
                    - rmed.astype(float))))) < 40:
                return None, "gate_ring"
    except Exception:
        pass
    med = np.median(chr_px, axis=0)
    return [int(med[0]), int(med[1]), int(med[2])], "colored"


def _b31_region_base(page_bgr, ink_mask, x, y, w, h, tau):
    """Fallback-ladder rung 2: region-level DOMINANT CHROMATIC cluster
    (fraction over the region's ink, single hue) — the median-free fix;
    the B3 region sampler's whole-population median is black on
    emphasis corpora by construction."""
    x1, y1, x2, y2 = _b31_win(ink_mask, x, y, w, h)
    if x1 is None:
        return None, "no_window"
    m = ink_mask[y1:y2, x1:x2] > 0
    if int(m.sum()) < 30:
        return None, "no_ink"
    px_rgb = page_bgr[y1:y2, x1:x2][m].astype(np.int16)[:, ::-1].copy()
    chroma_sel = (px_rgb.max(axis=1) - px_rgb.min(axis=1)) >= 25
    frac = float(chroma_sel.sum()) / float(len(px_rgb))
    if frac < tau:
        return None, "below_tau"
    if not _b31_hue_unimodal(px_rgb):
        return None, "gate_bimodal"
    med = np.median(px_rgb[chroma_sel], axis=0)
    return [int(med[0]), int(med[1]), int(med[2])], "colored"


def l2(a, b):
    return float(np.linalg.norm(np.asarray(a, float) - np.asarray(b, float)))


# ─────────────────────────────────────────────────────────────────
# 4. PART A+B drivers
# ─────────────────────────────────────────────────────────────────

def part_a_b(page_bgr, raw, ledger, ns):
    _b3_undilated_ink_mask = ns["_b3_undilated_ink_mask"]
    _b3_sample_ink_color = ns["_b3_sample_ink_color"]
    _b2_mask_orientation = ns["_b2_mask_orientation"]

    # the REAL B3 detect-side mask (thr 60 + close(5,5)x2 + clean)
    b3_mask = _b3_undilated_ink_mask(raw)
    # alternative locator: raw-threshold only (no close) — band fidelity
    raw_thr = ((raw > 60).astype(np.uint8) * 255)

    def clean_min3(mask):
        # clean_binary_mask is in ns (cell 6); reuse via ns if present
        fn = ns.get("clean_binary_mask")
        return fn(mask, min_area=3) if fn else mask

    raw_mask_noclean = clean_min3(raw_thr)

    out = {"b3_mask_px": int((b3_mask > 0).sum()) if b3_mask is not None
           else 0,
           "regions": []}
    taus = [0.10, 0.20, 0.30, 0.50]

    for reg in ledger:
        x, y, w, h = reg["x"], reg["y"], reg["w"], reg["h"]
        # PART A — B3 region sampler (live-REJECT reproduction)
        b3_c, b3_note = _b3_sample_ink_color(
            page_bgr, b3_mask, x, y, w, h)
        # PART A — B2 orientation on emphasis ink (spurious-angle check)
        try:
            b2_ang, b2_quad, b2_gt, b2_meas = _b2_mask_orientation(
                b3_mask, x, y, w, h)
        except Exception as exc:
            b2_ang, b2_quad, b2_gt, b2_meas = (
                None, None, {"err": str(exc)[:80]}, None)
        # chromatic fraction (the design input)
        x1, y1 = max(0, x - 2), max(0, y - 2)
        x2, y2 = min(PAGE_W, x + w + 2), min(PAGE_H, y + h + 2)
        mwin = b3_mask[y1:y2, x1:x2] > 0
        px_rgb = page_bgr[y1:y2, x1:x2][mwin].astype(np.int16)[:, ::-1]
        chr_sel = (px_rgb.max(axis=1) - px_rgb.min(axis=1)) >= 25
        chr_px = int(chr_sel.sum())
        region = {
            "id": reg["id"], "bbox": [x, y, w, h],
            "gt_lines": len(reg["lines"]),
            "gt_colored_lines": sum(
                1 for ln in reg["lines"] if ln["gt_color"]),
            "chromatic_px": chr_px,
            "ink_px": int(mwin.sum()),
            "chromatic_frac": round(
                chr_px / max(1, int(mwin.sum())), 4),
            "b3_region_key": b3_c, "b3_region_note": b3_note,
            "b2_orientation": {
                "measured": b2_meas, "angle": b2_ang,
                "gt": ({k: b2_gt[k] for k in b2_gt}
                       if isinstance(b2_gt, dict) else None),
            },
        }

        # PART B — per-line law on both locators
        for loc_name, loc_mask in (("b3_closed", b3_mask),
                                   ("raw_thr", raw_mask_noclean)):
            bands = _b31_line_bands(loc_mask, x, y, w, h)
            lines_out = []
            for bi, band in enumerate(bands):
                # GT line = the ledger line overlapping this band most
                gt_idx, gt_color = None, None
                best_ov = 0
                for gi, ln in enumerate(reg["lines"]):
                    ov = (min(band[1], ln["y1"]) - max(band[0], ln["y0"]))
                    if ov > best_ov:
                        best_ov, gt_idx = ov, gi
                if gt_idx is not None:
                    gt_color = reg["lines"][gt_idx]["gt_color"]
                per_tau = {}
                for tau in taus:
                    c, note = _b31_line_color(
                        page_bgr, loc_mask, x, y, w, h, band, tau)
                    hit = (c is not None and gt_color is not None
                           and l2(c, gt_color) <= 30)
                    false_hit = (c is not None and gt_color is None)
                    per_tau[str(tau)] = {
                        "color": c, "note": note,
                        "hit": bool(hit), "false_color": bool(false_hit)}
                lines_out.append({
                    "band": [round(band[0], 1), round(band[1], 1)],
                    "gt_line_idx": gt_idx, "gt_color": gt_color,
                    "tau": per_tau})
            base = {}
            for tau in taus:
                c, note = _b31_region_base(
                    page_bgr, loc_mask, x, y, w, h, tau)
                any_gt = next(
                    (ln["gt_color"] for ln in reg["lines"]
                     if ln["gt_color"]), None)
                base[str(tau)] = {"color": c, "note": note,
                                  "gt_any": any_gt}
            region[loc_name] = {
                "band_count": len(bands), "gt_lines": len(reg["lines"]),
                "bands": lines_out, "region_base": base}
        out["regions"].append(region)

    # summary
    for loc in ("b3_closed", "raw_thr"):
        for tau in taus:
            hits = falses = miss = 0
            for r in out["regions"]:
                for ln in r[loc]["bands"]:
                    t = ln["tau"][str(tau)]
                    hits += 1 if t["hit"] else 0
                    falses += 1 if t["false_color"] else 0
                    if (not t["hit"]) and ln["gt_color"] is not None:
                        miss += 1
            out.setdefault("summary", {})[f"{loc}_tau{tau}"] = {
                "colored_line_hits": hits, "false_colors": falses,
                "colored_line_misses": miss}
    # B3 inertness verdict
    out["summary"]["b3_region_keys_fired"] = sum(
        1 for r in out["regions"] if r["b3_region_key"] is not None)
    return out


# ─────────────────────────────────────────────────────────────────
# 5. PART C — tiny-text reproduction matrix
# ─────────────────────────────────────────────────────────────────

def _mk_variant_page(ns, pid, det_rows, translation=TR_TEXT):
    canvas = np.full((PAGE_H, PAGE_W, 3), 255, np.uint8)
    ns["init_page"](pid, width=PAGE_W, height=PAGE_H,
                    image_np=canvas, overwrite=True)
    ns["save_image_artifact"](pid, "inpainted", canvas, quality=95)
    ns["save_json_artifact"](pid, "detections", det_rows)
    ns["mark_stage_done"](pid, "detect", meta={"region_count": len(det_rows)})
    rows = []
    for dr in det_rows:
        row = {c: "" for c in ns["TRANSLATION_DF_COLUMNS"]}
        row.update({
            "page_id": pid, "page": pid, "id": dr["id"],
            "region_type": dr.get("region_type", "bubble"),
            "detector_class": dr.get("detector_class", "text_bubble"),
            "detector_score": 0.9, "parent_bubble_id": "",
            "x": dr["x"], "y": dr["y"],
            "width": dr["width"], "height": dr["height"],
            "angle": dr.get("angle", 0.0),
            "original_text": "テスト", "translated_text": translation,
            "confidence": 0.9, "ocr_engine": "b31",
            "is_english": True, "bengali_valid": True,
            "status": "ok", "reading_order": -1,
        })
        rows.append(row)
    ns["upsert_translation_rows"](pid, rows)


def _oriented_quad(cx, cy, wu, hv, deg):
    t = np.radians(deg)
    u = np.array([np.cos(t), np.sin(t)])
    v = np.array([-np.sin(t), np.cos(t)])
    qc = np.array([cx, cy], float)
    hw, hh = wu / 2.0, hv / 2.0
    q = [qc - hw * u - hh * v, qc + hw * u - hh * v,
         qc + hw * u + hh * v, qc - hw * u + hh * v]
    return [[round(float(p[0]), 2), round(float(p[1]), 2)] for p in q]


def _measure_render(ns, pid, det):
    out = ns["render_page"](pid, force=True)
    x, y, w, h = det["x"], det["y"], det["width"], det["height"]
    x1, y1 = max(0, x - 20), max(0, y - 20)
    x2, y2 = min(PAGE_W, x + w + 20), min(PAGE_H, y + h + 60)
    angle = float(det.get("angle", 0.0) or 0.0)
    if abs(angle) > 1.0:
        # wider window for the rotated paste (canvas + rotation expand)
        x1, y1 = max(0, x - 160), max(0, y - 160)
        x2 = min(PAGE_W, x + w + 160)
        y2 = min(PAGE_H, y + h + 160)
    roi = out[y1:y2, x1:x2].copy()
    if abs(angle) > 1.0:
        # de-rotate around the REGION's center in ROI coords (the
        # rotated canvas is pasted at the bbox center; a single rotated
        # line spans many rows — the raw row-profile would report its
        # diagonal extent, not the glyph height)
        cx_roi = (x + w / 2.0) - x1
        cy_roi = (y + h / 2.0) - y1
        rh, rw = roi.shape[:2]
        # PIL rotate(+a) = CCW; undo with cv2 CW (-a)
        mmat = cv2.getRotationMatrix2D((cx_roi, cy_roi), -angle, 1.0)
        roi = cv2.warpAffine(
            roi, mmat, (rw, rh), flags=cv2.INTER_LINEAR,
            borderValue=(255, 255, 255))
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    ink = gray < 120
    prof = ink.sum(axis=1)
    thr = max(1.0, 0.10 * prof.max()) if prof.max() > 0 else 0
    bands = _b31_bands_from_profile(
        np.nonzero(prof >= thr)[0].astype(float) if thr else np.array([]),
        0.0, float(len(prof))) if thr else []
    # column bands (for the V-3 vertical arm — rotated canvas columns)
    cprof = ink.sum(axis=0)
    cthr = max(1.0, 0.10 * cprof.max()) if cprof.max() > 0 else 0
    cbands = _b31_bands_from_profile(
        np.nonzero(cprof >= cthr)[0].astype(float) if cthr else np.array([]),
        0.0, float(len(cprof))) if cthr else []
    band_heights = [round(b - a, 1) for a, b in bands]
    col_widths = [round(b - a, 1) for a, b in cbands]
    meta = {}
    try:
        pdir = ns["get_page_dir"](pid)
        for cand in ("metadata.json", "stages.json", "render_meta.json"):
            p = pdir / cand
            if p.exists():
                meta[cand] = json.loads(p.read_text(encoding="utf-8"))
                break
    except Exception:
        pass
    return {
        "row_bands": len(bands), "band_heights": band_heights,
        "col_bands": len(cbands), "col_widths": col_widths,
        "ink_px": int(ink.sum()), "meta_found": bool(meta),
        "meta": meta,
    }


def part_c(ns):
    variants = []

    def v0():
        # baseline: correct 4-line bubble geometry, horizontal
        return {"id": 1, "x": 60, "y": 80, "width": 340, "height": 210,
                "quad": [[60, 80], [400, 80], [400, 290], [60, 290]],
                "angle": 0.0, "region_type": "bubble"}

    def v1():
        # V-3 predicate capture: w<90, h>2w -> vertical renderer
        return {"id": 1, "x": 60, "y": 400, "width": 80, "height": 220,
                "quad": [[60, 400], [140, 400], [140, 620], [60, 620]],
                "angle": 0.0, "region_type": "bubble"}

    def v2():
        # quad-collapse tilt: angle 24°, quad long diagonal 520 / thin 70
        q = _oriented_quad(230, 185, 520, 70, 24.0)
        return {"id": 1, "x": 60, "y": 80, "width": 340, "height": 210,
                "quad": q, "angle": 24.0, "region_type": "bubble"}

    def v2b():
        # quad-collapse, THIN variant: hv=30 -> fit_h crushes the size
        q = _oriented_quad(230, 185, 520, 30, 24.0)
        return {"id": 1, "x": 60, "y": 80, "width": 340, "height": 210,
                "quad": q, "angle": 24.0, "region_type": "bubble"}

    def v3():
        # mis-detected height: bbox h truncated to one line's worth
        return {"id": 1, "x": 60, "y": 80, "width": 340, "height": 52,
                "quad": [[60, 80], [400, 80], [400, 132], [60, 132]],
                "angle": 0.0, "region_type": "bubble"}

    def v4():
        # wrap-width from wrong box: w nearly full page + tiny h
        return {"id": 1, "x": 20, "y": 80, "width": 800, "height": 52,
                "quad": [[20, 80], [820, 80], [820, 132], [20, 132]],
                "angle": 0.0, "region_type": "bubble"}

    def v4b():
        # w-oversized + h crushed to a sliver (36px) -> size floor ~14
        return {"id": 1, "x": 20, "y": 80, "width": 800, "height": 36,
                "quad": [[20, 80], [820, 80], [820, 116], [20, 116]],
                "angle": 0.0, "region_type": "bubble"}

    def v4c():
        # V4b isolated from B1 smart-fill (region_type overlay -> bf
        # guard "region_type" -> exact current fit path)
        return {"id": 1, "x": 20, "y": 80, "width": 800, "height": 36,
                "quad": [[20, 80], [820, 80], [820, 116], [20, 116]],
                "angle": 0.0, "region_type": "overlay"}

    def v5():
        # b2gt GT-mirrored with merged bands: lines=1, spacing=0, tilted
        q = _oriented_quad(230, 185, 340, 210, 14.0)
        return {"id": 1, "x": 60, "y": 80, "width": 340, "height": 210,
                "quad": q, "angle": 14.0, "region_type": "bubble",
                "b2_gt_lines": 1, "b2_gt_spacing": 0.0,
                "b2_gt_cx": 230.0, "b2_gt_cy": 185.0}

    for name, fn in (("V0_baseline", v0), ("V1_v3_capture", v1),
                     ("V2_quad_collapse", v2), ("V2b_quad_thin", v2b),
                     ("V3_h_truncated", v3), ("V4_w_oversized", v4),
                     ("V4b_w_oversize_sliver", v4b),
                     ("V4c_sliver_no_bf", v4c), ("V5_b2gt_merged", v5)):
        det = fn()
        pid = f"__b31_{name.lower()}__"
        _mk_variant_page(ns, pid, [det])
        meas = _measure_render(ns, pid, det)
        # signature: single line AND tiny (band height <= 16 px)
        single_tiny = (meas["row_bands"] == 1
                       and meas["band_heights"]
                       and meas["band_heights"][0] <= 16)
        meas["single_tiny_line"] = bool(single_tiny)
        variants.append({"variant": name, "det": det, "measure": meas})
        # self-clean
        try:
            df = ns.get("translation_df")
            if df is not None and len(df):
                keep = df[df["page_id"] != pid]
                ns["translation_df"] = keep
                ns["save_translation_df"](keep)
            ns["reset_page"](pid, delete_artifacts=True)
        except Exception:
            pass
    return variants


# ─────────────────────────────────────────────────────────────────
# 6. main
# ─────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells-dir", default=str(WORK / "cells_b3tip"))
    ap.add_argument("--from-notebook", action="store_true",
                    help="extract cells from the repo working notebook "
                         "(must match the B3-tip pin)")
    ap.add_argument("--results", default=str(RESULTS_PATH))
    args = ap.parse_args()

    if HARNESS.exists():
        shutil.rmtree(HARNESS)
    HARNESS.mkdir(parents=True)
    fonts_dir = HARNESS / "content" / "mangabd" / "fonts"
    fonts_dir.mkdir(parents=True)
    shutil.copy(FONTS / "NotoSansBengali-Regular.ttf",
                fonts_dir / "NotoSansBengali-Regular.ttf")
    shutil.copy(FONTS / "NotoSansBengali-Regular.ttf",
                fonts_dir / "NotoSansBengali-Bold.ttf")
    shutil.copy(FONTS / "NotoSansJP.ttf", fonts_dir / "NotoSansJP.ttf")

    cells_dir = _RealPath(args.cells_dir)
    if args.from_notebook or not cells_dir.exists():
        nb_path = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
        raw = nb_path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if sha != NB_PIN:
            print(f"FATAL: notebook sha {sha[:16]}... != B3-tip pin "
                  f"{NB_PIN[:16]}... — checkout the B3 branch or pass "
                  "--cells-dir with the pinned extracts")
            sys.exit(2)
        nb = json.loads(raw.decode("utf-8"))
        cells_dir = WORK / "cells_b3tip_run"
        cells_dir.mkdir(parents=True, exist_ok=True)
        for i, c in enumerate(nb["cells"]):
            (cells_dir / f"cell_{i:02d}.py").write_text(
                "".join(c.get("source", [])), encoding="utf-8")

    print("[b31] exec'ing B3-tip cells (torch stub, pathlib shim) ...")
    sys.modules["torch"] = make_torch_stub()
    ns, logs, sha_manifest = exec_cells(cells_dir)
    print("[b31] cells exec'd OK")
    # battery continuity check (Test 23 must still pass in this env)
    t23 = "PASS" if "✅ B3 sampler: colored fires" in logs[10] else "CHECK"

    page_bgr, raw, ledger = build_replica(FONTS / "NotoSansBengali-Regular.ttf")
    # contact sheet (workspace-only)
    WORK.mkdir(parents=True, exist_ok=True)
    PILImage.fromarray(page_bgr[:, :, ::-1]).save(WORK / "replica.png")

    print("[b31] PART A+B: B3 reproduction + per-line law ...")
    ab = part_a_b(page_bgr, raw, ledger, ns)
    print("[b31] PART C: tiny-text matrix ...")
    c = part_c(ns)

    results = {
        "instrument": "m009_b31_perline_measure.py",
        "batch": "MANGABD-009 B3.1 Phase A (docs-only)",
        "base_branch": "origin/mangabd-009-b3 @ cf01aef (UNMERGED)",
        "notebook_sha256_pin": NB_PIN,
        "cell_sha_manifest": sha_manifest,
        "battery_test23_in_env": t23,
        "font": {
            "path": str(FONTS / "NotoSansBengali-Regular.ttf"),
            "sha256": hashlib.sha256(
                (FONTS / "NotoSansBengali-Regular.ttf").read_bytes()
            ).hexdigest(),
        },
        "page": {"w": PAGE_W, "h": PAGE_H,
                 "note": "B1-era working res; bubble geometry from the "
                         "S011 detections census; ink hues from the "
                         "owner diagnostic"},
        "part_ab": ab,
        "part_c": c,
        "disclosures": [
            "detection-stage box geometry in PART C is INJECTED (no real "
            "CTD/RT-DETR under the torch stub) — the mis-detection "
            "hypothesis (V3/V4 preconditions) is ranked by injection + "
            "static analysis; final adjudication should capture the "
            "owner page's real detections.json from the Colab run",
            "the raw prob map is drawn stroke-precise at 255 (the Test "
            "23 idealization); real CTD prob maps are soft — threshold "
            "behavior at 60 is expected to be equivalent, disclosed",
            "per-line law functions here are the PROTOTYPE (Phase C "
            "ports them into cell-6 anchored patches); NO source changes "
            "in this batch",
        ],
    }
    outp = _RealPath(args.results)
    outp.write_text(json.dumps(results, indent=1, ensure_ascii=False),
                    encoding="utf-8")
    print(f"[b31] results -> {outp}")

    # console digest
    s = ab["summary"]
    print("\n=== DIGEST ===")
    print(f"B3 region keys fired on replica: "
          f"{s['b3_region_keys_fired']} (live-REJECT reproduction: "
          f"expect 0)")
    for loc in ("b3_closed", "raw_thr"):
        for tau in ("0.1", "0.2", "0.3", "0.5"):
            k = f"{loc}_tau{tau}"
            if k in s:
                v = s[k]
                print(f"per-line[{loc} tau={tau}]: hits={v['colored_line_hits']} "
                      f"false={v['false_colors']} miss={v['colored_line_misses']}")
    for v in c:
        m = v["measure"]
        print(f"{v['variant']}: rows={m['row_bands']} "
              f"h={m['band_heights'][:4]} cols={m['col_bands']} "
              f"single_tiny={m['single_tiny_line']}")


if __name__ == "__main__":
    main()
