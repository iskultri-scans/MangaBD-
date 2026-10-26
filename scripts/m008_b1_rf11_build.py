#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-11 — build driver: vendored-font graceful skip +
auto-download self-heal.

Branch mangabd-008-b1 @ b627686 (NO amend — new commit on top; b627686 is
the Flash RF-10 DELTA CHECK report, docs-only, its notebook ==
9b232f0's). Delta base for re-derivation: 9b232f0 (checked on the
NOTEBOOK BLOB so the docs-only commit between is acceptable).

Owner live-test @ 9b232f0 on Colab: cell-10 battery STILL 10/12 —
  FAIL Test 9  glyph-coverage routing (D-1/D-2)
  FAIL Test 12 tofu detector: JP solid vs main .notdef (D-2)
  (Test 10 NOW green — the RF-10 explicit /tmp/MISSING-test-font.ttf
   fixture works; so the D-4 degradation side is FIXED.)
Critical diagnostic: the vendored font FILE (assets/fonts/
NotoSansJP[wght].ttf, 9.6 MB) is NOT present in the Owner's Colab
environment — the registry key exists, but the resolved path points at
a file that does not exist there. RF-10's loud exists-assert fires
exactly as designed: it NAMES the env failure — but the directive now
rules that a missing vendored font is an env-PROVISIONING gap, not a
test failure: skip gracefully + self-heal in cell 4.

FIX (Owner directive — cell-10 test fixtures + cell-4 font loader
ONLY; no other source changes; no amend):
  cell 4  §8.5 gains _ensure_vendored_font() (M6-B1 RF-7 pattern):
          candidates hold NO sha-verified font -> (a) copy from a repo
          checkout (CWD-relative + parents + conventional Colab clone
          paths), (b) repo absent -> download from google Fonts
          (sha-pinned: the cells-11/12 historical URL + jsdelivr
          mirror; both serve the exact vendored sha256); .partial ->
          sha256-verify -> os.replace — wrong/corrupt bytes never land
          on the final path; clear Bengali diagnostics on success AND
          failure; never raises. Called BEFORE the candidate scan, so
          the scan picks the healed file up and registry + config get
          the real path.
  cell 10 Tests 9/12 (D-1/D-2) skip gracefully when the vendored font
          is missing: shared fixture flag _vendored_jp_present (loud
          Bengali diagnostic printed ONCE at the fixture check) +
          run_test_skip() — SKIP marker, NOT appended to the pass/fail
          ledger (no FAIL icon), counted in tests_skipped and reported
          in tests_total (10 passed + 2 skipped = 12 total) + final
          status line + log_event extras. Tests 10/11 (D-4/D-3
          degradation fixtures) byte-untouched — on a genuinely-missing
          ambient they fail LOUD as env diagnostics (RF-10 R3d
          contract, preserved).

Scope: cells {4, 10} ONLY. Cell-10 §1-§9 byte-identical (fixtures
only); cell-4 delta confined to the §8.5 span (loader only); the
other 25 cells byte-identical to 9b232f0.

