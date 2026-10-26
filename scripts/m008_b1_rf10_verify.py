#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-10 — verification suite (workspace instrument).

Branch mangabd-008-b1, delta base b848c75 (Phase C WIP commit). The
Flash Phase D report commit 33d5183 (docs-only, GLM_5_3_FLASH.md;
notebook-identical to b848c75) sits between the base and this
fix — the base invariant is checked on the NOTEBOOK BLOB, not the
commit hash, so docs-only commits in between are acceptable.
The Owner's live test @ b848c75 found the cell-10 battery 10/12
(Test 9 routing + Test 12 tofu detector failing) with the
Test-10/11 degradation fixture deriving
<drive fonts dir>/MISSING-NotoSansJP.ttf — RF-10 fixes the
fixtures (real vendored font for D-1/D-2; explicit missing path
for D-4/D-3 degradation; cell-10 self-tests ONLY).

Layers:
  R1  static: scope {10} exact vs b848c75 (26 non-target
      byte-identical); cell-10 §1-§9 byte-identical (fixtures-only
      proof); AST 27/27 warnings-as-errors; writer byte-faithful;
      non-source fields; re-derivation from the 4-patch manifest;
      vendored font bytes untouched; fixture-pattern source checks
  R2  battery: cell-10 §3-§8 + §10 exec -> 12/12 SUCCESS
      (MANGABD_ASSETS registry injected per the Run All contract)
  R3  ambient-independence matrix (the RF-10 delta proof):
      F-pre   b848c75 battery under a loadable-but-wrong ambient
              fallback (Bengali bytes at a Drive-style
              NotoSansJP.ttf) REPRODUCES the Owner's exact live
              signature: 9 fail + 12 fail + 10/11 pass = 10/12
      F-post  RF-10 battery under the same ambient: 12/12
      B-post  RF-10 battery, ambient = real JP at a Drive-style
              path: 12/12
      D-post  RF-10 battery, ambient = the relative vendored path with
              CWD OUTSIDE the repo (genuinely missing): Tests 9/12 still
              green via the registry pin (the D-1/D-2 fixtures are
              ambient-fallback-independent); Tests 10/11 correctly fail
              as env diagnostics
  R4  cells-11/12 §7.5 glyph-coverage self-checks 5/5 in both
      cells (unchanged bytes, re-proven on the working tree)
  R5  m002_sim_v2 fresh-kernel simulator on the working cells:
      0 abort sites

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
BASE_REF = "b848c75"
BRANCH = "mangabd-008-b1"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_CELLS = Path("/home/z/my-project/cells")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"

BEN = FONTS / "NotoSansBengali-Regular.ttf"
JP = FONTS / "NotoSansJP.ttf"

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


def make_ns(fb_path=None, main_path=None, fonts_dir=FONTS):
    """Battery harness namespace (the Phase C make_ns contract) +
    the MANGABD_ASSETS registry the Run All flow provides via cell 4."""
    ns = {"__name__": "m008_rf10_harness"}
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
            "fallback_path": str(JP),  # cell-4 registry: sha-verified vendored
            "fallback_sha256": SHA_PIN,
            "fallback_size": 9589900,
            "fallback_sha_ok": True,
            "fallback_license": "OFL-1.1",
        },
    }
    exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
         "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)
    return ns


def run_battery(span_core, span_batt, fb_path=None, main_path=None):
    """Exec §3-§8 + §10 battery; returns (per-test dict, n_pass, n_total,
    success_flag, captured stdout)."""
    ns = make_ns(fb_path=fb_path, main_path=main_path)
    so = io.StringIO()
    success = False
    try:
        exec(compile(span_core, "<cell10 core>", "exec"), ns)
        with contextlib.redirect_stdout(so):
            exec(compile(span_batt, "<cell10 battery>", "exec"), ns)
        success = True
    except RuntimeError as exc:
        assert "Cell 10 self-tests failed" in str(exc), exc
    out = so.getvalue()
    per = {}
    for line in out.splitlines():
        line = line.strip()
        m = re.match(r"^(✅|❌)\s+(.*)$", line)
        if m:
            per[m.group(2)] = (m.group(1) == "✅")
    tot = [e for e in ns["MANGABD_EVENTS"]
           if "Cell 10 completed" in e["message"]]
    return per, out, success, (tot[0]["extra"] if tot else {})


