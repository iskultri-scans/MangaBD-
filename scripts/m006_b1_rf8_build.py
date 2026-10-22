#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-8 — build driver (onnxruntime + download hang fix).

Branch mangabd-006-b1 @ 0b5d11d (RF-7 a0e6bbf + Flash RF-7 delta CLOSED,
report-only — notebook bytes unchanged since a0e6bbf). Scope: cells
{0, 5, 7} — the RF-8 directive's explicit scope; the 24 non-target cells
stay byte-identical to 0b5d11d.

Patch mechanism identical to RF-7: anchored exact-replace, each old-string
unique-asserted; manifest written to scripts/m006_b1_rf8_patches.json so
the verifier can re-derive new == old + exactly these patches. JSON
writer re-proven byte-faithful on the pre-edit file.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/scripts")
from m006_b1_rf8_content import (
    C0_PACKAGES_NEW, C0_PACKAGES_OLD, C5_DOCSTRING_NEW, C5_DOCSTRING_OLD,
    C5_DOWNLOADER_NEW, C5_DOWNLOADER_OLD, C5_LOOP_NEW, C5_LOOP_OLD,
    C5_SECTION_NEW, C5_SECTION_OLD, C5_TIMEOUT_NEW, C5_TIMEOUT_OLD,
    C7_HEADER_NEW, C7_HEADER_OLD, C7_T29_HEADER_NEW, C7_T29_HEADER_OLD,
    C7_T29_IMPORTS_NEW, C7_T29_IMPORTS_OLD, C7_T29_PHASE_KA_NEW,
    C7_T29_PHASE_KA_OLD, C7_T29_PHASE_KHA_NEW, C7_T29_PHASE_KHA_OLD,
    C7_T29_TAIL_NEW, C7_T29_TAIL_OLD,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "0b5d11d"  # branch tip (RF-7 delta CLOSED; notebook == a0e6bbf)
MANIFEST = "/home/z/my-project/scripts/m006_b1_rf8_patches.json"
TARGET_CELLS = {0, 5, 7}  # RF-8 touched cells (directive-authorized)

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-006-b1", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-006-b1 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
assert not tracked_dirty, f"tracked files dirty: {tracked_dirty}"
print("PASS  tracked tree clean")

with open(NB, "rb") as f:
    raw = f.read()
nb = json.loads(raw.decode("utf-8"))

rt = json.dumps(nb, indent=2, ensure_ascii=False)
assert rt.encode("utf-8") == raw, "round-trip writer is NOT byte-faithful!"
print("PASS  json writer byte-faithful on pre-edit file")

assert len(nb["cells"]) == 27
SRC0 = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}

# ── 1. anchored patches ─────────────────────────────────────
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


# ---- CELL 0 (Defect 1) ----
apply(0, "RF-8 onnxruntime in DETECTION_PACKAGES",
      C0_PACKAGES_OLD, C0_PACKAGES_NEW)

# ---- CELL 5 (Defect 2) ----
apply(5, "RF-8 per-file download timeout constant",
      C5_TIMEOUT_OLD, C5_TIMEOUT_NEW)
apply(5, "RF-8 self-heal section header", C5_SECTION_OLD, C5_SECTION_NEW)
apply(5, "RF-8 downloader: local_dir direct write + timeout",
      C5_DOWNLOADER_OLD, C5_DOWNLOADER_NEW)
apply(5, "RF-8 _ensure_engine_weights docstring tier-2",
      C5_DOCSTRING_OLD, C5_DOCSTRING_NEW)
apply(5, "RF-8 download loop: per-file verify + progress",
      C5_LOOP_OLD, C5_LOOP_NEW)

# ---- CELL 7 (Test 29 extension) ----
apply(7, "RF-8 Tests 26-29 header comment", C7_HEADER_OLD, C7_HEADER_NEW)
apply(7, "RF-8 Test 29 header comment",
      C7_T29_HEADER_OLD, C7_T29_HEADER_NEW)
apply(7, "RF-8 Test 29 imports (contextlib+io)",
      C7_T29_IMPORTS_OLD, C7_T29_IMPORTS_NEW)
apply(7, "RF-8 Test 29 phase ka: fail-fast assertion",
      C7_T29_PHASE_KA_OLD, C7_T29_PHASE_KA_NEW)
apply(7, "RF-8 Test 29 phase kha: progress capture",
      C7_T29_PHASE_KHA_OLD, C7_T29_PHASE_KHA_NEW)
apply(7, "RF-8 Test 29 hang phase + verdict",
      C7_T29_TAIL_OLD, C7_T29_TAIL_NEW)

# ── 2. static gates ─────────────────────────────────────────
for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(SRC[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL  cell {i} warning-as-error: {w}")
print("PASS  AST compile 27/27 (warnings-as-errors)")

non_target = [i for i in range(27) if i not in TARGET_CELLS]
untouched = [i for i in non_target if SRC0[i] == SRC[i]]
assert len(untouched) == len(non_target) == 24, \
    f"non-target cells changed: {[i for i in non_target if SRC0[i] != SRC[i]]}"
print(f"PASS  24 non-target cells byte-identical (touched = {sorted(TARGET_CELLS)})")

for i in sorted(TARGET_CELLS):
    print(f"      cell {i:2d}: {SRC0[i].count(chr(10)) + 1} -> "
          f"{SRC[i].count(chr(10)) + 1} lines")

# ── 3. write notebook (byte-faithful writer) ────────────────
for i in range(27):
    nb["cells"][i]["source"] = SRC[i].splitlines(keepends=True)

out = json.dumps(nb, indent=2, ensure_ascii=False).encode("utf-8")
with open(NB, "wb") as f:
    f.write(out)

with open(NB, "rb") as f:
    reread = f.read()
nb2 = json.loads(reread.decode("utf-8"))
assert [ "".join(c["source"]) for c in nb2["cells"] ] == \
       [ SRC[i] for i in range(27) ], "post-write source mismatch"
print("PASS  notebook written + re-read verification")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump({
        "base_ref": BASE_REF,
        "target_cells": sorted(TARGET_CELLS),
        "patches": PATCHES,
    }, f, indent=2, ensure_ascii=False)
print(f"PASS  manifest -> {MANIFEST} ({len(PATCHES)} patches)")

print(f"\nnotebook: {len(raw)} -> {len(reread)} bytes, "
      f"md5 {hashlib.md5(raw).hexdigest()[:16]} -> "
      f"{hashlib.md5(reread).hexdigest()[:16]}")
print("BUILD OK")
