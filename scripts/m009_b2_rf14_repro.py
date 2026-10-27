#!/usr/bin/env python3
"""MANGABD-009 B2 RF-14 — zero-text render regression: reproduction harness.

Owner-like run of the pipeline cells VERBATIM from the notebook blob at a
chosen git ref, on synthetic AI-gen-like manga pages (horizontal-only /
tilted / multi-region), then per-region render ink assertions + per-region
render instrumentation.

Cell set (extraction indices): 01, 02, 03, 04, 05, 06, 07, 10.
  * cell_00 (env doctor / pip installs) is Colab environment prep — the
    local env already has the deps; SKIPPED (disclosed).
  * cell_05 is exec'd verbatim because cell_07 (L36) and cell_06 (L43)
    hard-require `model_manager` at import time (disclosed).
  * cell_08 (translation service) / cell_09 (inpaint) are out of the
    Owner's failing loop: the Owner's facts state inpaint OK and 8/9
    translations already applied; the harness supplies the synthetic
    clean-bubble `inpainted` artifact directly (disclosed).

Env-level stubs — cell source bytes stay VERBATIM:
  * torch  : inert stub module (no CUDA) — RT-DETR inference is
             harness-stubbed anyway; cells need import + @torch.no_grad().
  * pathlib: /content* paths remapped to <HARNESS>/content* via a Path
             subclass installed only during cell exec (no /content dir
             exists on this box; no sudo).
  * rtdetr_detect        : ground-truth boxes for the synthetic bubbles.
  * run_ocr_engine       : per-region Japanese text (what the bubble shows).
  * model_manager.ensure_ocr_engine : no-op truthy (prevents Qwen download).

Refs:
  post = fd8d625 (branch tip, Flash Phase D APPROVED; notebook 08225748...)
  pre  = 5fe8804 (B2 Phase A base == B1 main notebook 0858a1c9...)
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import PosixPath, PurePosixPath, Path as _RealPath

import numpy as np

ROOT = _RealPath("/home/z/my-project")
REPO = ROOT / "MangaBD"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
FONTS = ROOT / "m008_probe" / "fonts"
VJP = REPO / "assets" / "fonts" / "NotoSansJP[wght].ttf"
HARNESS = ROOT / "rf14_home"
REPORTS = ROOT / "rf14_reports"
CELLS_POST = ROOT / "cells_rf14"
CELLS_PRE = ROOT / "cells_rf14_pre"
REFS = {"post": "fd8d625", "pre": "5fe8804"}
# cell_23 exec'd for the Owner's step_4 flow: its sync_translate_stage is
# what the UI 'Inpaint + Render' button runs before render_all_pages
# (module-level sync at exec time is a no-op: no pages have
# translations yet at Run-All time — DISCLOSED harness addition).
CELL_IDS = [1, 2, 3, 4, 5, 6, 7, 10, 23]

RNG_SEED = 20261027
ZERO_INK_FLOOR = 10          # < 10 diff px inside a rendered region = ZERO-INK
VISIBLE_INK_FLOOR = 50       # >= 50 px = clearly visible render


# ──────────────────────────────────────────────────────────────
# 0. Small helpers
# ──────────────────────────────────────────────────────────────

def log(msg):
    print(f"[rf14] {msg}", flush=True)


def nb_blob(ref):
    if ref == "work":
        # working-tree notebook (e.g. the RF-14 fix, pre-commit)
        return (REPO / NB_NAME).read_bytes()
    out = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{REFS[ref]}:{NB_NAME}"],
        capture_output=True, check=True,
    )
    return out.stdout


def extract_cells(ref):
    nb = json.loads(nb_blob(ref).decode("utf-8"))
    outdir = {"post": CELLS_POST, "pre": CELLS_PRE,
              "work": ROOT / "cells_rf14_work"}[ref]
    outdir.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(nb["cells"]):
        src = "".join(c.get("source", []))
        (outdir / f"cell_{i:02d}.py").write_text(src, encoding="utf-8")
    sha = hashlib.sha256(nb_blob(ref)).hexdigest()
    tag = REFS.get(ref, ref)
    log(f"extracted {ref} @ {tag}: {len(nb['cells'])} cells -> {outdir} (blob sha {sha[:8]})")
    return outdir


# ──────────────────────────────────────────────────────────────
# 1. Env shims (torch stub, pathlib remap) — cells stay verbatim
# ──────────────────────────────────────────────────────────────

def make_torch_stub():
    """Inert torch: import-only + @torch.no_grad() decorator passthrough."""
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
    """Colab-only absolute roots -> <HARNESS>/... (cells stay verbatim).

    /content/* (Colab base dir, needs no sudo there) and
    /root/* (HF cache in cell-05) do not exist / are not writable on
    this box; both are remapped into the harness root."""
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
    """Real PosixPath subclass; absolute /content* -> <HARNESS>/content*.

    NOTE: py3.12 pathlib parses args in __init__ (not __new__), so the
    rewrite hooks __init__ (an earlier __new__-based draft was a no-op)."""

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


# ──────────────────────────────────────────────────────────────
# 2. Synthetic AI-gen-like manga pages
# ──────────────────────────────────────────────────────────────

JP_HORIZONTAL = {
    1: "おはよう。今日も元気だね！",
    2: "どこに行くの？待ってよ。",
    3: "そういうことだったのか…",
}
JP_TILTED = {
    1: "危ない！逃げろ！！",
    2: "何だこの気配は…",
}
JP_VERTICAL = ["縦", "書", "き", "の", "測", "試"]

BENGALI_BY_KIND = {
    "horizontal": "এই কাজটা তোমার পক্ষে সম্ভব নয়!",
    "tilted": "চুপ করে শোনো, কী বলছি!",
    "v3_tall": "আমি কিছুই বুঝতে পারছি না।",
    "wide_vertical": "দাঁড়াও! এখানে কী হয়েছে?",
    "sfx_free": "খুব দ্রুত চলতে হবে!",
    "horizontal2": "তুমি কি আমায় বিশ্বাস করো?",
}


def _page_canvas(w, h, rng):
    """Light-art background: gray + screentone band + a few strokes."""
    bg = np.full((h, w, 3), 238, np.uint8)
    # screentone dots (halftone) in a margin band
    for yy in range(0, h, 8):
        for xx in range(0, w, 8):
            if (xx // 8 + yy // 8) % 2 == 0:
                bg[yy, xx] = 205
    # art strokes outside bubbles
    import cv2 as _cv2
    for _ in range(26):
        x1, y1 = int(rng.uniform(0, w)), int(rng.uniform(0, h))
        x2 = x1 + int(rng.uniform(-160, 160))
        y2 = y1 + int(rng.uniform(-160, 160))
        thickness = int(rng.uniform(2, 5))
        _cv2.line(bg, (x1, y1), (x2, y2), (60, 60, 60), thickness)
    return bg


def _draw_bubble(pil, cx, cy, bw, bh):
    """White ellipse + black border; returns (x, y, w, h) ground-truth box."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(pil)
    x0, y0 = cx - bw // 2, cy - bh // 2
    x1, y1 = cx + bw // 2, cy + bh // 2
    d.ellipse([x0, y0, x1, y1], fill=(255, 255, 255),
              outline=(20, 20, 20), width=3)
    return int(x0), int(y0), int(x1 - x0), int(y1 - y0)


def _jp_font(size):
    from PIL import ImageFont
    return ImageFont.truetype(str(VJP), size)


def _draw_jp_horizontal(pil, cx, cy, text, size=30, lines=1):
    from PIL import ImageDraw
    d = ImageDraw.Draw(pil)
    f = _jp_font(size)
    mid = (len(text) + lines - 1) // lines
    chunks = [text[i * mid:(i + 1) * mid] for i in range(lines)]
    lh = int(size * 1.5)
    total = lh * len(chunks)
    y0 = cy - total // 2
    for i, ch in enumerate(chunks):
        wpx = d.textlength(ch, font=f)
        d.text((cx - wpx / 2, y0 + i * lh), ch, font=f, fill=(0, 0, 0))


def _draw_jp_tilted(pil, cx, cy, text, beta, size=30):
    """Draw a horizontal JP line, rotate by beta (PIL, CCW positive), paste."""
    from PIL import Image, ImageDraw
    f = _jp_font(size)
    probe = ImageDraw.Draw(Image.new("L", (8, 8)))
    wpx = int(probe.textlength(text, font=f)) + 24
    strip = Image.new("RGB", (max(wpx, 60), int(size * 2.2)), (255, 255, 255))
    ImageDraw.Draw(strip).text((12, 8), text, font=f, fill=(0, 0, 0))
    rot = strip.rotate(beta, expand=True, resample=Image.BICUBIC,
                        fillcolor=(255, 255, 255))
    pil.paste(rot, (int(cx - rot.width / 2), int(cy - rot.height / 2)))


def _draw_jp_vertical(pil, cx, cy, text, size=30, columns=1):
    from PIL import ImageDraw
    d = ImageDraw.Draw(pil)
    f = _jp_font(size)
    chars = [c for c in text if c.strip()]
    col_h = len(chars) * int(size * 1.35)
    x0 = cx + (columns - 1) * int(size * 1.35) / 2
    for col in range(columns):
        xs = x0 - col * int(size * 1.35)
        ys = cy - col_h // 2
        for i, ch in enumerate(chars):
            d.text((xs, ys + i * int(size * 1.35)), ch, font=f, fill=(0, 0, 0))


def _bgr_from_pil(pil):
    import cv2 as _cv2
    return _cv2.cvtColor(np.asarray(pil), _cv2.COLOR_RGB2BGR)


def _pil_from_bgr(bgr):
    from PIL import Image
    import cv2 as _cv2
    return Image.fromarray(_cv2.cvtColor(bgr, _cv2.COLOR_BGR2RGB))


def build_pages():
    """Three Owner-like test pages. Returns list of page dicts."""
    import cv2
    from PIL import Image

    rng = np.random.default_rng(RNG_SEED)
    W, H = 1100, 1600
    pages = []

    def make(page_name, bubbles, sfx=None):
        """
        bubbles: list of dicts:
          kind, cx, cy, bw, bh, jp (text), jp_mode, beta, columns, size
        """
        full, clean = {}, {}
        for with_text in (True, False):
            bg = _page_canvas(W, H, rng)
            pil = _pil_from_bgr(bg).copy()
            boxes = []
            for b in bubbles:
                bx = _draw_bubble(pil, b["cx"], b["cy"], b["bw"], b["bh"])
                if with_text:
                    if b.get("jp_mode") == "tilt":
                        _draw_jp_tilted(pil, b["cx"], b["cy"], b["jp"],
                                        b["beta"], size=b.get("size", 30))
                    elif b.get("jp_mode") == "vertical":
                        _draw_jp_vertical(pil, b["cx"], b["cy"], b["jp"],
                                           size=b.get("size", 30),
                                           columns=b.get("columns", 1))
                    else:
                        _draw_jp_horizontal(pil, b["cx"], b["cy"], b["jp"],
                                            size=b.get("size", 30),
                                            lines=b.get("lines", 1))
                boxes.append({"box": bx, "kind": b["kind"],
                              "detector_class": "text_bubble"})
            if with_text and sfx is not None:
                _draw_jp_tilted(pil, sfx["cx"], sfx["cy"], sfx["jp"],
                                sfx["beta"], size=sfx.get("size", 40))
                boxes.append({"box": (int(sfx["cx"] - 150), int(sfx["cy"] - 40),
                                      300, 80),
                              "kind": "sfx_free",
                              "detector_class": "text_free"})
            arr = _bgr_from_pil(pil)
            (full if with_text else clean)["img"] = arr
            (full if with_text else clean)["boxes"] = boxes
        pages.append({
            "filename": f"{page_name}.jpg",
            "full": full["img"], "clean": clean["img"],
            "boxes": full["boxes"],
        })

    # P1 — horizontal-only (3 bubbles)
    make("p1_horizontal_only", [
        {"kind": "horizontal", "cx": 300, "cy": 280, "bw": 340, "bh": 240,
         "jp": JP_HORIZONTAL[1], "lines": 2},
        {"kind": "horizontal2", "cx": 780, "cy": 520, "bw": 300, "bh": 200,
         "jp": JP_HORIZONTAL[2], "lines": 1},
        {"kind": "horizontal", "cx": 450, "cy": 1050, "bw": 360, "bh": 260,
         "jp": JP_HORIZONTAL[3], "lines": 2},
    ])

    # P2 — tilted (2 tilted + 1 horizontal)
    make("p2_tilted", [
        {"kind": "tilted", "cx": 330, "cy": 350, "bw": 380, "bh": 260,
         "jp": JP_TILTED[1], "jp_mode": "tilt", "beta": -12.0},
        {"kind": "tilted", "cx": 750, "cy": 800, "bw": 340, "bh": 230,
         "jp": JP_TILTED[2], "jp_mode": "tilt", "beta": 9.0},
        {"kind": "horizontal2", "cx": 420, "cy": 1250, "bw": 320, "bh": 200,
         "jp": JP_HORIZONTAL[1], "lines": 1},
    ])

    # P3 — multi-region: horizontal + tilted + V-3 tall + wide vertical + SFX
    make("p3_multi_region", [
        {"kind": "horizontal", "cx": 280, "cy": 240, "bw": 320, "bh": 200,
         "jp": JP_HORIZONTAL[2], "lines": 1},
        {"kind": "tilted", "cx": 780, "cy": 480, "bw": 360, "bh": 240,
         "jp": JP_TILTED[2], "jp_mode": "tilt", "beta": -18.0},
        {"kind": "v3_tall", "cx": 240, "cy": 800, "bw": 76, "bh": 300,
         "jp": "".join(JP_VERTICAL), "jp_mode": "vertical", "columns": 1},
        {"kind": "wide_vertical", "cx": 620, "cy": 900, "bw": 170, "bh": 300,
         "jp": "".join(JP_VERTICAL), "jp_mode": "vertical", "columns": 2},
        {"kind": "horizontal2", "cx": 880, "cy": 1300, "bw": 300, "bh": 190,
         "jp": JP_HORIZONTAL[3], "lines": 2},
    ], sfx={"cx": 260, "cy": 1300, "jp": "ドォン!!", "beta": -8.0, "size": 40})

    return pages


# ──────────────────────────────────────────────────────────────
# 3. Cell exec (verbatim) with per-cell stdout capture
# ──────────────────────────────────────────────────────────────

def seed_cell00_side_effects(ns):
    """cell_00 (env doctor) is not exec'd locally: it unconditionally
    pip-installs the full package list (Colab bootstrap). Its RUNTIME
    side effects are provided here instead (disclosed env-level stub):
      * MANGABD_ENV report dict (cell_01's import gate + prints)
      * the safe environment variables it sets
    Cell source bytes stay verbatim."""
    from PIL import features as _feat
    ns["MANGABD_ENV"] = {
        "version": "12.0.0",
        "timestamp": "rf14-harness",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "cuda_available": False,
        "gpu_name": None,
        "gpu_memory_gb": None,
        "torch_version": "stub",
        "pip_ok": True,
        "libraqm_ok": bool(_feat.check("raqm")),
        "critical_imports": {"harness": True},
        "errors": [],
        "warnings": [],
    }
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["MANGABD_VERSION"] = "12.0.0"


def exec_cells(cell_dir):
    ns = {"__name__": "__mangabd__"}
    logs = {}
    seed_cell00_side_effects(ns)
    install_pathlib_shim()
    try:
        for cid in CELL_IDS:
            src = (cell_dir / f"cell_{cid:02d}.py").read_text(encoding="utf-8")
            code = compile(src, f"cell_{cid:02d}.py", "exec")
            buf = io.StringIO()
            log(f"exec cell_{cid:02d} ({len(src)} bytes) ...")
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code, ns)
            except RuntimeError as exc:
                # DISCLOSED tolerance, cell_04 only: the inert torch stub
                # cannot feed the zyddnys import chain (ComicTextDetector /
                # LamaLargeInpainter need real torch+torchvision). Those two
                # imports power CTD + LaMa inpaint — OUT of the render path
                # under test (Owner's facts: inpaint OK). Tolerated ONLY if
                # every font/raqm/Bengali render test passed and the failure
                # set is exactly those torch-dependent imports.
                txt = buf.getvalue()
                fail_lines = [ln for ln in txt.splitlines() if "❌" in ln]
                zyddnys_only = fail_lines and all(
                    ("ComicTextDetector" in ln or "LamaLargeInpainter" in ln)
                    for ln in fail_lines
                )
                render_green = all(
                    marker in txt for marker in (
                        "Bengali font render test passed",
                        "libraqm available",
                        "Bengali render test",
                    )
                )
                if (cid == 4 and "Cell 4 self-tests failed" in str(exc)
                        and zyddnys_only and render_green):
                    log("cell_04: env-limited zyddnys torch-imports only "
                        "(torch stub; CTD/LaMa = inpaint deps, out of scope) "
                        "— tolerated (DISCLOSED); font tests all green")
                else:
                    raise
            logs[cid] = buf.getvalue()
            tail = [ln for ln in logs[cid].splitlines() if ln.strip()]
            log(f"cell_{cid:02d} done ({len(tail)} lines); tail: "
                f"{tail[-1][:100] if tail else '<empty>'}")
    finally:
        restore_pathlib()
    return ns, logs


def battery_summary(logs):
    """Pull self-test pass/fail lines out of the captured cell logs."""
    import re as _re
    out = {}
    for cid, text in logs.items():
        hits = _re.findall(
            r"((?:TESTS|Self-tests?|RESULT).*|\d+\s*/\s*\d+\s*(?:passed|PASS|HARD).*)",
            text,
            _re.IGNORECASE,
        )
        if hits:
            out[cid] = [h.strip() for h in hits][-3:]
    return out


