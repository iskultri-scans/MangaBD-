#!/usr/bin/env python3
r"""MANGABD-009 B3.1 — S012_manhwa_emphasis regression archive builder.

Commits the OWNER-REJECT page class (per-word emphasis coloring, the
live-REJECT corpus style @ cf01aef) permanently into the corpus. Like
S009/S010/S011, the Owner's live page bytes are not in the repo, so
S012 is a SYNTHESIZED owner-signature page (disclosed in metadata):

  * R1 emphasis4 (the owner case: black base + one red word + one
    blue word) — the class that made B3's region-level whole-
    population median inert (live-REJECT root cause);
  * R2 full-red shout; R3 two-hue SFX (line-level RB3-5 gate); R4
    all-black control; R5 purple-emphasis;
  * R6 narrow-tilted 3-line (w<80, gap 14 — the raw-locator split
    regime): the V5/narrow-fix pin (b2_gt_lines=3 via the B3.1 call
    site; close(5,5)x2 would merge to 1);
  * R7 tiny id=8 class (52x60, area 3120 >= 2000, 4 lines) — the
    tiny-text assertion pin;
  * R8 V-3 vertical note (gray ink — RB31-5 skip pin).

Archive contents (samples/S012_manhwa_emphasis/): original.jpg /
inpainted.png / text_mask.png / detections.json / ocr.json /
translation.json / final.jpg / metadata.json / b31_parity.json —
same shape as S009/S010/S011 (production-schema rows from the REAL
detect/OCR/render path on the B3.1 WORK bytes; the sandbox has no
onnxruntime so RT-DETR is stubbed to the true boxes and CTD to the
true text-ink prob map — disclosed).
"""
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

import cv2
import numpy as np

REPO = Path("/home/z/my-project/MangaBD")
sys.path.insert(0, str(REPO / "scripts"))
from m009_b2_rf18_chain import artifact_path, run_chain  # noqa: E402
from m009_b31_s012_page import (  # noqa: E402
    COL_BLUE, COL_PURPLE, COL_RED, PAGE_H, PAGE_W, RNG_SEED,
    build_s012_page, region_boxes_payload,
)

DEST = REPO / "samples" / "S012_manhwa_emphasis"

# ── 0. preconditions ────────────────────────────────────────────────
branch = subprocess.run(["git", "-C", str(REPO), "branch", "--show-current"],
                        capture_output=True, text=True).stdout.strip()
