#!/usr/bin/env python3
r"""MANGABD-006 B1 (Phase C) — verification suite.

Checks (all must be GREEN before commit):
  V0  vendored weights sha256 re-check (RF-5 pins + new int4 pin)
  V1  static: AST 27/27 warnings-as-errors; re-derivation equality from
      the patch manifest; 23 non-target cells byte-identical to 86d4bdf;
      key markers present exactly once; untouched functional spans
      verbatim; cell-15/25 wiring statics
  V2  non-source + top-level notebook fields identical
  V3  runtime harness: exec cells 5 -> 7 -> 8 with mocked upstream
      globals; SUCCESS banners + battery counts (5: 9/9, 7: 9/9, 8: 25/25)
  V4  real-ONNX chain smoke on samples/S003_batch2 (vendored weights):
      kellenok manual read, REAL chain recovery (openrouter no-key error
      -> kellenok), baberu manual read, vertical R1 V-3 ladder, and
      byte-fidelity of the notebook kellenok class vs the committed RF-5
      measurement (kellenok_results.json)
  V5  m002_sim_v2 fresh-run static simulator on the post-build extraction
      (0 abort sites)
  V6  cell-25 dropdown slice exec (stub widgets): CONFIG seed + observer
      propagation semantics
"""
import contextlib
import difflib
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "86d4bdf"
MANIFEST = Path("/home/z/my-project/scripts/m006_b1_patches.json")
POST_CELLS = Path("/home/z/my-project/cells_m006_b1_post")
W_MANIFEST = json.loads(
    Path("/home/z/my-project/scripts/m006_b1_weights_manifest.json").read_text()
)

PASS = 0
FAIL = 0


def check(name, cond, details=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS  {name}")
    else:
        FAIL += 1
        print(f"FAIL  {name}  {details}")


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cells_of(nb_dict):
    return ["".join(c.get("source", [])) for c in nb_dict["cells"] if True]


os.chdir(REPO)  # vendored weights resolve CWD-relative (models/...)

# ── V0: weights ─────────────────────────────────────────────
print("── V0 vendored weights ──")
for group, gkey in (("kellenok", "kellenok"), ("baberu", "baberu")):
    for rel, meta in W_MANIFEST[gkey]["files"].items():
        p = REPO / "models" / gkey / rel
        ok = p.exists() and sha256_of(p) == meta["sha256"]
        check(f"V0.{gkey}:{rel} sha256", ok,
              f"want {meta['sha256'][:16]} got {sha256_of(p) if p.exists() else 'MISSING'}")

# ── load base + post notebook ───────────────────────────────
base_raw = subprocess.run(["git", "-C", str(REPO), "show", f"{BASE_REF}:{NB_NAME}"],
                          capture_output=True, check=True).stdout
base_nb = json.loads(base_raw.decode("utf-8"))
post_raw = NB.read_bytes()
post_nb = json.loads(post_raw.decode("utf-8"))
BASE = cells_of(base_nb)
POST = cells_of(post_nb)
assert len(BASE) == len(POST) == 27

# ── V1: static ──────────────────────────────────────────────
print("── V1 static ──")
for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(POST[i], f"post_cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL V1 AST cell {i}: {w}")
check("V1.1 AST compile 27/27 (warnings-as-errors)", True)

TARGET = {5, 7, 15, 25}
non_target = [i for i in range(27) if i not in TARGET]
check("V1.2 23 non-target cells byte-identical to 86d4bdf",
      all(BASE[i] == POST[i] for i in non_target),
      str([i for i in non_target if BASE[i] != POST[i]]))

patches = json.loads(MANIFEST.read_text())
re_src = list(BASE)
applied_ok = True
for p in patches:
    if re_src[p["cell"]].count(p["old"]) != 1:
        applied_ok = False
        break
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1.3 re-derivation equality (post == base + manifest patches)",
      applied_ok and re_src == POST)

