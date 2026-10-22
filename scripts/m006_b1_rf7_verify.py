#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-7 — verification suite.

Checks (all must be GREEN before commit):
  V0  vendored weights sha256 re-check against the committed provenance
      manifest (RF-5 pins + M6-B1 int4 pin)
  V1  static: AST 27/27; 25 non-target cells byte-identical to d569c08
      (RF-7 touches exactly {5, 7}); re-derivation equality from the RF-7
      patch manifest; the registry text carries the manifest's pinned
      revisions + sha256 values; _resolve_vendored_engine_dir byte-untouched;
      ensure_kellenok/ensure_baberu differ from d569c08 by EXACTLY the one
      call-site line; marker counts; cell-15/25 untouched by RF-7
  V2  non-source + top-level notebook fields identical
  V3  runtime harness: exec cells 5 -> 7 -> 8 with mocked upstream globals;
      batteries 5: 9/9, 7: 10/10 (now incl. Test 29), 8: 25/25; registry
      runtime pins == manifest pins
  V4  vendored-present behavior: kellenok manual R3 read BYTE-EXACT vs the
      committed RF-5 measurement through the full new path (silent sha pass,
      identical stdout, zero network), baberu int4 read
  V5  RF-7 self-heal behavior: vendored-present zero-network proof; REAL
      sha-pinned HF download (kellenok full + baberu tokenizer pair) with
      sha verification; full _ensure_engine_weights flow on a hermetic
      empty dir; sha-mismatch refusal; download-exception diagnostic
  V6  m002_sim_v2 fresh-run static simulator on the post-build extraction
      (0 abort sites)