# ──────────────────────────────────────────────────────────────
# 4. Per-region render instrumentation (ns-level wrappers)
# ──────────────────────────────────────────────────────────────

class RegionTrace:
    def __init__(self):
        self.calls = []

    def add(self, fn, args, kw, result=None):
        self.calls.append({
            "fn": fn,
            "args": [repr(a)[:60] for a in args],
            "kw": {k: repr(v)[:60] for k, v in kw.items()},
            "result": repr(result)[:80],
        })


def instrument(ns):
    """Wrap the render decision points; return (trace, unwrap)."""
    trace = RegionTrace()
    wraps = []

    def deco(name):
        orig = ns.get(name)

        def wrapper(*a, **kw):
            r = orig(*a, **kw)
            trace.add(name, a, kw, r)
            return r
        ns[name] = wrapper
        wraps.append((name, orig))

    for name in (
        "_b2_render_angle", "fit_font_size", "get_font",
        "choose_text_color", "bubble_fill_decision",
    ):
        if name in ns:
            deco(name)

    # render_bengali_text: also measure ink drawn per call
    orig_rb = ns.get("render_bengali_text")

    def rb_wrapper(image_pil, text, x, y, w, h, *a, **kw):
        before = np.asarray(image_pil).copy()
        out = orig_rb(image_pil, text, x, y, w, h, *a, **kw)
        after = np.asarray(out)
        x0, y0 = max(0, x - 80), max(0, y - 80)
        x1 = min(before.shape[1], x + w + 80)
        y1 = min(before.shape[0], y + h + 80)
        try:
            delta = int((np.abs(after[y0:y1, x0:x1].astype(int)
                                - before[y0:y1, x0:x1].astype(int)).sum(axis=2)
                         > 30).sum())
        except Exception:
            delta = -1
        trace.add("render_bengali_text", (x, y, w, h),
                  {**kw, "text": str(text)[:40], "ink_px": delta})
        return out

    ns["render_bengali_text"] = rb_wrapper
    wraps.append(("render_bengali_text", orig_rb))

    def unwrap():
        for name, orig in wraps:
            ns[name] = orig

    return trace, unwrap


