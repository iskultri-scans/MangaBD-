#!/usr/bin/env python3
r"""MANGABD-009 B3 Phase C — verification instrument (branch mangabd-009-b3).

Verifies the ruled B3 scope (ink color inheritance, RB3-1..RB3-7):

  V1  static: scope drift exactly {6,10,11,12} vs 8fbde52; the other
      23 cells byte-identical; AST 27/27 warnings-as-errors; manifest
      re-derivation; B1/B2/B2.1 surfaces byte-untouched (choose_text_color
      RF-17, production rotate block, _b2_render_angle mirror,
      _b2_gt_tilted_layout, B2.1 guard helpers, _b2_page_ink_mask incl.
      artifact fallback, _b2_mask_orientation, battery Tests 16-22
      blocks + RF-13 hygiene tail, wrapper predicates/guards/_qc_render_
      vertical/Test 20 block); secret scan on the delta
  V2  dynamic battery via scripts/m009_b3_phaseC_harness.py (cells
      01-07+10+11+12 verbatim, env stubs disclosed there): cell-10
      SUCCESS 29/29, Test 23 all arms PASS, Tests 17/19/21/22 PASS,
      cell-11 B3 wrapper check + m8 5/5, cell-12 Test 20 + B3
      full-chain PASS, B2.1 quarantine/guard WARN evidence intact
  V3  healthy-path render parity: S003/S007/S009/S010/S011 fresh
      renders byte-IDENTICAL base vs work (span-exec, FilePages store —
      the B2.1 V4 pattern); the archives carry NO ink_color key, so
      this proves the conditional-key law keeps the render side inert
      on the whole committed corpus; render-meta parity + no
      quarantine side effects
  V4  wrapper-chain law (RF-15): cells 11/12 wrapper spans differ from
      base by EXACTLY the ink_color threading (signature / vertical
      arm / forward); predicate, guard mechanism, _qc_orig_render/
      _base_render binding and _qc_render_vertical byte-untouched;
      vertical None-path literals preserved; old-style call sites
      (no kwarg) structurally identical (default None)
  V5  knob-law static proof: every ink_color consumer is gated
      (cell-6 build gate / cell-10 parse gate); zero ink_color
      consumers outside {6,10,11,12}
  V6  m002_sim_v2 fresh-kernel simulator on the fixed cells: 0 abort
      sites
"""
import difflib
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
BASE_REF = "8fbde52"
BRANCH = "mangabd-009-b3"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
S003 = REPO / "samples" / "S003_batch2"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
HARNESS = REPO / "scripts" / "m009_b3_phaseC_harness.py"
FIX_CELLS = Path("/home/z/my-project/cells_b3_fix")
MANIFEST = REPO / "scripts" / "m009_b3_phaseC_patches.json"

RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    RESULTS.append(ok)
    print(f"  {'✅' if ok else '❌'} {name}"
          + (f"  [{detail}]" if detail else ""))


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


print("=" * 72)
print("MANGABD-009 B3 Phase C — VERIFY (branch mangabd-009-b3)")
print("=" * 72)

# ════════════════════════════════════════════════════════════════════
# V1 — static integrity
# ════════════════════════════════════════════════════════════════════
print("\n── V1 static integrity ──")
check("V1a branch mangabd-009-b3",
      git("branch", "--show-current").strip() == BRANCH)

raw_work, nb_work, cells_work = load_cells(NB)
raw_base = git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8")
nb_base = json.loads(raw_base.decode("utf-8"))
cells_base = ["".join(c.get("source", [])) for c in nb_base["cells"]
              if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_work[i] != cells_base[i]]
check("V1b scope drift exactly {6,10,11,12} (the ruled cells ONLY)",
      sorted(scope) == [6, 10, 11, 12], f"drift={sorted(scope)}")
untouched = [i for i in set(range(27)) - {6, 10, 11, 12}
             if cells_work[i] != cells_base[i]]
check("V1c the other 23 cells byte-identical to 8fbde52",
      not untouched,
      f"changed={untouched} (incl. RB2-7 named 7,24 + "
      f"reading-order 13,15,23)")

