#!/usr/bin/env python3
r"""MANGABD-007 B2 (Phase C) — verification suite.

Layers:
  V1  AST + JSON integrity (27 cells) + writer byte-faithfulness +
      re-derivation from main @ dcd96c0 + scripts/m007_b2_patches.json
      (new == old + exactly the 6 manifest patches)
  V2  Scope vs main @ dcd96c0: ONLY cells {5, 8} drift (25 others
      byte-identical incl. outputs/metadata); non-source fields +
      top-level notebook fields identical; changed-line summary
  V3  Cell-5 runtime (real torch exec — RF-8-proven venv recipe):
      full cell exec — SUCCESS, 10/10 self-tests (9 existing + new
      "Embedding graceful degrade (S05-1)"), zero failures, Bengali
      diagnostics visible on the simulated failures, no real load
      attempt; PLUS harness-level independent re-proof of the
      ensure_embedding degrade contract (ImportError + OSError sims
      through the harness's own log_event)
  V4  Cell-8 runtime: full cell exec — SUCCESS, 32/32 self-tests
      (30 existing + Tests 31-32), zero failures, final log_event
      tests_total == 32
  V5  Escape-hardening edge matrix via the live parse_ai_text:
      escape-stack convergence 1..4 levels (both brackets), trailing
      backslash runs 1..3, directive edge trio, idempotence, and
      regression guards (Owner sample (a) parity, placeholder/marker
      skip invariants, no-escape passthrough)
  V6  m002_sim_v2 fresh-kernel simulator on the post-change cells:
      0 abort sites (output archived)

Run with: scripts/venv_m007b2/bin/python (workspace-external venv,
NOT in the repo tree; torch 2.14.1+cpu + nest_asyncio + numpy +
pillow + pandas — the M006 RF-8 recipe).
"""
import ast
import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

import pandas as pd

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "dcd96c0"
MANIFEST = REPO / "scripts/m007_b2_patches.json"
CELLS_DIR = Path("/home/z/my-project/cells")
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_LOG = Path("/home/z/my-project/phaseC007/sim_v2_output_b2.txt")
TARGET_CELLS = {5, 8}

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
    return cond


def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True, cwd=str(REPO))


nb = json.loads(NB.read_text(encoding="utf-8"))
SRC = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}

# ── V1: AST + JSON integrity + re-derivation ─────────────────
print("── V1 AST + JSON + re-derivation vs base + manifest ──")
check("V1.1 27 cells", len(nb["cells"]) == 27)
ok_ast = True
for i in range(27):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(SRC[i], f"cell_{i:02d}.py", "exec")
    except (Warning, SyntaxError) as w:
        ok_ast = False
        print(f"      cell {i}: {w}")
check("V1.2 AST 27/27 warnings-as-errors", ok_ast)

rt = json.dumps(nb, indent=2, ensure_ascii=False)
check("V1.3 writer byte-faithful on the post-edit file",
      rt.encode("utf-8") == NB.read_bytes(),
      f"md5 file {hashlib.md5(NB.read_bytes()).hexdigest()} md5 dump {hashlib.md5(rt.encode('utf-8')).hexdigest()}")

base_raw = run("git", "show", f"{BASE_REF}:{NB_NAME}").stdout
base_nb = json.loads(base_raw)
BASE = {i: "".join(base_nb["cells"][i]["source"]) for i in range(27)}

patches = json.loads(MANIFEST.read_text(encoding="utf-8"))
check("V1.4 manifest carries exactly the 6 B2 patches", len(patches) == 6,
      f"n={len(patches)}")
re_src = dict(BASE)
for p in patches:
    c = re_src[p["cell"]].count(p["old"])
    if c != 1:
        check(f"V1.4a anchor unique in cell {p['cell']}: {p['name']}", False, f"count={c}")
        re_src[p["cell"]] = None
        break
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
ok_rederive = all(re_src[i] == SRC[i] for i in range(27))
check("V1.5 working cells == base @ dcd96c0 + exactly the manifest patches",
      ok_rederive,
      "drift=" + str([i for i in range(27) if re_src[i] != SRC[i]]))
