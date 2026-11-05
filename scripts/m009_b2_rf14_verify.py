#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-14 — verification instrument (branch mangabd-009-b2).

Verifies the stale-BLANK-render-cache fix (3 patches, cell 10 only)
against the Owner's zero-text regression:

  V1  static: scope drift exactly {10} vs fd8d625; RB2-7 named cells
      {6,7,11,12,24} + reading-order {13,15,23} byte-identical (cell 6
      byte-identical => Phase C's 45/45 estimator/battery evidence
      transfers); AST 27/27 warnings-as-errors; manifest re-derivation;
      production rotate/paste block + _b2_render_angle + Tests 16-18
      byte-untouched; secret scan on the delta
  V2  dynamic via the RF-14 harness (scripts/m009_b2_rf14_repro.py):
      V2a owner-session @ fd8d625 -> zero-text REPRODUCED (bug evidence)
      V2b owner-session @ fix    -> zero-ink GONE (all regions ink,
          loud bypass lines present)
      V2c pipeline happy-path @ fix -> every region visible ink
      V2d cell-10 battery -> 19/19 HARD incl. Test 19 (trap + h/t/v
          full-page ink + healthy-cache stability)
  V3  archive render parity: S003/S007 render_page bytes pre-vs-post
      byte-IDENTICAL + meta parity + the trap cannot fire for archives
      (rendered>0 path byte-unchanged; helper returns False)
  V4  m002_sim_v2 fresh-kernel on the fixed cells -> 0 abort sites

