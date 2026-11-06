#!/usr/bin/env python3
r"""MANGABD-009 B2.1 Phase C — verification instrument (branch mangabd-009-b2-1).

Verifies the ruled B2.1 scope (RB21-2 guard except-WARN allowlist +
RB21-3 never-save-blank quarantine; RB21-1/RB21-4 = NO change):

  V1  static: scope drift exactly {10} vs 67bc594; RB2-7 named cells
      {6,7,11,12,24} + reading-order {13,15,23} byte-identical (cell 6
      byte-identity also proves item 4 untouched — the ring margin +
      estimator live there); item-1 surfaces (_b2_gt_tilted_layout incl.
      the vjust block) byte-untouched; AST 27/27 warnings-as-errors;
      manifest re-derivation; production rotate/paste block +
      _b2_render_angle + battery Tests 16/17-18/19/21 blocks + the
      RF-13 hygiene tail byte-untouched; secret scan on the delta
  V2  dynamic battery via scripts/m009_b21_phaseC_harness.py (cells
      01-07+10 verbatim, env stubs disclosed there): cell-10 SUCCESS,
      Test 22 PASS, Tests 19+21 PASS, ledger 21/21, quarantine + guard
      WARN events both exercised
  V3  fail-on-current-bytes contract (span-exec, base 67bc594 vs work):
      the Test 22 scenario — forced all-fail render with a renderable
      row — on BASE saves the blank final + marks done + no WARN (the
      contract FAILS on current bytes = the poison-cache write), on
      WORK saves quarantine/ + no stage-done + WARN; recovery re-render
      inks on both (base via the RF-14 guard — the resume half; work
      because it was never marked done — the fresh half closed);
      eyeball render (no translations) keeps final+done on BOTH
  V4  healthy-path render parity: S003/S007/S009/S010/S011 fresh
      renders byte-IDENTICAL base vs work + render-meta parity + no
      quarantine side effects (the rendered>0 path never consults the
      predicate)
  V5  guard edge matrix + the RB21-2 delta: return-value parity on all
      six edges (healthy / cold-start / marker-only / renderable /
      corrupted-meta / missing-page); WARN parity on the expected
      classes; WARN delta exactly on the unexpected classes (base
      silent, work loud)
  V6  m002_sim_v2 fresh-kernel simulator on the fixed cells: 0 abort
      sites
"""
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
BASE_REF = "67bc594"
BRANCH = "mangabd-009-b2-1"
FONTS = Path("/home/z/my-project/m008_probe/fonts")
S003 = REPO / "samples" / "S003_batch2"
S007_ZIP = REPO / "S007_mangabd005_02.zip"
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
HARNESS = REPO / "scripts" / "m009_b21_phaseC_harness.py"
FIX_CELLS = Path("/home/z/my-project/cells_b21_fix")
MANIFEST = REPO / "scripts" / "m009_b21_phaseC_patches.json"

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
print("MANGABD-009 B2.1 Phase C — VERIFY (branch mangabd-009-b2-1)")
print("=" * 72)

# ════════════════════════════════════════════════════════════════════
# V1 — static integrity
# ════════════════════════════════════════════════════════════════════
print("\n── V1 static integrity ──")
check("V1a branch mangabd-009-b2-1",
      git("branch", "--show-current").strip() == BRANCH)

raw_work, nb_work, cells_work = load_cells(NB)
raw_base = git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8")
nb_base = json.loads(raw_base.decode("utf-8"))
cells_base = ["".join(c.get("source", [])) for c in nb_base["cells"]
              if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_work[i] != cells_base[i]]
check("V1b scope drift exactly {10} (cells {10} ONLY per the ruling)",
      sorted(scope) == [10], f"drift={sorted(scope)}")
for i in (6, 7, 11, 12, 24):
    check(f"V1c RB2-7 named cell {i} byte-identical"
          + (" (item 4 ring margin + estimator live here — untouched)"
             if i == 6 else ""),
          cells_work[i] == cells_base[i])
for i in (13, 15, 23):
    check(f"V1d reading-order cell {i} byte-identical",
          cells_work[i] == cells_base[i])

