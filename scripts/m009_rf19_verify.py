#!/usr/bin/env python3
r"""MANGABD-009 RF-19 — verification (ALL GREEN gate).

Base ref: 36faa98 (B3.1 Phase D tip = branch tip, UNMERGED hold).
Work: the RF-19-patched notebook (built by m009_rf19_build.py).

  V0  preconditions: branch, base pin, cells dirs pinned
  V1  scope: changed cells EXACTLY {6,10}; 25 non-targets
      byte-identical; AST 27/27 both refs; manifest (8 patches)
      re-derivation base<->work BYTE-EXACT; wiring probes; secret scan
  V2  dynamic battery (harness subprocess): cell-10 SUCCESS + the 6
      Test-25 arms + the 11 Test-24 arms + legacy markers + census
  V3  archive render parity (S003/S007/S009/S010/S011/S012, base vs
      work on identical archived inputs) + RF-19 fire census 0 on
      every archive render + knob-OFF == BASE bytes on real S003
  V4  S012 chain re-run determinism (detections + final.jpg
      byte-identical to the committed archive) — the band-gate
      live-detection test (R6 12° stays tilted, keys unchanged)
  V5  m002_sim_v2 on the post-build extraction: 0 abort sites
  V6  results JSON (scripts/m009_rf19_results.json, committed)
"""
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import warnings
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "36faa98"
CELLS_BASE = Path("/home/z/my-project/cells_b31_fix")   # 36faa98 pin
CELLS_WORK = Path("/home/z/my-project/cells_rf19_fix")
S012 = REPO / "samples" / "S012_manhwa_emphasis"
RESULTS = REPO / "scripts" / "m009_rf19_results.json"

PASS = FAIL = 0
RESULTS_DATA = {"checks": []}


def check(name, ok, detail=""):
    global PASS, FAIL
    ok = bool(ok)
    PASS += ok
    FAIL += (not ok)
    tag = "PASS" if ok else "FAIL"
    print(f"[{tag}] {name}" + (f" — {detail}" if detail else ""))
    RESULTS_DATA["checks"].append({"name": name, "ok": ok,
                                   "detail": str(detail)[:300]})


def git(*a):
    return subprocess.run(["git", "-C", str(REPO)] + list(a),
                          capture_output=True, text=True,
                          check=True).stdout


def extract_span(src, start, end):
    i = src.index(start)
    j = src.index(end, i)
    return src[i:j]


# ════════════════════════════════════════════════════════════════════
# V0 — preconditions
# ════════════════════════════════════════════════════════════════════
print("── V0 preconditions ──")
branch = git("branch", "--show-current").strip()
check("V0a on branch mangabd-009-b3", branch == "mangabd-009-b3", branch)
for ref in (BASE_REF, "cf01aef"):
    hold = subprocess.run(
        ["git", "-C", str(REPO), "merge-base", "--is-ancestor",
         ref, "main"], capture_output=True).returncode != 0
    check(f"V0b merge hold intact ({ref} NOT ancestor of main)", hold)