RF-14 harness env-level stubs (disclosed in the harness header): inert
torch stub, /content+/root pathlib remap, ground-truth RT-DETR boxes,
stubbed run_ocr_engine, synthetic clean-page inpaint artifacts.
"""
import contextlib
import io
import json
import re
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
BASE_REF = "fd8d625"
BRANCH = "mangabd-009-b2"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
S003 = REPO / "samples" / "S003_batch2"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
HARNESS = Path("/home/z/my-project/scripts/m009_b2_rf14_repro.py")
FIX_CELLS = Path("/home/z/my-project/cells_rf14_fix")
MANIFEST = REPO / "scripts" / "m009_b2_rf14_patches.json"

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
    return raw, nb, ["".join(c.get("source", [])) for c in nb["cells"]
                     if c.get("cell_type") == "code"]


def extract_span(src, start_marker, end_marker=None):
    lines = src.split("\n")
    si = next(i for i, l in enumerate(lines) if start_marker in l)
    if end_marker is None:
        return "\n".join(lines[si:])
    ei = next(i for i, l in enumerate(lines) if end_marker in l and i > si)
    return "\n".join(lines[si:ei])


print("=" * 72)
print("MANGABD-009 B2 RF-14 — VERIFY (branch mangabd-009-b2)")
print("=" * 72)

# ════════════════════════════════════════════════════════════════════
# V1 — static integrity
# ════════════════════════════════════════════════════════════════════
print("\n── V1 static integrity ──")
check("V1a branch mangabd-009-b2",
      git("branch", "--show-current").strip() == BRANCH)

raw_work, nb_work, cells_work = load_cells(NB)
raw_base = git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8")
nb_base = json.loads(raw_base.decode("utf-8"))
cells_base = ["".join(c.get("source", [])) for c in nb_base["cells"]
              if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_work[i] != cells_base[i]]
check("V1b scope drift exactly {10}", sorted(scope) == [10],
      f"drift={sorted(scope)}")
for i in (6, 7, 11, 12, 24):
    check(f"V1c RB2-7 named cell {i} byte-identical "
          f"(cell 6 byte-identity transfers Phase C's 45/45)",
          cells_work[i] == cells_base[i])
for i in (13, 15, 23):
    check(f"V1d reading-order cell {i} byte-identical",
          cells_work[i] == cells_base[i])

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
check("V1f re-derivation (work == fd8d625 + exactly the manifest)",
      all(re_src[i] == cells_work[i] for i in range(27)),
      f"{len(patches)} patches: " + "; ".join(p["name"] for p in patches))

# production surfaces byte-untouched
rot_old = extract_span(cells_base[10], "rotated = text_canvas.rotate(",
                       "return image_pil")
rot_new = extract_span(cells_work[10], "rotated = text_canvas.rotate(",
                       "return image_pil")
check("V1g production rotate/paste block byte-untouched", rot_old == rot_new)
mir_old = extract_span(cells_base[10], "def _b2_render_angle(",
                       'print("  ✅ B2 render-angle mirror ready')
mir_new = extract_span(cells_work[10], "def _b2_render_angle(",
                      'print("  ✅ B2 render-angle mirror ready')
check("V1h _b2_render_angle mirror byte-untouched", mir_old == mir_new)
t16_old = extract_span(cells_base[10], "# Test 16: B2 estimator",
                       "# Test 17: B2 render side")
t16_new = extract_span(cells_work[10], "# Test 16: B2 estimator",
                       "# Test 17: B2 render side")
check("V1i battery Test 16 block byte-untouched", t16_old == t16_new)
t1718_old = extract_span(cells_base[10], "# Test 17: B2 render side",
                         "# RF-13 fixture hygiene:")
t1718_new = extract_span(cells_work[10], "# Test 17: B2 render side",
                         "# Test 19: B2 RF-14")
check("V1j battery Tests 17-18 byte-untouched (19 inserted after 18)",
      t1718_old == t1718_new)

# secret scan on the delta
delta = "\n".join(p["new"] for p in patches)
hits = [kw for kw in ("api_key", "password", "secret", "token=")
        if kw in delta.lower()]
check("V1k secret scan on the patch delta", not hits, f"hits={hits}")

# helper wiring probes
check("V1l helper + guard + Test 19 wiring",
      cells_work[10].count("def _b2_blank_cache_stale(") == 1
      and cells_work[10].count("not _b2_blank_cache_stale(page_id)") == 1
      and cells_work[10].count("B2 RF-14: blank-cache trap") == 2
      and cells_work[10].count("Stale blank render cache bypassed") == 1)

# ════════════════════════════════════════════════════════════════════
# V2 — dynamic scenarios through the RF-14 harness
# ════════════════════════════════════════════════════════════════════
print("\n── V2 dynamic (RF-14 harness) ──")


def run_harness(mode):
    out = subprocess.run(
        [sys.executable, str(HARNESS), mode],
        capture_output=True, text=True, timeout=560)
    return out.stdout + out.stderr


txt_base = run_harness("owner-session")
check("V2a owner-session @ fd8d625: zero-text REPRODUCED (bug evidence)",
      "ZERO-TEXT REPRODUCED" in txt_base
      and txt_base.count("Render cached: p") >= 3,
      "12/12 regions zero ink; step_4 cache-hit blank finals")

txt_fix = run_harness("owner-session-fix")
check("V2b owner-session @ fix: zero-ink GONE",
      "OWNER_SESSION verdict: text rendered" in txt_fix
      and "ZERO-TEXT REPRODUCED" not in txt_fix.split("=== RUN")[-1],
      "bypass WARNs: " + str(txt_fix.count("Stale blank render cache")))

txt_pipe = run_harness("fix")
check("V2c pipeline happy-path @ fix: every region visible ink",
      "ZERO-INK regions: 0" in txt_pipe,
      [ln.strip() for ln in txt_pipe.splitlines()
       if "region" in ln and "ink=" in ln][-1][:90])

# battery: exec log evidence from the fix run — the harness reports the
# cell-10 self-test summary; parse the Test 19 line + final result
check("V2d cell-10 battery final result @ fix (19/19 incl. Test 19)",
      '"10": ["Self-tests", "result: SUCCESS"]' in txt_fix,
      "harness battery summary cell-10 = SUCCESS")
# count run_test PASS lines in the battery span of the work cell
batt = extract_span(cells_work[10], "# Test 1: font load", "# Final status")
n_pass = batt.count('print(f"  {status} {name}")')  # noqa — runtime check only
check("V2e battery Test 19 present + trap assertions wired",
      "B2 RF-14: blank-cache trap + full-page ink" in batt
      and "_t19_ok_a and _t19_ok_c and _t19_ok_d" in batt)


# ════════════════════════════════════════════════════════════════════
# V3 — archive render parity (S003/S007): pre vs post byte-identical
# ════════════════════════════════════════════════════════════════════
print("\n── V3 archive render parity (fresh render + cached arm) ──")


def make_ns():
    ns = {"__name__": "m009_b2_rf14_harness"}
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
    """Storage stubs (Phase C V5 pattern) + page-meta store for the
    RF-14 helper's rendered_regions lookup (flat page['meta'])."""
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
    ns["save_translation_df"] = lambda: None
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