with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        try:
            compile(cells_work[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL cell {i} warning-as-error: {w}")
check("V1e AST compile 27/27 (warnings-as-errors)", True)

patches = json.loads(MANIFEST.read_text(encoding="utf-8"))
re_src = list(cells_base)
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"{p['name']} anchor"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("V1f re-derivation (work == 67bc594 + exactly the manifest)",
      all(re_src[i] == cells_work[i] for i in range(27)),
      f"{len(patches)} patches: " + "; ".join(p["name"] for p in patches))

# production surfaces byte-untouched
rot_old = extract_span(cells_base[10], "rotated = text_canvas.rotate(",
                       "return image_pil")
rot_new = extract_span(cells_work[10], "rotated = text_canvas.rotate(",
                       "return image_pil")
check("V1g production rotate/paste block byte-untouched", rot_old == rot_new)
mir_old = extract_span(cells_base[10], "def _b2_render_angle(",
                       'print("  ✅ B2 render-angle mirror ready')
mir_new = extract_span(cells_work[10], "def _b2_render_angle(",
                      'print("  ✅ B2 render-angle mirror ready')
check("V1h _b2_render_angle mirror byte-untouched", mir_old == mir_new)
# item 1 (asymmetric parity / vjust) explicitly untouched
gtl_old = extract_span(cells_base[10], "def _b2_gt_tilted_layout",
                       "def render_bengali_text")
gtl_new = extract_span(cells_work[10], "def _b2_gt_tilted_layout",
                      "def render_bengali_text")
check("V1i item-1 surface _b2_gt_tilted_layout (incl. vjust block) "
      "byte-untouched (RB21-1 REJECT = no change)", gtl_old == gtl_new)

# battery blocks byte-untouched
t16_old = extract_span(cells_base[10], "# Test 16: B2 estimator",
                       "# Test 17: B2 render side")
t16_new = extract_span(cells_work[10], "# Test 16: B2 estimator",
                       "# Test 17: B2 render side")
check("V1j battery Test 16 block byte-untouched", t16_old == t16_new)
t1718_old = extract_span(cells_base[10], "# Test 17: B2 render side",
                         "# Test 19: B2 RF-14")
t1718_new = extract_span(cells_work[10], "# Test 17: B2 render side",
                         "# Test 19: B2 RF-14")
check("V1k battery Tests 17-18 byte-untouched", t1718_old == t1718_new)
t19_old = extract_span(cells_base[10], "# Test 19: B2 RF-14",
                       "# Test 21: B2 RF-18")
t19_new = extract_span(cells_work[10], "# Test 19: B2 RF-14",
                       "# Test 21: B2 RF-18")
check("V1l battery Test 19 (RF-14 regression) byte-untouched",
      t19_old == t19_new)
t21_old = extract_span(cells_base[10], "# Test 21: B2 RF-18",
                       "# RF-13 fixture hygiene:")
t21_new = extract_span(cells_work[10], "# Test 21: B2 RF-18",
                       "# Test 22: B2.1")
check("V1m battery Test 21 (RF-18 parity) byte-untouched "
      "(22 inserted after it)", t21_old == t21_new)
hyg_old = extract_span(cells_base[10], "# RF-13 fixture hygiene:")
hyg_new = extract_span(cells_work[10], "# RF-13 fixture hygiene:")
check("V1n RF-13 hygiene tail byte-untouched", hyg_old == hyg_new)
t22_span = extract_span(cells_work[10], "# Test 22: B2.1",
                        "# RF-13 fixture hygiene:")
check("V1o Test 22 wiring (fail-on-current-bytes contract)",
      "B2.1 RB21-2/RB21-3: blank-render quarantine" in t22_span
      and "_t22_ok_a and _t22_ok_b and _t22_ok_c and _t22_ok_d" in t22_span
      and 'reset_page("__b21_t22__", delete_artifacts=True)' in t22_span
      and t22_span.count("render_page(_t22_pid,") == 2)

# secret scan on the delta
delta = "\n".join(p["new"] for p in patches)
hits = [kw for kw in ("api_key", "password", "secret", "token=")
        if kw in delta.lower()]
check("V1p secret scan on the patch delta", not hits, f"hits={hits}")

# quarantine never uses the final artifact slot
check("V1q quarantine path = page-dir sibling quarantine/, final slot "
      "save unchanged",
      cells_work[10].count('get_page_dir(page_id) / "quarantine"') == 1
      and cells_work[10].count(
          'save_image_artifact(page_id, "final", canvas_pil, quality=95)'
      ) == 1)

# ════════════════════════════════════════════════════════════════════
# V2 — battery on the work bytes (harness subprocess)
# ════════════════════════════════════════════════════════════════════
print("\n── V2 dynamic battery (harness, cells verbatim) ──")
hout = subprocess.run([sys.executable, str(HARNESS)],
                      capture_output=True, text=True, timeout=570)
txt = hout.stdout + hout.stderr
check("V2a cell-10 battery final result SUCCESS",
      "CELL10_RESULT: SUCCESS" in txt,
      (hout.stderr[-120:] if "CELL10_RESULT" not in txt else ""))
check("V2b Test 22 PASS (fail-on-current-bytes contract holds on the "
      "fixed bytes)", "TEST22: PASS" in txt)
check("V2c Tests 19+21 still PASS (RF-14/RF-18 regressions intact)",
      "TEST19: PASS" in txt and "TEST21: PASS" in txt)
m = re.search(r"BATTERY_EVENTS: tests_passed=(\d+) tests_total=(\d+) "
              r"tests_skipped=(\d+)", txt)
check("V2d battery ledger all-pass",
      bool(m) and m.group(1) == m.group(2),
      f"passed={m.group(1) if m else '?'}/{m.group(2) if m else '?'} "
      f"(19 @ RF-14 -> 20 @ RF-18 -> 21 with Test 22)")
m2 = re.search(r"EVENT_EVIDENCE: quarantine_warns=(\d+) guard_warns=(\d+)",
               txt)
check("V2e both new WARN routes exercised in-battery",
      bool(m2) and m2.group(1) == "1" and m2.group(2) == "1",
      f"quarantine={m2.group(1) if m2 else '?'} "
      f"guard={m2.group(2) if m2 else '?'}")

# ════════════════════════════════════════════════════════════════════
# shared span-exec machinery (V3/V4/V5)
# ════════════════════════════════════════════════════════════════════


def make_ns():
    ns = {"__name__": "m009_b21_verify"}
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


class FilePages:
    """File-backed page/artifact store (V3/V4/V5 stub set)."""

    def __init__(self, root):
        self.root = Path(root)
        self.pages = {}
        self.saved = []   # (pid, artifact_name) ledger
        self.marks = []   # (pid, stage, meta) ledger

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
            return cv2.imread(str(q), cv2.IMREAD_COLOR) if q.exists() else None
        ns["load_image_artifact"] = load_image_artifact

        def load_json_artifact(pid, name, default=None):
            q = store.root / "pages" / pid / "detections.json"
            if name == "detections" and q.exists():
                return json.loads(q.read_text(encoding="utf-8"))
            return default
        ns["load_json_artifact"] = load_json_artifact

        ns["save_translation_df"] = lambda df=None: None
        ns["load_translation_df"] = lambda: None
        ns["reset_page"] = lambda pid, from_stage=None, delete_artifacts=False: None
        return ns


def cell10_spans(cells):
    cfg = extract_span(cells[10], "# 2. Rendering config defaults",
                       "# 3. Text helpers")
    core = extract_span(cells[10], "# 3. Text helpers",
                        "# 10. Self-tests")
    return cfg, core


def core_ns(side):
    """Fresh namespace with the given side's cfg+core exec'd."""
    tmp = tempfile.mkdtemp(prefix=f"b21_{side}_")
    store = FilePages(tmp)
    ns = make_ns()
    store.bind(ns)
    cfg, core = cell10_spans(cells_base if side == "base" else cells_work)
    exec(compile(cfg, f"<c10 {side} cfg>", "exec"), ns)
    exec(compile(core, f"<c10 {side} core>", "exec"), ns)
    return ns, store


T22_DET = [{
    "id": 1, "page_id": "pg", "x": 60, "y": 80,
    "width": 200, "height": 90,
    "quad": [[60, 80], [260, 80], [260, 170], [60, 170]],
    "angle": 0.0, "region_type": "bubble",
    "detector_class": "text_bubble", "detector_score": 0.9,
    "parent_bubble_id": None,
}]


def t22_row(pid, text):
    return {
        "page_id": pid, "id": 1, "region_type": "bubble",
        "x": 60, "y": 80, "width": 200, "height": 90,
        "angle": 0.0, "translated_text": text,
        "bengali_valid": bool(text), "status": "ok",
    }


# ════════════════════════════════════════════════════════════════════
# V3 — fail-on-current-bytes contract (base vs work)
# ════════════════════════════════════════════════════════════════════
print("\n── V3 fail-on-current-bytes contract (span-exec) ──")

V3 = {}
for side in ("base", "work"):
    ns, store = core_ns(side)
    canvas = np.full((400, 600, 3), 255, np.uint8)
    store.init("pg", T22_DET, canvas)
    ns["translation_df"] = pd.DataFrame([t22_row("pg", "এই কী হয়েছে বলো তো?!")])

    orig_rbt = ns["render_bengali_text"]

    def boom(*a, **k):
        raise RuntimeError("v3 forced render failure")
    ns["render_bengali_text"] = boom
    ev0 = len(ns["MANGABD_EVENTS"])
    ns["render_page"]("pg", force=True)
    ns["render_bengali_text"] = orig_rbt

    final_a = (store.root / "pages" / "pg" / "final.jpg").exists()
    quar_a = (store.root / "pages" / "pg" / "quarantine" / "final.jpg").exists()
    done_a = bool(store.pages["pg"]["stages"].get("render"))
    warn_a = [e for e in ns["MANGABD_EVENTS"][ev0:]
              if e["level"] == "WARN" and "quarantined" in e["message"]]

    # recovery: re-render with the real engine
    out = ns["render_page"]("pg", force=False)
    roi = np.abs(out[80:170, 60:260].astype(int)
                 - canvas[80:170, 60:260].astype(int)).sum(axis=2)
    ink_b = int((roi > 30).sum())
    stale_bypass = [e for e in ns["MANGABD_EVENTS"][ev0:]
                    if e["level"] == "WARN"
                    and "Stale blank render cache bypassed" in e["message"]]

    # eyeball: no renderable rows -> final + done (today's behavior)
    store.init("eye", T22_DET, canvas)
    ns["translation_df"] = pd.DataFrame([t22_row("eye", "")])
    ns["render_page"]("eye", force=False)
    eye_final = (store.root / "pages" / "eye" / "final.jpg").exists()
    eye_done = bool(store.pages["eye"]["stages"].get("render"))
    eye_quar = (store.root / "pages" / "eye" / "quarantine").exists()

    V3[side] = dict(final_a=final_a, quar_a=quar_a, done_a=done_a,
                    warn_a=len(warn_a), ink_b=ink_b,
                    stale_bypass=len(stale_bypass),
                    eye_final=eye_final, eye_done=eye_done,
                    eye_quar=eye_quar,
                    final_saves=store.saved.count(("pg", "final")))

b, w = V3["base"], V3["work"]
check("V3a BASE (67bc594): blank final SAVED + stage DONE — the "
      "Test-22 contract FAILS on current bytes (poison-cache write "
      "live-proven)",
      b["final_a"] and b["done_a"] and not b["quar_a"] and b["warn_a"] == 0,
      f"final={b['final_a']} done={b['done_a']} "
      f"quarantine={b['quar_a']} warn={b['warn_a']}")
check("V3b WORK: blank final NOT saved, quarantine/final.jpg saved, "
      "stage NOT done, WARN logged (RB21-3)",
      (not w["final_a"]) and w["quar_a"] and (not w["done_a"])
      and w["warn_a"] == 1,
      f"final={w['final_a']} quarantine={w['quar_a']} "
      f"done={w['done_a']} warn={w['warn_a']}")
check("V3c recovery re-render inks on both (base via the RF-14 guard "
      "= resume half; work because never marked done = fresh half "
      "closed)",
      b["ink_b"] >= 50 and w["ink_b"] >= 50,
      f"ink base={b['ink_b']} work={w['ink_b']}; stale-bypass WARN "
      f"base={b['stale_bypass']} work={w['stale_bypass']} (work never "
      "poisoned)")
check("V3d final-slot saves: base 2 (blank + re-render), work 1 "
      "(re-render only — the blank was never a final)",
      b["final_saves"] == 2 and w["final_saves"] == 1,
      f"base={b['final_saves']} work={w['final_saves']}")
check("V3e eyeball render (no translations) keeps final+done on BOTH "
      "sides, no quarantine",
      b["eye_final"] and b["eye_done"] and not b["eye_quar"]
      and w["eye_final"] and w["eye_done"] and not w["eye_quar"])

# ════════════════════════════════════════════════════════════════════
# V4 — healthy-path render parity (archives, base vs work)
# ════════════════════════════════════════════════════════════════════
print("\n── V4 healthy-path render parity ──")


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
            arr = cv2.imdecode(np.frombuffer(rd("inpainted.png"), np.uint8),
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
            meta=[m for m in store.marks if m[0] == sid and m[1] == "render"],
            saved=list(store.saved),
            quar=(store.root / "pages" / sid / "quarantine").exists(),
            warns=[e for e in ns["MANGABD_EVENTS"]
                   if e["level"] == "WARN" and "quarantin" in e["message"]],
        )
    same = outs["base"]["bytes"] == outs["work"]["bytes"]
    check(f"V4a {sid} fresh render byte-IDENTICAL (base vs work)",
          same, f"{len(outs['work']['bytes'])} B")
    check(f"V4b {sid} render meta parity + no quarantine side effects",
          outs["base"]["meta"] == outs["work"]["meta"]
          and not outs["work"]["quar"] and not outs["work"]["warns"]
          and outs["work"]["saved"] == [(sid, "final")],
          f"meta={outs['work']['meta'][-1][2] if outs['work']['meta'] else '?'}")

# ════════════════════════════════════════════════════════════════════
# V5 — guard edge matrix + RB21-2 delta
# ════════════════════════════════════════════════════════════════════
print("\n── V5 guard edge matrix (return parity + WARN delta) ──")


def guard_edges(side):
    ns, store = core_ns(side)
    canvas = np.full((400, 600, 3), 255, np.uint8)
    out = {}

    def ev_len():
        return len(ns["MANGABD_EVENTS"])

    def warns_since(n):
        return [e for e in ns["MANGABD_EVENTS"][n:]
                if e["level"] == "WARN"]

    # E1 healthy page: rendered=3
    store.init("e1", T22_DET, canvas, meta={"rendered_regions": 3})
    ns["translation_df"] = pd.DataFrame([t22_row("e1", "এই কী হয়েছে বলো তো?!")])
    n = ev_len(); out["E1"] = (ns["_b2_blank_cache_stale"]("e1"), warns_since(n))

    # E2 cold-start: rendered=0, df empty, TRANSLATION_CSV missing
    store.init("e2", T22_DET, canvas, meta={"rendered_regions": 0})
    ns["translation_df"] = pd.DataFrame()
    ns["TRANSLATION_CSV"] = Path(tempfile.mkdtemp()) / "no_such.csv"
    n = ev_len(); out["E2"] = (ns["_b2_blank_cache_stale"]("e2"), warns_since(n))

    # E3 marker-only rows
    store.init("e3", T22_DET, canvas, meta={"rendered_regions": 0})
    ns["translation_df"] = pd.DataFrame([t22_row("e3", "[KEEP]")])
    n = ev_len(); out["E3"] = (ns["_b2_blank_cache_stale"]("e3"), warns_since(n))

    # E4 renderable row present -> True (the trap condition)
    store.init("e4", T22_DET, canvas, meta={"rendered_regions": 0})
    ns["translation_df"] = pd.DataFrame([t22_row("e4", "এই কী হয়েছে বলো তো?!")])
    n = ev_len(); out["E4"] = (ns["_b2_blank_cache_stale"]("e4"), warns_since(n))

    # E5 corrupted meta (unexpected class)
    store.init("e5", T22_DET, canvas,
               meta={"rendered_regions": "not-a-number"})
    ns["translation_df"] = pd.DataFrame([t22_row("e5", "এই কী হয়েছে বলো তো?!")])
    n = ev_len(); out["E5"] = (ns["_b2_blank_cache_stale"]("e5"), warns_since(n))

    # E6 missing page (KeyError from get_page required=True)
    n = ev_len()
    try:
        ns["_b2_blank_cache_stale"]("no-such-page")
        out["E6"] = (False, warns_since(n))
    except Exception as exc:
        out["E6"] = (f"RAISED {type(exc).__name__}", warns_since(n))
    return out


gb, gw = guard_edges("base"), guard_edges("work")
check("V5a return-value parity on all six edges (fail-open False / "
      "trap True unchanged)",
      all(gb[k][0] == gw[k][0] for k in gb),
      str({k: (gb[k][0], gw[k][0]) for k in gb}))
check("V5b E4 trap condition still True (RF-14 semantics intact)",
      gb["E4"][0] is True and gw["E4"][0] is True)
check("V5c cold-start E2: silent on BOTH (allowlist; base had no WARN "
      "anywhere)",
      gb["E2"][0] is False and not gb["E2"][1]
      and gw["E2"][0] is False and not gw["E2"][1],
      f"base_warn={len(gb['E2'][1])} work_warn={len(gw['E2'][1])}")
check("V5d RB21-2 delta: unexpected classes (E5 corrupted-meta, E6 "
      "missing-page) WARN on work, silent on base (the closed silent "
      "route)",
      not gb["E5"][1] and not gb["E6"][1]
      and len(gw["E5"][1]) == 1 and len(gw["E6"][1]) == 1
      and all("guard raised" in e["message"] for e in gw["E5"][1] + gw["E6"][1]),
      f"E5 warn base/work={len(gb['E5'][1])}/{len(gw['E5'][1])} "
      f"E6={len(gb['E6'][1])}/{len(gw['E6'][1])}")

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
print(f"B2.1 Phase C VERIFY: {n_ok}/{len(RESULTS)} PASS")
print("=" * 72)
sys.exit(0 if n_ok == len(RESULTS) else 1)
