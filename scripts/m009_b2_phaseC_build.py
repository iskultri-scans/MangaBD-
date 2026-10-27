#!/usr/bin/env python3
r"""MANGABD-009 B2 Phase C — build driver: orientation inheritance.

Branch mangabd-009-b2 @ 5fe8804 (main). Target cells {6, 10} ONLY
(RB2-7: cells 11/12/7/24 byte-untouched — asserted):
  cell 6  : 9b estimator section (knob + pixel-PCA function, RB2-1..4)
            + region-build wiring (kill-switch gate) + conditional
            detect-meta key — 4 anchored patches
  cell 10 : _b2_render_angle mirror (RB2-7) + fit_w/fit_h trailing
            kwargs through render_bengali_text/_render_rotated_text
            (RB2-5) + render_page quad lookup & fit dims & counter &
            meta + battery Tests 16-18 — 13 anchored patches

Patch mechanism (M008/M009-B1 precedent): anchored exact-replace, each
old-string unique-asserted; the full manifest is written to
scripts/m009_b2_phaseC_patches.json so the verifier re-derives
new == old + exactly these patches.

RF-9 discipline: this driver + the three content modules + the verifier
+ the pre-commit audit are committed IN the Phase C commit.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b2_phaseC_content06 import (
    C06_COUNT_NEW, C06_COUNT_OLD,
    C06_BUILD_NEW, C06_BUILD_OLD,
    C06_META_NEW, C06_META_OLD,
    C06_SECTION_NEW, C06_SECTION_OLD,
)
from m009_b2_phaseC_content10 import (
    C10_HELPER_NEW, C10_HELPER_OLD,
    C10_RUNSIG_NEW, C10_RUNSIG_OLD,
    C10_RUNFIT_NEW, C10_RUNFIT_OLD,
    C10_ROTGATE_NEW, C10_ROTGATE_OLD,
    C10_ROTSIG_NEW, C10_ROTSIG_OLD,
    C10_ROTCANVAS_NEW, C10_ROTCANVAS_OLD,
    C10_RPPAGE_NEW, C10_RPPAGE_OLD,
    C10_RPANGLE_NEW, C10_RPANGLE_OLD,
    C10_RPEST_NEW, C10_RPEST_OLD,
    C10_RPCALL_NEW, C10_RPCALL_OLD,
    C10_RPCOUNT_NEW, C10_RPCOUNT_OLD,
    C10_RPMETA_NEW, C10_RPMETA_OLD,
)
from m009_b2_phaseC_content10b import (
    C10_BATT_NEW, C10_BATT_OLD,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "5fe8804"
MANIFEST = f"{REPO}/scripts/m009_b2_phaseC_patches.json"
TARGET_CELLS = {6, 10}

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
# RF-9: the Phase C instrument files are the expected untracked content
# at build time — they ride in the Phase C commit; tracked tree clean
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


# ---- CELL 6 (B2 estimator + region-build wiring) ----
apply(6, "9b section: b2 knob + pixel-PCA estimator (RB2-1..4)",
      C06_SECTION_OLD, C06_SECTION_NEW)
apply(6, "region build: b2_tilted_count init",
      C06_COUNT_OLD, C06_COUNT_NEW)
apply(6, "region build: kill-switch gate + estimation call (RB2-3)",
      C06_BUILD_OLD, C06_BUILD_NEW)
apply(6, "detect meta: conditional b2 disclosure key",
      C06_META_OLD, C06_META_NEW)

# ---- CELL 10 (mirror + fit dims + render_page + battery) ----
apply(10, "_b2_render_angle: render-side kill-switch mirror (RB2-7)",
      C10_HELPER_OLD, C10_HELPER_NEW)
apply(10, "render_bengali_text: fit_w/fit_h kwargs (RB2-5)",
      C10_RUNSIG_OLD, C10_RUNSIG_NEW)
apply(10, "render_bengali_text: current-fit dims (RB2-5)",
      C10_RUNFIT_OLD, C10_RUNFIT_NEW)
apply(10, "render_bengali_text: thread fit dims into rotated branch",
      C10_ROTGATE_OLD, C10_ROTGATE_NEW)
apply(10, "_render_rotated_text: fit_w/fit_h kwargs (RB2-5)",
      C10_ROTSIG_OLD, C10_ROTSIG_NEW)
apply(10, "_render_rotated_text: canvas dims from quad extents (RB2-5)",
      C10_ROTCANVAS_OLD, C10_ROTCANVAS_NEW)
apply(10, "render_page: detections-artifact quad lookup + B2 counter",
      C10_RPPAGE_OLD, C10_RPPAGE_NEW)
apply(10, "render_page: angle mirror + fit dims from quad (RB2-4/5/7)",
      C10_RPANGLE_OLD, C10_RPANGLE_NEW)
apply(10, "render_page: est_size tracking dims (tilted branch)",
      C10_RPEST_OLD, C10_RPEST_NEW)
apply(10, "render_page: pass fit dims to the render call",
      C10_RPCALL_OLD, C10_RPCALL_NEW)
apply(10, "render_page: tilted counter after render",
      C10_RPCOUNT_OLD, C10_RPCOUNT_NEW)
apply(10, "render_page: conditional B2 meta disclosure",
      C10_RPMETA_OLD, C10_RPMETA_NEW)
apply(10, "battery Tests 16-18: B2 semantics + fit dims + end-to-end",
      C10_BATT_OLD, C10_BATT_NEW)

# ── 2. scope + static gates ─────────────────────────
non_target = [i for i in range(27) if i not in TARGET_CELLS]
for i in non_target:
    assert SRC[i] == SRC0[i], f"cell {i} drifted!"
print(f"PASS  {len(non_target)} non-target cells byte-identical "
      f"(scope exact: {sorted(TARGET_CELLS)})")

# RB2-7 named guarantee: 11/12 (V-3 wrappers), 7 (OCR), 24 (slicer)
for i in (7, 11, 12, 24):
    assert SRC[i] == SRC0[i]
print("PASS  RB2-7 named cells {7, 11, 12, 24} byte-untouched")

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
# cell 6: estimator + knob + build wiring
assert SRC[6].count('setdefault("b2_orientation_enable", True)') == 1
assert SRC[6].count("def _estimate_region_angle(") == 1
assert SRC[6].count("b2_tilted_count = 0") == 1
assert SRC[6].count('MANGABD_CONFIG["detection"].get("b2_orientation_enable", True)') == 1
assert SRC[6].count("if w < 90 and h > 2 * max(1, w):") == 1
assert SRC[6].count("if aniso > 0.70:") == 1
assert SRC[6].count("if a < 5.0 or a >= 85.0:") == 1
assert SRC[6].count("if abs(dev) < 5.0:") == 1
assert SRC[6].count('detect_meta["b2_tilted_regions"]') == 1
assert SRC[6].count("def crop_region_rotated(") == 1
# the pre quad/angle construction preserved inside the patched block
assert SRC[6].count("        angle = 0.0") == 1
assert SRC[6].count("], dtype=np.int32)\n\n        angle = 0.0") == 1
# cell 10: mirror + kwargs + render_page + battery
assert SRC[10].count("def _b2_render_angle(") == 1
assert SRC[10].count('angle = _b2_render_angle(row.get("angle", 0.0))') == 1
assert SRC[10].count("    fit_w=None,\n") == 2
assert SRC[10].count("    fit_h=None,\n") == 2
assert SRC[10].count("fit_w=fit_w,") == 2
assert SRC[10].count("load_json_artifact(page_id, \"detections\", default=[])") == 1
assert SRC[10].count("b2_tilted_rendered = 0") == 1
assert SRC[10].count("b2_tilted_rendered += 1") == 1
assert SRC[10].count('meta["b2_orientation"]') == 1
# rotated machinery itself untouched (RB2-5: PIL expand=True stays) —
# the PRODUCTION rotate block byte-exact (battery fixtures add their own
# expand=True test canvases, so a global count would over-assert)
_rot_block = ('        rotated = text_canvas.rotate(\n'
              '            angle,\n'
              '            expand=True,\n'
              '            resample=PILImage.BICUBIC,\n'
              '        )')
assert SRC[10].count(_rot_block) == 1
assert SRC0[10].count(_rot_block) == 1
assert SRC[10].count("rotated = text_canvas.rotate(") == 1
assert SRC[10].count("center_x = int(x + w // 2)") == 1
# B1 surfaces all intact (no regression from B2)
assert SRC[10].count('setdefault("bubble_fill_enable", True)') == 1
assert SRC[10].count('setdefault("bubble_fill_trigger", 0.60)') == 1
assert SRC[10].count('setdefault("bubble_fill_target", 0.85)') == 1
assert SRC[10].count('setdefault("font_size_max", 48)') == 1
assert SRC[10].count("def _bubble_interior_mask(") == 1
assert SRC[10].count("def bubble_fill_decision(") == 1
assert SRC[10].count('guard"] = "rotated"') == 1
assert SRC[10].count('guard"] = "vertical_note"') == 1
assert SRC[10].count("w < 90 and h > 2 * max(1, w) and abs(float(angle)) <= 1.0") == 1
assert SRC[10].count("fit_result=bf_fit,") == 1
# battery: +3 tests (6 run_test occurrences: try+except per test)
assert SRC[10].count("run_test(") == SRC0[10].count("run_test(") + 6
assert SRC[10].count("B2 estimator: synthetic tilt semantics (RB2-1/2/3/4 + gates)") == 2
assert SRC[10].count("B2 render: quad-extents fit + kill-switch mirror") == 2
assert SRC[10].count("B2 end-to-end: estimator -> render inherits the lean") == 2
# RF-13 hygiene block still present exactly once, after the new tests
assert SRC[10].count("# RF-13 fixture hygiene:") == 1
print("PASS  wiring probes (estimator, knob, mirror, kwargs, render_page, B1 intact, battery)")

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
