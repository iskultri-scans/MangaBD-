#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-13 — VERIFY (supersedes the RF-10/11/12 suites on
this branch; those instruments stay byte-identical as committed records).

Delta base: 5a84994 (RF-12). Scope {4,10,11,12} (10 anchored patches,
manifest scripts/m008_b1_rf13_patches.json).

V1  static integrity (scope/confinement/RF-12+RF-11+RF-10 patterns/AST/
    re-derivation/vendored sha) + m002_sim_v2 = 0 abort sites.
V2  runtime battery matrix, cell 10 §3-§8 + §10 VERBATIM from the working
    notebook bytes:
      A  healthy Drive env ........ 12/12 hard PASS, no gate raise
      G  Latin-main (OWNER class) . 12/12 hard PASS + 🔶 DIAG lines,
                                   NO GATE RAISE (the directive-5 decouple),
                                   hygiene + config restore proven
      C  main = JP bytes .......... T9 HARD FAIL naming the tofu chars,
                                   gate raise (render genuinely broken)
      D  stale-bad ambient fb ..... T10+T11 loud FAIL, gate raise
      F  garbage at vendored ...... T9/T12 loud FAIL w/ exception details,
                                   gate raise (no false-pass)
      S  vendored missing ......... Tests 9/12 SKIP + 10 passed, no raise
                                   (RF-11 contract preserved)
      P  _FB_CACHE pre-pollution ... still 12/12 (RF-12 contract preserved)
V3  cell-4 §8.6 sanity harness (healthy/Latin/JP-at-regular/missing/
    unloadable).
V4  §7.5 mirrors runtime (both, R-A 5/5; R-G check-2 tofu-semantics pass
    + INFO note, no ❌) + mirror parity.
V5  mutation trace on the patched battery: all 8 font_fallback writes are
    pin/finally-restore pairs; first /tmp/MISSING write is Test 10's D-4
    fixture (AFTER Test 9); post-battery residue popped (hygiene).
