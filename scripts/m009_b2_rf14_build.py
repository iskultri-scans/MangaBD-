#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-14 — build driver: stale BLANK render-cache guard.

Branch mangabd-009-b2 @ fd8d625 (Flash Phase D APPROVED; docs-only delta
vs c05c6e8 — notebook blob identical, sha256 08225748...).

Root cause (RF-14, reproduced + instrumented in the Owner-like harness):
  render_page's cache check returns the stage-cached final.jpg whenever
  the render stage is marked done and force=False. The B2 live-gate's
  own procedure (Phase D: pre-translation eyeball renders of the
  diagonal/axis-aligned pages, kill-switch rollback WITHOUT re-detect)
  marks the render stage done with a BLANK final (rendered=0 — no
  translations applied yet). The Owner then applies 8/9 translations
  and calls step_4 (run_render_all, resume-aware force=False): every
  page cache-hits its poisoned blank final -> "renders ZERO text" on
  every region class (horizontal + tilted + vertical). PRE-B2 cells
  reproduce the same trap in the same harness — the cache defect is
  version-agnostic and LATENT; B2's gate procedure is the trigger, and
  B2 shipped without a guard. Fix scope: cell 10 ONLY (cells {6,10}
  allowed; cell 6 needs no change — its estimator stores are not the
  zero-ink cause; disclosed as observation O-RF14-1/2).

Patches (3, all cell 10, manifest re-derivable):
  P1  `_b2_blank_cache_stale(page_id)` helper after the B2 render-angle
      mirror (meta rendered_regions == 0 AND >=1 now-renderable Bengali
      row; global df or CSV fallback; fail-closed -> False)
  P2  render_page cache check: bypass + loud WARN + reset_page when the
      cached render is a stale blank; healthy pages byte-identical
  P3  battery Test 19 — RF-14 regression guard: traps arms, bypasses,
      renders visible ink for horizontal AND tilted AND vertical
      regions on a full synthetic page, proves the healthy cache stays
      byte-stable, and cleans its fixture up (cell-3 discipline)

RF-9 discipline: this driver + the content module + the verifier +
the pre-commit audit are committed in the RF-14 commit.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b2_rf14_content import (
    C10_P1_OLD, C10_P1_NEW,
    C10_P2_OLD, C10_P2_NEW,
    C10_P3_OLD, C10_P3_NEW,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "fd8d625"
MANIFEST = f"{REPO}/scripts/m009_b2_rf14_patches.json"
TARGET_CELLS = {10}
POST_CELLS = "/home/z/my-project/cells_rf14_fix"

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
print(f"PASS  tracked tree clean ({len(untracked)} untracked RF-14 files)")
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


apply(10, "P1: _b2_blank_cache_stale helper (RF-14 root-cause guard)",
      C10_P1_OLD, C10_P1_NEW)
apply(10, "P2: render_page cache check — stale blank bypass (RF-14 fix)",
      C10_P2_OLD, C10_P2_NEW)
apply(10, "P3: battery Test 19 — RF-14 regression guard (h/t/v ink + trap)",
      C10_P3_OLD, C10_P3_NEW)

# wiring probes on the patched source
assert SRC[10].count("def _b2_blank_cache_stale(") == 1
assert SRC[10].count("not _b2_blank_cache_stale(page_id)") == 1
assert SRC[10].count("B2 RF-14: blank-cache trap") == 2  # run_test + except arm
assert SRC[10].count("# RF-13 fixture hygiene:") == 1
assert SRC[10].count("def render_page(") == 1
# B1/B2 Phase C surfaces preserved
assert SRC[10].count("def _b2_render_angle(") == 1
assert SRC[10].count("def _estimate_region_angle") == 0  # estimator lives in cell 6
assert 'rotated = text_canvas.rotate(' in SRC[10]  # production rotate block
assert SRC[10].count("fit_w if fit_w is not None else w") == 1
# healthy-cache parity probes: cached return line unchanged in shape
assert SRC[10].count('print(f"    ✅ Render cached: {page_id}")') == 1
print("PASS  wiring probes (helper, cache guard, Test 19, B1/B2 surfaces)")

# ── 3. AST compile all cells (warnings-as-errors) ──
with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        compile(SRC[i], f"cell_{i:02d}.py", "exec")
print("PASS  AST 27/27 (warnings-as-errors)")

# ── 4. write notebook (byte-faithful writer) ────────
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
print(f"      cell 10: {len(SRC0[10])} -> {len(SRC[10])} chars "
      f"(+{len(SRC[10]) - len(SRC0[10])})")