# ═══════════════════════════════════════════════════════════════
print("=" * 72)
print("MANGABD-008 B1 RF-10 — VERIFY (branch mangabd-008-b1, base b848c75)")
print("=" * 72)

# ── R1 static integrity ──────────────────────────────────────
print("\n── R1 static integrity ──")
branch_ok = git("branch", "--show-current").strip() == BRANCH
nb_blob_head = git("rev-parse", f"HEAD:{NB_NAME}").strip()
nb_blob_base = git("rev-parse", f"{BASE_REF}:{NB_NAME}").strip()
anc = subprocess.run(
    ["git", "-C", str(REPO), "merge-base", "--is-ancestor",
     BASE_REF, "HEAD"], capture_output=True).returncode == 0
check("R1a branch + HEAD descends from b848c75 and carries its exact "
      "notebook bytes (no amend; docs-only commits between allowed)",
      branch_ok and anc and nb_blob_head == nb_blob_base,
      f"branch_ok={branch_ok} ancestor={anc} blob={nb_blob_head[:12]}")

raw_post, nb_post, cells_post = load_cells(NB)
raw_base_json = git("show", f"{BASE_REF}:{NB_NAME}")
nb_base = json.loads(raw_base_json)
cells_base = ["".join(c.get("source", [])) for c in nb_base["cells"]
              if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_post[i] != cells_base[i]]
check("R1b scope drift exactly {10} (26 cells byte-identical to b848c75)",
      sorted(scope) == [10], f"drift={sorted(scope)}")

marker = "# 10. Self-tests"
pre_span_base = cells_base[10][:cells_base[10].index(marker)]
pre_span_post = cells_post[10][:cells_post[10].index(marker)]
check("R1c cell-10 §1-§9 byte-identical — fixtures ONLY (no source changes)",
      pre_span_base == pre_span_post)

for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        compile(cells_post[i], f"cell_{i:02d}.py", "exec")
check("R1d AST 27/27 (warnings-as-errors)", True)

rt = json.dumps(nb_post, indent=2, ensure_ascii=False)
check("R1e json writer byte-faithful on the working file",
      rt.encode("utf-8") == raw_post)

ok_fields = all(
    {k: v for k, v in nb_base["cells"][i].items() if k != "source"} ==
    {k: v for k, v in nb_post["cells"][i].items() if k != "source"}
    for i in range(27))
top_ok = ({k: v for k, v in nb_base.items() if k != "cells"} ==
          {k: v for k, v in nb_post.items() if k != "cells"})
check("R1f non-source + top-level notebook fields identical",
      ok_fields and top_ok)

with open(REPO / "scripts/m008_b1_rf10_patches.json", encoding="utf-8") as f:
    patches = json.load(f)
re_src = dict(enumerate(cells_base))
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, p["name"]
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("R1g re-derivation: post == b848c75 + exactly the 4 RF-10 patches",
      all(re_src[i] == cells_post[i] for i in range(27)) and len(patches) == 4)

vf = REPO / "assets/fonts/NotoSansJP[wght].ttf"
check("R1h vendored font bytes untouched (sha256 == pin)",
      hashlib.sha256(vf.read_bytes()).hexdigest() == SHA_PIN
      and vf.stat().st_size == 9589900)

batt_src = cells_post[10][cells_post[10].index(marker):]
check("R1i fixture pattern in source: 2x registry pin (Tests 9/12) + "
      "2x explicit /tmp missing path (Tests 10/11)",
      batt_src.count('MANGABD_ASSETS["fonts"]["fallback_path"]') == 2
      and batt_src.count("/tmp/MISSING-test-font.ttf") == 2
      and "MISSING-NotoSansJP.ttf" not in cells_post[10]
      and "Path(fb_real).parent" not in batt_src)
