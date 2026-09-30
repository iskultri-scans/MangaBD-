MangaBD — Task 003
TASK ID
MANGABD-003
STATUS
OPEN
TASK TYPE
Visual Quality, OCR Accuracy & Translation Engine Upgrade
OBJECTIVE
Implement the 5 verified proposals (V-1 to V-5) from GLM-5.3's Phase A and GLM-5.3-Flash's Phase B review to fix the critical visual, OCR, and translation quality issues identified in the S001_color_webtoon sample.

BACKGROUND
- MANGABD-001 & MANGABD-002 are COMPLETE. The notebook's fresh-run reliability is fixed (Phase D Approved).
- S001 Visual Review revealed that while the pipeline works end-to-end, the output quality is not production-ready:
  1. NLLB translation quality is unusable for profanity/idioms (e.g., "fuck" -> "যৌনসঙ্গম").
  2. CJK fallback font in vertical notes is too small and pale.
  3. Vertical-note OCR mis-transcribes rotated text.
  4. Mask under-coverage leaves residue at the bottom of vertical notes.
  5. Manual translation workflow lacks visibility for silent line losses.
- GLM-5.3 proposed 5 fixes (V-1 to V-5). GLM-5.3-Flash independently reviewed and APPROVED_WITH_CHANGES, providing strict amendments that MUST be followed.

IMPLEMENTATION BATCHES
To minimize regression coupling and maintain the single-hunk audit convention, implementation MUST proceed in this exact order:

BATCH 1: Geometry & Rendering Polish (Safe, Disjoint)
- V-4a: Manual Workflow Polish (Unparsed-line report only. Edit C is DEFERRED).
- V-2: Mask-Miss Residue / Vertical Band (Cell 6 insertion).
- V-1: CJK Fallback Glyph Size/Weight (Cells 11 & 12 mirror edit).

BATCH 2: OCR Accuracy (Behavioral Change)
- V-3: Vertical-Note OCR (Cells 7 & 16).

BATCH 3: Translation Architecture (High Impact)
- V-5: Provider-Flexible Translation (Cells 8 & 25).

STRICT AMENDMENTS (MANDATORY FROM FLASH'S PHASE B REVIEW)
GLM-5.3 MUST implement these exact corrections. GLM-5.3-Flash WILL reject the PR if these are missing.

[V-1 Amendments] CJK Fallback
1. Scale-vs-fit overflow prevention: After scaling fallback runs, you MUST re-check line width against `int(h) - 2*padding`. If it overflows, retry at stepwise-reduced scale (e.g., 1.12 -> 1.0) OR fold the fallback scale into `fit_font_size`'s measurement loop (scale-then-fit order).
2. Baseline alignment: Do NOT share the top-left anchor `ly`. Use `f.getmetrics()` to align fallback runs: `ly_fb = ly + ascent_main - ascent_fb`.

[V-2 Amendments] Mask Band
- No amendments required. Proceed as proposed. (Note: document that `mask_vpad_vertical` effective ceiling is `mask_clip_padding`).

[V-3 Amendments] Vertical OCR
1. Drop the upright candidate: When the vertical predicate fires, EXCLUDE the upright read from the candidate set (2 VLM calls, not 3).
2. Explicit tie-break: Use strict `>` comparison starting from `ROTATE_90_CLOCKWISE` so a rotated candidate always wins ties.
3. Audit trail: Append the chosen orientation + all candidate scores to the result `warnings` / OCR sidecar.
4. Cell 16 snippet MUST include `import re` (it is not imported in cell 16).
5. Layer 2 severity: Keep as "warning" (score penalty only, no abort).

[V-4 Amendments] Manual Workflow
1. Implement Edit A (unparsed-line report) and Edit B (pre-render coverage).
2. DEFER Edit C (`|TYPE` header). Do NOT alter the ai.Text wire format in this task.

[V-5 Amendments] Provider-Flexible Translation
1. Sanitizer compatibility: The registry field MUST be named `key_env` (NOT `api_key_env`), otherwise `save_config`'s sanitizer will strip it and cause guaranteed auth failures.
2. Closure-bound engine: `translate_with_retry` does not accept an `engine` kwarg. You MUST bind the engine via closure: 
   `translate_with_retry(lambda t, rt: translate_with_provider(t, rt, engine=engine), text, region_type=region_type)`
3. LiteLLM is REJECTED. Use the native ~35-line OpenAI-compatible adapter.

RULES OF ENGAGEMENT
1. NO source code modified until GLM-5.3-Flash signs off on the Phase A/B plan (Already signed off via this document).
2. Mirror Discipline (V-1): `get_font_fb` and `_qc_render_vertical` exist in BOTH cells 11 and 12. They are byte-identical. You MUST update BOTH. A fix applied to only cell 12 will leave a stale shadow in cell 11.
3. Single-Hunk Audit: Every cell modified must carry exactly one logical change.
4. Evidence Rule: Use [FACT], [TEST RESULT], [HYPOTHESIS] in your PR descriptions.

VERIFICATION PROTOCOL (Phase D)
After GLM-5.3 implements a batch:
1. GLM-5.3-Flash will run the `m002_sim_v2.py` and `m002_flash_repro.py` equivalents to ensure no fresh-run regressions.
2. A new visual sample (S002) MUST be generated and archived in `samples/S002_.../` to prove the visual defects (residue, CJK size, OCR accuracy) are resolved.

USER DECISION
APPROVED. Qwen3.8-Max (Lead Architect) has authorized the immediate execution of TASK_003 based on the Phase B consensus.
