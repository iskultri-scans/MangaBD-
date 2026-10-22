#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-8 — verification suite.

Checks (all must be GREEN before commit):
  V0  vendored weights sha256 re-check against the committed provenance
      manifest (RF-5 pins + M6-B1 int4 pin)
  V1  static: AST 27/27; 24 non-target cells byte-identical to 0b5d11d
      (RF-8 touches exactly {0, 5, 7}); re-derivation equality from the
      RF-8 patch manifest; cell-0 onnxruntime pin; cell-5 timeout constant
      + downloader local_dir/timeout mechanics + per-file verify/progress
      loop; _resolve_vendored_engine_dir + ensure_kellenok/ensure_baberu +
      `tried` string byte-untouched; Test 29 hang-phase hermeticity and
      assertion updates; cell-8 battery byte-untouched
  V2  non-source + top-level notebook fields identical
  V3  runtime harness: exec cells 5 -> 7 -> 8 with mocked upstream globals;
      batteries 5: 9/9, 7: 10/10 (incl. extended Test 29 with hang
      simulation), 8: 25/25; timeout-constant/hf/downloader restoration
      proven after cell 7
  V4  vendored-present behavior unchanged: kellenok manual R3 read
      BYTE-EXACT vs the committed RF-5 measurement, no download banner,
      baberu int4 read
  V5  RF-8 download behavior: vendored-present zero-network; REAL HF
      local_dir direct-write downloads (kellenok 3/3 + baberu FULL 5/5 —
      discharges Phase-D observation D-28); full self-heal flow with
      visible [N/M] progress lines; offline re-run; REAL timeout mechanism
      (hanging hf_hub_download -> loud TIMEOUT + full Bengali diagnostic);
      wrong-bytes fail-fast (downloader called once); corrupt-vendored
      refusal
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
import time
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "0b5d11d"  # branch tip at build time (notebook == a0e6bbf)
MANIFEST = Path("/home/z/my-project/scripts/m006_b1_rf8_patches.json")
W_MANIFEST = json.loads(
    Path("/home/z/my-project/scripts/m006_b1_weights_manifest.json").read_text()
)
POST_CELLS = Path("/home/z/my-project/cells_rf8_post")

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

RF8_TARGET = {0, 5, 7}
non_target = [i for i in range(27) if i not in RF8_TARGET]
check("V1.2 24 non-target cells byte-identical to 0b5d11d (RF-8 touches {0,5,7} only)",
      all(BASE[i] == POST[i] for i in non_target),
      str([i for i in non_target if BASE[i] != POST[i]]))

check("V1.3 batch cells 15/25 + cell-8 battery untouched",
      BASE[15] == POST[15] and BASE[25] == POST[25] and BASE[8] == POST[8])

patches_doc = json.loads(MANIFEST.read_text())
patches = patches_doc["patches"]
assert patches_doc["base_ref"] == BASE_REF and patches_doc["target_cells"] == [0, 5, 7]
re_src = list(BASE)
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derivation: {p['name']}"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1.4 re-derivation equality (post == 0b5d11d + exactly the 12 RF-8 patches)",
      all(re_src[i] == POST[i] for i in range(27)))
check("V1.5 patch manifest scope = {0, 5, 7}, 12 patches",
      {p["cell"] for p in patches} == RF8_TARGET and len(patches) == 12)

# ── cell 0 (Defect 1) ───────────────────────────────────────
c0 = POST[0]
det_span = span(c0, "DETECTION_PACKAGES = [", "TRANSLATION_API_PACKAGES = [")
check("V1.6 cell-0 onnxruntime>=1.31.0 in DETECTION_PACKAGES exactly once",
      c0.count('"onnxruntime>=1.31.0"') == 1
      and '"onnxruntime>=1.31.0"' in det_span)
check("V1.6b onnxruntime pin absent from every other cell + every other package group",
      all('"onnxruntime>=1.31.0"' not in POST[i] for i in range(27) if i != 0)
      and "onnxruntime" not in span(c0, "CORE_PACKAGES = [", "DETECTION_PACKAGES = [")
      and "onnxruntime" not in span(c0, "TRANSLATION_API_PACKAGES = [", "pip_ok = True"))

