#!/usr/bin/env python3
r"""MANGABD-009 B2 Phase C — verification instrument.

Branch mangabd-009-b2, base = main @ 5fe8804. Verifies the
orientation-inheritance Phase C against the ruling surface
RB2-1..RB2-7 (angle semantic A / snap 5° / pixel-PCA source / PCA quad
recompute / PIL-expand fit dims / emphasis skipped / scope {6,10} +
default-ON kill-switch):

  V1  static integrity: scope exactly {6, 10}; cells 7/11/12/24
      byte-identical (RB2-7 named guarantee); reading-order 13/15/23
      byte-identical; AST 27/27 warnings-as-errors; re-derivation from
      scripts/m009_b2_phaseC_patches.json; non-source fields identical;
      secret scan; per-cell delta confined to the manifest; B1 surfaces
      preserved; cell-10 §2 (B1 knob block) byte-identical
  V2  config exec: cell-6 9b knob default True; B1 knob values intact
  V3  cell-10 battery: 18/18 HARD (12 M008 + 13-15 B1 + 16-18 B2) —
      with the production estimator from cell-6 9b exec'd first
  V4  archive parity (production estimator): all 6 archives, all 36
      rows → _estimate_region_angle == (0.0, None) — detections.json
      byte-parity on the archived corpus by construction
  V5  render_page pre-vs-post on S003/S007: finals byte-IDENTICAL
      everywhere (archives carry no tilt) + meta parity (no
      b2_orientation key either side)
  V6  synthetic tilted page through render_page: tilt renders (meta
      disclosure), lean inherited (estimator round-trip on the new
      ink), PRE dormant-chain rotation vs POST quad-extents fit
      (smaller font = RB2-5 anti-oversize), kill-switch OFF == axis-
      aligned row byte-exact + silent meta (immediate rollback)
  V7  m002_sim_v2 fresh-kernel simulator on the POST cells: 0 abort

Fonts: /home/z/my-project/m008_probe/fonts (real NotoSansBengali +
NotoSansJP — the M008-verified pair).
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
from PIL import Image as PILImage, ImageDraw

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "5fe8804"
BRANCH = "mangabd-009-b2"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
S003 = REPO / "samples" / "S003_batch2"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
SAMPLES = REPO / "samples"
POST_CELLS_DIR = Path("/home/z/my-project/cells_m009_b2_post")
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


def make_ns(config_extra=None):
    ns = {"__name__": "m009_b2_phaseC_harness"}
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
    ns["MANGABD_ASSETS"] = {"fonts": {
        "fallback_path": str(FONTS / "NotoSansJP.ttf"),
        "fallback_sha_ok": True, "fallback_size": 0,
        "fallback_license": "",
    }}
    exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
         "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)
    return ns


def install_render_stubs(ns, page_id, inpainted_bgr, detections=None):
    """Minimal storage-layer stubs so render_page runs (B1 pattern + the
    B2 load_json_artifact stub for the detections-quad lookup)."""
    ns["get_page"] = lambda pid, required=True: {"page_id": pid}
    ns["is_stage_done"] = lambda pid, stage: False
    ns["load_image_artifact"] = (
        lambda pid, kind: inpainted_bgr.copy() if kind == "inpainted" else None)
    saved = {}

    def save_image_artifact(pid, kind, img, quality=95):
        if kind == "final":
            saved[("final", pid)] = (
                np.array(img) if hasattr(img, "size") else np.asarray(img))

    ns["save_image_artifact"] = save_image_artifact
    ns["save_translation_df"] = lambda: None
    ns["load_translation_df"] = lambda: None
    ns["reset_page"] = lambda pid, from_stage=None: None
    ns["load_json_artifact"] = lambda pid, name, default=None: (
        list(detections) if (name == "detections" and detections)
        else (default if default is not None else None))
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


ARCHIVES = ["S003_batch2", "S007_mangabd005_02",
            "S001_color_webtoon", "S002_batch1",
            "S005_manual", "S005_openrouter"]


def load_archive(name):
    if name == "S007_mangabd005_02":
        with zipfile.ZipFile(S007_ZIP) as z:
            img = cv2.imdecode(
                np.frombuffer(z.read("original.jpg"), np.uint8),
                cv2.IMREAD_COLOR)
            regions = json.loads(z.read("detections.json").decode())
        return img, regions
    d = SAMPLES / name
    img = cv2.imread(str(d / "original.jpg"), cv2.IMREAD_COLOR)
    regions = json.loads((d / "detections.json").read_text())
    return img, regions


print("=" * 72)
print("MANGABD-009 B2 PHASE C — VERIFY (branch mangabd-009-b2)")
print("=" * 72)

# ════════════════════════════════════════════════════════════════════
# V1 — static integrity
# ════════════════════════════════════════════════════════════════════
print("\n── V1 static integrity ──")
check("V1a branch mangabd-009-b2",
      git("branch", "--show-current").strip() == BRANCH)
raw_post, nb_post, cells_post = load_cells(NB)
raw_pre = git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8")
nb_pre = json.loads(raw_pre.decode("utf-8"))
cells_pre = ["".join(c.get("source", [])) for c in nb_pre["cells"]
             if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_post[i] != cells_pre[i]]
check("V1b scope drift exactly {6, 10}", sorted(scope) == [6, 10],
      f"drift={sorted(scope)}")
for i in (7, 11, 12, 24):
    check(f"V1c RB2-7 named cell {i} byte-identical",
          cells_post[i] == cells_pre[i])
for i in (13, 15, 23):
    check(f"V1d reading-order cell {i} byte-identical",
          cells_post[i] == cells_pre[i])

for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(cells_post[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL cell {i} warning-as-error: {w}")
check("V1e AST compile 27/27 (warnings-as-errors)", True)

manifest = json.loads((REPO / "scripts" / "m009_b2_phaseC_patches.json")
                      .read_text(encoding="utf-8"))
re_src = dict(enumerate(cells_pre))
for p in manifest:
    cnt = re_src[p["cell"]].count(p["old"])
    assert cnt == 1, f"re-derivation anchor {p['name']}: {cnt}x"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1f re-derivation: post == pre + exactly the manifest patches",
      all(re_src[i] == cells_post[i] for i in range(27)))

nb_check = json.loads(raw_post.decode("utf-8"))
non_src_ok = all(
    {k: v for k, v in nb_pre["cells"][i].items() if k != "source"}
    == {k: v for k, v in nb_check["cells"][i].items() if k != "source"}
    for i in range(len(nb_pre["cells"])))
top_ok = ({k: v for k, v in nb_pre.items() if k != "cells"}
          == {k: v for k, v in nb_check.items() if k != "cells"})
check("V1g non-source + top-level fields identical", non_src_ok and top_ok)

added = "\n".join(p["new"] for p in manifest)
secret_pats = [r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
               r"sk-[A-Za-z0-9]{20,}", r"AIza[0-9A-Za-z_\-]{20,}",
               r"hf_[A-Za-z0-9]{20,}", r"Bearer\s+[A-Za-z0-9._\-]{20,}"]
secrets = [p for p in secret_pats if re.search(p, added)]
check("V1h secret scan on added lines (0 hits)", not secrets, str(secrets))

for i in (6, 10):
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
    check(f"V1i cell {i} delta confined to the manifest patches",
          minus_ok and plus_ok, f"{len(d)} diff lines")

# cell-10 §2 (B1 knob block) byte-identical: B2 adds NO rendering knobs
cfg_pre = extract_span(cells_pre[10], "# 2. Rendering config defaults",
                       "# 3. Text helpers")
cfg_post = extract_span(cells_post[10], "# 2. Rendering config defaults",
                        "# 3. Text helpers")
check("V1j cell-10 §2 byte-identical (B2 adds no rendering knobs)",
      cfg_pre == cfg_post)

# B1 surfaces preserved on the merged file
b1_ok = all(s in cells_post[10] for s in (
    'setdefault("bubble_fill_enable", True)',
    'setdefault("bubble_fill_trigger", 0.60)',
    'setdefault("bubble_fill_target", 0.85)',
    'setdefault("font_size_max", 48)',
    "def _bubble_interior_mask(", "def bubble_fill_decision(",
    "fit_result=bf_fit,", 'guard"] = "vertical_note"',
))
check("V1k B1 surfaces all preserved (no B2 regression)", b1_ok)
# V-3 predicate untouched in both wrapper cells + cell-10 decision
v3_sig = "w < 90 and h > 2*max(1, w) and abs(float(angle)) <= 1.0"
check("V1l V-3 wrapper predicate byte-intact in cells 11/12",
      all(cells_post[i].count(v3_sig) == 1 for i in (11, 12)))
# rotated production block byte-untouched (RB2-5: PIL expand=True stays)
rot_block = ('        rotated = text_canvas.rotate(\n'
             '            angle,\n'
             '            expand=True,\n'
             '            resample=PILImage.BICUBIC,\n'
             '        )')
check("V1m production rotate block byte-untouched",
      rot_block in cells_post[10] and cells_post[10].count(rot_block) == 1)

# ════════════════════════════════════════════════════════════════════
# V2 — config exec (knob defaults)
# ════════════════════════════════════════════════════════════════════
print("\n── V2 config knobs ──")
span_b2_post = extract_span(cells_post[6], "# 9b. MANGABD-009 B2",
                            "# 10. Visualization")
ns_v2 = make_ns()
exec(compile(span_b2_post, "<cell6 9b post>", "exec"), ns_v2)
check("V2a cell-6 b2_orientation_enable default True (RB2-7)",
      ns_v2["MANGABD_CONFIG"]["detection"].get("b2_orientation_enable") is True)
check("V2b cell-6 estimator defined by the 9b span",
      callable(ns_v2.get("_estimate_region_angle")))

ns_cfg = make_ns()
exec(compile(cfg_post, "<cell10 §2 post>", "exec"), ns_cfg)
rc = ns_cfg["MANGABD_CONFIG"]["rendering"]
check("V2c B1 knob defaults intact (trigger 0.60 / target 0.85 / cap 48)",
      rc.get("bubble_fill_enable") is True
      and rc.get("bubble_fill_trigger") == 0.60
      and rc.get("bubble_fill_target") == 0.85
      and rc.get("font_size_max") == 48)

# ════════════════════════════════════════════════════════════════════
# V3 — cell-10 battery 18/18 (with the production estimator exec'd first)
# ════════════════════════════════════════════════════════════════════
print("\n── V3 cell-10 battery ──")
span10_post = extract_span(cells_post[10], "# 3. Text helpers",
                           "# 9. Page rendering pipeline")
batt_post = extract_span(cells_post[10], "# 10. Self-tests", None)
span9_post = extract_span(cells_post[10], "# 9. Page rendering pipeline",
                          "# 10. Self-tests")
span10_pre = extract_span(cells_pre[10], "# 3. Text helpers",
                          "# 9. Page rendering pipeline")
span9_pre = extract_span(cells_pre[10], "# 9. Page rendering pipeline",
                         "# 10. Self-tests")

ns_post = make_ns()
exec(compile(cfg_post, "<cell10 §2 post>", "exec"), ns_post)
exec(compile(span_b2_post, "<cell6 9b post>", "exec"), ns_post)
exec(compile(span10_post, "<cell10 §3-§8 post>", "exec"), ns_post)
ns_pre = make_ns()
exec(compile(cfg_pre, "<cell10 §2 pre>", "exec"), ns_pre)
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
check("V3a cell-10 battery 18/18 HARD (12 M008 + B1 13/14/15 + B2 16/17/18)",
      "Cell 10 result: SUCCESS" in out_batt
      and tot and tot[0]["extra"]["tests_total"] == 18
      and tot[0]["extra"]["tests_passed"] == 18
      and tot[0]["extra"]["tests_skipped"] == 0,
      (tot[0]["extra"] if tot else "no completion event"))
for tname, needle in (
        ("Test 13 B1 synthetic ellipse", "B1 mask fill: synthetic ellipse"),
        ("Test 14 B1 guards", "B1 guards: trigger + kill-switch"),
        ("Test 15 N-1 loud degrade", "get_font loud degradation"),
        ("Test 16 B2 estimator semantics",
         "B2 estimator: synthetic tilt semantics (RB2-1/2/3/4 + gates)"),
        ("Test 17 B2 fit dims + mirror",
         "B2 render: quad-extents fit + kill-switch mirror"),
        ("Test 18 B2 end-to-end inheritance",
         "B2 end-to-end: estimator -> render inherits the lean")):
    check(f"V3b {tname} ✅", f"✅ {needle}" in out_batt)

# ════════════════════════════════════════════════════════════════════
# V4 — archive parity: production estimator on ALL archived regions
# ════════════════════════════════════════════════════════════════════
print("\n── V4 archive parity (production estimator) ──")
est = ns_post["_estimate_region_angle"]
n_rows = 0
n_store = 0
bad = []
for name in ARCHIVES:
    img, regions = load_archive(name)
    for r in regions:
        n_rows += 1
        ang, quad = est(img, int(r["x"]), int(r["y"]),
                        int(r["width"]), int(r["height"]))
        if not (ang == 0.0 and quad is None):
            n_store += 1
            bad.append((name, r.get("id"), ang))
check("V4a production estimator: 0/36 archived rows store a tilt "
      "(archive-byte-identical by construction)",
      n_rows == 36 and n_store == 0, f"rows={n_rows} storing={n_store} {bad}")

# every archived detections row already carries angle 0.0 + bbox quad
ang_nonzero = sum(1 for name in ARCHIVES
                  for r in load_archive(name)[1]
                  if float(r.get("angle", 0.0)) != 0.0)
check("V4b archived detections all angle 0.0 (input sanity)",
      ang_nonzero == 0, f"nonzero={ang_nonzero}")

# the six archives are one byte-identical original (Phase A finding,
# re-verified at Phase C time)
import hashlib as _hl
oshas = {_hl.sha256(np.asarray(load_archive(n)[0]).tobytes()).hexdigest()
         for n in ARCHIVES}
check("V4c archives still share ONE original (6 unique regions)",
      len(oshas) == 1, f"{len(oshas)} distinct")

# ════════════════════════════════════════════════════════════════════
# V5 — render_page pre vs post on BOTH archives (byte-identical)
# ════════════════════════════════════════════════════════════════════
print("\n── V5 render_page pre/post parity ──")
for sid in ("S003", "S007"):
    det, rows, img = load_sample(sid)
    ns_p = install_render_stubs(make_ns(), sid, img, detections=det)
    ns_p["translation_df"] = build_translation_df(sid, det, rows)
    exec(compile(cfg_pre, "<cell10 §2 pre>", "exec"), ns_p)
    exec(compile(span10_pre, "<cell10 §3-§8 pre>", "exec"), ns_p)
    exec(compile(span9_pre, "<cell10 §9 pre>", "exec"), ns_p)
    ns_p["render_page"](sid, force=True)
    pre_final = ns_p["_harness_saved"][("final", sid)]
    pre_meta = dict(ns_p["_harness_metas"][sid])

    ns_q = install_render_stubs(make_ns(), sid, img, detections=det)
    ns_q["translation_df"] = build_translation_df(sid, det, rows)
    exec(compile(cfg_post, "<cell10 §2 post>", "exec"), ns_q)
    exec(compile(span_b2_post, "<cell6 9b post>", "exec"), ns_q)
    exec(compile(span10_post, "<cell10 §3-§8 post>", "exec"), ns_q)
    exec(compile(span9_post, "<cell10 §9 post>", "exec"), ns_q)
    ns_q["render_page"](sid, force=True)
    post_final = ns_q["_harness_saved"][("final", sid)]
    post_meta = dict(ns_q["_harness_metas"][sid])

    same = (pre_final.shape == post_final.shape
            and np.array_equal(pre_final, post_final))
    check(f"V5a {sid} pre/post final render byte-IDENTICAL "
          f"(archives carry no tilt)", same,
          f"shape {pre_final.shape} vs {post_final.shape}")
    check(f"V5b {sid} render meta byte-parity (no b2_orientation key)",
          {k: v for k, v in post_meta.items() if k != "bubble_fill"}
          == {k: v for k, v in pre_meta.items() if k != "bubble_fill"}
          and "b2_orientation" not in post_meta,
          f"post keys={sorted(post_meta)}")

# ════════════════════════════════════════════════════════════════════
# V6 — synthetic tilted page through render_page (the B2 live class)
# ════════════════════════════════════════════════════════════════════
print("\n── V6 synthetic tilted page (render_page level) ──")


def _synth_tilted_page():
    """A 700x520 white page with ONE -25° text strip; the region dict is
    built EXACTLY like cell-6's build (estimator angle + PCA quad)."""
    from PIL import ImageFont
    font = ImageFont.truetype(str(FONTS / "NotoSansBengali-Regular.ttf"), 28)
    txt = "বাংলা টেস্ট লাইন বাংলা টেস্ট লাইন বাংলা টেস্ট"
    c = PILImage.new("L", (780, 130), 255)
    ImageDraw.Draw(c).text((12, 40), txt, font=font, fill=0)
    # fillcolor=255: PIL's default rotate fill is BLACK — on a white
    # canvas the corner triangles would become spurious ink for PCA
    r = c.rotate(-25.0, expand=True, resample=PILImage.BICUBIC,
                 fillcolor=255)
    pg = np.full((r.height + 80, r.width + 80, 3), 255, np.uint8)
    pg[40:40 + r.height, 40:40 + r.width] = cv2.cvtColor(
        np.asarray(r), cv2.COLOR_GRAY2BGR)
    g = cv2.cvtColor(pg, cv2.COLOR_BGR2GRAY)
    ys, xs = np.nonzero(g < 128)
    box = (int(xs.min()), int(ys.min()),
           int(xs.max() - xs.min()) + 1, int(ys.max() - ys.min()) + 1)
    ang, quad = est(pg, *box)
    det = [{
        "id": 1, "x": box[0], "y": box[1], "width": box[2], "height": box[3],
        "angle": ang, "quad": quad, "region_type": "bubble",
        "detector_class": "text_bubble", "detector_score": 0.9,
    }]
    tr = [{"id": 1, "translated_text": "এই কী হয়েছে বলো তো?!",
           "bengali_valid": True, "status": "rendered"}]
    return pg, det, tr, ang


