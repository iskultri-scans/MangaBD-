#!/usr/bin/env python3
r"""MANGABD-007 B1 (Phase C) — verification suite.

Layers:
  V1  AST + JSON integrity (all 27 cells) + raw-byte reconstruction identity
      vs base @ 292369a (working tree == base bytes + exactly the 1-line
      surgical replacement — byte-faithful writer proof)
  V2  Scope: ONLY cell 1 differs vs main @ 292369a; within cell 1 exactly
      source line 302 changes (1024 -> 2048); non-source fields of every
      cell identical; top-level notebook fields identical
  V3  Cell-9 runtime (NO functional change — two-seed matrix, full cell-9
      exec with the M005-proven fake-globals + torch/manga_translator stubs):
      Seed A: the REAL post-change cell-1 inpainting literal (AST-extracted;
      lama_size == 2048) -> exec clean, 10/10 self-tests, startup print
      "LaMa size : 2048", value respected (no stomp)
      Seed B: legacy {"lama_size": 1024} -> exec clean, 10/10 self-tests,
      migration still fires (1024 -> 2048)
      Plus the 4-case migration matrix on the real cell-9 config slice
      (1024 -> 2048 / missing -> 2048 / 1536 respected / 2048 stays)
  V4  m002_sim_v2 fresh-kernel simulator on the post-change cells:
      0 abort sites
"""
import ast
import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
import types
import warnings
from pathlib import Path

import asyncio

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "292369a"
CELLS_DIR = Path("/home/z/my-project/cells")
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_LOG = Path("/home/z/my-project/phaseC007/sim_v2_output.txt")

OLD_RAW = b'\\"lama_size\\": 1024,'
NEW_RAW = b'\\"lama_size\\": 2048,'
CELL1_LINE = 302

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

# ── V1: AST + JSON integrity + raw-byte reconstruction ──────
print("── V1 AST + JSON + raw-byte identity ──")
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

base_raw = run("git", "show", f"{BASE_REF}:MangaBD_V12_ipynb_txt.ipynb (3).txt").stdout
base_bytes = base_raw.encode("utf-8")
cur_bytes = NB.read_bytes()
expected_bytes = base_bytes.replace(OLD_RAW, NEW_RAW, 1)
check("V1.3 raw bytes == base @ 292369a + exactly the 1-line replacement",
      cur_bytes == expected_bytes,
      f"base md5 {hashlib.md5(base_bytes).hexdigest()} cur md5 {hashlib.md5(cur_bytes).hexdigest()}")
check("V1.4 file size identical to base",
      len(cur_bytes) == len(base_bytes),
      f"{len(base_bytes)} -> {len(cur_bytes)}")

# ── V2: scope — only cell 1, only line 302 ───────────────────
print()
print("── V2 scope vs main @ 292369a ──")
base_nb = json.loads(base_raw)
drift = [i for i in range(27) if i != 1
         and json.dumps(nb["cells"][i]) != json.dumps(base_nb["cells"][i])]
check("V2.1 26 non-target cells fully byte-identical (source + outputs + metadata)",
      not drift, f"drift={drift}")
check("V2.2 cell-1 non-source fields identical to base",
      {k: v for k, v in nb["cells"][1].items() if k != "source"}
      == {k: v for k, v in base_nb["cells"][1].items() if k != "source"})
src1_pre = "".join(base_nb["cells"][1]["source"]).split("\n")
src1_post = SRC[1].split("\n")
changed = [k for k in range(max(len(src1_pre), len(src1_post)))
           if src1_pre[k] != src1_post[k]]
check("V2.3 cell-1 source line count unchanged", len(src1_pre) == len(src1_post))
check("V2.4 cell-1 changed source lines == [302] only",
      changed == [CELL1_LINE - 1], f"changed={changed}")
check("V2.5 cell-1 line 302: 1024 -> 2048",
      src1_pre[CELL1_LINE - 1] == '        "lama_size": 1024,'
      and src1_post[CELL1_LINE - 1] == '        "lama_size": 2048,')
check("V2.6 top-level notebook fields identical",
      all(nb[k] == base_nb[k] for k in nb if k != "cells"))
check("V2.7 cell-9 fully byte-identical to base (migration + ladder untouched)",
      json.dumps(nb["cells"][9]) == json.dumps(base_nb["cells"][9]))