"""
import contextlib
import hashlib
import io
import json
import re
import subprocess
import sys
import tempfile
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
MANIFEST = REPO / "scripts" / "m008_b1_rf13_patches.json"
BASE_REF = "5a84994"       # RF-12 (the notebook re-derivation base)
HEAD_REF = "c072dc5"       # the Flash RF-12 DELTA CHECK report (docs-only;
                            # its notebook blob == 5a84994's — RF-11/RF-12
                            # precedent docs-only-between topology)
BRANCH = "mangabd-008-b1"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_CELLS = Path("/home/z/my-project/cells")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"
SIZE_PIN = 9589900

PROBE_BEN = FONTS / "NotoSansBengali-Regular.ttf"
FREESERIF = Path("/usr/share/fonts/truetype/freefont/FreeSerif.ttf")
VENDORED = REPO / "assets/fonts/NotoSansJP[wght].ttf"

T9 = "glyph-coverage routing (D-1/D-2)"
T10 = "JP fallback WARN-never-silent (D-4)"
T11 = "horizontal mixed render: fallback glyphs real (D-3)"
T12 = "tofu detector: JP solid glyph vs main .notdef (D-2)"

RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    print(("PASS  " if ok else "FAIL  ") + name
          + (f"  [{detail}]" if detail and not ok else ""))
    RESULTS.append((name, ok))


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout


def extract_span(src, start_marker, end_marker=None):
    lines = src.split("\n")
    si = next(i for i, l in enumerate(lines) if start_marker in l)
    if end_marker is None:
        return "\n".join(lines[si:])
    ei = next(i for i, l in enumerate(lines) if end_marker in l and i > si)
    return "\n".join(lines[si:ei])


raw = NB.read_bytes()
nb = json.loads(raw.decode("utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"]]

# base cells (RF-12 = 5a84994)
raw_base = git("show", f"{BASE_REF}:{NB.name}")
cells_base = ["".join(c["source"])
              for c in json.loads(raw_base)["cells"]]

print("=" * 72)
print("MANGABD-008 B1 RF-13 — VERIFY (delta base 5a84994 = RF-12)")
print("=" * 72)

# ── V1 static integrity ──────────────────────────────────────
print("\n── V1 static integrity ──")
branch_ok = git("branch", "--show-current").strip() == BRANCH
anc = subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor",
                      BASE_REF, "HEAD"], capture_output=True).returncode == 0
head_ok = git("rev-parse", "--short", "HEAD").strip() == HEAD_REF
nb_blob_head = git("rev-parse", f"HEAD:{NB.name}").strip()
nb_blob_base = git("rev-parse", f"{BASE_REF}:{NB.name}").strip()
check("V1a branch + HEAD == c072dc5 (the Flash RF-12 DELTA CHECK report, "
      "docs-only — its notebook blob == RF-12 5a84994's; build state: the "
      "RF-13 notebook patch uncommitted; byte-proof via V1c re-derivation)",
      branch_ok and anc and head_ok and nb_blob_head == nb_blob_base,
      f"{branch_ok} {anc} {head_ok} blob {nb_blob_head[:10]} vs {nb_blob_base[:10]}")

scope = sorted(i for i in range(27) if cells[i] != cells_base[i])
check("V1b scope drift vs RF-12 exactly {4,10,11,12}", scope == [4, 10, 11, 12],
      f"drift={scope}")

PATCHES = json.loads(MANIFEST.read_text(encoding="utf-8"))
re_src = {i: cells_base[i] for i in range(27)}
for p in PATCHES:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derive {p['name']}"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1c 10-patch manifest re-derivation byte-exact",
      all(re_src[i] == cells[i] for i in range(27)) and len(PATCHES) == 10)

c4, c4b = cells[4], cells_base[4]
check("V1d cell-4 §8.5 span + §9 span byte-identical; whole-cell delta = "
      "§8.6 block + the one declared registry key line",
      extract_span(c4, "# 8.5 Japanese fallback font",
                   'MANGABD_CONFIG["rendering"]["font_fallback"] = str(fallback_font_path)')
      == extract_span(c4b, "# 8.5 Japanese fallback font",
                      'MANGABD_CONFIG["rendering"]["font_fallback"] = str(fallback_font_path)')
      and extract_span(c4, "# 9. Font + libraqm test", "# 10. Asset registry")
      == extract_span(c4b, "# 9. Font + libraqm test", "# 10. Asset registry")
      and c4.replace('        "regular_sane": bool(_main_font_sane),\n', "")
      .replace(PATCHES[0]["new"][len(PATCHES[0]["old"]):], "") == c4b)
check("V1e cell-4 §8.6 present (header + print) + registry key wired",
      c4.count("8.6 Bengali main font sanity check") == 2
      and c4.count('"regular_sane": bool(_main_font_sane),') == 1
      and "_main_font_sane" in c4)

c10, c10b = cells[10], cells_base[10]
check("V1f cell-10 §1-§9 byte-identical to RF-12",
      extract_span(c10, "MangaBD V12 — Cell 10", "# 3. Text helpers")
      == extract_span(c10b, "MangaBD V12 — Cell 10", "# 3. Text helpers")
      and extract_span(c10, "# 3. Text helpers", "# 10. Self-tests")
      == extract_span(c10b, "# 3. Text helpers", "# 10. Self-tests"))
batt = extract_span(c10, "# 10. Self-tests")
batt_b = extract_span(c10b, "# 10. Self-tests")
BLK = [("# Test 1: font load", "# Test 2: measure text"),
       ("# Test 2: measure text", "# Test 3: text wrap"),
       ("# Test 3: text wrap", "# Test 4: font fit"),
       ("# Test 4: font fit", "# Test 5: background color"),
       ("# Test 5: background color", "# Test 6: render Bengali text"),
       ("# Test 6: render Bengali text", "# Test 7: special marker skip"),
       ("# Test 7: special marker skip", "# Test 8: Bengali validation"),
       ("# Test 8: Bengali validation", "# RF-11: Tests 9/12"),
       ("# Test 10: JP fallback font loads", "# RF-12: Test 10"),
       ("# Test 11: horizontal mixed-script render", "# Test 12: tofu detector")]
ok_blocks = True
for m_start, m_end in BLK:
    if extract_span(batt, m_start, m_end) != extract_span(batt_b, m_start, m_end):
        ok_blocks = False
        print(f"      block changed: {m_start}")
check("V1g Tests 1-8 + 10 + 11 blocks byte-identical to RF-12", ok_blocks)

check("V1h RF-12 clear/pin/probe patterns preserved (clears=10, 2 direct "
      "probes, clear->pin->probe in T9 and T12, fb hollow probes kept + こ added)",
      batt.count("_FB_CACHE.clear()") == 10
      and batt.count('MANGABD_CONFIG["rendering"]["font_fallback"], 24') == 2
      and batt.index('_FB_CACHE.clear()\n            MANGABD_CONFIG["rendering"]["font_fallback"] = str(real_jp_path)')
      < batt.index("_m9_probe = ImageFont.truetype(")
      and '_m8_hollow(get_font_fb(48), "H") is False' in batt
      and '_m8_hollow(get_font_fb(48), "こ") is False' in batt)
check("V1i RF-11 skip + RF-10 D-4 asserts preserved",
      batt.count("def run_test_skip") == 1
      and batt.count("if not _vendored_jp_present:") == 3
      and batt.count("assert not Path(missing_path).exists()") == 2
      and "tests_skipped=tests_skipped," in batt)
check("V1j RF-13 diag + gate decoupling patterns",
      batt.count("def run_test_diag") == 1
      and batt.count("tests_diagnosed=tests_diagnosed,") == 1
      and "all_tests_passed = all(tests)" in batt
      and 'raise RuntimeError("Cell 10 self-tests failed' in batt
      and "run_test(\"glyph-coverage routing (D-1/D-2)\", ok, _m9_details)" in batt
      and "fb_solid,\n        )" in batt)
check("V1k RF-13 hygiene tail (fixture residue popped once each)",
      batt.count('_FONT_COVERAGE_CACHE.pop("/tmp/MISSING-test-font.ttf", None)') == 1
      and batt.count('_FONT_ROUTE_WARNED.pop("fb_load", None)') == 2)
v11 = extract_span(cells[11], "# ── 7.5)", "# ── 8) pipeline wrap ──")
v12 = extract_span(cells[12], "# ── 7.5)", "# ── 6) UI button")
check("V1l §7.5 mirrors byte-identical (excl. cell-local end header)",
      v11.split("\n")[:-1] == v12.split("\n")[:-1])
check("V1m cells 11/12 delta confined to the §7.5 D-2 check",
      cells[11].replace(PATCHES[8]["new"], PATCHES[8]["old"]) == cells_base[11]
      and cells[12].replace(PATCHES[9]["new"], PATCHES[9]["old"]) == cells_base[12])

ast_ok = True
for i in range(27):
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error")
            compile(cells[i], f"cell_{i:02d}", "exec")
    except Exception as e:
        ast_ok = False
        print(f"      AST fail cell {i}: {e}")
check("V1n AST 27/27 clean (warnings-as-errors)", ast_ok)

vf = REPO / "assets/fonts/NotoSansJP[wght].ttf"
check("V1o vendored font untouched",
      hashlib.sha256(vf.read_bytes()).hexdigest() == SHA_PIN
      and vf.stat().st_size == SIZE_PIN)

SIM_CELLS.mkdir(exist_ok=True)
for old in SIM_CELLS.glob("cell_*.py"):
    old.unlink()
for i in range(27):
    (SIM_CELLS / f"cell_{i:02d}.py").write_text(cells[i], encoding="utf-8")
sim = subprocess.run(["python3", str(SIM)], capture_output=True, text=True)
m_abort = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)",
                    sim.stdout)
check("V1p m002_sim_v2 = 0 abort sites",
      sim.returncode == 0 and m_abort is not None and int(m_abort.group(1)) == 0,
      (sim.stderr or sim.stdout)[-200:])


# ── shared runtime harness ───────────────────────────────────
SPAN_CORE = extract_span(cells[10], "# 3. Text helpers", "# 10. Self-tests")
SPAN_BATT = extract_span(cells[10], "# 10. Self-tests")


def make_drive_env(tmp, main_src, fb_src, ambient_fb=None, registry=None):
    fonts = Path(tmp) / "drive" / "MyDrive" / "MangaBD_V12" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    ben, bold = fonts / "NotoSansBengali-Regular.ttf", fonts / "NotoSansBengali-Bold.ttf"
    jp = fonts / "NotoSansJP.ttf"
    if main_src is not None:
        ben.write_bytes(Path(main_src).read_bytes())
        bold.write_bytes(Path(main_src).read_bytes())
    if fb_src is not None:
        jp.write_bytes(Path(fb_src).read_bytes())
    cfg = {"rendering": {
        "font_size_min": 8, "font_size_max": 48, "font_size_default": 24,
        "line_spacing_factor": 1.18, "padding_ratio": 0.08,
        "allow_synthetic_bold": True,
        "stroke_width_bubble": 0, "stroke_width_thought": 0,
        "stroke_width_narrator": 0, "stroke_width_sfx": 1,
        "stroke_width_overlay": 1,
        "default_bubble_color": [0, 0, 0], "default_sfx_color": [255, 255, 255],
        "default_narrator_color": [0, 0, 0], "default_overlay_color": [255, 255, 255],
        "preview_max_width": 900,
        "font_regular": str(ben), "font_bold": str(bold),
        "font_fallback": str(jp) if ambient_fb is None else ambient_fb,
        "vertical_rotate": -90,
    }, "detection": {}, "inpainting": {}}
    return fonts, cfg, (str(jp) if registry is None else registry)


def make_ns(cfg, registry_path, trace=False):
    import inspect
    ns = {"__name__": "rf13_verify"}
    ns["MANGABD_CONFIG"] = cfg
    ns["MANGABD_EVENTS"] = []
    trace_log = []

    def log_event(message, level="INFO", **extra):
        ns["MANGABD_EVENTS"].append({"level": level, "message": message,
                                     "extra": extra})

    ns["log_event"] = log_event
    ns["MANGABD_ASSETS"] = {"fonts": {
        "regular_path": cfg["rendering"]["font_regular"],
        "bold_path": cfg["rendering"]["font_bold"],
        "fallback_path": str(registry_path),
        "fallback_sha256": SHA_PIN, "fallback_size": SIZE_PIN,
        "fallback_sha_ok": True, "fallback_license": "OFL-1.1"}}
    exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
         "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)
    if trace:
        class _TD(dict):
            def __setitem__(self, k, v):
                if k == "font_fallback":
                    fr = inspect.stack()[1]
                    trace_log.append({"value": str(v),
                                      "line": fr.lineno - 1250})
                super().__setitem__(k, v)
        cfg["rendering"] = _TD(cfg["rendering"])
    ns["_TRACE"] = trace_log
    return ns


def run_env(name, main_src, fb_src, ambient_fb=None, registry=None,
            pre_pollute=None, want_gate=None):
    tmp = tempfile.mkdtemp(prefix=f"rf13v_{name}_")
    fonts, cfg, reg = make_drive_env(tmp, main_src, fb_src, ambient_fb, registry)
    ns = make_ns(cfg, reg)
    so = io.StringIO()
    gate = None
    try:
        exec(compile(SPAN_CORE, "<core>", "exec"), ns)
        if pre_pollute:
            ns["_FB_CACHE"].update(pre_pollute)
        with contextlib.redirect_stdout(so):
            exec(compile(SPAN_BATT, "<batt>", "exec"), ns)
        gate = False
    except RuntimeError as exc:
        gate = "Cell 10 self-tests failed" in str(exc)
    out = so.getvalue()
    per = {}
    for line in out.splitlines():
        m = re.match(r"^(✅|❌|⚪)\s+(SKIP\s+)?(.*)$", line.strip())
        if m:
            per[m.group(3)] = ("pass" if m.group(1) == "✅" else
                               "skip" if m.group(1) == "⚪" else "fail")
    tot = [e for e in ns["MANGABD_EVENTS"]
           if "Cell 10 completed" in e["message"]]
    extras = tot[0]["extra"] if tot else {}
    st = {
        "per": per, "gate": gate, "diag": out.count("🔶 DIAG"),
        "extras": extras, "out": out,
        "config_fb": ns["MANGABD_CONFIG"]["rendering"]["font_fallback"],
        "fb_cache": dict(ns["_FB_CACHE"]),
        "cov_keys": set(ns["_FONT_COVERAGE_CACHE"].keys()),
        "warned": set(ns["_FONT_ROUTE_WARNED"].keys()),
    }
    return st


# ── V2 runtime battery matrix ────────────────────────────────
print("\n── V2 runtime battery matrix (cell 10 VERBATIM) ──")
A = run_env("A_healthy", PROBE_BEN, VENDORED)
check("V2a A healthy: 12/12 PASS, 0 skip/diag, NO gate raise",
      all(v == "pass" for v in A["per"].values()) and len(A["per"]) == 12
      and A["diag"] == 0 and A["gate"] is False
      and A["extras"].get("tests_diagnosed") == 0,
      json.dumps(A["per"], ensure_ascii=False)[:200])

G = run_env("G_owner_class", FREESERIF, VENDORED)
check("V2b G OWNER CLASS (Latin main): 12/12 hard PASS, 🔶 DIAG >= 2, "
      "NO gate raise — the directive-5 decouple",
      all(v == "pass" for v in G["per"].values()) and len(G["per"]) == 12
      and G["diag"] >= 2 and G["gate"] is False,
      json.dumps(G["per"], ensure_ascii=False)[:200])
check("V2c G diag lines name the Latin shape + final-status line + extras "
      "(main-side calibration branch: hollow/blank/substitute — all diag)",
      "ASCII/kana not in main" in G["out"] and "U+0061" in G["out"]
      and ("not exercisable" in G["out"] or "basic Latin" in G["out"]
           or "substitutes missing glyphs" in G["out"])
      and "font-shape diagnostic" in G["out"]
      and G["extras"].get("tests_diagnosed", 0) >= 2,
      G["out"][-400:])
check("V2d G post-run state clean (config restored, _FB_CACHE empty, "
      "fixture residue popped)",
      Path(G["config_fb"]).name == "NotoSansJP.ttf" and G["fb_cache"] == {}
      and not any("MISSING-test-font" in k for k in G["cov_keys"])
      and "fb_load" not in G["warned"])

C = run_env("C_main_jp", VENDORED, VENDORED)
check("V2e C main=JP bytes: T9 HARD FAIL naming tofu chars (ক/।), gate raise",
      C["per"].get(T9) == "fail" and C["gate"] is True
      and "U+0995" in C["out"] and "U+0964" in C["out"],
      json.dumps(C["per"], ensure_ascii=False)[:200])

D = run_env("D_stale_bad_ambient", PROBE_BEN, VENDORED,
            ambient_fb="/tmp/MISSING-test-font.ttf")
check("V2f D stale-bad ambient fb: T10+T11 loud FAIL, gate raise "
      "(regression class preserved)",
      D["per"].get(T10) == "fail" and D["per"].get(T11) == "fail"
      and D["gate"] is True,
      json.dumps(D["per"], ensure_ascii=False)[:200])

tmp_f = tempfile.mkdtemp(prefix="rf13v_garbage_")
garbage = Path(tmp_f) / "garbage-at-vendored.ttf"
garbage.write_bytes(b"NOT A FONT" * 100)
F = run_env("F_garbage_vendored", PROBE_BEN, VENDORED, registry=str(garbage))
check("V2g F garbage at vendored: T9+T12 loud FAIL with exception details, "
      "gate raise (Flash no-false-pass contract)",
      F["per"].get(T9) == "fail" and F["per"].get(T12) == "fail"
      and F["gate"] is True,
      json.dumps(F["per"], ensure_ascii=False)[:200])

S = run_env("S_missing_vendored", PROBE_BEN, VENDORED,
            registry="/tmp/rf13v_nonexistent_dir/NotoSansJP[wght].ttf")
skips = sum(1 for v in S["per"].values() if v == "skip")
check("V2h S vendored missing: Tests 9/12 SKIP + 10 passed, NO gate raise "
      "(RF-11 contract)",
      skips == 2 and S["per"].get(T9) == "skip" and S["per"].get(T12) == "skip"
      and S["gate"] is False and len(S["per"]) == 12,
      json.dumps(S["per"], ensure_ascii=False)[:200])

P = run_env("P_pre_polluted", PROBE_BEN, VENDORED,
            pre_pollute={(24, False): None, (48, False): None})
check("V2i P _FB_CACHE pre-pollution: still 12/12 (RF-12 contract preserved)",
      all(v == "pass" for v in P["per"].values()) and len(P["per"]) == 12
      and P["gate"] is False,
      json.dumps(P["per"], ensure_ascii=False)[:200])


# ── V3 cell-4 §8.6 sanity harness ────────────────────────────
print("\n── V3 cell-4 §8.6 main-font sanity harness ──")
SEC_86 = extract_span(c4, "# 8.6 Bengali main font sanity check", "# 9. Font + libraqm test")


def run_86(font_src):
    tmp = tempfile.mkdtemp(prefix="rf13v_86_")
    fonts, cfg, reg = make_drive_env(tmp, font_src, VENDORED)
    ns = {"__name__": "v3", "FONT_REGULAR_PATH": cfg["rendering"]["font_regular"],
          "MANGABD_EVENTS": []}
    ns["log_event"] = lambda m, level="INFO", **k: ns["MANGABD_EVENTS"].append((level, m))
    exec("from PIL import ImageFont\nfrom pathlib import Path", ns)
    so = io.StringIO()
    with contextlib.redirect_stdout(so):
        exec(compile(SEC_86, "<8.6>", "exec"), ns)
    return so.getvalue(), ns["_main_font_sane"], ns["MANGABD_EVENTS"]


o86, s86, ev86 = run_86(PROBE_BEN)
check("V3a healthy main: 'sanity OK' + sane=True",
      "sanity OK" in o86 and s86 is True)
o86b, s86b, ev86b = run_86(FREESERIF)
check("V3b Latin main: loud 'basic Latin আছে' note + sane=True + INFO event",
      "basic Latin আছে" in o86b and s86b is True
      and any(l == "INFO" for l, _ in ev86b))
o86c, s86c, ev86c = run_86(VENDORED)
check("V3c JP bytes at regular: loud glyph-missing diagnostic + sane=False + WARN event",
      "glyph নেই" in o86c and s86c is False
      and any(l == "WARN" for l, _ in ev86c))
tmp_d = tempfile.mkdtemp(prefix="rf13v_86d_")
fonts_d, cfg_d, _ = make_drive_env(tmp_d, None, VENDORED)
Path(cfg_d["rendering"]["font_regular"]).unlink(missing_ok=True)
ns = {"__name__": "v3d", "FONT_REGULAR_PATH": cfg_d["rendering"]["font_regular"],
      "MANGABD_EVENTS": []}
ns["log_event"] = lambda m, level="INFO", **k: ns["MANGABD_EVENTS"].append((level, m))
exec("from PIL import ImageFont\nfrom pathlib import Path", ns)
so = io.StringIO()
with contextlib.redirect_stdout(so):
    exec(compile(SEC_86, "<8.6d>", "exec"), ns)
check("V3d missing main: loud missing diagnostic + sane=False",
      "missing" in so.getvalue() and ns["_main_font_sane"] is False)
tmp_e = tempfile.mkdtemp(prefix="rf13v_86e_")
fonts_e, cfg_e, _ = make_drive_env(tmp_e, PROBE_BEN, VENDORED)
bad = Path(cfg_e["rendering"]["font_regular"])
bad.write_bytes(b"GARBAGE-BYTES" * 50)
ns = {"__name__": "v3e", "FONT_REGULAR_PATH": str(bad), "MANGABD_EVENTS": []}
ns["log_event"] = lambda m, level="INFO", **k: ns["MANGABD_EVENTS"].append((level, m))
exec("from PIL import ImageFont\nfrom pathlib import Path", ns)
so = io.StringIO()
with contextlib.redirect_stdout(so):
    exec(compile(SEC_86, "<8.6e>", "exec"), ns)
check("V3e unloadable main: loud load-failed diagnostic + sane=False",
      "load failed" in so.getvalue() and ns["_main_font_sane"] is False)


# ── V4 §7.5 mirrors runtime ──────────────────────────────────
print("\n── V4 §7.5 mirrors runtime ──")
s2_post = extract_span(cells[11], "# ── 2) Fallback font", "# ── 3)")
s7_post = extract_span(cells[11], "# ── 7) vertical note render ──",
                      "# ── 8) pipeline wrap ──")
s5_12 = extract_span(cells[12], "# ── 5) Vertical note render",
                     "# ── 6) UI button")


def run_mirror(main_src):
    tmp = tempfile.mkdtemp(prefix="rf13v_mirror_")
    fonts, cfg, reg = make_drive_env(tmp, main_src, VENDORED)
    ns = make_ns(cfg, reg)
    with contextlib.redirect_stdout(io.StringIO()) as so:
        exec(compile(SPAN_CORE, "<core>", "exec"), ns)
        exec(compile(s2_post, "<c11 s2>", "exec"), ns)
        exec(compile(s7_post, "<c11 s7+7.5>", "exec"), ns)
        out11 = so.getvalue()
        exec(compile(s5_12, "<c12 s5+7.5>", "exec"), ns)
        out12 = so.getvalue()
    return out11, out12


m11_a, m12_a = run_mirror(PROBE_BEN)
check("V4a mirrors R-A (healthy): both 5/5",
      "QUALITY CORE glyph-coverage: 5/5" in m11_a
      and "QUALITY CORE glyph-coverage: 5/5" in m12_a)
m11_g, m12_g = run_mirror(FREESERIF)
_x = m11_g.count("❌")
check("V4b mirrors R-G (Latin main): D-2 tofu-semantics ✅ + INFO note; the "
      "single ❌ is exactly §7.5 D-5 (the disclosed blank-notdef fit "
      "artifact — print-only, no gate; measured drawn=37 vs ref=44 at "
      "fit=45/scale=1.25 — production vertical-fit limitation, follow-up)",
      "✅ kana + ASCII glyph coverage (D-2)" in m11_g
      and "basic Latin আছে" in m11_g
      and _x == 1
      and "❌ baseline clamp keeps full glyph (D-5)" in m11_g
      and "❌ baseline clamp keeps full glyph (D-5)" in m12_g
      and "4/5" in m11_g and "4/5" in m12_g,
      m11_g[-300:])


# ── V5 mutation trace on the patched battery ─────────────────
print("\n── V5 mutation trace + hygiene (patched battery, R-G env) ──")
tmp = tempfile.mkdtemp(prefix="rf13v_trace_")
fonts, cfg, reg = make_drive_env(tmp, FREESERIF, VENDORED)
ns = make_ns(cfg, reg, trace=True)
so = io.StringIO()
try:
    exec(compile(SPAN_CORE, "<core>", "exec"), ns)
    with contextlib.redirect_stdout(so):
        exec(compile(SPAN_BATT, "<batt>", "exec"), ns)
except RuntimeError:
    pass
writes = ns["_TRACE"]
vals = ["MISSING" if "MISSING" in w["value"] else "reg" for w in writes]
check("V5a 8 font_fallback writes, value pattern = the 4 pin/finally-restore "
      "pairs (T9 reg/reg, T10 MISSING/reg, T11 MISSING/reg, T12 reg/reg)",
      len(writes) == 8 and vals == ["reg", "reg", "MISSING", "reg",
                                    "MISSING", "reg", "reg", "reg"],
      f"values={vals}")
missing_writes = [w for w in writes if "MISSING" in w["value"]]
check("V5b first /tmp/MISSING write is Test 10's D-4 fixture (AFTER Test 9)",
      len(missing_writes) == 2
      and writes.index(missing_writes[0]) == 2,
      f"missing writes at positions {[writes.index(w) for w in missing_writes]}")
check("V5c post-battery: config restored to Drive JP, _FB_CACHE empty, "
      "fixture residue popped",
      ns["MANGABD_CONFIG"]["rendering"]["font_fallback"] == reg
      and dict(ns["_FB_CACHE"]) == {}
      and not any("MISSING-test-font" in k for k in ns["_FONT_COVERAGE_CACHE"])
      and "fb_load" not in ns["_FONT_ROUTE_WARNED"])

# ── summary ──────────────────────────────────────────────────
print("\n" + "=" * 72)
fails = [n for n, ok in RESULTS if not ok]
print(f"MANGABD-008 B1 RF-13 VERIFY: {len(RESULTS) - len(fails)}/{len(RESULTS)} PASS")
if fails:
    print("FAILED:")
    for n in fails:
        print("  - " + n)
    sys.exit(1)
print("ALL GREEN")