assert branch == "mangabd-009-b3", f"on branch {branch!r}"
nb_sha256 = hashlib.sha256(
    (REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt").read_bytes()).hexdigest()
print(f"notebook sha256: {nb_sha256[:16]}...")
assert not DEST.exists(), f"{DEST} already exists"

full, clean, regions, ink_mask = build_s012_page()
print(f"page drawn: {PAGE_W}x{PAGE_H}, {len(regions)} regions, "
      f"ink {int((ink_mask > 0).sum())} px")

# ── 1. run the full chain on the B3.1 WORK bytes ────────────────────
ns, pid, det_rows = run_chain("s012_manhwa_emphasis.jpg", full, clean,
                              regions, ink_mask)
print(f"chain done: {len(det_rows)} regions rendered")

gt_by_id = {}
for r in det_rows:
    best, bt = 0, None
    for g in regions:
        gx, gy, gw, gh = g["box"]
        ix = max(0, min(r["x"] + r["width"], gx + gw) - max(r["x"], gx))
        iy = max(0, min(r["y"] + r["height"], gy + gh) - max(r["y"], gy))
        if ix * iy > best:
            best, bt = ix * iy, g
    gt_by_id[int(r["id"])] = bt

# ── 2. collect the session artifacts ────────────────────────────────
DEST.mkdir(parents=True)
for kind in ("original", "detections", "ocr", "inpainted", "final"):
    src = artifact_path(ns, pid, kind)
    assert src.exists(), f"artifact {kind} missing: {src}"
    shutil.copy2(src, DEST / src.name)
    print(f"  archived {src.name} ({src.stat().st_size} B)")
cv2.imwrite(str(DEST / "text_mask.png"), ink_mask)
print(f"  archived text_mask.png (TRUE ink, "
      f"{int((ink_mask > 0).sum())} px)")

trans_rows = []
for r in det_rows:
    g = gt_by_id[int(r["id"])]
    trans_rows.append({
        "id": int(r["id"]), "region_type": r["region_type"],
        "original_text": g["jp"],
        "translated_text": g["bengali"],
        "translator_engine": "synthetic (B3.1 fixture)",
        "bengali_valid": True, "status": "rendered",
    })
with open(DEST / "translation.json", "w", encoding="utf-8") as f:
    json.dump(trans_rows, f, ensure_ascii=False, indent=1)
print(f"  archived translation.json ({len(trans_rows)} rows)")

# ── 3. ground-truth table + per-region acceptance (the B3.1 law) ────
def _close(a, b, tol=10):
    return (a is not None and b is not None
            and max(abs(a[0] - b[0]), abs(a[1] - b[1]),
                    abs(a[2] - b[2])) <= tol)


gt_table = []
for r in det_rows:
    g = gt_by_id[int(r["id"])]
    lc = r.get("line_colors")
    ic = r.get("ink_color")
    entry = {
        "id": int(r["id"]), "tag": g["tag"], "class": g["class"],
        "box": {"x": r["x"], "y": r["y"], "width": r["width"],
                "height": r["height"]},
        "angle": float(r["angle"]),
        "b2_gt_lines": r.get("b2_gt_lines"),
        "gt_line_colors": g["gt_line_colors"],
        "actual_line_colors": lc,
        "actual_ink_color": ic,
    }
    ok = True
    notes = []
    if g["expect_line_colors"]:
        ok = ok and lc is not None and len(lc) == len(g["gt_line_colors"])
        if ok:
            for i, (want, got) in enumerate(
                    zip(g["gt_line_colors"], lc)):
                if want is None:
                    if got is not None:
                        ok = False
                        notes.append(f"line{i}: expected null, got {got}")
                elif not _close(want, got):
                    ok = False
                    notes.append(f"line{i}: want {want} got {got}")
        else:
            notes.append(f"len mismatch: {lc}")
    else:
        if lc is not None:
            ok = False
            notes.append(f"unexpected line_colors {lc}")
    if g.get("expect_ink_color") is not None:
        if not _close(g["expect_ink_color"], ic):
            ok = False
            notes.append(f"ink_color want {g['expect_ink_color']} "
                         f"got {ic}")
    elif ic is not None:
        ok = False
        notes.append(f"unexpected ink_color {ic}")
    if g.get("expect_gt_lines") is not None:
        if int(r.get("b2_gt_lines") or 0) != g["expect_gt_lines"]:
            ok = False
            notes.append(f"b2_gt_lines want {g['expect_gt_lines']} "
                         f"got {r.get('b2_gt_lines')}")
    if g.get("expect_tilted") and abs(float(r["angle"])) <= 1.0:
        ok = False
        notes.append(f"expected tilted, got {r['angle']}")
    if g.get("expect_vertical") and abs(float(r["angle"])) != 0.0:
        ok = False
        notes.append(f"vertical expected angle 0, got {r['angle']}")
    entry["pass"] = bool(ok)
    entry["notes"] = notes
    gt_table.append(entry)
    print(f"  GT {g['tag']:14s} class={g['class']:12s} "
          f"lc={str(lc)[:44]:44s} ic={ic} gt_lines="
          f"{r.get('b2_gt_lines')} pass={ok} {notes}")

n_pass = sum(1 for e in gt_table if e["pass"])
assert n_pass == len(gt_table), \
    f"S012 GT: {n_pass}/{len(gt_table)} regions pass"

with open(DEST / "b31_parity.json", "w", encoding="utf-8") as f:
    json.dump({
        "fixture": "S012_manhwa_emphasis",
        "notebook_sha256": nb_sha256,
        "regions": gt_table,
    }, f, ensure_ascii=False, indent=1)
print(f"  archived b31_parity.json ({n_pass}/{len(gt_table)} pass)")

# gate-warn census for R3 (line-level RB3-5)
evs = ns["MANGABD_EVENTS"]
gate_warns = [e for e in evs if e.get("level") == "WARN"
              and "line-color gate skip" in str(e.get("message", ""))]
print(f"  line-level gate WARNs in chain log: {len(gate_warns)}")
assert len(gate_warns) >= 1, "R3 two-hue line gate WARN missing"

metadata = {
    "sample_id": "S012_manhwa_emphasis",
    "captured_at": str(date.today()),
    "branch": "mangabd-009-b3",
    "notebook_sha256": nb_sha256,
    "pipeline_variant": (
        "MANGABD-009 B3.1 regression fixture — synthesized "
        "owner-REJECT page class (per-word emphasis coloring), full "
        "chain (detect -> ocr -> inpaint -> translate -> render) on "
        "the B3.1 Phase C bytes"),
    "translation_engine": "synthetic (B3.1 fixture)",
    "source_page": (
        "synthesized by scripts/m009_b31_s012_page.py "
        "(rng_seed 20261109; construction fully deterministic) — NOT "
        "an Owner Colab upload"),
    "provenance": (
        "B3.1 ruling (RB31-1..RB31-8 on Phase A 13a6e02 + the "
        "phase-C addendum: V5 CONFIRMED via the Owner's "
        "detections.json, id=8 w=51 h=62 area=3162): pin the "
        "emphasis-corpus class that made B3 region-median sampling "
        "inert (live-REJECT 0/5 keys) + the narrow-bubble V5 class + "
        "the tiny-text id=8 class. Ground truth = the builder's own "
        "per-line color ledger (gt_line_colors) + the true-ink mask "
        "(text_mask.png); the pipeline's per-line law (raw-threshold "
        "locator, chromatic-cluster median tau=0.15) must reproduce "
        "the ledger, and the render must put each mapped line's "
        "color on that line."),
    "disclosures": [
        "SYNTHESIZED fixture (not Owner-produced art); its job is to "
        "pin the emphasis-coloring + narrow-bubble + tiny-text "
        "classes, not to imitate art.",
        "Sandbox has no onnxruntime/torch GPU: RT-DETR is stubbed to "
        "the TRUE region boxes and CTD to the TRUE text-ink prob map "
        "(the S009/S010/S011 pattern); the region build, B2 "
        "orientation ladder (incl. the B3.1 narrow fix at w<80), the "
        "per-line color law, reading-order sort and every render "
        "byte after the boxes are the REAL production path.",
        "OCR is stubbed to the drawn JP text; translations are the "
        "builder's Bengali strings; inpainted.png is the synthesized "
        "clean page.",
        "text_mask.png is the TRUE synthesized text ink, not the "
        "pipeline detect-stage mask.",
        "R6's b2_gt_lines=3 arrives via the B3.1 narrow fix (raw "
        "locator at w<80): on the B3-tip bytes the closed mask "
        "merges its 8px-gap variant (Test 24 mechanism arm) — the "
        "fixture pins the FIXED behavior.",
        "The Owner's live colored page remains the final re-accept "
        "gate for the B3/B3.1 merge.",
    ],
    "acceptance_rule": (
        "per-region: line_colors == the builder's per-line GT ledger "
        "(L2 <= 10 per colored line, null elsewhere; conditional-key "
        "law — keyless regions stay keyless), ink_color only where "
        "the B3 region law legitimately fires (R2), b2_gt_lines=3 on "
        "R6 (narrow fix), angle 0 on the axis-aligned/vertical "
        "classes, line-level gate WARN on R3; render: mapped colored "
        "lines carry their color (base-vs-work delta asserted by "
        "scripts/m009_b31_phaseC_verify.py)."),
    "ground_truth": gt_table,
}
with open(DEST / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=1)
print(f"  archived metadata.json ({n_pass}/{len(gt_table)} regions "
      f"pass, {len(gate_warns)} line-gate WARNs)")

print(f"\nS012 archive -> {DEST}")
for p in sorted(DEST.iterdir()):
    print(f"  {p.name:18s} {p.stat().st_size:>9,d} B")
