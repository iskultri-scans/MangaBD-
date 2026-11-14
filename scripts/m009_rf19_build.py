#!/usr/bin/env python3
r"""MANGABD-009 RF-19 — build driver: band-consistency gate + tiny-guard.

Branch mangabd-009-b3 @ 36faa98 (B3.1 Phase D tip = branch tip ==
origin; notebook blob sha256 3055f374...07f).

Owner fast-round ruling (live re-accept finding, id=4: angle=7.97 on
straight text, area 31313px, single tiny line; three causes, two
fixable in code — OCR garbage on multi-color text OUT OF SCOPE,
content via manual paste):
  FIX 1  band-consistency gate (cell 6): bands horizontal (<=2 deg,
         >= 2 crisp bands) while minAreaRect says > 5 deg -> reject
         tilt, store 0.0 (measured horizontal, no quad/GT)
  FIX 2  production tiny-guard (cell 10, render_page): rendered == 1
         AND bbox-fit >= 2 lines AND area >= 2000px -> horizontal
         bbox re-layout (no GT mirror) + WARN
  Scope  cells {6,10} ONLY; battery Test 25; archives byte-identical;
         knob law intact.

Patches (8, all manifest re-derivable):
  cell 6  (2): gate helper / gate call at the tilted verdict
  cell 10 (6): namespace report init / report write / per-page fire
               list / the guard around the primary render call /
               render-meta disclosure / battery Test 25
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_rf19_content_c6 import (
    C6_P1_OLD, C6_P1_NEW, C6_P2_OLD, C6_P2_NEW,
)
from m009_rf19_content_c10 import (
    C10_P1_OLD, C10_P1_NEW, C10_P2_OLD, C10_P2_NEW,
    C10_P3_OLD, C10_P3_NEW, C10_P4_OLD, C10_P4_NEW,
    C10_P5_OLD, C10_P5_NEW,
)
from m009_rf19_content_t25 import C10_P6_OLD, C10_P6_NEW

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "36faa98"
MANIFEST = f"{REPO}/scripts/m009_rf19_patches.json"
TARGET_CELLS = {6, 10}
POST_CELLS = "/home/z/my-project/cells_rf19_fix"

# ── 0. preconditions ────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-009-b3", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
base_blob = subprocess.run(
    ["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
    capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-009-b3 + notebook blob == "
      f"{BASE_REF} ({cur_blob[:12]}...)")

nb_sha = hashlib.sha256(open(NB, "rb").read()).hexdigest()
assert nb_sha.startswith("3055f374"), f"notebook sha {nb_sha}"
print(f"PASS  notebook sha256 == B3.1-tip pin 3055f374... "
      f"({nb_sha[:16]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True
                        ).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked RF-19 files)")
for ln in untracked:
    print(f"        {ln}")

# ── 1. load notebook ───────────────────────────────
with open(NB, "rb") as f:
    raw = f.read()
nb = json.loads(raw.decode("utf-8"))

rt = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
assert rt.encode("utf-8") == raw, "round-trip writer is NOT byte-faithful!"
print("PASS  json writer byte-faithful on pre-edit file "
      "(indent=1 + trailing NL)")

assert len(nb["cells"]) == 27
SRC0 = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}

# ── 2. anchored patches ────────────────────────────
SRC = dict(SRC0)
PATCHES = []


def apply(cell, name, old, new):
    src = SRC[cell]
    assert isinstance(old, str) and old, f"{name}: empty old anchor"
    cnt = src.count(old)
    assert cnt == 1, f"{name}: anchor occurs {cnt}x in cell {cell}"
    assert cell in TARGET_CELLS, f"{name}: cell {cell} not in scope"
    SRC[cell] = src.replace(old, new)
    PATCHES.append({"cell": cell, "name": name, "old": old, "new": new})
    print(f"PASS  patch applied [cell {cell}] {name}")


apply(6, "P1: RF-19 band-consistency gate helper "
         "(_rf19_band_tilt_max + _RF19_BAND_TILT_MAX)",
      C6_P1_OLD, C6_P1_NEW)
apply(6, "P2: gate call at the tilted verdict (bands horizontal "
         "→ reject, store 0.0)",
      C6_P2_OLD, C6_P2_NEW)

apply(10, "P1: namespace layout report + guard census init",
       C10_P1_OLD, C10_P1_NEW)
apply(10, "P2: layout report write after resolution",
       C10_P2_OLD, C10_P2_NEW)
apply(10, "P3: render_page per-page fire list",
       C10_P3_OLD, C10_P3_NEW)
apply(10, "P4: production tiny-guard around the primary render call",
       C10_P4_OLD, C10_P4_NEW)
apply(10, "P5: render-meta rf19_tiny_guard disclosure",
       C10_P5_OLD, C10_P5_NEW)
apply(10, "P6: battery Test 25 — false-tilt reject + genuine-tilt "
          "keep + guard fires + healthy silent + census",
       C10_P6_OLD, C10_P6_NEW)

# ── 3. wiring probes on the patched source ─────────
assert SRC[6].count("def _rf19_band_tilt_max(") == 1
assert SRC[6].count("_RF19_BAND_TILT_MAX = 2.0") == 1
assert SRC[6].count("return 0.0, None, None, True") == 4
#   ^ V-3 + snap + dev-snap + THE GATE (base has 3)
assert SRC[6].count("def _b2_mask_orientation(") == 1
assert SRC[6].count("def _b31_line_colors_key(") == 1
assert SRC[6].count("def _b31_raw_ink_mask(") == 1
assert SRC[6].count("def _b3_undilated_ink_mask(") == 1
assert SRC[6].count("if w < 80 and b31_raw_ink is not None:") == 1
assert SRC[6].count('regions[-1]["line_colors"] = _b31_lc') == 1
assert SRC[6].count('regions[-1]["ink_color"] = _b3_c') == 1   # B3 intact
assert SRC[6].count("color_inherit_enable") == 4  # B3.1 knob law intact

assert SRC[10].count("_RF19_LAST_LAYOUT = {\"lines\": None}") == 1
assert SRC[10].count("_RF19_GUARD_FIRES = []") == 1
assert SRC[10].count('_RF19_LAST_LAYOUT["lines"] = int(len(lines))') == 1
assert SRC[10].count('_RF19_LAST_LAYOUT["lines"] = None') == 2
assert SRC[10].count("_RF19_LAST_LAYOUT.get(\"lines\") == 1") == 1
assert SRC[10].count("_rf19_snap = canvas_pil.copy() "
                     "if _rf19_area_ok else None") == 1
assert SRC[10].count("canvas_pil = _rf19_snap") == 1
assert SRC[10].count('meta["rf19_tiny_guard"] = {"regions": '
                     "_rf19_fires}") == 1
assert SRC[10].count("RF-19 tiny-guard re-layout") == 1
assert SRC[10].count("# Test 25: MANGABD-009 RF-19") == 1
assert SRC[10].count("# Test 24: B3.1") == 1
assert SRC[10].count("# Test 23: B3") == 1
assert SRC[10].count("def render_page(") == 1
assert SRC[10].count("def render_bengali_text(") == 1
assert SRC[10].count("def _render_rotated_text(") == 1
assert SRC[10].count("def _b2_gt_tilted_layout") == 1
assert SRC[10].count("def bubble_fill_decision(") == 1
assert SRC[10].count("def fit_font_size(") == 1
assert SRC[10].count("quarantine") >= 3                   # B2.1 intact
assert SRC[10].count("Invalid line_colors ignored") == 2  # B3.1 intact
assert SRC[10].count("Invalid ink_color ignored") == 2    # B3 intact
assert SRC[10].count("line_colors=b31_page_line_colors.get("
                     "region_id),") == 1  # P4 keeps the primary kwargs
print("PASS  wiring probes (RF-19 surfaces + B1/B2/B3/B3.1 preserved)")

# ── 4. AST compile all cells (warnings-as-errors) ──
with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        compile(SRC[i], f"cell_{i:02d}.py", "exec")
print("PASS  AST 27/27 (warnings-as-errors)")

# ── 5. write notebook (byte-faithful writer) ────────
for i in range(27):
    nb["cells"][i]["source"] = SRC[i].splitlines(keepends=True)

out_raw = (json.dumps(nb, indent=1, ensure_ascii=False)
           + "\n").encode("utf-8")
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
    assert ({k: v for k, v in old_cell.items() if k != "source"}
            == {k: v for k, v in new_cell.items() if k != "source"}), i
top_old = {k: v for k, v in json.loads(raw.decode("utf-8")).items()
           if k != "cells"}
top_new = {k: v for k, v in nb_check.items() if k != "cells"}
assert top_old == top_new, "top-level fields changed"
print("PASS  non-source + top-level fields identical")

# re-derivation proof (both directions)
re_src = dict(SRC0)
for p in PATCHES:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derive {p['name']}"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
for i in range(27):
    assert re_src[i] == SRC[i], f"re-derivation mismatch cell {i}"
rev_src = dict(SRC)
for p in reversed(PATCHES):
    assert rev_src[p["cell"]].count(p["new"]) == 1, f"reverse {p['name']}"
    rev_src[p["cell"]] = rev_src[p["cell"]].replace(p["new"], p["old"])
for i in range(27):
    assert rev_src[i] == SRC0[i], f"reverse mismatch cell {i}"
print("PASS  re-derivation equality BOTH directions "
      "(work == base + exactly these patches; base == work - patches)")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)

# ── 6. extracts for verification ────────────────────
import os
os.makedirs(POST_CELLS, exist_ok=True)
for i in range(27):
    with open(f"{POST_CELLS}/cell_{i:02d}.py", "w",
              encoding="utf-8") as f:
        f.write(SRC[i])

new_sha = hashlib.sha256(open(NB, "rb").read()).hexdigest()
print(f"PASS  build complete: notebook sha256 {new_sha}")
print(f"      manifest -> {MANIFEST}")
print(f"      post cells -> {POST_CELLS}")
for c in sorted(TARGET_CELLS):
    print(f"      cell {c}: {len(SRC0[c])} -> {len(SRC[c])} chars "
          f"(+{len(SRC[c]) - len(SRC0[c])})")