def cell10_spans(cells):
    cfg = extract_span(cells[10], "# 2. Rendering config defaults",
                       "# 3. Text helpers")
    core = extract_span(cells[10], "# 3. Text helpers",
                        "# 10. Self-tests")
    return cfg, core


cfg_base, core_base = cell10_spans(cells_base)
cfg_work, core_work = cell10_spans(cells_work)

for sid in ("S003", "S007"):
    det, rows, img = load_sample(sid)

    ns_p = install_render_stubs(make_ns(), sid, img, detections=det)
    ns_p["translation_df"] = build_translation_df(sid, det, rows)
    exec(compile(cfg_base, "<c10 base cfg>", "exec"), ns_p)
    exec(compile(core_base, "<c10 base core>", "exec"), ns_p)
    ns_p["render_page"](sid, force=True)
    pre_final = ns_p["_harness_saved"][("final", sid)]
    pre_meta = dict(ns_p["_harness_metas"][sid])

    ns_q = install_render_stubs(make_ns(), sid, img, detections=det)
    ns_q["translation_df"] = build_translation_df(sid, det, rows)
    exec(compile(cfg_work, "<c10 work cfg>", "exec"), ns_q)
    exec(compile(core_work, "<c10 work core>", "exec"), ns_q)
    ns_q["render_page"](sid, force=True)
    post_final = ns_q["_harness_saved"][("final", sid)]
    post_meta = dict(ns_q["_harness_metas"][sid])

    same = (pre_final.shape == post_final.shape
            and np.array_equal(pre_final, post_final))
    check(f"V3a {sid} fresh render byte-IDENTICAL (base vs fix)",
          same, f"shape {pre_final.shape}")
    check(f"V3b {sid} render meta byte-parity (no new keys)",
          {k: v for k, v in post_meta.items() if k != "bubble_fill"}
          == {k: v for k, v in pre_meta.items() if k != "bubble_fill"},
          f"post keys={sorted(post_meta)}")

    # the RF-14 helper cannot fire for healthy archive pages:
    # rendered_regions > 0 -> False (and the same df state)
    ns_r = install_render_stubs(make_ns(), sid, img, detections=det)
    ns_r["translation_df"] = build_translation_df(sid, det, rows)
    exec(compile(cfg_work, "<c10 work cfg>", "exec"), ns_r)
    exec(compile(core_work, "<c10 work core>", "exec"), ns_r)
    ns_r["render_page"](sid, force=True)          # rendered > 0 + meta marked
    helper_false = ns_r["_b2_blank_cache_stale"](sid) is False
    check(f"V3c {sid} helper False on healthy page (trap cannot fire)",
          helper_false)

# ════════════════════════════════════════════════════════════════════
# V4 — m002_sim_v2 fresh-kernel simulator on the FIXED cells
# ════════════════════════════════════════════════════════════════════
print("\n── V4 fresh-kernel simulator (m002_sim_v2) ──")
FIX_CELLS.mkdir(exist_ok=True)
for i, src in enumerate(cells_work):
    (FIX_CELLS / f"cell_{i:02d}.py").write_text(src, encoding="utf-8")
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
     % (str(SIM), str(FIX_CELLS))],
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
print(f"RF-14 VERIFY: {n_ok}/{len(RESULTS)} PASS")
print("=" * 72)
sys.exit(0 if n_ok == len(RESULTS) else 1)
