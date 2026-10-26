#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-12 — verification suite (committed instrument).

Branch mangabd-008-b1 @ 48efb5c (the Flash RF-11 DELTA CHECK report —
docs-only, its notebook == bb3b1df's; it landed MID-FLIGHT, after the
RF-12 build had started on the then-tip bb3b1df). Delta base for
re-derivation: bb3b1df, checked on the WORKING notebook blob (the build
re-derives it from the 3-patch manifest; the docs-only Flash commit
between is acceptable — the RF-11-precedent topology).

Owner live-test @ bb3b1df: cell-10 battery STILL 10/12 (Test 9 + Test
12 failing with "JP fallback font unavailable" in the output) while the
Owner's 3 diagnostic cells prove the env is healthy: valid TTF at the
registry path (magic 00010000, 9,589,900 bytes), ImageFont.truetype
succeeds manually, registry + config both correct. Owner-confirmed root
cause: _FB_CACHE pollution — Test 10's D-4 degradation caches
(size, bold) -> None and the tests' font loads must not trust any cache
state from before the load moment. RF-12 = the directive's
pollution-proof fixtures: clear + registry re-pin + DIRECT
ImageFont.truetype immediately before the load INSIDE the Test 9/12
bodies, plus an explicit _FB_CACHE.clear() right after Test 10's block.

Layers:
  V1  static: branch/HEAD preconditions (HEAD == bb3b1df, no amend);
      scope {10} exact (26 cells byte-identical); cell-10 §1-§9
      byte-identical (fixtures only); Tests 1-8 + Test 10's own block +
      Test 11's own block + final-status block byte-identical; AST 27/27
      warnings-as-errors; writer byte-faithful; non-source fields;
      re-derivation from the 3-patch manifest; vendored font bytes
      untouched; RF-12 pattern checks (probes, clear->pin->probe order,
      post-T10 clear position, battery clear count 9->10); RF-11 skip
      machinery intact
  V2  cell-10 battery matrix (real exec):
      A  happy path (registry + ambient = real JP): 12/12, 0 skipped
      B  Owner-key cache pollution immunity: _FB_CACHE pre-seeded with
         {(24, False): None} (the exact key Test 10's D-4 degradation
         caches) BEFORE the battery -> POST-fix still 12/12 — the loads
         no longer trust pre-existing cache state
      C  post-T10 pollution + the P2 line, segmented exec: battery
         through Test 10's block -> INJECT {(24, False): None,
         (48, False): None} -> exec the RF-12 post-T10 clear line ->
         cache provably empty -> Test 11 onward -> combined 12/12
      D  RF-11 Owner-env class regression (registry = missing relative
         vendored path, CWD outside repo; ambient = wrong-bytes
         Drive-style): Tests 9/12 SKIP, 10/11 pass, 10 passed + 2
         skipped = 12, SUCCESS, zero FAIL — the RF-11 contract preserved
      E  both-missing regression: 9/12 skip + 10/11 fail LOUD (the
         RF-10 R3d contract, preserved), NEEDS FIX
      F  vendored-present-but-GARBAGE (exists() passes, truetype
         throws): POST-fix Tests 9/12 fail LOUD with the exception
         named in the FAIL details (probe throws before any routing) —
         never silent; BASE (bb3b1df) observed under the same scenario
         for the honest pre/post comparison
  V3  cells-11/12 §7.5 glyph-coverage self-checks 5/5 in both cells
      (unchanged bytes, re-proven) + §7.5 byte-identical across mirrors
      + cells 11/12 byte-identical to bb3b1df
  V4  m002_sim_v2 = 0 abort sites