# ── cell 5 (Defect 2) ───────────────────────────────────────
c5 = POST[5]
check("V1.7 cell-5 timeout constant exactly once, default 300",
      c5.count("_ENGINE_DOWNLOAD_TIMEOUT_SECONDS = 300") == 1
      and c5.count("_ENGINE_DOWNLOAD_TIMEOUT_SECONDS") == 4)

dl_span = span(c5, "    def _download_engine_file(self, repo_id, revision, filename, dest_path):",
               "    def _verify_engine_weights(self, engine_name, weights_dir, pins):")
check("V1.8a downloader: cache-copy move step removed (no import shutil / no copyfile call)",
      "import shutil" not in dl_span
      and "shutil.copyfile(downloaded, dest)" not in dl_span
      and "downloaded = Path(" not in dl_span)
check("V1.8b downloader: hf_hub_download local_dir direct write + pinned rev + force_download=False",
      "local_dir=str(local_dir)," in dl_span
      and "force_download=False," in dl_span
      and "revision=revision," in dl_span
      and "repo_id=repo_id," in dl_span)
check("V1.8c downloader: daemon-thread timeout mechanism",
      "threading.Thread(target=_hf_download_worker, daemon=True)" in dl_span
      and "worker.join(timeout_s)" in dl_span
      and "worker.is_alive()" in dl_span
      and 'f"TIMEOUT: {filename} download {timeout_s:.0f}s-এ শেষ হয়নি' in dl_span)
check("V1.8d downloader: never-silent dest guard",
      "if not dest.is_file():" in dl_span
      and "path mismatch" in dl_span)
check("V1.8e downloader: timeout read is the patched global",
      'globals().get("_ENGINE_DOWNLOAD_TIMEOUT_SECONDS", 300)' in dl_span)

loop_span = span(c5, "        # RF-8: per-file download → immediate sha-verify → visible",
                 "        return target")
check("V1.9a loop: per-file immediate sha verify (fail-fast)",
      "_sha256_of_file(file_dest)" in loop_span
      and "downloaded sha mismatch" in loop_span
      and loop_span.index("if got_sha != want_sha:") < loop_span.index("print("))
check("V1.9b loop: [N/M] progress line format per directive",
      'f"    [{i}/{len(missing)}] sha256={got_sha[:8]} "' in loop_span
      and 'f"size={file_dest.stat().st_size} OK"' in loop_span)
check("V1.9c loop: final belt-and-braces full verify retained",
      "self._verify_engine_weights(engine_name, target, pins)" in loop_span)
check("V1.9d loop: diagnostic wrap carries per-file progress",
      "সম্পন্ন {progress['done']}/{len(missing)})।" in loop_span)

check("V1.10 _resolve_vendored_engine_dir byte-identical (legacy path kept)",
      span(BASE[5], "    def _resolve_vendored_engine_dir(self, engine_name):",
           "    def ensure_kellenok(self, force=False):")
      == span(POST[5], "    def _resolve_vendored_engine_dir(self, engine_name):",
              "    def ensure_kellenok(self, force=False):"))
check("V1.11 ensure_kellenok + ensure_baberu byte-identical to 0b5d11d (RF-8 untouched)",
      span(BASE[5], "    def ensure_kellenok(self, force=False):",
           "    def ensure_baberu(self, force=False):")
      == span(POST[5], "    def ensure_kellenok(self, force=False):",
              "    def ensure_baberu(self, force=False):")
      and span(BASE[5], "    def ensure_baberu(self, force=False):",
               "    def ensure_openrouter_vision(self, force=False):")
      == span(POST[5], "    def ensure_baberu(self, force=False):",
              "    def ensure_openrouter_vision(self, force=False):"))
check("V1.12 `tried` what-tried string byte-identical to 0b5d11d",
      span(BASE[5], "        tried = (", "        )")
      == span(POST[5], "        tried = (", "        )"))
check("V1.13 registry pins byte-untouched by RF-8",
      span(BASE[5], '        "hf_repo": "Kellenok/PP-OCRv6_manga"',
           '        "vrmb_gb": 0.4,')
      == span(POST[5], '        "hf_repo": "Kellenok/PP-OCRv6_manga"',
              '        "vrmb_gb": 0.4,'))