check("R1j registry pin NOT present in the source span (§1-§9)",
      'MANGABD_ASSETS["fonts"]["fallback_path"]' not in pre_span_post)

# ── R2 battery: baseline ambient ────────────────────────────
print("\n── R2 cell-10 battery (baseline ambient: real JP fallback) ──")
span_core = extract_span(cells_post[10], "# 3. Text helpers",
                         "# 9. Page rendering pipeline")
span_batt = extract_span(cells_post[10], "# 10. Self-tests", None)
per, out, success, tot = run_battery(span_core, span_batt)
check("R2a cell-10 battery 12/12 SUCCESS",
      success and tot.get("tests_total") == 12 and tot.get("tests_passed") == 12,
      f"totals={tot} success={success}")
check("R2b all four MANGABD-008 tests green (9/10/11/12)",
      per.get("glyph-coverage routing (D-1/D-2)") is True
      and per.get("JP fallback WARN-never-silent (D-4)") is True
      and per.get("horizontal mixed render: fallback glyphs real (D-3)") is True
      and per.get("tofu detector: JP solid glyph vs main .notdef (D-2)") is True)

# ── R3 ambient-independence matrix ───────────────────────────
print("\n── R3 ambient-fallback independence matrix (RF-10 delta) ──")
# Config F: loadable-but-wrong ambient fallback — Bengali bytes under a
# Drive-style NotoSansJP.ttf name (the reproduced Owner live signature)
drive_dir = Path(tempfile.mkdtemp()) / "drive" / "MyDrive" / "MangaBD_V12" / "fonts"
drive_dir.mkdir(parents=True)
shutil.copy(BEN, drive_dir / "NotoSansJP.ttf")  # WRONG bytes under the JP name
fb_wrong = drive_dir / "NotoSansJP.ttf"

span_core_base = extract_span(cells_base[10], "# 3. Text helpers",
                              "# 9. Page rendering pipeline")
span_batt_base = extract_span(cells_base[10], "# 10. Self-tests", None)
perF_pre, outF_pre, succF_pre, totF_pre = run_battery(
    span_core_base, span_batt_base, fb_path=fb_wrong)
check("R3a PRE-fix @ wrong-bytes ambient reproduces the Owner live test: "
      "9 ❌ + 12 ❌, 10 ✅ + 11 ✅ = 10/12",
      perF_pre.get("glyph-coverage routing (D-1/D-2)") is False
      and perF_pre.get("tofu detector: JP solid glyph vs main .notdef (D-2)") is False
      and perF_pre.get("JP fallback WARN-never-silent (D-4)") is True
      and perF_pre.get("horizontal mixed render: fallback glyphs real (D-3)") is True
      and totF_pre.get("tests_passed") == 10 and totF_pre.get("tests_total") == 12,
      f"totals={totF_pre}")

perF_post, outF_post, succF_post, totF_post = run_battery(
    span_core, span_batt, fb_path=fb_wrong)
check("R3b POST-fix @ wrong-bytes ambient: 12/12 SUCCESS",
      succF_post and totF_post.get("tests_passed") == 12,
      f"totals={totF_post}")

shutil.copy(JP, drive_dir / "NotoSansJP.ttf")  # real bytes, Drive-style path
perB_post, outB_post, succB_post, totB_post = run_battery(
    span_core, span_batt, fb_path=drive_dir / "NotoSansJP.ttf")
check("R3c POST-fix @ real JP on a Drive-style path: 12/12 SUCCESS",
      succB_post and totB_post.get("tests_passed") == 12,
      f"totals={totB_post}")