# ──────────────────────────────────────────────────────────────
# 5. Owner-like pipeline over the harness ns
# ──────────────────────────────────────────────────────────────

def _box_key(box_dict):
    return (box_dict["box"][0], box_dict["box"][1])


def run_page(ns, page, ocr_stub_map, trace):
    """register -> detect -> ocr -> translate -> inpaint -> render; probe ink."""
    import cv2
    nsb = ns
    res = {"filename": page["filename"], "regions": []}

    page_id = ns["init_page"](
        page["filename"],
        width=page["full"].shape[1],
        height=page["full"].shape[0],
        image_np=page["full"],
        overwrite=True,
    )
    res["page_id"] = page_id

    # stub detector -> REAL region build (incl. B2 estimator wiring)
    boxes = [{"x": b["box"][0], "y": b["box"][1], "w": b["box"][2],
              "h": b["box"][3], "score": 0.9,
              "detector_class": b["detector_class"]}
             for b in page["boxes"]]
    ns["rtdetr_detect"] = lambda img: {
        "text_bubble_boxes": [b for b in boxes
                              if b["detector_class"] == "text_bubble"],
        "text_free_boxes": [b for b in boxes
                            if b["detector_class"] == "text_free"],
        "bubble_boxes": [],
    }

    regions, _mask = ns["detect_page"](page_id, page["full"], force=True)

    det_rows = ns["load_json_artifact"](page_id, "detections", default=[])
    for r in det_rows:
        res["regions"].append({
            "id": r["id"], "x": r["x"], "y": r["y"],
            "w": r["width"], "h": r["height"],
            "angle": r["angle"], "quad": r["quad"],
            "region_type": r["region_type"],
        })

    # OCR: stub engine -> REAL chain/row builder -> translation_df
    ns["run_ocr_engine"] = lambda name, img, region, page_id=None: (
        ocr_stub_map[tuple(int(region.get(k, 0)) for k in ("x", "y"))]
        if tuple(int(region.get(k, 0)) for k in ("x", "y")) in ocr_stub_map
        else {"text": "テスト", "confidence": 0.9, "engine": name,
              "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
              "warnings": [], "is_english": True, "status": "ok",
              "vertical_ocr": None}
    )
    ns["ocr_page"](page_id, page["full"], force=True)

    # Owner-like apply: Bengali translated_text per row
    df = ns["translation_df"]
    page_rows = df[df["page_id"] == page_id]
    applied = 0
    for idx, row in page_rows.iterrows():
        key = (int(row["x"]), int(row["y"]))
        beng = ocr_stub_map.get(key, {}).get("__bengali", "")
        if beng:
            df.at[idx, "translated_text"] = beng
            applied += 1
    ns["save_translation_df"]()
    res["applied_translations"] = applied

    # synthetic inpainted artifact (bubbles cleaned) + stage mark
    ns["save_image_artifact"](page_id, "inpainted", page["clean"], quality=95)
    ns["mark_stage_done"](page_id, "inpaint", meta={"inpaint_engine": "synthetic"})

    # render (force; the Owner's step_4 fresh-session equivalent)
    trace.calls.clear()
    final_bgr = ns["render_page"](page_id, force=True)

    # per-region ink probe vs the clean inpainted canvas
    clean = page["clean"]
    fh, fw = final_bgr.shape[:2]
    for reg in res["regions"]:
        m = 34
        x0 = max(0, reg["x"] - m)
        y0 = max(0, reg["y"] - m)
        x1 = min(fw, reg["x"] + reg["w"] + m)
        y1 = min(fh, reg["y"] + reg["h"] + m)
        diff = np.abs(
            final_bgr[y0:y1, x0:x1].astype(int)
            - clean[y0:y1, x0:x1].astype(int)).sum(axis=2)
        reg["ink_px"] = int((diff > 30).sum())

    # df status after render
    page_rows2 = ns["translation_df"][ns["translation_df"]["page_id"] == page_id]
    status_counts = {}
    for s in page_rows2["status"]:
        status_counts[s] = status_counts.get(s, 0) + 1
    res["status_after_render"] = status_counts
    res["render_trace"] = [c for c in trace.calls]
    res["render_meta"] = (ns["get_page"](page_id) or {}).get("meta", {})
    return res