# ── cell 7 (Test 29 extension) ───────────────────────────────
c7 = POST[7]
check("V1.14 Test 29 present exactly once in cell 7",
      c7.count("OCR weights self-heal (RF-7)") == 2  # run_test call + except path
      and c7.count("# Test 29: weights self-heal") == 1)
check("V1.15 hang-phase hermeticity: sleep-stub hf monkey-patch, no real network",
      "def _w29_hang_download(**_kwargs29):" in c7
      and "_time29.sleep(30)" in c7
      and c7.count("NO real network") >= 3)
check("V1.16 hang-phase: patched small timeout + full restore in finally",
      'globals()["_ENGINE_DOWNLOAD_TIMEOUT_SECONDS"] = 1' in c7
      and "_hfmod29.hf_hub_download = _saved_hf29" in c7
      and 'globals()["_ENGINE_DOWNLOAD_TIMEOUT_SECONDS"] = _saved_timeout29' in c7
      and "model_manager._download_engine_file = _saved_downloader29" in c7)
check("V1.17 hang-phase assertions per directive (timeout fires + diagnostic taken)",
      '"TIMEOUT" in _hang_refusal29' in c7
      and '"1s" in _hang_refusal29' in c7
      and '"git clone" in _hang_refusal29' in c7
      and '"Drive" in _hang_refusal29' in c7
      and "_hang_elapsed29 < 10" in c7)
check("V1.18 phase ka fail-fast assertion (per-file verify: stop at first bad file)",
      '_w29_calls["n"] == 1' in c7
      and '_w29_calls["args"][0][2] in set(_exp_files29)' in c7)
check("V1.19 phase kha progress capture",
      '"[1/2] sha256=" in _captured29.getvalue()' in c7
      and '"[2/2] sha256=" in _captured29.getvalue()' in c7)
check("V1.20 Test 29 verdict includes progress + hang conjuncts",
      "and _progress_ok29" in c7 and "and _hang_ok29" in c7
      and "hang-timeout={_hang_ok29}" in c7)
check("V1.21 Test 29 hermetic (existing phases unchanged): downloader monkey-patched",
      "model_manager._download_engine_file = _w29_downloader" in c7
      and "model_manager._engine_weights_candidates = _w29_candidates" in c7)

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
tmp = Path(tempfile.mkdtemp(prefix="m006b1rf8_"))
cfg = {
    "session_id": "m006b1rf8test",
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
    "__name__": "__m006b1rf8__",
}

# DISCLOSED HARNESS-ONLY SUBSTITUTION (same class as RF-7's): cell 5
# hardcodes the Colab-root HF cache path; this sandbox user cannot create
# /root/*. Exactly one substring redirected to a temp dir; no repository
# byte touched.
ROOT_CACHE = 'Path("/root/.cache/huggingface/hub")'
HARNESS5_DIR = tmp / "hfhub"
harness5 = POST[5].replace(ROOT_CACHE, f'Path("{HARNESS5_DIR}")')
check("V3.0a harness substitution is exactly one substring (disclosed)",
      POST[5].count(ROOT_CACHE) == 1 and harness5 != POST[5]
      and len(harness5) - len(POST[5])
      == len(str(HARNESS5_DIR)) - len("/root/.cache/huggingface/hub"))

import huggingface_hub as _hf_probe  # noqa: E402
HF_ORIG = _hf_probe.hf_hub_download

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
check("V3.4 runtime timeout constant defined by cell 5 (300, patchable global)",
      ns.get("_ENGINE_DOWNLOAD_TIMEOUT_SECONDS") == 300)

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
    print(buf7.getvalue()[-2500:])
out7 = buf7.getvalue()
tests7 = list(ns.get("tests", []))
check("V3.5 cell 7 execs clean", ok7)
check("V3.6 cell 7 SUCCESS banner", "Cell 7 result: SUCCESS" in out7)
check("V3.7 cell 7 battery 10/10 (6 original + Tests 26-29 extended)",
      len(tests7) == 10 and all(tests7),
      f"n={len(tests7)} passed={sum(tests7)}")
