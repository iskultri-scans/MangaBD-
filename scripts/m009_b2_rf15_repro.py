#!/usr/bin/env python3
"""MANGABD-009 B2 RF-15 — V-3 wrapper kwarg mismatch: full-chain repro harness.

Owner live failure (Run All, first full-chain 10->11->12->15 in one kernel):
every region "render_bengali_text() got an unexpected keyword argument
'fit_w'" -> rendered=0, warnings=8, blank final.

Root cause (bytes, this harness reproduces it): cell-10 render_page calls
render_bengali_text(..., fit_result=, fit_w=, fit_h=) UNCONDITIONALLY
(RB2-5 quad-extents fit dims; None for non-tilted, kwarg always passed);
the cells 11/12 V-3 wrapper that rebinds the global name in Run All stops
its signature at fit_result=None -> TypeError at CALL time for EVERY
region class -> render_page's per-row except swallows it as a WARN ->
rendered=0, blank final. Battery never saw it (runs inside cell 10,
wrapper undefined); chain tests called the wrapper directly; no
instrument ever ran render_page AFTER cells 11/12 in one namespace.

This harness IS that instrument: cells [1,2,3,4,5,6,7,10,11,12,15] exec'd
VERBATIM in ONE namespace (Run-All order, incl. the Owner's cell-15
orchestrator), then the full chain over synthetic AI-gen-like pages,
then per-region ink + MANGABD_EVENTS evidence.

Env-level stubs — cell source bytes stay VERBATIM (disclosed, same class
as the RF-14 harness, imported from it):
  * torch  : inert stub (no CUDA) — RT-DETR inference harness-stubbed
  * pathlib: /content* + /root* remapped into <HARNESS>
  * cell_00: runtime side effects seeded (env vars + MANGABD_ENV dict)
  * rtdetr_detect        : ground-truth boxes for the synthetic bubbles
  * run_ocr_engine       : per-region Japanese text
  * model_manager.ensure_ocr_engine : no-op truthy
  * cell_04 RuntimeError : tolerated ONLY for the zyddnys torch-import
    chain (CTD/LaMa inpaint deps, out of the render path; RF-14 legacy)
  * cell_12 RuntimeError : tolerated ONLY for the RF-15 integration
    battery marker on refs where the battery is REQUIRED to fail
    (fail-on-current-bytes proof); on the fix ref it must NOT fire

Refs:
  post = 84aa238 (branch tip: RF-14 CLOSED by Flash re-verify)
  work = working tree (the RF-15 fix)
  b1   = f218b35 (B1 final merge — pre-B2 control)
"""
import contextlib
import hashlib
import io
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path("/home/z/my-project/MangaBD")
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
HARNESS = Path("/home/z/my-project/rf15_home")
REPORTS = Path("/home/z/my-project/rf15_reports")
CELLS = {
    "post": Path("/home/z/my-project/cells_rf15_post"),
    "work": Path("/home/z/my-project/cells_rf15_work"),
    "b1": Path("/home/z/my-project/cells_rf15_b1"),
}
REFS = {"post": "84aa238", "work": None, "b1": "f218b35"}

# RF-14 harness reuse (env shims + synthetic pages — same disclosed stubs)
sys.path.insert(0, str(REPO / "scripts"))
from m009_b2_rf14_repro import (  # noqa: E402
    FONTS, build_pages, battery_summary, exec_cells as rf14_exec_cells,
    install_pathlib_shim, make_torch_stub, restore_pathlib,
    seed_cell00_side_effects, BENGALI_BY_KIND,
)

# Run-All order: the Owner's "first full-chain 10->11->12->15 in one
# kernel". cell_23 (translate-stage sync — the UI step_4 pre-step) is
# exec'd too, verbatim, so run_render_all sees the translate stage
# exactly like the Owner's button press. cell_08/09 (translate service
# + inpaint engines) stay out (Owner facts: inpaint OK, translations
# already applied — the harness supplies the synthetic clean-page
# inpainted artifact + applies Bengali directly, RF-14 owner_session
# pattern).
CELL_IDS = [1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 15, 23]