# marker presence, exactly once
MARKERS = [
    (5, "def ensure_ocr_engine(self, engine_name"),
    (5, "def unload_ocr_engine(self, engine_name"),
    (5, "def ensure_kellenok(self"),
    (5, "def ensure_baberu(self"),
    (5, "def ensure_openrouter_vision(self"),
    (5, "def unload_qwen(self"),
    (5, "def unload_kellenok(self"),
    (5, "def unload_baberu(self"),
    (5, "def unload_openrouter_vision(self"),
    (5, "class KellenokOnnxOCR:"),
    (5, "class BaberuOnnxOCR:"),
    (5, 'MANGABD_CONFIG["ocr"]["fallback_chain"] = ['),
    (5, 'vision="vision_int4.onnx"'),
    (7, "def ocr_region_with_fallback("),
    (7, "def run_ocr_engine("),
    (7, "def _ocr_region_onnx("),
    (7, "def _ocr_region_openrouter("),
    (7, '_OCR_REJECT_MARKERS = '),
    (7, "def _run_vertical_ladder("),
    (7, '"text": "[SKIP:OCR_FAILED]"'),
    (7, "# Test 26: OCR engine registry shape"),
    (7, "# Test 27: fallback chain"),
    (7, "# Test 28: chain guards"),
    (15, "ocr_page(page_id, force=force, engine_mode=engine_mode)"),
    (15, "run_ocr_all(force=force, engine_mode=engine_mode)"),
    (25, "ocr_engine_sel=widgets.Dropdown("),
    (25, "fn(engine_mode=ocr_engine_sel.value)"),
    (25, "ocr_engine_sel.observe(_apply_ocr_engine_sel,names=\"value\")"),
]
for cell, marker in MARKERS:
    check(f"V1.4 marker once [cell {cell}] {marker[:44]!r}",
          POST[cell].count(marker) == 1, f"count={POST[cell].count(marker)}")

# registry content (post cell 5)
check("V1.5 fallback chain order",
      '"qwen",\n    "openrouter_vision",\n    "kellenok",\n    "baberu",' in POST[5])
check("V1.6 all four engines carry load_fn + unload_fn (dict literals)",
      POST[5].count('"load_fn":') == 4 and POST[5].count('"unload_fn":') == 4,
      f"load_fn={POST[5].count('"load_fn":')} unload_fn={POST[5].count('"unload_fn":')}")

# untouched functional spans: AST function-segment equality (base vs post)
import ast

def fn_segment(src, name):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node)
    return None

SPAN_FNS = [
    (5, "ensure_qwen"), (5, "ensure_ovis"), (5, "unload_all"), (5, "status"),
    (7, "ocr_region"), (7, "build_ocr_row"), (7, "preprocess_for_ocr"),
    (7, "clean_ocr_output"), (7, "get_ocr_status"),
    (15, "run_full_pipeline"), (15, "run_translation_all"),
]
for cell, fname in SPAN_FNS:
    seg_base = fn_segment(BASE[cell], fname)
    seg_post = fn_segment(POST[cell], fname)
    ok = seg_base is not None and seg_base == seg_post
    check(f"V1.7 function segment [cell {cell}] {fname}", ok)
check("V1.7a _resolve_vendored_engine_dir is NEW (absent in base)",
      fn_segment(BASE[5], "_resolve_vendored_engine_dir") is None
      and fn_segment(POST[5], "_resolve_vendored_engine_dir") is not None)

def span(src, start, end):
    a = src.index(start)
    b = src.index(end, a)
    return src[a:b]

for cell, start, end in [
    (5, "class QwenVLWrapper:", 'print("  ✅ Qwen VL wrapper ready")'),
    (7, "def ocr_region(image_bgr, region", 'print("  ✅ Single region OCR ready")'),
    (7, "def build_ocr_row(", 'print("  ✅ OCR row builder ready")'),
]:
    base_span = span(BASE[cell], start, end)
    check(f"V1.7b class/section span verbatim [cell {cell}] {start[:30]!r}",
          base_span in POST[cell])

# cell 15/25 wiring statics
c15 = POST[15]
check("V1.8 run_ocr_all signature", "def run_ocr_all(force=False, engine_mode=None):" in c15)
check("V1.9 run_detection_ocr_all signature",
      "def run_detection_ocr_all(force=False, engine_mode=None):" in c15)
check("V1.10 run_detection_ocr_all -> run_ocr_all pass",
      "run_ocr_all(force=force, engine_mode=engine_mode)" in c15)