for tname in ("OCR engine registry (M6-B1)", "OCR fallback chain auto/manual (M6-B1)",
              "OCR chain guards + wiring (M6-B1)", "OCR weights self-heal (RF-7)"):
    check(f"V3.8 test passing: {tname}", f"✅ {tname}" in out7)
check("V3.9 zero test failures in cell 7 output", "❌ " not in out7)
check("V3.10 hang-phase tier-2 ran during the cell-7 battery (0-MB fake-pin banner)",
      "vendored weights নেই" in out7 and "~0 MB" in out7,
      f"banner_count={out7.count('vendored weights নেই')}")

# restoration proofs after the extended Test 29
check("V3.11 timeout constant restored to 300 after cell 7",
      ns.get("_ENGINE_DOWNLOAD_TIMEOUT_SECONDS") == 300)
check("V3.12 huggingface_hub.hf_hub_download restored after cell 7",
      _hf_probe.hf_hub_download is HF_ORIG)
mm = ns["model_manager"]
check("V3.13 model_manager._download_engine_file restored to the real bound method",
      mm._download_engine_file.__func__ is type(mm)._download_engine_file)

# Test 29's fake-pin save/restore still works after the RF-8 extension
rt_pins_ok = True
for gkey in ("kellenok", "baberu"):
    rt_spec = ns["MANGABD_CONFIG"]["ocr"]["engines"][gkey]
    grp = W_MANIFEST[gkey]
    rt_pins_ok &= rt_spec.get("hf_repo") == grp["repo"]
    rt_pins_ok &= rt_spec.get("hf_revision") == grp["revision"]
    rt_pins_ok &= set(rt_spec.get("files", {})) == set(grp["files"])
    for rel, meta in grp["files"].items():
        rt_pins_ok &= rt_spec["files"][rel]["sha256"] == meta["sha256"]
check("V3.13b runtime registry pins restored + == manifest after cell 7",
      rt_pins_ok)

ns["TRANSLATION_DF_COLUMNS"] = ns["TRANSLATION_DF_COLUMNS"]
buf8 = io.StringIO()
ok8 = True
try:
    with contextlib.redirect_stdout(buf8):
        exec(compile(POST[8], "cell_08.py", "exec"), ns)
except Exception as e:
    ok8 = False
    print(f"      cell8 exception: {type(e).__name__}: {e}")
    print(buf8.getvalue()[-1500:])
out8 = buf8.getvalue()
tests8 = list(ns.get("tests", []))
check("V3.14 cell 8 execs clean (byte-identical battery)", ok8)
check("V3.15 cell 8 SUCCESS banner", "Cell 8 result: SUCCESS" in out8)
check("V3.16 cell 8 battery 25/25", len(tests8) == 25 and all(tests8),
      f"n={len(tests8)} passed={sum(tests8)}")
check("V3.17 zero test failures in cell 8 output", "❌ " not in out8)

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
check("V4.2 vendored-present stdout unchanged (load banner, no download banner)",
      "📥 Loading kellenok ONNX (CPU, vendored weights)" in smoke_out
      and "vendored weights নেই" not in smoke_out
      and "HF hub থেকে" not in smoke_out
      and "sha-pinned download" not in smoke_out
      and "[1/" not in smoke_out)

# byte fidelity: notebook kellenok class vs the committed RF-5 measurement
kell = mm.instances["kellenok"]
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

# ── V5: RF-8 download behavior ───────────────────────────────
print("── V5 RF-8 download behavior ──")
orig_candidates = mm._engine_weights_candidates
orig_downloader = mm._download_engine_file

# V5.1 vendored present → zero network (downloader must not fire)
def _no_network_dl(*a, **k):
    raise AssertionError("network touched with vendored weights present!")

try:
    mm._download_engine_file = _no_network_dl
    got_dir = mm._ensure_engine_weights("kellenok")
    v51 = (Path(got_dir).resolve() == (REPO / "models" / "kellenok").resolve())
except AssertionError:
    v51 = False
finally:
    mm._download_engine_file = orig_downloader
check("V5.1 vendored present → sha-verify + use, downloader NEVER called", v51)

