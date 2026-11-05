#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-16 — verification instrument (branch mangabd-009-b2).

Verifies the text-ink-only tilt estimator fix (3 patches, cell 6 only)
against the Owner's LIVE REJECT on dc612d5 (7 tilted bubbles, 1/7
inherited, df angles 0.00 on truly tilted regions):

  V1  static: scope drift exactly {6} vs dc612d5; HARD cells
      {10,11,12} byte-untouched (RF-14 fix + RF-15 fix + B2 render
      engine + wrappers ride unchanged); reading-order cells
      {7,13,15,23,24} byte-identical; AST 27/27 warnings-as-errors;
      manifest re-derivation; isolation-block wiring probes; the
      kill-switch call-site + V-3 predicate + all gates byte-untouched;
      secret scan on the delta
  V2  dynamic via the RF-16 repro harness:
      V2a post @ dc612d5 -> LIVE REJECT symptom REPRODUCED (0/7
          inherited; raw all-ink tilt diluted to <60% of GT on all 7)
      V2b work @ fix     -> 7/7 within +/-3 deg (gate >= 6/7),
          horizontals 0, vertical 0/V-3
  V3  archive estimator parity: production estimator (base vs work) on
      ALL archived regions of the six sample archives (S001, S002,
      S003, S005_manual, S005_openrouter, S007) -> outputs EXACTLY
      equal (all (0.0, None)) => detections.json byte-identical
  V4  S009 full-chain (verbatim cells 1-7,10,11,12,15,23 in ONE
      namespace, RF-14/15 harness env): cell-10 battery 19/19 unique
      tests + cell-12 Test 20; S009 through the REAL detect path
      (stubbed detector boxes -> real region build incl. the RF-16
      estimator) -> render; >= 6/7 tilted rows store |angle-beta|<=3
      with quad; rendered 10/10, TypeError 0, render-fail WARN 0;
      rendered-ink orientation round-trip >= 6/7 within +/-3 deg
  V5  kill-switch (RB2-7): fresh namespace, knob OFF before detect ->
      S009 rows all angle 0.0 + bbox quads; render inked, TypeError 0;
      render-side mirror (_b2_render_angle) ON/OFF/absent law
  V6  archive render parity: S003/S007 full-chain render (span level)
      B1 main (f218b35) vs work -> byte-IDENTICAL finals
  V7  m002_sim_v2 fresh-kernel simulator on the fixed cells -> 0
      abort sites