VISIBLE_INK_FLOOR = 50


def log(msg):
    print(f"[rf15] {msg}", flush=True)


def nb_blob(ref):
    if REFS[ref] is None:
        return (REPO / NB_NAME).read_bytes()
    out = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{REFS[ref]}:{NB_NAME}"],
        capture_output=True, check=True)
    return out.stdout


def extract_cells(ref):
    nb = json.loads(nb_blob(ref).decode("utf-8"))
    outdir = CELLS[ref]
    outdir.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(nb["cells"]):
        src = "".join(c.get("source", []))
        (outdir / f"cell_{i:02d}.py").write_text(src, encoding="utf-8")
    sha = hashlib.sha256(nb_blob(ref)).hexdigest()
    log(f"extracted {ref}: {len(nb['cells'])} cells -> {outdir} "
        f"(blob sha {sha[:8]})")
    return outdir


def exec_cells(cell_dir, battery_must_fail):
    """Verbatim exec in ONE namespace. Returns (ns, logs, battery_failed).

    battery_must_fail: True -> a cell-12 RuntimeError carrying the RF-15
    integration-battery marker is EXPECTED (fail-on-current-bytes proof)
    and is recorded, not raised. False -> any such raise is a harness
    FAILURE (the fix must clear it).
    """
    ns = {"__name__": "__mangabd__"}
    logs = {}
    battery_failed = None
    seed_cell00_side_effects(ns)
    install_pathlib_shim()
    try:
        for cid in CELL_IDS:
            src = (cell_dir / f"cell_{cid:02d}.py").read_text(encoding="utf-8")
            code = compile(src, f"cell_{cid:02d}.py", "exec")
            buf = io.StringIO()
            log(f"exec cell_{cid:02d} ({len(src)} bytes) ...")
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code, ns)
            except RuntimeError as exc:
                txt = str(exc)
                # RF-15 battery gate: cell 12 raises when the wrapper
                # kwarg seam fires (fail-on-current-bytes contract)
                if (cid == 12 and "RF-15" in txt
                        and "integration battery" in txt):
                    battery_failed = txt
                    if battery_must_fail:
                        log("cell_12: RF-15 integration battery FAILED "
                            "as required on these bytes (fail-on-current-"
                            "bytes proof) — recorded, exec continues")
                    else:
                        raise
                # RF-14 legacy tolerance: cell_04 zyddnys torch imports
                elif cid == 4 and "Cell 4 self-tests failed" in txt:
                    fail_lines = [ln for ln in buf.getvalue().splitlines()
                                  if "❌" in ln]
                    zyddnys_only = fail_lines and all(
                        ("ComicTextDetector" in ln
                         or "LamaLargeInpainter" in ln)
                        for ln in fail_lines)
                    render_green = all(
                        m in buf.getvalue() for m in (
                            "Bengali font render test passed",
                            "libraqm available",
                            "Bengali render test",
                        ))
                    if zyddnys_only and render_green:
                        log("cell_04: env-limited zyddnys torch-imports "
                            "only (torch stub; CTD/LaMa = inpaint deps, "
                            "out of scope) — tolerated (DISCLOSED)")
                    else:
                        raise
                else:
                    raise
            logs[cid] = buf.getvalue()
            tail = [ln for ln in logs[cid].splitlines() if ln.strip()]
            log(f"cell_{cid:02d} done ({len(tail)} lines); tail: "
                f"{tail[-1][:100] if tail else '<empty>'}")
    finally:
        restore_pathlib()
    return ns, logs, battery_failed