# ──────────────────────────────────────────────────────────────
# 6. Main
# ──────────────────────────────────────────────────────────────

def run_ref(ref, kill_switch_off=False, scenario="pipeline"):
    log(f"=== RUN ref={ref} kill_switch_off={kill_switch_off} scenario={scenario} ===")
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

    cell_dir = extract_cells(ref)

    # torch stub BEFORE cell exec (cell-05/06 import torch)
    sys.modules["torch"] = make_torch_stub()

    ns, logs = exec_cells(cell_dir)
    log("battery summaries: " + json.dumps(battery_summary(logs), ensure_ascii=False))

    pages = build_pages()
    ocr_stub_map = {}
    for page in pages:
        for b in page["boxes"]:
            key = (b["box"][0], b["box"][1])
            ocr_stub_map[key] = {
                "text": "テスト文章です。", "confidence": 0.9, "engine": "harness",
                "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
                "warnings": [], "is_english": True, "status": "ok",
                "vertical_ocr": None,
                "__bengali": BENGALI_BY_KIND.get(b["kind"], "এই কী হয়েছে বলো তো!"),
            }

    if kill_switch_off:
        ns["MANGABD_CONFIG"]["detection"]["b2_orientation_enable"] = False

    # model_manager.ensure_ocr_engine stub AFTER cells exec (self-tests are done)
    ns["model_manager"].ensure_ocr_engine = lambda name, force=False: True

    trace, unwrap = instrument(ns)
    results = []
    if scenario == "owner_session":
        owner = owner_session(ns, pages, ocr_stub_map, f"{ref}")
        results = owner
        zero_ink = [
            (p["page"], rid, ink)
            for p in owner["pages"]
            for rid, ink in p["zero_regions"]
        ]
        unwrap()
        log(f"ref={ref} owner_session zero-ink: {len(zero_ink)} -> "
            f"{'REPRODUCED' if zero_ink else 'no repro'}")
        return {"ref": ref, "kill_switch_off": kill_switch_off,
                "scenario": scenario, "results": results,
                "zero_ink": zero_ink, "battery": battery_summary(logs)}
    for page in pages:
        results.append(run_page(ns, page, ocr_stub_map, trace))
    unwrap()

    # verdict
    zero_ink = []
    if scenario == "pipeline":
        for page in results:
            for reg in page["regions"]:
                floor = (VISIBLE_INK_FLOOR if reg["ink_px"] >= VISIBLE_INK_FLOOR
                         else ("ZERO" if reg["ink_px"] < ZERO_INK_FLOOR else "FAINT"))
                if reg["ink_px"] < ZERO_INK_FLOOR:
                    zero_ink.append((page["filename"], reg["id"], reg["ink_px"]))
                log(f"  {page['filename']} region {reg['id']}: "
                    f"angle={reg['angle']:+.2f} quad={'Y' if reg['quad'] else 'N'} "
                    f"{reg['w']}x{reg['h']} ink={reg['ink_px']:>6} [{floor}]")
    log(f"ref={ref} kill={kill_switch_off} ZERO-INK regions: {len(zero_ink)}"
        f" -> {'REPRODUCED' if zero_ink else 'no repro'}")
    return {"ref": ref, "kill_switch_off": kill_switch_off,
            "scenario": scenario,
            "results": results, "zero_ink": zero_ink,
            "battery": battery_summary(logs)}


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "post"
    REPORTS.mkdir(parents=True, exist_ok=True)
    runs = []
    if mode in ("post", "both"):
        runs.append(run_ref("post"))
    if mode == "fix":
        runs.append(run_ref("work"))
    if mode in ("pre", "both"):
        runs.append(run_ref("pre"))
    if mode == "post-kill":
        runs.append(run_ref("post", kill_switch_off=True))
    if mode == "owner-session":
        runs.append(run_ref("post", scenario="owner_session"))
    if mode == "owner-session-fix":
        runs.append(run_ref("work", scenario="owner_session"))
    if mode == "owner-session-pre":
        runs.append(run_ref("pre", scenario="owner_session"))
    out = REPORTS / f"rf14_repro_{mode}.json"
    out.write_text(json.dumps(runs, ensure_ascii=False, indent=2, default=str),
                   encoding="utf-8")
    log(f"report -> {out}")
    any_zero = any(r["zero_ink"] for r in runs)
    log(f"VERDICT: {'ZERO-INK REPRODUCED' if any_zero else 'no zero-ink in this run'}")
    return 0




