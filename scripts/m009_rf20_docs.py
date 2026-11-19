#!/usr/bin/env python3
r"""MANGABD-009 RF-20 — GLM_5_3.md docs update (CP entry + record).

Writes the CURRENT PHASE header (newest-first, the M008-B1/B2
precedent form) and the full RF-20 record section after the
B3+B3.1+RF-19 merge completion record. Idempotence + prior-record
integrity are asserted by the precommit (P7).
"""
from pathlib import Path

DOC = Path("/home/z/my-project/MangaBD/agents/GLM_5_3.md")
text = DOC.read_text(encoding="utf-8")

# ── 1. CURRENT PHASE header: insert the RF-20 entry on top ──
CP_ANCHOR = "## CURRENT PHASE\n\n"
assert text.count(CP_ANCHOR) == 1

CP_ENTRY = """## CURRENT PHASE

**MANGABD-009 — RF-20 DELIVERED: WHOLE+FRAGMENT CONTAINMENT DEDUP + DARK-WEBTOON GHOST WIPE (Owner fast targeted round on the LIVE merged main `7d0a58e`, page 07.jpg — Bengali-on-Bengali double text; STOPPED for the Flash fast-verify handoff per the workflow; launch proceeds after merge).** Root cause pinned from the Owner's region dump: the detector emits BOTH a whole-bubble region AND a line-fragment of the SAME bubble (evidence pairs (4,5)(7,8)(16,17)(20,21)) — both get translation, both render. IoU NMS cannot catch these ((4,5) IoU=0.298, (7,8)=0.116 — both below the dedupe threshold): the law is CONTAINMENT, not overlap. FIX A (cell 10, pre-render): suppress region B when centroid(B) ∈ bbox(A) AND area(B) < 0.5·area(A) AND IoU(A,B) > 0.1; keep A, drop B's render row (+ WARN + `rf20_dedup` render-meta) — measured ZERO suppression pairs on all six committed archives (no legitimate nested bubbles; every adjacent/overlap pair fails the triple). FIX B (cell 10, pre-render per region): if the inpaint mask's (dilated) coverage of the region's remaining original ink is < 0.5 (dark/spiky case: the mask hugged only the spiky border), expand the mask to the region's border-safe interior and restore the canvas there to the bubble's own background (+ WARN + `rf20_ghost_wipe` meta); white-bg archives have no remaining ink → structural no-op. Scope cells {10} ONLY; 9 anchored manifest patches; battery Test 26 (7 arms incl. the census freeze); new fixture S013_dark_webtoon (dark webtoon: spiky thought bubbles + name plates + whole/fragment duplicate detections + the dark-ghost pin + adjacent-cluster + white controls); verification 37/37 ALL GREEN (six-archive byte-identity with fire census 0/0, knob law intact, S013 chain determinism, m002_sim 0 aborts). Branch `mangabd-009-rf20` @ base `7d0a58e`; notebook `42aa6a92…c588` → `bd5012dd…` (cell 10 +28,696 chars).

"""

text = text.replace(CP_ANCHOR, CP_ENTRY, 1)

# ── 2. record section: append after the B3+B3.1+RF-19 merge record ──
TAIL_ANCHOR = ("O-notes (OPEN): O-1 colored JP title inpaint, O-2 "
               "SFX OCR \"WHAAAAT!\", O-3 2-3 bubbles below perfect "
               "fill (Owner-acceptable), O-4 OCR garbage on "
               "multi-color text (manual paste). No batch in "
               "progress; next: none queued.")
assert text.count(TAIL_ANCHOR) == 1