def owner_chain(ns, pages, ocr_stub_map, label):
    """The Owner's full chain in the already-populated namespace:
    register -> detect -> ocr -> apply Bengali -> synthetic inpaint ->
    run_render_all (cell-15 orchestrator, the step_4 equivalent)."""
    log(f"=== OWNER_CHAIN {label} ===")
    ev0 = len(ns["MANGABD_EVENTS"])

    for page in pages:
        pid = ns["init_page"](page["filename"],
                              width=page["full"].shape[1],
                              height=page["full"].shape[0],
                              image_np=page["full"], overwrite=True)
        page["page_id"] = pid
        boxes = [{"x": b["box"][0], "y": b["box"][1], "w": b["box"][2],
                  "h": b["box"][3], "score": 0.9,
                  "detector_class": b["detector_class"]}
                 for b in page["boxes"]]
        ns["rtdetr_detect"] = lambda img: {
            "text_bubble_boxes": [b for b in boxes
                                  if b["detector_class"] == "text_bubble"],
            "text_free_boxes": [b for b in boxes
                                if b["detector_class"] == "text_free"],
            "bubble_boxes": [],
        }
        ns["detect_page"](pid, page["full"], force=True)
        ns["run_ocr_engine"] = lambda name, img, region, page_id=None: (
            ocr_stub_map.get(
                tuple(int(region.get(k, 0)) for k in ("x", "y")),
                {"text": "テスト", "confidence": 0.9, "engine": name,
                 "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
                 "warnings": [], "is_english": True, "status": "ok",
                 "vertical_ocr": None})
        )
        ns["ocr_page"](pid, page["full"], force=True)
        ns["save_image_artifact"](pid, "inpainted", page["clean"], quality=95)
        ns["mark_stage_done"](pid, "inpaint",
                              meta={"inpaint_engine": "synthetic"})

    # Owner-like apply: ALL rows get Bengali (clean accounting: every
    # region must render; the live run had 8/9 -> warnings=8)
    df = ns["translation_df"]
    applied = 0
    for page in pages:
        rows = df[df["page_id"] == page["page_id"]]
        for idx, row in rows.iterrows():
            key = (int(row["x"]), int(row["y"]))
            beng = ocr_stub_map.get(key, {}).get(
                "__bengali", "এই কী হয়েছে বলো তো!")
            df.at[idx, "translated_text"] = beng
            applied += 1
    ns["save_translation_df"]()
    log(f"applied {applied} Bengali translations to translation_df")

    # THE seam moment: step_4 = sync_translate_stage (cell-23) ->
    # run_render_all (cell-15 orchestrator) -> render_all_pages ->
    # render_page -> global render_bengali_text == the cell-12 wrapper
    ev1 = len(ns["MANGABD_EVENTS"])
    ns["sync_translate_stage"]()
    ns["run_render_all"](force=True, require_translation=True)

    new_events = ns["MANGABD_EVENTS"][ev1:]
    typerr = [e for e in new_events
              if "unexpected keyword argument" in str(e.get("message", ""))]
    kwarg_names = sorted({str(e["message"]).split("'")[-2]
                          for e in typerr if "'" in str(e["message"])})
    render_fails = [e for e in new_events
                    if str(e.get("message", "")).startswith("Render failed")]

    out = []
    for page in pages:
        final = ns["load_image_artifact"](page["page_id"], "final")
        clean = page["clean"]
        det_rows = ns["load_json_artifact"](page["page_id"], "detections",
                                            default=[])
        page_out = {"page": page["filename"], "regions": [],
                    "total_ink": 0}
        for r in det_rows:
            x, y, w, h = r["x"], r["y"], r["width"], r["height"]
            m = 34
            x0, y0 = max(0, x - m), max(0, y - m)
            x1 = min(final.shape[1], x + w + m)
            y1 = min(final.shape[0], y + h + m)
            diff = np.abs(final[y0:y1, x0:x1].astype(int)
                          - clean[y0:y1, x0:x1].astype(int)).sum(axis=2)
            ink = int((diff > 30).sum())
            page_out["total_ink"] += ink
            page_out["regions"].append({
                "id": r["id"], "angle": r["angle"],
                "quad": bool(r.get("quad")),
                "w": w, "h": h, "ink_px": ink,
                "zero": ink < VISIBLE_INK_FLOOR,
            })
            log(f"  {page['filename']} region {r['id']}: "
                f"angle={r['angle']:+.2f} quad={'Y' if r.get('quad') else 'N'} "
                f"{w}x{h} ink={ink:>6} "
                f"[{'VISIBLE' if ink >= VISIBLE_INK_FLOOR else 'ZERO-INK'}]")
        # re-read the global: save_translation_df() rebinds it (column
        # re-selection), so the apply-time reference would be stale
        rows2 = ns["translation_df"][
            ns["translation_df"]["page_id"] == page["page_id"]]
        page_out["status"] = rows2["status"].value_counts().to_dict()
        out.append(page_out)
        log(f"  {page['filename']}: total ink={page_out['total_ink']}, "
            f"df status={page_out['status']}")

    n_regions = sum(len(p["regions"]) for p in out)
    n_zero = sum(1 for p in out for r in p["regions"] if r["zero"])
    n_rendered = sum(p["status"].get("rendered", 0) for p in out)
    log(f"regions={n_regions} zero-ink={n_zero} rendered(df)={n_rendered} "
        f"TypeError-events={len(typerr)} kwargs={kwarg_names} "
        f"Render-failed-WARNs={len(render_fails)}")
    if typerr:
        for e in typerr[:3]:
            log(f"    TypeError evidence: {str(e['message'])[:130]}")
    repro = bool(typerr) or n_rendered == 0 or n_zero == n_regions
    log(f"OWNER_CHAIN verdict: "
        f"{'RF-15 SEAM REPRODUCED (wrapper kwarg TypeError)' if repro else 'RF-15 SEAM FIXED (all regions rendered)'}")
    return {"pages": out, "repro": repro, "typerr": len(typerr),
            "kwarg_names": kwarg_names, "render_fails": len(render_fails),
            "n_regions": n_regions, "n_rendered": n_rendered,
            "n_zero": n_zero}


