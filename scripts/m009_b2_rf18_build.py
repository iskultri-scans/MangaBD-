#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-18 — build driver: original-ink orientation GT.

Branch mangabd-009-b2 @ 0eeca00 (RF-17 tip) notebook bytes.

Owner product ruling (RF-18): readable != professional — exact
ORIENTATION PARITY with the original. Design transfer: stop
estimating from crop pixels; the pipeline's own original text-ink
mask is the orientation ground-truth source.

Fix (27 anchored hunks, scope {6,10} ONLY — all other cells
byte-untouched):

  cell 6  hunk1  _B2_RING_MARGIN 16 -> 6 revert (9b estimator is
          the fallback rung only; S009 stored angles byte-stable
          across margins 6..18 — RF-17 V3 proof)
  cell 6  hunk2  9c section: _b2_page_ink_mask (undilated CTD raw
          mask, or saved mask artifact de-dilated) +
          _b2_mask_orientation (minAreaRect angle + oriented quad +
          row-profile GT lines/spacing + ink centroid)
  cell 6  hunk3  detect_page: b2_ink_mask build (kill-switch gated)
  cell 6  hunk4  detect_page: RF-18 ladder — mask GT first (a
          measured 0.0 is FINAL), 9b estimator fallback, 0 deg
  cell 6  hunk5  detect_page: b2_gt_lines/spacing/cx/cy stored on
          tilted mask-GT rows only (detections.json stays
          byte-stable everywhere else)
  cell 10 hunk1-2   choose_text_color: mask-restricted brightness
          (the D2 white-on-white surface)
  cell 10 hunk3     _b2_gt_tilted_layout: largest font whose wrap
          count == GT lines (closest allowed), line_height = GT
          spacing (clamped to natural metrics), vjust stretch cap
          1.6x, degenerate GT -> None (exact old path)
  cell 10 hunk4-11  render_bengali_text/_render_rotated_text: b2gt
          mode (rotated-only, RF-15 disjoint-condition law), GT
          line_height, canvas growth, paste at the original ink
          centroid
  cell 10 hunk12-20 render_page: b2_page_gt from the detections
          artifact; b2gt fit_result + quad fillPoly color mask;
          the RF-17 _b2_interior_fit path REMOVED (superseded)
  cell 10 hunk21-22 battery Test 21 rewritten: mask-GT -> render
          parity trap (angle <=2 deg, lines +-1, IoU >= 0.6 or
          side parity <=15%, outpx 0, ladder rung contract)

ANCHOR LAW (this session): the RF-18 state survived the session
recycle as the extracted cells (cells_rf18_work, 27 files). This
driver re-derives the notebook from 0eeca00 + the manifest patches
and HARD-asserts the extracted cells == those surviving bytes, so
the committed notebook is byte-anchored to the cells every
pre-restart verification ran against.

