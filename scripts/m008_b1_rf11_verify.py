#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-11 — verification suite (committed instrument).

Branch mangabd-008-b1 @ b627686 (the Flash RF-10 DELTA CHECK report,
docs-only, notebook-identical to 9b232f0). Delta base for re-derivation:
9b232f0, checked on the NOTEBOOK BLOB.

Owner live-test @ 9b232f0: cell-10 battery STILL 10/12 (Test 9 + Test 12
failing; Test 10 green via the RF-10 explicit missing path) because the
vendored font FILE is absent in the Owner's Colab env — the registry key
resolves to a path that does not exist there. RF-11 = graceful skip for
Tests 9/12 + cell-4 self-heal (_ensure_vendored_font: repo copy →
google/fonts sha-pinned download).

Layers:
  V1  static: branch/HEAD preconditions; scope {4,10} exact (25
      non-target cells byte-identical to 9b232f0); cell-10 §1-§9
      byte-identical (fixtures only); cell-4 delta confined to §8.5
      (pre/post spans byte-identical — loader only); AST 27/27
      warnings-as-errors; writer byte-faithful; non-source fields;
      re-derivation from the 6-patch manifest; vendored font bytes
      untouched; fixture/loader pattern source checks
  V2  cell-4 §8.5 harness (real exec, 6 scenarios):
      S-present    repo checkout at CWD → ensure no-op, registry = repo font
      S-download   no repo, no fonts-dir file → REAL google/fonts download
                   → .partial → sha256-verify → replace; registry = fonts
                   dir file; no .partial residue
      S-wrongbytes Owner-env class: wrong bytes under the fonts-dir
                   NotoSansJP.ttf → overwritten with pinned bytes
      S-copy       repo checkout at a PARENT of CWD → copy branch →
                   sha-verified copy in the fonts dir
      S-fail       repo absent + downloads fail → None + Bengali failure
                   diagnostic + WARN events, never raises; registry keeps
                   the relative candidate path (missing-font WARN block)
      S-badbytes   downloaded bytes fail the sha → final path NEVER
                   created, .partial cleaned
  V3  cell-10 battery matrix (the RF-11 delta proof):
      A  happy path (registry + ambient = real JP): 12/12, 0 skipped
      B  Owner-env class POST-fix (registry = missing relative vendored
         path, CWD outside repo; ambient = loadable-but-wrong bytes at a
         Drive-style path): Tests 9/12 SKIP (no FAIL), 10/11 pass →
         10 passed + 2 skipped = 12 total, SUCCESS verdict + the skip
         status line — the directive's exact signature
      C  BASE (9b232f0) under the same env: Tests 9/12 FAIL (the RF-10
         asserts fire) → 10/12 with 2 FAIL — the Owner live signature,
         proving the delta (pre-fix FAIL vs post-fix SKIP)
      D  registry missing AND ambient genuinely missing: 9/12 SKIP,
         10/11 FAIL as loud env diagnostics (RF-10 R3d contract kept),
         NEEDS FIX verdict, 8 passed + 2 skipped
  V4  cells-11/12 §7.5 glyph-coverage self-checks 5/5 in both cells
      (unchanged bytes, re-proven) + §7.5 byte-identical across mirrors
  V5  m002_sim_v2 = 0 abort sites
  V6  both FONT_FALLBACK_URLS serve the exact pinned sha256 bytes

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
BASE_REF = "9b232f0"
HEAD_REF = "b627686"
BRANCH = "mangabd-008-b1"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_CELLS = Path("/home/z/my-project/cells")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"
SIZE_PIN = 9589900

BEN = FONTS / "NotoSansBengali-Regular.ttf"
JP = FONTS / "NotoSansJP.ttf"
VENDORED = REPO / "assets/fonts/NotoSansJP[wght].ttf"
URL_GH = ("https://github.com/google/fonts/raw/main/ofl/notosansjp/"
          "NotoSansJP%5Bwght%5D.ttf")