def make_mutant_cells():
    """work cells with ONLY the two wrapper-signature patches reverted
    (battery patch KEPT) — the fail-on-current-bytes construction: the
    new battery running against the old, broken wrapper bytes."""
    man = json.loads((REPO / "scripts" / "m009_b2_rf15_patches.json")
                     .read_text(encoding="utf-8"))
    wrapper_patches = [p for p in man if "wrapper" in p["name"]]
    assert len(wrapper_patches) == 2, \
        f"expected 2 wrapper patches, got {len(wrapper_patches)}"
    src = {
        i: (CELLS["work"] / f"cell_{i:02d}.py").read_text(encoding="utf-8")
        for i in CELL_IDS
    }
    for p in wrapper_patches:
        assert src[p["cell"]].count(p["new"]) == 1, p["name"]
        src[p["cell"]] = src[p["cell"]].replace(p["new"], p["old"])
    outdir = Path("/home/z/my-project/cells_rf15_mutant")
    outdir.mkdir(parents=True, exist_ok=True)
    for i, s in src.items():
        (outdir / f"cell_{i:02d}.py").write_text(s, encoding="utf-8")
    # non-exec'd cells copied verbatim for completeness
    for i in range(27):
        f = outdir / f"cell_{i:02d}.py"
        if not f.exists():
            f.write_text((CELLS["work"] / f"cell_{i:02d}.py")
                         .read_text(encoding="utf-8"), encoding="utf-8")
    log("mutant cells built: work bytes minus the 2 wrapper patches "
        "(battery kept) -> " + str(outdir))
    return outdir


