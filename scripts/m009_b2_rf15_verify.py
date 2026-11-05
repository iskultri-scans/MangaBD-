#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-15 — verification instrument (branch mangabd-009-b2).

Verifies the V-3 wrapper kwarg-mismatch fix (3 patches, cells {11,12}
only) against the Owner's full-chain zero-render regression:

  V1  static: scope drift exactly {11,12} vs 84aa238; HARD constraint
      cells {6,10} byte-untouched (RF-15 directive: the RF-14 fix and
      the B2 render engine must not move) + reading-order cells
      {7,13,15,23,24} byte-identical; AST 27/27 warnings-as-errors;
      manifest re-derivation; wrapper signature/forward wiring probes;
      V-3 vertical predicate + divert byte-untouched; secret scan on
      the delta
  V2  dynamic via the RF-15 harness (scripts/m009_b2_rf15_repro.py):
      V2a post @ 84aa238  -> LIVE FAILURE REPRODUCED (TypeError fit_w,
          rendered=0, zero ink — committed-bug evidence)
      V2b work @ fix      -> SEAM FIXED (12/12 rendered, h/t/v ink,
          0 TypeError events, battery Test 20 pass, no raise)
      V2c mutant          -> BATTERY FAILS ON CURRENT BYTES (new
          battery + reverted wrapper patches raises; the
          fail-on-current-bytes contract)
      V2d battery summaries -> cell-10 battery SUCCESS (19/19) +
          cell-15 SUCCESS in the fix run
  V3  render-byte equivalence + archive parity (span-level, stub
      storage — RF-14 V3 pattern):
      V3a wrapper passthrough: work wrapper chain (11+12) vs the cell-10
          base function called directly, SAME args incl. fit_w/fit_h ->
          byte-identical output (non-vertical region)
      V3b old-call compatibility: work chain vs OLD wrapper chain
          (84aa238 == B1 bytes), old signature (no fit_w/fit_h kwargs,
          _render_rotated_text's fallback call shape) -> byte-identical
      V3c V-3 vertical arm unchanged: old vs new wrapper on a
          vertical-note region -> byte-identical
      V3d archives: S003/S007 full-chain render (cell 10 + wrappers)
          B1 main (f218b35) vs work -> byte-IDENTICAL (RF-15 restores
          the B1 render through the wrapper chain)
      V3e kill-switch: b2_orientation_enable=False through the work
          chain renders ink (axis-aligned) and stays TypeError-free
  V4  m002_sim_v2 fresh-kernel simulator on the fixed cells -> 0 abort
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
BASE_REF = "84aa238"
B1_REF = "f218b35"
BRANCH = "mangabd-009-b2"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
S003 = REPO / "samples" / "S003_batch2"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
HARNESS = REPO / "scripts" / "m009_b2_rf15_repro.py"
WORK_CELLS = Path("/home/z/my-project/cells_rf15_work")
MANIFEST = REPO / "scripts" / "m009_b2_rf15_patches.json"

RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    RESULTS.append(ok)
    print(f"  {'✅' if ok else '❌'} {name}"
          + (f"  [{detail}]" if detail else ""))


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout


def load_cells(path):
    raw = Path(path).read_bytes()
    nb = json.loads(raw.decode("utf-8"))
    return raw, nb, ["".join(c.get("source", [])) for c in nb["cells"]]


def cells_at(ref):
    raw = git("show", f"{ref}:{NB_NAME}").encode("utf-8")
    nb = json.loads(raw.decode("utf-8"))
    return ["".join(c.get("source", [])) for c in nb["cells"]]


def extract_span(src, start_marker, end_marker=None):
    lines = src.split("\n")
    si = next(i for i, l in enumerate(lines) if start_marker in l)
    if end_marker is None:
        return "\n".join(lines[si:])
    ei = next(i for i, l in enumerate(lines) if end_marker in l and i > si)
    return "\n".join(lines[si:ei])


print("=" * 72)
print("MANGABD-009 B2 RF-15 — VERIFY (branch mangabd-009-b2)")
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
check("V1b scope drift exactly {11,12}", sorted(scope) == [11, 12],
      f"drift={sorted(scope)}")
for i in (6, 10):
    check(f"V1c HARD cell {i} byte-untouched (RF-15 directive: RF-14 fix "
          f"+ B2 engine must not move)",
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
check("V1f re-derivation (work == 84aa238 + exactly the manifest)",
      all(re_src[i] == cells_work[i] for i in range(27)),
      f"{len(patches)} patches: " + "; ".join(p["name"] for p in patches))

# wrapper wiring probes
check("V1g wrapper signatures accept fit_w/fit_h (both cells)",
      cells_work[11].count("fit_w=None, fit_h=None):") == 1
      and cells_work[12].count("fit_w=None, fit_h=None):") == 1)
check("V1h fallback arms forward fit_w/fit_h (both cells)",
      cells_work[11].count(
          "bold, stroke_width, text_color, padding, fit_result,\n"
          "                            fit_w, fit_h)") == 1
      and cells_work[12].count(
          "bold, stroke_width, text_color, padding, fit_result,\n"
          "                               fit_w, fit_h)") == 1)
# V-3 vertical predicate + divert byte-untouched in both wrappers
for i in (11, 12):
    vp_old = extract_span(cells_base[i], "if text and str(text).strip()",
                          "return _base_render" if i == 11
                          else "return _qc_orig_render")
    vp_new = extract_span(cells_work[i], "if text and str(text).strip()",
                          "return _base_render" if i == 11
                          else "return _qc_orig_render")
    check(f"V1i cell-{i} V-3 vertical predicate + divert byte-untouched",
          vp_old == vp_new)
# battery Test 20 wiring
check("V1j battery Test 20 wired + hard gate",
      cells_work[12].count(
          "B2 RF-15: full-chain render integration") == 3
      and cells_work[12].count(
          "Cell 12 RF-15 integration battery failed") == 1
      and cells_work[12].count('"__b2_rf15_t20__"') == 3)
# run_inpaint_render_all + final print preserved
check("V1k cell-12 run_inpaint_render_all + final print preserved",
      cells_work[12].count("def run_inpaint_render_all(") == 1
      and cells_work[12].count(
          'print("✅ QUALITY CORE active:') == 1)

# secret scan on the delta
delta = "\n".join(p["new"] for p in patches)
hits = [kw for kw in ("api_key", "password", "secret", "token=")
        if kw in delta.lower()]
check("V1l secret scan on the patch delta", not hits, f"hits={hits}")

# cells 11/12 wrappers identical between B1 and the RF-15 base
# (proves the OLD wrapper bytes predate B2 — latent seam)
cells_b1 = cells_at(B1_REF)
check("V1m base wrapper bytes == B1 main (seam is latent, not B2-introduced)",
      cells_base[11] == cells_b1[11] and cells_base[12] == cells_b1[12])

# ════════════════════════════════════════════════════════════════════
# V2 — dynamic scenarios through the RF-15 harness
# ════════════════════════════════════════════════════════════════════
print("\n── V2 dynamic (RF-15 harness) ──")


def run_harness(mode):
    out = subprocess.run(
        [sys.executable, str(HARNESS), mode],
        capture_output=True, text=True, timeout=560)
    return out.stdout + out.stderr


txt_post = run_harness("post")
check("V2a post @ 84aa238: LIVE FAILURE REPRODUCED (bug evidence)",
      "RF-15 LIVE FAILURE REPRODUCED" in txt_post
      and "unexpected keyword argument 'fit_w'" in txt_post
      and "rendered(df)=0" in txt_post,
      "12/12 zero-ink; TypeError per region")

txt_fix = run_harness("fix")
check("V2b work @ fix: SEAM FIXED (12/12 rendered + full ink + no TypeError)",
      "VERDICT work: RF-15 FIXED" in txt_fix
      and "TypeError-events=0" in txt_fix
      and "rendered(df)=12" in txt_fix
      and "zero-ink=0" in txt_fix
      and "✅ B2 RF-15: full-chain render integration" in txt_fix,
      "battery Test 20 pass, no raise")

txt_mut = run_harness("mutant")
check("V2c mutant: BATTERY FAILS ON CURRENT BYTES (fail-on-current contract)",
      "VERDICT mutant: BATTERY FAILS ON CURRENT BYTES" in txt_mut
      and "cell-12 battery raise: YES (as required)" in txt_mut,
      "new battery + old wrapper -> hard raise")

check("V2d cell-10 battery SUCCESS + cell-15 SUCCESS in the fix run",
      '"10": ["Self-tests", "result: SUCCESS"]' in txt_fix
      and '"15": ["Self-tests", "result: SUCCESS"]' in txt_fix,
      "cell-10 19/19 incl. RF-14 Test 19; cell-15 self-tests")

# ════════════════════════════════════════════════════════════════════
# V3 — render-byte equivalence + archive parity (span level)
# ════════════════════════════════════════════════════════════════════
print("\n── V3 wrapper equivalence + archive parity ──")


def make_ns():
    ns = {"__name__": "m009_b2_rf15_verify"}
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


def cell10_spans(cells):
    cfg = extract_span(cells[10], "# 2. Rendering config defaults",
                       "# 3. Text helpers")
    core = extract_span(cells[10], "# 3. Text helpers",
                        "# 10. Self-tests")
    return cfg, core


def wrapper_span(cell_src, work_cut=False):
    """Full cells 11/12 (defs + config + wrapper rebind + m8 checks +
    run_inpaint_render_all). For WORK cell 12, cut before the RF-15
    battery marker (battery fixture needs real cell-3/7 storage — its
    proof lives in V2; this span isolates RENDER behavior)."""
    if not work_cut:
        return cell_src
    lines = cell_src.split("\n")
    ei = next(i for i, l in enumerate(lines)
              if "7.6) MANGABD-009 B2 RF-15" in l)
    return "\n".join(lines[:ei])


def build_chain(cells, page_id, inpainted, detections, tr_rows,
                work_cut_cell12=False, kill_switch_off=False):
    """Exec cell-10 cfg+core + cells 11/12 wrapper spans; return ns with
    the wrapper-bound global + the captured base function."""
    ns = install_render_stubs(make_ns(), page_id, inpainted,
                              detections=detections)
    ns["translation_df"] = build_translation_df(page_id, detections, tr_rows)
    cfg, core = cell10_spans(cells)
    exec(compile(cfg, "<c10 cfg>", "exec"), ns)
    exec(compile(core, "<c10 core>", "exec"), ns)
    if kill_switch_off:
        ns["MANGABD_CONFIG"]["detection"]["b2_orientation_enable"] = False
    base_fn = ns["render_bengali_text"]
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(wrapper_span(cells[11]), "<c11>", "exec"), ns)
        exec(compile(wrapper_span(cells[12], work_cut=work_cut_cell12),
                     "<c12>", "exec"), ns)
    return ns, base_fn


def _blank(w=880, h=760):
    return np.full((h, w, 3), 255, np.uint8)


TXT = "এই কী হয়েছে বলো তো?!"
# non-vertical region (goes through the fallback arm -> base)
NV_DET = [{"id": 1, "x": 60, "y": 80, "width": 200, "height": 90,
           "angle": 0.0, "region_type": "bubble", "quad": None}]
# vertical-note region (w<90, h>2w, |angle|<=1 -> _qc_render_vertical)
V3_DET = [{"id": 1, "x": 60, "y": 80, "width": 60, "height": 240,
           "angle": 0.0, "region_type": "bubble", "quad": None}]
# tilted region with quad (fit_w/fit_h actually non-None)
TILT_DET = [{"id": 1, "x": 380, "y": 50, "width": 210, "height": 160,
             "angle": -12.0, "region_type": "bubble",
             "quad": [[371, 96], [566, 54], [589, 164], [394, 206]]}]
TR = [{"id": 1, "translated_text": TXT}]


def render_one(ns, det, fit=None):
    from PIL import Image as _PILImage
    d = det[0]
    img = _PILImage.fromarray(_blank())
    kw = {}
    if fit is not None:
        kw["fit_w"], kw["fit_h"] = fit
    out = ns["render_bengali_text"](
        img, TXT, d["x"], d["y"], d["width"], d["height"],
        angle=d["angle"], region_type="bubble",
        text_color=(0, 0, 0), stroke_width=0, **kw)
    return np.asarray(out.convert("RGB"))


# V3a: work wrapper chain vs base direct — same args incl fit_w/fit_h
ns_w, base_w = build_chain(cells_work, "v3a", _blank(), NV_DET, TR,
                           work_cut_cell12=True)
from PIL import Image as _PILImage
a_wrapped = render_one(ns_w, NV_DET, fit=(180, 70))
a_base = np.asarray(base_w(
    _PILImage.fromarray(_blank()), TXT, 60, 80, 200, 90, angle=0.0,
    region_type="bubble", text_color=(0, 0, 0), stroke_width=0,
    fit_w=180, fit_h=70).convert("RGB"))
check("V3a passthrough: work-chain == base-direct (fit_w/fit_h forwarded)",
      a_wrapped.shape == a_base.shape and np.array_equal(a_wrapped, a_base))

# tilted region with real quad-fit dims through the chain vs base
t_wrapped = render_one(ns_w, TILT_DET, fit=(205, 175))
t_base = np.asarray(base_w(
    _PILImage.fromarray(_blank()), TXT, 380, 50, 210, 160, angle=-12.0,
    region_type="bubble", text_color=(0, 0, 0), stroke_width=0,
    fit_w=205, fit_h=175).convert("RGB"))
check("V3a2 tilted quad-fit: work-chain == base-direct",
      t_wrapped.shape == t_base.shape and np.array_equal(t_wrapped, t_base),
      f"ink={int((np.abs(t_wrapped.astype(int) - 255).sum(axis=2) > 30).sum())}")

# V3b: old-call compatibility — work chain vs OLD chain, no fit kwargs
ns_o, _ = build_chain(cells_base, "v3b", _blank(), NV_DET, TR)
b_old = render_one(ns_o, NV_DET)
b_new = render_one(ns_w, NV_DET)
check("V3b old-signature call: work-chain == old-chain (no fit kwargs)",
      b_old.shape == b_new.shape and np.array_equal(b_old, b_new))

# V3c: V-3 vertical arm — old vs new wrapper chain
c_old = render_one(ns_o, V3_DET)
c_new = render_one(ns_w, V3_DET)
c_ink = int((np.abs(c_new.astype(int) - 255).sum(axis=2) > 30).sum())
check("V3c V-3 vertical arm: old-chain == work-chain (divert unchanged)",
      c_old.shape == c_new.shape and np.array_equal(c_old, c_new),
      f"vertical ink={c_ink}")

# V3d: archives — full-chain render B1 main vs work
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

    ns_fw, _ = build_chain(cells_work, sid, img, det, rows,
                           work_cut_cell12=True)
    ns_fw["render_page"](sid, force=True)
    w_final = ns_fw["_harness_saved"][("final", sid)]

    same = (b1_final.shape == w_final.shape
            and np.array_equal(b1_final, w_final))
    check(f"V3d {sid} full-chain render byte-IDENTICAL (B1 main vs work)",
          same, f"shape {b1_final.shape}")

# V3e: kill-switch through the work chain — renders ink, no TypeError
ns_k, _ = build_chain(cells_work, "v3e", _blank(), TILT_DET, TR,
                      work_cut_cell12=True, kill_switch_off=True)
ev0 = len(ns_k["MANGABD_EVENTS"])
k_out = ns_k["render_page"]("v3e", force=True)
k_typerr = sum(1 for e in ns_k["MANGABD_EVENTS"][ev0:]
               if "unexpected keyword argument" in str(e.get("message", "")))
k_ink = int((np.abs(k_out.astype(int) - 255).sum(axis=2) > 30).sum())
check("V3e kill-switch OFF: axis-aligned render through the chain, "
      "TypeError-free, ink>0",
      k_typerr == 0 and k_ink > 200,
      f"ink={k_ink} typerr={k_typerr}")

# ════════════════════════════════════════════════════════════════════
# V4 — fresh-kernel simulator (m002_sim_v2) on the fixed cells
# ════════════════════════════════════════════════════════════════════
print("\n── V4 fresh-kernel simulator (m002_sim_v2) ──")
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
check("V4 m002_sim_v2 on the fixed cells: 0 abort sites",
      "ABORT_ZERO" in sim_out.stdout,
      sim_out.stdout.strip().splitlines()[-1][:100]
      if sim_out.stdout.strip() else sim_out.stderr[-100:])

# ════════════════════════════════════════════════════════════════════
# summary
# ════════════════════════════════════════════════════════════════════
n_ok = sum(RESULTS)
print("\n" + "=" * 72)
print(f"RF-15 VERIFY: {n_ok}/{len(RESULTS)} PASS")
print("=" * 72)
sys.exit(0 if n_ok == len(RESULTS) else 1)