check("V1.11 run_full_pipeline untouched (config-resolved mode)",
      "run_detection_ocr_all(force=force)" in c15
      and BASE[15].count("def run_full_pipeline") == 1)
c25 = POST[25]
check("V1.12 dropdown options (auto + 4 engines)",
      '("Auto (fallback chain)","auto")' in c25 and c25.count('("kellenok","kellenok")') == 1)
check("V1.13 STEP 1-2 section includes dropdown",
      'section("STEP 1–2 • INPUT + OCR",[btn_upload,ocr_engine_sel,btn_ocr])' in c25)

# ── V2: non-source fields ───────────────────────────────────
print("── V2 non-source fields ──")
ok_cells = all(
    {k: v for k, v in base_nb["cells"][i].items() if k != "source"}
    == {k: v for k, v in post_nb["cells"][i].items() if k != "source"}
    for i in range(27)
)
ok_top = ({k: v for k, v in base_nb.items() if k != "cells"}
          == {k: v for k, v in post_nb.items() if k != "cells"})
check("V2.1 cell non-source fields identical", ok_cells)
check("V2.2 top-level fields identical", ok_top)

# ── V3: runtime harness (cells 5 -> 7 -> 8) ─────────────────
print("── V3 runtime harness ──")
tmp = Path(tempfile.mkdtemp(prefix="m006b1_"))
cfg = {
    "session_id": "m006b1test",
    "paths": {
        "session_dir": str(tmp), "session_export_dir": str(tmp),
        "models": str(tmp / "models"), "events_file": str(tmp / "events.jsonl"),
        "session_log_file": str(tmp / "session.log"),
    },
    "runtime": {"device": "cpu", "torch_dtype": "float32"},
    "translation": {},
    # cell-1-faithful ocr block (cell 5's registry merges into it)
    "ocr": {
        "engine": "qwen",
        "allowed_engines": ["qwen", "ovis", "hybrid"],
        "qwen_model_id": "Qwen/Qwen2.5-VL-3B-Instruct",
        "max_new_tokens": 512,
        "deterministic": True,
        "do_sample": False,
        "num_beams": 1,
        "temperature": 1.0,
        "top_p": 1.0,
        "min_confidence": 0.50,
        "confidence_threshold": 0.65,
        "min_crop_height": 40,
        "preprocess": {"upscale_small": True, "denoise": True},
    },
}

logs = []
def fake_log_event(msg, level="INFO", **kw):
    logs.append((level, str(msg)))

def fake_get_page(page_id, required=False):
    return {"page_id": page_id, "original_filename": page_id}

def fake_crop_bubble_with_context(image_bgr, region, context_ratio=0.15):
    # region-box crop stand-in for cell 6's real context-crop (baberu has no
    # det model — it must see the REGION, not the page, to read correctly)
    x = int(region.get("x", 0))
    y = int(region.get("y", 0))
    w = int(region.get("width", image_bgr.shape[1]))
    h = int(region.get("height", image_bgr.shape[0]))
    return image_bgr[y : y + h, x : x + w]

ns = {
    "MANGABD_CONFIG": cfg,
    "log_event": fake_log_event,
    "MANGABD_SECRETS": {"openrouter_api_key": "sk-test", "hf_token": ""},
    "__name__": "__m006b1__",
}

buf5 = io.StringIO()
ok5 = True
# DISCLOSED HARNESS-ONLY SUBSTITUTION: cell 5:104 hardcodes the Colab-root
# HF cache (QWEN_LOCAL_CACHE = Path("/root/.cache/huggingface/hub") + a
# module-level mkdir). Colab runs as root; this sandbox user cannot create
# /root/*. The exec below redirects ONLY that one path string to a temp dir
# — asserted to be a single-substring difference; every other byte of the
# exec'd source equals POST[5] (which is itself proven against git by
# V1.2/V1.3/V2). No repository byte is touched.
ROOT_CACHE = 'Path("/root/.cache/huggingface/hub")'
HARNESS5_DIR = tmp / "hfhub"
harness5 = POST[5].replace(ROOT_CACHE, f'Path("{HARNESS5_DIR}")')
check("V3.0a harness substitution is exactly one substring (disclosed)",
      POST[5].count(ROOT_CACHE) == 1 and harness5 != POST[5]
      and len(harness5) - len(POST[5])
      == len(str(HARNESS5_DIR)) - len("/root/.cache/huggingface/hub"))
