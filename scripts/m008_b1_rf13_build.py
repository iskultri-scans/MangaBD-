#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-13 — build driver: ROOT-CAUSE fix.

Owner directive (RF-13, zai-web IM): STOP fixture guesses; one bounded
research round. Repro PROVEN (scripts/m008_b1_rf13_repro.py + _dump.py):

  * Owner's exact live signature (T9+T12 FAIL, T10+T11 PASS, single D-4
    ERROR line, after-D-4 /tmp/MISSING cmap WARN, post-run config good +
    _FB_CACHE empty) reproduces in ONE env class only:
    R-G — the MAIN font at font_regular CONTAINS BASIC LATIN
    (a Bengali font that is not Latin-less NotoSansBengali).
  * At Test 9: probe loads; _main_font_ok("ক"/"।") = True (D-1 fine);
    _main_font_ok("a"/'"/"—") = True — expected False → chain dies there.
    get_font_fb(24) = FreeTypeFont; caches clean at the assert moment.
  * Mutation trace: exactly 8 font_fallback writes, all fixture pin /
    finally-restore pairs; the FIRST /tmp/MISSING write is Test 10's D-4
    fixture — AFTER Test 9 already failed. Nobody mutates config before
    Test 9. RF-12's Test-10-pollution theory was chronologically
    impossible (Owner-stated) and the fix is unrelated to the failure.
  * The "JP fallback font unavailable" ERROR is Test 10's DESIGNED D-4
    WARN-proof (warned must be True), emitted through logging/stderr —
    displaced in Colab's interleaved output. The "cmap coverage
    unavailable: /tmp/MISSING-test-font.ttf" WARN after D-4 is Test 11's
    DESIGNED D-3 fixture (range routing under the missing path).

ROOT CAUSE: Tests 9/12 (and cells-11/12 §7.5 check D-2) hardcode the
DEFAULT font set's charset SHAPE ("main must lack ASCII"; "main must
render H hollow"). A Latin-having main font renders tofu-free, yet the
fixtures assert the shape and the gate hard-blocks a healthy pipeline.
The env-provisioning gap itself (wrong/other font at font_regular)
passes SILENTLY because cell 4 §8 downloads only when the file is
missing — no identity check.

FIX (production path + fixtures + gate decoupling; ONE commit):
  cell 4  §8.6 main-font sanity check (load + cmap: ক/। required —
          never raises, §8.5 contract) + registry regular_sane key.
          Latin coverage → loud INFO (shape differs, tofu-free).
  cell 10 Test 9  re-scoped: HARD = render integrity (every sample
          glyph in >=1 font cmap — tofu named on fail; probe kept);
          DIAG = D-2 shape (ASCII/kana present in main) — counted in
          tests_diagnosed, NOT in the pass/fail ledger.
  cell 10 Test 12 re-scoped: HARD = fb solid pixel-probe on BOTH "H"
          and "こ" (garbage-font guard, fontTools-independent) +
          .notdef-hollow calibration on a dynamically chosen char the
          main font lacks ("H"→"こ"→none); "main covers H" = DIAG.
  cell 10 run_test_diag helper + final-status line + log_event extra
          tests_diagnosed; gate (all(tests)) now raises ONLY on hard
          render-integrity failures — decoupled per directive 5.
  cell 10 fixture hygiene: pop the fixture-scoped
          /tmp/MISSING-test-font.ttf coverage-cache entry + fb_load
          warn-gate after the battery (trace-proven finallys kept).
  cells 11/12 §7.5 check D-2 (byte-identical mirrors): re-scoped to
          tofu-semantics (glyph in >=1 font) + INFO note for
          Latin-in-main — same root-cause class in the production path.
"""
import json
import subprocess
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
MANIFEST = REPO / "scripts" / "m008_b1_rf13_patches.json"
HEAD_EXPECT = "c072dc5"  # branch tip at REBUILD time: the Flash RF-12 DELTA
                         # CHECK report (docs-only, its notebook == 5a84994's)

raw = NB.read_bytes()
nb = json.loads(raw.decode("utf-8"))
SRC0 = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}

head = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--short", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                        capture_output=True, text=True).stdout.strip()
assert branch == "mangabd-008-b1", f"branch={branch}"
assert head == HEAD_EXPECT, f"HEAD {head} != {HEAD_EXPECT} (docs-only-between re-parent; no amend chain)"
print(f"PASS  branch {branch} @ {head} (RF-12) — building RF-13 on top")


def lines_of(src):
    return src.split("\n")


def slice_between(src, start_sub, end_sub, extra_end=0):
    ls = lines_of(src)
    si = next(i for i, l in enumerate(ls) if start_sub in l)
    ei = next(i for i, l in enumerate(ls) if i > si and end_sub in l)
    return "\n".join(ls[si:ei + 1 + extra_end])


PATCHES = []


def add(cell, name, old, new):
    assert SRC0[cell].count(old) == 1, \
        f"{name}: anchor count {SRC0[cell].count(old)} != 1"
    PATCHES.append({"cell": cell, "name": name, "old": old, "new": new})


# ── cell 4 P1: §8.6 main-font sanity check ────────────────────
OLD_46 = ('print(f"  🔤 JP fallback: {fallback_font_path} '
          '(sha_ok={fallback_sha_ok})")\n\nprint()\n')
SEC_86 = """# ═══════════════════════════════════════════════════════════
# 8.6 Bengali main font sanity check (MANGABD-008 RF-13)
# ═══════════════════════════════════════════════════════════

print("─" * 70)
print("  8.6 Bengali main font sanity check (RF-13)")
print("─" * 70)

# RF-13 root cause (Owner live-test @ 5a84994): cell-10 Tests 9/12 ফেল
# করেছিল কারণ Drive fonts dir-এর font_regular ফাইলটা basic Latin সহ
# অন্য একটা Bengali font ছিল (Latin-less NotoSansBengali নয়)। §8 download
# শুধু missing হলে নামায় — ওই path-এ ভুল ফাইল চুপচাপ চলে যেত। এখন load +
# cmap sanity দেখে LOUD ডায়াগনস্টিক (never raises — §8.5 contract)।
_main_font_sane = False
try:
    _mfs_path = Path(FONT_REGULAR_PATH)
    if not _mfs_path.exists():
        print(f"  ❌ Bengali main font missing: {_mfs_path}")
        print("     Fix: Cell 4 আবার চালাও — auto-download হবে।")
        log_event("Bengali main font missing at font_regular", level="WARN")
    else:
        try:
            ImageFont.truetype(str(_mfs_path), 28)
        except Exception as exc:
            print(f"  ❌ Bengali main font load failed: {_mfs_path}")
            print(f"     ({str(exc)[:100]}; size={_mfs_path.stat().st_size}B) — ভুল/corrupt ফাইল।")
            print("     Fix: ফাইলটা delete করে Cell 4 আবার চালাও — NotoSansBengali auto-download হবে।")
            log_event("Bengali main font unloadable at font_regular", level="WARN")
        else:
            _mfs_cmap = None
            try:
                from fontTools.ttLib import TTFont
                _mfs_tf = TTFont(str(_mfs_path))
                try:
                    _mfs_cmap = _mfs_tf.getBestCmap()
                finally:
                    _mfs_tf.close()
            except Exception:
                print("  ⚠️ main font-এর cmap পড়া যায়নি (fontTools?) — coverage check skipped")
            if _mfs_cmap is not None:
                _mfs_missing = [ch for ch in ("ক", "।") if ord(ch) not in _mfs_cmap]
                if _mfs_missing:
                    print(f"  ❌ Bengali main font-এ দরকারি glyph নেই {_mfs_missing}: {_mfs_path}")
                    print(f"     এটা সম্ভবত Bengali font-ই নয় (size={_mfs_path.stat().st_size}B)।")
                    print("     Fix: ফাইলটা delete করে Cell 4 আবার চালাও — NotoSansBengali auto-download হবে।")
                    log_event("font_regular lacks Bengali glyphs — not a Bengali font", level="WARN")
                else:
                    _main_font_sane = True
                    if all(ord(ch) in _mfs_cmap for ch in ("a", '"', "H", "—")):
                        print("  ⚠️ font_regular-এ basic Latin আছে — ASCII main font-এ render হবে")
                        print("     (NotoSansBengali default shape থেকে D-2 routing আলাদা; tofu হয় না;")
                        print("     cell-10-এর shape diagnostic-গুলো এই কারণে আলাদা verdict দেখাবে)")
                        log_event("font_regular contains basic Latin — D-2 routing shape differs", level="INFO")
                    else:
                        print("  ✅ Bengali main font sanity OK (Latin-less, NotoSansBengali-এর মতো)")
            else:
                _main_font_sane = True
                print("  ✅ Bengali main font load OK (cmap check skipped)")
except Exception as _mfs_exc:
    print(f"  ⚠️ main font sanity check ব্যর্থ: {str(_mfs_exc)[:120]} (উপেক্ষা)")

print()
"""
NEW_46 = OLD_46 + "\n" + SEC_86
add(4, "c4 §8.6 main-font sanity check", OLD_46, NEW_46)

# ── cell 4 P2: registry regular_sane key ─────────────────────
OLD_47 = '        "regular_ok": regular_font_ok,\n        "bold_ok": bold_font_ok,'
NEW_47 = OLD_47 + '\n        "regular_sane": bool(_main_font_sane),'
add(4, "c4 registry regular_sane", OLD_47, NEW_47)

# ── cell 10 P1: run_test_diag helper ─────────────────────────
OLD_101 = ('    if reason:\n        print(f"     {reason}")\n\n\n'
           '# Test 1: font load')
HELPER = '''    if reason:
        print(f"     {reason}")


tests_diagnosed = 0


def run_test_diag(name, ok, details=""):
    """
    RF-13 (Owner live-test @ 5a84994): font-set shape diagnostic — hard
    gate থেকে আলাদা। Render tofu-মুক্ত কিন্তু D-2 default font-set shape
    না মেলে শুধু এখানে বলা হয়; pass/fail ledger-এ যায় না (pipeline
    hard-block হয় না), skip-এর মতোই আলাদা counter-এ গোনা হয় — কিন্তু
    চুপচাপ কখনোই নয়: loud 🔶 + log_event।
    """
    global tests_diagnosed
    if not ok:
        tests_diagnosed += 1
        print(f"  🔶 DIAG {name}")
        if details:
            print(f"     {details}")


# Test 1: font load'''
add(10, "c10 run_test_diag helper", OLD_101, HELPER)

# ── cell 10 P2: Test 9 re-scope ──────────────────────────────
OLD_92 = slice_between(SRC0[10],
                       "# RF-12: clear এখন load-এর ঠিক আগে",
                       'run_test("glyph-coverage routing (D-1/D-2)", ok)')
NEW_92 = '''            # RF-12: clear load-ের ঠিক আগে; Registry থেকে config pin,
            # তারপর DIRECT ImageFont.truetype — get_font_fb-এর cached-None
            # arm পুরোপুরি বাইপাস।
            _FB_CACHE.clear()
            MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
            _m9_probe = ImageFont.truetype(
                MANGABD_CONFIG["rendering"]["font_fallback"], 24
            )
            # RF-13 root-cause re-scope: HARD = render integrity (tofu),
            # DIAG = D-2 default font-set shape। Owner-এর Drive font_regular
            # basic Latin সহ Bengali font হলে ASCII main-এ render হয়
            # (tofu নয়) — সেটা এখন diagnostic, hard-fail নয়।
            _m9_main_cov = _main_font_cov()
            _m9_fb_cov = _fb_font_cov()
            _m9_samples = ("ক", "।", "a", '"', "—", "こ")
            if _m9_main_cov is not None and _m9_fb_cov is not None:
                _m9_tofu = [
                    f"U+{ord(ch):04X}" for ch in _m9_samples
                    if ord(ch) not in _m9_main_cov and ord(ch) not in _m9_fb_cov
                ]
                _m9_details = ("দুই font-এই glyph নেই: " + ", ".join(_m9_tofu)) \
                    if _m9_tofu else ""
                _m9_latin_in_main = [
                    f"U+{ord(ch):04X}" for ch in ("a", '"', "—", "こ")
                    if ord(ch) in _m9_main_cov
                ]
            else:
                _m9_tofu = None
                _m9_details = ""
                _m9_latin_in_main = None
            ok = _m9_probe is not None and not _m9_tofu
            run_test_diag(
                "glyph-coverage shape: ASCII/kana not in main (D-2 default-set)",
                not _m9_latin_in_main,
                "font_regular-এ এই glyph-গুলো আছে: "
                + (", ".join(_m9_latin_in_main) if _m9_latin_in_main else "")
                + " — main font-এ render হবে (tofu নয়); Cell 4 §8.6 নোট দেখো"
                if _m9_latin_in_main else "",
            )
            if _m9_tofu is None:
                run_test_diag(
                    "glyph-coverage cmap scan (fontTools degraded)",
                    False,
                    "main/fallback cmap পড়া যায়নি — tofu-scan স্পষ্টভাবে যাচাই "
                    "হলো না; Test 12-র pixel probe তবুও tofu ধরে",
                )
        finally:
            MANGABD_CONFIG["rendering"]["font_fallback"] = fb_real
            _FB_CACHE.clear()

        run_test("glyph-coverage routing (D-1/D-2)", ok, _m9_details)'''
add(10, "c10 Test 9 re-scope (tofu hard / shape diag)", OLD_92, NEW_92)

# ── cell 10 P3: Test 12 re-scope ──────────────────────────────
OLD_93 = slice_between(SRC0[10],
                       "# RF-12: Test 9-এর মতোই",
                       "fb_solid and main_hollow,", extra_end=1)
NEW_93 = '''            # RF-12: clear load-ের ঠিক আগে, registry থেকে config pin, তারপর
            # DIRECT probe। get_font_fb(48) তখন ফাঁকা cache থেকে fresh
            # load করে — cached-None arm পুরোপুরি বাইপাস।
            _FB_CACHE.clear()
            MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
            _m12_probe = ImageFont.truetype(
                MANGABD_CONFIG["rendering"]["font_fallback"], 24
            )
            # RF-13: HARD = fb solid pixel-probe (fontTools-নিরপেক্ষ
            # garbage guard) — ASCII + kana দুটোই solid। Probe throw হলে
            # RF-12-এর except-arm FAIL (loud, details সহ)।
            fb_solid = (
                _m12_probe is not None
                and _m8_hollow(get_font_fb(48), "H") is False
                and _m8_hollow(get_font_fb(48), "こ") is False
            )
            # RF-13: main-side = DIAGNOSTIC (font property, সামগ্রিক render
            # integrity নয়)। Hollow box / blank notdef / solid substitute —
            # তিনটাই loud DIAG, hard-fail নয়: main-এর missing-glyph behavior
            # এই detector-এর নিজের heuristic-কে প্রভাবিত করে, pipeline-এর
            # আসল render নয়। Tofu-দায়িত্ব: Test 9-এর tofu-scan + এই fb
            # pixel-probe + Test 1-এর main load।
            _m12_main_cov = _main_font_cov()
            _m12_calib = None
            if _m12_main_cov is not None:
                for _m12_cand in ("H", "こ"):
                    if ord(_m12_cand) not in _m12_main_cov:
                        _m12_calib = _m12_cand
                        break
            if _m12_calib is None:
                run_test_diag(
                    "main .notdef-hollow calibration (D-2 shape)",
                    False,
                    "font_regular সব calibration probe glyph cover করে — এই "
                    "font-এ calibration চলে না (render ঠিক আছে; Test 9-এর "
                    "DIAG দেখো)",
                )
            else:
                _m12_res = _m8_hollow(get_font(48, False), _m12_calib)
                if _m12_res is True:
                    if _m12_calib != "H":
                        run_test_diag(
                            "main font covers basic Latin (D-2 shape)",
                            False,
                            "font_regular-এ 'H' আছে — hollow calibration "
                            f"{_m12_calib!r} দিয়ে হলো; ASCII main-এ render "
                            "হয় (tofu নয়)",
                        )
                elif _m12_res is None:
                    run_test_diag(
                        "main .notdef blank — calibration not exercisable (D-2 shape)",
                        False,
                        "font_regular-এর missing-glyph ফাঁকা (hollow box নয়) — "
                        "glyph-বিহীন দুই-font কেস Test 9-এর tofu-scan ধরে",
                    )
                else:
                    run_test_diag(
                        "main substitutes missing glyphs (D-2 shape)",
                        False,
                        f"font_regular-এ {_m12_calib!r} নিজের glyph দিয়ে বসায় — "
                        "font property, tofu নয়",
                    )
        finally:
            MANGABD_CONFIG["rendering"]["font_fallback"] = fb_real
            _FB_CACHE.clear()

        run_test(
            "tofu detector: JP solid glyph vs main .notdef (D-2)",
            fb_solid,
        )
'''
add(10, "c10 Test 12 re-scope (fb solid H+こ / dynamic calibration)", OLD_93, NEW_93)

# ── cell 10 P4: fixture hygiene tail ──────────────────────────
OLD_104 = ('except Exception as exc:\n    run_test(\n'
           '        "tofu detector: JP solid glyph vs main .notdef (D-2)",\n'
           '        False, str(exc)[:160],\n    )\n')
HYG = OLD_104 + '''
# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।
# তিনটা finally config+_FB_CACHE ঠিকঠাক restore করে (mutation-trace
# proven — 8টা write, সব pin/restore জোড়া); এগুলো শুধু fixture-scoped
# entry, যেন এই cell-এর পরের render pipeline বা পরের run-এ লিক না করে।
_FONT_COVERAGE_CACHE.pop("/tmp/MISSING-test-font.ttf", None)
_FONT_ROUTE_WARNED.pop("fb_load", None)
'''
add(10, "c10 fixture hygiene tail", OLD_104, HYG)

# ── cell 10 P5: final-status diag line ────────────────────────
OLD_105 = ('        print(f"  ⚠️ {tests_skipped}টি test skipped — vendored font নেই (উপরের fix দেখো)")\n'
           '    print("  Next: Cell 11 — Upload/Input & Pipeline Orchestrator")')
NEW_105 = ('        print(f"  ⚠️ {tests_skipped}টি test skipped — vendored font নেই (উপরের fix দেখো)")\n'
           '    if tests_diagnosed:\n'
           '        # RF-13: shape diagnostic ≠ fail — font set আলাদা, render tofu-মুক্ত\n'
           '        print(f"  🔶 {tests_diagnosed}টি font-shape diagnostic — D-2 default shape আলাদা (tofu নয়)")\n'
           '    print("  Next: Cell 11 — Upload/Input & Pipeline Orchestrator")')
add(10, "c10 final-status diag line", OLD_105, NEW_105)

# ── cell 10 P6: log_event extra ───────────────────────────────
OLD_106 = '    tests_skipped=tests_skipped,\n)'
NEW_106 = '    tests_skipped=tests_skipped,\n    tests_diagnosed=tests_diagnosed,\n)'
add(10, "c10 log_event tests_diagnosed", OLD_106, NEW_106)

# ── cells 11/12: §7.5 D-2 check re-scope (identical mirrors) ──
OLD_75 = slice_between(SRC0[11],
                       "# D-2/D-3: kana + ASCII",
                       '_main_font_ok("こ") is False and _main_font_ok(\'"\') is False,',
                       extra_end=1)
NEW_75 = '''# D-2/D-3: RF-13 — kana + ASCII glyph coverage (tofu-semantics)।
# Latin-সহ main font-এ ASCII main-এ render হয় — shape আলাদা, tofu নয়;
# সেটা INFO note। দুই font-এ glyph-ই না থাকলে (আসল tofu) ❌ হয়।
def _m8_cov_has(ch):
    try:
        _m8_mc = _main_font_cov()
        _m8_fc = _fb_font_cov()
    except Exception:
        return True
    if _m8_mc is not None and ord(ch) in _m8_mc:
        return True
    if _m8_fc is not None and ord(ch) in _m8_fc:
        return True
    return _m8_mc is None or _m8_fc is None

_m8_check(
    "kana + ASCII glyph coverage (D-2)",
    _m8_cov_has("こ") and _m8_cov_has('"'),
)
try:
    if _main_font_cov() is not None and ord('"') in _main_font_cov():
        print("  ℹ️ font_regular-এ basic Latin আছে — ASCII main-এ render হয় (D-2 shape আলাদা, tofu নয়)")
except Exception:
    pass'''
old12 = slice_between(SRC0[12],
                      "# D-2/D-3: kana + ASCII",
                      '_main_font_ok("こ") is False and _main_font_ok(\'"\') is False,',
                      extra_end=1)
assert old12 == OLD_75, "cells 11/12 §7.5 anchors differ"
add(11, "c11 §7.5 D-2 tofu-semantics", OLD_75, NEW_75)
add(12, "c12 §7.5 D-2 tofu-semantics (mirror)", old12, NEW_75)

# ── apply ─────────────────────────────────────────────────────
SRC = dict(SRC0)
for p in PATCHES:
    SRC[p["cell"]] = SRC[p["cell"]].replace(p["old"], p["new"])

scope = sorted(i for i in range(27) if SRC[i] != SRC0[i])
assert scope == [4, 10, 11, 12], f"scope drift {scope}"
print(f"PASS  scope exactly {{4,10,11,12}} ({len(PATCHES)} anchored patches)")

# cell-4 confinement: §8.5 span + §9 onward byte-identical; §8.6 between
c4 = SRC[4]
assert slice_between(c4, "# 8.5 Japanese fallback font",
                     'print(f"  🔤 JP fallback:') + "\n" == \
    slice_between(SRC0[4], "# 8.5 Japanese fallback font",
                  'print(f"  🔤 JP fallback:') + "\n", "cell4 §8.5 span changed"
assert slice_between(c4, "# 9. Font + libraqm test", "raqm_ok = False", extra_end=0) == \
    slice_between(SRC0[4], "# 9. Font + libraqm test", "raqm_ok = False", extra_end=0), \
    "cell4 §9 changed"
assert c4.count("def _check_main_font_sanity") == 0  # sanity is inline, no stray def
print("PASS  cell-4 delta confined to §8.6 + registry key")

# cell-10 battery pattern proofs
c10 = SRC[10]
batt = slice_between(c10, "# 10. Self-tests", "Fix errors before moving to Cell 11")
base_batt = slice_between(SRC0[10], "# 10. Self-tests",
                          "Fix errors before moving to Cell 11")
assert batt.count("_FB_CACHE.clear()") == base_batt.count("_FB_CACHE.clear()") == 10, \
    f"clear count {batt.count('_FB_CACHE.clear()')} vs base {base_batt.count('_FB_CACHE.clear()')}"
assert batt.count('MANGABD_CONFIG["rendering"]["font_fallback"], 24') == 2
assert batt.count("def run_test_diag") == 1
assert batt.count("_m8_hollow(get_font_fb(48), \"H\") is False") == 1
assert batt.count('_m8_hollow(get_font_fb(48), "こ") is False') == 1
assert batt.count('if not _vendored_jp_present:') == 3
assert batt.count('assert not Path(missing_path).exists()') == 2
assert batt.count('_FONT_COVERAGE_CACHE.pop("/tmp/MISSING-test-font.ttf", None)') == 1
assert batt.count('_FONT_ROUTE_WARNED.pop("fb_load", None)') == 2, \
    "one is Test 10's L1497 fixture re-arm, one is the RF-13 hygiene tail"
assert "all_tests_passed = all(tests)" in batt
assert "run_test(\"glyph-coverage routing (D-1/D-2)\", ok, _m9_details)" in batt
assert "fb_solid,\n        )" in batt
print("PASS  cell-10 battery pattern checks (RF-12 clear/pin/probe + RF-11 skip + gate intact)")

# cells 11/12: §7.5 identical across mirrors; non-§7.5 unchanged
v11 = slice_between(SRC[11], "# ── 7.5)", "# ── 8) pipeline wrap ──")
v12 = slice_between(SRC[12], "# ── 7.5)", "# ── 8) pipeline wrap ──") \
    if "# ── 8) pipeline wrap ──" in SRC[12] else \
    slice_between(SRC[12], "# ── 7.5)", "# ── 6) UI button")
assert v11.split("\n")[:-1] == v12.split("\n")[:-1], \
    "§7.5 mirrors differ"  # last line excluded: end-marker header is cell-local (§8 vs §6)
assert SRC[11].replace(NEW_75, OLD_75) == SRC0[11], "cell 11 non-§7.5 bytes changed"
assert SRC[12].replace(NEW_75, OLD_75) == SRC0[12], "cell 12 non-§7.5 bytes changed"
print("PASS  §7.5 mirrors byte-identical; cells 11/12 delta confined to §7.5 D-2 check")

# ── write (byte-faithful writer) ─────────────────────────────
for i in range(27):
    nb["cells"][i]["source"] = SRC[i].splitlines(keepends=True)
out_raw = json.dumps(nb, indent=2, ensure_ascii=False).encode("utf-8")
with open(NB, "wb") as f:
    f.write(out_raw)
with open(NB, "rb") as f:
    assert f.read() == out_raw, "post-write byte mismatch"
nb_check = json.loads(out_raw.decode("utf-8"))
old_nb = json.loads(raw.decode("utf-8"))
for i in range(27):
    ok = {k: v for k, v in old_nb["cells"][i].items() if k != "source"}
    nk = {k: v for k, v in nb_check["cells"][i].items() if k != "source"}
    assert ok == nk, f"cell {i} non-source fields changed"
assert {k: v for k, v in old_nb.items() if k != "cells"} == \
       {k: v for k, v in nb_check.items() if k != "cells"}, "top-level changed"
print("PASS  notebook written byte-faithfully; non-source + top-level identical")

# re-derivation proof
re_src = dict(SRC0)
for p in PATCHES:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derive {p['name']}"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
for i in range(27):
    assert re_src[i] == SRC[i], f"re-derivation mismatch cell {i}"
print("PASS  re-derivation equality (old + manifest == new)")

# AST 27/27 warnings-as-errors
for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile("".join(nb_check["cells"][i]["source"]), f"cell_{i:02d}", "exec")
print("PASS  AST 27/27 clean (warnings-as-errors)")

# vendored font untouched
import hashlib
h = hashlib.sha256((REPO / "assets/fonts/NotoSansJP[wght].ttf").read_bytes()).hexdigest()
assert h == "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"
print("PASS  vendored font sha untouched")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)
print(f"\nRF-13 BUILD OK — {len(PATCHES)} patches -> {MANIFEST.name}")
print("NEXT: scripts/m008_b1_rf13_verify.py")
