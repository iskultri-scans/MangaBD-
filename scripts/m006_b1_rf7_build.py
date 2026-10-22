#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-7 — build driver (weights self-heal).

Branch mangabd-006-b1 @ d569c08 (M6-B1 Phase C delivery; Flash Phase D
report-only commit 186af82 touched only GLM_5_3_FLASH.md, notebook bytes
unchanged). Scope: cell 5 (loader) + cell 7 (Test 29) — within the batch
scope {5, 7, 15, 25}; the 23 non-target cells stay byte-identical to
d569c08 (cells 15/25 untouched by RF-7).

Patch mechanism identical to the M6-B1 build: anchored exact-replace,
each old-string unique-asserted; manifest written to
scripts/m006_b1_rf7_patches.json so the verifier can re-derive
new == old + exactly these patches. JSON writer re-proven byte-faithful
on the pre-edit file.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/scripts")
from m006_b1_rf7_content import (
    C5_BABERU_CALL_NEW, C5_BABERU_CALL_OLD, C5_BABERU_NEW, C5_BABERU_OLD,
    C5_COMMENT_NEW, C5_COMMENT_OLD, C5_KELLENOK_CALL_NEW,
    C5_KELLENOK_CALL_OLD, C5_KELLENOK_NEW, C5_KELLENOK_OLD,
    C5_SELFHEAL_NEW, C5_SELFHEAL_OLD, C5_SHA_HELPER_NEW, C5_SHA_HELPER_OLD,
    C7_HEADER_NEW, C7_HEADER_OLD, C7_T29_NEW, C7_T29_OLD,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "d569c08"  # M6-B1 Phase C delivery (RF-7 builds on it)
MANIFEST = "/home/z/my-project/scripts/m006_b1_rf7_patches.json"
TARGET_CELLS = {5, 7}  # RF-7 touched cells (subset of the batch's {5,7,15,25})

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


# ---- CELL 5 ----
apply(5, "RF-7 registry comment (vendored -> download)",
      C5_COMMENT_OLD, C5_COMMENT_NEW)
apply(5, "RF-7 kellenok provenance pins", C5_KELLENOK_OLD, C5_KELLENOK_NEW)
apply(5, "RF-7 baberu provenance pins", C5_BABERU_OLD, C5_BABERU_NEW)
apply(5, "RF-7 sha256 streaming helper", C5_SHA_HELPER_OLD, C5_SHA_HELPER_NEW)
apply(5, "RF-7 weights self-heal methods", C5_SELFHEAL_OLD, C5_SELFHEAL_NEW)
apply(5, "RF-7 ensure_kellenok call-site",
      C5_KELLENOK_CALL_OLD, C5_KELLENOK_CALL_NEW)
apply(5, "RF-7 ensure_baberu call-site",
      C5_BABERU_CALL_OLD, C5_BABERU_CALL_NEW)

# ---- CELL 7 ----
apply(7, "RF-7 Tests 26-29 header comment", C7_HEADER_OLD, C7_HEADER_NEW)
apply(7, "RF-7 Test 29 (weights self-heal)", C7_T29_OLD, C7_T29_NEW)

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
assert len(untouched) == len(non_target) == 25, \
    f"non-target cells changed: {[i for i in non_target if SRC0[i] != SRC[i]]}"
print(f"PASS  25 non-target cells byte-identical (touched = {sorted(TARGET_CELLS)})")

for i in sorted(TARGET_CELLS):
    print(f"      cell {i:2d}: {SRC0[i].count(chr(10)) + 1} -> {SRC[i].count(chr(10)) + 1} lines")

# ── 3. write notebook (byte-faithful writer) ────────────────
for i in range(27):
    nb["cells"][i]["source"] = SRC[i].splitlines(keepends=True)

out_raw = json.dumps(nb, indent=2, ensure_ascii=False).encode("utf-8")
with open(NB, "wb") as f:
    f.write(out_raw)

with open(NB, "rb") as f:
    check = f.read()
assert check == out_raw, "post-write byte mismatch"

nb_check = json.loads(check.decode("utf-8"))
assert len(nb_check["cells"]) == 27
for i in range(27):
    old_cell = json.loads(raw.decode("utf-8"))["cells"][i]
    new_cell = nb_check["cells"][i]
    old_keys = {k: v for k, v in old_cell.items() if k != "source"}
    new_keys = {k: v for k, v in new_cell.items() if k != "source"}
    assert old_keys == new_keys, f"cell {i} non-source fields changed"
top_old = {k: v for k, v in json.loads(raw.decode("utf-8")).items() if k != "cells"}
top_new = {k: v for k, v in nb_check.items() if k != "cells"}
assert top_old == top_new, "top-level fields changed"
print("PASS  non-source + top-level fields identical")

# re-derivation proof
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