with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        try:
            compile(cells_work[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL cell {i} warning-as-error: {w}")
check("V1d AST compile 27/27 (warnings-as-errors)", True)

patches = json.loads(MANIFEST.read_text(encoding="utf-8"))
re_src = list(cells_base)
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"{p['name']} anchor"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1e re-derivation (work == 8fbde52 + exactly the manifest)",
      all(re_src[i] == cells_work[i] for i in range(27)),
      f"{len(patches)} patches")

# B1/B2/B2.1 production surfaces byte-untouched (cell 10)
surfaces10 = [
    ("RF-17 choose_text_color", "def choose_text_color(",
     "def choose_stroke_width("),
    ("production rotate/paste block", "rotated = text_canvas.rotate(",
     "return image_pil"),
    ("B2 _b2_render_angle mirror", "def _b2_render_angle(",
     'print("  ✅ B2 render-angle mirror ready'),
    ("B2 _b2_gt_tilted_layout (incl. vjust)", "def _b2_gt_tilted_layout",
     "def render_bengali_text"),
    ("B2.1 guard helpers", "def _b2_renderable_rows_present(",
     "def render_page("),
]
for label, s, e in surfaces10:
    check(f"V1f cell-10 {label} byte-untouched",
          extract_span(cells_base[10], s, e)
          == extract_span(cells_work[10], s, e))

# cell 6: B2 functions byte-untouched (B3 helpers inserted BETWEEN them)
check("V1g cell-6 _b2_page_ink_mask body byte-untouched "
      "(B3 helpers appended after it)",
      extract_span(cells_base[6], "def _b2_page_ink_mask(",
                   "def _b2_mask_orientation(")
      == extract_span(cells_work[6], "def _b2_page_ink_mask(",
                      "def _b3_undilated_ink_mask("))
check("V1g cell-6 _b2_mask_orientation body byte-untouched",
      extract_span(cells_base[6], "def _b2_mask_orientation(",
                   "def visualize_detections(")
      == extract_span(cells_work[6], "def _b2_mask_orientation(",
                      "def visualize_detections("))
check("V1g cell-6 B2 estimator + region-loop anchors byte-untouched",
      extract_span(cells_base[6], "def _estimate_region_angle(",
                   "def _b2_page_ink_mask(")
      == extract_span(cells_work[6], "def _estimate_region_angle(",
                      "def _b2_page_ink_mask("))

# battery blocks byte-untouched (Tests 16..22 + hygiene tail)
bat = [
    ("Test 16", "# Test 16: B2 estimator", "# Test 17: B2 render side"),
    ("Tests 17-18", "# Test 17: B2 render side", "# Test 19: B2 RF-14"),
    ("Test 19", "# Test 19: B2 RF-14", "# Test 21: B2 RF-18"),
    ("Test 21", "# Test 21: B2 RF-18", "# Test 22: B2.1"),
]
for label, s, e in bat:
    check(f"V1h battery {label} block byte-untouched",
          extract_span(cells_base[10], s, e)
          == extract_span(cells_work[10], s, e))
# Test 22: base block runs to the hygiene tail; work block to Test 23
check("V1h battery Test 22 block byte-untouched (23 inserted after)",
      extract_span(cells_base[10], "# Test 22: B2.1",
                   "# RF-13 fixture hygiene:")
      == extract_span(cells_work[10], "# Test 22: B2.1", "# Test 23: B3"))
check("V1h RF-13 hygiene tail byte-untouched",
      extract_span(cells_base[10], "# RF-13 fixture hygiene:", None)
      == extract_span(cells_work[10], "# RF-13 fixture hygiene:", None))

t23_span = extract_span(cells_work[10], "# Test 23: B3",
                        "# RF-13 fixture hygiene:")
check("V1i battery Test 23 present + fail-on-current contract comment",
      len(t23_span) > 4000
      and "fail-on-current-bytes contract" in t23_span)

# cell 11/12: predicate + guards + vertical renderer untouched
PRED = ("if text and str(text).strip() and w < 90 and h > 2*max(1, w)"
        " and abs(float(angle)) <= 1.0:")
for c in (11, 12):
    check(f"V1j cell-{c} _qc_render_vertical byte-untouched",
          extract_span(cells_base[c], "def _qc_render_vertical(",
                       "if not globals().get(")
          == extract_span(cells_work[c], "def _qc_render_vertical(",
                          "if not globals().get("))
    check(f"V1k cell-{c} wrapper predicate + guard byte-untouched",
          cells_base[c].count(PRED) == 1
          and cells_work[c].count(PRED) == 1
          and f'globals()["_QC_' in cells_base[c]
          and f'globals()["_QC_' in cells_work[c])

T20_RAISE = (
    'if not _t20_ok:\n'
    '    raise RuntimeError(\n'
    '        "Cell 12 RF-15 integration battery failed: V-3 wrapper-গুলো "\n'
    '        "render_page-এর fit_w/fit_h নিতে পারছে না — Run All-এ প্রতিটা "\n'
    '        "region নীরবে blank হয়ে যায়। Fix করে তারপর পরের cell-এ যাও।"\n'
    '    )')
check("V1l cell-12 Test 20 body + raise block byte-untouched "
      "(B3 7.7 appended after)",
      extract_span(cells_base[12], "# ── 7.6)", "if not _t20_ok:")
      == extract_span(cells_work[12], "# ── 7.6)", "if not _t20_ok:")
      and cells_base[12].count(T20_RAISE) == 1
      and cells_work[12].count(T20_RAISE) == 1)

# secret scan on the delta (added lines)
diff = git("diff", f"{BASE_REF}", "--", NB_NAME, "-U0")
added = "\n".join(ln[1:] for ln in diff.splitlines()
                  if ln.startswith("+") and not ln.startswith("+++"))
SECRET_PATTERNS = [
    (r"api_key\s*=\s*['\"][^'\"]{8,}", "api_key assignment"),
    (r"password\s*=\s*['\"][^'\"]{4,}", "password assignment"),
    (r"token\s*=\s*['\"][A-Za-z0-9._-]{8,}", "token assignment"),
    (r"AKIA[0-9A-Z]{16}", "AWS key id"),
    (r"sk-[A-Za-z0-9_-]{16,}", "sk- key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY", "private key block"),
]
hits = [lbl for pat, lbl in SECRET_PATTERNS if re.search(pat, added)]
check("V1m secret-pattern scan on added notebook lines (0 hits)",
      not hits, f"{len(added.splitlines())} added lines, hits={hits}")

# ════════════════════════════════════════════════════════════════════
# V2 — dynamic battery
# ════════════════════════════════════════════════════════════════════
print("\n── V2 dynamic battery (harness) ──")
harness_out = subprocess.run(
    [sys.executable, str(HARNESS)], capture_output=True, text=True)
markers = {}
for ln in harness_out.stdout.splitlines():
    if ": " in ln:
        k, v = ln.split(": ", 1)
        if k.isupper() and len(k) > 3 and k.replace("_", "").isalnum():
            markers[k] = v
need = {
    "CELL10_RESULT": "SUCCESS",
    "TEST23": "PASS", "TEST23_RENDER": "PASS", "TEST23_KNOB": "PASS",
    "TEST23_BAD": "PASS", "TEST23_KWARG": "PASS",
    "TEST22": "PASS", "TEST19": "PASS", "TEST21": "PASS",
    "TEST17": "PASS",
    "CELL11_B3": "PASS", "CELL12_T20": "PASS", "CELL12_B3": "PASS",
}
for k, v in need.items():
    check(f"V2a {k} == {v}", markers.get(k) == v, markers.get(k, "ABSENT"))
check("V2b battery ledger 29/29 (0 skipped)",
      markers.get("BATTERY_EVENTS", "").startswith(
          "tests_passed=29 tests_total=29 tests_skipped=0"),
      markers.get("BATTERY_EVENTS", "absent"))
check("V2c B2.1 evidence intact (quarantine+guard WARNs)",
      "quarantine_warns=1 guard_warns=1" in markers.get(
          "EVENT_EVIDENCE", ""), markers.get("EVENT_EVIDENCE", ""))
check("V2d cell-11 m8 glyph coverage 5/5",
      "5/5" in markers.get("CELL11_M8", ""),
      markers.get("CELL11_M8", "absent"))
check("V2e cell-12 tail (QUALITY CORE active)",
      "QUALITY CORE active" in markers.get("CELL12_TAIL", ""),
      markers.get("CELL12_TAIL", "absent"))

# ════════════════════════════════════════════════════════════════════
# V3 — healthy-path render parity (archives, base vs work)
# ════════════════════════════════════════════════════════════════════
print("\n── V3 archive render parity (base vs work) ──")


def make_ns():
    ns = {"__name__": "m009_b3_verify"}
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
    """File-backed page/artifact store (V3 stub set — B2.1 V4 pattern)."""

    def __init__(self, root):
        self.root = Path(root)
        self.pages = {}
        self.saved = []
        self.marks = []

    def _raise_missing(self, pid):
        raise KeyError(f"Page not found in manifest: {pid}")

    def init(self, pid, det_rows, inpainted_bgr, meta=None, stages=None):
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
            if pid in store.pages:
                return store.pages[pid]
            if required:
                store._raise_missing(pid)
            return None
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
    """Fresh namespace with the given side's cfg+core exec'd."""
    tmp = tempfile.mkdtemp(prefix=f"b3_{side}_")
    store = FilePages(tmp)
    ns = make_ns()
    store.bind(ns)
    cfg, core = cell10_spans(cells_base if side == "base" else cells_work)
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


def load_sample(sid):
    if sid == "S003":
        det = json.load(open(S003 / "detections.json"))
        tr = json.load(open(S003 / "translation.json"))
        rows = tr if isinstance(tr, list) else tr.get("rows", [])
        img = cv2.imread(str(S003 / "inpainted.png"), cv2.IMREAD_COLOR)
        return det, rows, img
    if sid == "S007":
        with zipfile.ZipFile(S007_ZIP) as z:
            def rd(name):
                cand = [n for n in z.namelist() if n.endswith(name)]
                return z.read(cand[0])
            det = json.loads(rd("detections.json"))
            tr = json.loads(rd("translation.json"))
            rows = tr if isinstance(tr, list) else tr.get("rows", [])
            arr = cv2.imdecode(
                np.frombuffer(rd("inpainted.png"), np.uint8),
                cv2.IMREAD_COLOR)
            return det, rows, arr
    d = REPO / "samples" / f"{sid}_diagonal" if sid == "S009" else (
        REPO / "samples" / f"{sid}_burst" if sid == "S010" else
        REPO / "samples" / f"{sid}_manhwa_ui")
    det = json.load(open(d / "detections.json"))
    tr = json.load(open(d / "translation.json"))
    rows = tr if isinstance(tr, list) else tr.get("rows", [])
    img = cv2.imread(str(d / "inpainted.png"), cv2.IMREAD_COLOR)
    return det, rows, img


# corpus pre-check: no archived detections row carries ink_color
no_key = True
for sid in ("S003", "S007", "S009", "S010", "S011"):
    det, _, _ = load_sample(sid)
    if any("ink_color" in d for d in det):
        no_key = False
check("V3a0 corpus pre-condition: 0 ink_color keys in the five archives",
      no_key, "the conditional-key law's inertness premise")

for sid in ("S003", "S007", "S009", "S010", "S011"):
    det, rows, img = load_sample(sid)
    outs = {}
    for side in ("base", "work"):
        ns, store = core_ns(side)
        store.init(sid, det, img)
        ns["translation_df"] = build_translation_df(sid, det, rows)
        ns["render_page"](sid, force=True)
        fpath = store.root / "pages" / sid / "final.jpg"
        outs[side] = dict(
            bytes=fpath.read_bytes(),
            meta=[m for m in store.marks
                  if m[0] == sid and m[1] == "render"],
            saved=list(store.saved),
            quar=(store.root / "pages" / sid / "quarantine").exists(),
            warns=[e for e in ns["MANGABD_EVENTS"]
                   if e["level"] == "WARN"
                   and "quarantin" in e["message"]],
        )
    same = outs["base"]["bytes"] == outs["work"]["bytes"]
    check(f"V3a {sid} fresh render byte-IDENTICAL (base vs work)",
          same, f"{len(outs['work']['bytes'])} B")
    check(f"V3b {sid} render meta parity + no quarantine side effects",
          outs["base"]["meta"] == outs["work"]["meta"]
          and not outs["work"]["quar"] and not outs["work"]["warns"]
          and outs["work"]["saved"] == [(sid, "final")],
          f"meta={outs['work']['meta'][-1][2]
              if outs['work']['meta'] else '?'}")

# ════════════════════════════════════════════════════════════════════
# V4 — wrapper-chain law (RF-15, static span parity)
# ════════════════════════════════════════════════════════════════════
print("\n── V4 wrapper-chain law ──")
for c, guard in ((11, "_QC_FINAL_RENDER_PATCHED"),
                 (12, "_QC_RENDER_PATCHED")):
    b_span = extract_span(cells_base[c], f"if not globals().get(",
                          "# ── 7.5) MANGABD-008")
    w_span = extract_span(cells_work[c], f"if not globals().get(",
                          "# ── 7.5) MANGABD-008")
    # reverse-apply this cell's manifest patches to the work span;
    # equality with the base span proves the wrapper delta is EXACTLY
    # the ink_color threading patches (nothing else in the span moved)
    w2 = w_span
    applied = 0
    for p in [q for q in patches if q["cell"] == c]:
        if p["new"] in w2:
            w2 = w2.replace(p["new"], p["old"])
            applied += 1
    check(f"V4a cell-{c} wrapper span == base + exactly the "
          f"ink_color threading patches (reverse-apply equality)",
          w2 == b_span and applied >= 3 and "ink_color" in w_span,
          f"applied={applied} equal={w2 == b_span}")
    check(f"V4b cell-{c} binding/guard lines byte-identical",
          f'_qc_orig_render = render_bengali_text' in b_span
          or '_base_render = globals().get("_qc_orig_render", '
          'render_bengali_text)' in b_span)
    check(f"V4c cell-{c} vertical None-path literal preserved",
          ("else (0,0,0)," in w_span) if c == 11
          else ("else (0, 0, 0)," in w_span))
    check(f"V4d cell-{c} old-call compatibility (default None — "
          f"callers without the kwarg take the exact previous path)",
          "ink_color=None" in w_span)

# ════════════════════════════════════════════════════════════════════
# V5 — knob-law static proof
# ════════════════════════════════════════════════════════════════════
print("\n── V5 knob law (static) ──")
c6w = cells_work[6]
c10w = cells_work[10]
check("V5a cell-6 sampling fully knob-gated "
      "(setdefault + build gate; OFF → no mask, no keys, no events)",
      c6w.count('MANGABD_CONFIG["rendering"].setdefault('
                '"color_inherit_enable", True)') == 1
      and c6w.count('MANGABD_CONFIG["rendering"].get('
                    '"color_inherit_enable", True)') == 1
      and "b3_ink_mask = None" in c6w
      and "if b3_ink_mask is not None:" in c6w)
check("V5b cell-10 consumption knob-gated at parse "
      "(OFF → map empty → no override, zero events)",
      "_b3_inherit = bool(" in c10w
      and "if _b3_inherit:" in c10w
      and c10w.count("b3_page_ink") >= 3)
check("V5c zero ink_color consumers outside {6,10,11,12}",
      all("ink_color" not in cells_work[i]
          for i in range(27) if i not in (6, 10, 11, 12)))
check("V5d RB3-2/RB3-3 laws: gray/white/black never keyed; "
      "vertical white impossible (no key by construction)",
      'return None, "gray"' in c6w
      and 'return None, "white"' in c6w
      and 'return None, "black"' in c6w)

# ════════════════════════════════════════════════════════════════════
# V6 — fresh-kernel simulator on the fixed cells
# ════════════════════════════════════════════════════════════════════
print("\n── V6 fresh-kernel simulator (m002_sim_v2) ──")
FIX_CELLS.mkdir(exist_ok=True)
for i, src in enumerate(cells_work):
    (FIX_CELLS / f"cell_{i:02d}.py").write_text(src, encoding="utf-8")
sim_out = subprocess.run(
    [sys.executable, "-c",
     "import sys, importlib.util\n"
     "from pathlib import Path\n"
     "spec = importlib.util.spec_from_file_location('sim2', %r)\n"
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
     "print(txt[txt.find('ABORT-CLASS'):txt.find('ABORT-CLASS')+120])"
     % (str(SIM), str(FIX_CELLS))],
    capture_output=True, text=True)
check("V6 m002_sim_v2 on the fixed cells: 0 abort sites",
      "ABORT_ZERO" in sim_out.stdout,
      sim_out.stdout.strip().splitlines()[-1][:100]
      if sim_out.stdout.strip() else sim_out.stderr[-100:])

# ════════════════════════════════════════════════════════════════════
# summary
# ════════════════════════════════════════════════════════════════════
n_ok = sum(RESULTS)
print("\n" + "=" * 72)
print(f"B3 Phase C VERIFY: {n_ok}/{len(RESULTS)} PASS")
print("=" * 72)
sys.exit(0 if n_ok == len(RESULTS) else 1)
