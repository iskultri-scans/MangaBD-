#!/usr/bin/env python3
r"""MANGABD-008 B1 Phase C — build driver: glyph-coverage fix.

Branch mangabd-008-b1 @ 73ca565. Target cells {4, 10, 11, 12} ONLY
(23 non-target cells asserted byte-identical). Implements the
Owner-approved approach (a): extended per-run fallback +
cmap-coverage routing.

  D-1/D-2  cmap-coverage routing (SHARED_BLOCK in cells 10/11/12)
  D-3      per-run fallback on the horizontal + rotated paths
           (cell 10; gated — pure-Bengali lines keep the exact
           original single-font draw)
  D-4      WARN-never-silent get_font_fb (None return contract)
  D-5      baseline anchor clamp max(0, ·)
  Cell 4   vendored NotoSansJP registration (sha256-pinned,
           RF-7 pattern; no runtime download) + battery test

Patch mechanism: anchored exact-replace, each old-string
unique-asserted; the full (cell, name, old, new) manifest is
written to scripts/m008_b1_phaseC_patches.json so the verifier
re-derives new == old + exactly these patches. JSON writer proven
byte-faithful on the pre-edit file.

RF-9 lesson (applied at Phase C time): this driver + the three
content modules + the verifier + the pre-commit audit are
committed IN the Phase C commit — no uncommitted-instrument gap.
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m008_b1_phaseC_content4 import (
    CELL4_BATTERY_NEW,
    CELL4_BATTERY_OLD,
    CELL4_LOG_NEW,
    CELL4_LOG_OLD,
    CELL4_REGISTRY_NEW,
    CELL4_REGISTRY_OLD,
    CELL4_S85_NEW,
    CELL4_S85_OLD,
    FONT_FALLBACK_SHA256,
)
from m008_b1_phaseC_content10 import (
    CELL10_HELPERS_NEW,
    CELL10_HELPERS_OLD,
    SHARED_BLOCK,
)
from m008_b1_phaseC_content10b import (
    CELL10_GATE_NEW,
    CELL10_GATE_OLD,
    CELL10_ROTCALL_NEW,
    CELL10_ROTCALL_OLD,
    CELL10_ROTLOOP_NEW,
    CELL10_ROTLOOP_OLD,
    CELL10_ROTSIG_NEW,
    CELL10_ROTSIG_OLD,
    CELL10_TESTS_NEW,
    CELL10_TESTS_OLD,
)
from m008_b1_phaseC_content1112 import (
    CELL11_HELPERS_NEW,
    CELL11_HELPERS_OLD,
    CELL11_S2_NEW,
    CELL11_S2_OLD,
    CELL11_VCHECK_NEW,
    CELL11_VCHECK_OLD,
    CELL12_HELPERS_NEW,
    CELL12_HELPERS_OLD,
    CELL12_S2_NEW,
    CELL12_S2_OLD,
    CELL12_VCHECK_NEW,
    CELL12_VCHECK_OLD,
    QC_DRAW_NEW,
    QC_DRAW_OLD,
    QC_MEASURE_NEW,
    QC_MEASURE_OLD,
    VCHECK,
)

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "73ca565"
MANIFEST = f"{REPO}/scripts/m008_b1_phaseC_patches.json"
TARGET_CELLS = {4, 10, 11, 12}

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-008-b1", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-008-b1 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
# the Phase C instrument update (None-contract) is the one expected
# tracked-dirty file at build time — it rides in the Phase C commit
expected_dirty = ["M scripts/m008_b1_kana_repro.py"]
assert tracked_dirty == expected_dirty or not tracked_dirty, \
    f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked"
      f"{'; expected Phase C instrument update present' if tracked_dirty else ''})")
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

# ── 1. anchored patches ─────────────────────────────────────
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


# ---- CELL 4 (vendored registration) ----
apply(4, "section 8.5: vendored JP fallback font (sha-pinned)",
      CELL4_S85_OLD, CELL4_S85_NEW)
apply(4, "MANGABD_ASSETS fonts registry extension",
      CELL4_REGISTRY_OLD, CELL4_REGISTRY_NEW)
apply(4, "battery: JP fallback font registered test",
      CELL4_BATTERY_OLD, CELL4_BATTERY_NEW)
apply(4, "log_event extras: fallback_ok",
      CELL4_LOG_OLD, CELL4_LOG_NEW)

# ---- CELL 10 (D-3 horizontal/rotated fallback + shared routing) ----
apply(10, "SHARED_BLOCK + _draw_runs_horizontal after get_font",
      CELL10_HELPERS_OLD, CELL10_HELPERS_NEW)
apply(10, "render_bengali_text: per-run fallback gate (D-3)",
      CELL10_GATE_OLD, CELL10_GATE_NEW)
apply(10, "_render_rotated_text signature: bold param",
      CELL10_ROTSIG_OLD, CELL10_ROTSIG_NEW)
apply(10, "rotated call site passes bold",
      CELL10_ROTCALL_OLD, CELL10_ROTCALL_NEW)
apply(10, "_render_rotated_text: per-run fallback gate (D-3)",
      CELL10_ROTLOOP_OLD, CELL10_ROTLOOP_NEW)
apply(10, "battery Tests 9-12: glyph-coverage (D-1..D-4)",
      CELL10_TESTS_OLD, CELL10_TESTS_NEW)

# ---- CELL 11 (mirror) ----
apply(11, "S2 download removal -> vendored refresh", CELL11_S2_OLD, CELL11_S2_NEW)
apply(11, "helpers -> SHARED_BLOCK (cmap routing + D-4 WARN)",
      CELL11_HELPERS_OLD, CELL11_HELPERS_NEW)
apply(11, "_measure_line D-4 None-contract", QC_MEASURE_OLD, QC_MEASURE_NEW)
apply(11, "draw loop: D-4 None-contract + D-5 clamp", QC_DRAW_OLD, QC_DRAW_NEW)
apply(11, "S7.5 glyph-coverage self-checks (vertical)",
      CELL11_VCHECK_OLD, CELL11_VCHECK_NEW)

# ---- CELL 12 (older iteration, kept in sync) ----
apply(12, "S2 download removal -> vendored refresh", CELL12_S2_OLD, CELL12_S2_NEW)
apply(12, "helpers -> SHARED_BLOCK (cmap routing + D-4 WARN)",
      CELL12_HELPERS_OLD, CELL12_HELPERS_NEW)
apply(12, "_measure_line D-4 None-contract", QC_MEASURE_OLD, QC_MEASURE_NEW)
apply(12, "draw loop: D-4 None-contract + D-5 clamp", QC_DRAW_OLD, QC_DRAW_NEW)
apply(12, "S7.5 glyph-coverage self-checks (vertical)",
      CELL12_VCHECK_OLD, CELL12_VCHECK_NEW)

# ── 2. scope + static gates ─────────────────────────────────
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

# wiring probes on the built sources
assert SRC[4].count(FONT_FALLBACK_SHA256) == 1
assert SRC[4].count("def _sha256_of_file(") == 1
assert SRC[4].count('"fallback_sha256": FONT_FALLBACK_SHA256') == 1
assert SRC[4].count('"fallback_license": FONT_FALLBACK_LICENSE') == 1
assert SRC[4].count("MANGABD_CONFIG[\"rendering\"][\"font_fallback\"] = str(fallback_font_path)") == 1
assert SRC[4].count("run_test(") == SRC0[4].count("run_test(") + 1  # 1 new call (plain, matching cell-4 battery style)
for i in (10, 11, 12):
    assert SRC[i].count("def _font_cmap_codepoints(") == 1
    assert SRC[i].count("def _main_font_ok(") == 1
    assert SRC[i].count("def get_font_fb(") == 1
    assert SRC[i].count("def _draw_runs_horizontal(") == (1 if i == 10 else 0)
    assert SRC[i].count("_FB_CACHE[key] = None") == 1
    assert SRC[i].count("JP fallback font unavailable") == (3 if i == 10 else 2)
    assert SRC[i].count("glyph missing from both fonts") == 1
    assert SRC[i].count("(0x0980 <= o <= 0x09FF) or (0x0900 <= o <= 0x097F)") == 1
assert SRC[10].count("run_test(") == SRC0[10].count("run_test(") + 8
assert SRC[10].count("if _needs_fb and any(not _main_font_ok(ch) for ch in line):") == 1
assert SRC[10].count("if _needs_fb_rot and any(not _main_font_ok(ch) for ch in line):") == 1
assert SRC[10].count("bold=bold,") == SRC0[10].count("bold=bold,") + 1
for i in (11, 12):
    assert SRC[i].count("urllib.request.urlretrieve") == 0
    assert SRC[i].count("max(0, ly + asc_main - f.getmetrics()[0])") == 1
    assert SRC[i].count("or get_font(size, bold)") == 2
    assert SRC[i].count("def _m8_check(") == 1
    assert SRC[i].count("_m8_check(") == 7  # def + 5 checks (D-5 check has if/else arms)
    assert SRC[i].count("assets/fonts/NotoSansJP[wght].ttf") == 2  # S2 default + get_font_fb WARN
assert SRC[10].count("assets/fonts/NotoSansJP[wght].ttf") == 1  # get_font_fb WARN (shared block)
# mirrors: SHARED_BLOCK + VCHECK byte-identical across their host cells
for i in (10, 11, 12):
    assert SHARED_BLOCK in SRC[i], f"SHARED_BLOCK missing from cell {i}"
    assert SRC[i].count(SHARED_BLOCK) == 1, f"SHARED_BLOCK not unique in cell {i}"
for i in (11, 12):
    assert VCHECK in SRC[i], f"VCHECK missing from cell {i}"
    assert SRC[i].count(VCHECK) == 1
# cells 11/12 keep their own headers + banners (mirror discipline)
assert "# ── 2) Fallback font (MANGABD-008 Phase C: vendored) ──" in SRC[11]
assert "(MANGABD-008 Phase C: vendored) ──" in SRC[12]
print("PASS  wiring probes (registry pin, routing, gates, WARN, clamp, mirrors)")

# ── 3. write notebook (byte-faithful writer) ────────────────
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
print(f"notebook md5: {hashlib.md5(out_raw).hexdigest()}")
print("BUILD OK")
