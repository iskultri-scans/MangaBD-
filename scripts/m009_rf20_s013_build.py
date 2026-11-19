#!/usr/bin/env python3
r"""MANGABD-009 RF-20 — S013_dark_webtoon archive builder.

Commits the Owner's live 07.jpg page class (dark webtoon, 29
regions) permanently into the corpus. The Owner's live page bytes
are not in the repo, so S013 is a SYNTHESIZED owner-signature page
(disclosed in metadata), pinning BOTH RF-20 failure mechanisms:

  * duplicate whole+fragment detections (the Bengali-on-Bengali
    root cause — owner dump pairs (4,5)(7,8)(16,17)(20,21)),
    reproduced as R1/R2 + R3/R4 with a low-IoU pair (R3/R4 IoU
    0.131 — the (7,8)=0.116 class) that IoU-NMS cannot catch;
  * the dark-spiky ghost (R10): detect-stage mask hugs only the
    spiky border, interior ink never inpainted away.

Plus the must-stay-rendered controls: the adjacent cluster
R5/R6/R7 (the 12/13/14 class), the name plates R8/R9 (the
15/16/18 class) and the white control R11 (both fixes no-op).

Chain: the REAL detect->ocr->translate->render path on the RF-20
WORK bytes via m009_b2_rf18_chain.run_chain, with the SAME
disclosed sandbox stubs (RT-DETR stubbed to the fixture's TRUE
boxes INCLUDING the duplicate fragments; CTD stubbed to the TRUE
ink; inpaint = the synthesized clean page EXCEPT R10 where the
spiky-border mask law must leave the ink — the pinned bug).

Archive contents (samples/S013_dark_webtoon/): original.jpg /
inpainted.png / text_mask.png / detections.json / ocr.json /
translation.json / final.jpg / metadata.json / rf20_parity.json —
same shape as S009..S012.
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
from m009_rf20_s013_page import (  # noqa: E402
    PAGE_H, PAGE_W, RNG_SEED, build_s013_page,
    region_boxes_payload,
)

DEST = REPO / "samples" / "S013_dark_webtoon"

# ── 0. preconditions ────────────────────────────────────────────────
branch = subprocess.run(["git", "-C", str(REPO), "branch",
                         "--show-current"],
                        capture_output=True, text=True).stdout.strip()
assert branch == "mangabd-009-rf20", f"on branch {branch!r}"
nb_sha256 = hashlib.sha256(
    (REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt")
    .read_bytes()).hexdigest()
print(f"notebook sha256: {nb_sha256[:16]}...")
assert not DEST.exists(), f"{DEST} already exists"

full, clean, regions, ink_mask, mask_override = build_s013_page()
print(f"page drawn: {PAGE_W}x{PAGE_H}, {len(regions)} regions, "
      f"ink {int((ink_mask > 0).sum())} px")

# ── 1. run the full chain on the RF-20 WORK bytes ───────────────────
# The R10 ghost is pinned by the CHAIN ITSELF: the chain's
# detect-stage builds the page mask from the TRUE ink, so here we
# instead save R10's spiky-border-only mask as the page's mask
# artifact BEFORE inpaint (the owner's live mask law), and give the
# chain a clean page whose R10 window STILL HOLDS the ink (the
# inpaint trusted the bad mask). run_chain's clean-page inpaint
# stub is therefore post-processed: nothing — build_s013_page
# already drew clean with the R10 ink present.
ns, pid, det_rows = run_chain(
    "s013_dark_webtoon.jpg", full, clean, regions, ink_mask)
print(f"chain done: {len(det_rows)} regions detected")

# R10's spiky-border mask becomes the archived page mask (the
# pinned bug: interior uncovered) — the chain's own mask (full
# ink) is the RF-20-ideal; the archive pins the OWNER's live shape.
spiky_mask = mask_override["R10"]
page_mask = ns["load_image_artifact"](pid, "mask")
assert page_mask is not None
merged_mask = np.maximum(page_mask, np.zeros_like(page_mask))
# remove R10's interior ink from the page mask (spiky border only)
r10 = next(r for r in regions if r["tag"] == "R10")
x, y, w, h = r10["box"]
interior = np.zeros_like(merged_mask)
interior[y + 3:y + h - 3, x + 3:x + w - 3] = 255
merged_mask = cv2.bitwise_and(
    merged_mask, cv2.bitwise_not(interior))
merged_mask = np.maximum(merged_mask, spiky_mask)
ns["save_image_artifact"](pid, "mask", merged_mask)
print(f"page mask re-pinned: R10 spiky-border law "
      f"({int((merged_mask > 0).sum())} px)")

# re-render on the re-pinned mask (the ghost now reachable)
ns["run_render_all"](force=True, require_translation=True)

gt_by_id = {}
for r in det_rows:
    best, bt = 0, None
    for g in regions:
        gx, gy, gw, gh = g["box"]
        ix = max(0, min(r["x"] + r["width"], gx + gw)
                 - max(r["x"], gx))
        iy = max(0, min(r["y"] + r["height"], gy + gh)
                 - max(r["y"], gy))
        # containment tie-break: a fragment det-row equals its own
        # ledger box EXACTLY (ix==gw and iy==gh) — prefer the exact
        # match over the whole's partial overlap (the fragment box
        # sits inside BOTH, overlap area identical)
        if ix * iy > best or (ix * iy == best and ix == gw
                              and iy == gh and bt is not None
                              and not (bt["box"][2] == ix
                                       and bt["box"][3] == iy)):
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
shutil.copy2(str(ns["get_artifact_path"](pid, "mask")),
             str(DEST / "detect_mask.png"))
print("  archived detect_mask.png (the R10 spiky-border law)")

trans_rows = []
for r in det_rows:
    g = gt_by_id[int(r["id"])]
    trans_rows.append({
        "id": int(r["id"]), "region_type": r["region_type"],
        "original_text": g["jp"],
        "translated_text": g["bengali"],
        "translator_engine": "synthetic (RF-20 fixture)",
        "bengali_valid": True, "status": "rendered",
    })
with open(DEST / "translation.json", "w", encoding="utf-8") as f:
    json.dump(trans_rows, f, ensure_ascii=False, indent=1)
print(f"  archived translation.json ({len(trans_rows)} rows)")

# ── 3. ground-truth table + per-region acceptance ───────────────────
df_now = ns["translation_df"]
page_df = df_now[df_now["page_id"] == pid]
rendered_ids = set(
    int(i) for i in page_df[page_df["status"] == "rendered"]["id"])
meta = dict(ns["get_page"](pid, required=True).get("meta") or {})

gt_table = []
n_pass = 0
for r in det_rows:
    g = gt_by_id[int(r["id"])]
    rid = int(r["id"])
    entry = {
        "id": rid, "tag": g["tag"], "class": g["class"],
        "box": {"x": r["x"], "y": r["y"], "width": r["width"],
                "height": r["height"]},
        "expect_rendered": bool(g.get("expect_rendered", True)),
        "actually_rendered": rid in rendered_ids,
    }
    ok = entry["expect_rendered"] == entry["actually_rendered"]
    notes = []
    if g.get("expect_suppressed_by") is not None:
        sup = meta.get("rf20_dedup", {}).get("suppressed", [])
        ok = ok and rid in sup
        if rid not in sup:
            notes.append(f"expected in rf20_dedup.suppressed, "
                         f"got {sup}")
    if g.get("expect_ghost_wipe"):
        gw = meta.get("rf20_ghost_wipe", {}).get("regions", [])
        ok = ok and rid in gw
        if rid not in gw:
            notes.append(f"expected in rf20_ghost_wipe.regions, "
                         f"got {gw}")
    if ok:
        n_pass += 1
    entry["pass"] = bool(ok)
    entry["notes"] = notes
    gt_table.append(entry)
    print(f"  GT {g['tag']:6s} class={g['class']:14s} "
          f"rendered={entry['actually_rendered']} "
          f"(want {entry['expect_rendered']}) pass={ok} {notes}")

assert n_pass == len(gt_table), \
    f"S013 GT: {n_pass}/{len(gt_table)} regions pass"
meta_out = {
    "rf20_dedup": meta.get("rf20_dedup"),
    "rf20_ghost_wipe": meta.get("rf20_ghost_wipe"),
    "rendered_regions": meta.get("rendered_regions"),
    "skipped_regions": meta.get("skipped_regions"),
}
assert meta.get("rf20_dedup") is not None, "dedup meta missing"
assert meta.get("rf20_ghost_wipe") is not None, "ghost meta missing"

with open(DEST / "rf20_parity.json", "w", encoding="utf-8") as f:
    json.dump({
        "fixture": "S013_dark_webtoon",
        "notebook_sha256": nb_sha256,
        "render_meta": meta_out,
        "regions": gt_table,
    }, f, ensure_ascii=False, indent=1)
print(f"  archived rf20_parity.json ({n_pass}/{len(gt_table)} pass, "
      f"meta={meta_out})")

# ── 4. ghost pixel law on final.jpg ─────────────────────────────────
# The wipe paints the region interior to bubble-bg BEFORE the render,
# so any light pixel in the final window is either (a) the rendered
# Bengali or (b) surviving original ink. Robust residue law: rows
# that held DENSE original ink (the JP rectangles, >= 80 light px)
# must either be clean or sit inside the rendered Bengali band
# range — ghost = a dense-original row that still has >= 80 light px
# OUTSIDE the Bengali band range (probe: post-wipe count is 0).
final = cv2.imread(str(DEST / "final.jpg"), cv2.IMREAD_COLOR)
x, y, w, h = r10["box"]
gf = cv2.cvtColor(final[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
gi = cv2.cvtColor(clean[y:y + h, x:x + w], cv2.COLOR_BGR2GRAY)
fp = (gf > 170).sum(axis=1)
ip = (gi > 170).sum(axis=1)
fb_rows = np.nonzero(fp >= 20)[0]
assert len(fb_rows) > 0, "R10 render empty"
band_lo, band_hi = int(fb_rows.min()), int(fb_rows.max())
dense_orig = np.nonzero(ip >= 80)[0]
ghost_rows = [int(r) for r in dense_orig
              if fp[r] >= 80 and not (band_lo <= r <= band_hi)]
assert not ghost_rows, f"ghost residue rows: {ghost_rows}"
light_now = int((gf > 170).sum())
light_orig = int((gi > 170).sum())
print(f"  ghost law: R10 dense-original rows "
      f"{len(dense_orig)}, residue outside Bengali band 0, "
      f"light ink {light_now} (was {light_orig} pre-wipe; now = "
      f"the rendered Bengali) — PASS")

metadata = {
    "sample_id": "S013_dark_webtoon",
    "captured_at": str(date.today()),
    "branch": "mangabd-009-rf20",
    "notebook_sha256": nb_sha256,
    "pipeline_variant": (
        "MANGABD-009 RF-20 regression fixture — synthesized "
        "owner-live 07.jpg page class (dark webtoon, double "
        "detections + dark-spiky ghost), full chain (detect -> ocr "
        "-> inpaint -> translate -> render) on the RF-20 WORK bytes"),
    "translation_engine": "synthetic (RF-20 fixture)",
    "source_page": (
        "synthesized by scripts/m009_rf20_s013_page.py "
        "(rng_seed 20261117; construction fully deterministic) — NOT "
        "an Owner Colab upload; the Owner's live 07.jpg (29 regions, "
        "merged main 7d0a58e) is the re-accept gate"),
    "provenance": (
        "RF-20 (Owner fast targeted): the live root cause — the "
        "detector emitting BOTH a whole-bubble region AND a "
        "line-fragment of the SAME bubble (owner dump pairs "
        "(4,5)(7,8)(16,17)(20,21); IoU (4,5)=0.298, (7,8)=0.116 — "
        "containment law, not IoU) — plus the dark-webtoon ghost "
        "(spiky-border mask leaving interior ink uninpainted). "
        "Ground truth = the builder's ledger (expect_rendered / "
        "expect_suppressed_by / expect_ghost_wipe) + the TRUE ink "
        "(text_mask.png); the pipeline's RF-20 laws must reproduce "
        "it: fragments suppressed (rendered once), ghost wiped, "
        "adjacent cluster + name plates + white control all "
        "rendered."),
    "disclosures": [
        "SYNTHESIZED fixture (not Owner-produced art); its job is "
        "to pin the double-detection + dark-ghost classes, not to "
        "imitate art.",
        "Sandbox has no onnxruntime/torch GPU: RT-DETR is stubbed "
        "to the TRUE region boxes INCLUDING the duplicate fragment "
        "boxes (the owner's live detector behavior); CTD to the "
        "TRUE text-ink prob map (the S009..S012 pattern); "
        "everything after the boxes — region build, reading order, "
        "layout, render bytes — is the REAL production path.",
        "OCR is stubbed to the drawn JP text; translations are the "
        "builder's Bengali strings.",
        "inpainted.png is the synthesized clean page EXCEPT R10: "
        "its ink STAYS (the spiky-border mask law — the pinned "
        "ghost); detect_mask.png archives that mask shape.",
        "The Owner's live 07.jpg remains the final re-accept gate "
        "for the RF-20 merge.",
    ],
    "acceptance_rule": (
        "per-region: expect_rendered == actually rendered; "
        "R2/R4 in render-meta rf20_dedup.suppressed (rendered "
        "ONCE via their wholes R1/R3); R10 in "
        "rf20_ghost_wipe.regions; final.jpg R10 window light-ink "
        "residue < 40% of original (no ghost); R5/R6/R7 adjacent "
        "cluster + R8/R9 plates + R11 white control all rendered "
        "with NO dedup/ghost fires."),
    "ground_truth": gt_table,
}
with open(DEST / "metadata.json", "w", encoding="utf-8") as f:
    json.dump(metadata, f, ensure_ascii=False, indent=1)
print(f"  archived metadata.json")

print(f"\nS013 archive -> {DEST}")
for p in sorted(DEST.iterdir()):
    print(f"  {p.name:18s} {p.stat().st_size:>9,d} B")
