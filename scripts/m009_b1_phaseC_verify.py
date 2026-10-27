#!/usr/bin/env python3
r"""MANGABD-009 B1 Phase C — verification instrument.

Branch mangabd-009-b1, base = main @ d394947. Verifies the smart-bubble-fill
Phase C against the 4-ruling surface (R1 sequence/B1, R2 cap 48, R3 trigger
0.60, R4 target 0.85 honest fallback):

  V1  static integrity: scope exactly {10,11,12}; reading-order cells
      13/15/23 byte-identical; AST 27/27 warnings-as-errors; re-derivation
      from scripts/m009_b1_phaseC_patches.json; non-source fields identical;
      secret scan; cap-48 preservation; cells 11/12 delta = C-1 wrapper only
  V2  §2 config exec: knob defaults == the ruling values
  V3  cell-10 battery: 15/15 HARD (12 existing + B1 13/14/15)
  V4  B1 decision on the archives (S003/S007, all 12 regions): trigger
      classification + guard machinery + fill monotonicity vs Phase A
  V5  render_page pre-vs-post on BOTH archives: kept-current regions
      byte-identical, triggered regions re-laid-out with MORE ink;
      bubble_fill meta disclosure; kill-switch (enable=False) == pre bytes
  V6  C-1 wrapper chain: W12(W11(orig)) forwards fit_result (no
      TypeError); vertical arm untouched
  V7  N-1 dynamic: get_font missing-font -> default font + loud WARN +
      log_event ERROR captured
  V8  m002_sim_v2 fresh-kernel simulator on the POST cells: 0 abort sites

Fonts: /home/z/my-project/m008_probe/fonts (real NotoSansBengali-Regular +
NotoSansJP — the M008-verified pair; the m009_work Regular/Bold are HTML
error pages, the N-1 evidence).
"""
import contextlib
import difflib
import io
import json
import re
import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from PIL import Image as PILImage

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "d394947"
BRANCH = "mangabd-009-b1"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
S003 = REPO / "samples" / "S003_batch2"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
POST_CELLS_DIR = Path("/home/z/my-project/cells_m009_post")
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")

RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    print(("PASS  " if ok else "FAIL  ") + name
          + (f"  [{detail}]" if detail else ""))
    RESULTS.append((name, ok))
    return ok


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


def extract_wrapper_span(src, guard_name):
    """The V-3 wrapper block: `if not globals().get(GUARD):` .. `= True`."""
    lines = src.split("\n")
    si = next(i for i, l in enumerate(lines)
              if f'globals().get("{guard_name}")' in l)
    ei = next(i for i in range(si, len(lines))
              if f'globals()["{guard_name}"] = True' in lines[i])
    return "\n".join(lines[si:ei + 1])


def make_ns(config_extra=None):
    ns = {"__name__": "m009_phaseC_harness"}
    ns["MANGABD_CONFIG"] = {
        "rendering": {
            "font_size_min": 8, "font_size_max": 48, "font_size_default": 24,
            "line_spacing_factor": 1.18, "padding_ratio": 0.08,
            "use_grapheme_safe_wrap": True, "use_background_aware_color": True,
            "allow_synthetic_bold": True,
            "stroke_width_bubble": 0, "stroke_width_thought": 0,
            "stroke_width_narrator": 0, "stroke_width_sfx": 1,
            "stroke_width_overlay": 1,
            "default_bubble_color": [0, 0, 0],
            "default_sfx_color": [255, 255, 255],
            "default_narrator_color": [0, 0, 0],
            "default_overlay_color": [255, 255, 255],
            "preview_max_width": 900,
            "font_regular": str(FONTS / "NotoSansBengali-Regular.ttf"),
            "font_bold": str(FONTS / "NotoSansBengali-Regular.ttf"),
            "font_fallback": str(FONTS / "NotoSansJP.ttf"),
            "vertical_rotate": -90,
        },
        "detection": {}, "inpainting": {},
    }
    if config_extra:
        ns["MANGABD_CONFIG"]["rendering"].update(config_extra)
    ev = []
    ns["MANGABD_EVENTS"] = ev

    def log_event(message, level="INFO", **extra):
        ev.append({"level": level, "message": message, "extra": extra})

    ns["log_event"] = log_event
    # cell-4 §8.5 registry stub (battery Tests 9/10/12 fixture): the
    # M008-verified real JP font pair — present => Tests 9/12 run, not skip
    ns["MANGABD_ASSETS"] = {"fonts": {
        "fallback_path": str(FONTS / "NotoSansJP.ttf"),
        "fallback_sha_ok": True, "fallback_size": 0,
        "fallback_license": "",
    }}
    exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
         "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)
    return ns