try:
    with contextlib.redirect_stdout(buf5):
        exec(compile(harness5, "cell_05.py", "exec"), ns)
except Exception as e:
    ok5 = False
    print(f"      cell5 exception: {type(e).__name__}: {e}")
    print(buf5.getvalue()[-1500:])
out5 = buf5.getvalue()
tests5 = list(ns.get("tests", []))
check("V3.1 cell 5 execs clean", ok5)
check("V3.2 cell 5 SUCCESS banner", "Cell 5 result: SUCCESS" in out5)
check("V3.3 cell 5 battery 9/9", len(tests5) == 9 and all(tests5),
      f"n={len(tests5)} passed={sum(tests5)}")
check("V3.4 registry banner in cell 5 output",
      "3b. OCR engine registry (MANGABD-006 B1)" in out5
      and "qwen -> openrouter_vision -> kellenok -> baberu" in out5)
check("V3.5 cell-1 ocr keys preserved (additive merge)",
      cfg["ocr"]["qwen_model_id"] == "Qwen/Qwen2.5-VL-3B-Instruct"
      and cfg["ocr"]["deterministic"] is True
      and cfg["ocr"]["do_sample"] is False)
check("V3.6 registry merged + allowed_engines derived",
      cfg["ocr"]["engine"] == "auto"
      and cfg["ocr"]["allowed_engines"] == ["qwen", "openrouter_vision", "kellenok", "baberu"]
      and cfg["ocr"]["fallback_chain"] == ["qwen", "openrouter_vision", "kellenok", "baberu"])

ns["get_page"] = fake_get_page
ns["crop_bubble_with_context"] = fake_crop_bubble_with_context
ns["TRANSLATION_DF_COLUMNS"] = [
    "page_id", "page", "id", "region_type", "detector_class", "detector_score",
    "parent_bubble_id", "x", "y", "width", "height", "angle", "original_text",
    "translated_text", "confidence", "ocr_engine", "translator_engine",
    "quality_score", "is_english", "bengali_valid", "status",
]
buf7 = io.StringIO()
ok7 = True
try:
    with contextlib.redirect_stdout(buf7):
        exec(compile(POST[7], "cell_07.py", "exec"), ns)
except Exception as e:
    ok7 = False
    print(f"      cell7 exception: {type(e).__name__}: {e}")
    print(buf7.getvalue()[-2000:])
out7 = buf7.getvalue()
tests7 = list(ns.get("tests", []))
check("V3.7 cell 7 execs clean", ok7)
check("V3.8 cell 7 SUCCESS banner", "Cell 7 result: SUCCESS" in out7)
check("V3.9 cell 7 battery 9/9 (6 original + Tests 26-28)",
      len(tests7) == 9 and all(tests7), f"n={len(tests7)} passed={sum(tests7)}")
for tname in ("OCR engine registry (M6-B1)",
              "OCR fallback chain auto/manual (M6-B1)",
              "OCR chain guards + wiring (M6-B1)"):
    check(f"V3.10 new test passing: {tname}", f"✅ {tname}" in out7)
check("V3.11 zero test failures in cell 7 output", "❌ " not in out7)
check("V3.12 chain-ready banner", "✅ OCR fallback chain ready (M6-B1)" in out7)

buf8 = io.StringIO()
ok8 = True
try:
    with contextlib.redirect_stdout(buf8):
        exec(compile(POST[8], "cell_08.py", "exec"), ns)
except Exception as e:
    ok8 = False
    print(f"      cell8 exception: {type(e).__name__}: {e}")
    print(buf8.getvalue()[-2000:])
out8 = buf8.getvalue()
tests8 = list(ns.get("tests", []))
check("V3.13 cell 8 execs clean (byte-identical battery)", ok8)
check("V3.14 cell 8 SUCCESS banner", "Cell 8 result: SUCCESS" in out8)
check("V3.15 cell 8 battery 25/25", len(tests8) == 25 and all(tests8),
      f"n={len(tests8)} passed={sum(tests8)}")
check("V3.16 zero test failures in cell 8 output", "❌ " not in out8)