# ──────────────────────────────────────────────────────────────
# 7. OWNER_SESSION scenario — the Phase D gate sequence
# ──────────────────────────────────────────────────────────────
# Simulates the Owner's live-gate flow in ONE kernel:
#   (1) upload pages -> detect -> OCR               [fresh]
#   (2) EYEBALL RENDER pre-translation (the gate's
#       "DIAGONAL page eyeball / axis-aligned byte-unchanged"
#       step) — render_page(force=False) on untranslated rows
#   (3) apply 8/9 Bengali translations (Owner-like apply)
#   (4) step_4 = run_render_all(force=False, require_translation=True)
#   (5) ink probe: is the final now ZERO-TEXT?
# Also runs the control arm: same pages, render only AFTER apply.

def owner_session(ns, pages, ocr_stub_map, label):
    """Returns per-page ink table for the gated flow."""
    log(f"=== OWNER_SESSION {label} ===")

    # (1) fresh pages: detect + ocr + register inpainted
    for page in pages:
        pid = ns["init_page"](page["filename"],
                              width=page["full"].shape[1],
                              height=page["full"].shape[0],
                              image_np=page["full"], overwrite=True)
        page["page_id"] = pid
        boxes = [{"x": b["box"][0], "y": b["box"][1], "w": b["box"][2],
                  "h": b["box"][3], "score": 0.9,
                  "detector_class": b["detector_class"]}
                 for b in page["boxes"]]
        ns["rtdetr_detect"] = lambda img: {
            "text_bubble_boxes": [b for b in boxes
                                  if b["detector_class"] == "text_bubble"],
            "text_free_boxes": [b for b in boxes
                                if b["detector_class"] == "text_free"],
            "bubble_boxes": [],
        }
        ns["detect_page"](pid, page["full"], force=True)
        ns["run_ocr_engine"] = lambda name, img, region, page_id=None: (
            ocr_stub_map.get(
                tuple(int(region.get(k, 0)) for k in ("x", "y")),
                {"text": "テスト", "confidence": 0.9, "engine": name,
                 "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
                 "warnings": [], "is_english": True, "status": "ok",
                 "vertical_ocr": None})
        )
        ns["ocr_page"](pid, page["full"], force=True)
        ns["save_image_artifact"](pid, "inpainted", page["clean"], quality=95)
        # the Owner's cell-9 inpaint marks this stage; the synthetic clean
        # page is the same state -> mark it the same way (harness fidelity)
        ns["mark_stage_done"](pid, "inpaint", meta={"inpaint_engine": "synthetic"})

    # (2) eyeball render PRE-translation (the Phase D gate step)
    log("(2) eyeball render pre-translation (gate step)")
    for page in pages:
        ns["render_page"](page["page_id"], force=False)

    # (3) apply 8/9-style translations
    log("(3) applying Bengali translations (one region left untranslated)")
    df = ns["translation_df"]
    applied = 0
    for page in pages:
        rows = df[df["page_id"] == page["page_id"]]
        for i, (idx, row) in enumerate(rows.iterrows()):
            if i == 0 and page is pages[0] and len(pages) == 1:
                continue  # the "1/9 untranslated"
            key = (int(row["x"]), int(row["y"]))
            beng = ocr_stub_map.get(key, {}).get(
                "__bengali", "এই কী হয়েছে বলো তো!")
            df.at[idx, "translated_text"] = beng
            applied += 1
    ns["save_translation_df"]()
    log(f"    applied {applied} translations to translation_df")

    # (4) step_4: the UI flow = sync translate stage (cell-23) then
    #     run_render_all(force=False, require_translation=True)
    log("(4) step_4 = sync_translate_stage() + render_all_pages(force=False)")
    assert "sync_translate_stage" in ns, "cell_23 sync missing"
    ns["sync_translate_stage"]()
    ns["render_all_pages"](force=False, require_translation=True)

    # (5) ink probe
    out = []
    for page in pages:
        final = ns["load_image_artifact"](page["page_id"], "final")
        clean = page["clean"]
        zero_regions = []
        total_ink = 0
        det_rows = ns["load_json_artifact"](
            page["page_id"], "detections", default=[])
        for r in det_rows:
            x, y, w, h = r["x"], r["y"], r["width"], r["height"]
            m = 34
            x0, y0 = max(0, x - m), max(0, y - m)
            x1 = min(final.shape[1], x + w + m)
            y1 = min(final.shape[0], y + h + m)
            diff = np.abs(final[y0:y1, x0:x1].astype(int)
                          - clean[y0:y1, x0:x1].astype(int)).sum(axis=2)
            ink = int((diff > 30).sum())
            total_ink += ink
            if ink < ZERO_INK_FLOOR:
                zero_regions.append((r["id"], ink))
        log(f"  {page['filename']}: total ink={total_ink}, "
            f"zero-ink regions={zero_regions}")
        out.append({"page": page["filename"], "total_ink": total_ink,
                    "zero_regions": zero_regions})
    repro = any(o["zero_regions"] or o["total_ink"] < ZERO_INK_FLOOR
                for o in out)
    log(f"OWNER_SESSION verdict: "
        f"{'ZERO-TEXT REPRODUCED' if repro else 'text rendered'}")
    return {"pages": out, "repro": repro}


if __name__ == "__main__":
    sys.exit(main())