def install_render_stubs(ns, page_id, inpainted_bgr):
    """Minimal storage-layer stubs so render_page runs against an archive."""
    ns["get_page"] = lambda pid, required=True: {"page_id": pid}
    ns["is_stage_done"] = lambda pid, stage: False
    ns["load_image_artifact"] = (
        lambda pid, kind: inpainted_bgr.copy() if kind == "inpainted" else None)
    saved = {}

    def save_image_artifact(pid, kind, img, quality=95):
        if kind == "final":
            # render_page saves the PIL canvas — store as an RGB array so
            # pre/post byte comparisons are numpy-exact
            saved[("final", pid)] = (
                np.array(img) if hasattr(img, "size") else np.asarray(img))

    ns["save_image_artifact"] = save_image_artifact
    ns["save_translation_df"] = lambda: None
    ns["load_translation_df"] = lambda: None
    ns["reset_page"] = lambda pid, from_stage=None: None
    metas = {}

    def mark_stage_done(pid, stage, meta=None):
        metas[pid] = dict(meta or {})

    ns["mark_stage_done"] = mark_stage_done
    ns["_harness_saved"] = saved
    ns["_harness_metas"] = metas
    return ns


def build_translation_df(page_id, det_rows, tr_rows):
    tr_by_id = {int(r["id"]): r for r in tr_rows}
    recs = []
    for d in det_rows:
        t = tr_by_id.get(int(d["id"]), {})
        recs.append({
            "page_id": page_id,
            "id": int(d["id"]),
            "x": int(d["x"]), "y": int(d["y"]),
            "width": int(d["width"]), "height": int(d["height"]),
            "angle": float(d.get("angle", 0.0)),
            "region_type": d.get("region_type", "overlay"),
            "translated_text": str(t.get("translated_text", "") or ""),
            "bengali_valid": bool(t.get("bengali_valid", False)),
            "status": t.get("status", ""),
        })
    return pd.DataFrame(recs)


def load_sample(sid):
    """(detections, translation rows, inpainted BGR) for S003 / S007."""
    if sid == "S003":
        det = json.load(open(S003 / "detections.json"))
        tr = json.load(open(S003 / "translation.json"))
        rows = tr if isinstance(tr, list) else tr.get("rows", [])
        img = cv2.imread(str(S003 / "inpainted.png"), cv2.IMREAD_COLOR)
        return det, rows, img
    with zipfile.ZipFile(S007_ZIP) as z:
        def rd(name):
            cand = [n for n in z.namelist() if n.endswith(name)]
            return z.read(cand[0])
        det = json.loads(rd("detections.json"))
        tr = json.loads(rd("translation.json"))
        rows = tr if isinstance(tr, list) else tr.get("rows", [])
        arr = cv2.imdecode(np.frombuffer(rd("inpainted.png"), np.uint8),
                           cv2.IMREAD_COLOR)
        return det, rows, arr


print("=" * 72)
print("MANGABD-009 B1 PHASE C — VERIFY (branch mangabd-009-b1)")
print("=" * 72)

# ════════════════════════════════════════════════════════════════════
# V1 — static integrity
# ════════════════════════════════════════════════════════════════════
print("\n── V1 static integrity ──")
check("V1a branch mangabd-009-b1",
      git("branch", "--show-current").strip() == BRANCH)
raw_post, nb_post, cells_post = load_cells(NB)
raw_pre = git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8")
nb_pre = json.loads(raw_pre.decode("utf-8"))
cells_pre = ["".join(c.get("source", [])) for c in nb_pre["cells"]
             if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_post[i] != cells_pre[i]]
check("V1b scope drift exactly {10, 11, 12}", sorted(scope) == [10, 11, 12],
      f"drift={sorted(scope)}")
for i in (13, 15, 23):
    check(f"V1c reading-order cell {i} byte-identical",
          cells_post[i] == cells_pre[i])

