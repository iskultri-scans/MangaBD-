#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-17 — build driver: layout parity on tilted bubbles.

Branch mangabd-009-b2 @ 57ac480 (RF-16 tip) notebook bytes.

Root cause (RF-17, reproduced in scripts/m009_b2_rf17_repro.py post):
  (a) cell-6 enclosed-ink isolation at margin 6 leaves burst-spike
      cores, art-stroke cores and spike-ring junction blobs inside the
      "text" ink -> contaminated PCA -> 5 deg snap -> 0.00 on the
      owner-class page (S010 fixture: 0/7 inherit);
  (b) cell-10 tilted fit dims = quad side lengths (spike-inflated or
      text-ink PCA rect) -> line collapse + ink outside the bubble
      (D1, BU1/BU3 measured 2505/3295 px outside the true interior);
  (c) cell-10 text color = BBOX mean -> dark art/hatch in the box
      picks WHITE on a white bubble interior -> invisible text (D2,
      E3 measured 63 visible px in a 454x361 box);
  (d) fitting into the original text-ink quad under-sizes the render
      (D3: S009 archived tilted renders ~17px multi-touch-line blocks
      vs the original's ~26px airy lines — "অনেক তফাৎ").

Fix (7 hunks, scope {6,10} ONLY — all other cells byte-untouched):
  cell 6  hunk1   _B2_RING_MARGIN 6 -> 16 (swallow <= 32px structures;
          S009 stored angles byte-identical at margins 6..18 — 10/10)
  cell 10 hunk1   _b2_interior_fit(): render-time bubble-interior fit
          box (border flood -> interior cloud; quad (u,v) chord-
          profile ellipse-aware shrink) + interior mean + centroid
  cell 10 hunk2   render_page: interior box overrides quad side
          lengths; quad path stays as the exact fallback
  cell 10 hunk3   render_page: interior-path text color from the
          interior mean (choose_text_color's thresholds mirrored)
  cell 10 hunk4   render call: interior padding + centroid paste
          (x/y shifted so the bbox-center paste lands on the interior
          centroid; render_bengali_text signature untouched — RF-15
          wrapper seam safe)
  cell 10 hunk5   render call: padding kwarg forwarded (None for the
          fallback path — byte-exact old behavior)
  cell 10 hunk6   battery Test 21 — D1+D2 render trap

The patch bytes come from scripts/m009_b2_rf17_content.py
(REGENERATED from the verified working notebook by
scripts/m009_b2_rf17_regen.py — round-trip proven: base + patches ==
working tree).
"""
import ast
import hashlib
import json
import subprocess
import sys

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b2_rf17_content import PATCHES

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "57ac480"
MANIFEST = f"{REPO}/scripts/m009_b2_rf17_patches.json"

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

nb = json.loads(open(NB, encoding="utf-8").read())
cells_src = ["".join(c.get("source", [])) for c in nb["cells"]]
print(f"base notebook: {len(cells_src)} cells, blob {cur_blob[:12]}")

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

# ── 3. write back ───────────────────────────────────────────────────
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

# ── 4. manifest ─────────────────────────────────────────────────────
manifest = [
    {"cell": cell, "hunk": k,
     "old_sha256": hashlib.sha256(old.encode()).hexdigest(),
     "new_sha256": hashlib.sha256(new.encode()).hexdigest()}
    for k, (cell, old, new) in enumerate(PATCHES, 1)
]
with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(manifest, f, ensure_ascii=False, indent=1)
print(f"manifest -> {MANIFEST} ({len(manifest)} hunks)")

print("\nBUILD OK — next: repro fix-arm + battery + verify")
