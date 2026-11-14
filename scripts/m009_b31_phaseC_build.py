#!/usr/bin/env python3
r"""MANGABD-009 B3.1 Phase C — build driver: per-line color inheritance.

Branch mangabd-009-b3 @ cf01aef (B3 Phase D tip, UNMERGED — B3 merge
hold intact; notebook blob == branch tip == sha256 c719feb6...4d6).

Ruling (Owner, on Phase A 13a6e02 — registered in agents/GLM_5_3.md
as M9-B31-R): RB31-1..RB31-8 all approved + phase-C addendum:
  RB31-1  tau = 0.15                       (chromatic cluster law)
  RB31-2  raw-threshold locator ONLY       (no close, per-line law)
  RB31-3  line_colors kwarg + key          (ink_color retained)
  RB31-4  per-line cluster median          (i < min(n_orig, n_trans))
  RB31-5  V-3 vertical path unchanged      (kwarg accepted, unused)
  RB31-6  Test 24 assertion @ 2000px       (tiny-text guard)
  RB31-7  Phase C on top of cf01aef        (cells {6,10,11,12})
  Addendum: V5 CONFIRMED (owner detections.json, id=8 w=51 h=62);
  narrow-bubble fix — skip close(5,5)x2 when region w < 80px.

Patches (16, all manifest re-derivable):
  cell 6  (4): per-line law helpers / raw-locator build / narrow-fix
               at the orientation call site / conditional line_colors
  cell 10 (9): base line_colors kwarg / per-line materialize+strokes /
               rotated forward / horizontal loop / rotated sig+loop /
               parse-init + parse-read / render-call forward /
               battery Test 24
  cell 11 (3): wrapper signature / vertical-ignore + forward / 7.5c
  cell 12 (3): wrapper signature / vertical-ignore + forward / 7.7b

RF-9 discipline: this driver + the content modules + the verifier +
the pre-commit audit + the commit message + the S012 fixture builder
are committed in the Phase C commit.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b31_phaseC_content_c6 import (
    C6_P1_OLD, C6_P1_NEW, C6_P2_OLD, C6_P2_NEW,
    C6_P3_OLD, C6_P3_NEW, C6_P4_OLD, C6_P4_NEW,
)
from m009_b31_phaseC_content_c10 import (
    C10_P1_OLD, C10_P1_NEW, C10_P2_OLD, C10_P2_NEW,
    C10_P3_OLD, C10_P3_NEW, C10_P4_OLD, C10_P4_NEW,
    C10_P5A_OLD, C10_P5A_NEW, C10_P5B_OLD, C10_P5B_NEW,
    C10_P6A_OLD, C10_P6A_NEW, C10_P6B_OLD, C10_P6B_NEW,
    C10_P7_OLD, C10_P7_NEW,
)
from m009_b31_phaseC_content_t24 import C10_P8_OLD, C10_P8_NEW
from m009_b31_phaseC_content_c1112 import (
    C11_P1_OLD, C11_P1_NEW, C11_P2_OLD, C11_P2_NEW, C11_P3_OLD,
    C11_P3_NEW, C12_P1_OLD, C12_P1_NEW, C12_P2_OLD, C12_P2_NEW,
    C12_P3_OLD, C12_P3_NEW,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "cf01aef"
MANIFEST = f"{REPO}/scripts/m009_b31_phaseC_patches.json"
TARGET_CELLS = {6, 10, 11, 12}
POST_CELLS = "/home/z/my-project/cells_b31_fix"

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

nb_sha = hashlib.sha256(open(NB, "rb").read()).hexdigest()
assert nb_sha.startswith("c719feb6"), f"notebook sha {nb_sha}"
print(f"PASS  notebook sha256 == B3-tip pin c719feb6... ({nb_sha[:16]}...)")

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


apply(6, "P1: _b31 per-line law helpers (RB31-1/2/4 instrument port)",
      C6_P1_OLD, C6_P1_NEW)
apply(6, "P2: per-page b31_raw_ink build (RB31-2 raw locator, dual-gated)",
      C6_P2_OLD, C6_P2_NEW)
apply(6, "P3: narrow-bubble fix — w<80 raw locator at the orientation "
         "call site (Owner V5 addendum)",
      C6_P3_OLD, C6_P3_NEW)
apply(6, "P4: region-loop conditional line_colors key (RB31-3 law)",
      C6_P4_OLD, C6_P4_NEW)

apply(10, "P1: render_bengali_text line_colors kwarg (RF-15 signature law)",
       C10_P1_OLD, C10_P1_NEW)
apply(10, "P2: per-line materialize + per-line strokes (RB31-4 mapping)",
       C10_P2_OLD, C10_P2_NEW)
apply(10, "P3: rotated branch forwards line_colors",
       C10_P3_OLD, C10_P3_NEW)
apply(10, "P4: horizontal loop per-line fill/stroke (+ runs fallback)",
       C10_P4_OLD, C10_P4_NEW)
apply(10, "P5a: _render_rotated_text line_colors kwarg",
       C10_P5A_OLD, C10_P5A_NEW)
apply(10, "P5b: _render_rotated_text per-line draw loop",
       C10_P5B_OLD, C10_P5B_NEW)
apply(10, "P6a: render_page parse-init — b31_page_line_colors map",
       C10_P6A_OLD, C10_P6A_NEW)
apply(10, "P6b: render_page detections parse — line_colors strict "
          "validate + invalid-WARN",
       C10_P6B_OLD, C10_P6B_NEW)
apply(10, "P7: render call forwards line_colors (always-sent kwarg)",
       C10_P7_OLD, C10_P7_NEW)
apply(10, "P8: battery Test 24 — per-line end-to-end + kill-switch "
          "byte-parity + tiny-text @2000px + narrow V5 + invalid-key "
          "+ base kwarg",
       C10_P8_OLD, C10_P8_NEW)

apply(11, "P1: wrapper signature line_colors kwarg (RF-15)",
       C11_P1_OLD, C11_P1_NEW)
apply(11, "P2: vertical arm ignores line_colors (RB31-5) + forward",
       C11_P2_OLD, C11_P2_NEW)
apply(11, "P3: 7.5c wrapper line_colors self-check",
       C11_P3_OLD, C11_P3_NEW)

apply(12, "P1: wrapper signature line_colors kwarg (RF-15)",
       C12_P1_OLD, C12_P1_NEW)
apply(12, "P2: vertical arm ignores line_colors (RB31-5) + forward",
       C12_P2_OLD, C12_P2_NEW)
apply(12, "P3: 7.7b line_colors full-chain integration check",
       C12_P3_OLD, C12_P3_NEW)

# ── 3. wiring probes on the patched source ─────────
assert SRC[6].count("def _b31_raw_ink_mask(") == 1
assert SRC[6].count("def _b31_line_bands(") == 1
assert SRC[6].count("def _b31_hue_unimodal(") == 1
assert SRC[6].count("def _b31_line_color(") == 1
assert SRC[6].count("def _b31_line_colors_key(") == 1
assert SRC[6].count("_B31_LINE_TAU = 0.15") == 1
assert SRC[6].count("b31_raw_ink = _b31_raw_ink_mask(ctd_raw_mask)") == 1
assert SRC[6].count("if w < 80 and b31_raw_ink is not None:") == 1
assert SRC[6].count('_b2_src = b31_raw_ink') == 1
assert SRC[6].count('regions[-1]["line_colors"] = _b31_lc') == 1
assert SRC[6].count('regions[-1]["ink_color"] = _b3_c') == 1   # B3 intact
assert SRC[6].count("def _b2_mask_orientation(") == 1
assert SRC[6].count("def _b2_page_ink_mask(") == 1
assert SRC[6].count("def _b3_undilated_ink_mask(") == 1
assert SRC[6].count("def detect_page(") == 1
# B3 surfaces intact: the closed-mask region law unchanged
assert SRC[6].count("color_inherit_enable") == 4  # setdefault + b3 gate + b31 build gate + b31 loop gate

assert SRC[10].count("    ink_color=None,\n    line_colors=None,\n):") == 1
assert SRC[10].count("_b31_cols = None") == 3  # init + no-op collapse + except
assert SRC[10].count("line_colors=_b31_cols,") == 1
assert SRC[10].count("b31_page_line_colors = {}") == 1
assert SRC[10].count("b31_page_line_colors.get(region_id)") == 1
assert SRC[10].count("Invalid line_colors ignored") == 2  # parse + Test 24
assert SRC[10].count("Invalid ink_color ignored") == 2    # B3 intact
assert SRC[10].count("# Test 24: B3.1") == 1
assert SRC[10].count("# Test 23: B3") == 1
assert SRC[10].count("def render_page(") == 1
assert SRC[10].count("def _render_rotated_text(") == 1
assert SRC[10].count("def choose_text_color(") == 1       # RF-17 intact
assert SRC[10].count("def _b2_gt_tilted_layout") == 1
assert SRC[10].count("def _b2_render_angle(") == 1
assert SRC[10].count("def _b2_blank_cache_stale(") == 1
assert SRC[10].count("def _b2_renderable_rows_present(") == 1
assert SRC[10].count("quarantine") >= 3                   # B2.1 intact

for c, zeros in ((11, "(0,0,0)"), (12, "(0, 0, 0)")):
    assert SRC[c].count("ink_color=None,\n                            line_colors=None):") == 1
    assert SRC[c].count(
        f"tuple(ink_color) if ink_color is not None else {zeros}") == 1
    assert SRC[c].count("line_colors=line_colors)") == 1
    assert SRC[c].count("def _qc_render_vertical(") == 1
assert SRC[11].count("_QC_FINAL_RENDER_PATCHED") == 2
assert SRC[12].count("_QC_RENDER_PATCHED") == 2
assert SRC[11].count("7.5b) MANGABD-009 B3") == 1
assert SRC[11].count("7.5c) MANGABD-009 B3.1") == 1
assert SRC[12].count("7.7) MANGABD-009 B3") == 1
assert SRC[12].count("7.7b) MANGABD-009 B3.1") == 1
assert SRC[12].count("Cell 12 B3 ink-color chain failed") == 1
assert SRC[12].count("Cell 12 B3.1 line_colors chain failed") == 1
print("PASS  wiring probes (B3.1 surfaces + B1/B2/B3 preserved)")

# ── 4. AST compile all cells (warnings-as-errors) ──
with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        compile(SRC[i], f"cell_{i:02d}.py", "exec")
print("PASS  AST 27/27 (warnings-as-errors)")

# ── 5. write notebook (byte-faithful writer) ────────
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

# ── 6. extracts for verification ────────────────────
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