pg, det, tr, synth_ang = _synth_tilted_page()
check("V6a synthetic page estimator stores a tilt (the live class)",
      abs(synth_ang + 25.0) <= 1.5 and det[0]["quad"] is not None,
      f"angle={synth_ang}")

# render happens on the INPAINTED canvas (production truth: the original
# text is gone) — a white page of the same geometry; detection side above
# used the original strip page (detection sees the artist's ink)
PG_INPAINT = np.full_like(pg, 255)

DF_TILT = pd.DataFrame([{
    "page_id": "SYNTH", "id": 1,
    "x": det[0]["x"], "y": det[0]["y"],
    "width": det[0]["width"], "height": det[0]["height"],
    "angle": float(det[0]["angle"]), "region_type": "bubble",
    "translated_text": tr[0]["translated_text"],
    "bengali_valid": True, "status": "rendered",
}])
DF_FLAT = DF_TILT.copy()
DF_FLAT["angle"] = 0.0


def _run_render_page(df, knob, code="post", detections=det):
    ns = install_render_stubs(make_ns(), "SYNTH", PG_INPAINT,
                              detections=detections)
    ns["translation_df"] = df.copy()
    if knob is not None:
        ns["MANGABD_CONFIG"]["detection"]["b2_orientation_enable"] = knob
    exec(compile(cfg_post if code == "post" else cfg_pre,
                 "<cfg>", "exec"), ns)
    if code == "post":
        exec(compile(span_b2_post, "<cell6 9b post>", "exec"), ns)
        exec(compile(span10_post, "<c10 post>", "exec"), ns)
        exec(compile(span9_post, "<c9 post>", "exec"), ns)
    else:
        exec(compile(span10_pre, "<c10 pre>", "exec"), ns)
        exec(compile(span9_pre, "<c9 pre>", "exec"), ns)
    ns["render_page"]("SYNTH", force=True)
    return (ns["_harness_saved"][("final", "SYNTH")],
            dict(ns["_harness_metas"]["SYNTH"]))