for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(cells_post[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL cell {i} warning-as-error: {w}")
check("V1d AST compile 27/27 (warnings-as-errors)", True)

manifest = json.loads((REPO / "scripts" / "m009_b1_phaseC_patches.json")
                      .read_text(encoding="utf-8"))
re_src = dict(enumerate(cells_pre))
for p in manifest:
    cnt = re_src[p["cell"]].count(p["old"])
    assert cnt == 1, f"re-derivation anchor {p['name']}: {cnt}x"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1e re-derivation: post == pre + exactly the manifest patches",
      all(re_src[i] == cells_post[i] for i in range(27)))

nb_check = json.loads(raw_post.decode("utf-8"))
non_src_ok = all(
    {k: v for k, v in nb_pre["cells"][i].items() if k != "source"}
    == {k: v for k, v in nb_check["cells"][i].items() if k != "source"}
    for i in range(len(nb_pre["cells"])))
top_ok = ({k: v for k, v in nb_pre.items() if k != "cells"}
          == {k: v for k, v in nb_check.items() if k != "cells"})
check("V1f non-source + top-level fields identical", non_src_ok and top_ok)

added = "\n".join(p["new"] for p in manifest if p["cell"] in {10, 11, 12})
secret_pats = [r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
               r"sk-[A-Za-z0-9]{20,}", r"AIza[0-9A-Za-z_\-]{20,}",
               r"hf_[A-Za-z0-9]{20,}", r"Bearer\s+[A-Za-z0-9._\-]{20,}"]
secrets = [p for p in secret_pats if re.search(p, added)]
check("V1g secret scan on added lines (0 hits)", not secrets, str(secrets))

check("V1h cap 48 preserved (Ruling 2)",
      'setdefault("font_size_max", 48)' in cells_post[10]
      and cells_post[10].count('setdefault("font_size_max", 48)')
      == cells_pre[10].count('setdefault("font_size_max", 48)'))

for i in (11, 12):
    d = [l for l in difflib.unified_diff(cells_pre[i].splitlines(),
                                         cells_post[i].splitlines(),
                                         lineterm="", n=0)
         if l[:1] in "+-" and not l.startswith(("+++", "---"))]
    olds, news = set(), set()
    for p in manifest:
        if p["cell"] == i:
            olds.update(p["old"].split("\n"))
            news.update(p["new"].split("\n"))
    minus_ok = all(l[1:] in olds for l in d if l[0] == "-")
    plus_ok = all(l[1:] in news for l in d if l[0] == "+")
    vert_untouched = (
        "_qc_render_vertical(image_pil, text, x, y, w, h, b,"
        in cells_post[i]
        and cells_post[i].count(
            "w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0") == 1)
    check(f"V1i cell {i} delta confined to the C-1 wrapper patch "
          f"(vertical arm untouched)",
          minus_ok and plus_ok and len(d) <= 14 and vert_untouched,
          f"{len(d)} diff lines")

# ════════════════════════════════════════════════════════════════════
# V2 — §2 config exec (ruling values)
# ════════════════════════════════════════════════════════════════════
print("\n── V2 config knobs ──")
span_cfg_post = extract_span(cells_post[10], "# 2. Rendering config defaults",
                             "# 3. Text helpers")
span_cfg_pre = extract_span(cells_pre[10], "# 2. Rendering config defaults",
                            "# 3. Text helpers")
ns_cfg = make_ns()
exec(compile(span_cfg_post, "<cell10 §2 post>", "exec"), ns_cfg)
rc = ns_cfg["MANGABD_CONFIG"]["rendering"]
check("V2a bubble_fill_enable default True",
      rc.get("bubble_fill_enable") is True)
check("V2b bubble_fill_trigger default 0.60 (Ruling 3)",
      rc.get("bubble_fill_trigger") == 0.60)
check("V2c bubble_fill_target default 0.85 (Ruling 4)",
      rc.get("bubble_fill_target") == 0.85)
check("V2d bubble_fill_margin_ratio default 0.03",
      rc.get("bubble_fill_margin_ratio") == 0.03)
check("V2e region_types default [bubble, thought]",
      rc.get("bubble_fill_region_types") == ["bubble", "thought"])
check("V2f font_size_max still 48 (Ruling 2)", rc.get("font_size_max") == 48)

# ════════════════════════════════════════════════════════════════════
# V3 — cell-10 battery 15/15
# ════════════════════════════════════════════════════════════════════
print("\n── V3 cell-10 battery ──")
span10_post = extract_span(cells_post[10], "# 3. Text helpers",
                           "# 9. Page rendering pipeline")
span10_pre = extract_span(cells_pre[10], "# 3. Text helpers",
                          "# 9. Page rendering pipeline")
batt_post = extract_span(cells_post[10], "# 10. Self-tests", None)
# §9 (render pipeline: render_page/render_all_pages) — exec'd separately
# in V5 with storage stubs; battery needs §9's render_is_special_marker etc
# all live in §3-§8, render_page itself is not called by the battery.
span9_post = extract_span(cells_post[10], "# 9. Page rendering pipeline",
                          "# 10. Self-tests")
span9_pre = extract_span(cells_pre[10], "# 9. Page rendering pipeline",
                         "# 10. Self-tests")

ns_post = make_ns()
exec(compile(span_cfg_post, "<cell10 §2 post>", "exec"), ns_post)
exec(compile(span10_post, "<cell10 §3-§8 post>", "exec"), ns_post)
ns_pre = make_ns()
exec(compile(span_cfg_pre, "<cell10 §2 pre>", "exec"), ns_pre)
exec(compile(span10_pre, "<cell10 §3-§8 pre>", "exec"), ns_pre)

with contextlib.redirect_stdout(io.StringIO()) as so:
    try:
        exec(compile(batt_post, "<cell10 §10 battery>", "exec"), ns_post)
    except Exception:
        pass  # battery raises RuntimeError on FAIL — output inspected below
out_batt = so.getvalue()
if "Cell 10 result: SUCCESS" not in out_batt:
    print(out_batt[-4000:])
tot = [e for e in ns_post["MANGABD_EVENTS"]
       if "Cell 10 completed" in e["message"]]
check("V3a cell-10 battery 15/15 HARD (12 existing + B1 13/14/15)",
      "Cell 10 result: SUCCESS" in out_batt
      and tot and tot[0]["extra"]["tests_total"] == 15
      and tot[0]["extra"]["tests_passed"] == 15
      and tot[0]["extra"]["tests_skipped"] == 0,
      (tot[0]["extra"] if tot else "no completion event"))
for tname, needle in (
        ("Test 13 B1 synthetic ellipse", "B1 mask fill: synthetic ellipse"),
        ("Test 14 B1 guards", "B1 guards: trigger + kill-switch"),
        ("Test 15 N-1 loud degrade", "get_font loud degradation")):
    check(f"V3b {tname} ✅", f"✅ {needle}" in out_batt)

# ════════════════════════════════════════════════════════════════════
# V4 — B1 decision on the archives (the ruling surface)
# ════════════════════════════════════════════════════════════════════
print("\n── V4 B1 decision on archives ──")
ARCH = {}
for sid in ("S003", "S007"):
    det, rows, img = load_sample(sid)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    tr_by_id = {int(r["id"]): r for r in rows}
    ARCH[sid] = {"det": det, "gray": gray, "tr": tr_by_id}

DEC = {}
print(f"  {'region':<10} {'cur sz/ln/blkU':>18} -> {'new sz/ln/blkU':>18}"
      f"  mode/guard")
for sid in ("S003", "S007"):
    a = ARCH[sid]
    for d in a["det"]:
        rid = int(d["id"])
        text = str(a["tr"].get(rid, {}).get("translated_text", "") or "").strip()
        if not text:
            continue
        dec = ns_post["bubble_fill_decision"](
            text, int(d["x"]), int(d["y"]), int(d["width"]), int(d["height"]),
            image_gray=a["gray"], bold=False, angle=float(d.get("angle", 0.0)),
            region_type=d.get("region_type", "overlay"))
        DEC[(sid, rid)] = dec
        cur = (f"{dec.get('cur_size')}/{dec.get('cur_lines')}"
               f"/{dec.get('cur_block_fill_usable')}")
        new = (f"{dec.get('font_size')}/"
               f"{len(dec.get('lines') or [])}"
               f"/{dec.get('block_fill_usable')}")
        print(f"  {sid}-R{rid:<3} {cur:>18} -> {new:>18}"
              f"  {dec['mode']}/{dec.get('guard')}")

EARLY_GUARDS = {"disabled", "rotated", "vertical_note", "region_type",
                "degenerate"}
ok_struct = True
for (sid, rid), dec in DEC.items():
    if dec["mode"] == "mask":
        ok_struct &= dec.get("font_size", 0) >= dec.get("cur_size", 10 ** 6)
        ok_struct &= dec.get("block_fill_usable", -1) >= \
            dec.get("cur_block_fill_usable", 10 ** 6)
        ok_struct &= isinstance(dec.get("cap_bound"), bool)
        ok_struct &= dec.get("start_y") is not None
        ok_struct &= len(dec.get("band_centers") or []) == len(dec["lines"])
        ok_struct &= len(dec.get("band_widths") or []) == len(dec["lines"])
    else:
        ok_struct &= dec.get("guard") is not None
        if dec.get("guard") not in EARLY_GUARDS:
            ok_struct &= dec.get("cur_size", 0) > 0
check("V4a decision structure (guards/metrics/positioning) sound", ok_struct)

# Policy check (Ruling 3): mask mode IFF measured cur_blkU < 0.60 —
# font-robust, unlike a fixed region list. The production Regular font +
# measure_text(textbbox) shift borderline regions by +-0.01..0.03 vs the
# Phase A instrument (VF font + textlength): S003-R6 .583->.611,
# S007-R4 .615->.630, S007-R5 .595->.608 — all three land just ABOVE the
# trigger here and are correctly kept (disclosed for the Phase C record).
under = {k for k, d in DEC.items()
         if d.get("cur_block_fill_usable") is not None
         and d["cur_block_fill_usable"] < 0.60}
mask_set = {k for k, d in DEC.items() if d["mode"] == "mask"}
check("V4b policy: mask mode exactly iff cur_blkU < 0.60 trigger",
      under == mask_set,
      f"under={sorted(under)} mask={sorted(mask_set)}")

# Robust under-filled class (below trigger under BOTH fonts) must improve:
# Phase A: R4 .473 R5 .522 S007-R2 .575; this run: .479/.555/.584
robust = [("S003", 4), ("S003", 5), ("S007", 2)]
check("V4c robust under-filled class triggers mask mode",
      all(k in mask_set for k in robust),
      str({k: DEC[k].get("guard") for k in robust if k not in mask_set}))

# Phase A robust kept class stays current (trigger guard)
must_keep = [("S003", 2), ("S003", 3), ("S007", 3)]
ok_keep = all(DEC[k]["mode"] == "current" and DEC[k]["guard"] in
              ("trigger", "size_guard") for k in must_keep)
check("V4d Phase A kept class stays current (trigger/size guard)",
      ok_keep, str({k: (DEC[k]["mode"], DEC[k]["guard"]) for k in must_keep
                    if DEC[k]["mode"] != "current"}))

# overlay R1 (vertical T/L note geometry) -> vertical_note guard, B1 off
ok_vnote = all(DEC[(sid, 1)]["mode"] == "current"
               and DEC[(sid, 1)]["guard"] == "vertical_note"
               for sid in ("S003", "S007")
               if (sid, 1) in DEC)
check("V4e overlay/vertical-note regions guard out (V-3 untouched)",
      ok_vnote)

# fill gains on the actually-triggered set (target 0.85 max-goal, Ruling 4)
gains = {k: (DEC[k].get("block_fill_usable", 0)
             - DEC[k].get("cur_block_fill_usable", 0)) for k in mask_set}
check("V4f triggered regions' block_fill_usable improves "
      "(target 0.85 max-goal)",
      all(g > 0 for g in gains.values()),
      str({f"{k[0]}-R{k[1]}": round(g, 3) for k, g in gains.items()}))

# Phase A cross-check: predicted vs production sizes on the overlap set
PRED = {("S003", 4): (26, 0.653), ("S003", 5): (19, 0.951),
        ("S007", 2): (19, 0.717)}
for k, (p_size, p_bfu) in PRED.items():
    d = DEC[k]
    check(f"V4g {k[0]}-R{k[1]} matches Phase A prediction "
          f"(size {p_size}, blkU {p_bfu})",
          d.get("font_size") == p_size
          and abs(d.get("block_fill_usable", 0) - p_bfu) <= 0.02,
          f"got {d.get('font_size')}/{d.get('block_fill_usable')}")

# ════════════════════════════════════════════════════════════════════
# V5 — render_page pre vs post parity on BOTH archives
# ════════════════════════════════════════════════════════════════════
print("\n── V5 render_page pre/post parity ──")
PRE_FINAL = {}
POST_FINAL = {}
POST_META = {}
for sid in ("S003", "S007"):
    det, rows, img = load_sample(sid)
    tr_by_id = {int(r["id"]): r for r in rows}
    ns_p = install_render_stubs(make_ns(), sid, img)
    ns_p["translation_df"] = build_translation_df(sid, det, rows)
    exec(compile(span_cfg_pre, "<cell10 §2 pre>", "exec"), ns_p)
    exec(compile(span10_pre, "<cell10 §3-§8 pre>", "exec"), ns_p)
    exec(compile(span9_pre, "<cell10 §9 pre>", "exec"), ns_p)
    ns_p["render_page"](sid, force=True)
    PRE_FINAL[sid] = ns_p["_harness_saved"][("final", sid)]
    PRE_META = dict(ns_p["_harness_metas"][sid])

    ns_q = install_render_stubs(make_ns(), sid, img)
    ns_q["translation_df"] = build_translation_df(sid, det, rows)
    exec(compile(span_cfg_post, "<cell10 §2 post>", "exec"), ns_q)
    exec(compile(span10_post, "<cell10 §3-§8 post>", "exec"), ns_q)
    exec(compile(span9_post, "<cell10 §9 post>", "exec"), ns_q)
    ns_q["render_page"](sid, force=True)
    POST_FINAL[sid] = ns_q["_harness_saved"][("final", sid)]
    POST_META[sid] = dict(ns_q["_harness_metas"][sid])
    POST_META[sid]["_pre"] = PRE_META

for sid in ("S003", "S007"):
    pre, post = PRE_FINAL[sid], POST_FINAL[sid]
    check(f"V5a {sid} pre/post finals same shape",
          pre.shape == post.shape, f"{pre.shape} vs {post.shape}")
    diff = np.any(pre != post, axis=2) if pre.shape == post.shape else None
    triggered = [rid for (s, rid), dec in DEC.items()
                 if s == sid and dec["mode"] == "mask"]
    boxes = []
    a = ARCH[sid]
    for d in a["det"]:
        if int(d["id"]) in triggered:
            boxes.append((int(d["x"]) - 8, int(d["y"]) - 8,
                          int(d["x"]) + int(d["width"]) + 8,
                          int(d["y"]) + int(d["height"]) + 8))
    allow = np.zeros(diff.shape, bool)
    for (bx1, by1, bx2, by2) in boxes:
        allow[max(0, by1):by2, max(0, bx1):bx2] = True
    outside = int((diff & ~allow).sum())
    check(f"V5b {sid} kept-current regions byte-identical "
          f"(diff only inside {len(triggered)} triggered bboxes)",
          outside == 0, f"outside-diff px={outside}")
    inside = int((diff & allow).sum())
    check(f"V5c {sid} triggered regions re-laid-out (diff present)",
          inside > 0, f"inside-diff px={inside}")

    # ink growth inside each triggered region's bubble mask
    for rid in triggered:
        d = next(x for x in ARCH[sid]["det"] if int(x["id"]) == rid)
        mm = ns_post["_bubble_interior_mask"](
            ARCH[sid]["gray"], int(d["x"]), int(d["y"]),
            int(d["width"]), int(d["height"]))
        bub = mm[0]
        pre_ink = int(((cv2.cvtColor(pre, cv2.COLOR_RGB2GRAY) < 100)
                       & bub).sum())
        post_ink = int(((cv2.cvtColor(post, cv2.COLOR_RGB2GRAY) < 100)
                        & bub).sum())
        check(f"V5d {sid}-R{rid} rendered ink grows "
              f"(artist-direction, B1 effect)",
              post_ink > pre_ink, f"{pre_ink} -> {post_ink}")

    # meta disclosure (Ruling 4)
    m = POST_META[sid]
    bf = m.get("bubble_fill")
    check(f"V5e {sid} bubble_fill meta disclosure present",
          isinstance(bf, dict) and bf.get("enabled") is True
          and bf.get("mask_regions") == len(triggered)
          and {str(k) for k in bf.get("regions", {})}
          >= {str(r) for r in triggered},
          f"mask_regions={bf.get('mask_regions') if bf else None}")
    check(f"V5f {sid} pre meta has NO bubble_fill key "
          f"(untouched surface)", "bubble_fill" not in POST_META[sid]["_pre"])
    if bf:
        trig_entries = {k: v for k, v in bf["regions"].items()
                        if v.get("mode") == "mask"}
        check(f"V5g {sid} mask entries carry cap_bound disclosure "
              f"(Ruling 4 honest fallback)",
              all(isinstance(v.get("cap_bound"), bool)
                  for v in trig_entries.values()),
              str({k: v.get("cap_bound") for k, v in trig_entries.items()}))

# kill-switch: enable=False on POST == PRE bytes exactly
for sid in ("S003", "S007"):
    det, rows, img = load_sample(sid)
    ns_k = install_render_stubs(make_ns({"bubble_fill_enable": False}),
                                sid, img)
    ns_k["translation_df"] = build_translation_df(sid, det, rows)
    exec(compile(span_cfg_post, "<cell10 §2 post>", "exec"), ns_k)
    exec(compile(span10_post, "<cell10 §3-§8 post>", "exec"), ns_k)
    exec(compile(span9_post, "<cell10 §9 post>", "exec"), ns_k)
    ns_k["render_page"](sid, force=True)
    k_final = ns_k["_harness_saved"][("final", sid)]
    same = k_final.shape == PRE_FINAL[sid].shape and \
        np.array_equal(k_final, PRE_FINAL[sid])
    kmeta = ns_k["_harness_metas"][sid]
    check(f"V5h {sid} kill-switch (enable=False) == PRE render byte-exact",
          same and "bubble_fill" not in kmeta)

# ════════════════════════════════════════════════════════════════════
# V6 — C-1 wrapper chain (cells 11/12 patched)
# ════════════════════════════════════════════════════════════════════
print("\n── V6 C-1 wrapper chain ──")
wrap11 = extract_wrapper_span(cells_post[11], "_QC_FINAL_RENDER_PATCHED")
wrap12 = extract_wrapper_span(cells_post[12], "_QC_RENDER_PATCHED")
ns_w = make_ns()
exec(compile(span_cfg_post, "<cell10 §2 post>", "exec"), ns_w)
exec(compile(span10_post, "<cell10 §3-§8 post>", "exec"), ns_w)
ns_w["_v_calls"] = []
ns_w["_qc_render_vertical"] = (
    lambda image_pil, text, x, y, w, h, b, color, padding:
    (ns_w["_v_calls"].append((x, y, w, h)), image_pil)[1])
exec(compile(wrap11, "<cell11 wrapper post>", "exec"), ns_w)
exec(compile(wrap12, "<cell12 wrapper post>", "exec"), ns_w)

# wide bubble through the chain WITH fit_result — must not TypeError
det3, rows3, _ = load_sample("S003")
d4 = next(x for x in det3 if int(x["id"]) == 4)
dec4 = DEC[("S003", 4)]
assert dec4["mode"] == "mask"
cv1 = PILImage.new("RGB", (800, 600), (255, 255, 255))
try:
    ns_w["render_bengali_text"](
        cv1, str(ARCH["S003"]["tr"][4].get("translated_text")),
        int(d4["x"]), int(d4["y"]), int(d4["width"]), int(d4["height"]),
        region_type="bubble", text_color=(0, 0, 0),
        fit_result=dec4)
    drew = int((np.array(cv1).mean(axis=2) < 128).sum())
    check("V6a W12(W11(orig)) forwards fit_result (no TypeError, ink drawn)",
          drew > 0, f"ink px={drew}")
except TypeError as exc:
    check("V6a W12(W11(orig)) forwards fit_result (no TypeError, ink drawn)",
          False, str(exc)[:120])

# vertical-note geometry through the chain — vertical arm intact
cv2 = PILImage.new("RGB", (300, 400), (255, 255, 255))
ns_w["render_bengali_text"](cv2, "টি/এল নোট পরীক্ষা", 20, 20, 61, 298,
                            region_type="overlay",
                            text_color=(0, 0, 0))
check("V6b vertical arm still intercepts (V-3 predicate untouched)",
      len(ns_w["_v_calls"]) == 1 and ns_w["_v_calls"][0][2:] == (61, 298),
      str(ns_w["_v_calls"]))

# fallback arm without fit_result — plain call parity
cv3 = PILImage.new("RGB", (800, 600), (255, 255, 255))
cv4 = PILImage.new("RGB", (800, 600), (255, 255, 255))
ns_w["render_bengali_text"](cv3, "বাংলা পরীক্ষা", 100, 100, 300, 150,
                            region_type="bubble", text_color=(0, 0, 0))
ns_post["render_bengali_text"](cv4, "বাংলা পরীক্ষা", 100, 100, 300, 150,
                               region_type="bubble", text_color=(0, 0, 0))
check("V6c wrapper fallback (fit_result=None) == direct original bytes",
      np.array_equal(np.array(cv3), np.array(cv4)))

# ════════════════════════════════════════════════════════════════════
# V7 — N-1 dynamic (beyond battery Test 15: log_event ERROR capture)
# ════════════════════════════════════════════════════════════════════
print("\n── V7 N-1 dynamic ──")
ns_n1 = make_ns()
exec(compile(span_cfg_post, "<cell10 §2 post>", "exec"), ns_n1)
exec(compile(span10_post, "<cell10 §3-§8 post>", "exec"), ns_n1)
ns_n1["MANGABD_CONFIG"]["rendering"]["font_regular"] = "/tmp/MISSING-m009.ttf"
ns_n1["MANGABD_CONFIG"]["rendering"]["font_bold"] = ""
ns_n1["_FONT_CACHE"].pop((41, False), None)
with contextlib.redirect_stdout(io.StringIO()) as so_n1:
    f_n1 = ns_n1["get_font"](41, bold=False)
n1_events = [e for e in ns_n1["MANGABD_EVENTS"]
             if "main font load failed" in e["message"]]
check("V7a get_font missing font -> log_event ERROR (never silent)",
      bool(n1_events) and n1_events[0]["level"] == "ERROR"
      and "Main font load failed" in so_n1.getvalue())

# ════════════════════════════════════════════════════════════════════
# V8 — m002_sim_v2 fresh-kernel simulator on the POST cells
# ════════════════════════════════════════════════════════════════════
print("\n── V8 fresh-kernel simulator ──")
POST_CELLS_DIR.mkdir(exist_ok=True)
for i, src in enumerate(cells_post):
    (POST_CELLS_DIR / f"cell_{i:02d}.py").write_text(src, encoding="utf-8")
sim_out = subprocess.run(
    [sys.executable, "-c",
     "import sys, importlib.util\n"
     "from pathlib import Path\n"
     "spec = importlib.util.spec_from_file_location("
     "'sim2', %r)\n"
     "m = importlib.util.module_from_spec(spec)\n"
     "spec.loader.exec_module(m)\n"
     "m.CELLS_DIR = Path(%r)\n"
     "import io, contextlib\n"
     "buf = io.StringIO()\n"
     "with contextlib.redirect_stdout(buf):\n"
     "    m.main()\n"
     "txt = buf.getvalue()\n"
     "n = txt.count('ABORT-CLASS findings (unguarded, unresolvable): 0')\n"
     "print('ABORT_ZERO' if n == 1 else 'ABORT_NONZERO')\n"
     "print(txt[txt.find('ABORT-CLASS'):txt.find('ABORT-CLASS')+120])\n"
     % (str(SIM), str(POST_CELLS_DIR))],
    capture_output=True, text=True)
check("V8a m002_sim_v2 on POST cells: 0 abort sites",
      "ABORT_ZERO" in sim_out.stdout, sim_out.stdout.strip()[:160])

# ════════════════════════════════════════════════════════════════════
print()
print("=" * 72)
fails = [n for n, ok in RESULTS if not ok]
print(f"VERIFY TOTAL: {len(RESULTS)} checks, "
      f"{len(RESULTS) - len(fails)} PASS, {len(fails)} FAIL")
if fails:
    print("FAILED:")
    for n in fails:
        print(f"  - {n}")
print("VERIFY " + ("OK" if not fails else "FAILED"))
print("=" * 72)
sys.exit(0 if not fails else 1)
