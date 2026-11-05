#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-15 — build driver: V-3 wrapper kwarg mismatch fix.

Branch mangabd-009-b2 @ 84aa238 (RF-14 CLOSED by Flash re-verify;
notebook blob sha a06085c3... — same as the RF-14 build target, the
RF-14 commit + Flash docs-only delta left the notebook untouched).

Root cause (RF-15, reproduced in scripts/m009_b2_rf15_repro.py):
  Run All rebinds the global render_bengali_text to the cells 11/12
  V-3 wrapper (vertical-note divert + forward-only fallback). B2's
  render_page (cell 10, RB2-5) passes fit_w=/fit_h= UNCONDITIONALLY
  (quad extents for tilted, None otherwise — the kwarg always goes
  out). The wrapper signature stops at fit_result=None -> TypeError
  at CALL time for EVERY region -> render_page's per-row except
  swallows it as a WARN -> rendered=0, warnings=N, blank final.
  The seam was invisible to every existing instrument: the cell-10
  battery runs before the wrapper exists; chain tests called the
  wrapper directly (fit_result only); nothing ever ran render_page
  AFTER cells 11/12 in one namespace.

Patches (3, manifest re-derivable, scope {11,12} ONLY — cells 6/10
byte-untouched per the RF-15 directive):
  P1  cell 11 wrapper: signature +fit_w/+fit_h; fallback arm forwards
      them to the wrapped base (forward-only discipline kept)
  P2  cell 12 wrapper: same (this is the outermost binding after
      Run All order 11 -> 12)
  P3  cell 12 tail battery Test 20: exec-order integration — after
      the wrappers rebind, render_page on a quad-carrying synthetic
      page in the SAME namespace; asserts rendered>0 (h/t/v ink
      >= 50 each) + zero "unexpected keyword argument" events;
      hard-raises on failure so the seam class can never silently
      blank a Run All again

RF-9 discipline: this driver + the content module + the repro harness
+ the verifier + the pre-commit audit are committed in the RF-15
commit.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b2_rf15_content import (
    C11_P1_OLD, C11_P1_NEW,
    C12_P1_OLD, C12_P1_NEW,
    C12_P2_OLD, C12_P2_NEW,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "84aa238"
MANIFEST = f"{REPO}/scripts/m009_b2_rf15_patches.json"
TARGET_CELLS = {11, 12}
POST_CELLS = "/home/z/my-project/cells_rf15_work"

# ── 0. preconditions ────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-009-b2", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-009-b2 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked RF-15 files)")
for ln in untracked:
    print(f"        {ln}")

# ── 1. load notebook ───────────────────────────────
with open(NB, "rb") as f:
    raw = f.read()
nb = json.loads(raw.decode("utf-8"))

rt = json.dumps(nb, indent=2, ensure_ascii=False)
assert rt.encode("utf-8") == raw, "round-trip writer is NOT byte-faithful!"
print("PASS  json writer byte-faithful on pre-edit file")

assert len(nb["cells"]) == 27
SRC0 = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}

# ── 2. anchored patches ────────────────────────────
SRC = dict(SRC0)
PATCHES = []


def apply(cell, name, old, new):
    src = SRC[cell]
    assert isinstance(old, str) and old, f"{name}: empty old anchor"
    cnt = src.count(old)
    assert cnt == 1, f"{name}: anchor occurs {cnt}x in cell {cell} (must be 1)"
    assert cell in TARGET_CELLS, f"{name}: cell {cell} not in scope {TARGET_CELLS}"
    SRC[cell] = src.replace(old, new)
    PATCHES.append({"cell": cell, "name": name, "old": old, "new": new})
    print(f"PASS  patch applied [cell {cell}] {name}")


apply(11, "P1: V-3 wrapper accepts + forwards fit_w/fit_h (RF-15 fix)",
      C11_P1_OLD, C11_P1_NEW)