# knob ON: tilt renders + meta disclosure
fin_on, meta_on = _run_render_page(DF_TILT, True)
check("V6b knob ON: tilted region renders + meta discloses tilted_rendered=1",
      meta_on.get("b2_orientation", {}).get("tilted_rendered") == 1,
      f"meta={meta_on.get('b2_orientation')}")

# kill-switch OFF: byte-exact axis-aligned rollback, silent meta
fin_off, meta_off = _run_render_page(DF_TILT, False)
fin_flat, meta_flat = _run_render_page(DF_FLAT, True)
check("V6c kill-switch OFF == axis-aligned row byte-exact "
      "(immediate rollback)",
      fin_off.shape == fin_flat.shape and np.array_equal(fin_off, fin_flat))
check("V6d kill-switch OFF: silent meta (no b2_orientation key)",
      "b2_orientation" not in meta_off)

# knob-ON render differs from the flat render (the tilt is visible)
diff_tilt = int(np.any(np.asarray(fin_on) != np.asarray(fin_flat), axis=2).sum())
check("V6e knob ON: render visibly differs from axis-aligned "
      "(tilt actually inherited)", diff_tilt > 500, f"diff px={diff_tilt}")

# lean inheritance: PCA round-trip on the NEW ink only (the inpainted
# canvas was all-white, so every dark pixel in the output IS new ink)
src_gray = cv2.cvtColor(PG_INPAINT, cv2.COLOR_BGR2GRAY)
out_gray = cv2.cvtColor(np.asarray(fin_on), cv2.COLOR_RGB2GRAY)
new_ink = (out_gray < 128) & (src_gray >= 128)
diff_img = np.full(pg.shape, 255, np.uint8)
diff_img[new_ink] = 0
ys, xs = np.nonzero(new_ink)
rbox = (int(xs.min()) - 6, int(ys.min()) - 6,
        int(xs.max() - xs.min()) + 12, int(ys.max() - ys.min()) + 12)