Patch mechanism: anchored exact-replace, each old-string
unique-asserted; the (cell, name, old, new) manifest is written to
scripts/m008_b1_rf11_patches.json so the verifier re-derives
working == base + exactly these patches. RF-9: this driver + the
verifier + the pre-commit audit are committed IN the RF-11 commit.
"""
import json
import subprocess
import warnings

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "9b232f0"          # re-derivation base (notebook-blob-checked)
MANIFEST = f"{REPO}/scripts/m008_b1_rf11_patches.json"
TARGET_CELLS = {4, 10}

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-008-b1", f"on branch {cur_branch!r}"

head = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                      capture_output=True, text=True).stdout.strip()
assert head.startswith("b627686"), \
    f"HEAD {head[:12]} != b627686 (no amend: RF-11 builds on the Flash delta commit)"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-008-b1 @ b627686 + notebook blob == {BASE_REF}'s")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"unexpected tracked dirt: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked RF-11 instruments)")
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
    if cell == 10:
        # fixtures-only guard: everything lands inside the §10 self-test span
        span_start = src.index("# 10. Self-tests")
        assert pos > span_start, f"{name}: anchor outside the self-test span"
    elif cell == 4:
        # loader-only guard: everything lands inside the §8.5 vendored-font span
        s85 = src.index("# 8.5 Japanese fallback font")
        sentry = src.index(
            'MANGABD_CONFIG["rendering"]["font_fallback"] = str(fallback_font_path)')
        assert s85 < pos < sentry, f"{name}: anchor outside the §8.5 span"
    SRC[cell] = src.replace(old, new)
    PATCHES.append({"cell": cell, "name": name, "old": old, "new": new})
    print(f"PASS  patch applied [cell {cell}] {name}")


# ═════════════════════════════════════════════════════════════
# CELL 4 — §8.5 loader: _ensure_vendored_font() self-heal (RF-7 pattern)
# ═════════════════════════════════════════════════════════════

# ---- C4-P1: §8.5 header comment (runtime self-heal now exists) ----
apply(4, "C4 §8.5 comment: RF-11 self-heal authorized", '''# কানা/ASCII/em-dash glyph-গুলোর জন্য JP fallback font (OFL-1.1)।
# MANGABD-008 Phase C থেকে repo-তে vendored — runtime download নেই (Owner
# decision; cells 11/12-এর পুরনো download logic বাদ)। M6-B1 RF-7 প্যাটার্ন:
# load-এ sha256-verify; না পেলে clear diagnostic — কখনো silent নয়।''',
'''# কানা/ASCII/em-dash glyph-গুলোর জন্য JP fallback font (OFL-1.1)।
# MANGABD-008 Phase C থেকে repo-তে vendored। RF-11 (Owner live-test
# @ 9b232f0): vendored font না পেলে runtime self-heal — আগে repo
# checkout থেকে copy, না হলে google/fonts থেকে sha-pinned download
# (M6-B1 RF-7 প্যাটার্ন)। load-এ sha256-verify; না পেলে clear
# diagnostic — কখনো silent নয়।''')

# ---- C4-P2: the self-heal trio + URL list + the call ----
apply(4, "C4 §8.5 _ensure_vendored_font() self-heal (copy → download)", '''FONT_FALLBACK_CANDIDATES = [
    Path("assets/fonts/NotoSansJP[wght].ttf"),   # repo checkout (CWD-relative)
    DIRS["fonts"] / "NotoSansJP.ttf",            # notebook fonts convention (Drive)
]

fallback_font_path = None''',
'''FONT_FALLBACK_CANDIDATES = [
    Path("assets/fonts/NotoSansJP[wght].ttf"),   # repo checkout (CWD-relative)
    DIRS["fonts"] / "NotoSansJP.ttf",            # notebook fonts convention (Drive)
]

# RF-11 (Owner live-test @ 9b232f0): Owner-এর Colab env-এ vendored font
# candidates-এ পাওয়া যায় না (repo CWD-তে নেই, fonts dir-এও নেই) — তখন
# registry-র fallback_path শুধু একটা নাম। Self-heal: candidates-এ
# sha-verified font না থাকলে আগে repo checkout থেকে copy, না পেলে
# google/fonts থেকে sha-pinned download।
FONT_FALLBACK_URLS = [
    # cell-11/12-এর ঐতিহাসিক URL (Phase C-এ বাদ হয়েছিল) — সেই সঠিক bytes
    "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf",
    # jsdelivr mirror (github block থাকলে)
    "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf",
]


def _find_repo_vendored_font():
    """
    RF-11: repo checkout-এর vendored font খোঁজো — CWD-relative candidate
    (উপরের [0]) ছাড়াও CWD-র প্রথম কয়েকটা parent আর প্রথাগত Colab clone
    locations (/content/MangaBD, /content/mangabd)। পেলে path, না পেলে None।
    """
    _rel = Path("assets/fonts/NotoSansJP[wght].ttf")
    _roots = [Path.cwd()]
    try:
        _roots += list(Path.cwd().parents)[:3]
    except Exception:
        pass
    _roots += [Path("/content/MangaBD"), Path("/content/mangabd")]
    _seen = set()
    for _root in _roots:
        _cand = _root / _rel
        _key = str(_cand)
        if _key in _seen:
            continue
        _seen.add(_key)
        try:
            if _cand.is_file() and _cand.stat().st_size >= 1024:
                return _cand
        except OSError:
            continue
    return None


def _download_vendored_font(target):
    """
    RF-11: google/fonts থেকে sha-pinned download। প্রতিটা URL .partial-এ
    নামে → sha256-verify → তবেই final path-এ replace — wrong/corrupt
    bytes কখনো final path-এ যায় না। Timeout-aware (RF-8 শিক্ষা)।
    Never raises।
    """
    _partial = target.parent / (target.name + ".partial")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
    except Exception as _exc:
        print(f"  ⚠️ fonts dir বানানো গেল না: {str(_exc)[:100]}")
        return False
    for _url in FONT_FALLBACK_URLS:
        print(f"     Trying: {_url[:90]}")
        try:
            try:
                _partial.unlink()
            except OSError:
                pass
            with urllib.request.urlopen(_url, timeout=90) as _resp:
                with open(_partial, "wb") as _fh:
                    while True:
                        _chunk = _resp.read(1 << 20)
                        if not _chunk:
                            break
                        _fh.write(_chunk)
        except Exception as _exc:
            print(f"     ⚠️ download failed: {str(_exc)[:100]}")
            continue
        try:
            if (
                _partial.stat().st_size >= 1024
                and _sha256_of_file(_partial) == FONT_FALLBACK_SHA256
            ):
                _had_old = target.exists()
                os.replace(_partial, target)
                if _had_old:
                    print("  ℹ️ fonts dir-এ পুরনো wrong-bytes file ছিল — sha-pinned bytes দিয়ে replace হলো")
                return True
            print("     ⚠️ sha256 মেলে না — এই URL-এর bytes বাদ")
        except Exception as _exc:
            print(f"     ⚠️ verify/replace failed: {str(_exc)[:100]}")
        try:
            _partial.unlink()
        except OSError:
            pass
    return False


def _ensure_vendored_font():
    """
    RF-11 (Owner live-test @ 9b232f0): vendored JP font না থাকলে
    self-heal — M6-B1 RF-7 প্যাটার্ন। Candidates-এ একটাও sha-verified
    font না থাকলে: (a) repo checkout-এর assets/fonts/NotoSansJP[wght].ttf
    থেকে fonts dir-এ copy, (b) repo না পেলে google/fonts থেকে sha-pinned
    download। Copy/download-এর পরে sha256-verify — wrong bytes কখনো
    গ্রহণ নয়। Never raises; ফলাফল clear Bengali diagnostic-এ।
    Return: সফল/আগেই-ঠিক হলে resolved Path, নাহলে None।
    """
    for _cand in FONT_FALLBACK_CANDIDATES:
        try:
            if (
                _cand.is_file()
                and _cand.stat().st_size >= 1024
                and _sha256_of_file(_cand) == FONT_FALLBACK_SHA256
            ):
                return _cand   # আগেই sha-verified — কিছু করার নেই
        except OSError:
            continue

    _target = FONT_FALLBACK_CANDIDATES[1]   # fonts dir (writable convention)
    print("  ⚠️ Vendored JP font পাওয়া যায়নি — self-heal চালাচ্ছি (RF-11)...")

    # (a) repo checkout থেকে copy
    _repo_src = _find_repo_vendored_font()
    if _repo_src is not None:
        try:
            if _sha256_of_file(_repo_src) == FONT_FALLBACK_SHA256:
                shutil.copy(_repo_src, _target)
                if _sha256_of_file(_target) == FONT_FALLBACK_SHA256:
                    print(f"  ✅ repo থেকে copy + sha256-verified: {_target}")
                    return _target
                raise RuntimeError("copy-র পরে sha mismatch")
            print(f"  ⚠️ repo source-এর sha মেলে না — copy বাদ: {_repo_src}")
        except Exception as _exc:
            print(f"  ⚠️ repo থেকে copy ব্যর্থ: {str(_exc)[:100]}")

    # (b) google/fonts থেকে sha-pinned download
    try:
        if _download_vendored_font(_target):
            print(f"  ✅ download + sha256-verified: {_target}")
            return _target
    except Exception as _exc:
        print(f"  ⚠️ download ধাপ ব্যর্থ: {str(_exc)[:100]}")

    print(
        "  ⚠️ Vendored JP font self-heal ব্যর্থ — ASCII/কানা tofu হবে।\\n"
        "     Fix: নেটওয়ার্ক দেখো, অথবা repo-র assets/fonts/NotoSansJP[wght].ttf\\n"
        f"     কে {_target}-এ ম্যানুয়ালি কপি করো।"
    )
    log_event("JP fallback font self-heal failed — ASCII/kana will tofu", level="WARN")
    return None


# RF-11: candidates scan-এর আগে self-heal — missing হলে এখানেই
# copy/download হয়ে যায়, নিচের loop সেটা তুলে নেয় (registry + config
# তখন আসল path পায়)।
_ensure_vendored_font()

fallback_font_path = None''')

print("PASS  cell-4 patches: 2 applied")

# ═════════════════════════════════════════════════════════════
# CELL 10 — §10 battery: graceful skip for Tests 9/12 (D-1/D-2)
# ═════════════════════════════════════════════════════════════

# ---- C10-P1: run_test_skip helper + tests_skipped counter ----
apply(10, "C10 battery: run_test_skip helper (graceful skip, no FAIL)", '''    tests.append(bool(condition))


# Test 1: font load''',
'''    tests.append(bool(condition))


tests_skipped = 0


def run_test_skip(name, reason=""):
    """
    RF-11 (Owner live-test @ 9b232f0): graceful skip — vendored font না
    থাকা env-provisioning ঘাটতি, test failure নয়। FAIL দেখায় না, pass/fail
    ledger-এও যায় না; tests_skipped counter-এ গোনা হয় আর final status
    তাকে tests_total-এর সাথে রিপোর্ট করে (10 passed + 2 skipped = 12)।
    """
    global tests_skipped
    tests_skipped += 1
    print(f"  ⚪ SKIP {name}")
    if reason:
        print(f"     {reason}")


# Test 1: font load''')

# ---- C10-P2: shared fixture check + Test 9 skip branch ----
apply(10, "C10 Test 9: shared vendored-font fixture + graceful skip", '''# Test 9: glyph-coverage routing (MANGABD-008 D-1/D-2)
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
    run_test("glyph-coverage routing (D-1/D-2)", False, str(exc)[:160])''',
'''# RF-11: Tests 9/12-এর shared fixture — vendored JP font আছে কি না।
# Missing হলে loud Bengali diagnostic + graceful skip (FAIL নয়): env-
# provisioning ঘাটতি test failure নয়, Cell 4-এর RF-11 self-heal
# (repo copy → google/fonts sha-pinned download) চালালেই ঠিক হয়।
_vendored_jp = MANGABD_ASSETS["fonts"]["fallback_path"]
_vendored_jp_present = Path(_vendored_jp).exists()
if not _vendored_jp_present:
    print(f"  ⚠️ Vendored JP font missing: {_vendored_jp}। Tests 9/12 skipped।")
    print("     Fix: Cell 4 আবার চালাও — auto-download হবে, অথবা")
    print("     assets/fonts/NotoSansJP[wght].ttf কে ওই path-এ কপি করো।")


# Test 9: glyph-coverage routing (MANGABD-008 D-1/D-2)
# RF-10: routing যাচাই চলবে আসল vendored JP font-এর বিরুদ্ধে — ambient
# config-এর fallback path-এ ভরসা করা যায় না (Owner live-test @ b848c75:
# Drive-এ wrong bytes থাকলে Test 9/12 ভুল করত)।
# RF-11: vendored font missing হলে graceful skip (FAIL নয়)।
try:
    if not _vendored_jp_present:
        run_test_skip(
            "glyph-coverage routing (D-1/D-2)",
            "vendored JP font missing — Cell 4 self-heal চালাও (RF-11)",
        )
    else:
        real_jp_path = _vendored_jp

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

# ---- C10-P3: Test 12 skip branch ----
apply(10, "C10 Test 12: graceful skip (same shared fixture)", '''    # RF-10: solid-glyph side অবশ্যই আসল vendored JP font দিয়ে — ambient
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

    main_hollow = _m8_hollow(get_font(48, False), "H") is True
    run_test(
        "tofu detector: JP solid glyph vs main .notdef (D-2)",
        fb_solid and main_hollow,
    )''',
'''    # RF-10: solid-glyph side অবশ্যই আসল vendored JP font দিয়ে — ambient
    # fallback-এ wrong bytes থাকলে hollow .notdef এসে ভুল verdict দিত।
    # RF-11: vendored font missing হলে graceful skip (FAIL নয়)।
    if not _vendored_jp_present:
        run_test_skip(
            "tofu detector: JP solid glyph vs main .notdef (D-2)",
            "vendored JP font missing — Cell 4 self-heal চালাও (RF-11)",
        )
    else:
        real_jp_path = _vendored_jp

        fb_real = MANGABD_CONFIG["rendering"].get("font_fallback", "")
        try:
            MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)
            _FB_CACHE.clear()
            fb_solid = _m8_hollow(get_font_fb(48), "H") is False
        finally:
            MANGABD_CONFIG["rendering"]["font_fallback"] = fb_real
            _FB_CACHE.clear()

        main_hollow = _m8_hollow(get_font(48, False), "H") is True
        run_test(
            "tofu detector: JP solid glyph vs main .notdef (D-2)",
            fb_solid and main_hollow,
        )''')

# ---- C10-P4: final status — skip accounting ----
apply(10, "C10 final status: tests_skipped reporting (10+2=12)", '''if all_tests_passed:
    print("  Cell 10 result: SUCCESS")
    print("  Next: Cell 11 — Upload/Input & Pipeline Orchestrator")
else:
    print("  Cell 10 result: NEEDS FIX")
    print("  কিছু self-test fail করেছে। উপরের output দেখুন।")

print("=" * 70)

log_event(
    "Cell 10 completed",
    level="INFO",
    tests_passed=sum(tests),
    tests_total=len(tests),
)''',
'''if all_tests_passed:
    print("  Cell 10 result: SUCCESS")
    if tests_skipped:
        # RF-11: skip ≠ fail — vendored font নেই; Cell 4 self-heal চালালে
        # পরের run-এ test-গুলো আবার চলবে
        print(f"  ⚠️ {tests_skipped}টি test skipped — vendored font নেই (উপরের fix দেখো)")
    print("  Next: Cell 11 — Upload/Input & Pipeline Orchestrator")
else:
    print("  Cell 10 result: NEEDS FIX")
    print("  কিছু self-test fail করেছে। উপরের output দেখুন।")

print("=" * 70)

log_event(
    "Cell 10 completed",
    level="INFO",
    tests_passed=sum(tests),
    tests_total=len(tests) + tests_skipped,
    tests_skipped=tests_skipped,
)''')

assert len(PATCHES) == 6, f"expected 6 patches, got {len(PATCHES)}"
print("PASS  cell-10 patches: 4 applied")

# ── 2. invariants ────────────────────────────────────────────
drift = [i for i in range(27) if SRC[i] != SRC0[i]]
assert drift == [4, 10], f"scope drift {drift} != [4, 10]"

# fixtures-only: cell-10 §1-§9 (everything before the self-test span)
# stays byte-identical
span_marker = "# 10. Self-tests"
cut_pre = SRC0[10].index(span_marker)
cut_post = SRC[10].index(span_marker)
assert SRC0[10][:cut_pre] == SRC[10][:cut_post], "source (pre-self-test) changed!"
print("PASS  cell-10 §1-§9 byte-identical — fixtures only")

# loader-only: cell-4 delta confined to the §8.5 span (between the §8.5
# banner and the config-set line); everything before/after byte-identical
s85_banner = "# 8.5 Japanese fallback font"
cfg_line = 'MANGABD_CONFIG["rendering"]["font_fallback"] = str(fallback_font_path)'
b_pre_start = SRC0[4].rindex("\n# ═", 0, SRC0[4].index(s85_banner))
n_pre_start = SRC[4].rindex("\n# ═", 0, SRC[4].index(s85_banner))
assert SRC0[4][:b_pre_start + 1] == SRC[4][:n_pre_start + 1], "cell-4 pre-§8.5 changed!"
assert SRC0[4][SRC0[4].index(cfg_line):] == SRC[4][SRC[4].index(cfg_line):], \
    "cell-4 post-§8.5 changed!"
print("PASS  cell-4 delta confined to §8.5 (pre/post spans byte-identical)")

# fixture/loader pattern checks on the patched sources
b10 = SRC[10]
b4 = SRC[4]
assert b10.count("def run_test_skip") == 1
assert b10.count("tests_skipped = 0") == 1
assert b10.count("if not _vendored_jp_present:") == 3          # fixture diag + Tests 9/12
assert b10.count("_vendored_jp_present = Path(_vendored_jp).exists()") == 1
assert b10.count("assert Path(real_jp_path).exists()") == 0    # RF-10 assert gone
assert b10.count("assert not Path(missing_path).exists()") == 2  # Tests 10/11 kept
assert b10.count("tests_total=len(tests) + tests_skipped") == 1
assert b10.count("tests_skipped=tests_skipped") == 1
assert b4.count("def _ensure_vendored_font") == 1
assert b4.count("def _find_repo_vendored_font") == 1
assert b4.count("def _download_vendored_font") == 1
assert b4.count("_ensure_vendored_font()\n") == 1  # the single pre-scan call
assert b4.index("FONT_FALLBACK_URLS") < b4.index("def _find_repo_vendored_font")
call_pos = b4.index("_ensure_vendored_font()\n\nfallback_font_path = None")
assert b4.index("def _ensure_vendored_font") < call_pos < b4.index("for _fb_cand in")
assert b4.count("https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf") == 1
assert b4.count("https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf") == 1
print("PASS  fixture + loader pattern source checks")

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
print("PASS  notebook written byte-faithfully; scope {4,10}; AST 27/27 clean")

# ── 4. manifest ──────────────────────────────────────────────
with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)
print(f"PASS  manifest written: {len(PATCHES)} patches -> {MANIFEST.split('/')[-1]}")

print(f"\n-> {NB}")
print(f"-> {MANIFEST} ({len(PATCHES)} patches)")
print("RF-11 BUILD OK — run scripts/m008_b1_rf11_verify.py next")