base_sha = hashlib.sha256(
    git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8")).hexdigest()
check("V0d base notebook == the B3.1-tip pin (3055f374...)",
      base_sha.startswith("3055f374"), base_sha[:16])

nb_work = json.loads(NB.read_text(encoding="utf-8"))
nb_base = json.loads(
    git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8"))
cells_work = {i: "".join(c["source"])
              for i, c in enumerate(nb_work["cells"])}
cells_base = {i: "".join(c["source"])
              for i, c in enumerate(nb_base["cells"])}
assert len(cells_work) == 27 and len(cells_base) == 27

nb_sha = hashlib.sha256(NB.read_bytes()).hexdigest()
nb_expect = json.loads(git("show", f"{BASE_REF}:{NB_NAME}"))
for _i in range(27):
    nb_expect["cells"][_i]["source"] = cells_work[_i].splitlines(
        keepends=True)
expect_raw = (json.dumps(nb_expect, indent=1, ensure_ascii=False)
              + "\n").encode("utf-8")
check("V0c working notebook == byte-faithful (base + manifest) "
      "rebuild", NB.read_bytes() == expect_raw, nb_sha[:16])
dir_ok = True
for i in range(27):
    for cells_dir, src in ((CELLS_BASE, cells_base[i]),
                           (CELLS_WORK, cells_work[i])):
        if (cells_dir / f"cell_{i:02d}.py").read_text(
                encoding="utf-8") != src:
            dir_ok = False
check("V0e cells dirs byte-pinned to their notebook refs", dir_ok)

# ════════════════════════════════════════════════════════════════════
# V1 — scope + AST + manifest re-derivation + secret scan
# ════════════════════════════════════════════════════════════════════
print("\n── V1 scope ──")
changed = sorted(i for i in range(27)
                 if cells_base[i] != cells_work[i])
check("V1a changed cells EXACTLY {6,10}", changed == [6, 10],
      str(changed))
non_targets = [i for i in range(27) if i not in (6, 10)]
check("V1b 25 non-target cells byte-identical",
      all(cells_base[i] == cells_work[i] for i in non_targets))

with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        compile(cells_work[i], f"cell_{i:02d}.py", "exec")
        compile(cells_base[i], f"cell_{i:02d}.py", "exec")
check("V1c AST 27/27 both refs (warnings-as-errors)", True)

patches = json.loads(
    (REPO / "scripts" / "m009_rf19_patches.json")
    .read_text(encoding="utf-8"))
check("V1d manifest present (8 patches)", len(patches) == 8,
      f"{len(patches)} patches")

re_src = dict(cells_base)
for p in patches:
    if re_src[p["cell"]].count(p["old"]) != 1:
        check(f"V1e anchor unique: {p['name']}", False)
        break
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
else:
    check("V1e re-derivation base->work BYTE-EXACT (all 27 cells)",
          all(re_src[i] == cells_work[i] for i in range(27)))

re_src2 = dict(cells_work)
for p in patches:
    if re_src2[p["cell"]].count(p["new"]) != 1:
        check(f"V1f reverse anchor unique: {p['name']}", False)
        break
    re_src2[p["cell"]] = re_src2[p["cell"]].replace(p["new"],
                                                    p["old"])
else:
    check("V1f re-derivation work->base BYTE-EXACT (all 27 cells)",
          all(re_src2[i] == cells_base[i] for i in range(27)))

w = cells_work
probe_ok = (
    w[6].count("def _rf19_band_tilt_max(") == 1
    and w[6].count("_RF19_BAND_TILT_MAX = 2.0") == 1
    and w[6].count("return 0.0, None, None, True") == 4
    and w[6].count("def _b2_mask_orientation(") == 1
    and w[6].count("def _b31_line_colors_key(") == 1
    and w[6].count("_B31_LINE_TAU = 0.15") == 1
    and w[6].count("if w < 80 and b31_raw_ink is not None:") == 1
    and w[6].count('regions[-1]["line_colors"] = _b31_lc') == 1
    and w[6].count('regions[-1]["ink_color"] = _b3_c') == 1
    and w[6].count("color_inherit_enable") == 4
    and w[10].count('_RF19_LAST_LAYOUT = {"lines": None}') == 1
    and w[10].count("_RF19_GUARD_FIRES = []") == 1
    and w[10].count('_RF19_LAST_LAYOUT["lines"] = int(len(lines))') == 1
    and w[10].count('_RF19_LAST_LAYOUT.get("lines") == 1') == 1
    and w[10].count("_rf19_snap = canvas_pil.copy() "
                    "if _rf19_area_ok else None") == 1
    and w[10].count('meta["rf19_tiny_guard"] = {"regions": '
                    "_rf19_fires}") == 1
    and w[10].count("RF-19 tiny-guard re-layout") == 1
    and w[10].count("# Test 25: MANGABD-009 RF-19") == 1
    and w[10].count("# Test 24: B3.1") == 1
    and w[10].count("# Test 23: B3") == 1
    and w[10].count("Invalid line_colors ignored") == 2
    and w[10].count("Invalid ink_color ignored") == 2
    and w[10].count("quarantine") >= 3
    and w[11] == cells_base[11] and w[12] == cells_base[12])
check("V1g wiring probes (RF-19 surfaces + B1/B2/B3/B3.1 preserved "
      "+ cells 11/12 untouched)", probe_ok)

diff = git("diff", BASE_REF, "--", NB_NAME, "-U0")
added = "\n".join(ln[1:] for ln in diff.splitlines()
                  if ln.startswith("+") and not ln.startswith("+++"))
SECRET_PATTERNS = [
    (r"github_pat_[A-Za-z0-9]{20,}", "github pat"),
    (r"ghp_[A-Za-z0-9]{30,}", "ghp key"),
    (r"sk-[A-Za-z0-9_-]{16,}", "sk- key"),
    (r"AIza[A-Za-z0-9_-]{30,}", "google key"),
    (r"xox[baprs]-[A-Za-z0-9-]{10,}", "slack token"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY", "private key block"),
]
hits = [lbl for pat, lbl in SECRET_PATTERNS if re.search(pat, added)]
check("V1h secret-pattern scan on added notebook lines (0 hits)",
      not hits, f"{len(added.splitlines())} added lines, hits={hits}")

# ════════════════════════════════════════════════════════════════════
# V2 — dynamic battery (harness subprocess)
# ════════════════════════════════════════════════════════════════════
print("\n── V2 dynamic battery (harness) ──")
smoke = subprocess.run(
    [sys.executable, str(REPO / "scripts" / "m009_rf19_harness.py")],
    capture_output=True, text=True)
out = smoke.stdout
check("V2a battery smoke ALL GREEN (exit 0)",
      smoke.returncode == 0, out[-300:] if smoke.returncode else "")
t25_arms = [ln for ln in out.splitlines() if "✅ RF-19" in ln]
check("V2b RF-19 green markers 6 (the Test-25 arms)",
      len(t25_arms) == 6, f"{len(t25_arms)} markers")
need_markers = [
    "RF-19 false-tilt gate: asymmetric emphasis cloud",
    "RF-19 genuine tilt preserved: 12° block",
    "RF-19 tiny-guard FIRES: id=4-class",
    "RF-19 healthy single line: short text",
    "RF-19 healthy multi-line: normal region",
    "RF-19 battery guard census: fires EXACTLY",
]
for mk in need_markers:
    check(f"V2c Test-25 arm present+green: {mk[:44]}...",
          any(mk in ln and "✅" in ln for ln in out.splitlines()))
t24_arms = [ln for ln in out.splitlines() if "✅ B3.1" in ln]
check("V2d B3.1 green markers 13 (11 Test-24 arms + cell-11 7.5c "
      "+ cell-12 7.7b)", len(t24_arms) == 13, f"{len(t24_arms)} markers")
for mk in ("B3.1 tiny-text assertion: original lines >= 2 AND area >= "
           "2000px",
           "B3.1 kill-switch: OFF",
           "B3.1 narrow V5 end-to-end: raw-locator GT"):
    check(f"V2e Test-24 arm still green: {mk[:44]}...",
          any(mk in ln and "✅" in ln for ln in out.splitlines()))
check("V2f legacy B3 arms still green (Test 23 family)",
      all(any(m in ln and "✅" in ln for ln in out.splitlines())
          for m in ("B3 render: key→red ink",
                    "B3 kill-switch: OFF",
                    "B3 invalid stored color"))
      and any(ln.startswith("LEGACY-B3-MARKERS-OK True")
              for ln in out.splitlines()),
      next((ln for ln in out.splitlines()
            if ln.startswith("LEGACY-B3-MARKERS-OK")), "absent"))
check("V2g cell-10 SUCCESS", "Cell 10 result: SUCCESS" in out)

# ════════════════════════════════════════════════════════════════════
# V3 — archive render parity + RF-19 fire census + knob-OFF
# ════════════════════════════════════════════════════════════════════
print("\n── V3 archive render parity + fire census ──")
FONTS = Path("/home/z/my-project/rf14_home/mangabd/fonts")
assert (FONTS / "NotoSansBengali-Regular.ttf").exists()


def make_ns():
    ns = {"__name__": "m009_rf19_verify"}
    ns["MANGABD_CONFIG"] = {
        "rendering": {
            "font_size_min": 8, "font_size_max": 48,
            "font_size_default": 24,
            "line_spacing_factor": 1.18, "padding_ratio": 0.08,
            "use_grapheme_safe_wrap": True,
            "use_background_aware_color": True,
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
         "from PIL import Image as PILImage\n"
         "from PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)
    return ns


class FilePages:
    def __init__(self, root):
        self.root = Path(root)
        self.pages = {}
        self.saved = []
        self.marks = []

    def init(self, pid, det_rows, inpainted_bgr, meta=None,
             stages=None):
        d = self.root / "pages" / pid
        d.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(d / "inpainted.png"), inpainted_bgr)
        (d / "detections.json").write_text(
            json.dumps(det_rows), encoding="utf-8")
        self.pages[pid] = {"page_id": pid, "meta": dict(meta or {}),
                           "stages": dict(stages or {})}
        return self.pages[pid]

    def bind(self, ns):
        store = self

        def get_page(pid, required=False):
            return store.pages.get(pid) if pid in store.pages else (
                store._raise_missing(pid) if required else None)
        ns["get_page"] = get_page
        ns["get_page_dir"] = lambda pid: store.root / "pages" / pid
        ns["is_stage_done"] = lambda pid, stage: bool(
            store.pages.get(pid, {}).get("stages", {}).get(stage, False))

        def mark_stage_done(pid, stage, meta=None):
            store.marks.append((pid, stage, dict(meta or {})))
            pg = store.pages.setdefault(
                pid, {"page_id": pid, "meta": {}, "stages": {}})
            pg.setdefault("stages", {})[stage] = True
            pg.setdefault("meta", {}).update(dict(meta or {}))
        ns["mark_stage_done"] = mark_stage_done

        def save_image_artifact(pid, name, img, quality=95):
            store.saved.append((pid, name))
            d = store.root / "pages" / pid
            d.mkdir(parents=True, exist_ok=True)
            if name == "final":
                img.save(d / "final.jpg", quality=int(quality))
            elif name == "inpainted":
                cv2.imwrite(str(d / "inpainted.png"), img)
        ns["save_image_artifact"] = save_image_artifact

        def load_image_artifact(pid, name, flags=None):
            p = store.root / "pages" / pid
            fname = {"inpainted": "inpainted.png",
                     "final": "final.jpg"}.get(name)
            if fname is None:
                return None
            q = p / fname
            return cv2.imread(str(q), cv2.IMREAD_COLOR) if q.exists() \
                else None
        ns["load_image_artifact"] = load_image_artifact

        def load_json_artifact(pid, name, default=None):
            q = store.root / "pages" / pid / "detections.json"
            if name == "detections" and q.exists():
                return json.loads(q.read_text(encoding="utf-8"))
            return default
        ns["load_json_artifact"] = load_json_artifact
        ns["save_translation_df"] = lambda df=None: None
        ns["load_translation_df"] = lambda: None
        ns["reset_page"] = lambda pid, from_stage=None, \
            delete_artifacts=False: None
        return ns


def cell10_spans(cells):
    cfg = extract_span(cells[10], "# 2. Rendering config defaults",
                       "# 3. Text helpers")
    core = extract_span(cells[10], "# 3. Text helpers",
                        "# 10. Self-tests")
    return cfg, core


def core_ns(side):
    tmp = tempfile.mkdtemp(prefix=f"rf19_{side}_")
    store = FilePages(tmp)
    ns = make_ns()
    store.bind(ns)
    cfg, core = cell10_spans(
        cells_base if side == "base" else cells_work)
    exec(compile(cfg, f"<c10 {side} cfg>", "exec"), ns)
    exec(compile(core, f"<c10 {side} core>", "exec"), ns)
    return ns, store


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


ARCHIVES = {
    "S003": ("dir", REPO / "samples" / "S003_batch2"),
    "S007": ("zip", REPO / "S007_mangabd005_02.zip"),
    "S009": ("dir", REPO / "samples" / "S009_diagonal"),
    "S010": ("dir", REPO / "samples" / "S010_burst"),
    "S011": ("dir", REPO / "samples" / "S011_manhwa_ui"),
    "S012": ("dir", S012),
}


def load_sample(sid):
    kind, path = ARCHIVES[sid]
    if kind == "zip":
        with zipfile.ZipFile(path) as z:
            def rd(name):
                cand = [n for n in z.namelist() if n.endswith(name)]
                return z.read(cand[0])
            det = json.loads(rd("detections.json"))
            tr = json.loads(rd("translation.json"))
            img = cv2.imdecode(
                np.frombuffer(rd("inpainted.png"), np.uint8),
                cv2.IMREAD_COLOR)
    else:
        det = json.load(open(path / "detections.json"))
        tr = json.load(open(path / "translation.json"))
        img = cv2.imread(str(path / "inpainted.png"), cv2.IMREAD_COLOR)
    rows = tr if isinstance(tr, list) else tr.get("rows", [])
    return det, rows, img


for sid in ARCHIVES:
    det, rows, img = load_sample(sid)
    outs = {}
    fires = None
    for side in ("base", "work"):
        ns, store = core_ns(side)
        store.init(sid, det, img)
        ns["translation_df"] = build_translation_df(sid, det, rows)
        ns["render_page"](sid, force=True)
        outs[side] = (store.root / "pages" / sid
                      / "final.jpg").read_bytes()
        if side == "work":
            fires = list(ns["_RF19_GUARD_FIRES"])
    check(f"V3a {sid} fresh render byte-IDENTICAL (base vs work) + "
          f"RF-19 fire census 0",
          outs["base"] == outs["work"] and fires == [],
          f"{len(outs['work'])} B, fires={fires}")

# knob-OFF on real S003: WORK with color_inherit_enable=False ==
# BASE bytes (the kill-switch law)
det, rows, img = load_sample("S003")
ns_b, store_b = core_ns("base")
store_b.init("S003", det, img)
ns_b["translation_df"] = build_translation_df("S003", det, rows)
ns_b["render_page"]("S003", force=True)
base_bytes = (store_b.root / "pages" / "S003"
              / "final.jpg").read_bytes()
ns_w, store_w = core_ns("work")
store_w.init("S003", det, img)
ns_w["translation_df"] = build_translation_df("S003", det, rows)
ns_w["MANGABD_CONFIG"]["rendering"]["color_inherit_enable"] = False
ns_w["render_page"]("S003", force=True)
off_bytes = (store_w.root / "pages" / "S003"
             / "final.jpg").read_bytes()
check("V3b knob-OFF on real S003: WORK-OFF == BASE bytes",
      off_bytes == base_bytes, f"{len(off_bytes)} B")

# ════════════════════════════════════════════════════════════════════
# V4 — S012 chain re-run determinism (band-gate live detection)
# ════════════════════════════════════════════════════════════════════
print("\n── V4 S012 chain re-run (band gate live) ──")
detl = subprocess.run(
    [sys.executable, "-c", """
import sys
sys.path.insert(0, "/home/z/my-project/MangaBD/scripts")
from m009_b2_rf18_chain import run_chain, artifact_path
from m009_b31_s012_page import build_s012_page
full, clean, regions, ink = build_s012_page()
ns, pid, det_rows = run_chain("s012_manhwa_emphasis.jpg", full, clean,
                              regions, ink)
import json, hashlib
det = json.load(open(str(artifact_path(ns, pid, "detections"))))
print("DET_SHA", hashlib.sha256(
    json.dumps(det, sort_keys=True).encode()).hexdigest())
print("FIN_SHA", hashlib.sha256(
    artifact_path(ns, pid, "final").read_bytes()).hexdigest())
r6 = next(d for d in det if d.get("id") == 5)
print("R6_ANG", r6.get("angle"), r6.get("b2_gt_lines"))
"""], capture_output=True, text=True)
assert detl.returncode == 0, detl.stdout[-300:] + detl.stderr[-300:]
det_sha = fin_sha = None
r6_pin = ""
for ln in detl.stdout.splitlines():
    if ln.startswith("DET_SHA"):
        det_sha = ln.split()[1]
    elif ln.startswith("FIN_SHA"):
        fin_sha = ln.split()[1]
    elif ln.startswith("R6_ANG"):
        r6_pin = ln
arch_det = json.load(open(S012 / "detections.json"))
arch_det_sha = hashlib.sha256(
    json.dumps(arch_det, sort_keys=True).encode()).hexdigest()
arch_fin_sha = hashlib.sha256(
    (S012 / "final.jpg").read_bytes()).hexdigest()
check("V4a S012 determinism: chain re-run detections byte-identical "
      "(band gate: R6 12° stays tilted, all keys unchanged)",
      det_sha == arch_det_sha, f"{det_sha} vs {arch_det_sha}; {r6_pin}")
check("V4b S012 determinism: chain re-run final.jpg byte-identical "
      "(tiny-guard census 0 on the S012 chain render)",
      fin_sha == arch_fin_sha, f"{fin_sha} vs {arch_fin_sha}")

# ════════════════════════════════════════════════════════════════════
# V5 — m002_sim_v2 on the post-build extraction
# ════════════════════════════════════════════════════════════════════
print("\n── V5 m002_sim_v2 ──")
sim = subprocess.run(
    [sys.executable, "/home/z/my-project/scripts/m005_sim2.py",
     str(CELLS_WORK)], capture_output=True, text=True)
check("V5a sim runs", sim.returncode == 0,
      (sim.stdout[-200:] + sim.stderr[-200:]) if sim.returncode else "")
check("V5b m002_sim_v2 = 0 abort sites",
      "ABORT-CLASS findings (unguarded, unresolvable): 0"
      in sim.stdout, sim.stdout[-300:])

# ════════════════════════════════════════════════════════════════════
# V6 — results
# ════════════════════════════════════════════════════════════════════
RESULTS_DATA["summary"] = {
    "pass": PASS, "fail": FAIL,
    "notebook_sha256_work": nb_sha,
    "notebook_sha256_base": base_sha,
    "test25_arms": len(t25_arms),
    "test24_arms": len([ln for ln in out.splitlines()
                        if "✅ B3.1" in ln and "integration" not in ln
                        and "threading" not in ln]),
    "archives_parity": sorted(ARCHIVES),
    "guard_fire_census": "archives 0; battery exactly "
                         "(__rf19_t25_guard__, 1)",
}
with open(RESULTS, "w", encoding="utf-8") as f:
    json.dump(RESULTS_DATA, f, ensure_ascii=False, indent=1)
print(f"\nresults -> {RESULTS}")

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
if FAIL:
    raise SystemExit("RF-19 VERIFICATION FAILED")
print("ALL GREEN")