def run_ref(ref, battery_must_fail, cell_dir=None):
    log(f"=== RUN ref={ref} battery_must_fail={battery_must_fail} ===")
    if HARNESS.exists():
        shutil.rmtree(HARNESS)
    fonts_dir = HARNESS / "content" / "mangabd" / "fonts"
    fonts_dir.mkdir(parents=True)
    shutil.copy(FONTS / "NotoSansBengali-Regular.ttf",
                fonts_dir / "NotoSansBengali-Regular.ttf")
    shutil.copy(FONTS / "NotoSansBengali-Regular.ttf",
                fonts_dir / "NotoSansBengali-Bold.ttf")
    shutil.copy(FONTS / "NotoSansJP.ttf", fonts_dir / "NotoSansJP.ttf")

    if cell_dir is None:
        cell_dir = extract_cells(ref)
    sys.modules["torch"] = make_torch_stub()
    ns, logs, battery_failed = exec_cells(cell_dir, battery_must_fail)

    batt = battery_summary(logs)
    log("battery summaries: " + json.dumps(batt, ensure_ascii=False))
    cell12_txt = logs.get(12, "")
    battery_line = "ABSENT"
    for ln in cell12_txt.splitlines():
        if "RF-15" in ln and "integration" in ln:
            battery_line = ln.strip()
    log(f"cell-12 RF-15 battery line: {battery_line}")
    log(f"cell-12 battery raise: "
        f"{'YES (as required)' if battery_failed else 'no'}")

    ns["model_manager"].ensure_ocr_engine = lambda name, force=False: True

    pages = build_pages()
    ocr_stub_map = {}
    for page in pages:
        for b in page["boxes"]:
            key = (b["box"][0], b["box"][1])
            ocr_stub_map[key] = {
                "text": "テスト文章です。", "confidence": 0.9,
                "engine": "harness",
                "language_score": {"en": 1.0, "bn": 0.0, "unknown": 0.0},
                "warnings": [], "is_english": True, "status": "ok",
                "vertical_ocr": None,
                "__bengali": BENGALI_BY_KIND.get(
                    b["kind"], "এই কী হয়েছে বলো তো!"),
            }

    chain = owner_chain(ns, pages, ocr_stub_map, f"{ref}")
    return {"ref": ref, "battery_failed_raise": bool(battery_failed),
            "battery_line": battery_line, "chain": chain,
            "battery": batt}

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "post"
    REPORTS.mkdir(parents=True, exist_ok=True)
    runs = []
    if mode in ("post", "both"):
        # post = current branch bytes: the LIVE failure must reproduce
        # (TypeError events + rendered=0 + zero ink). No battery exists
        # in these bytes — the battery's own fail-proof is the mutant run.
        runs.append(run_ref("post", battery_must_fail=False))
    if mode in ("fix", "both"):
        # work = the RF-15 fix: the battery must PASS (no raise allowed)
        runs.append(run_ref("work", battery_must_fail=False))
    if mode == "mutant":
        # fail-on-current-bytes proof: the NEW battery against the OLD
        # wrapper bytes (work minus the 2 wrapper patches) must RAISE
        runs.append(run_ref("mutant", battery_must_fail=True,
                            cell_dir=make_mutant_cells()))
    if mode == "b1":
        runs.append(run_ref("b1", battery_must_fail=False))
    out = REPORTS / f"rf15_repro_{mode}.json"
    out.write_text(json.dumps(runs, ensure_ascii=False, indent=2,
                              default=str), encoding="utf-8")
    log(f"report -> {out}")

    verdicts = []
    for r in runs:
        if r["ref"] == "post":
            ok = (r["chain"]["repro"] and r["chain"]["typerr"] > 0
                  and r["chain"]["n_rendered"] == 0)
            verdicts.append(ok)
            tag = ("RF-15 LIVE FAILURE REPRODUCED (TypeError fit_w)"
                   if ok else "UNEXPECTED post state")
            log(f"VERDICT post: {tag}")
        elif r["ref"] == "work":
            ok = (not r["chain"]["repro"] and r["chain"]["typerr"] == 0
                  and not r["battery_failed_raise"]
                  and r["chain"]["n_rendered"] == r["chain"]["n_regions"]
                  and r["chain"]["n_zero"] == 0)
            verdicts.append(ok)
            tag = ("RF-15 FIXED (battery pass + full ink)"
                   if ok else "UNEXPECTED work state")
            log(f"VERDICT work: {tag}")
        elif r["ref"] == "mutant":
            ok = (r["battery_failed_raise"]
                  and r["chain"]["typerr"] > 0
                  and r["chain"]["n_rendered"] == 0)
            verdicts.append(ok)
            tag = ("BATTERY FAILS ON CURRENT BYTES (as required)"
                   if ok else "UNEXPECTED mutant state")
            log(f"VERDICT mutant: {tag}")
    return 0 if all(verdicts) else 1


if __name__ == "__main__":
    sys.exit(main())