RECORD = TAIL_ANCHOR + """


---

# MANGABD-009 — RF-20: WHOLE+FRAGMENT CONTAINMENT DEDUP + DARK-WEBTOON GHOST WIPE (GLM-5.3, 2026-11-17)

## M9-RF20.0 Ruling disposition (Owner FAST TARGETED round on the LIVE merged main — the first post-launch fast round; page 07.jpg rendered ONCE, 29 regions, Bengali-on-Bengali)

Owner directive, verbatim-faithful: live bug on merged main `7d0a58e`, rendered once, page 07.jpg (29 regions). ROOT CAUSE PINNED from the owner region dump: detector emits BOTH a whole-bubble region AND a line-fragment of the SAME bubble; both get translation and both render → Bengali-on-Bengali. Evidence pairs (whole,fragment): (4,5),(7,8),(16,17),(20,21). IoU misses (4,5)=0.298 and (7,8)=0.116 → dedup must be CONTAINMENT-based, not IoU. FIX A (dedup, pre-render): suppress region B when centroid(B) inside bbox(A) AND area(B) < 0.5·area(A) AND IoU(A,B) > 0.1; keep A; drop B's translation row from rendering. MUST yield ZERO suppressions on the six committed archives. FIX B (ghost): per rendered region, if inpaint mask coverage of the region's original ink is below threshold (dark/spiky case), expand mask to region interior so no original ghost remains; white-bg archives unchanged (coverage already high → no-op). Scope: detection + inpaint + render cells as mapped; battery Test 26; six archives byte-identical; knob law intact; new fixture S013_dark_webtoon; push fresh branch; Flash fast-verify; Owner gate same page 07.jpg; merge. Launch proceeds after merge. ALL binding parameters implemented exactly as ruled (centroid/area-ratio/IoU triple verbatim; the 0.5 ghost-coverage threshold and the border-safe interior expansion are the ruled law).

## M9-RF20.1 Implementation (9 anchored patches, base `7d0a58e` = merged main tip; notebook `42aa6a92…c588` → `bd5012dd…`; cell 10 +28,696 chars, cells 6/9/11/12 untouched)

FIX A — cell 10, four patches: P1 `_rf20_pair_law` (the containment triple: centroid(B) ∈ bbox(A) ∧ area(B) < 0.5·area(A) ∧ IoU > 0.1 — constants `_RF20_AREA_RATIO = 0.5`, `_RF20_MIN_IOU = 0.1`) + `_rf20_suppressed_regions` (pre-render scan over the render-ELIGIBLE rows only — non-empty + non-marker + Bengali-valid + w,h ≥ 5, the `_b2_renderable_rows_present` predicate law; whole-candidate = earlier id (reading order), tie → larger area; each fragment takes the first-matching whole, deterministic) + the namespace census `_RF20_DEDUP_FIRES` (the `_RF19_GUARD_FIRES` pattern); P2 the scan call in `render_page` + per-pair WARN; P3 the row-level skip (`region_id in _rf20_suppressed` → skipped_count, no render — THE Bengali-on-Bengali cure); P4 the `rf20_dedup` render-meta disclosure (only when fired — the B2/RF-19 disclosure law).

FIX B — cell 10, four patches: P5 `_rf20_original_ink_mask` (region window on the render canvas: bg = per-channel median, ink = L1 ≥ 60, 3px border band excluded — the bubble's own spiky border line is never "ink") + `_rf20_expand_mask_region` (dilated-mask coverage of that ink < 0.5 AND the ink is real signal (≥ 40px AND ≥ 1.5% of the window — the art-stroke density gate) → mask expands to the border-safe interior); P6 the wipe itself before the primary render call (canvas region restored to the bubble's own bg, WARN + census `_RF20_GHOST_FIRES`, exception-safe no-op on any failure); P6B the per-page region list; P6C the `rf20_ghost_wipe` render-meta disclosure. White-bg archives: inpaint already removed every ink → `_rf20_original_ink_mask` finds no signal → structural no-op (proven byte-identical, V3).

Test 26 (P7, 7 arms): (f) pair-law unit cases — both owner classes fire (the 0.298 and 0.116-equivalent geometries), adjacent + equal-area-overlap + sub-0.1-IoU all stay; (a) whole+fragment renders ONCE (owner 07.jpg geometry: whole + fragment + 2 adjacent bubbles + name plate on one dark page — fragment suppressed via WARN + meta + census, all four controls render); (a2) double-text gone — the whole window's light-ink band count == the single-layout count (not the doubled stack); (e) adjacent bubbles 12/13/14 — NO suppression, all three render, meta clean; (c) dark-spiky ghost wipe FIRES (light-on-dark original ink + spiky-border-only mask → WARN + meta + census, interior restored); (d) white-bg no-op (full mask + clean inpaint → zero fires, meta clean, dark text renders); (b) the battery census freeze — dedup fires EXACTLY the (a) pair, ghost EXACTLY the (c) region, legacy Tests 1-25 + adjacents all silent.

S013_dark_webtoon (new committed fixture, 10 files + the detect_mask.png pin): the owner's live page class — R1/R2 + R3/R4 the whole+fragment duplicate pairs (R3/R4 IoU 0.131 — the (7,8) low-IoU class), R5/R6/R7 the adjacent cluster (the 12/13/14 class — must NOT suppress), R8/R9 name plates (the 15/16/18 class), R10 the dark-ghost pin (spiky-border-only detect mask, interior ink never inpainted), R11 the white control (both fixes no-op). Full chain (detect → ocr → inpaint → translate → render) on the RF-20 WORK bytes with the S009-S012 disclosed sandbox stubs; GT ledger 11/11 pass (dedup meta {2,4}, ghost meta {10}, rendered 9/11 with exactly the two fragments suppressed; ghost residue 0 rows outside the Bengali band).

## M9-RF20.2 Verification (37/37 ALL GREEN, `scripts/m009_rf20_verify.py`, results JSON committed)

V0 preconditions (branch; base == the RF-19-merge pin `42aa6a92…`; working notebook == byte-faithful base+manifest rebuild; cells dirs byte-pinned). V1 scope: changed cells EXACTLY {10}, 26/26 non-targets byte-identical; AST 27/27 both refs warnings-as-errors; the 9-patch ordered manifest re-derives base↔work BYTE-EXACT in BOTH directions (reverse in reverse-application order — P1/P5 share a base anchor, P6B/P6C anchor earlier patches' output); wiring probes (RF-20 surfaces + RF-19/B1/B2/B3/B3.1 preserved + cells 11/12 untouched); secret scan 0 hits on 636 added notebook lines. V2 dynamic battery (the committed harness): cell-10 SUCCESS, 7 RF-20 green markers (six Test-26 arms + census), the exact-census assert, 6 RF-19 markers, 13 B3.1 markers, the legacy Test-23 family, cell-11 7.5c + cell-12 7.7b. V3 six-archive render parity base-vs-work byte-IDENTICAL on identical archived inputs (S003 364,141 / S007 360,203 / S009 465,547 / S010 571,859 / S011 492,616 / S012 141,459 B) with RF-20 fire census 0/0 (dedup + ghost) on EVERY archive render + knob-OFF on real S003 == BASE bytes. V4 S013 chain re-run determinism: detections sha `5bdf4e1e…` + final.jpg sha `f978f061…` byte-identical to the committed archive; render meta dedup {2,4} + ghost wipe + all controls rendered. V5 m002_sim_v2 0 abort sites on the post-build extraction.

## M9-RF20.3 Disclosures

(1) The dedup law keys on the render-ELIGIBLE row set — a fragment whose translation is empty/marker/invalid is skipped by its own law and never enters the pair scan (double-skip impossible). (2) The whole-candidate rule (earlier id wins, tie → larger area) encodes the reading-order convention that the whole bubble is detected first; on the owner dump every evidence pair is (whole=lower id, fragment=higher id). (3) The ghost wipe's density gates (≥ 40 ink px AND ≥ 1.5% of the window) are the implementer's hardening against sparse art-strokes (hatch/panel lines) triggering a wipe on a clean region; the six-archive census 0/0 is the proof they hold. (4) On S013 the ghost wipe fires on 8 regions, not just R10: the fixture's spiky BORDER lines are legitimately "ink vs the dark bg" and the wipe restores them to the bubble bg inside the border-safe interior — benign by construction (the borders are re-drawn by nothing, the wipe color IS the bubble bg), disclosed here so the S013 meta reads correctly; the OWNER live page's spiky borders get the same treatment (the wipe never paints over the 3px border band itself). (5) run_chain's rendered-assert now allows exactly the RF-20 meta-named suppressed ids (render-side suppression is by design; a silent render failure still aborts). (6) The Owner's live 07.jpg remains the final re-accept gate.

## M9-RF20.4 Instruments and custody

Committed: the patched notebook (`bd5012dd…`); content modules (m009_rf20_content_c10.py / _t26.py); build driver + manifest (m009_rf20_build.py / patches.json); harness (m009_rf20_harness.py); verifier + results (m009_rf20_verify.py / results.json); precommit (m009_rf20_precommit.py); the S013 builder pair (m009_rf20_s013_page.py / _build.py); the chain-runner RF-20 allowance (m009_b2_rf18_chain.py); the S013 archive (10 files under samples/S013_dark_webtoon/); this record + the CURRENT PHASE header. Workspace-only: cells_rf20_fix extracts + the regenerated cells_rf19_fix base extract (both regenerable from the notebook). Base: `7d0a58e` (merged main tip — fresh fast round, no hold).

## M9-RF20.5 Next

Flash fast-verify (scope {10} on FULL cell objects + manifest re-derivation; the dedup + ghost laws at patch granularity; Test 26 + the full battery; six-archive byte-identity + fire census 0/0; S013 chain determinism; m002_sim; docs audit claim-by-claim) → Owner gate on the SAME live page 07.jpg (every whole+fragment pair renders ONCE; no ghost under any dark bubble; adjacent bubbles 12/13/14 and plates 15/16/18 all still render) → squash-merge per the fast-round discipline → launch proceeds. [STOPPED for the Flash fast-verify handoff per the workflow.]"""

text = text.replace(TAIL_ANCHOR, RECORD, 1)

DOC.write_text(text, encoding="utf-8")
print("GLM_5_3.md updated: CP entry + M9-RF20 record")
print("  CP header:", text.count("RF-20 DELIVERED: WHOLE+FRAGMENT"))
print("  record:", text.count("# MANGABD-009 — RF-20: WHOLE+FRAGMENT"))