"""
import contextlib
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
BASE_REF = "d569c08"  # M6-B1 Phase C delivery — RF-7's direct base
MANIFEST = Path("/home/z/my-project/scripts/m006_b1_rf7_patches.json")
W_MANIFEST = json.loads(
    Path("/home/z/my-project/scripts/m006_b1_weights_manifest.json").read_text()
)
POST_CELLS = Path("/home/z/my-project/cells_rf7_post")

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


def span(src, start_marker, end_marker):
    a = src.index(start_marker)
    b = src.index(end_marker, a)
    return src[a:b]


def cells_of(nb_dict):
    return ["".join(c.get("source", [])) for c in nb_dict["cells"]]


os.chdir(REPO)  # vendored weights resolve CWD-relative (models/...)

# ── V0: vendored weights vs provenance manifest ─────────────
print("── V0 vendored weights ──")
for gkey in ("kellenok", "baberu"):
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

RF7_TARGET = {5, 7}
non_target = [i for i in range(27) if i not in RF7_TARGET]
check("V1.2 25 non-target cells byte-identical to d569c08 (RF-7 touches {5,7} only)",
      all(BASE[i] == POST[i] for i in non_target),
      str([i for i in non_target if BASE[i] != POST[i]]))

check("V1.3 cell 15 + 25 untouched by RF-7 (batch scope intact)",
      BASE[15] == POST[15] and BASE[25] == POST[25])

patches = json.loads(MANIFEST.read_text())
re_src = list(BASE)
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derivation: {p['name']}"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1.4 re-derivation equality (post == d569c08 + exactly the 9 RF-7 patches)",
      all(re_src[i] == POST[i] for i in range(27)))
check("V1.5 patch manifest scope = {5, 7}",
      {p["cell"] for p in patches} == RF7_TARGET and len(patches) == 9)

c5 = POST[5]
# registry text carries the manifest's pinned revisions + shas
pin_static_ok = True
for gkey in ("kellenok", "baberu"):
    grp = W_MANIFEST[gkey]
    pin_static_ok &= c5.count(f'"{grp["revision"]}"') == 1
    for rel, meta in grp["files"].items():
        pin_static_ok &= c5.count(f'"{meta["sha256"]}"') == 1
        pin_static_ok &= c5.count(f'"{rel}"') >= 1
check("V1.6 registry text carries every manifest revision + sha256 pin exactly once",
      pin_static_ok)
check("V1.7 hf_repo pins present",
      c5.count('"hf_repo": "Kellenok/PP-OCRv6_manga"') == 1
      and c5.count('"hf_repo": "genshiai-daichi/baberu-ocr"') == 1)

# untouched function: _resolve_vendored_engine_dir byte-identical
res_span_base = span(BASE[5], "    def _resolve_vendored_engine_dir(self, engine_name):",
                     "    def ensure_kellenok(self, force=False):")
res_span_post = span(POST[5], "    def _resolve_vendored_engine_dir(self, engine_name):",
                     "    def ensure_kellenok(self, force=False):")
check("V1.8 _resolve_vendored_engine_dir byte-identical (legacy path kept)",
      res_span_base == res_span_post)

# changed functions: exactly the one call-site line
sys.path.insert(0, "/home/z/my-project/scripts")
from m006_b1_rf7_content import C5_KELLENOK_CALL_NEW, C5_KELLENOK_CALL_OLD

k_span_base = span(BASE[5], "    def ensure_kellenok(self, force=False):",
                   "    def ensure_baberu(self, force=False):")
k_span_post = span(POST[5], "    def ensure_kellenok(self, force=False):",
                   "    def ensure_baberu(self, force=False):")
check("V1.9 ensure_kellenok differs from d569c08 by exactly the call-site line",
      k_span_post == k_span_base.replace(C5_KELLENOK_CALL_OLD, C5_KELLENOK_CALL_NEW)
      and k_span_base.count(C5_KELLENOK_CALL_OLD) == 1)

b_span_base = span(BASE[5], "    def ensure_baberu(self, force=False):",
                   "    def ensure_openrouter_vision(self, force=False):")
b_span_post = span(POST[5], "    def ensure_baberu(self, force=False):",
                   "    def ensure_openrouter_vision(self, force=False):")
b_call_old = '            weights_dir = self._resolve_vendored_engine_dir("baberu")'
b_call_new = '            weights_dir = self._ensure_engine_weights("baberu")'
check("V1.10 ensure_baberu differs from d569c08 by exactly the call-site line",
      b_span_post == b_span_base.replace(b_call_old, b_call_new)
      and b_span_base.count(b_call_old) == 1)

# marker counts
check("V1.11 self-heal method wiring counts",
      c5.count("def _ensure_engine_weights(") == 1
      and c5.count('self._ensure_engine_weights("kellenok")') == 1
      and c5.count('self._ensure_engine_weights("baberu")') == 1
      and c5.count("def _download_engine_file(") == 1
      and c5.count("def _verify_engine_weights(") == 1
      and c5.count("def _engine_weights_diagnostic(") == 1
      and c5.count("def _engine_weights_candidates(") == 1
      and c5.count("def _sha256_of_file(path):") == 1)
check("V1.12 legacy resolution no longer called by the two loaders",
      'self._resolve_vendored_engine_dir("kellenok")' not in k_span_post
      and 'self._resolve_vendored_engine_dir("baberu")' not in b_span_post)

c7 = POST[7]
check("V1.13 Test 29 present exactly once in cell 7",
      c7.count("OCR weights self-heal (RF-7)") == 2  # run_test call + except path
      and c7.count("# Test 29: weights self-heal") == 1)
check("V1.14 Test 29 hermetic (no real network): downloader monkey-patched",
      "model_manager._download_engine_file = _w29_downloader" in c7
      and "model_manager._engine_weights_candidates = _w29_candidates" in c7
      and "NO real network" in c7)
check("V1.15 cell-7 battery numbering header updated",
      "# MANGABD-006 B1 — Tests 26-29" in c7
      and "# MANGABD-006 B1 — Tests 26-28" not in c7)
check("V1.16 cell-8 battery byte-untouched (Tests 1-25)",
      BASE[8] == POST[8])

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
tmp = Path(tempfile.mkdtemp(prefix="m006b1rf7_"))
cfg = {
    "session_id": "m006b1rf7test",
    "paths": {
        "session_dir": str(tmp), "session_export_dir": str(tmp),
        "models": str(tmp / "models"), "events_file": str(tmp / "events.jsonl"),
        "session_log_file": str(tmp / "session.log"),
    },
    "runtime": {"device": "cpu", "torch_dtype": "float32"},
    "translation": {},
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
    x = int(region.get("x", 0))
    y = int(region.get("y", 0))
    w = int(region.get("width", image_bgr.shape[1]))
    h = int(region.get("height", image_bgr.shape[0]))
    return image_bgr[y : y + h, x : x + w]

ns = {
    "MANGABD_CONFIG": cfg,
    "log_event": fake_log_event,
    "MANGABD_SECRETS": {"openrouter_api_key": "sk-test", "hf_token": ""},
    "__name__": "__m006b1rf7__",
}

# DISCLOSED HARNESS-ONLY SUBSTITUTION (same class as the M6-B1 verify):
# cell 5 hardcodes the Colab-root HF cache path; this sandbox user cannot
# create /root/*. Exactly one substring redirected to a temp dir; no
# repository byte touched.
ROOT_CACHE = 'Path("/root/.cache/huggingface/hub")'
HARNESS5_DIR = tmp / "hfhub"
harness5 = POST[5].replace(ROOT_CACHE, f'Path("{HARNESS5_DIR}")')
check("V3.0a harness substitution is exactly one substring (disclosed)",
      POST[5].count(ROOT_CACHE) == 1 and harness5 != POST[5]
      and len(harness5) - len(POST[5])
      == len(str(HARNESS5_DIR)) - len("/root/.cache/huggingface/hub"))

buf5 = io.StringIO()
ok5 = True
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
check("V3.5 cell-1 ocr keys preserved (additive merge intact)",
      cfg["ocr"]["qwen_model_id"] == "Qwen/Qwen2.5-VL-3B-Instruct"
      and cfg["ocr"]["deterministic"] is True
      and cfg["ocr"]["do_sample"] is False)

# runtime registry pins == manifest pins
rt_pins_ok = True
for gkey in ("kellenok", "baberu"):
    rt_spec = cfg["ocr"]["engines"][gkey]
    grp = W_MANIFEST[gkey]
    rt_pins_ok &= rt_spec.get("hf_repo") == grp["repo"]
    rt_pins_ok &= rt_spec.get("hf_revision") == grp["revision"]
    rt_files = rt_spec.get("files", {})
    rt_pins_ok &= set(rt_files.keys()) == set(grp["files"].keys())
    for rel, meta in grp["files"].items():
        rt_pins_ok &= rt_files[rel]["sha256"] == meta["sha256"]
        rt_pins_ok &= int(rt_files[rel]["size"]) == int(meta["size"])
check("V3.6 runtime registry pins == provenance manifest (repo+rev+sha+size)",
      rt_pins_ok)
check("V3.7 self-heal methods on the runtime ModelManager",
      all(hasattr(ns["model_manager"], m) for m in
          ("_ensure_engine_weights", "_download_engine_file",
           "_verify_engine_weights", "_engine_weights_diagnostic",
           "_engine_weights_candidates"))
      and "_sha256_of_file" in ns)  # module-level helper

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
check("V3.8 cell 7 execs clean", ok7)
check("V3.9 cell 7 SUCCESS banner", "Cell 7 result: SUCCESS" in out7)
check("V3.10 cell 7 battery 10/10 (6 original + Tests 26-29)",
      len(tests7) == 10 and all(tests7),
      f"n={len(tests7)} passed={sum(tests7)}")
for tname in ("OCR engine registry (M6-B1)",
              "OCR fallback chain auto/manual (M6-B1)",
              "OCR chain guards + wiring (M6-B1)",
              "OCR weights self-heal (RF-7)"):
    check(f"V3.11 test passing: {tname}", f"✅ {tname}" in out7)
check("V3.12 zero test failures in cell 7 output", "❌ " not in out7)
check("V3.13 chain-ready banner", "✅ OCR fallback chain ready (M6-B1)" in out7)
# Test 29 restored the registry (no fake-pin leakage into subsequent cells)
check("V3.14 Test 29 restored the real kellenok pins",
      cfg["ocr"]["engines"]["kellenok"]["hf_revision"]
      == W_MANIFEST["kellenok"]["revision"]
      and len(cfg["ocr"]["engines"]["kellenok"]["files"]) == 3)

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
check("V3.15 cell 8 execs clean (byte-identical battery)", ok8)
check("V3.16 cell 8 SUCCESS banner", "Cell 8 result: SUCCESS" in out8)
check("V3.17 cell 8 battery 25/25", len(tests8) == 25 and all(tests8),
      f"n={len(tests8)} passed={sum(tests8)}")
check("V3.18 zero test failures in cell 8 output", "❌ " not in out8)

# ── V4: vendored-present behavior (real ONNX) ────────────────
print("── V4 vendored-present behavior (real ONNX, repo weights) ──")
import cv2  # noqa: E402
import numpy as np  # noqa: E402

sample = REPO / "samples" / "S003_batch2"
dets = json.loads((sample / "detections.json").read_text())
img = cv2.imread(str(sample / "original.jpg"))
regions = {d["id"]: d for d in dets}
r3 = regions[3]

ns["MANGABD_SECRETS"]["openrouter_api_key"] = ""
os.environ.pop("OPENROUTER_API_KEY", None)

chain_fn = ns["ocr_region_with_fallback"]
cfg_ocr = ns["MANGABD_CONFIG"]["ocr"]
cfg_ocr["fallback_chain"] = ["qwen", "openrouter_vision", "kellenok", "baberu"]

buf_s = io.StringIO()
with contextlib.redirect_stdout(buf_s):
    res_k = chain_fn(img, r3, page_id="smoke.jpg", engine_mode="kellenok")
smoke_out = buf_s.getvalue()
check("V4.1 kellenok manual mode reads R3 through the new path",
      res_k.get("engine") == "kellenok" and "KOGANEI" in str(res_k.get("text", "")).upper()
      and res_k.get("fallback_trace", [{}])[-1].get("outcome") == "ok",
      f"engine={res_k.get('engine')} text={res_k.get('text','')[:60]!r}")
check("V4.2 vendored-present stdout unchanged (M6-B1 load banner, no download banner)",
      "📥 Loading kellenok ONNX (CPU, vendored weights)" in smoke_out
      and "vendored weights নেই" not in smoke_out
      and "HF hub থেকে" not in smoke_out
      and "sha-pinned download" not in smoke_out)

# byte fidelity: notebook kellenok class vs the committed RF-5 measurement
kell = ns["model_manager"].instances["kellenok"]
x, y, w, h = r3["x"], r3["y"], r3["width"], r3["height"]
crop3 = img[y : y + h, x : x + w]
text_direct = kell.read_crop(crop3)[0]
committed_k = json.loads((REPO / "m006_bench" / "results" / "kellenok_results.json").read_text())
committed_r3 = next(r for r in committed_k["regions"]
                    if r["region_id"] == 3 and r["variant"] == "upright")
check("V4.3 vendored kellenok reproduces the committed RF-5 R3 read byte-exactly",
      text_direct == committed_r3["text"],
      f"notebook={text_direct[:60]!r} committed={committed_r3['text'][:60]!r}")

buf_b = io.StringIO()
with contextlib.redirect_stdout(buf_b):
    res_b = chain_fn(img, r3, page_id="smoke.jpg", engine_mode="baberu")
check("V4.4 baberu manual mode reads R3 (int4, full new path)",
      res_b.get("engine") == "baberu" and "KOGANEI" in str(res_b.get("text", "")).upper(),
      f"engine={res_b.get('engine')} text={res_b.get('text','')[:60]!r}")

# ── V5: RF-7 self-heal behavior ──────────────────────────────
print("── V5 RF-7 self-heal behavior ──")
mm = ns["model_manager"]
orig_candidates = mm._engine_weights_candidates
orig_downloader = mm._download_engine_file

# V5.1 vendored present → zero network (downloader must not fire)
def _no_network_dl(*a, **k):
    raise AssertionError("network touched with vendored weights present!")

try:
    mm._download_engine_file = _no_network_dl
    got_dir = mm._ensure_engine_weights("kellenok")
    v51 = (Path(got_dir).resolve() == (REPO / "models" / "kellenok").resolve())
except AssertionError as e:
    v51 = False
finally:
    mm._download_engine_file = orig_downloader
check("V5.1 vendored present → sha-verify + use, downloader NEVER called", v51)

# V5.2 REAL downloader: kellenok full set at the pinned revision
real_dl_dir = Path(tempfile.mkdtemp(prefix="m006b1rf7_dl_"))
try:
    for rel, meta in W_MANIFEST["kellenok"]["files"].items():
        dest = real_dl_dir / "kellenok" / rel
        mm._download_engine_file(
            W_MANIFEST["kellenok"]["repo"],
            W_MANIFEST["kellenok"]["revision"],
            rel,
            dest,
        )
        check(f"V5.2 REAL HF download kellenok:{rel} sha == pin",
              dest.is_file() and sha256_of(dest) == meta["sha256"])
except Exception as e:
    check("V5.2 REAL HF download kellenok (pinned rev resolves)", False,
          f"{type(e).__name__}: {str(e)[:160]}")

# V5.3 REAL downloader: baberu tokenizer pair at the pinned revision
try:
    for rel in ("tokenizer/vocab.json", "tokenizer/tokenizer_config.json"):
        meta = W_MANIFEST["baberu"]["files"][rel]
        dest = real_dl_dir / "baberu" / rel
        mm._download_engine_file(
            W_MANIFEST["baberu"]["repo"],
            W_MANIFEST["baberu"]["revision"],
            rel,
            dest,
        )
        check(f"V5.3 REAL HF download baberu:{rel} sha == pin",
              dest.is_file() and sha256_of(dest) == meta["sha256"])
except Exception as e:
    check("V5.3 REAL HF download baberu tokenizer pair (pinned rev resolves)",
          False, f"{type(e).__name__}: {str(e)[:160]}")

# V5.4 full production flow, hermetic empty dir, REAL downloader
# (HF cache hit from V5.2 — no new bytes over the wire)
try:
    flow_dir = Path(tempfile.mkdtemp(prefix="m006b1rf7_flow_")) / "kellenok"
    flow_dir.mkdir(parents=True)
    mm._engine_weights_candidates = lambda engine_name: [flow_dir]
    got = mm._ensure_engine_weights("kellenok")
    v54 = (Path(got) == flow_dir
           and all(sha256_of(flow_dir / rel) == meta["sha256"]
                   for rel, meta in W_MANIFEST["kellenok"]["files"].items()))
except Exception as e:
    v54 = False
    print(f"      V5.4 exception: {type(e).__name__}: {str(e)[:200]}")
finally:
    mm._engine_weights_candidates = orig_candidates
check("V5.4 full flow: empty dir → sha-pinned download → verify → return dir", v54)

# V5.5 sha mismatch → refusal (hermetic, monkey-patched downloader)
try:
    bad_dir = Path(tempfile.mkdtemp(prefix="m006b1rf7_bad_")) / "kellenok"
    bad_dir.mkdir(parents=True)
    mm._engine_weights_candidates = lambda engine_name: [bad_dir]

    def _wrong_bytes_dl(repo_id, revision, filename, dest_path):
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        Path(dest_path).write_bytes(b"rf7-corrupted-download")
    mm._download_engine_file = _wrong_bytes_dl

    refusal = None
    try:
        mm._ensure_engine_weights("kellenok")
    except RuntimeError as r:
        refusal = str(r)
    v55 = (refusal is not None and "sha mismatch" in refusal
           and "git clone" in refusal and "MangaBD-.git" in refusal
           and "Drive" in refusal)
except Exception as e:
    v55 = False
    print(f"      V5.5 exception: {type(e).__name__}: {str(e)[:200]}")
finally:
    mm._engine_weights_candidates = orig_candidates
    mm._download_engine_file = orig_downloader
check("V5.5 downloaded sha mismatch → refusal + expanded diagnostic", v55)

# V5.6 download exception → expanded diagnostic (root cause carried)
try:
    err_dir = Path(tempfile.mkdtemp(prefix="m006b1rf7_err_")) / "kellenok"
    err_dir.mkdir(parents=True)
    mm._engine_weights_candidates = lambda engine_name: [err_dir]

    def _network_down_dl(repo_id, revision, filename, dest_path):
        raise ConnectionError("network down")
    mm._download_engine_file = _network_down_dl

    diag = None
    try:
        mm._ensure_engine_weights("kellenok")
    except RuntimeError as r:
        diag = str(r)
    v56 = (diag is not None and "network down" in diag
           and "git clone" in diag and "self-heal fail" in diag)
except Exception as e:
    v56 = False
    print(f"      V5.6 exception: {type(e).__name__}: {str(e)[:200]}")
finally:
    mm._engine_weights_candidates = orig_candidates
    mm._download_engine_file = orig_downloader
check("V5.6 download failure → expanded Bengali diagnostic (cause + remedies)", v56)

# V5.7 corrupt VENDORED bundle → refusal, downloader never called
try:
    corr_dir = Path(tempfile.mkdtemp(prefix="m006b1rf7_corr_")) / "kellenok"
    (corr_dir / "det").mkdir(parents=True)
    (corr_dir / "det/manga_det_v0.2.onnx").write_bytes(b"tampered")
    (corr_dir / "rec").mkdir(parents=True)
    (corr_dir / "rec/manga_rec_v0.2.onnx").write_bytes(b"tampered")
    (corr_dir / "ppocrv6_dict.txt").write_bytes(b"tampered")
    mm._engine_weights_candidates = lambda engine_name: [corr_dir]
    mm._download_engine_file = _no_network_dl

    vrefusal = None
    try:
        mm._ensure_engine_weights("kellenok")
    except RuntimeError as r:
        vrefusal = str(r)
    v57 = (vrefusal is not None and "sha mismatch" in vrefusal
           and "git clone" in vrefusal)
except Exception as e:
    v57 = False
    print(f"      V5.7 exception: {type(e).__name__}: {str(e)[:200]}")
finally:
    mm._engine_weights_candidates = orig_candidates
    mm._download_engine_file = orig_downloader
check("V5.7 corrupt vendored bundle → refusal (no silent use, no re-download)", v57)

# ── V6: m002_sim_v2 ─────────────────────────────────────────
print("── V6 m002_sim_v2 fresh-run simulator ──")
POST_CELLS.mkdir(exist_ok=True)
for i in range(27):
    (POST_CELLS / f"cell_{i:02d}.py").write_text(POST[i], encoding="utf-8")
sim = subprocess.run([sys.executable, "/home/z/my-project/scripts/m005_sim2.py",
                      str(POST_CELLS)], capture_output=True, text=True)
sim_out = sim.stdout
check("V6.1 sim runs", sim.returncode == 0, sim_out[-300:] + sim.stderr[-300:])
check("V6.2 m002_sim_v2 = 0 abort sites",
      "ABORT-CLASS findings (unguarded, unresolvable): 0" in sim_out,
      sim_out[-500:])

# ── totals ──────────────────────────────────────────────────
print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
if FAIL:
    raise SystemExit("RF-7 VERIFICATION FAILED")
print("ALL GREEN")