# ── V4: real-ONNX chain smoke ───────────────────────────────
print("── V4 real-ONNX chain smoke (vendored weights) ──")
import cv2  # noqa: E402
import numpy as np  # noqa: E402

sample = REPO / "samples" / "S003_batch2"
dets = json.loads((sample / "detections.json").read_text())
img = cv2.imread(str(sample / "original.jpg"))
regions = {d["id"]: d for d in dets}
r3 = regions[3]
r1 = regions[1]

# clear the fake key so the openrouter adapter takes the clean no-key path
ns["MANGABD_SECRETS"]["openrouter_api_key"] = ""
os.environ.pop("OPENROUTER_API_KEY", None)

chain_fn = ns["ocr_region_with_fallback"]
cfg_ocr = ns["MANGABD_CONFIG"]["ocr"]
cfg_ocr["fallback_chain"] = ["qwen", "openrouter_vision", "kellenok", "baberu"]

buf_s = io.StringIO()
with contextlib.redirect_stdout(buf_s):
    res_k = chain_fn(img, r3, page_id="smoke.jpg", engine_mode="kellenok")
check("V4.1 kellenok manual mode reads R3",
      res_k.get("engine") == "kellenok" and "KOGANEI" in str(res_k.get("text", "")).upper()
      and res_k.get("fallback_trace", [{}])[-1].get("outcome") == "ok",
      f"engine={res_k.get('engine')} text={res_k.get('text','')[:60]!r}")

cfg_ocr["fallback_chain"] = ["openrouter_vision", "kellenok"]
buf_r = io.StringIO()
with contextlib.redirect_stdout(buf_r):
    res_r = chain_fn(img, r3, page_id="smoke.jpg", engine_mode="auto")
trace_r = res_r.get("fallback_trace", [])
out_r = buf_r.getvalue()
check("V4.2 REAL chain recovery: openrouter no-key error -> kellenok",
      [t.get("outcome") for t in trace_r] == ["error", "ok"]
      and trace_r[0]["engine"] == "openrouter_vision"
      and trace_r[1]["engine"] == "kellenok"
      and res_r.get("engine") == "kellenok"
      and "KOGANEI" in str(res_r.get("text", "")).upper(),
      f"trace={trace_r}")
check("V4.3 recovery banner visible", "🔁 OCR fallback" in out_r)
warn_engines = [m for lv, m in logs if lv == "WARN" and "openrouter_vision failed" in m]
check("V4.4 engine failure logged via log_event", len(warn_engines) >= 1)

buf_b = io.StringIO()
with contextlib.redirect_stdout(buf_b):
    res_b = chain_fn(img, r3, page_id="smoke.jpg", engine_mode="baberu")
check("V4.5 baberu manual mode reads R3 (vendored int4 build)",
      res_b.get("engine") == "baberu" and "KOGANEI" in str(res_b.get("text", "")).upper(),
      f"engine={res_b.get('engine')} text={res_b.get('text','')[:60]!r}")
_res_after_b = [k for k in ("qwen", "kellenok", "baberu")
               if k in ns["model_manager"].instances]
check("V4.5b single-resident discipline: kellenok EVICTED by baberu cold load",
      _res_after_b == ["baberu"], f"resident={_res_after_b}")

buf_v = io.StringIO()
with contextlib.redirect_stdout(buf_v):
    res_v = chain_fn(img, r1, page_id="smoke.jpg", engine_mode="kellenok")
vocr = res_v.get("vertical_ocr") or {}
check("V4.6 vertical R1 runs the V-3 ladder (chosen_orientation + scores)",
      res_v.get("engine") == "kellenok"
      and vocr.get("chosen_orientation") in ("rotate_90_clockwise", "rotate_90_counterclockwise")
      and set(vocr.get("candidate_scores", {}))
      == {"rotate_90_clockwise", "rotate_90_counterclockwise"}
      and len(str(res_v.get("text", ""))) > 0,
      f"vertical_ocr={vocr}")

inst = ns["model_manager"].instances
resident_local = [k for k in ("qwen", "kellenok", "baberu") if k in inst]
check("V4.7 single-resident discipline: baberu EVICTED by kellenok reload",
      resident_local == ["kellenok"],
      f"resident={resident_local}")