apply(12, "P2: V-3 wrapper accepts + forwards fit_w/fit_h (RF-15 fix)",
      C12_P1_OLD, C12_P1_NEW)
apply(12, "P3: battery Test 20 — full-chain render integration (RF-15 guard)",
      C12_P2_OLD, C12_P2_NEW)

# wiring probes on the patched source
assert SRC[11].count("fit_w=None, fit_h=None):") == 1
assert SRC[12].count("fit_w=None, fit_h=None):") == 1
assert SRC[11].count("padding, fit_result,\n                            fit_w, fit_h)") == 1
assert SRC[12].count("padding, fit_result,\n                               fit_w, fit_h)") == 1
assert SRC[12].count("B2 RF-15: full-chain render integration") == 3  # comment + run_test + except arm
assert SRC[12].count("Cell 12 RF-15 integration battery failed") == 1
assert SRC[12].count('"__b2_rf15_t20__"') == 3  # pid + finally cleanup x2
assert SRC[12].count("def run_inpaint_render_all(") == 1
assert SRC[12].count('print("✅ QUALITY CORE active:') == 1
# vertical arm predicate + divert untouched (V-3 behavior preserved)
assert SRC[11].count("w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0") == 1
assert SRC[12].count("w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0") == 1
assert SRC[11].count("return _qc_render_vertical(") == 1
assert SRC[12].count("return _qc_render_vertical(") == 1
print("PASS  wiring probes (signatures, forwards, Test 20, V-3 surfaces)")

# ── 3. AST compile all cells (warnings-as-errors) ──
with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        compile(SRC[i], f"cell_{i:02d}.py", "exec")
print("PASS  AST 27/27 (warnings-as-errors)")

# ── 4. write notebook (byte-faithful writer) ───────
for i in range(27):
    nb["cells"][i]["source"] = SRC[i].splitlines(keepends=True)

out_raw = json.dumps(nb, indent=2, ensure_ascii=False).encode("utf-8")
with open(NB, "wb") as f:
    f.write(out_raw)

with open(NB, "rb") as f:
    check = f.read()
assert check == out_raw, "post-write byte mismatch"

# non-source fields identical (only source arrays changed)
nb_check = json.loads(check.decode("utf-8"))
assert len(nb_check["cells"]) == 27
for i in range(27):
    old_cell, new_cell = json.loads(raw.decode("utf-8"))["cells"][i], nb_check["cells"][i]
    old_keys = {k: v for k, v in old_cell.items() if k != "source"}
    new_keys = {k: v for k, v in new_cell.items() if k != "source"}
    assert old_keys == new_keys, f"cell {i} non-source fields changed"
top_old = {k: v for k, v in json.loads(raw.decode("utf-8")).items() if k != "cells"}
top_new = {k: v for k, v in nb_check.items() if k != "cells"}
assert top_old == top_new, "top-level fields changed"
print("PASS  non-source + top-level fields identical")

# re-derivation proof: new == old + exactly the manifest patches
re_src = dict(SRC0)
for p in PATCHES:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derivation: {p['name']}"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
for i in range(27):
    assert re_src[i] == SRC[i], f"re-derivation mismatch cell {i}"
print("PASS  re-derivation equality (new == old + exactly these patches)")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)

# ── 5. extracts for verification ────────────────────
import os
os.makedirs(POST_CELLS, exist_ok=True)
for i in range(27):
    with open(f"{POST_CELLS}/cell_{i:02d}.py", "w", encoding="utf-8") as f:
        f.write(SRC[i])

new_sha = hashlib.sha256(open(NB, "rb").read()).hexdigest()
print(f"PASS  build complete: notebook sha256 {new_sha}")
print(f"      manifest -> {MANIFEST}")
print(f"      post cells -> {POST_CELLS}")
for c in sorted(TARGET_CELLS):
    print(f"      cell {c}: {len(SRC0[c])} -> {len(SRC[c])} chars "
          f"(+{len(SRC[c]) - len(SRC0[c])})")