# ── V3: cell-9 runtime — no functional change (two-seed matrix) ──
print()
print("── V3 cell-9 runtime: full exec, two-seed matrix ──")

# Seed A: AST-extract the REAL post-change cell-1 inpainting literal
tree = ast.parse(SRC[1])
assign = next(n for n in tree.body
              if isinstance(n, ast.Assign)
              and getattr(n.targets[0], "id", None) == "MANGABD_CONFIG")
inpainting_literal = None
for k, v in zip(assign.value.keys, assign.value.values):
    if isinstance(k, ast.Constant) and k.value == "inpainting":
        inpainting_literal = ast.literal_eval(v)
check("V3.1 post-change cell-1 inpainting literal AST-extracts (lama_size == 2048)",
      inpainting_literal is not None and inpainting_literal.get("lama_size") == 2048,
      f"literal={inpainting_literal}")

# migration matrix on the real cell-9 config slice (byte-identical slice)
c9 = SRC[9]
slice_start = c9.index('MANGABD_CONFIG.setdefault("inpainting", {})')
slice_end = c9.index("Redilate mask")
slice_end = c9.index("print()\n", slice_end) + len("print()\n")
config_slice = c9[slice_start:slice_end]


def run_migration_case(start_value):
    cfg = {}
    cfg["inpainting"] = {} if start_value == "__missing__" else {"lama_size": start_value}
    ns = {"MANGABD_CONFIG": cfg, "print": lambda *a, **k: None}
    exec(compile(config_slice, "cell9_config_slice.py", "exec"), ns)
    return cfg["inpainting"].get("lama_size")


check("V3.2 migration matrix: legacy 1024 -> 2048",
      run_migration_case(1024) == 2048)
check("V3.3 migration matrix: missing key -> 2048",
      run_migration_case("__missing__") == 2048)
check("V3.4 migration matrix: explicit 1536 respected (no stomp)",
      run_migration_case(1536) == 1536)
check("V3.5 migration matrix: explicit 2048 stays 2048",
      run_migration_case(2048) == 2048)

# torch + manga_translator stubs (M005-proven; cell 9 byte-identical since)
torch_stub = types.ModuleType("torch")
torch_cuda = types.ModuleType("torch.cuda")


class _StubOOMError(RuntimeError):
    pass


torch_cuda.OutOfMemoryError = _StubOOMError
torch_stub.cuda = torch_cuda
mt = types.ModuleType("manga_translator")
mt_inp = types.ModuleType("manga_translator.inpainting")
mt_common = types.ModuleType("manga_translator.inpainting.common")


class InpainterConfig:
    pass


mt_common.InpainterConfig = InpainterConfig
mt.inpainting = mt_inp
mt_inp.common = mt_common
saved_modules = {}
for name, mod in [("torch", torch_stub), ("manga_translator", mt),
                  ("manga_translator.inpainting", mt_inp),
                  ("manga_translator.inpainting.common", mt_common)]:
    saved_modules[name] = sys.modules.get(name)
    sys.modules[name] = mod


