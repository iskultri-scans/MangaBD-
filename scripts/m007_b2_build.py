#!/usr/bin/env python3
r"""MANGABD-007 B2 (Phase C) — build driver: S05-1/S05-2 hardening.

Branch mangabd-007-b2 @ dcd96c0. Target cells {5, 8} ONLY (25
non-target cells asserted byte-identical). Implements the Owner
directive (B2 backlog): S05-1 embedding model warning (cell 5 —
ModelManager.ensure_embedding created, Bengali diagnostics, graceful
degrade, Test 10) + S05-2 paste-back escape normalize (cell 8 —
iterative unescape-to-stable, residual-escape WARN-never-fail,
trailing-backslash strip, Tests 31-32).

Patch mechanism: anchored exact-replace, each old-string
unique-asserted; the full (cell, name, old, new) manifest is written
to scripts/m007_b2_patches.json so the verifier re-derives
new == old + exactly these patches. JSON writer proven byte-faithful
on the pre-edit file (no re-serialization drift).

RF-9 lesson (applied at Phase C time): this driver + the two content
modules + the verifier + the pre-commit audit are committed IN the
Phase C commit — no uncommitted-instrument gap.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m007_b2_content5 import (
    CELL5_ENSURE_EMBEDDING_NEW,
    CELL5_ENSURE_EMBEDDING_OLD,
    CELL5_TEST10_NEW,
    CELL5_TEST10_OLD,
)
from m007_b2_content8 import (
    CELL8_DOCSTRING_NEW,
    CELL8_DOCSTRING_OLD,
    CELL8_STATS_NEW,
    CELL8_STATS_OLD,
    CELL8_TESTS3132_NEW,
    CELL8_TESTS3132_OLD,
    CELL8_UNESCAPE_NEW,
    CELL8_UNESCAPE_OLD,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "dcd96c0"
MANIFEST = f"{REPO}/scripts/m007_b2_patches.json"
TARGET_CELLS = {5, 8}

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                             capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-007-b2", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                           capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-007-b2 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                         capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"tracked files dirty: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked)")
for ln in untracked:
    print(f"        untracked: {ln[3:]}")

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


# ---- CELL 5 (S05-1) ----
apply(5, "ensure_embedding + _embedding_load_failed (S05-1)",
      CELL5_ENSURE_EMBEDDING_OLD, CELL5_ENSURE_EMBEDDING_NEW)
apply(5, "Test 10: embedding graceful-degrade battery (S05-1)",
      CELL5_TEST10_OLD, CELL5_TEST10_NEW)

# ---- CELL 8 (S05-2) ----
apply(8, "parse_ai_text docstring step-1 S05-2 note",
      CELL8_DOCSTRING_OLD, CELL8_DOCSTRING_NEW)
apply(8, "stats dict: escape_warn + trailing_backslash counters (S05-2)",
      CELL8_STATS_OLD, CELL8_STATS_NEW)
apply(8, "unescape pipeline: iterative + validate + trailing-strip (S05-2)",
      CELL8_UNESCAPE_OLD, CELL8_UNESCAPE_NEW)
apply(8, "Tests 31-32: double-escaped + mixed-escape fixtures (S05-2)",
      CELL8_TESTS3132_OLD, CELL8_TESTS3132_NEW)

# ── 2. scope + static gates ─────────────────────────────────
non_target = [i for i in range(27) if i not in TARGET_CELLS]
for i in non_target:
    assert SRC[i] == SRC0[i], f"cell {i} drifted!"
print(f"PASS  {len(non_target)} non-target cells byte-identical (scope exact: {sorted(TARGET_CELLS)})")

for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(SRC[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL  cell {i} warning-as-error: {w}")
print("PASS  AST compile 27/27 (warnings-as-errors)")

for i in sorted(TARGET_CELLS):
    print(f"      cell {i:2d}: {SRC0[i].count(chr(10)) + 1} -> {SRC[i].count(chr(10)) + 1} lines")

# S05-1 wiring probes on the built source
assert SRC[5].count("def ensure_embedding(") == 1
assert SRC[5].count("def _embedding_load_failed(") == 1
assert 'm.startswith("⚠️ Embedding model load failed:")' in SRC[5]
assert "Fix: !pip install sentence-transformers OR check " in SRC[5]
assert SRC[5].count("run_test(") == 18, f"cell-5 run_test occurrences = {SRC[5].count('run_test(')} (expected def + 17 call arms)"
# S05-2 wiring probes
assert SRC[8].count("stats[\"escape_warn\"] += 1") == 1
assert SRC[8].count("stats[\"trailing_backslash\"] += 1") == 1
assert SRC[8].count("double-escaped fixture 100% parse (S05-2)") == 2  # pass + fail arms
assert SRC[8].count("mixed-escape fixture 100% parse (S05-2)") == 2
print("PASS  S05-1/S05-2 wiring probes (methods, diagnostics, counters, tests)")

# ── 3. write notebook (byte-faithful writer) ────────────────
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
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derivation: {p['name']} anchor"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
for i in range(27):
    assert re_src[i] == SRC[i], f"re-derivation mismatch cell {i}"
print("PASS  re-derivation equality (new == old + exactly these patches)")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)
print(f"\n-> {NB}")
print(f"-> {MANIFEST} ({len(PATCHES)} patches)")
print(f"notebook md5: {hashlib.md5(out_raw).hexdigest()}")
print("BUILD OK")
