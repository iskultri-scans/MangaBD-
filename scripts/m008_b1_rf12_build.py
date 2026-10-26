#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-12 — build driver: Test 9/12 cache-pollution-proof
fixtures (clear + registry pin + DIRECT load immediately before the load,
INSIDE the test bodies) + the post-Test-10 pollution clear.

Branch mangabd-008-b1, delta base bb3b1df (RF-11). At BUILD TIME the
branch tip was bb3b1df (no Flash delta commit after it yet — the
precondition below asserts exactly that); the Flash RF-11 DELTA CHECK
report 48efb5c (RF-11 CLOSED, zero required fixes) landed MID-FLIGHT,
is docs-only (its notebook blob == bb3b1df's), and became RF-12's
parent per the RF-11-precedent docs-only-between topology — the build's
blob-based re-derivation base (bb3b1df) is unaffected by it.

Owner live-test @ bb3b1df on Colab: cell-10 battery STILL 10/12 —
  FAIL Test 9  glyph-coverage routing (D-1/D-2)
  FAIL Test 12 tofu detector: JP solid vs main .notdef (D-2)
with "JP fallback font unavailable" in the output. The Owner confirmed
via 3 diagnostic cells that the env is NOT the culprit this time:
  1. font file valid TTF (magic 00010000, 9,589,900 bytes)
  2. ImageFont.truetype(path, 24) succeeds manually
  3. MANGABD_ASSETS registry correct
  4. MANGABD_CONFIG["rendering"]["font_fallback"] correct path
Owner-confirmed root cause: _FB_CACHE pollution — cell 10 re-initializes
_FB_CACHE = {} at module level, Test 10's D-4 degradation sets
_FB_CACHE[(size, bold)] = None, and the tests' loads must not trust any
cache state from before; the clear has to happen IMMEDIATELY BEFORE the
actual font load, inside the test body, with the config re-pinned from
the registry, and the load made DIRECT (ImageFont.truetype) so the
cached-None arm of get_font_fb is bypassed entirely.

FIX (Owner directive — cell 10 ONLY; no other source changes; no amend):
  P1 Test 9 (glyph-coverage routing): inside the else-branch body —
     _FB_CACHE.clear() -> registry re-pin -> DIRECT
     ImageFont.truetype(config, 24) probe -> probe folded into the ok
     chain -> the routing checks unchanged.
  P2 after Test 10's block completes: explicit
     _FB_CACHE.clear()  # Clear pollution from D-4 test
     at module level between Test 10 and Test 11.
  P3 Test 12 (tofu detector): same pattern as Test 9 — clear -> registry
     re-pin -> DIRECT probe at 24 -> fb_solid = (probe is not None and
     _m8_hollow(get_font_fb(48), "H") is False) — get_font_fb(48) then
     loads fresh from the just-cleared cache (cached-None arm bypassed).

All three patches land inside the cell-10 §10 self-test span; §1-§9 is
byte-identical (fixtures-only proof); Tests 1-8, Test 10's own block,
Test 11's own block and the final-status block are byte-untouched; the
other 26 cells are byte-identical to bb3b1df.
"""
import json
import subprocess
import sys
import warnings

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "bb3b1df"          # re-derivation base (RF-11, the branch tip)
MANIFEST = f"{REPO}/scripts/m008_b1_rf12_patches.json"
TARGET_CELLS = {10}

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-008-b1", f"on branch {cur_branch!r}"

head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
assert head.startswith("bb3b1df"), \
    f"HEAD {head[:12]} != bb3b1df (no amend: RF-12 builds directly on RF-11)"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-008-b1 @ bb3b1df + notebook blob == {BASE_REF}'s")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked RF-12 instruments)")
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
    pos = src.index(old)
    # fixtures-only guard: everything lands inside the §10 self-test span
    span_start = src.index("# 10. Self-tests")
    assert pos > span_start, f"{name}: anchor outside the self-test span"
    SRC[cell] = src.replace(old, new)
    PATCHES.append({"cell": cell, "name": name, "old": old, "new": new})
    print(f"PASS  patch applied [cell {cell}] {name}")


# ═════════════════════════════════════════════════════════════
# CELL 10 — §10 self-test fixtures (RF-12)
# ═════════════════════════════════════════════════════════════

# ---- P1: Test 9 — pollution-proof fixture (clear -> pin -> DIRECT probe) ----
apply(10, "T9 fixture: clear+pin+DIRECT probe right before the load", '''        fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
        try:
            MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
            _FB_CACHE.clear()
            ok = (
                _main_font_ok("ক") is True''',
'''        fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
        try:
            # RF-12: clear এখন load-এর ঠিক আগে — Test 10-এর D-4 pollution
            # (cached None) এই load-কে আর ছুঁতে পারবে না। Registry থেকে
            # config pin, তারপর DIRECT ImageFont.truetype — get_font_fb-এর
            # cached-None arm পুরোপুরি বাইপাস।
            _FB_CACHE.clear()
            MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
            _m9_probe = ImageFont.truetype(
                MANGABD_CONFIG["rendering"]["font_fallback"], 24
            )
            ok = (
                _m9_probe is not None
                and _main_font_ok("ক") is True''')

# ---- P2: post-Test-10 pollution clear (between Test 10 and Test 11) ----
apply(10, "post-T10 pollution clear", '''except Exception as exc:
    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])


# Test 11: horizontal mixed-script render — fallback glyphs real (MANGABD-008 D-3)''',
'''except Exception as exc:
    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])

# RF-12: Test 10-এর D-4 degradation _FB_CACHE-তে (size, bold) -> None বসায়;
# battery-র বাকি test-গুলোর আগে সেই pollution সাফ করা হলো।
_FB_CACHE.clear()  # Clear pollution from D-4 test


# Test 11: horizontal mixed-script render — fallback glyphs real (MANGABD-008 D-3)''')

# ---- P3: Test 12 — pollution-proof fixture (same pattern as Test 9) ----
apply(10, "T12 fixture: clear+pin+DIRECT probe right before the load", '''        fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
        try:
            MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
            _FB_CACHE.clear()
            fb_solid = _m8_hollow(get_font_fb(48), "H") is False''',
'''        fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
        try:
            # RF-12: Test 9-এর মতোই — clear load-এর ঠিক আগে, registry থেকে
            # config pin, তারপর DIRECT probe। get_font_fb(48) তখন ফাঁকা
            # cache থেকে fresh load করে — cached-None arm পুরোপুরি বাইপাস।
            _FB_CACHE.clear()
            MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
            _m12_probe = ImageFont.truetype(
                MANGABD_CONFIG["rendering"]["font_fallback"], 24
            )
            fb_solid = (
                _m12_probe is not None
                and _m8_hollow(get_font_fb(48), "H") is False
            )''')

assert len(PATCHES) == 3, f"expected 3 patches, got {len(PATCHES)}"

# ── 2. invariants ────────────────────────────────────────────
drift = [i for i in range(27) if SRC[i] != SRC0[i]]
assert drift == [10], f"scope drift {drift} != [10]"
print("PASS  scope drift exactly {10} (26 cells byte-identical)")

# fixtures-only: everything before the §10 self-test span byte-identical
span_marker = "# 10. Self-tests"
cut_pre = SRC0[10].index(span_marker)
cut_post = SRC[10].index(span_marker)
assert SRC0[10][:cut_pre] == SRC[10][:cut_post], "source (pre-self-test) changed!"
print("PASS  cell-10 §1-§9 byte-identical — fixtures only")


def _block(src, start_marker, end_marker):
    s = src.index(start_marker)
    e = src.index(end_marker, s)
    return src[s:e]


# Tests 1-8 span + the RF-11 shared fixture: byte-identical
blk = _block(SRC0[10], "# Test 1: font load", "# Test 9: glyph-coverage routing")
assert blk == _block(SRC[10], "# Test 1: font load", "# Test 9: glyph-coverage routing"), \
    "Tests 1-8 span changed!"
# Test 10's own block (header .. its except run_test line): byte-identical
blk = _block(SRC0[10], "# Test 10: JP fallback font loads",
             '    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])\n')
assert blk == _block(SRC[10], "# Test 10: JP fallback font loads",
                     '    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])\n'), \
    "Test 10's own block changed!"
# Test 11's own block: byte-identical
blk = _block(SRC0[10], "# Test 11: horizontal mixed-script render", "# Test 12: tofu detector")
assert blk == _block(SRC[10], "# Test 11: horizontal mixed-script render", "# Test 12: tofu detector"), \
    "Test 11's own block changed!"
# final-status block: byte-identical
blk = _block(SRC0[10], "# Final status", "\x00") if "\x00" in SRC0[10] else SRC0[10][SRC0[10].index("# Final status") - len("# ═══════════════════════════════════════════════════════════\n# Final status"):]
blk_new = SRC[10][SRC[10].index("# Final status") - len("# ═══════════════════════════════════════════════════════════\n# Final status"):]
assert blk == blk_new, "final-status block changed!"
# the Test-12 tail after the fb_solid region: the finally + main_hollow +
# run_test lines byte-identical
assert SRC0[10][SRC0[10].index("        finally:\n            MANGABD_CONFIG[\"rendering\"][\"font_fallback\"] = fb_real\n            _FB_CACHE.clear()\n\n        main_hollow"):] == \
       SRC[10][SRC[10].index("        finally:\n            MANGABD_CONFIG[\"rendering\"][\"font_fallback\"] = fb_real\n            _FB_CACHE.clear()\n\n        main_hollow"):], \
    "Test 12 tail changed!"
print("PASS  Tests 1-8 + Test 10 + Test 11 + final-status spans byte-identical")

# fixture pattern checks on the patched battery source
b10 = SRC[10]
batt = b10[b10.index(span_marker):]
base_batt = SRC0[10][SRC0[10].index(span_marker):]

# 1) the two DIRECT probes, each reading the pinned config at size 24
assert batt.count("_m9_probe = ImageFont.truetype(") == 1
assert batt.count("_m12_probe = ImageFont.truetype(") == 1
assert batt.count("MANGABD_CONFIG[\"rendering\"][\"font_fallback\"], 24") == 2
# 2) probe folded into each verdict
assert batt.count("_m9_probe is not None") == 1
assert batt.count("_m12_probe is not None") == 1
# 3) clear -> pin -> probe ordering inside each test body
t9 = batt[batt.index("# Test 9: glyph-coverage routing"):batt.index("# Test 10: JP fallback font loads")]
assert t9.index("_FB_CACHE.clear()") < t9.index("MANGABD_CONFIG[\"rendering\"][\"font_fallback\"] = str(real_jp_path)") \
       < t9.index("_m9_probe = ImageFont.truetype("), "T9 clear/pin/probe order wrong"
t12 = batt[batt.index("# Test 12: tofu detector"):]
assert t12.index("_FB_CACHE.clear()") < t12.index("MANGABD_CONFIG[\"rendering\"][\"font_fallback\"] = str(real_jp_path)") \
       < t12.index("_m12_probe = ImageFont.truetype("), "T12 clear/pin/probe order wrong"
# 4) the post-T10 clear line: exactly once, positioned after Test 10's
#    except-run_test line and before Test 11's header
assert batt.count("_FB_CACHE.clear()  # Clear pollution from D-4 test") == 1
p_clear = batt.index("_FB_CACHE.clear()  # Clear pollution from D-4 test")
p_t10_end = batt.index('    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])')
p_t11 = batt.index("# Test 11: horizontal mixed-script render")
assert p_t10_end < p_clear < p_t11, "post-T10 clear mispositioned"
# 5) battery _FB_CACHE.clear() count: 9 (base) -> 10 (+1, the post-T10 line)
assert base_batt.count("_FB_CACHE.clear()") == 9, \
    f"base battery clear count {base_batt.count('_FB_CACHE.clear()')} != 9"
assert batt.count("_FB_CACHE.clear()") == 10, \
    f"patched battery clear count {batt.count('_FB_CACHE.clear()')} != 10"
# 6) RF-11 skip machinery intact
assert batt.count("def run_test_skip") == 1
assert batt.count("if not _vendored_jp_present:") == 3
assert batt.count("tests_total=len(tests) + tests_skipped") == 1
assert batt.count("tests_skipped=tests_skipped") == 1
assert batt.count("2টি test skipped") or "টি test skipped" in batt
# 7) get_font_fb(48) still the hollow-probe loader (wght-600 semantics kept)
assert batt.count("_m8_hollow(get_font_fb(48), \"H\") is False") == 1
print("PASS  RF-12 fixture pattern source checks (probes/order/post-T10/counts)")

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
    if i not in TARGET_CELLS:
        assert src == SRC0[i], f"non-target cell {i} changed"
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile(src, f"cell_{i:02d}.py", "exec")
print("PASS  notebook written byte-faithfully; scope {10}; AST 27/27 clean")

# ── 4. manifest ──────────────────────────────────────────────
with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)
print(f"PASS  manifest written: {len(PATCHES)} patches -> {MANIFEST.split('/')[-1]}")

print(f"\n-> {NB}")
print(f"-> {MANIFEST} ({len(PATCHES)} patches)")
print("RF-12 BUILD OK — run scripts/m008_b1_rf12_verify.py next")