def _run_async_real(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError("closed")
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


logs = []


def fake_log_event(msg, level="INFO", **kw):
    logs.append((level, msg))


class _InitialManager:
    def unload_all(self, exclude=None):
        pass

    def ensure_lama(self, force=False):
        raise RuntimeError("not used in V3")


def _clear_counter():
    _clear_counter.n += 1


_clear_counter.n = 0

TEST_NAMES = [
    "inpaint_clean_mask", "inpaint_adaptive_dilate_mask",
    "inpaint_bbox_mask_from_regions", "inpaint_clip_mask_to_regions",
    "prepare_mask_for_inpaint", "opencv_inpaint fallback",
    "inpainting config valid",
    "LaMa OOM ladder steps down (B1)",
    "LaMa non-OOM/empty: no retry (Amd5)",
    "LaMa all-rungs OOM: single error (B1)",
]


def exec_cell9(seed_cfg, label):
    """Exec FULL cell 9 against a seeded MANGABD_CONFIG; return (ns, out, ok)."""
    ns = {
        "MANGABD_CONFIG": seed_cfg,
        "log_event": fake_log_event,
        "model_manager": _InitialManager(),
        "_run_async": _run_async_real,
        "get_page": lambda page_id, required=False: {"page_id": page_id},
        "clear_gpu_cache": _clear_counter,
        "torch": torch_stub,
        "__name__": f"__m7cell9_{label}__",
    }
    buf = io.StringIO()
    ok = True
    try:
        with contextlib.redirect_stdout(buf):
            exec(compile(SRC[9], "cell_09.py", "exec"), ns)
    except Exception as e:
        ok = False
        print(f"      cell 9 raised ({label}): {type(e).__name__}: {e}")
        print(buf.getvalue()[-2500:])
    return ns, buf.getvalue(), ok


# Seed A: the real post-change cell-1 literal (2048)
cfgA = {"inpainting": dict(inpainting_literal)}
nsA, outA, okA = exec_cell9(cfgA, "seedA")
passedA = [t for t in TEST_NAMES if f"✅ {t}" in outA]
check("V3.6 Seed A (post-change literal 2048): exec clean", okA)
check("V3.7 Seed A: 'Cell 9 result: SUCCESS' printed",
      "Cell 9 result: SUCCESS" in outA)
check("V3.8 Seed A: all 10 self-tests present+passing",
      len(passedA) == 10, f"missing={set(TEST_NAMES) - set(passedA)}")
check("V3.9 Seed A: zero self-test failures", "❌ " not in outA)
check("V3.10 Seed A: startup print 'LaMa size : 2048'",
      "LaMa size       : 2048" in outA)
check("V3.11 Seed A: explicit 2048 respected (no stomp)",
      cfgA["inpainting"]["lama_size"] == 2048)
check("V3.12 Seed A: model_manager restored after monkeypatch tests",
      nsA["model_manager"].__class__ is _InitialManager)
check("V3.13 Seed A: clear_gpu_cache restored after monkeypatch tests",
      nsA["clear_gpu_cache"] is _clear_counter)
check("V3.14 Seed A: last_size_effective left None after all-OOM test",
      getattr(nsA["lama_inpaint_full"], "last_size_effective", "unset") is None)

# Seed B: legacy 1024 (regression guard — migration must still fire)
cfgB = {"inpainting": {"lama_size": 1024}}
nsB, outB, okB = exec_cell9(cfgB, "seedB")
passedB = [t for t in TEST_NAMES if f"✅ {t}" in outB]
check("V3.15 Seed B (legacy 1024): exec clean", okB)
check("V3.16 Seed B: 'Cell 9 result: SUCCESS' + 10/10 self-tests",
      "Cell 9 result: SUCCESS" in outB and len(passedB) == 10,
      f"missing={set(TEST_NAMES) - set(passedB)}")
check("V3.17 Seed B: zero self-test failures", "❌ " not in outB)
check("V3.18 Seed B: migration still fires (1024 -> 2048)",
      cfgB["inpainting"]["lama_size"] == 2048)
check("V3.19 Seed B: startup print 'LaMa size : 2048'",
      "LaMa size       : 2048" in outB)

# restore module stubs
for name, mod in saved_modules.items():
    if mod is None:
        sys.modules.pop(name, None)
    else:
        sys.modules[name] = mod

# ── V4: m002_sim_v2 — 0 abort sites ──────────────────────────
print()
print("── V4 m002_sim_v2 fresh-kernel simulator ──")
for old in CELLS_DIR.glob("cell_*.py"):
    old.unlink()
for i in range(27):
    (CELLS_DIR / f"cell_{i:02d}.py").write_text(SRC[i], encoding="utf-8")
sim_out = subprocess.run([sys.executable, str(SIM)], capture_output=True, text=True)
SIM_LOG.parent.mkdir(parents=True, exist_ok=True)
SIM_LOG.write_text(sim_out.stdout, encoding="utf-8")
m = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)", sim_out.stdout)
check("V4.1 simulator ran to completion", m is not None and sim_out.returncode == 0,
      sim_out.stderr[-500:])
if m:
    aborts = int(m.group(1))
    check(f"V4.2 m002_sim_v2 = {aborts} abort sites (expect 0)", aborts == 0)
    for line in sim_out.stdout.splitlines():
        if line.startswith("  >>>"):
            print("      " + line)

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
sys.exit(1 if FAIL else 0)