Run with system python3 (numpy/pillow/cv2/pandas/fontTools).
"""
import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "bb3b1df"
HEAD_REF = "48efb5c"          # the Flash RF-11 delta report (docs-only)
BRANCH = "mangabd-008-b1"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_CELLS = Path("/home/z/my-project/cells")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"
SIZE_PIN = 9589900

BEN = FONTS / "NotoSansBengali-Regular.ttf"
JP = FONTS / "NotoSansJP.ttf"
VENDORED = REPO / "assets/fonts/NotoSansJP[wght].ttf"

RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    print(("PASS  " if ok else "FAIL  ") + name
          + (f"  [{detail}]" if detail and not ok else ""))
    RESULTS.append((name, ok))


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout


def load_cells(path):
    raw = Path(path).read_bytes()
    nb = json.loads(raw.decode("utf-8"))
    return raw, nb, ["".join(c.get("source", [])) for c in nb["cells"]
                     if c.get("cell_type") == "code"]


def extract_span(src, start_marker, end_marker=None):
    lines = src.split("\n")
    si = next(i for i, l in enumerate(lines) if start_marker in l)
    if end_marker is None:
        return "\n".join(lines[si:])
    ei = next(i for i, l in enumerate(lines) if end_marker in l and i > si)
    return "\n".join(lines[si:ei])


def make_ns(fb_path=None, main_path=None, fonts_dir=FONTS, registry_path=None):
    """Battery harness namespace (the Phase C make_ns contract) +
    the MANGABD_ASSETS registry the Run All flow provides via cell 4."""
    ns = {"__name__": "m008_rf12_harness"}
    fb = str(fb_path if fb_path is not None
             else Path(fonts_dir) / "NotoSansJP.ttf")
    main_ = str(main_path if main_path is not None
                else Path(fonts_dir) / "NotoSansBengali-Regular.ttf")
    ns["MANGABD_CONFIG"] = {
        "rendering": {
            "font_size_min": 8, "font_size_max": 48, "font_size_default": 24,
            "line_spacing_factor": 1.18, "padding_ratio": 0.08,
            "allow_synthetic_bold": True,
            "stroke_width_bubble": 0, "stroke_width_thought": 0,
            "stroke_width_narrator": 0, "stroke_width_sfx": 1,
            "stroke_width_overlay": 1,
            "default_bubble_color": [0, 0, 0],
            "default_sfx_color": [255, 255, 255],
            "default_narrator_color": [0, 0, 0],
            "default_overlay_color": [255, 255, 255],
            "preview_max_width": 900,
            "font_regular": main_,
            "font_bold": main_,
            "font_fallback": fb,
            "vertical_rotate": -90,
        },
        "detection": {}, "inpainting": {},
    }
    ev = []
    ns["MANGABD_EVENTS"] = ev

    def log_event(message, level="INFO", **extra):
        ev.append({"level": level, "message": message, "extra": extra})

    ns["log_event"] = log_event
    ns["MANGABD_ASSETS"] = {
        "fonts": {
            "regular_path": main_,
            "bold_path": main_,
            "fallback_path": str(registry_path if registry_path is not None
                                 else JP),
            "fallback_sha256": SHA_PIN,
            "fallback_size": SIZE_PIN,
            "fallback_sha_ok": True,
            "fallback_license": "OFL-1.1",
        },
    }
    exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
         "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)
    return ns


def _parse_out(out, ns):
    per = {}
    for line in out.splitlines():
        line = line.strip()
        m = re.match(r"^(✅|❌|⚪)\s+(SKIP\s+)?(.*)$", line)
        if m:
            per[m.group(3)] = (m.group(1) == "✅", m.group(1) == "⚪")
    tot = [e for e in ns["MANGABD_EVENTS"]
           if "Cell 10 completed" in e["message"]]
    return per, (tot[0]["extra"] if tot else {})


def run_battery(span_core, span_batt, fb_path=None, main_path=None,
                registry_path=None, pre_pollute=None):
    """Exec §3-§8 + §10 battery; optional pre_pollute dict seeded into
    _FB_CACHE AFTER the core exec (before the battery) — the Owner-key
    pollution model. Returns (per-test dict, stdout, success, totals)."""
    ns = make_ns(fb_path=fb_path, main_path=main_path,
                 registry_path=registry_path)
    so = io.StringIO()
    success = False
    try:
        exec(compile(span_core, "<cell10 core>", "exec"), ns)
        if pre_pollute:
            ns["_FB_CACHE"].update(pre_pollute)
        with contextlib.redirect_stdout(so):
            exec(compile(span_batt, "<cell10 battery>", "exec"), ns)
        success = True
    except RuntimeError as exc:
        assert "Cell 10 self-tests failed" in str(exc), exc
    out = so.getvalue()
    per, tot = _parse_out(out, ns)
    return per, out, success, tot


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _st(per, name):
    if name not in per:
        return "absent"
    p, s = per[name]
    return "skip" if s else ("pass" if p else "fail")


T9 = "glyph-coverage routing (D-1/D-2)"
T10 = "JP fallback WARN-never-silent (D-4)"
T11 = "horizontal mixed render: fallback glyphs real (D-3)"
T12 = "tofu detector: JP solid glyph vs main .notdef (D-2)"


# ═══════════════════════════════════════════════════════════════
print("=" * 72)
print("MANGABD-008 B1 RF-12 — VERIFY (branch mangabd-008-b1, base bb3b1df)")
print("=" * 72)

# ── V1 static integrity ──────────────────────────────────────
print("\n── V1 static integrity ──")
branch_ok = git("branch", "--show-current").strip() == BRANCH
head = git("rev-parse", "HEAD").strip()
nb_blob_head = git("rev-parse", f"{HEAD_REF}:{NB_NAME}").strip()
nb_blob_base = git("rev-parse", f"{BASE_REF}:{NB_NAME}").strip()
anc = subprocess.run(
    ["git", "-C", str(REPO), "merge-base", "--is-ancestor",
     BASE_REF, "HEAD"], capture_output=True).returncode == 0
check("V1a branch mangabd-008-b1 + HEAD == 48efb5c (the Flash RF-11 DELTA "
      "CHECK report) which descends from bb3b1df and carries its exact "
      "notebook bytes (NO amend; docs-only commits between allowed — the "
      "RF-11-precedent topology)",
      branch_ok and head.startswith(HEAD_REF) and anc
      and nb_blob_head == nb_blob_base,
      f"branch_ok={branch_ok} head={head[:12]} blob={nb_blob_head[:12]}")

raw_post, nb_post, cells_post = load_cells(NB)
raw_base_json = git("show", f"{BASE_REF}:{NB_NAME}")
nb_base = json.loads(raw_base_json)
cells_base = ["".join(c.get("source", [])) for c in nb_base["cells"]
              if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_post[i] != cells_base[i]]
check("V1b scope drift exactly {10} (26 cells byte-identical to bb3b1df)",
      sorted(scope) == [10], f"drift={sorted(scope)}")

marker = "# 10. Self-tests"
pre_span_base = cells_base[10][:cells_base[10].index(marker)]
pre_span_post = cells_post[10][:cells_post[10].index(marker)]
check("V1c cell-10 §1-§9 byte-identical — fixtures ONLY (no source changes)",
      pre_span_base == pre_span_post)


def _block(src, start_marker, end_marker):
    s = src.index(start_marker)
    e = src.index(end_marker, s)
    return src[s:e]


blocks_ok = (
    _block(cells_base[10], "# Test 1: font load", "# Test 9: glyph-coverage routing") ==
    _block(cells_post[10], "# Test 1: font load", "# Test 9: glyph-coverage routing")
    and _block(cells_base[10], "# Test 10: JP fallback font loads",
               '    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])\n') ==
    _block(cells_post[10], "# Test 10: JP fallback font loads",
           '    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])\n')
    and _block(cells_base[10], "# Test 11: horizontal mixed-script render", "# Test 12: tofu detector") ==
    _block(cells_post[10], "# Test 11: horizontal mixed-script render", "# Test 12: tofu detector")
)
tail_marker = '        finally:\n            MANGABD_CONFIG["rendering"]["font_fallback"] = fb_real\n            _FB_CACHE.clear()\n\n        main_hollow'
blocks_ok = blocks_ok and (
    cells_base[10][cells_base[10].index(tail_marker):] ==
    cells_post[10][cells_post[10].index(tail_marker):])
fs_banner = "# ═══════════════════════════════════════════════════════════\n# Final status"
blocks_ok = blocks_ok and (
    cells_base[10][cells_base[10].index(fs_banner):] ==
    cells_post[10][cells_post[10].index(fs_banner):])
check("V1d Tests 1-8 + Test 10's own block + Test 11's own block + Test 12 "
      "tail + final-status block byte-identical — RF-12 touches ONLY the "
      "Test 9/12 fixture heads + the one inserted clear line",
      blocks_ok)

ast_ok = True
for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(cells_post[i], f"cell_{i:02d}.py", "exec")
        except Exception:
            ast_ok = False
check("V1e AST 27/27 (warnings-as-errors)", ast_ok)

rt = json.dumps(nb_post, indent=2, ensure_ascii=False)
check("V1f json writer byte-faithful on the working file",
      rt.encode("utf-8") == raw_post)

ok_fields = all(
    {k: v for k, v in nb_base["cells"][i].items() if k != "source"} ==
    {k: v for k, v in nb_post["cells"][i].items() if k != "source"}
    for i in range(27))
top_ok = ({k: v for k, v in nb_base.items() if k != "cells"} ==
          {k: v for k, v in nb_post.items() if k != "cells"})
check("V1g non-source + top-level notebook fields identical",
      ok_fields and top_ok)

with open(REPO / "scripts/m008_b1_rf12_patches.json", encoding="utf-8") as f:
    patches = json.load(f)
re_src = dict(enumerate(cells_base))
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, p["name"]
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1h re-derivation: post == bb3b1df + exactly the 3 RF-12 patches",
      all(re_src[i] == cells_post[i] for i in range(27)) and len(patches) == 3)

check("V1i vendored font bytes untouched (sha256 == pin)",
      sha256_of(VENDORED) == SHA_PIN and VENDORED.stat().st_size == SIZE_PIN)

batt = cells_post[10][cells_post[10].index(marker):]
base_batt = cells_base[10][cells_base[10].index(marker):]
pat_ok = (
    batt.count("_m9_probe = ImageFont.truetype(") == 1
    and batt.count("_m12_probe = ImageFont.truetype(") == 1
    and batt.count('MANGABD_CONFIG["rendering"]["font_fallback"], 24') == 2
    and batt.count("_m9_probe is not None") == 1
    and batt.count("_m12_probe is not None") == 1
    and batt.count('_FB_CACHE.clear()  # Clear pollution from D-4 test') == 1
    and batt.count("_FB_CACHE.clear()") == 10
    and base_batt.count("_FB_CACHE.clear()") == 9
    and batt.count('_m8_hollow(get_font_fb(48), "H") is False') == 1
)
t9s = batt[batt.index("# Test 9: glyph-coverage routing"):
           batt.index("# Test 10: JP fallback font loads")]
t12s = batt[batt.index("# Test 12: tofu detector"):]
pat_ok = pat_ok and (
    t9s.index("_FB_CACHE.clear()") <
    t9s.index('MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)') <
    t9s.index("_m9_probe = ImageFont.truetype("))
pat_ok = pat_ok and (
    t12s.index("_FB_CACHE.clear()") <
    t12s.index('MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)') <
    t12s.index("_m12_probe = ImageFont.truetype("))
p_clear = batt.index("_FB_CACHE.clear()  # Clear pollution from D-4 test")
pat_ok = pat_ok and (
    batt.index('    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])')
    < p_clear < batt.index("# Test 11: horizontal mixed-script render"))
check("V1j RF-12 pattern: 2 DIRECT probes at size 24 reading the pinned "
      "config; clear -> pin -> probe order inside BOTH test bodies; probes "
      "folded into the verdicts; post-T10 clear exactly once, after Test "
      "10's block, before Test 11; battery clear count 9 -> 10; "
      "get_font_fb(48) hollow-probe semantics kept", pat_ok)

skip_ok = (
    batt.count("def run_test_skip") == 1
    and batt.count("if not _vendored_jp_present:") == 3
    and batt.count("_vendored_jp_present = Path(_vendored_jp).exists()") == 1
    and batt.count("tests_total=len(tests) + tests_skipped") == 1
    and batt.count("tests_skipped=tests_skipped") == 1
    and "টি test skipped" in batt
    and batt.count("assert not Path(missing_path).exists()") == 2
)
check("V1k RF-11 machinery intact (skip helper + 2 skip branches + shared "
      "fixture + totals arithmetic + skip status line) and RF-10 missing-"
      "path asserts kept (Tests 10/11)", skip_ok)

# ── V2 cell-10 battery matrix ────────────────────────────────
print("\n── V2 cell-10 battery matrix (RF-12) ──")
span_core = extract_span(cells_post[10], "# 3. Text helpers",
                         "# 9. Page rendering pipeline")
span_batt = extract_span(cells_post[10], "# 10. Self-tests", None)

# A: happy path — registry + ambient = real JP
perA, outA, succA, totA = run_battery(span_core, span_batt)
check("V2a happy path: 12/12 SUCCESS, 0 skipped — the directive's bar",
      succA and totA.get("tests_total") == 12
      and totA.get("tests_passed") == 12
      and totA.get("tests_skipped", 0) == 0 and "❌" not in outA,
      f"totals={totA}")

# B: Owner-key cache pollution immunity — _FB_CACHE pre-seeded with the
# exact (24, False) -> None key Test 10's D-4 degradation caches
perB, outB, succB, totB = run_battery(
    span_core, span_batt, pre_pollute={(24, False): None})
check("V2b Owner-key pollution immunity: _FB_CACHE pre-seeded with "
      "(24, False) -> None BEFORE the battery -> still 12/12 — the "
      "Test 9/12 loads no longer trust pre-existing cache state",
      succB and totB.get("tests_passed") == 12 and "❌" not in outB,
      f"t9={_st(perB, T9)} t10={_st(perB, T10)} t11={_st(perB, T11)} "
      f"t12={_st(perB, T12)} totals={totB}")

# C: post-T10 injection + the P2 line, segmented exec
seg_t10_end = '    run_test("JP fallback WARN-never-silent (D-4)", False, str(exc)[:160])\n'
idx_t10_end = span_batt.index(seg_t10_end) + len(seg_t10_end)
idx_p2 = span_batt.index("# RF-12: Test 10-এর D-4 degradation")
idx_t11 = span_batt.index("# Test 11: horizontal mixed-script render")
seg1 = span_batt[:idx_t10_end]
seg2 = span_batt[idx_t10_end:idx_t11]
seg3 = span_batt[idx_t11:]
nsC = make_ns()
soC = io.StringIO()
succC = False
try:
    exec(compile(span_core, "<cell10 core>", "exec"), nsC)
    with contextlib.redirect_stdout(soC):
        exec(compile(seg1, "<battery s1: through Test 10>", "exec"), nsC)
    # INJECT the pollution right where Test 10's block just ended —
    # the Owner's observed residual state, BOTH vulnerable keys
    nsC["_FB_CACHE"][(24, False)] = None
    nsC["_FB_CACHE"][(48, False)] = None
    assert set(nsC["_FB_CACHE"].keys()) == {(24, False), (48, False)}
    with contextlib.redirect_stdout(soC):
        exec(compile(seg2, "<battery s2: RF-12 post-T10 clear>", "exec"), nsC)
    cache_after_p2 = dict(nsC["_FB_CACHE"])
    with contextlib.redirect_stdout(soC):
        exec(compile(seg3, "<battery s3: Test 11 onward>", "exec"), nsC)
    succC = True
except RuntimeError as exc:
    assert "Cell 10 self-tests failed" in str(exc), exc
outC = soC.getvalue()
perC, totC = _parse_out(outC, nsC)
check("V2c post-T10 injection, segmented: pollution {(24,F):None, "
      "(48,F):None} injected after Test 10's block -> the RF-12 post-T10 "
      "clear line wipes it (cache provably empty) -> Test 11 onward -> "
      "combined 12/12",
      cache_after_p2 == {} and succC and totC.get("tests_passed") == 12
      and "❌" not in outC,
      f"cache_after_p2={cache_after_p2} t9={_st(perC, T9)} "
      f"t11={_st(perC, T11)} t12={_st(perC, T12)} totals={totC}")

# D: RF-11 Owner-env class regression (registry = missing relative vendored
# path, CWD outside repo; ambient = wrong-bytes Drive-style)
drive_dir = Path(tempfile.mkdtemp()) / "drive" / "MyDrive" / "MangaBD_V12" / "fonts"
drive_dir.mkdir(parents=True)
shutil.copy(BEN, drive_dir / "NotoSansJP.ttf")   # WRONG bytes under the JP name
fb_wrong = drive_dir / "NotoSansJP.ttf"
missing_registry = "assets/fonts/NotoSansJP[wght].ttf"

_cwd = Path.cwd()
_chdir_tmp = Path(tempfile.mkdtemp())
os.chdir(_chdir_tmp)
try:
    perD, outD, succD, totD = run_battery(
        span_core, span_batt, fb_path=fb_wrong, registry_path=missing_registry)

    # E: registry missing AND ambient genuinely missing
    perE, outE, succE, totE = run_battery(
        span_core, span_batt, fb_path=missing_registry,
        registry_path=missing_registry)
finally:
    os.chdir(_cwd)

check("V2d RF-11 Owner-env class preserved: Tests 9/12 SKIP (no FAIL), "
      "10/11 pass, 10 passed + 2 skipped = 12 total, SUCCESS + skip "
      "status lines — RF-12 changed nothing in the skip path",
      _st(perD, T9) == "skip" and _st(perD, T12) == "skip"
      and _st(perD, T10) == "pass" and _st(perD, T11) == "pass"
      and totD.get("tests_passed") == 10 and totD.get("tests_total") == 12
      and totD.get("tests_skipped") == 2 and succD
      and outD.count("⚪ SKIP") == 2 and "❌" not in outD
      and "2টি test skipped" in outD
      and "Vendored JP font missing" in outD,
      f"t9={_st(perD, T9)} t10={_st(perD, T10)} t11={_st(perD, T11)} "
      f"t12={_st(perD, T12)} totals={totD}")

check("V2e both-missing regression: 9/12 SKIP, 10/11 FAIL as loud env "
      "diagnostics (RF-10 R3d contract kept), NEEDS FIX, 8 passed + 2 "
      "skipped",
      _st(perE, T9) == "skip" and _st(perE, T12) == "skip"
      and _st(perE, T10) == "fail" and _st(perE, T11) == "fail"
      and totE.get("tests_passed") == 8 and totE.get("tests_total") == 12
      and totE.get("tests_skipped") == 2 and not succE,
      f"t9={_st(perE, T9)} t10={_st(perE, T10)} t11={_st(perE, T11)} "
      f"t12={_st(perE, T12)} totals={totE}")

# F: vendored present-but-GARBAGE — exists() passes, truetype throws.
# POST-fix: the DIRECT probe throws BEFORE any routing -> both tests fail
# LOUD with the exception named in the FAIL details. BASE (bb3b1df)
# observed under the same scenario for the honest pre/post comparison.
garbage = Path(tempfile.mkdtemp()) / "NotoSansJP-garbage.ttf"
garbage.write_bytes(b"GARBAGE-BYTES-NOT-A-FONT" * 128)
assert garbage.exists() and garbage.stat().st_size >= 1024

perF, outF, succF, totF = run_battery(
    span_core, span_batt, fb_path=JP, registry_path=garbage)
t9_details = re.search(r"❌ glyph-coverage routing \(D-1/D-2\)\n     (\S.*)", outF)
t12_details = re.search(r"❌ tofu detector: JP solid glyph vs main \.notdef \(D-2\)\n     (\S.*)", outF)
check("V2f vendored-present-but-garbage: POST-fix Tests 9/12 fail LOUD — "
      "the DIRECT probe names the failure in the FAIL details (visible, "
      "never silent); Tests 10/11 still pass (ambient healthy)",
      _st(perF, T9) == "fail" and _st(perF, T12) == "fail"
      and _st(perF, T10) == "pass" and _st(perF, T11) == "pass"
      and t9_details is not None and t12_details is not None
      and not succF,
      f"t9={_st(perF, T9)} t12={_st(perF, T12)} "
      f"t9_details={t9_details.group(1)[:60] if t9_details else None}")

span_core_base = extract_span(cells_base[10], "# 3. Text helpers",
                              "# 9. Page rendering pipeline")
span_batt_base = extract_span(cells_base[10], "# 10. Self-tests", None)
perFb, outFb, succFb, totFb = run_battery(
    span_core_base, span_batt_base, fb_path=JP, registry_path=garbage)
print(f"      [observed] BASE (bb3b1df) under the same garbage-vendored "
      f"scenario: t9={_st(perFb, T9)} t10={_st(perFb, T10)} "
      f"t11={_st(perFb, T11)} t12={_st(perFb, T12)} "
      f"success={succFb} totals={totFb}")
check("V2g garbage-vendored delta, honest form: the RF-12 probes convert "
      "the BASE's observed verdict under an unloadable vendored font into "
      "a loud named failure with details (no silent acceptance of an "
      "unloadable fixture); BASE's observed signature recorded above "
      "(whatever it was — false-PASS or detail-less FAIL — RF-12 names "
      "the env failure explicitly)",
      _st(perF, T9) == "fail" and t9_details is not None
      and t12_details is not None)

# ── V3 cells-11/12 §7.5 self-checks (unchanged bytes) ─────────
print("\n── V3 cells-11/12 §7.5 glyph-coverage self-checks ──")
s2_post = extract_span(cells_post[11], "# ── 2) Fallback font", "# ── 3)")
s7_post = extract_span(cells_post[11], "# ── 7) vertical note render ──",
                       "# ── 8) pipeline wrap ──")
s2_12 = extract_span(cells_post[12], "# ── 2) Fallback font", "# ── 3)")
s5_12 = extract_span(cells_post[12], "# ── 5) Vertical note render",
                     "# ── 6) UI button")

ns_v = make_ns()
exec(compile(span_core, "<cell10 §3-§8>", "exec"), ns_v)
with contextlib.redirect_stdout(io.StringIO()) as so11:
    exec(compile(s2_post, "<cell11 §2>", "exec"), ns_v)
    exec(compile(s7_post, "<cell11 §7+§7.5>", "exec"), ns_v)
check("V3a cell-11 §7.5 self-checks 5/5 (D-1..D-5 vertical)",
      "QUALITY CORE glyph-coverage: 5/5" in so11.getvalue(),
      so11.getvalue()[-300:])

ns_v12 = make_ns()
exec(compile(span_core, "<cell10 §3-§8>", "exec"), ns_v12)
with contextlib.redirect_stdout(io.StringIO()) as so12:
    exec(compile(s2_12, "<cell12 §2>", "exec"), ns_v12)
    exec(compile(s7_post, "<cell11 §7+§7.5>", "exec"), ns_v12)
    exec(compile(s5_12, "<cell12 §5+§7.5>", "exec"), ns_v12)
check("V3b cell-12 §7.5 self-checks 5/5 (mirror)",
      so12.getvalue().count("QUALITY CORE glyph-coverage: 5/5") >= 1,
      so12.getvalue()[-300:])

v11 = extract_span(cells_post[11], "# ── 7.5)", "# ── 8) pipeline wrap ──")
v12 = extract_span(cells_post[12], "# ── 7.5)", "# ── 6) UI button")
check("V3c §7.5 block byte-identical in cells 11/12", v11 == v12)
check("V3d cells 11/12 byte-identical to bb3b1df (unchanged by RF-12)",
      cells_post[11] == cells_base[11] and cells_post[12] == cells_base[12])

# ── V4 m002_sim_v2 on the working cells ─────────────────────
print("\n── V4 m002_sim_v2 fresh-kernel simulator ──")
SIM_CELLS.mkdir(exist_ok=True)
for old in SIM_CELLS.glob("cell_*.py"):
    old.unlink()
for i in range(27):
    (SIM_CELLS / f"cell_{i:02d}.py").write_text(cells_post[i], encoding="utf-8")
sim = subprocess.run(["python3", str(SIM)], capture_output=True, text=True)
m_abort = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)",
                    sim.stdout)
check("V4a simulator runs", sim.returncode == 0 and m_abort is not None,
      (sim.stderr or sim.stdout)[-300:])
print(sim.stdout.strip().splitlines()[-1] if sim.stdout.strip() else "")
check("V4b m002_sim_v2 = 0 abort sites",
      m_abort is not None and int(m_abort.group(1)) == 0,
      f"count={m_abort.group(1) if m_abort else 'parse-fail'}")

# ── summary ──────────────────────────────────────────────────
print("\n" + "=" * 72)
fails = [n for n, ok in RESULTS if not ok]
print(f"MANGABD-008 B1 RF-12 VERIFY: {len(RESULTS) - len(fails)}/{len(RESULTS)} PASS")
if fails:
    print("FAILED:")
    for n in fails:
        print("  - " + n)
    sys.exit(1)
print("ALL GREEN")