The patch bytes come from scripts/m009_b2_rf18_content.py
(REGENERATED from the verified cells by
scripts/m009_b2_rf18_regen.py — round-trip proven: base + patches
== verified cells, 27/27).
"""
import ast
import hashlib
import json
import subprocess
import sys

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b2_rf18_content import PATCHES

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "0eeca00"
MANIFEST = f"{REPO}/scripts/m009_b2_rf18_patches.json"
POST_CELLS = "/home/z/my-project/cells_rf18_work"

# ── 0. preconditions ────────────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-009-b2", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
base_blob = subprocess.run(
    ["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
    capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, (
    f"working blob {cur_blob[:12]} != {BASE_REF} — the notebook must "
    "be at the base state (use git checkout to revert, then rebuild)")
print(f"PASS  branch mangabd-009-b2 + notebook blob == {BASE_REF} "
      f"({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout
tracked_dirty = [ln for ln in status.strip().splitlines()
                 if ln and not ln.startswith("??")]
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print("PASS  tracked tree clean")

nb = json.loads(open(NB, encoding="utf-8").read())
cells_src = ["".join(c.get("source", [])) for c in nb["cells"]]
print(f"base notebook: {len(cells_src)} cells, blob {cur_blob[:12]}")

# the surviving verified bytes (session anchor), when present
import os
surviving = None
if os.path.isdir(POST_CELLS):
    surviving = [
        open(f"{POST_CELLS}/cell_{i:02d}.py", encoding="utf-8").read()
        for i in range(27)]

# ── 1. apply patches ────────────────────────────────────────────────
drift = {}
for k, (cell, old, new) in enumerate(PATCHES, 1):
    src = cells_src[cell]
    assert src.count(old) == 1, (
        f"hunk{k}: old-string count {src.count(old)} != 1 in cell {cell}")
    cells_src[cell] = src.replace(old, new, 1)
    drift[cell] = drift.get(cell, 0) + 1
    print(f"  applied hunk{k} [cell {cell}] ({len(old)}B -> {len(new)}B)")

# ── 2. AST + drift census ───────────────────────────────────────────
for i, src in enumerate(cells_src):
    ast.parse(src)  # raises on broken syntax
diff_cells = sorted(i for i, s in enumerate(cells_src)
                    if s != "".join(nb["cells"][i].get("source", [])))
assert diff_cells == sorted(drift), (
    f"drift census {diff_cells} != patched cells {sorted(drift)}")
assert set(drift) <= {6, 10}, f"scope breach: {drift}"
print(f"AST ok on all {len(cells_src)} cells; drift census: {diff_cells}")

# ── 3. wiring probes on the patched source ─────────────────────────
c6, c10 = cells_src[6], cells_src[10]
assert c6.count("_B2_RING_MARGIN = 6") == 1
assert c6.count("def _b2_page_ink_mask") == 1
assert c6.count("def _b2_mask_orientation") == 1
assert c6.count("_B2_MASK_MIN_PX = 100") == 1
assert c6.count("if not b2_measured:") == 1
assert c6.count('regions[-1]["b2_gt_lines"]') == 1
assert c6.count('if w < 90 and h > 2 * max(1, w):') == 2  # 9b + 9c
assert c6.count('MANGABD_CONFIG["detection"].get('
                '"b2_orientation_enable", True)') == 2  # ink-mask + ladder
assert c6.count('MANGABD_CONFIG["detection"].setdefault('
                '"b2_orientation_enable", True)') == 1  # knob registration
# 9b estimator body byte-untouched (base vs patched, bounded span)
s9 = "".join(nb["cells"][6].get("source", []))
_A = "def _estimate_region_angle"
_B = 'print("  ✅ B2 orientation estimator ready (MANGABD-009 B2, ' \
     'default ON)")\nprint()\n'
assert _A in s9 and _B in s9 and _A in c6 and _B in c6
assert s9[s9.index(_A):s9.index(_B) + len(_B)] == \
    c6[c6.index(_A):c6.index(_B) + len(_B)], \
    "9b estimator body drifted!"
assert c10.count("def _b2_gt_tilted_layout") == 1
assert c10.count('_b2_interior_fit') == 0        # RF-17 helper removed
assert c10.count('mode") == "b2gt"') >= 2
assert c10.count("gt_cx=None,") == 1
assert c10.count("mask=b2_gt_mask") == 1
assert c10.count("Test 21: B2 RF-18") == 1
assert c10.count("def _render_rotated_text") == 1
print("PASS  wiring probes (ladder + GT layout + RF-17 interior-fit "
      "fully removed + 9b byte-untouched)")

# ── 4. write back ───────────────────────────────────────────────────
for i, c in enumerate(nb["cells"]):
    c["source"] = cells_src[i].splitlines(keepends=True)

with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
    f.write("\n")

new_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True,
                          check=True).stdout.strip()
new_sha = hashlib.sha256(open(NB, "rb").read()).hexdigest()
print(f"new notebook blob: {new_blob}")
print(f"new notebook sha256: {new_sha}")

# ── 5. manifest ─────────────────────────────────────────────────────
manifest = [
    {"cell": cell, "hunk": k,
     "old_sha256": hashlib.sha256(old.encode()).hexdigest(),
     "new_sha256": hashlib.sha256(new.encode()).hexdigest()}
    for k, (cell, old, new) in enumerate(PATCHES, 1)
]
with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
print(f"manifest -> {MANIFEST} ({len(manifest)} hunks)")

# ── 6. extracts + SESSION-ANCHOR assertion ─────────────────────────
os.makedirs(POST_CELLS, exist_ok=True)
for i in range(27):
    with open(f"{POST_CELLS}/cell_{i:02d}.py", "w", encoding="utf-8") as f:
        f.write(cells_src[i])
if surviving is not None:
    for i in range(27):
        assert cells_src[i] == surviving[i], (
            f"SESSION-ANCHOR violation: rebuilt cell {i} != the "
            "surviving verified bytes (cells_rf18_work)")
    print("PASS  SESSION-ANCHOR: rebuilt cells == the surviving "
          "verified bytes (27/27) — the notebook is byte-anchored to "
          "the cells the pre-restart verification ran against")
else:
    print("NOTE  no surviving cells found; extracts written fresh")

print("\nBUILD OK — next: S011 build + S009/S010 refresh + verify")
