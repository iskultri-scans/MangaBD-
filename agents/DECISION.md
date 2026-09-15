# MangaBD — Engineering Decision

## STATUS

**WAITING_FOR_USER**

MANGABD-001 COMPLETE (dual-agent audit + comparison; historical record below).
MANGABD-002 PHASE B COMPLETE — second-pass technical review finished; final engineering proposal written (see "MANGABD-002 — PHASE B" section at the end of this file). Root cause dual-confirmed; one GLM-5.3 Phase A claim corrected (Drive-scenario, §B.5); proposal verdicts: GLM-5.3-Flash APPROVE_WITH_CORRECTED_JUSTIFICATION, GLM-5.3 accepts all four corrections after independent code verification + runtime reproduction.

**No source code modified at any point. Implementation (Phase C) is gated on explicit Project Owner approval of the §B.6 patch.**

---

## PURPOSE

This file records technical discussions and decisions between:

- GLM-5.3
- GLM-5.3-Flash
- Project Owner

AI agents may propose technical solutions.
The Project Owner has final authority over major changes.

---

## CURRENT TASK

MANGABD-002 — Fresh-Colab Execution Reliability (investigation complete; proposal awaiting Owner approval)

(Historical: MANGABD-001 — Initial Codebase Audit, Phase 1, complete; record below)

---

## COMPARISON METHOD (how disagreements were resolved)

GLM-5.3 performed the comparison. Per the review protocol, no challenge was accepted or rejected on authority — every disputed claim was re-verified directly against the current repository in a fresh session:

1. Re-ran output forensics on the raw notebook JSON (resolves DIS-1).
2. Read physical cells 11, 12, 13, 14 in full, line-by-line (resolves DIS-2, DIS-3, DIS-4 and new findings F-1/F-5/F-6).
3. Line-pinned every module-level call and gating flag cited by either report (cells 10, 15, 20, 23, 25, 26).
4. Re-executed the pandas `bengali_valid` round-trip simulation locally (verifies T-6).
5. Actively searched for errors in Flash's own report. One candidate was found — 3 occurrences of `image/png|jpeg` in the notebook JSON versus Flash's "zero image outputs" claim — and investigated: all 3 are MIME-type strings inside cell 24's source code (the base64 download patch), not cell outputs. Flash's claim stands.

Result: all five of Flash's challenges are upheld by independent repo evidence. The comparison also produced five new findings (N-1..N-5 below) that appear in neither individual report.

---

# GLM-5.3 FINDINGS

Full report: `agents/GLM_5_3.md`. Summary: single-artifact Colab notebook (27 code cells, two strata: structured V12 core + patch/hotfix layer), full model inventory verified, end-to-end pipeline traced, 12 potential bugs (P-1..P-12), 7 performance bottlenecks, 8 reliability risks, 10 unknowns. Central conclusion: the patch layer created an order-dependent runtime where the effective pipeline depends on which cells were executed last; the notebook cannot bootstrap itself fresh top-to-bottom.

---

# GLM-5.3-FLASH FINDINGS

Full report: `agents/GLM_5_3_FLASH.md`. Summary: independent audit performed BEFORE reading GLM-5.3's report (methodologically correct). ~45 specific claims checked; ~41 confirmed exactly; 4 corrections proposed (D-1..D-4); 6 new findings (F-0..F-6); verdict **APPROVE_WITH_CHANGES** with 8 Phase-2 proposals. Central conclusion independently matches GLM-5.3's: order-dependent fragility, orphaned quality core, in-place artifact mutation, heuristic confidence, no visual evidence.

---

# AGREEMENTS

Both agents independently reached these conclusions; GLM-5.3 re-verified each during this comparison. All are [FACT] unless noted.

**Project shape**
1. The repository is exactly one source artifact — the 800 KB Colab notebook `MangaBD_V12_ipynb_txt.ipynb (3).txt` (27 code cells, 0 markdown) — plus agent docs. No `.py` tree, no requirements pinning, no CI, no external tests.
2. Two strata: structured V12 core (physical 0–10, 15–18) vs. patch/hotfix layer (physical 11–14, 19–26). Attribution of the patch layer to Qwen3.8-Max remains a style-based [HYPOTHESIS] in both reports — git provides no attribution evidence (single upload commit `27d8643`).

**Pipeline and models**
3. End-to-end pipeline trace (upload → detect → OCR → translate → inpaint → render → QA → export) with all stage thresholds verified by both agents at identical line references.
4. Model inventory: RT-DETR-v2 `ogkalu/comic-text-and-bubble-detector` (float32), CTD (zyddnys, beta-0.3), LaMa Large (zyddnys), Qwen2.5-VL-3B fp16-on-CUDA with local HF cache, NLLB-200-distilled-600M (`ben_Beng`, fallback BOS 100362, beams 4), Gemini 2.5 Flash + GPT-4o-mini APIs, OvisOCR2 = placeholder (`NotImplementedError`).
5. OCR "confidence" is a heuristic (base 0.45, cap 0.95 — cell 5:293/314), not token probability.

