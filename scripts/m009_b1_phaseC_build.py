#!/usr/bin/env python3
r"""MANGABD-009 B1 Phase C — build driver: smart bubble fill.

Branch mangabd-009-b1 @ d394947 (main). Target cells {10, 11, 12} —
cell 10 carries the whole B1 engine + renderer + render_page + battery
+ N-1; cells 11/12 carry ONLY the C-1 forward-only fit_result threading
through the V-3 wrappers (disclosed discovery; vertical arm untouched).
24 non-target cells asserted byte-identical (reading-order cells
13/15/23 asserted byte-identical).

Patch mechanism (M008 Phase C precedent): anchored exact-replace, each
old-string unique-asserted; the full (cell, name, old, new) manifest is
written to scripts/m009_b1_phaseC_patches.json so the verifier re-derives
new == old + exactly these patches. JSON writer proven byte-faithful on
the pre-edit file.

RF-9 discipline: this driver + the three content modules + the verifier +
the pre-commit audit are committed IN the Phase C commit.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b1_phaseC_content10 import (
    C10_CFG_NEW, C10_CFG_OLD,
    C10_CFGPRINT_NEW, C10_CFGPRINT_OLD,
    C10_N1_NEW, C10_N1_OLD,
    C10_ENGINE_NEW, C10_ENGINE_OLD,
)
from m009_b1_phaseC_content10b import (
    C10_BATT_NEW, C10_BATT_OLD,
    C10_FBPEN_NEW, C10_FBPEN_OLD,
    C10_FBX_NEW, C10_FBX_OLD,
    C10_LOOP_NEW, C10_LOOP_OLD,
    C10_META_NEW, C10_META_OLD,
    C10_RPCTX_NEW, C10_RPCTX_OLD,
    C10_RPLOOP_NEW, C10_RPLOOP_OLD,
    C10_RUNPOS_NEW, C10_RUNPOS_OLD,
    C10_RUNSIG_NEW, C10_RUNSIG_OLD,
)
from m009_b1_phaseC_content1112 import (
    C11_WRAP_NEW, C11_WRAP_OLD,
    C12_WRAP_NEW, C12_WRAP_OLD,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "d394947"
MANIFEST = f"{REPO}/scripts/m009_b1_phaseC_patches.json"
TARGET_CELLS = {10, 11, 12}

# ── 0. preconditions ────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-009-b1", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-009-b1 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
# the RF-9 Phase C instrument files are the expected untracked content at
# build time — they ride in the Phase C commit; tracked tree must be clean
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked Phase C files)")
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

# ── 1. anchored patches ─────────────────────────────
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


# ---- CELL 10 (B1 engine + renderer + render_page + battery + N-1) ----
apply(10, "section 2: bubble_fill_* config knobs (Rulings 2/3/4)",
      C10_CFG_OLD, C10_CFG_NEW)
apply(10, "section 2: smart-fill config print",
      C10_CFGPRINT_OLD, C10_CFGPRINT_NEW)
apply(10, "N-1: get_font loud load_default arm (M9-A.4)",
      C10_N1_OLD, C10_N1_NEW)
apply(10, "section 6: B1 mask-aware engine (mask/bands/wrap/fit/decision)",
      C10_ENGINE_OLD, C10_ENGINE_NEW)
apply(10, "render_bengali_text: fit_result param + conditional fit",
      C10_RUNSIG_OLD, C10_RUNSIG_NEW)
apply(10, "render_bengali_text: mask-mode positioning",
      C10_RUNPOS_OLD, C10_RUNPOS_NEW)
apply(10, "_draw_runs_horizontal: center_x param (B1 band centering)",
      C10_FBX_OLD, C10_FBX_NEW)
apply(10, "_draw_runs_horizontal: center_x pen_x arm",
      C10_FBPEN_OLD, C10_FBPEN_NEW)
apply(10, "render_bengali_text draw loop: band centering + fb box",
      C10_LOOP_OLD, C10_LOOP_NEW)
apply(10, "render_page: B1 context (gray once per page)",
      C10_RPCTX_OLD, C10_RPCTX_NEW)
apply(10, "render_page loop: decision + fit_result threading",
      C10_RPLOOP_OLD, C10_RPLOOP_NEW)
apply(10, "render_page meta: bubble_fill disclosure (Ruling 4)",
      C10_META_OLD, C10_META_NEW)
apply(10, "battery Tests 13-15: B1 + N-1",
      C10_BATT_OLD, C10_BATT_NEW)

# ---- CELL 11 (C-1: V-3 wrapper forward-only threading) ----
apply(11, "C-1: V-3 wrapper fit_result forward (vertical arm untouched)",
      C11_WRAP_OLD, C11_WRAP_NEW)

# ---- CELL 12 (C-1: V-3 wrapper forward-only threading) ----
apply(12, "C-1: V-3 wrapper fit_result forward (vertical arm untouched)",
      C12_WRAP_OLD, C12_WRAP_NEW)

# ── 2. scope + static gates ─────────────────────────
non_target = [i for i in range(27) if i not in TARGET_CELLS]
for i in non_target:
    assert SRC[i] == SRC0[i], f"cell {i} drifted!"
print(f"PASS  {len(non_target)} non-target cells byte-identical "
      f"(scope exact: {sorted(TARGET_CELLS)})")

for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(SRC[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL  cell {i} warning-as-error: {w}")
print("PASS  AST compile 27/27 (warnings-as-errors)")

for i in sorted(TARGET_CELLS):
    print(f"      cell {i:2d}: {SRC0[i].count(chr(10)) + 1} -> "
          f"{SRC[i].count(chr(10)) + 1} lines")

# ── 3. wiring probes on the built sources ───────────
# config knobs (Rulings 2/3/4) — exact defaults
assert SRC[10].count('setdefault("bubble_fill_enable", True)') == 1
assert SRC[10].count('setdefault("bubble_fill_trigger", 0.60)') == 1
assert SRC[10].count('setdefault("bubble_fill_target", 0.85)') == 1
assert SRC[10].count('setdefault("bubble_fill_margin_ratio", 0.03)') == 1
assert SRC[10].count('setdefault("bubble_fill_region_types",') == 1
# pre-এর choose_stroke_width arm + config setdefault + decision-এর cfg.get
# default — তিনটোই একই অনুমোদিত সেট ["bubble", "thought"]
assert SRC[10].count('["bubble", "thought"]') == SRC0[10].count('["bubble", "thought"]') + 2
assert SRC[10].count('setdefault("bubble_fill_max_rounds", 8)') == 1
# cap untouched (Ruling 2): font_size_max 48 setdefault exactly once, pre == post
assert SRC[10].count('setdefault("font_size_max", 48)') == 1
assert SRC0[10].count('setdefault("font_size_max", 48)') == 1
# engine surface
assert SRC[10].count("def _bubble_interior_mask(") == 1
assert SRC[10].count("def _bubble_band_widths(") == 1
assert SRC[10].count("def _wrap_text_to_bands(") == 1
assert SRC[10].count("def _mask_aware_fit(") == 1
assert SRC[10].count("def bubble_fill_decision(") == 1
assert SRC[10].count('guard"] = "vertical_note"') == 1
assert SRC[10].count("w < 90 and h > 2 * max(1, w) and abs(float(angle)) <= 1.0") == 1
# renderer surface
assert SRC[10].count("    fit_result=None,\n):") == 1
assert SRC[10].count("fit_result=(bf_decision") == 0  # bf_fit variable threading
assert SRC[10].count("fit_result=bf_fit,") == 1
assert SRC[10].count("center_x=None,\n):") == 1
assert SRC[10].count("if center_x is not None:") == 1
assert SRC[10].count("center_x=_b1_c,") == 1
# render_page surface
assert SRC[10].count("bf_gray = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2GRAY)") == 1
assert SRC[10].count('meta["bubble_fill"] = {') == 1
assert SRC[10].count("bubble_fill_decision(") == 6  # def + docstring ref + render_page + 3 battery
assert SRC[10].count("guard\"] = \"trigger\"") == 1
# N-1
assert SRC[10].count('_FONT_DEGRADE_WARNED["main_load_default"] = True') == 1
assert SRC[10].count("Main font load failed (") == 1
assert SRC[10].count("degrading to PIL default") == 1
# battery: +3 tests (6 run_test occurrences: try+except per test)
assert SRC[10].count("run_test(") == SRC0[10].count("run_test(") + 6
assert SRC[10].count("B1 mask fill: synthetic ellipse") == 2
assert SRC[10].count("B1 guards: trigger + kill-switch keep current") == 2
assert SRC[10].count("get_font loud degradation (N-1)") == 2
# kept-current path unchanged: fit_font_size body byte-identical region
assert "def fit_font_size(" in SRC[10]
assert SRC[10].count("def fit_font_size(") == SRC0[10].count("def fit_font_size(")
# split_text_to_lines / split_long_word untouched
assert SRC[10].count("def split_text_to_lines(") == 1
assert SRC[10].count("def split_long_word(") == 1
# M008 surfaces preserved (D-1..D-5 byte-parity of the shared block)
assert SRC[10].count("def _main_font_ok(") == 1
assert SRC[10].count("def get_font_fb(") == 1
assert SRC[10].count("def _draw_runs_horizontal(") == 1
assert SRC[10].count("def _render_rotated_text(") == 1
# C-1 wrappers: forward-only, vertical arm byte-preserved
for i in (11, 12):
    assert SRC[i].count("fit_result=None):") == 1
    assert SRC[i].count("_qc_render_vertical(image_pil, text, x, y, w, h, b,") == 1
    assert SRC[i].count("padding, fit_result)") == 1
    # the V-3 intercept predicate itself untouched in both wrappers
    assert SRC[i].count("w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0") == 1
print("PASS  wiring probes (knobs, engine, renderer, render_page, N-1, battery, C-1)")

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
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derivation: {p['name']} anchor"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
for i in range(27):
    assert re_src[i] == SRC[i], f"re-derivation mismatch cell {i}"
print("PASS  re-derivation equality (new == old + exactly these patches)")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)

print(f"\n-> {NB}")
print(f"-> {MANIFEST} ({len(PATCHES)} patches)")
print(f"notebook sha256: {hashlib.sha256(out_raw).hexdigest()}")
print("BUILD OK")