URL_JSD = ("https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansjp/"
           "NotoSansJP%5Bwght%5D.ttf")

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
    the MANGABD_ASSETS registry the Run All flow provides via cell 4.
    registry_path: what cell 4's §8.5 actually registered (may be a
    path that does not resolve in THIS environment)."""
    ns = {"__name__": "m008_rf11_harness"}
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


def run_battery(span_core, span_batt, fb_path=None, main_path=None,
                registry_path=None):
    """Exec §3-§8 + §10 battery; returns (per-test dict incl. skips,
    captured stdout, success flag, log extras of 'Cell 10 completed')."""
    ns = make_ns(fb_path=fb_path, main_path=main_path,
                 registry_path=registry_path)
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
        m = re.match(r"^(✅|❌|⚪)\s+(SKIP\s+)?(.*)$", line)
        if m:
            per[m.group(3)] = (m.group(1) == "✅", m.group(1) == "⚪")
    tot = [e for e in ns["MANGABD_EVENTS"]
           if "Cell 10 completed" in e["message"]]
    return per, out, success, (tot[0]["extra"] if tot else {})


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ═══════════════════════════════════════════════════════════════
print("=" * 72)
print("MANGABD-008 B1 RF-11 — VERIFY (branch mangabd-008-b1, base 9b232f0)")
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
check("V1a branch + HEAD == b627686 (the Flash delta report) which "
      "descends from 9b232f0 and carries its exact notebook bytes "
      "(no amend; docs-only commits between allowed)",
      branch_ok and head.startswith(HEAD_REF) and anc
      and nb_blob_head == nb_blob_base,
      f"branch_ok={branch_ok} head={head[:12]} blob={nb_blob_head[:12]}")

raw_post, nb_post, cells_post = load_cells(NB)
raw_base_json = git("show", f"{BASE_REF}:{NB_NAME}")
nb_base = json.loads(raw_base_json)
cells_base = ["".join(c.get("source", [])) for c in nb_base["cells"]
              if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_post[i] != cells_base[i]]
check("V1b scope drift exactly {4, 10} (25 cells byte-identical to 9b232f0)",
      sorted(scope) == [4, 10], f"drift={sorted(scope)}")

marker = "# 10. Self-tests"
pre_span_base = cells_base[10][:cells_base[10].index(marker)]
pre_span_post = cells_post[10][:cells_post[10].index(marker)]
check("V1c cell-10 §1-§9 byte-identical — fixtures ONLY (no source changes)",
      pre_span_base == pre_span_post)

s85_banner = "# 8.5 Japanese fallback font"
cfg_line = 'MANGABD_CONFIG["rendering"]["font_fallback"] = str(fallback_font_path)'
b_pre = cells_base[4][:cells_base[4].rindex("\n# ═", 0, cells_base[4].index(s85_banner)) + 1]
n_pre = cells_post[4][:cells_post[4].rindex("\n# ═", 0, cells_post[4].index(s85_banner)) + 1]
b_post_span = cells_base[4][cells_base[4].index(cfg_line):]
n_post_span = cells_post[4][cells_post[4].index(cfg_line):]
check("V1d cell-4 delta confined to §8.5 (pre-§8.5 + post-§8.5 byte-identical "
      "— loader ONLY)", b_pre == n_pre and b_post_span == n_post_span)

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

with open(REPO / "scripts/m008_b1_rf11_patches.json", encoding="utf-8") as f:
    patches = json.load(f)
re_src = dict(enumerate(cells_base))
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, p["name"]
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1h re-derivation: post == 9b232f0 + exactly the 6 RF-11 patches",
      all(re_src[i] == cells_post[i] for i in range(27)) and len(patches) == 6)

check("V1i vendored font bytes untouched (sha256 == pin)",
      sha256_of(VENDORED) == SHA_PIN and VENDORED.stat().st_size == SIZE_PIN)

b10 = cells_post[10]
b4 = cells_post[4]
batt_src = b10[b10.index(marker):]
check("V1j fixture pattern: run_test_skip defined + used 2x (Tests 9/12) + "
      "shared fixture check once + RF-10 asserts gone + Tests 10/11 "
      "missing-path asserts kept",
      batt_src.count("def run_test_skip") == 1
      and batt_src.count("if not _vendored_jp_present:") == 3
      and batt_src.count("_vendored_jp_present = Path(_vendored_jp).exists()") == 1
      and batt_src.count("assert Path(real_jp_path).exists()") == 0
      and batt_src.count("assert not Path(missing_path).exists()") == 2
      and "tests_total=len(tests) + tests_skipped" in batt_src
      and "tests_skipped=tests_skipped" in batt_src)
check("V1k loader pattern: ensure defined + called BEFORE the candidate "
      "scan; 2 sha-pinned URLs; helper trio",
      b4.count("def _ensure_vendored_font") == 1
      and b4.count("def _find_repo_vendored_font") == 1
      and b4.count("def _download_vendored_font") == 1
      and b4.index("_ensure_vendored_font()\n\nfallback_font_path = None")
          < b4.index("for _fb_cand in")
      and b4.count(URL_GH) == 1 and b4.count(URL_JSD) == 1)
check("V1l registry key still fallback_path (cell-4 L566 contract) + "
      "MANGABD_ASSETS block byte-identical",
      '"fallback_path": str(fallback_font_path),' in b4
      and cells_post[4][cells_post[4].index("MANGABD_ASSETS = {"):] ==
          cells_base[4][cells_base[4].index("MANGABD_ASSETS = {"):])

# ── V2 cell-4 §8.5 harness (real exec) ───────────────────────
print("\n── V2 cell-4 §8.5 self-heal harness (6 scenarios) ──")
span85 = extract_span(cells_post[4], "# 8.5 Japanese fallback font",
                      "# 9. Font + libraqm test")


def run_85(cwd, fonts_dir, urllib_mod=None, pre_seed=None):
    """Exec the §8.5 span verbatim in a fresh namespace under cwd.
    urllib_mod None → the REAL urllib (download/copy scenarios); pass a
    mock object to force download failure classes.
    Returns (namespace, captured stdout, events)."""
    ns = {"__name__": "m008_rf11_cell4_harness"}
    ns["MANGABD_CONFIG"] = {"rendering": {"font_fallback": ""}}
    ns["DIRS"] = {"fonts": Path(fonts_dir)}
    ev = []

    def log_event(message, level="INFO", **extra):
        ev.append({"level": level, "message": message, "extra": extra})

    ns["log_event"] = log_event
    exec("import os\nimport shutil\nfrom pathlib import Path", ns)
    ns["urllib"] = urllib_mod if urllib_mod is not None else real_urllib
    if pre_seed:
        pre_seed(Path(fonts_dir))
    so = io.StringIO()
    cwd_prev = Path.cwd()
    os.chdir(cwd)
    try:
        with contextlib.redirect_stdout(so):
            exec(compile(span85, "<cell4 §8.5>", "exec"), ns)
    finally:
        os.chdir(cwd_prev)
    return ns, so.getvalue(), ev


import urllib.request  # real module for download scenarios + V6
real_urllib = urllib

# S-present: repo checkout at CWD → ensure no-op, registry = repo font
tmp_a = Path(tempfile.mkdtemp())
ns_a, out_a, ev_a = run_85(REPO, tmp_a / "fonts")
reg_a = ns_a["MANGABD_CONFIG"]["rendering"]["font_fallback"]
reg_a_resolved = Path(reg_a) if Path(reg_a).is_absolute() else REPO / reg_a
check("V2a S-present: repo checkout at CWD → no self-heal line, "
      "registry = repo vendored font, sha_ok",
      "self-heal" not in out_a
      and Path(reg_a) == Path("assets/fonts/NotoSansJP[wght].ttf")
      and ns_a["fallback_sha_ok"] is True
      and reg_a_resolved.exists(),
      f"reg={reg_a} out={out_a[-200:]}")

# S-download: no repo anywhere, empty fonts dir → REAL google/fonts download
tmp_b = Path(tempfile.mkdtemp())
tmp_b_fonts = tmp_b / "drive" / "fonts"
tmp_b_fonts.mkdir(parents=True)
ns_b, out_b, ev_b = run_85(tmp_b, tmp_b_fonts)
reg_b = ns_b["MANGABD_CONFIG"]["rendering"]["font_fallback"]
dl_file = tmp_b_fonts / "NotoSansJP.ttf"
check("V2b S-download: no repo → REAL google/fonts download, "
      "sha256-verified, .partial cleaned, registry = fonts-dir file",
      "download + sha256-verified" in out_b
      and dl_file.is_file() and sha256_of(dl_file) == SHA_PIN
      and dl_file.stat().st_size == SIZE_PIN
      and not (tmp_b_fonts / "NotoSansJP.ttf.partial").exists()
      and Path(reg_b) == dl_file and ns_b["fallback_sha_ok"] is True,
      f"reg={reg_b} out={out_b[-300:]}")

# S-wrongbytes: the Owner-env class — wrong bytes under fonts-dir
# NotoSansJP.ttf get overwritten with the pinned bytes
tmp_c = Path(tempfile.mkdtemp())
tmp_c_fonts = tmp_c / "drive" / "fonts"
tmp_c_fonts.mkdir(parents=True)
shutil.copy(BEN, tmp_c_fonts / "NotoSansJP.ttf")   # WRONG bytes (Config F)
ns_c, out_c, ev_c = run_85(tmp_c, tmp_c_fonts)
reg_c = ns_c["MANGABD_CONFIG"]["rendering"]["font_fallback"]
check("V2c S-wrongbytes: fonts-dir wrong bytes overwritten with pinned "
      "bytes (the Owner-env self-heal), replace-info line shown",
      "replace হলো" in out_c
      and sha256_of(tmp_c_fonts / "NotoSansJP.ttf") == SHA_PIN
      and Path(reg_c) == tmp_c_fonts / "NotoSansJP.ttf"
      and ns_c["fallback_sha_ok"] is True,
      f"reg={reg_c} out={out_c[-300:]}")

# S-copy: repo checkout at a PARENT of CWD → copy branch
tmp_d = Path(tempfile.mkdtemp())
(tmp_d / "repo" / "assets" / "fonts").mkdir(parents=True)
shutil.copy(JP, tmp_d / "repo" / "assets" / "fonts" / "NotoSansJP[wght].ttf")
(tmp_d / "repo" / "sub").mkdir()
tmp_d_fonts = tmp_d / "drive" / "fonts"
tmp_d_fonts.mkdir(parents=True)
ns_d, out_d, ev_d = run_85(tmp_d / "repo" / "sub", tmp_d_fonts)
reg_d = ns_d["MANGABD_CONFIG"]["rendering"]["font_fallback"]
check("V2d S-copy: repo at a parent of CWD → sha-verified COPY into the "
      "fonts dir (no download), registry = copied file",
      "repo থেকে copy + sha256-verified" in out_d
      and "Trying:" not in out_d
      and sha256_of(tmp_d_fonts / "NotoSansJP.ttf") == SHA_PIN
      and Path(reg_d) == tmp_d_fonts / "NotoSansJP.ttf"
      and ns_d["fallback_sha_ok"] is True,
      f"reg={reg_d} out={out_d[-300:]}")

# S-fail: repo absent + both URLs fail (mocked urlopen) → None + WARNs,
# never raises; registry keeps the relative candidate path
class _FailUrlopen:
    class request:
        @staticmethod
        def urlopen(*a, **k):
            raise OSError("mock network down")


tmp_e = Path(tempfile.mkdtemp())
tmp_e_fonts = tmp_e / "drive" / "fonts"
tmp_e_fonts.mkdir(parents=True)
ns_e, out_e, ev_e = run_85(tmp_e, tmp_e_fonts, urllib_mod=_FailUrlopen)
reg_e = ns_e["MANGABD_CONFIG"]["rendering"]["font_fallback"]
warns_e = [e["message"] for e in ev_e if e["level"] == "WARN"]
warns_e_txt = " | ".join(warns_e)
check("V2e S-fail: repo absent + downloads fail → Bengali failure "
      "diagnostic + WARN events, never raises, registry keeps the "
      "relative candidate path + the §8.5 missing-font WARN block",
      "self-heal ব্যর্থ" in out_e and "নেটওয়ার্ক দেখো" in out_e
      and "JP fallback font self-heal failed" in warns_e_txt
      and "JP fallback font missing" in warns_e_txt
      and reg_e == "assets/fonts/NotoSansJP[wght].ttf"
      and ns_e["fallback_sha_ok"] is False
      and "আগেই sha-verified" not in out_e,
      f"reg={reg_e} warns={warns_e} out={out_e[-300:]}")

# S-badbytes: downloaded bytes fail the sha → final path NEVER created
class _BadBytesUrlopen:
    class request:
        @staticmethod
        def urlopen(*a, **k):
            class _R:
                def __init__(self):
                    self._data = BEN.read_bytes()
                    self._pos = 0

                def read(self, n=-1):
                    if n is None or n < 0:
                        out = self._data[self._pos:]
                        self._pos = len(self._data)
                        return out
                    out = self._data[self._pos:self._pos + n]
                    self._pos += len(out)
                    return out

                def __enter__(self):
                    return self

                def __exit__(self, *a):
                    return False

                def close(self):
                    pass
            return _R()


tmp_f = Path(tempfile.mkdtemp())
tmp_f_fonts = tmp_f / "drive" / "fonts"
tmp_f_fonts.mkdir(parents=True)
ns_f, out_f, ev_f = run_85(tmp_f, tmp_f_fonts, urllib_mod=_BadBytesUrlopen)
reg_f = ns_f["MANGABD_CONFIG"]["rendering"]["font_fallback"]
check("V2f S-badbytes: sha-mismatched downloads NEVER land on the final "
      "path — both URLs rejected, .partial cleaned, self-heal fails "
      "loud, registry keeps the relative candidate",
      "sha256 মেলে না" in out_f and out_f.count("sha256 মেলে না") == 2
      and not (tmp_f_fonts / "NotoSansJP.ttf").exists()
      and not (tmp_f_fonts / "NotoSansJP.ttf.partial").exists()
      and "self-heal ব্যর্থ" in out_f
      and reg_f == "assets/fonts/NotoSansJP[wght].ttf",
      f"reg={reg_f} out={out_f[-300:]}")

# ── V3 cell-10 battery matrix (RF-11 delta proof) ────────────
print("\n── V3 cell-10 battery matrix (RF-11 delta) ──")
span_core = extract_span(cells_post[10], "# 3. Text helpers",
                         "# 9. Page rendering pipeline")
span_batt = extract_span(cells_post[10], "# 10. Self-tests", None)

# A: happy path — registry + ambient = real JP
perA, outA, succA, totA = run_battery(span_core, span_batt)
check("V3a happy path: 12/12 SUCCESS, 0 skipped",
      succA and totA.get("tests_total") == 12 and totA.get("tests_passed") == 12
      and totA.get("tests_skipped", 0) == 0, f"totals={totA}")

# the Owner-env class, POST-fix: registry = the relative vendored path with
# CWD OUTSIDE the repo (post-self-heal-failure registry state); ambient =
# loadable-but-wrong bytes at a Drive-style path (loads, wrong cmap)
drive_dir = Path(tempfile.mkdtemp()) / "drive" / "MyDrive" / "MangaBD_V12" / "fonts"
drive_dir.mkdir(parents=True)
shutil.copy(BEN, drive_dir / "NotoSansJP.ttf")   # WRONG bytes under the JP name
fb_wrong = drive_dir / "NotoSansJP.ttf"
missing_registry = "assets/fonts/NotoSansJP[wght].ttf"

_cwd = Path.cwd()
_chdir_tmp = Path(tempfile.mkdtemp())
os.chdir(_chdir_tmp)
try:
    perB, outB, succB, totB = run_battery(
        span_core, span_batt, fb_path=fb_wrong, registry_path=missing_registry)

    # C: BASE (9b232f0) under the same env → the Owner live signature
    span_core_base = extract_span(cells_base[10], "# 3. Text helpers",
                                  "# 9. Page rendering pipeline")
    span_batt_base = extract_span(cells_base[10], "# 10. Self-tests", None)
    perC, outC, succC, totC = run_battery(
        span_core_base, span_batt_base, fb_path=fb_wrong,
        registry_path=missing_registry)

    # D: registry missing AND ambient genuinely missing
    perD, outD, succD, totD = run_battery(
        span_core, span_batt, fb_path=missing_registry,
        registry_path=missing_registry)
finally:
    os.chdir(_cwd)

def _st(per, name):
    if name not in per:
        return "absent"
    p, s = per[name]
    return "skip" if s else ("pass" if p else "fail")

T9 = "glyph-coverage routing (D-1/D-2)"
T10 = "JP fallback WARN-never-silent (D-4)"
T11 = "horizontal mixed render: fallback glyphs real (D-3)"
T12 = "tofu detector: JP solid glyph vs main .notdef (D-2)"

check("V3b Owner-env class POST-fix: Tests 9/12 SKIP (no FAIL), Tests "
      "10/11 pass, 10 passed + 2 skipped = 12 total, SUCCESS verdict + "
      "skip status line — the directive's exact signature",
      _st(perB, T9) == "skip" and _st(perB, T12) == "skip"
      and _st(perB, T10) == "pass" and _st(perB, T11) == "pass"
      and totB.get("tests_passed") == 10 and totB.get("tests_total") == 12
      and totB.get("tests_skipped") == 2 and succB
      and outB.count("⚪ SKIP") == 2 and "❌" not in outB
      and "2টি test skipped" in outB
      and "Vendored JP font missing" in outB
      and "Tests 9/12 skipped" in outB,
      f"t9={_st(perB, T9)} t10={_st(perB, T10)} t11={_st(perB, T11)} "
      f"t12={_st(perB, T12)} totals={totB}")

check("V3c BASE (9b232f0) under the same env: Tests 9/12 FAIL (RF-10 "
      "asserts fire) → 10/12 with 2 FAIL — the Owner live signature "
      "reproduced, proving the delta",
      _st(perC, T9) == "fail" and _st(perC, T12) == "fail"
      and _st(perC, T10) == "pass" and _st(perC, T11) == "pass"
      and totC.get("tests_passed") == 10 and totC.get("tests_total") == 12
      and not succC,
      f"t9={_st(perC, T9)} t12={_st(perC, T12)} totals={totC}")

check("V3d registry AND ambient both missing: 9/12 SKIP, 10/11 FAIL as "
      "loud env diagnostics (RF-10 R3d contract kept), NEEDS FIX, "
      "8 passed + 2 skipped",
      _st(perD, T9) == "skip" and _st(perD, T12) == "skip"
      and _st(perD, T10) == "fail" and _st(perD, T11) == "fail"
      and totD.get("tests_passed") == 8 and totD.get("tests_total") == 12
      and totD.get("tests_skipped") == 2 and not succD,
      f"t9={_st(perD, T9)} t10={_st(perD, T10)} t11={_st(perD, T11)} "
      f"t12={_st(perD, T12)} totals={totD}")

# ── V4 cells-11/12 §7.5 self-checks (unchanged bytes) ─────────
print("\n── V4 cells-11/12 §7.5 glyph-coverage self-checks ──")
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
check("V4a cell-11 §7.5 self-checks 5/5 (D-1..D-5 vertical)",
      "QUALITY CORE glyph-coverage: 5/5" in so11.getvalue(),
      so11.getvalue()[-300:])

ns_v12 = make_ns()
exec(compile(span_core, "<cell10 §3-§8>", "exec"), ns_v12)
with contextlib.redirect_stdout(io.StringIO()) as so12:
    exec(compile(s2_12, "<cell12 §2>", "exec"), ns_v12)
    exec(compile(s7_post, "<cell11 §7+§7.5>", "exec"), ns_v12)
    exec(compile(s5_12, "<cell12 §5+§7.5>", "exec"), ns_v12)
check("V4b cell-12 §7.5 self-checks 5/5 (mirror)",
      so12.getvalue().count("QUALITY CORE glyph-coverage: 5/5") >= 1,
      so12.getvalue()[-300:])

v11 = extract_span(cells_post[11], "# ── 7.5)", "# ── 8) pipeline wrap ──")
v12 = extract_span(cells_post[12], "# ── 7.5)", "# ── 6) UI button")
check("V4c §7.5 block byte-identical in cells 11/12", v11 == v12)
check("V4d cells 11/12 byte-identical to 9b232f0 (unchanged by RF-11)",
      cells_post[11] == cells_base[11] and cells_post[12] == cells_base[12])

# ── V5 m002_sim_v2 on the working cells ─────────────────────
print("\n── V5 m002_sim_v2 fresh-kernel simulator ──")
SIM_CELLS.mkdir(exist_ok=True)
for old in SIM_CELLS.glob("cell_*.py"):
    old.unlink()
for i in range(27):
    (SIM_CELLS / f"cell_{i:02d}.py").write_text(cells_post[i], encoding="utf-8")
sim = subprocess.run(["python3", str(SIM)], capture_output=True, text=True)
m_abort = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)",
                    sim.stdout)
check("V5a simulator runs", sim.returncode == 0 and m_abort is not None,
      (sim.stderr or sim.stdout)[-300:])
print(sim.stdout.strip().splitlines()[-1] if sim.stdout.strip() else "")
check("V5b m002_sim_v2 = 0 abort sites",
      m_abort is not None and int(m_abort.group(1)) == 0,
      f"count={m_abort.group(1) if m_abort else 'parse-fail'}")

# ── V6 URL pin proof ─────────────────────────────────────────
print("\n── V6 FONT_FALLBACK_URLS serve the pinned bytes ──")


def _fetch_sha(url):
    tmp_p = Path(tempfile.mkdtemp()) / "probe.ttf"
    with real_urllib.request.urlopen(url, timeout=120) as resp, \
            open(tmp_p, "wb") as fh:
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
    return sha256_of(tmp_p)


sha_gh = _fetch_sha(URL_GH)
check("V6a google/fonts URL serves the exact pinned sha256",
      sha_gh == SHA_PIN, f"sha={sha_gh[:16]}")
sha_jsd = _fetch_sha(URL_JSD)
check("V6b jsdelivr mirror serves the exact pinned sha256",
      sha_jsd == SHA_PIN, f"sha={sha_jsd[:16]}")

# ── summary ──────────────────────────────────────────────────
print("\n" + "=" * 72)
fails = [n for n, ok in RESULTS if not ok]
print(f"MANGABD-008 B1 RF-11 VERIFY: {len(RESULTS) - len(fails)}/{len(RESULTS)} PASS")
if fails:
    print("FAILED:")
    for n in fails:
        print("  - " + n)
    sys.exit(1)
print("ALL GREEN")