**Defects (both reports, independently confirmed)**
6. Fresh "Run All" cannot complete: cell 14 line 40 executes `run_inpaint_render_all(force=True)` at module level; the bound definition (cell 13's wrap) calls `run_inpaint_all`, defined only in cell 15 → `NameError`. See N-1 for scenario precision.
7. `run_inpaint_render_all` defined 5× (cells 11, 12, 13, 15, 23); `kill_residual` 3× (11, 13, 14); `render_bengali_text` patched 2× (11, 12); NLLB translator 2× (8, 19); detection wrappers (6, 24).
8. Quality core is orphaned in sequential flow; Control Studio's render button (cell 25:363–365) calls `run_inpaint_all`/`run_render_all` directly, bypassing every wrap.
9. In-place, non-idempotent artifact mutation: `mask_only_translated` AND-shrinks the stored mask (cell 11:96); `kill_residual`/`restore_boxes` overwrite `inpainted.png` (11:117/130, 13:31).
10. `_has_valid_trans` rejects any text starting with `[` (cell 11:84–86).
11. Dead OCR config: `temperature`/`top_p` never passed to `generate()` (cell 5:404–408).
12. Cell 24's "proof" block runs whole-vs-sliced detection at cell-run time, requiring an existing `02.jpg` (cell 24:133–147).
13. Cell 12 dead code `size, lines = 8, [text]` (12:116→120); vertical renderers hardcode `(0,0,0)` (11:183, 12:148).
14. Double detection per page: CTD runs even when RT-DETR succeeds (default `use_ctd_pixel_mask=True`, cell 6:1095–1120).
15. Performance set: per-region `generate()` with no batching, `clear_gpu_cache()` per OCR call, model ping-pong across stages, manifest/CSV rewrite frequency, slicer multiplication on tall strips, `iterrows()` costs.
16. `reset_checkpoint` (cell 25:230–245) clears memory state only; per-page artifacts leak on disk.

**Process facts**
17. No secrets embedded (both agents ran independent scans; sanitizer strips key names containing `api_key|token|secret|password` before config save).
18. Zero image outputs in the notebook and zero image files in the repo — **NO_VISUAL_EVIDENCE_AVAILABLE**; output quality is unassessable by anyone until sample artifacts are committed.
19. Stored outputs prove a real run on 2026-08-31 12:18 (Python 3.13.15, T4, 14.56 GB, base dir `/content/mangabd`, Drive unmounted, `hf_token` not set).

---

# DISAGREEMENTS

Each disagreement below follows the required protocol: claim identified → checked against the actual repository → better-supported conclusion determined → reasoning stated. **Outcome: all five resolved in favor of GLM-5.3-Flash, on evidence.** None of the resolutions overturns the audit's central conclusions.

## DIS-1 — Coverage of the stored outputs

- **Claim (GLM-5.3 §7.3):** "stored outputs prove cells 1–7 passed on the reference machine."
- **Repository check:** [TEST RESULT] Output forensics re-run on the raw notebook JSON. Outputs exist ONLY in physical cells 0, 1, 2, 3, 5, 6 (banner Cells 1, 2, 2.1, 3, 5, 6). Physical cell 4 (banner "Cell 4: External Assets, Fonts & zyddnys Patch") has no stored output. All outputs are `stream` type; no error outputs exist anywhere.
- **Better-supported conclusion:** GLM-5.3-Flash. The claim is an over-claim. GLM-5.3's own §2 wording ("partial, cells 0–6 only") is also imprecise because cell 4 lies inside that range yet has no output.
- **Reasoning:** Absence of output is not proof of failure, but it is proof of absence of evidence. The evidence discipline this project committed to (never present assumptions as facts) requires narrowing the claim. Practical consequence: cell 4 — the zyddnys clone/patch, fonts, and libraqm render test — has UNPROVEN status in the owner's last saved session. Additionally, `execution_count` is None on every cell including those with outputs, meaning the JSON was post-processed (counts cleared, outputs kept); the stored outputs are environment forensics, not a clean execution log.
- **Resolution:** Adopt the narrower claim. Banner Cells 1, 2, 2.1, 3, 5, 6 proven; cell 4 and beyond UNKNOWN for that session.

## DIS-2 — "In the owner's warm-kernel workflow the wrap wins"

- **Claim (GLM-5.3 P-2, second half):** the QUALITY CORE wrap wins in the owner's warm-kernel workflow.
- **Repository check:** No repository artifact documents the owner's execution order. The only runtime evidence (stored outputs, DIS-1) covers physical cells 0–6 and stops there. GLM-5.3's own §13 lists the canonical workflow as UNKNOWN #2 and the quality core's desired status as UNKNOWN #3 — an internal tension with P-2's phrasing.
- **Better-supported conclusion:** GLM-5.3-Flash. The statement must be downgraded from implied fact to [HYPOTHESIS].
- **Reasoning:** Cell 23 is physically last among the five definitions; an owner who executes cells in physical order in a warm kernel ends with cell 23's plain version, exactly as in a fresh run. The wrap wins only if the owner re-executes cells 11–13 after 23 — plausible (the quality cells were authored as interactive hotfixes) but undocumented. What IS fact: the effective pipeline differs by re-execution order, and the UI button bypasses all wraps unconditionally.
- **Resolution:** P-2's first half (sequential final = cell 23 plain; quality core orphaned) stands as verified. The second half is reclassified [HYPOTHESIS] pending owner input. See N-1 for a sharper three-scenario model that supersedes both phrasings.

## DIS-3 — Severity and blast radius of the box-snap / restore_boxes misfire (P-5 / F-1)

- **Claim (GLM-5.3 P-5, Medium):** misfire risk described using cell 11's guarded implementation (5 probe points, border exclusion, area cap).
- **Repository check:** [FACT] Cell 12 redefines `apply_container_types` (line 44), `restore_boxes` (line 71), and `_snap_white_box` (lines 30–42). In sequential execution cell 12's definitions WIN. Cell 12's `_snap_white_box` probes ONLY the center point (line 34), has NO border exclusion (cell 11 line 56 had `bx<=2 / by<=2 / bx+bw>=W-2 / by+bh>=H-2` rejections), and NO 4× area cap (cell 11 line 57). Any white connected component with fill > 0.85 and dims ≥ 30 px qualifies — including page-scale components such as margins or full white panels. `restore_boxes` (cell 12:71–86) then paints a synthetic white rectangle with a 2 px black border over everything classified `narrator`.
- **Better-supported conclusion:** GLM-5.3-Flash. P-5 was understated; the audit's description matched the LOSING variant.
- **Reasoning:** GLM-5.3's P-5 text says "a thought bubble or white SFX panel with ≥85% fill can be mis-typed" — but with the border exclusion and area cap gone, the realistic misfire set includes any detection box whose center lands in a large white region (page margin, panel background, screentone-free area). The destructive `restore_boxes` overwrite then scales with the snapped component size, not the original region size. This is the highest art-preservation risk in the codebase and its severity should be High, not Medium.
- **Resolution:** P-5 upgraded to High; effective variant is cell 12's; Flash's F-1 incorporated.

## DIS-4 — Scope of `recover_coordinates()` (P-3 / F-6)

- **Claim (GLM-5.3 P-3):** cell-run-time `recover_coordinates()` reverts snapped coordinates back to detection coords.
- **Repository check:** [FACT] Cell 11 line 40 also resets `region_type` from `detections.json` (`translation_df.at[idx, "region_type"] = d.get("region_type", "bubble")`) — undoing the narrator reclassification that box-snap performs. It would likewise clobber any manual coordinate/region-type corrections made through the QA/dashboard workflow. The module-level call site is line 203: `print(f"✅ Recovered {recover_coordinates()} region coords")` — an argument inside a print() f-string, which is genuinely easy for a static top-level-call scan to miss (both agents' initial scans did). Also verified: `apply_container_types` is NOT called at module level in cells 11/12 — it only runs inside the wraps — so on a first fresh pass nothing has been snapped yet and the revert only bites when cell 11 is re-executed after a snap.
- **Better-supported conclusion:** GLM-5.3-Flash (extension). P-3's mechanism was correct; its scope was narrower than reality.
- **Reasoning:** The function restores FOUR coordinate fields plus region_type from a source (`detections.json`) that predates every later improvement, on every page, as a print side effect. The blast radius is "any post-detection correction", not just box-snap.
- **Resolution:** P-3 stands with F-6's scope added: coordinates + region_type + manual edits, call site print-f-string.

## DIS-5 — "Three ai.Text parsers" wording

- **Claim (GLM-5.3 §8.8):** "three ai.Text parsers (cell 8, cell 22 local, cell 25 builder)."
- **Repository check:** [FACT] Cell 25 line 153 defines `build_ai_text_content()` — it CONSTRUCTS the export text; it does not parse. Cell 8 (`parse_ai_text`) and cell 22 (`_parse_ai_text_local`, line 42) are the parsers.
- **Better-supported conclusion:** GLM-5.3-Flash. The duplication is real (three independent implementations of the ai.Text format, which is the actual risk — format drift between writer and readers), but "3 parsers" is imprecise.
- **Reasoning:** Precision matters here because the failure mode is writer/reader drift: if the builder's format diverges from either parser, translations silently fail to re-import. The correct count is 2 parsers + 1 builder sharing one undocumented format.
- **Resolution:** Reworded in this record; GLM_5_3.md addendum notes the correction.

---

# NEW FINDINGS FROM THE COMPARISON ITSELF

These five findings exist in NEITHER individual report; they emerged from cross-checking the two audits against the code. They are the concrete output of the two-agent collaboration this project is testing.

## N-1 — The entrypoint hazard has three distinct execution scenarios [TEST RESULT, static]

Both reports state (a) a fresh Run All crashes at cell 14 (P-1/F-0) and (b) the sequential final definition of `run_inpaint_render_all` is cell 23's plain version (P-2). Both statements are individually true but **cannot occur in the same run** — a latent tension neither report flagged. Verified mechanism: cell 13's wrap calls `run_inpaint_all(force=force, require_translation=False)` at line 39 **unconditionally** — before any page iteration, with no page-count guard — so the `NameError` fires even on a session with zero pages. A literal Colab "Run all" stops at the first uncaught exception, so cells 15–26 never execute in that pass.

The three real scenarios:

| Scenario | What happens | Final effective `run_inpaint_render_all` |
|---|---|---|
| (a) Fresh kernel + literal Run All | Aborts at cell 14 with `NameError` (unconditional call, cell 13:39). Cells 15–26 never run. | cell 13's wrap (last executed def) |
| (b) Fresh kernel + run in order, continuing past the cell-14 error | All 27 cells execute; cell 14's call still fails but is skipped/recovered. | cell 23's plain version |
| (c) Warm kernel (names exist) + Run All, or re-running cell 14 | **No NameError.** Cell 14's call executes the full quality-core pipeline — `apply_container_types` + irreversible `mask_only_translated` AND-shrink on ALL pages + `run_inpaint_all(force=True)` + `kill_residual` + `restore_boxes` + `run_render_all(force=True)` — as a side effect of running a "definition" cell. | cell 13's wrap, and it just ran destructively |

Scenario (c) is the owner-realistic destructive path: it requires only a warm kernel and a re-run of a cell that looks like a patch installer. It combines force-qualified re-inpainting with the irreversible mask shrink from DIS-3/P-6 in one accidental keystroke. This supersedes both reports' two-state ("fresh fails / warm wins") framing and should drive the Phase-2 entrypoint reconciliation.

## N-2 — The two vertical-render patches stack, they do not replace [FACT]

Cell 11's patch is guarded by `_QC_FINAL_RENDER_PATCHED` (cell 11:176); cell 12's by `_QC_RENDER_PATCHED` (cell 12:141). Different flag names → in sequential execution BOTH wrap: cell 12's wrapper captures cell 11's wrapper as `_qc_orig_render`, which itself captured the original cell-10 function as `_base_render`. Net call chain for non-vertical text: cell-12 wrapper → cell-11 wrapper → original — a double condition check per call. Behavior is equivalent (identical trigger conditions; cell 12's `_qc_render_vertical` handles vertical notes), but "cell 12's patch replaces cell 11's" — the impression both reports give — is structurally wrong. It is one more layering artifact of the redefinition jungle, and it means future edits to cell 11's wrapper are still live code in sequential flow, not dead code.

## N-3 — `sync_translate_stage` counts markers and NaN as translations [FACT]

Cell 23 lines 43–45: `has_translation = int(page_rows["translated_text"].astype(str).str.strip().ne("").sum())`. For a NaN cell, `astype(str)` yields `"nan"` — non-empty → counted. For marker rows, `"[UNTRANSLATED]"`, `"[SFX]"`, `"[EMPTY]"`, `"[TRANS_FAILED]"` are all non-empty strings → counted. A page whose rows are ALL failed/marker rows can therefore have its `translate` stage marked done (`if valid_bengali > 0 or has_translation > 0`, line 47) with zero real translations. This composes into a verified silent-failure chain:

1. P-7 inflation (`bengali_valid.astype(bool)` counts NaN as True — reproduced in T-6 and re-verified locally on pandas 2.2.3) OR the marker/NaN counting above → `translate` stage falsely marked done;
2. `render_all_pages(require_translation=True)` gates on the **stage flag**, not the data (cell 10:1001: `if require_translation and not stages.get("translate", False): continue`) → page becomes render-eligible;
3. The per-row render gate then skips every marker/non-Bengali row with only a WARN (cell 10:870–886) → a page that *looks* finished but shows untranslated/English text over inpainted art (reliability risk 6).

Mitigating precision: the currently-effective execution paths mostly bypass this chain — cell 23's own `run_inpaint_render_all` and the UI button both pass `require_translation=False`. The chain bites cell 15's defaults (`require_translation=True`) and `run_full_pipeline`, i.e., exactly the paths a Phase-2 re-hardening would restore. The fix must therefore cover BOTH the dtype coercion (P-7) and the marker/NaN counting (N-3), or re-hardening the stage gate will re-activate the silent failure.

## N-4 — P-7 blast-radius precision [FACT]

The four `astype(bool)` sites are not equal: cell 15:849 is display-only (inside a try/except that prints a DataFrame summary — no control flow); cell 23:42 is control-flow (stage marking, feeds N-3); cell 25:122/219 are UI statistics. The render path itself re-validates each row's text directly via `render_validate_bengali` (cell 10:874) and rejects non-Bengali strings, so P-7 does not put garbage text onto pages — its damage is stage bookkeeping, statistics, and downstream stage-gate decisions (via N-3). This narrows P-7's severity to Medium (as originally calibrated by GLM-5.3 and confirmed by Flash's T-6 refutation of the worse variant) but makes its control-flow site (23:42) the one that matters.

## N-5 — Retry/backoff constants pinned [FACT]

GLM-5.3's pipeline description said "retry w/ linear backoff (3×)"; Flash could not separately pin the constant and called it immaterial. Now pinned: cell 8 lines 80–83 set `retry.max_retries = 3`, `retry.backoff_seconds = 2`; line 380 reads them; line ~397 computes `sleep_time = backoff * (attempt + 1)` — linear backoff, 3 retries (4 attempts total), 2/4/6 s sleeps. The original claim was accurate; closed as confirmed.

---

# VERIFIED FACTS

Consolidated facts confirmed by BOTH agents with independent line-level evidence (full lists in the individual reports; evidence labels per the project's format):

1. Repository shape, cell count (27/0), two strata, filename oddity, single-commit notebook history. [FACT]
2. Full cell-to-component map (physical indices 0–26, banner names). [FACT]
3. Model inventory and loading behavior per the Agreements section, including RT-DETR float32 (no dtype arg), Qwen fp16 gated on CUDA+config, local HF cache for Qwen weights, OvisOCR2 placeholder. [FACT]
4. Stored-output forensics: run of 2026-08-31 12:18, Python 3.13.15, T4 14.56 GB, `/content/mangabd`, `hf_token` not set, outputs in physical 0,1,2,3,5,6 only, all stream-type, `execution_count` None everywhere (post-processed JSON). [TEST RESULT]
5. All 27 cells AST-parse cleanly; the hazards are execution-order issues, not syntax issues. [TEST RESULT]
6. Redefinition map: `run_inpaint_render_all` ×5 (11,12,13,15,23), `kill_residual` ×3 (11,13,14), `render_bengali_text` patches ×2 with stacking (N-2), `apply_container_types`/`restore_boxes` ×2 (11,12 — cell 12 wins), `translate_with_nllb` ×2 (8,19), detection wrappers ×2 (6,24). [TEST RESULT]
7. Module-level pipeline executions: cell 14 (`run_inpaint_render_all(force=True)`), cell 23:89 (`sync_translate_stage()`), cell 20 (`apply_translations_from_ai_file()`), cell 26 (`render_all_pages(force=True)`); font downloads in 11/12; UI build in 25. [TEST RESULT]
8. Fresh Run-All failure mechanism and the three-scenario model (N-1). [TEST RESULT — static; one confirming Colab run still open, see T-8]
9. Box-snap variant analysis: cell 12's unguarded variant is the effective one (DIS-3). [FACT]
10. `bengali_valid.astype(bool)` NaN→True inflation, reproduced independently on pandas 2.2.3; quoted-string worse variant refuted. [TEST RESULT]
11. Marker-set drift: cell 8 (6 markers, no `"nan"`) is the effective render-skip set; cell 10's local set (with `"nan"`) is dead code via the globals-preference block (cell 10:156–161); cell 16's local set (with `"nan"`, line 227) is live for QA. [FACT]
12. `sync_translate_stage` marker/NaN counting gap (N-3) and stage-flag render gating (cell 10:1001). [FACT]
13. In-place artifact mutation sites and irreversibility (11:96/117/130, 13:31). [FACT]
14. UI button bypass (25:363–365); `reset_checkpoint` memory-only (25:230–245). [FACT]
15. Secrets: none embedded; sanitizer active; both agents' scans clean. [TEST RESULT]
16. Zero image outputs / zero image files → NO_VISUAL_EVIDENCE_AVAILABLE. [TEST RESULT]

---

# UNKNOWN / NEEDS EVIDENCE

Merged open questions, ordered by decision impact:

1. **Owner's canonical cell execution order** (blocks DIS-2 resolution and all Phase-2 entrypoint work). Only the owner can answer.
2. **Whether the QUALITY CORE behavior (box-snap → narrator, synthetic white boxes with black borders, residual killing) is currently desired** in the final pipeline, or whether cell 23's plain behavior is the accepted latest state. The two produce visibly different outputs.
3. **T-8: one confirming Colab run** — fresh Run-All to confirm the static NameError analysis and the N-1 scenario model against real runtime; also which transformers/pandas versions the last successful full run used.
4. **Actual output quality** — unassessable until sample artifacts (original/detections/mask/inpainted/final for one page) are committed.
5. Whether `SLICE_MODE=True` has been validated against non-strip pages (dedupe merging distinct dense regions).
6. Whether the NLLB fallback BOS id `100362` is still correct for the runtime transformers version.
7. Whether `ogkalu/comic-text-and-bubble-detector` remains available/unchanged upstream (unpinned remote dependency).
8. Whether the "(3)" notebook is the owner's newest snapshot.
9. Cell 4 (zyddnys clone/patch, fonts, libraqm test) status in the last saved session — no stored output (DIS-1).

---

# IMPORTANT RISKS

Severity-adjusted merged register (highest first):

| # | Risk | Severity | Source |
|---|---|---|---|
| R-1 | Entrypoint chaos: 5 definitions of the pipeline function, module-level executions, fresh-run bootstrap failure, and the warm-kernel destructive scenario N-1(c) | **Critical** | P-1/P-2, F-0/F-2/F-3, N-1 |
| R-2 | Box-snap misfire blast radius: unguarded cell-12 variant + destructive synthetic `restore_boxes` over-paint → permanent artwork damage | **High** (upgraded from Medium) | P-5 + F-1/DIS-3 |
| R-3 | Irreversible in-place artifact mutation (mask AND-shrink compounds; inpainted overwrite); undo requires full re-inpaint; scenario N-1(c) triggers it accidentally | **High** | P-6, reliability 2/3 |
| R-4 | Silent-failure chain: false translate-done marking (P-7 + N-3) + stage-flag gating + WARN-only render skips → pages that look finished but aren't | **Medium-High** | P-7, N-3, reliability 6 |
| R-5 | `recover_coordinates` reverts coordinates + region_type + manual edits on re-execution | **Medium-High** | P-3 + F-6/DIS-4 |
| R-6 | Dependency drift: no pinning; the NLLB breakage (cell 19 exists) proves the failure class; RTDetrV2/Qwen processor APIs equally exposed | **Medium** | reliability 4 |
| R-7 | Widget-state vs kernel-state divergence in Control Studio; UI bypasses wraps | **Medium** | reliability 8, weakness 3 |
| R-8 | kill_residual v1 out-of-bounds crash (unguarded empty crop) if v1 variant is re-executed | **Low-Medium** | F-5 |
| R-9 | Orphaned per-page artifacts after `reset_checkpoint` (storage leak) | **Low-Medium** | reliability 7 |
| R-10 | Maintainability: redefinition jungle, dead code, magic numbers, mixed-language comments, 800 KB single artifact | **Medium** (structural) | weakness 5/8/9 |

---

# RECOMMENDED NEXT INVESTIGATION

Ordered, with owners:

1. **Owner answers the five blocking questions** (see USER DECISION below). Everything else is blocked or speculative until then.
2. **One confirming Colab run (closes T-8):** fresh kernel → Run All → record where it stops (expect NameError at cell 14 per N-1(a)); then run remaining cells in order; then in the warm kernel re-run cell 14 and observe scenario N-1(c) on a sacrificial copy of one page's artifacts. This converts the three-scenario model from static analysis to runtime proof. No repo changes required — run on a copy.
3. **Commit visual evidence:** one small sample page plus its artifacts (`original.jpg`, `detections.json`, `text_mask.png`, `ocr.json`, `translation.json`, `inpainted.png`, `final.jpg`, `qa.json`) so both agents can review output quality concretely. Until then, rendering/inpainting quality remains unassessable for everyone.
4. **Verify N-3 end-to-end in the sample session** (translate-done marking with only marker rows) — cheap once #3 exists.

---

# TECHNICAL PROPOSAL

**PHASE 2 PROPOSALS ONLY — NOT IMPLEMENTED. Owner approval required before any code change.** Merged from both agents' recommendation lists (which independently converged) plus the comparison findings:

1. **Reconcile the pipeline entrypoint (R-1).** One authoritative `run_inpaint_render_all`; remove or guard all module-level pipeline executions (cells 14, 20, 23:89, 26) so a fresh Run All survives. Acceptance test: fresh kernel → Run All → no NameError, no unintended GPU work. Must be designed against the N-1 three-scenario model, not just the fresh-run case — the warm-kernel re-run is the dangerous one.
2. **Merge the two box-snap variants (R-2).** Restore cell 11's 5-point probe, border exclusion, and 4× area cap inside the cell-12 lineage; make `restore_boxes` opt-in. Highest art-preservation risk in the codebase.
3. **Make quality-layer artifact mutation reversible/idempotent (R-3).** Re-derive from `original` + `mask` per run, or write versioned artifacts; never AND-shrink the stored mask in place.
4. **Fix the translate-stage bookkeeping (R-4).** Replace `.astype(bool)` consumers with an explicit coercion (`fillna(False)` on a normalized column, or persist 0/1) AND fix `sync_translate_stage`'s marker/NaN counting (skip rows where `is_special_marker(translated_text)` or the text is NaN) — fixing only the dtype re-arms the failure via N-3 when the stage gate is re-hardened.
5. **Commit visual evidence + pin the environment (closes UNKNOWN 3/4/6).** Sample artifacts; `requirements.txt` or Colab-tested pins.
6. **Consolidate duplicates.** One Bengali validator, one marker set (decide explicitly whether `"nan"` belongs — if it does, add it to cell 8's set, which is the effective one), one ai.Text implementation (2 parsers + 1 builder today), one `kill_residual`.
7. **Document the canonical cell execution order**, or extract a `mangabd/` package with an explicit composition root (notebook as thin driver). Also decide the fate of the stacked render patches (N-2) — keep one.

---

# ALTERNATIVES

**A. Minimal in-notebook reconciliation (quick win).** Do proposals 1, 4, 6 inside the notebook only; keep the single-artifact shape. Lower risk, immediate unblocking of fresh Run-All, but the 800 KB redefinition-jungle maintainability problem (R-10) remains.

**B. Module extraction (structural fix).** Extract a `mangabd/` package with an explicit composition root; notebook becomes a thin driver. Eliminates the entire class of execution-order hazards (R-1, N-1, N-2) by construction, enables real tests and diffs — but is a large refactor of an artifact with NO visual regression evidence yet, so it should follow (not precede) proposals 3–5.

Both agents' reports independently favor B as the end state and A as the immediate step. **Recommended sequence: A first (proposals 1, 4), then evidence gathering, then B.** Owner decides.

**For R-4 specifically:** alternative fixes are (i) `fillna(False).astype(bool)` at consumers, (ii) persisting `bengali_valid` as 0/1 integers, or (iii) enforcing bool dtype on load. (ii) is the most CSV-round-trip-robust; (i) is the smallest diff. Either must be paired with the N-3 marker fix.

---

# USER DECISION

**AWAITING OWNER.** The following decisions gate Phase 2 (no implementation has started):

1. What is your canonical cell execution order in Colab? (fresh Run-All / core-then-patches / other manual order)
2. Is the QUALITY CORE behavior (box-snap → narrator, synthetic white boxes, residual killing) currently desired in the final pipeline — or is the plain cell-23 behavior the accepted state?
3. Are `restore_boxes`' synthetic black-bordered white rectangles an accepted stylistic choice or a temporary workaround?
4. Should `SLICE_MODE=True` remain the default (validated on non-strip pages)?
5. Is `MangaBD_V12_ipynb_txt.ipynb (3).txt` the newest snapshot? (If a newer local copy exists, it must replace this one before any Phase-2 work.)
6. Approve Phase-2 proposal sequence A-then-B (or choose otherwise)?

---

# IMPLEMENTATION

NOT STARTED

---

# VERIFICATION

NOT STARTED

---

# FINAL OUTCOME

NOT DECIDED

---
---

# ═══ MANGABD-002 — PHASE B: SECOND-PASS REVIEW, FINAL ENGINEERING PROPOSAL ═══

**Date: 2026-09-16. Participants: GLM-5.3 (second-pass review + proposal), GLM-5.3-Flash (independent investigation + review, commit 4e3d239), Project Owner (decision pending).**

**DECISION STATUS: WAITING_FOR_USER.** Nothing in this section has been implemented. Phase C (implementation) starts only after the Project Owner explicitly approves the §B.6 patch.

Inputs compared: (1) GLM-5.3's original Phase A analysis (agents/GLM_5_3.md §T2.0–T2.11, commit d7622d7), (2) GLM-5.3-Flash's independent investigation + review (agents/GLM_5_3_FLASH.md §F2.0–F2.7, verdict APPROVE_WITH_CORRECTED_JUSTIFICATION, four challenges C-1..C-4), (3) the actual current repository. Per protocol, every disagreement was re-verified against the underlying code in a fresh session — not argued from memory.

---

## B.1 Second-Pass Verification Method (GLM-5.3, this session)

**Code re-verification [FACT, line-pinned this session]:** cell 13 in full (wrap structure lines 35–45); cell 12 `_snap_white_box` (30–42), `apply_container_types` (44–68, unconditional `save_translation_df()` at 66), `restore_boxes` (71+); cell 11 `_has_valid_trans` (84–86), `mask_only_translated` (88–97, `cv2.bitwise_and` + `save_image_artifact` at 96); cell 14 in full (title-only banner at 1, `globals()` rebind at 37, the fix site at 40); cell 1 `choose_base_directory` (67–103: active Drive mount request 80–88, Drive preference 91–94, local fallback 96–100); cell 3 module-level loads (992–993); cells 20:1 / 23:89 / 26:1 module-level calls; cell 25 UI handler (363–366); all five `run_inpaint_render_all` signatures + `inpaint_all_pages` (9:598) + `render_all_pages` (10:982).

**Independent runtime reproduction [TEST RESULT]** (`scripts/fresh_repro_drive.py`, analysis workspace, outside the repo): unlike the Phase A reproduction (which stubbed the quality helpers and therefore could only model the empty-disk state), this execution uses **verbatim AST-extracted helper sources from cells 11/12 + the whole verbatim sources of cells 13 and 14**, real cv2 4.13.0 / numpy 2.1.3 / pandas 2.2.3, and an in-memory artifact store modeling a Drive-persisted session (1 page, 2 translation rows — one valid, one not — real original/mask images). Six scenarios:

| Scenario | Kernel / Disk / Cell-14 code | Result | Persisted mutations |
|---|---|---|---|
| DR-A | fresh / Drive / current | **NameError `run_inpaint_all`**, frames `cell_14.py:40 → cell_13.py:39` | **YES** — see below |
| DR-B | warm / Drive / current | OK, full pipeline fires | YES (same as DR-A) + pipeline calls |
| DR-C | fresh / Drive / guarded | OK, clean printed skip | **ZERO** |
| DR-D | warm / Drive / guarded | OK, call sequence **identical to DR-B** | YES (same as DR-B) |
| ED-A | fresh / empty / current | NameError (matches Phase A scenario A) | one idempotent empty-CSV rewrite |
| ED-C | fresh / empty / guarded | OK, clean skip (matches Phase A scenario C) | ZERO |

DR-A mutation record (the decisive evidence for C-1): row `r1` coordinates snapped `(55,65,110,70) → (52,62,116,76)`, `region_type` `bubble → narrator`, `save_translation_df()` called (CSV rewritten); stored mask AND-shrunk **13,800 → 9,600 px** (the untranslated row's region zeroed — irreversible), `save_image_artifact(p1,"mask")` called; **then** the NameError. Full printout preserved in the workspace script output.

---

## B.2 Disagreement / Challenge Adjudication (all verified against code this session)

| ID | Flash's challenge (F2.4) | Verification performed | Verdict |
|---|---|---|---|
| **C-1 (significant)** | GLM-5.3's "pre-crash work on fresh is provably empty / outcome-neutral by construction" (T2.2.2 obs. 2, T2.7 point 3) is refuted in the Drive-persisted state: real mutations occur before the abort | Five-component code chain verified: cell 1:80–94 (Drive mount request + preference) → cell 3:992–993 (module-level disk loads) → cell 13:36 (`apply_container_types`) → cell 13:37–38 (per-page `mask_only_translated`) → cell 13:39 (crash line). Mutation carriers verified: cell 12:57–66 (snap + region_type + unconditional CSV save), cell 11:91–96 (mask AND + artifact save). **Independently reproduced (DR-A vs DR-C).** | **UPHELD — Flash is right.** GLM-5.3's Phase A claim holds only for the empty-disk state its E2 modeled. Correction accepted; §B.5/B.6 restate the justification accordingly. |
| **C-2 (moderate)** | R1 omits that post-fix fresh Run All + Drive data performs real work at cells 20/23/26 (incl. forced re-render), not just "newly-reachable environmental risk" | Verified: cell 20:1 `apply_translations_from_ai_file()` (applies any `ai_text_export*.txt`), cell 23:89 `sync_translate_stage()` (marks stages), cell 26:1 `render_all_pages(force=True)` (forced full re-render). | **UPHELD.** Folded into R1 (§B.8) and the owner-facing disclosure (§B.6). |
| **C-3 (minor)** | "Cell ORDER is intended" rests on placement banners in cells 11/12 only; cells 13/14 — the cells that actually break fresh runs — carry no placement banner | Verified: `Place:` banners exist at 11:3 and 12:3 only; cell 13:1 and 14:1 carry title-only banners ("RESIDUAL KILLER", "kill_residual v3"). | **UPHELD.** T2.1.1's inference is acceptable for the patch layer as a whole; evidence for cells 13/14 specifically is thinner — they read as patch-session scratch cells. Root cause and fix unaffected. |
| **C-4 (cosmetic)** | Proposed guard comment says "the orchestrator (Cell 11)" — old banner numbering vs physical numbering used everywhere else | Verified in GLM-5.3's own T2.7 text. | **UPHELD.** Comment corrected in the final patch (§B.6); corrected wording already executed in DR-C/DR-D. |

**One wording nit found in Flash's review (does not affect any conclusion):** F2.5.3 lists `sync_translate_stage` among free names "defined by cells ≤13" — it is defined at cell 23:28. The guard-sufficiency CONCLUSION is still sound because the only variant needing that name (cell 23:71) can only be bound after cell 23 has executed, and cell 23:28 precedes 23:28→71 binding in the same cell; no `del` statements exist anywhere (Phase A E1), so the name cannot disappear afterwards.

**Convergence check:** every other claim in F2.1–F2.6 matches GLM-5.3's Phase A and the code: single abort site; five-variant hunger table; deferred-NameError mechanism; guard-flag stickiness; four-path execution matrix; `require_translation` divergence (15:678 defaults `True`; 11/12/13/23 default `False` — verified this session); UI-button bypass at 25:363–366.

**New second-pass observations (in neither agent's prior report):**

1. **The guard idiom is native to this codebase.** Cell 25's UI handler already gates the same dependency with `if "run_inpaint_all" in globals() and "run_render_all" in globals(): … elif "run_inpaint_render_all" in globals(): …` (25:363–366). The proposed fix adopts the notebook's own established dependency-declaration pattern — it is not a foreign idiom introduced by reviewers.
2. **Warm "re-apply" has two sub-cases** that the Phase A text conflated: (a) re-running cells 13→14 re-binds and fires the quality wrap; (b) re-running cell 14 alone in a fully-warm kernel fires whichever variant was bound last (normally cell 23's plain variant). The guard is variant-agnostic (all five variants need exactly the two checked names), so it is correct under both sub-cases. Flash's F2.1.5 table captured this correctly ("whichever variant was last bound").
3. **Even empty-disk fresh performs one disk write** — the unconditional `save_translation_df()` at cell 12:66 (idempotent empty-CSV rewrite; Phase A noted this, but the Drive dimension upgrades the same line from "harmless" to "mutation carrier").

---

## B.3 Final Root Cause (dual-agent confirmed; three layers)

**Layer 1 — Immediate mechanism [FACT + TEST RESULT, dual-confirmed]:** physical cell 14, line 40, executes `run_inpaint_render_all(force=True)` at module level. On a fresh sequential run the name is bound to cell 13's quality-core wrap (defined 13:35, rebound 13:45), whose body resolves `run_inpaint_all` (13:39) and `run_render_all` (13:44) — defined only in cell 15 (15:634, 15:656). Python resolves function-body globals at call time → **deferred NameError** (the callee exists; its body's dependency does not) → Run All aborts; cells 15–26 never execute in that pass. **Positional invariant (both agents, independently derived):** all five `run_inpaint_render_all` variants require the two cell-15 names, so ANY module-level call to this name placed before cell 15 fails on a fresh kernel regardless of which variant is bound. On Drive-persisted state the abort is **preceded by destructive persisted mutations** (B.2/C-1: coordinate snap + region_type rewrite + CSV save + irreversible mask AND-shrink).

**Layer 2 — Structural cause [FACT, dual-confirmed]:** the patch layer (cells 11–14, 19–26) follows a "define-and-immediately-apply" authoring pattern — each hotfix cell both (re)defines functions AND executes pipeline work at module level (14:40, 20:1, 23:89, 26:1, plus the print-side-effect at 11:203). The pattern is only sound in a warm kernel where later cells have already run; cell 14 is the only site whose dependency graph points forward (before its own definition). The five variants also have **divergent semantics** (`require_translation` default `True` at 15:678 vs `False` elsewhere), so "making the name exist" is not equivalent to "preserving behavior" — which variant is live changes what the same call does.

**Layer 3 — Process cause [FACT, dual-confirmed]:** no fresh-run test has ever existed. Stored outputs show the last saved session executed only cells 0,1,2,3,5,6; execution counts were cleared; the artifact is a manual `.txt` snapshot of an `.ipynb`. The notebook's known-good state lives in warm Colab kernels, not in the repository, so the fresh-run regression persisted unnoticed across the patch-layer era.

---

## B.4 Contributing Causes (final merged register, evidence-tagged)

1. Five redefinitions of `run_inpaint_render_all` (11:190, 12:155, 13:35, 15:678, 23:71); the pre-cell-15 bindings are the most name-hungry variants. [FACT]
2. Cell-13 wrap execution order: `apply_container_types()` (13:36) and the per-page `mask_only_translated()` loop (13:37–38) run BEFORE the failing `run_inpaint_all` (13:39) — with Drive data these are destructive *(corrected wording vs Phase A T2.4 factor 2, which said "before any page iteration")*. The 13:39 call itself is unguarded by any page-count check, so the NameError fires even on a zero-page session. [FACT + TEST RESULT]
3. The define-and-immediately-apply pattern across patch cells; cell 14 is the only forward-pointing instance — the others (20, 23, 26) are fresh-safe by luck of placement, not design. [FACT]
4. **Fresh KERNEL ≠ fresh DISK** [Flash F2.1.4, now dual-confirmed]: cell 1 actively requests Drive mount and prefers `/content/drive/MyDrive/MangaBD_V12`; cell 3 loads `MANGABD_MANIFEST`/`translation_df` from disk at module level. A fresh runtime therefore inherits the previous session's real pages/rows/artifacts whenever Drive is mounted. Whether the owner actually uses Drive persistence is UNKNOWN (the one stored session used local `/content/mangabd`).
5. `apply_container_types`' unconditional `save_translation_df()` (12:66) — idempotent on empty disk, mutation-carrier on Drive. [FACT]
6. Sticky patch guards (`_QC_FINAL_RENDER_PATCHED` 11:187, `_QC_RENDER_PATCHED` 12:152, `_MBD_SLICED` 24:122, `colab_files.__mbd_patched` 24:46) make re-application semantics session-history-dependent. [FACT]
7. `globals()`-rebinding idiom (11:200, 12:162, 13:45, 14:37) makes the binding timeline order-sensitive and defeats naive def-before-use reasoning. [FACT]
8. No execution-order documentation, no CI, no fresh-run smoke test — the failure mode was structurally invisible to the owner's workflow. [FACT]
9. Post-abort surface (cells 15–26) has never executed in a fresh sequence; statically name-safe (dual-independent simulators) but runtime-unproven on fresh. [FACT + UNKNOWN]

---

## B.5 Corrected Understanding (what changed since Phase A, and why)

1. **"Pre-crash work on fresh is provably empty" — RETRACTED as a universal claim; holds only for empty disk.** In the Drive-persisted state, cell 14's call snaps coordinates, rewrites region_type, persists the CSV, and irreversibly AND-shrinks stored masks BEFORE the NameError (GLM-5.3's own DR-A reproduction, §B.1 — not accepted on Flash's authority). **Direction of the correction strengthens the fix:** the guard is not merely "skips no-op work"; in the realistic Drive scenario it PREVENTS artifact corruption (DR-C: zero mutations). The empty-disk neutrality proof alone was insufficient justification; the DECISION-grade justification is now "declare the dependency; fire only in the warm path that already works today; prevent the Drive-fresh mutate-then-crash".
2. **Phase A T2.4 factor 2 wording corrected** (see B.4.2): the mask loop precedes the failing line; what is true is that the failing call is unguarded and precedes the kill/restore loop.
3. **"Cell order is intended" — scope narrowed** (C-3): proven for the patch layer via the 11:3/12:3 banners; cells 13/14 carry no placement banners and read as patch-session scratch cells whose placement nobody reconsidered.
4. **Warm re-apply has two sub-cases** (re-run 13→14 vs re-run 14 alone); the guard is correct under both because it is variant-agnostic.
5. **The guard idiom is the codebase's own** (cell 25:363–366 uses the same `in globals()` check for the same names) — the fix is stylistically native, not reviewer-foreign.

---

## B.6 RECOMMENDED FIX (final; executable code byte-identical to Phase A proposal — only the comment changed per C-4)

**File:** `MangaBD_V12_ipynb_txt.ipynb (3).txt` — physical cell 14, replacing the single line 40 `run_inpaint_render_all(force=True)` with:

```python
# MANGABD-002: run_inpaint_render_all calls run_inpaint_all/run_render_all, which
# the orchestrator cell (physical cell 15; banner numbering "Cell 11") defines
# LATER in a fresh Run All. Skip the pipeline run until they exist.
if ("run_inpaint_all" in globals()) and ("run_render_all" in globals()):
    run_inpaint_render_all(force=True)
else:
    print("  ⏭️ kill_residual v3 loaded; pipeline run skipped (orchestrator not loaded yet)")
```

**Justification (corrected per C-1/C-2):**

1. **One cell, one statement, 7 lines replace 1 (+6 net), single hunk.** No definition moves; no binding-timeline change; the `def`s and `globals()` rebinds in cells 13/14 untouched.
2. **Warm-kernel behavior preserved exactly** — dual-confirmed by runtime reproduction on both disk states (Phase A E2: `calls_B == calls_D`; this session DR-B == DR-D, Drive state). The owner's interactive re-apply workflow is unaffected, under both warm sub-cases (B.5.4).
3. **Fresh-run skip is strictly safer than today's code in every modeled state** — empty disk: skips one idempotent empty-CSV rewrite (ED-A → ED-C); Drive: **prevents destructive pre-crash mutations** (DR-A → DR-C). Nothing of value is skipped; corruption is.
4. **It declares the dependency, it does not hide the error.** Not a try/except, not a silent fallback, not a dummy variable, not a global hack — the four forbidden patterns in TASK_002 are all avoided. The else-branch prints a visible, greppable reason. The idiom is the notebook's own (cell 25:363–366).
5. **No other module-level call needs the same treatment** — cells 20/23/26 are fresh-safe by construction (dual-independent transitive-closure analysis + manual reads). Guarding them would be unnecessary change, which TASK_002 forbids.

**Owner-facing disclosure (required by C-2 — this is what fresh Run All will do after the fix):** on a Drive-persisted runtime, a fresh Run All proceeds past cell 14 for the first time and executes real work at module level: cell 20 applies any `ai_text_export*.txt` found in storage; cell 23 syncs translate-stage flags; cell 26 runs `render_all_pages(force=True)` — a forced full re-render of every eligible page. This is the codebase's current intent once unblocked (and TASK_002's preservation mandate), not a side effect of the guard, but it may trigger hours of GPU work and artifact overwrites at Run-All time. If the owner does NOT want Run-All-time rendering, say so when approving — a `force=False` question for cell 26 is a separate one-line follow-up the Owner can bundle into this approval (out of MANGABD-002's minimal scope otherwise).

**What this fix deliberately does NOT change:** the fresh-vs-warm pipeline fork (fresh-final binding = cell 23's plain variant; Owner Question 2 in the MANGABD-001 record gates the canonical-variant decision); the warm-kernel destructive scenario N-1(c); sticky guards; stacked render patches (N-2); the redefinition jungle. All deferred to the structural phase (MANGABD-001 proposals 2–7).

---

## B.7 Alternative Solutions Considered (final; smallest-safe-first)

| # | Option | Verdict | Rationale (cumulative, both agents) |
|---|---|---|---|
| 0 | Do nothing / document only | REJECT | fails the task objective (fresh Run All must work). |
| 1 | **Dependency guard at the 14:40 call** | **RECOMMENDED** | §B.6. Only option that is fresh-safe in BOTH disk states while preserving warm semantics byte-identically. |
| 2 | Delete the 14:40 call outright | REJECT (as primary) | smaller diff but CHANGES warm behavior (re-running cell 14 would no longer re-apply the pipeline) — violates preservation without evidence the owner doesn't use that flow. |
| 3 | Move the call to a new end-of-notebook cell | REJECT (for 002) | bigger diff; duplicates cell 26's intent; **and (Flash F2.5.6, verified) it changes WHICH variant executes** — after cell 15 the binding is 15's `require_translation=True` variant, after cell 23 the plain variant — neither matches the owner's current warm re-apply semantics on the paths where the quality wrap applies. Revisit as structural follow-up. |
| 4 | Reorder cells (move 11–14 after 15) | REJECT | reshuffles every redefinition winner, invalidates both agents' maps, contradicts the 11/12 banner placement, highest regression risk. |
| 5 | Early stub definitions of `run_inpaint_all`/`run_render_all` | REJECT | explicitly forbidden by TASK_002 (dummy variables); silently changes fresh semantics. |
| 6 | Structural fix: single composition root / extracted `mangabd/` package | DEFER | correct end-state (MANGABD-001 Alternative B) but far beyond 002's minimal scope; blocked on Owner Questions 1/2 (canonical order; canonical variant). |

---

## B.8 Regression Risk Register (final; R1 amended per C-2, R3 verified this session)

| # | Risk | Likelihood | Impact | Mitigation / note |
|---|---|---|---|---|
| R1 | **(amended)** Post-fix fresh Run All newly reaches cells 15–26. Two dimensions: (a) environmental failures of newly-reachable code (cell 0/4 installs, GPU) — self-tests fail LOUDLY by design, correct behavior; (b) **real pipeline work over Drive-persisted data at cells 20/23/26, including a forced full re-render at 26:1** — possibly hours of GPU work and artifact overwrites at Run-All time. | Medium | Medium | (a) expectation-setting only; (b) disclosed to the Owner in §B.6 — if unwanted, the Owner can bundle a cell-26 `force=False` follow-up into the approval. Not a defect of the guard; it is the codebase's current intent once unblocked. |
| R2 | Fresh Run All leaves the plain (cell 23) pipeline bound; owner expects quality-core. | Low | Medium | Pre-existing fork (not introduced by the fix); Owner Question 2. The guard's printed skip line makes the fresh path visible in logs. |
| R3 | Guard-condition staleness: a future edit that changes which variant is bound at cell 14, or its free-name set, could desynchronize the guard. | Low | Low | All five current variants need exactly these two names (dual-verified hunger tables); the code comment states the dependency; both agents' reports document the check procedure. |
| R4 | A future rename of `run_inpaint_all`/`run_render_all` would turn a hard crash into a printed skip (error softening). | Low | Low | The else-branch prints loudly; a rename is a reviewed code-change event anyway. |
| R5 | Notebook JSON edit corrupts the artifact. | Low | High | Phase C protocol (§B.9): programmatic edit + JSON re-parse + AST re-validation + single-hunk diff + mode check (100644 — see the file-mode incident, worklog Task 3 addendum) + Flash review. |
| R6 | Owner's warm workflow silently diverges from fresh (fix works warm; owner never notices fresh is now different). | Medium | Low | Intended outcome of the task (deterministic fresh behavior); documented here and in §B.6. |

**Residual risk NOT introduced but NOT fixed by this change (explicitly out of scope, tracked in the MANGABD-001 register):** the warm-kernel destructive scenario N-1(c) (re-running cell 14 with pages loaded fires force-inpaint + irreversible mask shrink) and the Drive-fresh mutation class now proven by DR-A remain reachable through the WARM path and through any manual fresh continuation that re-runs cell 14 after cell 15. The guard removes the FRESH Run-All instances only. Full remediation is MANGABD-001 proposals 2–3 (opt-in `restore_boxes`, reversible artifact mutation), Owner-gated.

---

## B.9 Exact Files / Cells Requiring Modification (Phase C scope)

| Item | Value |
|---|---|
| File | `MangaBD_V12_ipynb_txt.ipynb (3).txt` (the repository's only source artifact) |
| Location | `cells[14]` in the notebook JSON (physical cell 14; banner title "kill_residual v3"), final source line (line 40) |
| Change | Replace 1 line with the 7-line guarded block (§B.6). Single hunk. |
| Everything else | **Untouched.** All 26 other cells byte-identical; no agent-doc changes count as source (TASK_002 permitted files during investigation). |
| Phase C protocol | Programmatic JSON edit of `cells[14].source`; then verify: JSON re-parses; cell count still 27; cell 14 AST-parses; the `def`/`globals()` statements in cells 13/14 byte-identical; `git diff` = exactly one hunk in one file; file mode preserved 100644; commit only after Flash's Phase D sign-off per TASK_002. |

---

## B.10 Verification Strategy (Phase D — for GLM-5.3-Flash, after Phase C)

1. **Static re-check:** re-run the fresh-kernel simulator against the edited notebook → abort-class site count must be 0; definition timeline unchanged except cell 14's tail.
2. **Diff audit:** exactly one hunk in `MangaBD_V12_ipynb_txt.ipynb (3).txt`; JSON parses; 27 cells; cell 14 AST-parses; guard text matches §B.6 verbatim; file mode 100644.
3. **Guard-logic equivalence:** re-run the six-scenario Drive-state reproduction (§B.1 matrix as the expected baseline: edited-notebook DR-A becomes OK-with-skip and zero mutations; DR-B == DR-D still; ED-C unchanged) against the EDITED notebook file — not a hand-edited copy.
4. **Colab fresh Run All (strongest practical test; requires the Owner or a Colab-capable environment — closes T-8):** fresh runtime → Run All → expect: no NameError; the skip line printed after "kill_residual v3 active"; self-test banners print; notebook reaches cell 26. With Drive mounted, additionally expect (disclosed behavior, §B.6): cells 20/23/26 perform real work including the forced re-render.
5. **Warm-path functional check:** in the same session, upload one page via the Control Studio UI → Detect + OCR + translate → run the "final" button → confirm outputs are produced normally (the guard must not have disabled anything in the warm path).
6. **Limitation:** if Colab is unavailable to both agents, static + local-runtime evidence stands (as in Phases A/B) and full fresh-runtime confirmation is explicitly deferred to the Owner's first Run All.

---

## B.11 Owner Inputs Requested (WAITING_FOR_USER)

1. **Approve or reject the §B.6 patch** (single-cell dependency guard). This is the only approval blocking Phase C.
2. **Optional bundle:** should cell 26's Run-All-time `render_all_pages(force=True)` become `force=False` (or otherwise not fire on Run All)? Only relevant if you do not want a forced full re-render whenever you Run All with data present (§B.6 disclosure).
3. **Drive usage (new, per C-1):** do you run with Google Drive persistence (the notebook's designed primary) or local `/content/mangabd` (used in the one stored session)? This calibrates the weight of R1(b) and the residual Drive-fresh mutation class (§B.8 residual note).
4. **Workflow question (carried from Phase A T2.10):** is fresh Run All ever your canonical workflow, and was cell 14's immediate-execution intentionally used as "re-apply quality core"? The fix preserves the warm path either way; the answer only weights R2/R6.
5. **Still open from MANGABD-001 (gate the STRUCTURAL follow-up, not this fix):** canonical execution order (Q1) and canonical pipeline variant (Q2).

---

## B.12 Phase B Outcome

Both agents independently investigated (statement-level fresh-kernel simulators + verbatim-code runtime reproductions), exchanged reviews, and converged on: root cause = three-layer (positional deferred-NameError / define-and-immediately-apply pattern / no fresh-run test); recommended fix = single-cell dependency guard; all four Phase A→B corrections resolved by repository evidence, with GLM-5.3's own Drive-state reproduction independently confirming Flash's decisive C-1 challenge. Zero source code modified during Phases A and B.

**NEXT STEP: Project Owner decision on §B.11.1 (and optionally B.11.2–B.11.4). Status remains WAITING_FOR_USER until then.**