names = [p["name"] for p in patches]
check("V1.6 patch names are the S05-1/S05-2 set (cells {5,8} only)",
      {p["cell"] for p in patches} == TARGET_CELLS
      and sum(1 for p in patches if p["cell"] == 5) == 2
      and sum(1 for p in patches if p["cell"] == 8) == 4,
      str(names))

# ── V2: scope vs main @ dcd96c0 ──────────────────────────────
print()
print("── V2 scope vs main @ dcd96c0 ──")
drift = [i for i in range(27) if i not in TARGET_CELLS
         and json.dumps(nb["cells"][i]) != json.dumps(base_nb["cells"][i])]
check("V2.1 25 non-target cells fully byte-identical (source + outputs + metadata)",
      not drift, f"drift={drift}")
ok_fields = all(
    {k: v for k, v in nb["cells"][i].items() if k != "source"}
    == {k: v for k, v in base_nb["cells"][i].items() if k != "source"}
    for i in range(27)
)
check("V2.2 non-source fields identical for all 27 cells", ok_fields)
check("V2.3 top-level notebook fields identical",
      all(nb[k] == base_nb[k] for k in nb if k != "cells"))
for i in sorted(TARGET_CELLS):
    a, b = BASE[i].split("\n"), SRC[i].split("\n")
    changed = [k for k in range(max(len(a), len(b))) if (a[k] if k < len(a) else None) != (b[k] if k < len(b) else None)]
    print(f"      cell {i}: {len(a)} -> {len(b)} lines; first/last changed line: "
          f"{changed[0] + 1 if changed else '-'} / {changed[-1] + 1 if changed else '-'} "
          f"({len(changed)} diff positions)")
check("V2.4 changed cells exactly {5, 8}",
      sorted(i for i in range(27) if json.dumps(nb["cells"][i]) != json.dumps(base_nb["cells"][i])) == [5, 8])