# V5.2 REAL downloader direct calls: kellenok full set, local_dir write
real_dl_dir = Path(tempfile.mkdtemp(prefix="m006b1rf8_dl_"))
try:
    for rel, meta in W_MANIFEST["kellenok"]["files"].items():
        dest = real_dl_dir / "kellenok" / rel
        mm._download_engine_file(
            W_MANIFEST["kellenok"]["repo"],
            W_MANIFEST["kellenok"]["revision"],
            rel,
            dest,
        )
        check(f"V5.2 REAL HF download kellenok:{rel} local_dir sha == pin",
              dest.is_file() and sha256_of(dest) == meta["sha256"])
except Exception as e:
    check("V5.2 REAL HF download kellenok (pinned rev resolves)", False,
          f"{type(e).__name__}: {str(e)[:160]}")

# V5.3 FULL flow on hermetic empty dir, REAL downloader, progress visible
try:
    flow_dir = Path(tempfile.mkdtemp(prefix="m006b1rf8_flow_")) / "kellenok"
    flow_dir.mkdir(parents=True)
    mm._engine_weights_candidates = lambda engine_name: [flow_dir]
    cap3 = io.StringIO()
    with contextlib.redirect_stdout(cap3):
        got = mm._ensure_engine_weights("kellenok")
    flow_out = cap3.getvalue()
    v53 = (Path(got) == flow_dir
           and all(sha256_of(flow_dir / rel) == meta["sha256"]
                   for rel, meta in W_MANIFEST["kellenok"]["files"].items()))
    check("V5.3 full flow: empty dir → download → per-file [N/M] progress → verify → dir",
          v53, flow_out[-200:])
    check("V5.3b progress lines exactly [1/3]..[3/3] + sha8 + size + OK",
          "[1/3] sha256=" in flow_out and "[2/3] sha256=" in flow_out
          and "[3/3] sha256=" in flow_out and flow_out.count(" OK") == 3
          and "size=" in flow_out)
except Exception as e:
    check("V5.3 full flow", False, f"{type(e).__name__}: {str(e)[:200]}")
finally:
    mm._engine_weights_candidates = orig_candidates

# V5.3c offline re-run: complete bundle → tier-1, no new download output
try:
    mm._engine_weights_candidates = lambda engine_name: [flow_dir]
    cap3b = io.StringIO()
    with contextlib.redirect_stdout(cap3b):
        got2 = mm._ensure_engine_weights("kellenok")
    rerun_out = cap3b.getvalue()
    check("V5.3c offline re-run: no banner, no progress, same dir returned",
          Path(got2) == flow_dir and "নেই" not in rerun_out
          and "sha256=" not in rerun_out)
except Exception as e:
    check("V5.3c offline re-run", False, f"{type(e).__name__}: {str(e)[:200]}")
finally:
    mm._engine_weights_candidates = orig_candidates

# V5.4 baberu FULL set (5/5 — discharges Phase-D observation D-28)
try:
    b_dir = Path(tempfile.mkdtemp(prefix="m006b1rf8_bab_")) / "baberu"
    b_dir.mkdir(parents=True)
    mm._engine_weights_candidates = lambda engine_name: [b_dir]
    cap4 = io.StringIO()
    with contextlib.redirect_stdout(cap4):
        got_b = mm._ensure_engine_weights("baberu")
    b_out = cap4.getvalue()
    v54 = (Path(got_b) == b_dir
           and all(sha256_of(b_dir / rel) == meta["sha256"]
                   for rel, meta in W_MANIFEST["baberu"]["files"].items()))
    check("V5.4 baberu FULL self-heal 5/5 (incl. ONNX trio) shas == pins", v54,
          b_out[-200:])
    check("V5.4b progress lines exactly [1/5]..[5/5]",
          all(f"[{i}/5] sha256=" in b_out for i in range(1, 6))
          and b_out.count(" OK") == 5)
except Exception as e:
    check("V5.4 baberu full flow", False, f"{type(e).__name__}: {str(e)[:200]}")
finally:
    mm._engine_weights_candidates = orig_candidates

