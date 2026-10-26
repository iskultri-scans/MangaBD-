#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-10 — build driver: cell-10 test fixture path fix.

Branch mangabd-008-b1 @ b848c75 (NO amend — new commit on top).

Owner live-test @ b848c75 on Colab: cell-10 battery 10/12 —
  ❌ Test 9  glyph-coverage routing (D-1/D-2)
  ❌ Test 12 tofu detector: JP solid glyph vs main .notdef (D-2)
  (Tests 10/11 passed; the Test-10/11 degradation fixture derived
   <drive fonts dir>/MISSING-NotoSansJP.ttf from the ambient
   fb_real = /content/drive/MyDrive/MangaBD_V12/fonts/NotoSansJP.ttf)

Forensic reproduction (scripts/m008_rf10_forensic.py, this sandbox):
the exact live signature (9❌ 12❌ 10✓ 11✓) reproduces when the
ambient fallback path holds LOADABLE-BUT-WRONG bytes (Config F:
Bengali font bytes under the Drive NotoSansJP.ttf name) — the
D-1/D-2 fixtures then verify routing/tofu against a fallback whose
cmap lacks Latin/kana ("neither font" -> MAIN -> Test 9 fail) and
whose "H" renders as a hollow .notdef (Test 12 fail).

FIX (Owner directive — cell-10 self-tests ONLY, fixtures only):
  Test 9/12  pin the fallback config to the REAL vendored font
             (MANGABD_ASSETS["fonts"]["fallback_path"], the Phase C
             registry key — the directive's "jp_fallback" entry)
             with a loud exists-assert; _FB_CACHE cleared around
             the pin so the pinned path actually loads
  Test 10/11 explicit missing path /tmp/MISSING-test-font.ttf
             (intentional degradation; NOT derived from
             Path(fb_real).parent, which on Drive-mounted Colab
             points into the real fonts dir)

No source changes: all 4 patches land inside the cell-10
"# 10. Self-tests" span; §1-§9 asserted byte-identical (verifier
R1b). 26 non-target cells byte-identical to b848c75.

Patch mechanism: anchored exact-replace, each old-string
unique-asserted; the (cell, name, old, new) manifest is written to
scripts/m008_b1_rf10_patches.json so the verifier re-derives
working == base + exactly these patches. RF-9: this driver + the
verifier + the pre-commit audit are committed IN the RF-10 commit.
"""
import json
import subprocess
import warnings

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "b848c75"
MANIFEST = f"{REPO}/scripts/m008_b1_rf10_patches.json"
TARGET_CELLS = {10}

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-008-b1", f"on branch {cur_branch!r}"

head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
assert head.startswith(BASE_REF), \
    f"HEAD {head[:12]} != {BASE_REF} (no amend: RF-10 builds on b848c75)"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-008-b1 @ {BASE_REF} + notebook blob identical")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked RF-10 instruments)")
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

# ── 1. anchored patches (cell 10, Tests 9-12 fixtures ONLY) ─
SRC = dict(SRC0)
PATCHES = []


def apply(cell, name, old, new):
    src = SRC[cell]
    assert isinstance(old, str) and old, f"{name}: empty old anchor"
    cnt = src.count(old)
    assert cnt == 1, f"{name}: anchor occurs {cnt}x in cell {cell} (must be 1)"
    assert cell in TARGET_CELLS, f"{name}: cell {cell} not in scope {TARGET_CELLS}"
    # fixtures-only guard: the anchor must live inside the §10 self-test span
    span_start = src.index("# 10. Self-tests")
    assert src.index(old) > span_start, f"{name}: anchor outside the self-test span"
    SRC[cell] = src.replace(old, new)
    PATCHES.append({"cell": cell, "name": name, "old": old, "new": new})
    print(f"PASS  patch applied [cell {cell}] {name}")


# ---- Test 9: pin the REAL vendored JP font for routing verification ----
apply(10, "Test 9 fixture: real vendored font for D-1/D-2 routing", '''# Test 9: glyph-coverage routing (MANGABD-008 D-1/D-2)
try:
    ok = (
        _main_font_ok("ক") is True
        and _main_font_ok("।") is True      # danda: main font-এ আছে (D-1)
        and _main_font_ok("a") is False     # ASCII: JP fallback-এ (D-2)
        and _main_font_ok('"') is False
        and _main_font_ok("—") is False
        and _main_font_ok("こ") is False     # kana: JP fallback-এ
    )

    run_test("glyph-coverage routing (D-1/D-2)", ok)
except Exception as exc:
    run_test("glyph-coverage routing (D-1/D-2)", False, str(exc)[:160])''',
'''# Test 9: glyph-coverage routing (MANGABD-008 D-1/D-2)
# RF-10: routing যাচাই চলবে আসল vendored JP font-এর বিরুদ্ধে — ambient
# config-এর fallback path-এ ভরসা করা যায় না (Owner live-test @ b848c75:
# Drive-এ wrong bytes থাকলে Test 9/12 ভুল করত)।
try:
    real_jp_path = MANGABD_ASSETS["fonts"]["fallback_path"]
    assert Path(real_jp_path).exists(), f"Vendored font missing: {real_jp_path}"

    fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    try:
        MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
        _FB_CACHE.clear()
        ok = (
            _main_font_ok("ক") is True
            and _main_font_ok("।") is True      # danda: main font-এ আছে (D-1)
            and _main_font_ok("a") is False     # ASCII: JP fallback-এ (D-2)
            and _main_font_ok('"') is False
            and _main_font_ok("—") is False
            and _main_font_ok("こ") is False     # kana: JP fallback-এ
        )
    finally:
        MANGABD_CONFIG["rendering"]["font_fallback"] = fb_real
        _FB_CACHE.clear()

    run_test("glyph-coverage routing (D-1/D-2)", ok)
except Exception as exc:
    run_test("glyph-coverage routing (D-1/D-2)", False, str(exc)[:160])''')

# ---- Test 10: explicit missing path (not derived from fb_real.parent) ----
apply(10, "Test 10 fixture: explicit missing path for D-4", '''    fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    _FB_CACHE.clear()
    fb_font = get_font_fb(24)

    try:
        MANGABD_CONFIG["rendering"]["font_fallback"] = str(
            Path(fb_real).parent / "MISSING-NotoSansJP.ttf")''',
'''    # RF-10: degradation fixture — explicit অনুপস্থিত path। fb_real-এর
    # parent থেকে derive করা বাদ (Drive-mounted Colab-এ ওটা আসল fonts
    # dir-এ পড়ে — Owner live-test-এ ঠিক সেটাই হয়েছিল)।
    missing_path = "/tmp/MISSING-test-font.ttf"
    assert not Path(missing_path).exists()  # intentional degradation

    fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    _FB_CACHE.clear()
    fb_font = get_font_fb(24)

    try:
        MANGABD_CONFIG["rendering"]["font_fallback"] = missing_path''')

# ---- Test 11: same explicit missing path for the A/B degradation arm ----
apply(10, "Test 11 fixture: explicit missing path for the D-3 A/B", '''    fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    try:
        MANGABD_CONFIG["rendering"]["font_fallback"] = str(
            Path(fb_real).parent / "MISSING-NotoSansJP.ttf")
        _FB_CACHE.clear()
        canvas_b = PILImage.new("RGB", (400, 120), (255, 255, 255))''',
'''    missing_path = "/tmp/MISSING-test-font.ttf"
    assert not Path(missing_path).exists()  # intentional degradation

    fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    try:
        MANGABD_CONFIG["rendering"]["font_fallback"] = missing_path
        _FB_CACHE.clear()
        canvas_b = PILImage.new("RGB", (400, 120), (255, 255, 255))''')

# ---- Test 12: pin the REAL vendored JP font for the solid-glyph side ----
apply(10, "Test 12 fixture: real vendored font for the D-2 detector", '''    fb_solid = _m8_hollow(get_font_fb(48), "H") is False
    main_hollow = _m8_hollow(get_font(48, False), "H") is True''',
'''    # RF-10: solid-glyph side অবশ্যই আসল vendored JP font দিয়ে — ambient
    # fallback-এ wrong bytes থাকলে hollow .notdef এসে ভুল verdict দিত।
    real_jp_path = MANGABD_ASSETS["fonts"]["fallback_path"]
    assert Path(real_jp_path).exists(), f"Vendored font missing: {real_jp_path}"

    fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
    try:
        MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
        _FB_CACHE.clear()
        fb_solid = _m8_hollow(get_font_fb(48), "H") is False
    finally:
        MANGABD_CONFIG["rendering"]["font_fallback"] = fb_real
        _FB_CACHE.clear()

    main_hollow = _m8_hollow(get_font(48, False), "H") is True''')

assert len(PATCHES) == 4, f"expected 4 patches, got {len(PATCHES)}"

# ── 2. invariants ───────────────────────────────────────────
drift = [i for i in range(27) if SRC[i] != SRC0[i]]
assert drift == [10], f"scope drift {drift} != [10]"

# fixtures-only: cell-10 §1-§9 (everything before the self-test span)
# stays byte-identical
span_marker = "# 10. Self-tests"
cut_pre = SRC0[10].index(span_marker)
cut_post = SRC[10].index(span_marker)
assert SRC0[10][:cut_pre] == SRC[10][:cut_post], "source (pre-self-test) changed!"
print("PASS  cell-10 source (§1-§9) byte-identical — fixtures only")

# the derived-missing-path pattern is gone from the battery
assert "MISSING-NotoSansJP.ttf" not in SRC[10], "derived missing path survives"
assert SRC[10].count('MANGABD_ASSETS["fonts"]["fallback_path"]') == 2
assert SRC[10].count('/tmp/MISSING-test-font.ttf') == 2
print("PASS  fixture pattern: 2x vendored-path pin + 2x explicit missing path")

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
    old_cell = json.loads(raw.decode("utf-8"))["cells"][i]
    new_cell = nb_check["cells"][i]
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

# reload + re-verify scope + AST
for i in range(27):
    src = "".join(nb_check["cells"][i]["source"])
    assert src == SRC[i], f"reload mismatch cell {i}"
    if i != 10:
        assert src == SRC0[i], f"non-target cell {i} changed"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile(src, f"cell_{i:02d}.py", "exec")
print("PASS  notebook written byte-faithfully; scope {10}; AST 27/27 clean")

# ── 4. manifest ─────────────────────────────────────────────
with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)
print(f"PASS  manifest written: {len(PATCHES)} patches -> {MANIFEST.split('/')[-1]}")

print(f"\n-> {NB}")
print(f"-> {MANIFEST} ({len(PATCHES)} patches)")
print("RF-10 BUILD OK — run scripts/m008_b1_rf10_verify.py next")