Disclosed env-level stubs (cells stay VERBATIM; same class as the
RF-14/RF-15 harnesses): inert torch stub, /content+/root pathlib
remap, cell-00 side effects, stubbed rtdetr_detect (S009 true boxes),
stubbed run_ocr_engine, synthetic inpaint artifact, cell_04 zyddnys
torch-import tolerance.
"""
import contextlib
import io
import json
import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "dc612d5"
B1_REF = "f218b35"
BRANCH = "mangabd-009-b2"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
S003 = REPO / "samples" / "S003_batch2"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
HARNESS = REPO / "scripts" / "m009_b2_rf16_repro.py"
WORK_CELLS = Path("/home/z/my-project/cells_rf16_work")
MANIFEST = REPO / "scripts" / "m009_b2_rf16_patches.json"
RESULTS_JSON = REPO / "scripts" / "m009_b2_rf16_results.json"

RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    RESULTS.append(ok)
    print(f"  {'✅' if ok else '❌'} {name}"
          + (f"  [{detail}]" if detail else ""))


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout


def cells_at(ref):
    raw = git("show", f"{ref}:{NB_NAME}").encode("utf-8")
    nb = json.loads(raw.decode("utf-8"))
    return ["".join(c.get("source", [])) for c in nb["cells"]]


def load_cells(path):
    raw = Path(path).read_bytes()
    nb = json.loads(raw.decode("utf-8"))
    return raw, nb, ["".join(c.get("source", [])) for c in nb["cells"]]


def estimator_span(cells):
    lines = cells[6].split("\n")
    si = next(i for i, l in enumerate(lines) if "9b. MANGABD-009 B2" in l)
    ei = next(i for i, l in enumerate(lines)
              if "10. Visualization" in l and i > si)
    return "\n".join(lines[si:ei])


def make_ns():
    ns = {"__name__": "m009_b2_rf16_verify"}
    ns["MANGABD_CONFIG"] = {
        "rendering": {
            "font_size_min": 8, "font_size_max": 48, "font_size_default": 24,
            "line_spacing_factor": 1.18, "padding_ratio": 0.08,
            "use_grapheme_safe_wrap": True, "use_background_aware_color": True,
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
    ns["MANGABD_EVENTS"] = ev

    def log_event(message, level="INFO", **extra):
        ev.append({"level": level, "message": message, "extra": extra})

    ns["log_event"] = log_event
    ns["MANGABD_ASSETS"] = {"fonts": {
        "fallback_path": str(FONTS / "NotoSansJP.ttf"),
        "fallback_sha_ok": True, "fallback_size": 0,
        "fallback_license": "",
    }}
    exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
         "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)
    return ns


def install_render_stubs(ns, page_id, inpainted_bgr, detections=None):
    page_store = {page_id: {"page_id": page_id, "meta": {}}}
    ns["get_page"] = lambda pid, required=True: page_store.get(pid)
    ns["is_stage_done"] = lambda pid, stage: False
    ns["load_image_artifact"] = (
        lambda pid, kind: inpainted_bgr.copy() if kind == "inpainted" else None)
    saved = {}

    def save_image_artifact(pid, kind, img, quality=95):
        if kind == "final":
            saved[("final", pid)] = (
                np.array(img) if hasattr(img, "size") else np.asarray(img))

    ns["save_image_artifact"] = save_image_artifact
    ns["save_translation_df"] = lambda df=None: None
    ns["load_translation_df"] = lambda: None
    ns["reset_page"] = lambda pid, from_stage=None: None
    ns["load_json_artifact"] = lambda pid, name, default=None: (
        list(detections) if (name == "detections" and detections)
        else (default if default is not None else None))
    metas = {}

    def mark_stage_done(pid, stage, meta=None):
        metas[pid] = dict(meta or {})
        if pid in page_store:
            page_store[pid]["meta"].update(dict(meta or {}))

    ns["mark_stage_done"] = mark_stage_done
    ns["_harness_saved"] = saved
    ns["_harness_metas"] = metas
    return ns


def build_translation_df(page_id, det_rows, tr_rows):
    tr_by_id = {int(r["id"]): r for r in tr_rows}
    recs = []
    for d in det_rows:
        t = tr_by_id.get(int(d["id"]), {})
        recs.append({
            "page_id": page_id,
            "id": int(d["id"]),
            "x": int(d["x"]), "y": int(d["y"]),
            "width": int(d["width"]), "height": int(d["height"]),
            "angle": float(d.get("angle", 0.0)),
            "region_type": d.get("region_type", "overlay"),
            "translated_text": str(t.get("translated_text", "") or ""),
            "bengali_valid": bool(t.get("bengali_valid", False)),
            "status": t.get("status", ""),
        })
    return pd.DataFrame(recs)


def extract_span(src, start_marker, end_marker=None):
    lines = src.split("\n")
    si = next(i for i, l in enumerate(lines) if start_marker in l)
    if end_marker is None:
        return "\n".join(lines[si:])
    ei = next(i for i, l in enumerate(lines) if end_marker in l and i > si)
    return "\n".join(lines[si:ei])


def cell10_spans(cells):
    cfg = extract_span(cells[10], "# 2. Rendering config defaults",
                       "# 3. Text helpers")
    core = extract_span(cells[10], "# 3. Text helpers", "# 10. Self-tests")
    return cfg, core


def wrapper_span(cell_src, work_cut=False):
    if not work_cut:
        return cell_src
    lines = cell_src.split("\n")
    ei = next(i for i, l in enumerate(lines)
              if "7.6) MANGABD-009 B2 RF-15" in l)
    return "\n".join(lines[:ei])


print("=" * 72)
print("MANGABD-009 B2 RF-16 — VERIFY (branch mangabd-009-b2)")
print("=" * 72)

# ════════════════════════════════════════════════════════════════════
# V1 — static integrity
# ════════════════════════════════════════════════════════════════════
print("\n── V1 static integrity ──")
check("V1a branch mangabd-009-b2",
      git("branch", "--show-current").strip() == BRANCH)

raw_work, nb_work, cells_work = load_cells(NB)
cells_base = cells_at(BASE_REF)

scope = [i for i in range(27) if cells_work[i] != cells_base[i]]
check("V1b scope drift exactly {6} (RF-16 directive: keep scope {6})",
      sorted(scope) == [6], f"drift={sorted(scope)}")
for i in (10, 11, 12):
    check(f"V1c HARD cell {i} byte-untouched (RF-14 fix + RF-15 fix + "
          f"B2 render engine/wrappers ride unchanged)",
          cells_work[i] == cells_base[i])
for i in (7, 13, 15, 23, 24):
    check(f"V1d cell {i} byte-identical", cells_work[i] == cells_base[i])

with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        try:
            compile(cells_work[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL cell {i} warning-as-error: {w}")
check("V1e AST compile 27/27 (warnings-as-errors)", True)

patches = json.loads(MANIFEST.read_text(encoding="utf-8"))
re_src = list(cells_base)
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"{p['name']} anchor"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1f re-derivation (work == dc612d5 + exactly the manifest)",
      all(re_src[i] == cells_work[i] for i in range(27)),
      f"{len(patches)} patches: " + "; ".join(p["name"] for p in patches))

# isolation-block wiring probes
check("V1g RF-16 isolation block wired (flood + dilate + fallback)",
      cells_work[6].count("_B2_RING_MARGIN = 6") == 1
      and cells_work[6].count("cv2.floodFill(_ff, _ffmask, (0, 0), 2)") == 1
      and cells_work[6].count("_enclosed = (ink > 0) & (cv2.dilate(") == 1
      and cells_work[6].count("if int(_enclosed.sum()) >= 100:") == 1
      and cells_work[6].count(
          "ink = _enclosed.astype(np.uint8) * 255") == 1)
# forward-only: downstream PCA/gates/quad byte-identical
tail_old = cells_base[6][cells_base[6].index("    ys, xs = np.nonzero(ink)"):]
tail_new = cells_work[6][cells_work[6].index("    ys, xs = np.nonzero(ink)"):]
check("V1h downstream PCA/gates/quad byte-identical (forward-only fix)",
      tail_old == tail_new)
# structural surfaces untouched
check("V1i V-3 predicate + kill-switch call + gates byte-untouched",
      cells_work[6].count("if w < 90 and h > 2 * max(1, w):") == 1
      and cells_work[6].count(
          'if MANGABD_CONFIG["detection"].get('
          '"b2_orientation_enable", True):') == 1
      and cells_work[6].count("if a < 5.0 or a >= 85.0:") == 1
      and cells_work[6].count("if aniso > 0.70:") == 1
      and cells_work[6].count("if abs(dev) < 5.0:") == 1
      and cells_work[6].count("if _dist > 10.0:") == 1
      and cells_work[6].count("pil_angle = round(-dev, 2)") == 1)

delta = "\n".join(p["new"] for p in patches)
hits = [kw for kw in ("api_key", "password", "secret", "token=")
        if kw in delta.lower()]
check("V1j secret scan on the patch delta", not hits, f"hits={hits}")

# ════════════════════════════════════════════════════════════════════
# V2 — dynamic via the RF-16 repro harness
# ════════════════════════════════════════════════════════════════════
print("\n── V2 dynamic (RF-16 repro harness) ──")


def run_harness(mode):
    out = subprocess.run([sys.executable, str(HARNESS), mode],
                         capture_output=True, text=True, timeout=560)
    return out.stdout + out.stderr


txt_post = run_harness("post")
check("V2a post @ dc612d5: LIVE REJECT symptom REPRODUCED",
      "RF-16 LIVE REJECT SYMPTOM REPRODUCED" in txt_post
      and "tilted within +-3.0 deg of GT: 0/7" in txt_post
      and "raw all-ink tilt diluted to <60% of GT on all tilted: YES"
      in txt_post,
      "0/7 inherited; ring+background dilution -> 5 deg snap -> 0.00")

txt_fix = run_harness("fix")
check("V2b work @ fix: 7/7 within ±3° (gate >= 6/7), H=0, V=0/V-3",
      "VERDICT fix: RF-16 FIXED (7/7 within +-3.0 deg" in txt_fix
      and "horizontals stay 0: YES" in txt_fix,
      "estimator-level S009 gate")

# ════════════════════════════════════════════════════════════════════
# V3 — archive estimator parity (all six sample archives)
# ════════════════════════════════════════════════════════════════════
print("\n── V3 archive estimator parity ──")


def make_est_ns():
    ns = {"__name__": "rf16_verify_est"}
    exec("import cv2\nimport numpy as np", ns)
    ns["MANGABD_CONFIG"] = {"detection": {}}
    ev = []

    def log_event(message, level="INFO", **extra):
        ev.append({"level": level, "message": message})

    ns["log_event"] = log_event
    return ns


ns_b = make_est_ns()
exec(compile(estimator_span(cells_base), "<base c6 9b>", "exec"), ns_b)
ns_w = make_est_ns()
exec(compile(estimator_span(cells_work), "<work c6 9b>", "exec"), ns_w)
est_b, est_w = ns_b["_estimate_region_angle"], ns_w["_estimate_region_angle"]


def archive_set():
    out = {}
    for sid in ("S001_color_webtoon", "S002_batch1", "S003_batch2",
                "S005_manual", "S005_openrouter"):
        d = REPO / "samples" / sid
        out[sid] = (cv2.imread(str(d / "original.jpg"), cv2.IMREAD_COLOR),
                    json.load(open(d / "detections.json")))
    with zipfile.ZipFile(S007_ZIP) as z:
        def rd(name):
            cand = [n for n in z.namelist() if n.endswith(name)]
            return z.read(cand[0])
        out["S007"] = (
            cv2.imdecode(np.frombuffer(rd("original.jpg"), np.uint8),
                         cv2.IMREAD_COLOR),
            json.loads(rd("detections.json")))
    return out


n_rows = n_mismatch = n_nonzero = 0
mismatch = []
for name, (img, dets) in archive_set().items():
    for r in dets:
        n_rows += 1
        args = (img, int(r["x"]), int(r["y"]),
                int(r["width"]), int(r["height"]))
        ob, ow = est_b(*args), est_w(*args)
        if ob != ow:
            n_mismatch += 1
            mismatch.append((name, r.get("id"), ob, ow))
        if ow != (0.0, None):
            n_nonzero += 1
check("V3a production estimator base == work on ALL archived regions "
      "(detections.json byte-identity by construction)",
      n_rows == 36 and n_mismatch == 0,
      f"rows={n_rows} mismatches={n_mismatch} {mismatch}")
check("V3b work estimator stores 0 tilt on 36/36 archived rows",
      n_nonzero == 0, f"nonzero={n_nonzero}")

# ════════════════════════════════════════════════════════════════════
# V4 — S009 full chain (verbatim cells, REAL detect path + render)
# ════════════════════════════════════════════════════════════════════
print("\n── V4 S009 full chain (verbatim cells harness) ──")
sys.path.insert(0, str(REPO / "scripts"))
from m009_b2_rf14_repro import (  # noqa: E402
    install_pathlib_shim, make_torch_stub, restore_pathlib,
    seed_cell00_side_effects,
)
from m009_b2_rf15_repro import exec_cells  # noqa: E402
from m009_b2_rf16_page import build_s009_page  # noqa: E402

TOL = 3.0
full, clean, regions, ink_mask = build_s009_page(str(REPO))


def match_gt(r):
    best, bi = 0, None
    for g in regions:
        gx, gy, gw, gh = g["box"]
        ix = max(0, min(r["x"] + r["width"], gx + gw) - max(r["x"], gx))
        iy = max(0, min(r["y"] + r["height"], gy + gh) - max(r["y"], gy))
        if ix * iy > best:
            best, bi = ix * iy, g
    return bi


def s009_chain(knob):
    """Exec work cells verbatim, drive S009 through the real chain.
    knob: None = default ON; False = kill-switch OFF before detect."""
    sys.modules["torch"] = make_torch_stub()
    install_pathlib_shim()
    try:
        ns, logs, battery_failed = exec_cells(WORK_CELLS,
                                              battery_must_fail=False)
    finally:
        restore_pathlib()
    if knob is False:
        ns["MANGABD_CONFIG"]["detection"]["b2_orientation_enable"] = False

    pid = ns["init_page"]("s009_diagonal.jpg", width=full.shape[1],
                          height=full.shape[0], image_np=full,
                          overwrite=True)
    boxes = [{"x": r["box"][0], "y": r["box"][1], "w": r["box"][2],
              "h": r["box"][3], "score": 0.9,
              "detector_class": "text_bubble" if r["class"] != "vertical"
              else "text_free"} for r in regions]
    ns["rtdetr_detect"] = lambda img: {
        "text_bubble_boxes": [b for b in boxes
                              if b["detector_class"] == "text_bubble"],
        "text_free_boxes": [b for b in boxes
                            if b["detector_class"] == "text_free"],
        "bubble_boxes": [],
    }
    ns["detect_page"](pid, full, force=True)
    det_rows = ns["load_json_artifact"](pid, "detections", default=[])

    ocr_stub = {}
    for r in det_rows:
        g = match_gt(r)
        ocr_stub[(int(r["x"]), int(r["y"]))] = {
            "text": g["jp"].split("\n")[0], "confidence": 0.9,
            "engine": "stub", "language_score": {"en": 1.0, "bn": 0.0,
                                                 "unknown": 0.0},
            "warnings": [], "is_english": True, "status": "ok",
            "vertical_ocr": None, "__bengali": g["bengali"],
        }
    ns["run_ocr_engine"] = lambda name, img, region, page_id=None: (
        ocr_stub.get(tuple(int(region.get(k, 0)) for k in ("x", "y")),
                     {"text": "テスト", "confidence": 0.9, "engine": name,
                      "language_score": {"en": 1.0, "bn": 0.0,
                                         "unknown": 0.0},
                      "warnings": [], "is_english": True, "status": "ok",
                      "vertical_ocr": None})
    )
    ns["ocr_page"](pid, full, force=True)
    ns["save_image_artifact"](pid, "inpainted", clean, quality=95)
    ns["mark_stage_done"](pid, "inpaint", meta={"inpaint_engine": "synthetic"})

    df = ns["translation_df"]
    for idx, row in df[df["page_id"] == pid].iterrows():
        key = (int(row["x"]), int(row["y"]))
        df.at[idx, "translated_text"] = ocr_stub.get(key, {}).get(
            "__bengali", "এই কী হয়েছে বলো তো!")
    ns["save_translation_df"]()

    ev0 = len(ns["MANGABD_EVENTS"])
    ns["sync_translate_stage"]()
    ns["run_render_all"](force=True, require_translation=True)
    events = ns["MANGABD_EVENTS"][ev0:]
    final = ns["load_image_artifact"](pid, "final")
    rows2 = ns["translation_df"][ns["translation_df"]["page_id"] == pid]
    return dict(ns=ns, logs=logs, battery_failed=battery_failed,
                det_rows=det_rows, events=events, final=final,
                rendered=int((rows2["status"] == "rendered").sum()),
                n_rows_df=len(rows2))


arm = s009_chain(None)

log10, log12 = arm["logs"][10], arm["logs"][12]
n_fail10 = sum(1 for l in log10.splitlines() if l.startswith("  ❌ "))
b2_tests = ["B2 estimator: synthetic tilt semantics (RB2-1/2/3/4 + gates)",
            "B2 render: quad-extents fit + kill-switch mirror",
            "B2 end-to-end: estimator -> render inherits the lean",
            "B2 RF-14: blank-cache trap + full-page ink "
            "(horizontal/tilted/vertical)"]
check("V4a cell-10 battery SUCCESS, 0 fail (19 unique tests incl. "
      "Tests 16-19)",
      "Cell 10 result: SUCCESS" in log10 and n_fail10 == 0
      and all(f"✅ {t}" in log10 for t in b2_tests),
      f"fail-lines={n_fail10}")
check("V4b cell-12 RF-15 Test 20 PASS, no battery raise",
      "✅ B2 RF-15: full-chain render integration (wrapper kwarg seam)"
      in log12 and arm["battery_failed"] is None,
      "RF-15 seam guard intact on RF-16 bytes")

tilted_ok = 0
h_zero = v_zero = True
for r in arm["det_rows"]:
    g = match_gt(r)
    if g["class"] == "tilted":
        tilted_ok += (abs(r["angle"] - g["beta"]) <= TOL
                      and r.get("quad") is not None)
    elif g["class"] == "horizontal":
        h_zero &= (r["angle"] == 0.0)
    else:
        v_zero &= (r["angle"] == 0.0)
check("V4c S009 detect rows: >= 6/7 tilted store |angle-beta| <= 3 + quad",
      tilted_ok >= 6, f"{tilted_ok}/7")
check("V4d horizontals stay 0; vertical stays 0 (V-3 class)",
      h_zero and v_zero)

typerr = [e for e in arm["events"]
          if "unexpected keyword argument" in str(e.get("message", ""))]
rfail = [e for e in arm["events"]
         if str(e.get("message", "")).startswith("Render failed")]
warns = [e for e in arm["events"]
         if str(e.get("level", "")).upper() in ("WARN", "WARNING")]
check("V4e S009 render: 10/10 rendered, TypeError 0, render-fail 0, "
      "WARN 0",
      arm["rendered"] == 10 and arm["n_rows_df"] == 10
      and not typerr and not rfail and not warns,
      f"rendered={arm['rendered']}/{arm['n_rows_df']} "
      f"typerr={len(typerr)} rfail={len(rfail)} warns={len(warns)}")

orient_ok = 0
for r in arm["det_rows"]:
    g = match_gt(r)
    x, y, w, h = r["x"], r["y"], r["width"], r["height"]
    m = 34
    x0, y0 = max(0, x - m), max(0, y - m)
    x1 = min(arm["final"].shape[1], x + w + m)
    y1 = min(arm["final"].shape[0], y + h + m)
    diff = np.abs(arm["final"][y0:y1, x0:x1].astype(int)
                  - clean[y0:y1, x0:x1].astype(int)).sum(axis=2)
    new_ink = diff > 30
    n_ink = int(new_ink.sum())
    pil = None
    if n_ink >= 100:
        ys, xs = np.nonzero(new_ink)
        pts = np.stack([xs, ys], 1).astype(np.float64)
        pts -= pts.mean(0)
        cov = pts.T @ pts / len(pts)
        ev_, evec = np.linalg.eigh(cov)
        ang = np.degrees(np.arctan2(evec[1, 1], evec[0, 1]))
        tilt = (ang + 180) % 180
        if tilt > 90:
            tilt -= 180
        pil = -(tilt - 90 * round(tilt / 90))
    if g["class"] == "tilted":
        orient_ok += (pil is not None and abs(pil - g["beta"]) <= TOL)
check("V4f rendered-ink orientation matches GT on >= 6/7 tilted "
      "(round-trip)",
      orient_ok >= 6, f"{orient_ok}/7")

# ════════════════════════════════════════════════════════════════════
# V5 — kill-switch (RB2-7) on the new bytes
# ════════════════════════════════════════════════════════════════════
print("\n── V5 kill-switch (RB2-7) ──")
arm_off = s009_chain(False)
all_zero = all(r["angle"] == 0.0 for r in arm_off["det_rows"])


def is_bbox_quad(r):
    q = r.get("quad")
    if q is None:
        return False
    q = np.asarray(q, dtype=float)
    x, y, w, h = r["x"], r["y"], r["width"], r["height"]
    return np.allclose(q, [[x, y], [x + w, y], [x + w, y + h], [x, y + h]])


bbox_quads = all(is_bbox_quad(r) for r in arm_off["det_rows"])
typerr_off = [e for e in arm_off["events"]
              if "unexpected keyword argument" in str(e.get("message", ""))]
ink_off = 0
for r in arm_off["det_rows"]:
    x, y, w, h = r["x"], r["y"], r["width"], r["height"]
    m = 34
    x0, y0 = max(0, x - m), max(0, y - m)
    x1 = min(arm_off["final"].shape[1], x + w + m)
    y1 = min(arm_off["final"].shape[0], y + h + m)
    diff = np.abs(arm_off["final"][y0:y1, x0:x1].astype(int)
                  - clean[y0:y1, x0:x1].astype(int)).sum(axis=2)
    ink_off += int((diff > 30).sum())
check("V5a knob OFF: S009 detect rows all angle 0.0 + bbox quads "
      "(detect-side gating through the untouched call site)",
      all_zero and bbox_quads,
      f"rows={len(arm_off['det_rows'])}")
check("V5b knob OFF: render inked + TypeError-free (straight renders)",
      arm_off["rendered"] == 10 and not typerr_off and ink_off > 5000,
      f"rendered={arm_off['rendered']} ink={ink_off} "
      f"typerr={len(typerr_off)}")

ns_v5 = arm["ns"]
_m = ns_v5["_b2_render_angle"]
ns_v5["MANGABD_CONFIG"]["detection"]["b2_orientation_enable"] = False
_off = (_m(-15.0) == 0.0 and _m(15.0) == 0.0 and _m(1.0) == 1.0)
ns_v5["MANGABD_CONFIG"]["detection"]["b2_orientation_enable"] = True
_on = (_m(-15.0) == -15.0 and _m(15.0) == 15.0
       and _m(1.0) == 1.0 and _m(0.0) == 0.0)
check("V5c render-side mirror: OFF zeroes, ON passthrough",
      _off and _on)

# ════════════════════════════════════════════════════════════════════
# V6 — archive render parity (B1 main vs work, span level)
# ════════════════════════════════════════════════════════════════════
print("\n── V6 archive render parity (S003/S007) ──")
cells_b1 = cells_at(B1_REF)


def load_sample(sid):
    if sid == "S003":
        det = json.load(open(S003 / "detections.json"))
        tr = json.load(open(S003 / "translation.json"))
        rows = tr if isinstance(tr, list) else tr.get("rows", [])
        img = cv2.imread(str(S003 / "inpainted.png"), cv2.IMREAD_COLOR)
        return det, rows, img
    with zipfile.ZipFile(S007_ZIP) as z:
        def rd(name):
            cand = [n for n in z.namelist() if n.endswith(name)]
            return z.read(cand[0])
        det = json.loads(rd("detections.json"))
        tr = json.loads(rd("translation.json"))
        rows = tr if isinstance(tr, list) else tr.get("rows", [])
        arr = cv2.imdecode(np.frombuffer(rd("inpainted.png"), np.uint8),
                           cv2.IMREAD_COLOR)
        return det, rows, arr


def build_chain(cells, page_id, inpainted, detections, tr_rows,
                work_cut_cell12=False):
    ns = install_render_stubs(make_ns(), page_id, inpainted,
                              detections=detections)
    ns["translation_df"] = build_translation_df(page_id, detections, tr_rows)
    cfg, core = cell10_spans(cells)
    exec(compile(cfg, "<c10 cfg>", "exec"), ns)
    exec(compile(core, "<c10 core>", "exec"), ns)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(wrapper_span(cells[11]), "<c11>", "exec"), ns)
        exec(compile(wrapper_span(cells[12], work_cut=work_cut_cell12),
                     "<c12>", "exec"), ns)
    return ns


for sid in ("S003", "S007"):
    det, rows, img = load_sample(sid)

    ns_b1 = install_render_stubs(make_ns(), sid, img, detections=det)
    ns_b1["translation_df"] = build_translation_df(sid, det, rows)
    cfg_b1, core_b1 = cell10_spans(cells_b1)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(cfg_b1, "<b1 c10 cfg>", "exec"), ns_b1)
        exec(compile(core_b1, "<b1 c10 core>", "exec"), ns_b1)
        exec(compile(wrapper_span(cells_b1[11]), "<b1 c11>", "exec"), ns_b1)
        exec(compile(wrapper_span(cells_b1[12]), "<b1 c12>", "exec"), ns_b1)
    ns_b1["render_page"](sid, force=True)
    b1_final = ns_b1["_harness_saved"][("final", sid)]

    ns_fw = build_chain(cells_work, sid, img, det, rows,
                        work_cut_cell12=True)
    ns_fw["render_page"](sid, force=True)
    w_final = ns_fw["_harness_saved"][("final", sid)]

    same = (b1_final.shape == w_final.shape
            and np.array_equal(b1_final, w_final))
    check(f"V6a {sid} full-chain render byte-IDENTICAL (B1 main vs work)",
          same, f"shape {b1_final.shape}")

# ════════════════════════════════════════════════════════════════════
# V7 — fresh-kernel simulator (m002_sim_v2)
# ════════════════════════════════════════════════════════════════════
print("\n── V7 fresh-kernel simulator (m002_sim_v2) ──")
WORK_CELLS.mkdir(exist_ok=True)
for i, src in enumerate(cells_work):
    (WORK_CELLS / f"cell_{i:02d}.py").write_text(src, encoding="utf-8")
sim_out = subprocess.run(
    [sys.executable, "-c",
     "import sys, importlib.util\n"
     "from pathlib import Path\n"
     "spec = importlib.util.spec_from_file_location('sim2', %r)\n"
     "m = importlib.util.module_from_spec(spec)\n"
     "spec.loader.exec_module(m)\n"
     "m.CELLS_DIR = Path(%r)\n"
     "import io, contextlib\n"
     "buf = io.StringIO()\n"
     "with contextlib.redirect_stdout(buf):\n"
     "    m.main()\n"
     "txt = buf.getvalue()\n"
     "n = txt.count('ABORT-CLASS findings (unguarded, unresolvable): 0')\n"
     "print('ABORT_ZERO' if n == 1 else 'ABORT_NONZERO')\n"
     "print(txt[txt.find('ABORT-CLASS'):txt.find('ABORT-CLASS')+120])"
     % (str(SIM), str(WORK_CELLS))],
    capture_output=True, text=True)
check("V7a m002_sim_v2 on the fixed cells: 0 abort sites",
      "ABORT_ZERO" in sim_out.stdout,
      sim_out.stdout.strip().splitlines()[-1][:100]
      if sim_out.stdout.strip() else sim_out.stderr[-100:])

# ════════════════════════════════════════════════════════════════════
# summary
# ════════════════════════════════════════════════════════════════════
n_ok = sum(RESULTS)
print("\n" + "=" * 72)
print(f"RF-16 VERIFY: {n_ok}/{len(RESULTS)} PASS")
print("=" * 72)
json.dump({"passed": n_ok, "total": len(RESULTS)},
          open(RESULTS_JSON, "w"))
sys.exit(0 if n_ok == len(RESULTS) else 1)