# byte fidelity: notebook kellenok class vs the committed RF-5 measurement
ns["model_manager"].ensure_ocr_engine("kellenok", force=True)
kell = ns["model_manager"].instances["kellenok"]
x, y, w, h = r3["x"], r3["y"], r3["width"], r3["height"]
crop3 = img[y : y + h, x : x + w]
text_direct = kell.read_crop(crop3)[0]
committed_k = json.loads((REPO / "m006_bench" / "results" / "kellenok_results.json").read_text())
committed_r3 = next(r for r in committed_k["regions"]
                    if r["region_id"] == 3 and r["variant"] == "upright")
check("V4.8 notebook kellenok class reproduces the committed RF-5 R3 read byte-exactly",
      text_direct == committed_r3["text"],
      f"notebook={text_direct[:60]!r} committed={committed_r3['text'][:60]!r}")

# manual failure terminal state (no engines) — config-restored chain
cfg_ocr["fallback_chain"] = ["qwen", "openrouter_vision", "kellenok", "baberu"]
buf_m = io.StringIO()
with contextlib.redirect_stdout(buf_m):
    res_m = chain_fn(img, r3, page_id="smoke.jpg", engine_mode="baberu")
check("V4.9 manual baberu after kellenok force-reload (evict+reload discipline)",
      res_m.get("engine") == "baberu" and "KOGANEI" in str(res_m.get("text", "")).upper())
_res_after_m = [k for k in ("qwen", "kellenok", "baberu")
                if k in ns["model_manager"].instances]
check("V4.9b single-resident after final baberu load",
      _res_after_m == ["baberu"], f"resident={_res_after_m}")

# ── V5: m002_sim_v2 ─────────────────────────────────────────
print("── V5 m002_sim_v2 fresh-run simulator ──")
POST_CELLS.mkdir(exist_ok=True)
for i in range(27):
    (POST_CELLS / f"cell_{i:02d}.py").write_text(POST[i], encoding="utf-8")
sim = subprocess.run([sys.executable, "/home/z/my-project/scripts/m005_sim2.py",
                      str(POST_CELLS)], capture_output=True, text=True)
sim_out = sim.stdout
check("V5.1 sim runs", sim.returncode == 0, sim_out[-300:] + sim.stderr[-300:])
check("V5.2 m002_sim_v2 = 0 abort sites",
      "ABORT-CLASS findings (unguarded, unresolvable): 0" in sim_out,
      sim_out[-500:])

# ── V6: cell-25 dropdown slice exec (stub widgets) ──────────
print("── V6 cell-25 dropdown semantics (stub widgets) ──")
class FakeDropdown:
    def __init__(self, **kw):
        self.options = kw.get("options", [])
        self.value = kw.get("value", None)
        self._observers = []
    def observe(self, fn, names):
        self._observers.append(fn)

class _FakeWidgets:
    Dropdown = FakeDropdown
    @staticmethod
    def Layout(**kw):
        return kw

c25_src = POST[25]
a = c25_src.index("# MANGABD-006 B1: OCR engine selection")
b = c25_src.index("_apply_ocr_engine_sel()  # default")
slice_src = c25_src[a:b] + "_apply_ocr_engine_sel()  # default দিয়ে CONFIG seed\n"

cfg25 = {"ocr": {"engine": "qwen"}}
ns25 = {"widgets": _FakeWidgets, "MANGABD_CONFIG": cfg25, "__name__": "__m006b1v6__"}
exec(compile(slice_src, "cell25_dropdown_slice.py", "exec"), ns25)
dd = ns25["ocr_engine_sel"]
check("V6.1 dropdown options = auto + 4 registry engines",
      [v for _, v in dd.options] == ["auto", "qwen", "openrouter_vision", "kellenok", "baberu"])
check("V6.2 seed call sets CONFIG from default value",
      cfg25["ocr"]["engine"] == "auto")
dd.value = "kellenok"
for fn in dd._observers:
    fn()
check("V6.3 observer propagates selection into CONFIG",
      cfg25["ocr"]["engine"] == "kellenok")

# ── summary ─────────────────────────────────────────────────
print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
print("notebook md5:", hashlib.md5(post_raw).hexdigest())
sys.exit(1 if FAIL else 0)
