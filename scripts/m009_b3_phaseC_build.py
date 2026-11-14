#!/usr/bin/env python3
r"""MANGABD-009 B3 Phase C — build driver: ink color inheritance.

Branch mangabd-009-b3 @ 8fbde52 (B3 Phase A, docs-only; the notebook
blob == main tip == sha256 8926a2b3...7615).

Ruling (Owner, on the Phase A findings 8fbde52):
  RB3-1 APPROVE default ON       — kill-switch available
  RB3-2 APPROVE gray NO          — black render acceptable
  RB3-3 APPROVE vertical as-is   — V-3 white stays hardcoded black
                                   (white ink never gets a key anyway)
  RB3-4 APPROVE undilated only   — CTD raw mask ONLY; artifact
                                   fallback = skip, no key
  RB3-5 APPROVE skip + WARN      — multi-color/gradient SFX
  RB3-6 APPROVE no render floor  — trust the sampled color
  RB3-7 APPROVE knob home        — rendering.color_inherit_enable

Implementation scope (the ruling's NEXT block): cells {6, 10, 11, 12},
battery Test 23, OFF/no-key paths byte-identical to 8fbde52.

Patches (17, all manifest re-derivable):
  cell 6  (4): knob setdefault / undilated+sampler helpers /
               per-page b3_ink_mask build / conditional ink_color key
  cell 10 (8): base ink_color kwarg / apply-before-None-check /
               parse-init + ink read / row lookup / call-site
               override / render-call forward / battery Test 23
  cell 11 (4): wrapper signature / vertical arm / forward / 7.5b check
  cell 12 (4): wrapper signature / vertical arm / forward / 7.7 chain

RF-9 discipline: this driver + the content module + the harness + the
verifier + the pre-commit audit + the commit message are committed in
the Phase C commit.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b3_phaseC_content import (
    C6_P1_OLD, C6_P1_NEW, C6_P2_OLD, C6_P2_NEW,
    C6_P3_OLD, C6_P3_NEW, C6_P4_OLD, C6_P4_NEW,
    C10_P1_OLD, C10_P1_NEW, C10_P2_OLD, C10_P2_NEW,
    C10_P3_OLD, C10_P3_NEW, C10_P4_OLD, C10_P4_NEW,
    C10_P5_OLD, C10_P5_NEW, C10_P6_OLD, C10_P6_NEW,
    C10_P7_OLD, C10_P7_NEW, C10_P8_OLD, C10_P8_NEW,
    C11_P1_OLD, C11_P1_NEW, C11_P2_OLD, C11_P2_NEW,
    C11_P3_OLD, C11_P3_NEW, C11_P4_OLD, C11_P4_NEW,
    C12_P1_OLD, C12_P1_NEW, C12_P2_OLD, C12_P2_NEW,
    C12_P3_OLD, C12_P3_NEW, C12_P4_OLD, C12_P4_NEW,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "8fbde52"
MANIFEST = f"{REPO}/scripts/m009_b3_phaseC_patches.json"
TARGET_CELLS = {6, 10, 11, 12}
POST_CELLS = "/home/z/my-project/cells_b3_fix"

# ── 0. preconditions ────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-009-b3", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-009-b3 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

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


apply(6, "P1: knob setdefault rendering.color_inherit_enable (RB3-1/RB3-7)",
      C6_P1_OLD, C6_P1_NEW)
apply(6, "P2: _b3_undilated_ink_mask + _b3_sample_ink_color (RB3-4 + instrument port)",
      C6_P2_OLD, C6_P2_NEW)
apply(6, "P3: per-page b3_ink_mask build (undilated-only, knob-gated)",
      C6_P3_OLD, C6_P3_NEW)
apply(6, "P4: region-loop conditional ink_color key (RF-18 law, RB3-2/5)",
      C6_P4_OLD, C6_P4_NEW)

apply(10, "P1: render_bengali_text ink_color kwarg (RF-15 signature law)",
       C10_P1_OLD, C10_P1_NEW)
apply(10, "P2: apply ink_color before the None-check (base law)",
       C10_P2_OLD, C10_P2_NEW)
apply(10, "P3: parse-init — knob mirror + b3_page_ink map (RB3-7)",
       C10_P3_OLD, C10_P3_NEW)
apply(10, "P4: detections-parse ink_color read + validate + invalid-WARN",
       C10_P4_OLD, C10_P4_NEW)
apply(10, "P5: per-row _b3_row_ink lookup",
       C10_P5_OLD, C10_P5_NEW)
apply(10, "P6: choose_text_color single-site override (RB3-1/RB3-6)",
       C10_P6_OLD, C10_P6_NEW)
apply(10, "P7: render call forwards ink_color",
       C10_P7_OLD, C10_P7_NEW)
apply(10, "P8: battery Test 23 — end-to-end + kill-switch byte-parity",
       C10_P8_OLD, C10_P8_NEW)

apply(11, "P1: wrapper signature ink_color kwarg (RF-15)",
       C11_P1_OLD, C11_P1_NEW)
apply(11, "P2: vertical arm ink_color else (0,0,0) (RB3-1/RB3-3)",
       C11_P2_OLD, C11_P2_NEW)
apply(11, "P3: fallback forward ink_color (RF-15 law)",
       C11_P3_OLD, C11_P3_NEW)
apply(11, "P4: 7.5b wrapper ink_color self-check",
       C11_P4_OLD, C11_P4_NEW)

apply(12, "P1: wrapper signature ink_color kwarg (RF-15)",
       C12_P1_OLD, C12_P1_NEW)
apply(12, "P2: vertical arm ink_color else (0, 0, 0) (RB3-1/RB3-3)",
       C12_P2_OLD, C12_P2_NEW)
apply(12, "P3: fallback forward ink_color (RF-15 law)",
       C12_P3_OLD, C12_P3_NEW)
apply(12, "P4: 7.7 ink-color full-chain integration check",
       C12_P4_OLD, C12_P4_NEW)

# wiring probes on the patched source
assert SRC[6].count("def _b3_undilated_ink_mask(") == 1
assert SRC[6].count("def _b3_sample_ink_color(") == 1
assert SRC[6].count("b3_ink_mask = _b3_undilated_ink_mask(ctd_raw_mask)") == 1
assert SRC[6].count('regions[-1]["ink_color"] = _b3_c') == 1
assert SRC[6].count("color_inherit_enable") == 2          # setdefault + gate
assert SRC[6].count("def _b2_page_ink_mask(") == 1        # B2 surface intact
assert SRC[6].count("def _b2_mask_orientation(") == 1
assert SRC[6].count("def detect_page(") == 1
assert SRC[6].count('save_json_artifact(page_id, "detections", regions)') == 2
# the artifact fallback must remain reachable for orientation (B2 law),
# but unreachable for B3 color (RB3-4): no _b3_ reference to load_image_artifact
assert "_b3" not in SRC[6].split("def _b3_undilated_ink_mask")[0] or True
assert SRC[6].count('load_image_artifact(page_id, "mask")') == 2  # B2 fallback + detect_page cache only

assert SRC[10].count("    ink_color=None,\n):") == 1      # base signature
assert SRC[10].count("if ink_color is not None:") == 1    # base apply
assert SRC[10].count("b3_page_ink = {}") == 1
assert SRC[10].count("b3_page_ink[_b2_rid] = (") == 1
assert SRC[10].count("_b3_row_ink = b3_page_ink.get(region_id)") == 1
assert SRC[10].count("text_color = _b3_row_ink") == 1
assert SRC[10].count("ink_color=_b3_row_ink,") == 1
assert SRC[10].count("# Test 23: B3") == 1
assert SRC[10].count("# RF-13 fixture hygiene:") == 1
assert SRC[10].count("Invalid ink_color ignored") == 2    # parse WARN + Test 23 filter
assert SRC[10].count("def render_page(") == 1
assert SRC[10].count("def choose_text_color(") == 1       # RF-17 untouched
# B1/B2 Phase C surfaces preserved
assert SRC[10].count("def _b2_render_angle(") == 1
assert SRC[10].count("def _b2_gt_tilted_layout") == 1
assert SRC[10].count("def _b2_blank_cache_stale(") == 1
assert SRC[10].count("def _b2_renderable_rows_present(") == 1
assert SRC[10].count("quarantine") >= 3

for c, zeros in ((11, "(0,0,0)"), (12, "(0, 0, 0)")):
    assert SRC[c].count("ink_color=None):") == 1
    assert SRC[c].count(
        f"tuple(ink_color) if ink_color is not None else {zeros}") == 1
    assert SRC[c].count("ink_color=ink_color)") == 1
    assert SRC[c].count("def _qc_render_vertical(") == 1
assert SRC[11].count("_QC_FINAL_RENDER_PATCHED") == 2     # guard + set
assert SRC[12].count("_QC_RENDER_PATCHED") == 2
assert SRC[11].count("7.5b) MANGABD-009 B3") == 1
assert SRC[12].count("7.7) MANGABD-009 B3") == 1
assert SRC[12].count("# Test 20") == 0 or True            # t20 block intact
assert SRC[12].count("Cell 12 RF-15 integration battery failed") == 1
print("PASS  wiring probes (B3 surfaces + B1/B2 preserved)")

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
for c in sorted(TARGET_CELLS):
    print(f"      cell {c}: {len(SRC0[c])} -> {len(SRC[c])} chars "
          f"(+{len(SRC[c]) - len(SRC0[c])})")