rt_ang, _ = est(diff_img, *rbox)
check("V6f rendered Bengali carries the same lean (estimator round-trip)",
      new_ink.sum() > 200 and abs(rt_ang - synth_ang) <= 2.5,
      f"page tilt={synth_ang} rendered-ink tilt={rt_ang} "
      f"newink={int(new_ink.sum())}")

# PRE dormant chain: same tilted row through the PRE renderer rotates
# with BBOX fit dims (oversized per V5 2.08x); POST quad-extents fit
# yields a smaller-or-equal tracked font (RB2-5 anti-oversize)
fin_pre, meta_pre = _run_render_page(DF_TILT, None, code="pre")
pre_max = meta_pre.get("font_size_max_used")
post_max = meta_on.get("font_size_max_used")
check("V6g PRE rotates too (dormant chain) but POST quad-fit font "
      "smaller-or-equal (RB2-5 anti-oversize)",
      pre_max is not None and post_max is not None and post_max <= pre_max,
      f"PRE bbox-fit max={pre_max}px POST quad-fit max={post_max}px")
pre_rot_diff = int(np.any(np.asarray(fin_pre) != np.asarray(fin_flat),
                         axis=2).sum())
check("V6h PRE render also rotated on the tilted row (machinery pre-built)",
      pre_rot_diff > 500, f"pre-vs-flat diff px={pre_rot_diff}")

# ════════════════════════════════════════════════════════════════════
# V7 — m002_sim_v2 fresh-kernel simulator on the POST cells
# ════════════════════════════════════════════════════════════════════
print("\n── V7 fresh-kernel simulator ──")
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
check("V7a m002_sim_v2 on POST cells: 0 abort sites",
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
