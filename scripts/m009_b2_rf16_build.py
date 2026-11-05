#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-16 — build driver: text-ink-only tilt estimator.

Branch mangabd-009-b2 @ dc612d5 notebook bytes (7dcc3b0 is the Flash
RF-15 re-verify docs commit on top — "no notebook/source bytes
modified", so the working notebook blob == dc612d5's).

Root cause (RF-16, reproduced in scripts/m009_b2_rf16_repro.py post):
  _estimate_region_angle runs PCA over ALL dark pixels of the region
  crop — bubble ring + background art + text. On the Owner's diagonal
  page the near-upright ring/art mass dilutes a true -15 deg text tilt
  to ~+4.6 deg (sign-flipped toward the ring's axis), the 5 deg snap
  zeroes it, df stores 0.00, the region renders straight. 0/7 on the
  S009-class fixture; Owner saw 1/7 live.

Fix (3 patches, scope {6} ONLY — cells 6/10 untouched per RF-15, all
other cells byte-untouched):
  P1  _B2_RING_MARGIN = 6 constant
  P2  estimator docstring: the RF-16 text-ink-only law + fallback
  P3  the isolation block: light flood-fill from the crop border ->
      "outside"; dilate(outside, margin) swallows the ring stroke +
      AA fringe + border art; enclosed ink = the text ink inside the
      bubble; < 100 px -> keep the previous full-ink mask (exact
      fallback = old behavior on ringless fixtures)

RF-9 discipline: this driver + the content module + the repro harness
+ the verifier + the pre-commit audit + the S009 builder are committed
in the RF-16 commit.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b2_rf16_content import (
    C6_P1_OLD, C6_P1_NEW,
    C6_P2_OLD, C6_P2_NEW,
    C6_P3_OLD, C6_P3_NEW,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "dc612d5"
MANIFEST = f"{REPO}/scripts/m009_b2_rf16_patches.json"
TARGET_CELLS = {6}
POST_CELLS = "/home/z/my-project/cells_rf16_work"

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
print(f"PASS  tracked tree clean ({len(untracked)} untracked RF-16 files)")
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


apply(6, "P1: _B2_RING_MARGIN constant (RF-16)",
      C6_P1_OLD, C6_P1_NEW)
apply(6, "P2: estimator docstring — text-ink-only law + fallback (RF-16)",
      C6_P2_OLD, C6_P2_NEW)
apply(6, "P3: enclosed-ink isolation before PCA (RF-16 fix)",
      C6_P3_OLD, C6_P3_NEW)

# wiring probes on the patched source
assert SRC[6].count("_B2_RING_MARGIN = 6") == 1
assert SRC[6].count("cv2.floodFill(_ff, _ffmask, (0, 0), 2)") == 1
assert SRC[6].count("_enclosed = (ink > 0) & (cv2.dilate(") == 1
assert SRC[6].count("if int(_enclosed.sum()) >= 100:") == 1
assert SRC[6].count("ink = _enclosed.astype(np.uint8) * 255") == 1
# forward-only: everything downstream of the isolation is byte-identical
tail_old = SRC0[6][SRC0[6].index("    ys, xs = np.nonzero(ink)"):]
tail_new = SRC[6][SRC[6].index("    ys, xs = np.nonzero(ink)"):]
assert tail_old == tail_new, "downstream PCA/gates/quad drifted!"
# structural surfaces untouched: V-3 predicate, kill-switch call, gates
assert SRC[6].count("if w < 90 and h > 2 * max(1, w):") == 1
assert SRC[6].count('if MANGABD_CONFIG["detection"].get('
                    '"b2_orientation_enable", True):') == 1
assert SRC[6].count("if a < 5.0 or a >= 85.0:") == 1
assert SRC[6].count("if aniso > 0.70:") == 1
assert SRC[6].count("if abs(dev) < 5.0:") == 1
assert SRC[6].count("if _dist > 10.0:") == 1
assert SRC[6].count("pil_angle = round(-dev, 2)") == 1
assert SRC[6].count("9b. MANGABD-009 B2") == 1  # span markers intact
assert SRC[6].count("10. Visualization") == 1
print("PASS  wiring probes (isolation + fallback + untouched gates)")

# ── 3. AST compile all cells (warnings-as-errors) ──
with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        compile(SRC[i], f"cell_{i:02d}.py", "exec")
print("PASS  AST 27/27 (warnings-as-errors)")

# ── 4. write notebook (byte-faithful writer) ───────
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
for c in sorted(TARGET_CELLS):
    print(f"      cell {c}: {len(SRC0[c])} -> {len(SRC[c])} chars "
          f"(+{len(SRC[c]) - len(SRC0[c])})")