# V5.5 REAL timeout mechanism: hanging hf_hub_download (monkey-patched,
# sleep stub — no real network) → loud TIMEOUT
import huggingface_hub as hf_mod  # noqa: E402
try:
    def _hang_dl(**kwargs):
        time.sleep(60)

    hf_mod.hf_hub_download = _hang_dl
    ns["_ENGINE_DOWNLOAD_TIMEOUT_SECONDS"] = 2

    t0 = time.monotonic()
    to_exc = None
    dest5 = Path(tempfile.mkdtemp(prefix="m006b1rf8_to_")) / "kellenok" / "det" / "x.onnx"
    try:
        mm._download_engine_file("Kellenok/PP-OCRv6_manga",
                                 W_MANIFEST["kellenok"]["revision"],
                                 "det/manga_det_v0.2.onnx", dest5)
    except RuntimeError as r:
        to_exc = str(r)
    el5 = time.monotonic() - t0
    check("V5.5 hanging download → TIMEOUT RuntimeError within the patched window",
          to_exc is not None and "TIMEOUT" in to_exc and "2s" in to_exc
          and el5 < 10,
          f"elapsed={el5:.2f}s msg={to_exc[:120]!r}")

    # V5.5b full diagnostic path with the hanging downloader
    hang_dir = Path(tempfile.mkdtemp(prefix="m006b1rf8_hang_")) / "kellenok"
    hang_dir.mkdir(parents=True)
    mm._engine_weights_candidates = lambda engine_name: [hang_dir]
    diag = None
    t0b = time.monotonic()
    try:
        mm._ensure_engine_weights("kellenok")
    except RuntimeError as r:
        diag = str(r)
    el5b = time.monotonic() - t0b
    check("V5.5b hang → full RF-7 diagnostic (TIMEOUT + git clone + Drive + progress)",
          diag is not None and "TIMEOUT" in diag and "git clone" in diag
          and "Drive" in diag and "সম্পন্ন 0/3" in diag and el5b < 10,
          f"elapsed={el5b:.2f}s")
except Exception as e:
    check("V5.5 timeout mechanism", False, f"{type(e).__name__}: {str(e)[:200]}")
finally:
    hf_mod.hf_hub_download = HF_ORIG
    ns["_ENGINE_DOWNLOAD_TIMEOUT_SECONDS"] = 300
    mm._engine_weights_candidates = orig_candidates
check("V5.5c post-timeout restoration (hf + constant)",
      hf_mod.hf_hub_download is HF_ORIG
      and ns["_ENGINE_DOWNLOAD_TIMEOUT_SECONDS"] == 300)

# V5.6 wrong-bytes download → FAIL-FAST refusal (downloader called ONCE)
try:
    bad_dir = Path(tempfile.mkdtemp(prefix="m006b1rf8_bad_")) / "kellenok"
    bad_dir.mkdir(parents=True)
    mm._engine_weights_candidates = lambda engine_name: [bad_dir]
    dl_calls = {"n": 0}

    def _wrong_bytes_dl(repo_id, revision, filename, dest_path):
        dl_calls["n"] += 1
        Path(dest_path).parent.mkdir(parents=True, exist_ok=True)
        Path(dest_path).write_bytes(b"rf8-corrupted-download")

    mm._download_engine_file = _wrong_bytes_dl
    refusal = None
    try:
        mm._ensure_engine_weights("kellenok")
    except RuntimeError as r:
        refusal = str(r)
    v56 = (refusal is not None and "sha mismatch" in refusal
           and "git clone" in refusal and "MangaBD-.git" in refusal
           and "Drive" in refusal and dl_calls["n"] == 1)
    check("V5.6 wrong-bytes download → fail-fast refusal (1 call, full diagnostic)",
          v56, f"calls={dl_calls['n']} refusal={str(refusal)[:120]!r}")
except Exception as e:
    check("V5.6 fail-fast refusal", False, f"{type(e).__name__}: {str(e)[:200]}")
finally:
    mm._engine_weights_candidates = orig_candidates
    mm._download_engine_file = orig_downloader

# V5.7 corrupt VENDORED bundle → refusal, downloader never called
try:
    corr_dir = Path(tempfile.mkdtemp(prefix="m006b1rf8_corr_")) / "kellenok"
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
    raise SystemExit("RF-8 VERIFICATION FAILED")
print("ALL GREEN")
