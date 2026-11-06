#!/usr/bin/env python3
r"""MANGABD-009 B2.1 Phase C — build driver: RB21-2 + RB21-3.

Branch mangabd-009-b2-1 @ 67bc594 (B2.1 Phase A, docs-only; the notebook
blob == main tip == the Flash-RF-18-pinned merged B2 bytes 98c01952...).

Ruling (Owner, on the Phase A findings 67bc594):
  RB21-1 REJECT  asymmetric parity  — placement-null (<0.001 deg);
                 T5 class resists (2.47 > 2); Owner-accepted RF-18
                 bytes stay; rendered-ink angle stays report-only.
  RB21-2 APPROVE guard except-WARN  — exception-type allowlist:
                 FileNotFoundError (cold-start) silent, others WARN
                 + return False (fail-open value unchanged).
  RB21-3 APPROVE quarantine         — rendered=0 AND renderable rows
                 -> save under quarantine/ (NOT final/), WARN, do NOT
                 mark stage done; eyeball renders stay legitimate
                 (final + done). New battery Test 22 with the
                 fail-on-current-bytes contract.
  RB21-4 REJECT  ring-margin tuning — rung-1 (CTD mask) covers 20/20;
                 margin churn re-opens V3/V6 risk.

Implementation scope (the ruling's NEXT block): items 2+3 ONLY,
cells {10} ONLY, healthy-path bytes byte-identical, NO changes to
items 1+4.

Patches (3, all cell 10, manifest re-derivable):
  P1  `_b2_renderable_rows_present` helper (the RF-14 guard's
      renderable-rows predicate extracted VERBATIM — guard + quarantine
      share ONE condition) + `_b2_blank_cache_stale` rewritten to call
      it + except split with the allowlist (RB21-2)
  P2  render_page quarantine branch before the unconditional save
      (RB21-3): quarantine/final.jpg + WARN + no stage-done + df save
      preserved + returns the canvas; rendered>0 path byte-identical
  P3  battery Test 22 — (a) quarantine arms, (b) recovery re-render
      inks, (c) eyeball legitimacy preserved, (d) guard allowlist
      quiet/loud; fixture cleaned up (Test 19 discipline)

RF-9 discipline: this driver + the content module + the verifier + the
pre-commit audit are committed in the Phase C commit.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b21_phaseC_content import (
    C10_P1_OLD, C10_P1_NEW,
    C10_P2_OLD, C10_P2_NEW,
    C10_P3_OLD, C10_P3_NEW,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "67bc594"
MANIFEST = f"{REPO}/scripts/m009_b21_phaseC_patches.json"
TARGET_CELLS = {10}
POST_CELLS = "/home/z/my-project/cells_b21_fix"

# ── 0. preconditions ────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-009-b2-1", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-009-b2-1 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked Phase C files)")
for ln in untracked:
    print(f"        {ln}")

# ── 1. load notebook ───────────────────────────────
with open(NB, "rb") as f:
    raw = f.read()
nb = json.loads(raw.decode("utf-8"))

rt = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
assert rt.encode("utf-8") == raw, "round-trip writer is NOT byte-faithful!"
print("PASS  json writer byte-faithful on pre-edit file (indent=1 + trailing NL)")

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


apply(10, "P1: _b2_renderable_rows_present helper + guard except-allowlist (RB21-2)",
      C10_P1_OLD, C10_P1_NEW)
apply(10, "P2: render_page never-save-blank quarantine branch (RB21-3)",
      C10_P2_OLD, C10_P2_NEW)
apply(10, "P3: battery Test 22 — fail-on-current-bytes contract (RB21-2+3)",
      C10_P3_OLD, C10_P3_NEW)

# wiring probes on the patched source
assert SRC[10].count("def _b2_renderable_rows_present(") == 1
assert SRC[10].count("def _b2_blank_cache_stale(") == 1
assert SRC[10].count("not _b2_blank_cache_stale(page_id)") == 1
assert SRC[10].count("return _b2_renderable_rows_present(page_id)") == 1
assert SRC[10].count("_b21_quarantine = _b2_renderable_rows_present(page_id)") == 1
assert SRC[10].count("except FileNotFoundError:") == 2      # guard + quarantine
assert SRC[10].count("Blank-cache guard raised") == 1
assert SRC[10].count("BLANK render quarantined") == 2      # log_event + print
assert SRC[10].count("Quarantine predicate raised") == 1
assert SRC[10].count("B2.1 RB21-2/RB21-3: blank-render quarantine") == 2  # ok + except arm
assert SRC[10].count("B2 RF-14: blank-cache trap") == 2     # Test 19 ok + except arm
assert SRC[10].count("# RF-13 fixture hygiene:") == 1
assert SRC[10].count("def render_page(") == 1
# B1/B2 Phase C surfaces preserved
assert SRC[10].count("def _b2_render_angle(") == 1
assert SRC[10].count("def _estimate_region_angle") == 0  # estimator lives in cell 6
assert 'rotated = text_canvas.rotate(' in SRC[10]  # production rotate block
assert SRC[10].count("fit_w if fit_w is not None else w") == 1
assert SRC[10].count('print(f"    ✅ Render cached: {page_id}")') == 1
# quarantine path uses the page-dir sibling, never the final slot
assert SRC[10].count('get_page_dir(page_id) / "quarantine"') == 1
assert SRC[10].count('canvas_pil.save(_b21_qdir / "final.jpg", quality=95)') == 1
assert SRC[10].count('save_image_artifact(page_id, "final", canvas_pil, quality=95)') == 1
print("PASS  wiring probes (helper, allowlist, quarantine, Test 22, B1/B2 surfaces)")

# ── 3. AST compile all cells (warnings-as-errors) ──
with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        compile(SRC[i], f"cell_{i:02d}.py", "exec")
print("PASS  AST 27/27 (warnings-as-errors)")

# ── 4. write notebook (byte-faithful writer) ────────
for i in range(27):
    nb["cells"][i]["source"] = SRC[i].splitlines(keepends=True)

out_raw = (json.dumps(nb, indent=1, ensure_ascii=False) + "\n").encode("utf-8")
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
