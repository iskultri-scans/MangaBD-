# MangaBD — Engineering Decision

## STATUS

REVIEW_COMPARISON_COMPLETE — Phase 1 dual-agent audit finished. Findings compared, disputed claims re-verified against the repository, and reconciled in this file. Awaiting owner decisions before any Phase 2 work.

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

MANGABD-001 — Initial Codebase Audit (Phase 1, no source changes)

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
