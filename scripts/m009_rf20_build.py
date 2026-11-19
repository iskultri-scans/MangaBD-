#!/usr/bin/env python3
r"""MANGABD-009 RF-20 — build driver: containment dedup + ghost wipe.

Branch mangabd-009-rf20 @ 7d0a58e (merged main tip; notebook blob
sha256 42aa6a92...c588 — the RF-19 merge pin).

Owner fast-targeted ruling (live merged-main 7d0a58e, rendered
ONCE, page 07.jpg, 29 regions; region dump root-caused):
  FIX A  containment dedup (cell 10, pre-render): suppress
         region B when centroid(B) inside bbox(A) AND
         area(B) < 0.5*area(A) AND IoU(A,B) > 0.1 — keep A,
         drop B's render row. ZERO suppressions on the six
         committed archives (no legitimate nested bubbles).
  FIX B  ghost (cell 10, pre-render per region): if the inpaint
         mask coverage of the region's remaining original ink is
         below 0.5 (dark/spiky case), expand the mask to the
         region interior so no original ghost remains. White-bg
         archives: no ink → no-op.
  Scope  cells {10} ONLY; battery Test 26; S013_dark_webtoon
         fixture; six archives byte-identical; knob law intact.

Patches (9, all manifest re-derivable, order matters — P1/P5 share
a base anchor, P6B anchors P2's output, P6C anchors P4's output):
  cell 10 (9): P1 dedup helpers + census / P5 ghost helpers /
         P2 pre-render scan + WARN / P6B ghost list init /
         P3 row-level skip / P6 ghost wipe / P4 dedup meta /
         P6C ghost meta / P7 battery Test 26.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_rf20_content_c10 import (  # noqa: E402
    C10_P1_OLD, C10_P1_NEW, C10_P2_OLD, C10_P2_NEW,
    C10_P3_OLD, C10_P3_NEW, C10_P4_OLD, C10_P4_NEW,
    C10_P5_OLD, C10_P5_NEW, C10_P6_OLD, C10_P6_NEW,
    C10_P6B_OLD, C10_P6B_NEW, C10_P6C_OLD, C10_P6C_NEW,
)
from m009_rf20_content_t26 import C10_P7_OLD, C10_P7_NEW  # noqa: E402

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "7d0a58e"
MANIFEST = f"{REPO}/scripts/m009_rf20_patches.json"
TARGET_CELLS = {10}
POST_CELLS = "/home/z/my-project/cells_rf20_fix"

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch",
                             "--show-current"],
                            capture_output=True, text=True
                            ).stdout.strip()
assert cur_branch == "mangabd-009-rf20", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
base_blob = subprocess.run(
    ["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
    capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-009-rf20 + notebook blob == "
      f"{BASE_REF} ({cur_blob[:12]}...)")

nb_sha = hashlib.sha256(open(NB, "rb").read()).hexdigest()
assert nb_sha.startswith("42aa6a92"), f"notebook sha {nb_sha}"
print(f"PASS  notebook sha256 == RF-19-merge pin 42aa6a92... "
      f"({nb_sha[:16]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True
                        ).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked RF-20 files)")
for ln in untracked:
    print(f"        {ln}")

# ── 1. load notebook ───────────────────────────────────────
with open(NB, "rb") as f:
    raw = f.read()
nb = json.loads(raw.decode("utf-8"))

rt = json.dumps(nb, indent=1, ensure_ascii=False) + "\n"
assert rt.encode("utf-8") == raw, "round-trip writer is NOT byte-faithful!"
print("PASS  json writer byte-faithful on pre-edit file "
      "(indent=1 + trailing NL)")

assert len(nb["cells"]) == 27
SRC0 = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}

# ── 2. anchored patches (ORDER MATTERS — see module docstring) ──
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


apply(10, "P1: RF-20 containment-dedup helpers + fire census "
          "(_rf20_pair_law / _rf20_suppressed_regions / "
          "_RF20_DEDUP_FIRES / _RF20_GHOST_FIRES)",
      C10_P1_OLD, C10_P1_NEW)
apply(10, "P5: RF-20 ghost-wipe helpers (_rf20_original_ink_mask / "
          "_rf20_expand_mask_region / _RF20_GHOST_COVERAGE)",
      C10_P5_OLD, C10_P5_NEW)
apply(10, "P2: pre-render containment scan + per-pair WARN "
          "(render_page)",
      C10_P2_OLD, C10_P2_NEW)
apply(10, "P6B: per-page ghost-wipe region list init",
      C10_P6B_OLD, C10_P6B_NEW)
apply(10, "P3: row-level fragment skip (the Bengali-on-Bengali cure)",
      C10_P3_OLD, C10_P3_NEW)
apply(10, "P6: ghost wipe before the primary render call",
      C10_P6_OLD, C10_P6_NEW)
apply(10, "P4: render-meta rf20_dedup disclosure",
      C10_P4_OLD, C10_P4_NEW)
apply(10, "P6C: render-meta rf20_ghost_wipe disclosure",
      C10_P6C_OLD, C10_P6C_NEW)
apply(10, "P7: battery Test 26 — dedup once + census + dark ghost "
          "wipe + white no-op + adjacent law + pair-law units",
      C10_P7_OLD, C10_P7_NEW)

# ── 3. wiring probes on the patched source ─────────
assert SRC[10].count("def _rf20_pair_law(") == 1
assert SRC[10].count("def _rf20_suppressed_regions(") == 1
assert SRC[10].count("def _rf20_original_ink_mask(") == 1
assert SRC[10].count("def _rf20_expand_mask_region(") == 1
assert SRC[10].count("_RF20_AREA_RATIO = 0.5") == 1
assert SRC[10].count("_RF20_MIN_IOU = 0.1") == 1
assert SRC[10].count("_RF20_GHOST_COVERAGE = 0.5") == 1
assert SRC[10].count("_RF20_DEDUP_FIRES = []") == 1
assert SRC[10].count("_RF20_GHOST_FIRES = []") == 1
assert SRC[10].count("region_id in _rf20_suppressed:") == 1
assert SRC[10].count('_RF20_DEDUP_FIRES.append((page_id, '
                     '_rf20_fid))') == 1
assert SRC[10].count("_RF20_GHOST_FIRES.append(") == 1
assert SRC[10].count('meta["rf20_dedup"]') == 1
assert SRC[10].count('meta["rf20_ghost_wipe"]') == 1
assert SRC[10].count("RF-20 whole+fragment dedup") >= 2
assert SRC[10].count("RF-20 ghost wipe") >= 2
assert SRC[10].count("# Test 26: MANGABD-009 RF-20") == 1
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
assert SRC[10].count("_RF19_LAST_LAYOUT.get(\"lines\") == 1") == 1
assert SRC[10].count('meta["rf19_tiny_guard"] = {"regions": '
                     "_rf19_fires}") == 1                  # RF-19 intact
assert SRC[10].count("line_colors=b31_page_line_colors.get("
                     "region_id),") == 1  # P6 keeps the primary kwargs
print("PASS  wiring probes (RF-20 surfaces + "
      "RF-19/B1/B2/B3/B3.1 preserved)")

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