# ── V3: cell-5 runtime — real torch exec ──────────────────────
print()
print("── V3 cell-5 runtime: real torch exec, S05-1 contract ──")
tmp = Path(tempfile.mkdtemp(prefix="m007b2_"))
cfg = {
    "session_id": "m007b2test",
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
    logs.append((level, str(msg), kw))


def fake_get_page(page_id, required=False):
    return {"page_id": page_id, "original_filename": page_id}


ns = {
    "MANGABD_CONFIG": cfg,
    "log_event": fake_log_event,
    "get_page": fake_get_page,
    "MANGABD_SECRETS": {"openrouter_api_key": "sk-test", "hf_token": ""},
    "__name__": "__m007b2_cell5__",
}

# DISCLOSED HARNESS-ONLY SUBSTITUTION (M006-proven): cell 5 hardcodes
# the Colab-root HF cache (QWEN_LOCAL_CACHE = Path("/root/.cache/...") +
# module-level mkdir). This sandbox user cannot create /root/*. The
# exec below redirects ONLY that one path string to a temp dir —
# asserted single-substring; every other byte equals the built source.
ROOT_CACHE = 'Path("/root/.cache/huggingface/hub")'
HARNESS5_DIR = tmp / "hfhub"
harness5 = SRC[5].replace(ROOT_CACHE, f'Path("{HARNESS5_DIR}")')
check("V3.0a harness substitution is exactly one substring (disclosed)",
      SRC[5].count(ROOT_CACHE) == 1 and harness5 != SRC[5]
      and len(harness5) - len(SRC[5])
      == len(str(HARNESS5_DIR)) - len("/root/.cache/huggingface/hub"))

buf5 = io.StringIO()
ok5 = True
try:
    with contextlib.redirect_stdout(buf5):
        exec(compile(harness5, "cell_05.py", "exec"), ns)
except Exception as e:
    ok5 = False
    print(f"      cell5 exception: {type(e).__name__}: {e}")
    print(buf5.getvalue()[-2500:])
out5 = buf5.getvalue()
tests5 = list(ns.get("tests", []))

check("V3.1 cell 5 execs clean (real torch)", ok5)
check("V3.2 cell 5 SUCCESS banner", "Cell 5 result: SUCCESS" in out5)
check("V3.3 cell 5 battery 10/10 (9 existing + Test 10)",
      len(tests5) == 10 and all(tests5), f"n={len(tests5)} passed={sum(tests5)}")
check("V3.4 zero self-test failures in cell 5 output", "❌ " not in out5)

CELL5_EXISTING_TESTS = [
    "PyTorch available", "Device valid", "GPU memory summary",
    "ModelManager status", "clear_gpu_cache works",
    "QwenVLWrapper class ready", "OCR deterministic config",
    "Language score helper", "OCR confidence helper",
]
missing5 = [t for t in CELL5_EXISTING_TESTS if f"✅ {t}" not in out5]
check("V3.5 the 9 existing cell-5 self-tests still pass (S05-1 additive)",
      not missing5, f"missing={missing5}")
check("V3.6 new test passing: Embedding graceful degrade (S05-1)",
      "✅ Embedding graceful degrade (S05-1)" in out5)
check("V3.7 Bengali diagnostic visible in console on simulated failures (Test-10 captures)",
      ns.get("_out10", "").count("⚠️ Embedding model load failed:") == 1
      and "Feature disabled: semantic search।" in ns.get("_out10", "")
      and "Fix: !pip install sentence-transformers OR check internet connection।" in ns.get("_out10", "")
      and ns.get("_out10b", "").count("⚠️ Embedding model load failed:") == 1
      and "Feature disabled: semantic search।" in ns.get("_out10b", ""))
check("V3.8 no real load attempted (no 'Loading embedding model' console line)",
      "📥 Loading embedding model" not in out5)
check("V3.9 ensure_embedding/_embedding_load_failed defined on ModelManager",
      hasattr(ns["ModelManager"], "ensure_embedding")
      and hasattr(ns["ModelManager"], "_embedding_load_failed"))
check("V3.10 module-level model_manager usable post-exec",
      isinstance(ns["model_manager"].status(), dict)
      and "embedding" not in ns["model_manager"].instances)

# harness-level independent re-proof of the degrade contract — this
# time through the harness's OWN log_event (not the cell-internal fake)
import types as _types  # noqa: E402

_n_logs_before = len(logs)
sys_modules = sys.modules
_had_st = "sentence_transformers" in sys_modules
_old_st = sys_modules.get("sentence_transformers")

sys_modules["sentence_transformers"] = None
_mm_probe = ns["ModelManager"](cfg)
_pb = io.StringIO()
try:
    with contextlib.redirect_stdout(_pb):
        _r_probe = _mm_probe.ensure_embedding()
finally:
    if _had_st:
        sys_modules["sentence_transformers"] = _old_st
    else:
        sys_modules.pop("sentence_transformers", None)
_out_probe = _pb.getvalue()
_errs_probe = [m for lv, m, kw in logs[_n_logs_before:] if lv == "ERROR"]
check("V3.11 independent ImportError sim: returns None, never raises",
      _r_probe is None and "embedding" in _mm_probe.errors
      and "embedding" not in _mm_probe.instances)
check("V3.12 independent ImportError sim: Bengali diagnostic in harness logs",
      any(m.startswith("⚠️ Embedding model load failed:") for m in _errs_probe)
      and any("Feature disabled: semantic search।" in m for m in _errs_probe)
      and any("Fix: !pip install sentence-transformers OR check internet connection।" in m for m in _errs_probe))

_fake_mod = _types.ModuleType("sentence_transformers")


def _st_raise(*args, **kwargs):
    raise OSError("simulated network failure (harness probe)")


_fake_mod.SentenceTransformer = _st_raise
sys_modules["sentence_transformers"] = _fake_mod
_pb2 = io.StringIO()
try:
    with contextlib.redirect_stdout(_pb2):
        _r_probe2 = ns["ModelManager"](cfg).ensure_embedding()
finally:
    if _had_st:
        sys_modules["sentence_transformers"] = _old_st
    else:
        sys_modules.pop("sentence_transformers", None)
_out_probe2 = _pb2.getvalue()
check("V3.13 independent OSError sim: returns None + Bengali diagnostic",
      _r_probe2 is None and "⚠️ Embedding model load failed:" in _out_probe2
      and "Feature disabled: semantic search।" in _out_probe2)
check("V3.14 cached-failure short-circuit (repeat call, zero new log lines)",
      _mm_probe.ensure_embedding() is None and len(logs) == _n_logs_before + 2)
# ── V4: cell-8 runtime — 32/32 self-tests ────────────────────
print()
print("── V4 cell-8 runtime: 32/32 self-tests (30 existing + Tests 31-32) ──")

# cross-cell prerequisites (M006-B2-proven harness pattern): cell 8's
# module-level body + Tests 26-30 use the cell-3 §9b reading-order
# helpers and the cell-7 build_ocr_row. The REAL sections are extracted
# from the built tree's own sources and exec'd into the shared ns —
# zero stubs for the S05-1/S05-2 code under test.
_c3 = SRC[3]
_a9b = _c3.index("# 9b. Reading order")
_b9b = _c3.index("# 10. Initialize manifest")
SECTION_9B = _c3[_a9b:_b9b]
ns["pd"] = pd
exec(compile(SECTION_9B, "cell_03_section9b.py", "exec"), ns)
check("V4.0a cell-3 §9b section exec'd (reading-order helpers bound)",
      all(k in ns for k in ("compute_reading_order", "payload_sort_page_rows",
                            "payload_sort_all_rows", "ensure_reading_order_column")))
_tree7 = ast.parse(SRC[7])
_seg7 = next(ast.get_source_segment(SRC[7], n) for n in _tree7.body
             if isinstance(n, ast.FunctionDef) and n.name == "build_ocr_row")
exec(compile(_seg7, "cell_07_build_ocr_row.py", "exec"), ns)
check("V4.0b cell-7 build_ocr_row exec'd (get_page from harness)",
      "build_ocr_row" in ns)

buf8 = io.StringIO()
ok8 = True
try:
    with contextlib.redirect_stdout(buf8):
        exec(compile(SRC[8], "cell_08.py", "exec"), ns)
except Exception as e:
    ok8 = False
    print(f"      cell8 exception: {type(e).__name__}: {e}")
    print(buf8.getvalue()[-2500:])
out8 = buf8.getvalue()
tests8 = list(ns.get("tests", []))  # cell 8 re-binds `tests` in the shared ns

check("V4.1 cell 8 execs clean", ok8)
check("V4.2 cell 8 SUCCESS banner", "Cell 8 result: SUCCESS" in out8)
check("V4.3 cell 8 battery 32/32", len(tests8) == 32 and all(tests8),
      f"n={len(tests8)} passed={sum(tests8)}")
check("V4.4 zero self-test failures in cell 8 output", "❌ " not in out8)

CELL8_TEST_NAMES = [
    # ── Tests 1-25 (MANGABD-004/005 era) ──
    "validate_bengali", "clean_translation", "is_special_marker", "parse_ai_text",
    "parse_ai_text arrow-first (B2)", "build_translation_prompt", "apply_sfx_glossary",
    "get_translation_status", "translate_with_retry",
    "openrouter-exclusive registry", "switch_translator valid_engines (B1)",
    "closure dispatch via retry (B1)", "external-AI system prompt (B2)",
    "_strip_llm_wrappers prefix-zone (B2)", "paste-back round-trip (B2)",
    "Owner sample (a) escaped+arrowless (B2)",
    "Owner sample (b) escaped+arrow (B2)",
    "Owner sample (c) raw+arrow (B2)",
    "tag-less junk reported (B2)",
    "single-line multi-tag split (B2)",
    "placeholder skip+report (B2)",
    "page stem-match/ambiguous (B2)",
    "live-state save/restore (RF-2)",
    "Owner trailing-arrow 6/6 apply (RF-3)",
    "bare [SKIP] marker-skip, never literal (RF-4)",
    # ── Tests 26-30 (MANGABD-006 B2) ──
    "M6-B2 single-column page (one band, y-order)",
    "M6-B2 two-column manga (RTL bands, y-order within)",
    "M6-B2 S003 gate == VLM-confirmed R3->R2->R4->R5->R6->R1 (tau +1.000)",
    "M6-B2 overlay_note_position geometric/first/last (D2)",
    "M6-B2 backward compat (lazy compute; id toggle; disabled; -1 row)",
    # ── Tests 31-32 (MANGABD-007 B2 / S05-2) ──
    "double-escaped fixture 100% parse (S05-2)",
    "mixed-escape fixture 100% parse (S05-2)",
]
missing8 = [t for t in CELL8_TEST_NAMES if f"✅ {t}" not in out8]
check("V4.5 all 30 pre-existing test names still pass (no regression)",
      not [t for t in CELL8_TEST_NAMES[:-2] if f"✅ {t}" not in out8],
      f"missing={missing8}")
check("V4.6 new Tests 31-32 pass",
      all(f"✅ {t}" in out8 for t in CELL8_TEST_NAMES[-2:]),
      f"missing={missing8}")
_tail_log = [kw for lv, m, kw in logs if isinstance(kw, dict) and "tests_total" in kw]
check("V4.7 final log_event carries tests_total == 32",
      any(kw.get("tests_total") == 32 and kw.get("tests_passed") == 32 for kw in _tail_log),
      str(_tail_log[-1] if _tail_log else "none"))

# ── V5: escape-hardening edge matrix (live parse_ai_text) ────
print()
print("── V5 escape-hardening edge matrix + regression guards ──")
parse_ai = ns["parse_ai_text"]


def _stats(p):
    return p.get(("_unparsed", 0), {}).get("stats", {})


def _unparsed(p):
    return p.get(("_unparsed", 0), {}).get("unparsed_lines", [])


# V5.1 escape-stack convergence: n levels before BOTH brackets, n = 1..4
ok_stack = True
for n in range(1, 5):
    # escaped-tag form: (\ x n) [ 01.jpg:1 (\ x n) ]  rest
    content = ("\\") * n + "[01.jpg:1" + ("\\") * n + "] Hello → হ্যালো"
    p = parse_ai(content)
    good = (("01.jpg", 1) in p
            and p[("01.jpg", 1)]["original_text"] == "Hello"
            and p[("01.jpg", 1)]["translated_text"] == "হ্যালো"
            and not _unparsed(p)
            and _stats(p).get("escape_warn", 1) == 0)
    if not good:
        ok_stack = False
        print(f"      n={n}: {str(p)[:180]}")
check("V5.1 escape-stack convergence levels 1..4 (both brackets) all parse",
      ok_stack)

# V5.2 trailing backslash runs 1..3 stripped before parsing
ok_trail = True
for k in range(1, 4):
    p = parse_ai("[01.jpg:2] A → আ" + ("\\") * k)
    good = (("01.jpg", 2) in p
            and p[("01.jpg", 2)]["translated_text"] == "আ"
            and _stats(p).get("trailing_backslash") == 1
            and not _unparsed(p))
    if not good:
        ok_trail = False
        print(f"      k={k}: {str(p)[:180]}")
check("V5.2 trailing-backslash runs 1..3 stripped, translations intact",
      ok_trail)

# V5.3 the directive's three named edges, combined in ONE paste
sample_edges = (
    "\\\\[01.jpg:1\\\\] Hello → হ্যালো\n"   # double-escaped
    "\\[01.jpg:2\\] World → বিশ্ব\n"          # single-escaped (mixed)
    "[01.jpg:3] Text → টেক্সট\\\n"            # trailing backslash
    "[01.jpg:4] Raw → কাঁচা"                  # raw
)
p = parse_ai(sample_edges)
ok_edges = (
    all(("01.jpg", n) in p for n in range(1, 5))
    and p[("01.jpg", 1)]["translated_text"] == "হ্যালো"
    and p[("01.jpg", 2)]["translated_text"] == "বিশ্ব"
    and p[("01.jpg", 3)]["translated_text"] == "টেক্সট"
    and p[("01.jpg", 4)]["translated_text"] == "কাঁচা"
    and not _unparsed(p)
    and _stats(p).get("unescaped") == 2
    and _stats(p).get("trailing_backslash") == 1
)
check("V5.3 directive edge trio in one paste: 4/4 parse, zero unparsed",
      ok_edges, str(p)[:220])

# V5.4 idempotence: same input twice → identical result dicts
check("V5.4 idempotent parse (same input twice, identical dicts)",
      parse_ai(sample_edges) == p)

# V5.5 regression: Owner sample (a) parity with the pre-change semantics
sample_a = "\\[02.jpg:1\\] সালা সে কে!?\n\\[02.jpg:2\\] মাদারচোদ!? কুত্তার মেয়ে"
p = parse_ai(sample_a)
check("V5.5 Owner sample (a) parity: 2 entries, unescaped=2, arrowless=2",
      len(p) == 3
      and p[("02.jpg", 1)]["translated_text"] == "সালা সে কে!?"
      and p[("02.jpg", 1)]["original_text"] == ""
      and p[("02.jpg", 2)]["translated_text"] == "মাদারচোদ!? কুত্তার মেয়ে"
      and _stats(p).get("unescaped") == 2
      and _stats(p).get("arrowless") == 2
      and not _unparsed(p))

# V5.6 regression: placeholder/marker skip invariants unchanged
p_ph = parse_ai("[02.jpg:1] English →")
p_mk = parse_ai("[02.jpg:2] X → [SKIP]")
check("V5.6 skip invariants: empty-after-arrow placeholder + [SKIP] marker",
      ("02.jpg", 1) not in p_ph
      and _stats(p_ph).get("placeholder_skipped") == 1
      and ("02.jpg", 2) not in p_mk
      and _stats(p_mk).get("marker_skipped") == 1
      and _stats(p_mk).get("escape_warn", 0) == 0)

# V5.7 regression: clean no-escape paste → no sentinel, zero counters
p_raw = parse_ai("[02.jpg:3] Hello → হ্যালো")
check("V5.7 no-escape passthrough: entry stored, zero variant counters",
      ("_unparsed", 0) not in p_raw
      and p_raw[("02.jpg", 3)]["translated_text"] == "হ্যালো")

# V5.8 stats shape: new counters ride the report sentinel (V-4a visible)
check("V5.8 new counters ride the sentinel report (never silent)",
      set(_stats(parse_ai("\\\\[02.jpg:9\\\\] টেস্ট"))) >= {"unescaped", "escape_warn", "trailing_backslash"})

# ── V6: m002_sim_v2 — 0 abort sites ──────────────────────────
print()
print("── V6 m002_sim_v2 fresh-kernel simulator ──")
for old in CELLS_DIR.glob("cell_*.py"):
    old.unlink()
for i in range(27):
    (CELLS_DIR / f"cell_{i:02d}.py").write_text(SRC[i], encoding="utf-8")
sim_out = subprocess.run([sys.executable, str(SIM)], capture_output=True, text=True)
SIM_LOG.parent.mkdir(parents=True, exist_ok=True)
SIM_LOG.write_text(sim_out.stdout, encoding="utf-8")
m = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)", sim_out.stdout)
check("V6.1 simulator ran to completion", m is not None and sim_out.returncode == 0,
      sim_out.stderr[-500:])
if m:
    aborts = int(m.group(1))
    check(f"V6.2 m002_sim_v2 = {aborts} abort sites (expect 0)", aborts == 0)
    for line in sim_out.stdout.splitlines():
        if line.startswith("  >>>"):
            print("      " + line)

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
sys.exit(1 if FAIL else 0)