perD_post, outD_post, succD_post, totD_post = None, None, None, None
# run from OUTSIDE the repo so the relative vendored path does not resolve
# (the notebook Run All case where the repo is not at CWD)
_cwd = Path.cwd()
_chdir_tmp = Path(tempfile.mkdtemp())
os.chdir(_chdir_tmp)
try:
    perD_post, outD_post, succD_post, totD_post = run_battery(
        span_core, span_batt, fb_path="assets/fonts/NotoSansJP[wght].ttf")
finally:
    os.chdir(_cwd)
check("R3d POST-fix @ MISSING ambient (CWD outside the repo): Tests 9/12 "
      "green via the registry pin (ambient-fallback-independent); "
      "10/11 fail as correct env diagnostics",
      perD_post.get("glyph-coverage routing (D-1/D-2)") is True
      and perD_post.get("tofu detector: JP solid glyph vs main .notdef (D-2)") is True
      and perD_post.get("JP fallback WARN-never-silent (D-4)") is False
      and perD_post.get("horizontal mixed render: fallback glyphs real (D-3)") is False
      and totD_post.get("tests_passed") == 10,
      f"totals={totD_post}")

# ── R4 cells-11/12 §7.5 self-checks (unchanged bytes) ────────
print("\n── R4 cells-11/12 §7.5 glyph-coverage self-checks ──")
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
check("R4a cell-11 §7.5 self-checks 5/5 (D-1..D-5 vertical)",
      "QUALITY CORE glyph-coverage: 5/5" in so11.getvalue(),
      so11.getvalue()[-300:])

ns_v12 = make_ns()
exec(compile(span_core, "<cell10 §3-§8>", "exec"), ns_v12)
with contextlib.redirect_stdout(io.StringIO()) as so12:
    exec(compile(s2_12, "<cell12 §2>", "exec"), ns_v12)
    exec(compile(s7_post, "<cell11 §7+§7.5>", "exec"), ns_v12)
    exec(compile(s5_12, "<cell12 §5+§7.5>", "exec"), ns_v12)
check("R4b cell-12 §7.5 self-checks 5/5 (mirror)",
      so12.getvalue().count("QUALITY CORE glyph-coverage: 5/5") >= 1,
      so12.getvalue()[-300:])

v11 = extract_span(cells_post[11], "# ── 7.5)", "# ── 8) pipeline wrap ──")
v12 = extract_span(cells_post[12], "# ── 7.5)", "# ── 6) UI button")
check("R4c §7.5 block byte-identical in cells 11/12", v11 == v12)
check("R4d cells 11/12 byte-identical to b848c75 (unchanged by RF-10)",
      cells_post[11] == cells_base[11] and cells_post[12] == cells_base[12])

# ── R5 m002_sim_v2 on the working cells ─────────────────────
print("\n── R5 m002_sim_v2 fresh-kernel simulator ──")
SIM_CELLS.mkdir(exist_ok=True)
for old in SIM_CELLS.glob("cell_*.py"):
    old.unlink()
for i in range(27):
    (SIM_CELLS / f"cell_{i:02d}.py").write_text(cells_post[i], encoding="utf-8")
sim = subprocess.run(["python3", str(SIM)], capture_output=True, text=True)
m_abort = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)",
                    sim.stdout)
check("R5a simulator runs", sim.returncode == 0 and m_abort is not None,
      (sim.stderr or sim.stdout)[-300:])
print(sim.stdout.strip().splitlines()[-1] if sim.stdout.strip() else "")
check("R5b m002_sim_v2 = 0 abort sites",
      m_abort is not None and int(m_abort.group(1)) == 0,
      f"count={m_abort.group(1) if m_abort else 'parse-fail'}")

# ── summary ──────────────────────────────────────────────────
print("\n" + "=" * 72)
fails = [n for n, ok in RESULTS if not ok]
print(f"MANGABD-008 B1 RF-10 VERIFY: {len(RESULTS) - len(fails)}/{len(RESULTS)} PASS")
if fails:
    print("FAILED:")
    for n in fails:
        print("  - " + n)
    sys.exit(1)
print("ALL GREEN")
