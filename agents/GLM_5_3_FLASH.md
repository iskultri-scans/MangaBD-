# GLM-5.3-Flash — Independent Review Log

## ROLE

Independent Reviewer / Test Engineer / Visual Analyst

---

## CURRENT PHASE

**S001 VISUAL REVIEW — ASSIGNED 2026-09-29, NOT YET STARTED (Project Owner request, relayed by GLM-5.3).**

The NO_VISUAL_EVIDENCE_AVAILABLE gap recorded in DECISION.md (findings 18 / 16) has been closed: the Project Owner's first visual evidence sample is archived at `samples/S001_color_webtoon/` (Owner ZIP upload commit `59be2ff`; extracted + verified by GLM-5.3 in commit `5457f3f`). You are requested to begin the independent visual review of these artifacts.

- **Artifacts (read-only evidence):** `original.jpg` (844×1200 color webtoon strip), `text_mask.png` (844×1200 grayscale), `inpainted.png` (844×1200 RGB), `final.jpg` (844×1200), sidecars `detections.json` / `ocr.json` / `translation.json` (6 regions each), `metadata.json` (provenance: fresh Run All success, notebook commit `9f4d82a`, second test image), plus `samples/README.md` (archive rules).
- **Suggested review scope:** (1) integrity & consistency — image dimensions, sidecar↔image agreement, mask↔detections agreement, region IDs across sidecars; (2) visual quality — text-detection coverage (misses/false positives), mask quality, inpainting artifacts, typesetting/rendering of the translated text in `final.jpg`; (3) provenance cross-check — `metadata.json` vs sidecar data. Known discrepancy to evaluate and report on: `metadata.json` says `"translation_engine": "manual"` while `translation.json` records `"translator_engine": "nllb"` on all 6 regions (metadata was written verbatim per the Owner's instruction); (4) record your verdict and findings in this file and update `agents/DECISION.md`.
- **Constraints:** artifacts are evidence — do not modify, re-generate, or move them; do not modify source code.

MANGABD-002 — Phase A COMPLETE: independent fresh-run investigation + review of GLM-5.3's proposal (see "# MANGABD-002 — PHASE A INDEPENDENT INVESTIGATION & PROPOSAL REVIEW" below).

MANGABD-001 — Independent Codebase Audit: PHASE 1 COMPLETE (historical, below).

NO IMPLEMENTATION PERFORMED. NO SOURCE CODE MODIFIED.

---

## MISSION

You are the independent reviewer for MangaBD.

Your job is to independently understand the CURRENT repository and challenge technical assumptions.

The project was originally developed with assistance from GLM-5.3 and GLM-5.3-Flash.

Later, Qwen3.8-Max modified the project.

Therefore, historical knowledge may be outdated.

The CURRENT REPOSITORY is the source of truth.

---

## IMPORTANT

You are an independent reviewer.

Do NOT automatically agree with GLM-5.3.

Do NOT automatically disagree either.

Evaluate claims using evidence.

If GLM-5.3 is correct, explain why.

If GLM-5.3 is wrong, explain why.

If evidence is insufficient, say so.

---

## REQUIRED READING

Before writing your final review:

1. Read agents/PROJECT_CONTEXT.md
2. Read agents/TASK.md
3. Inspect the actual current repository
4. Inspect the notebook/source files
5. Inspect dependencies/configuration
6. Inspect GLM_5_3.md
7. Compare GLM-5.3's claims with the actual code

---

## PHASE 1 RULE

DO NOT modify source code.

Only review, analyze and document.

Safe testing is allowed when possible.

---

## EVIDENCE FORMAT USED IN THIS REPORT

- FACT: directly verified in the current repository code (with cell:line reference where useful).
- HYPOTHESIS: technically plausible explanation, still needs verification.
- ASSUMPTION: accepted without evidence because evidence is unavailable.
- TEST RESULT: verified by executing a safe static/local test (no project files modified).
- UNKNOWN: cannot currently be determined.

Cell indices below are PHYSICAL notebook cell indices 0–26 (top to bottom). Banner names ("Cell 1", "Cell 2", …) are the labels printed inside the cells. Physical index ≠ banner number.

---

# REVIEW METHOD (INDEPENDENT)

[FACT] This review was performed WITHOUT executing the notebook (no Colab/GPU in this review environment). Method:

1. Parsed the notebook JSON (`MangaBD_V12_ipynb_txt.ipynb (3).txt`, 803,682 bytes) directly.
2. Extracted all 27 cell sources; AST-parsed every cell (27/27 parse OK — no syntax errors anywhere).
3. Built a definition/redefinition map and a module-level call map from the AST.
4. Ran a secret-pattern scan over the full notebook JSON.
5. Forensics on stored outputs (which cells have outputs, types, timestamps, error outputs, image outputs).
6. Independently traced the pipeline end-to-end from the code.
7. Only THEN read agents/GLM_5_3.md and checked ~45 of its specific claims one by one against extracted cell sources (line-referenced).
8. Ran one local pandas simulation (TEST RESULT T-6) to test the P-7 mechanism. No project file was touched.

[FACT] Files changed by this review: only `agents/GLM_5_3_FLASH.md` (this file). Source notebook and other agent docs untouched.

---

# INDEPENDENT ANALYSIS

## 1. What the Project Actually Does

[FACT] The repository contains exactly one source artifact: `MangaBD_V12_ipynb_txt.ipynb (3).txt` — a Google Colab notebook, nbformat 4.0, **27 code cells, zero markdown cells**, plus 5 agent/process documents under `agents/`. No `.py` module tree, no `requirements.txt`, no CI, no tests outside the notebook's per-cell self-tests. Verified by listing the working tree and parsing the JSON.

[FACT] The notebook implements a Bengali manga/manhwa translation pipeline for Google Colab (GPU T4 profile): upload → detect → OCR → translate → inpaint → render → QA → export, with a session/checkpoint system persisted to `/content/mangabd` (local fallback) or Google Drive (`/content/drive/MyDrive/MangaBD_V12`).

[FACT] The codebase has two clearly distinguishable strata:

1. **Structured V12 core** (physical 0–10 and 15–18; banners "Cell 1" … "Cell 14"): uniform banner format, config-driven design, per-cell self-tests that `raise RuntimeError` on failure, checkpoint-aware page manager, lazy-loading model manager.
2. **Patch/hotfix layer** (physical 11–14 "QUALITY CORE"/"RESIDUAL KILLER", and 19–26: NLLB hotfix, one-liner execution cells, copy/paste translation, stage-sync fix, mobile-download + long-strip slicer, Control Studio v4 UI): compressed style, relies on the core's kernel globals, repeatedly redefines and overrides earlier definitions.

[FACT] All 27 cells parse successfully with Python `ast` (TEST RESULT T-1), so the ordering hazards documented below are execution-order issues, not syntax issues.

## 2. Actual Architecture

[FACT] Repository layout (verified):

```
MangaBD-/
├── MangaBD_V12_ipynb_txt.ipynb (3).txt   # the entire application (27 code cells)
└── agents/
    ├── PROJECT_CONTEXT.md
    ├── TASK.md
    ├── GLM_5_3.md
    ├── GLM_5_3_FLASH.md   (this file)
    └── DECISION.md
```

[FACT] Notebook metadata: `accelerator: GPU`, `colab.gpuType: T4`, kernel `python3`, nbformat 4.0.

[FACT] Stored-output forensics (TEST RESULT T-3): outputs exist for physical cells **0, 1, 2, 3, 5, 6 only** (banner Cells 1, 2, 2.1, 3, 5, 6). All outputs are `stream` type; **no error outputs, no image outputs anywhere in the notebook**. `execution_count` is None for every cell (counts were cleared). The outputs prove a real run on **2026-08-31 12:18** with Python 3.13.15, Tesla T4, 14.56 GB GPU, libraqm True, base dir `/content/mangabd` (Drive NOT mounted), `hf_token: not set`, session `20260831_121807_f0c73a`.

[FACT] Physical cell map (independently rebuilt from banners; matches the notebook exactly):

| Index | Banner | Component |
|---|---|---|
| 0 | Cell 1 | Environment doctor, package install, libraqm check |
| 1 | Cell 2 | CONFIG, secrets, paths, logger |
| 2 | Cell 2.1 Hotfix | Adds missing `paths` keys (session/pages/logs/export/cache) |
| 3 | Cell 3 | Session storage & checkpoint manager (manifest, artifacts, translation_df) |
| 4 | Cell 4 | zyddnys repo clone+patch, fonts, libraqm render test |
| 5 | Cell 5 | ModelManager + GPU memory controller + QwenVLWrapper |
| 6 | Cell 6 | Detection service (RT-DETR + CTD) |
| 7 | Cell 7 | OCR service (Qwen VL) |
| 8 | Cell 8 | Translation service (manual/gemini/chatgpt/nllb) |
| 9 | Cell 9 | Inpainting service (LaMa + OpenCV fallback) |
| 10 | Cell 10 | Rendering service (Pillow + libraqm Bengali) |
| 11 | QUALITY CORE FINAL | config overrides, NotoSansJP fallback, box-snap v1, mask filter, kill_residual v1, vertical renderer patch, pipeline wrap |
| 12 | QUALITY CORE container-aware | re-snaps boxes (simpler), restore_boxes, vertical renderer patch (2nd), pipeline wrap (2nd) |
| 13 | RESIDUAL KILLER | kill_residual v1 (again) + full quality pipeline wrap |
| 14 | kill_residual v3 | pixel-level box-only residual eraser; **executes the whole pipeline at cell-run time** |
| 15 | Cell 11 | Upload/input & pipeline orchestrator (run_* batch functions) |
| 16 | Cell 12 | Quality inspector & manual review |
| 17 | Cell 13 | Export, preview & download |
| 18 | Cell 14 | Dashboard, session log & final review |
| 19 | Hotfix | `apply_translations_from_ai_file` rescue + NLLB `src_lang` fix |
| 20 | one-liner | `applied = apply_translations_from_ai_file()` at cell-run time |
| 21 | one-liner | prints translation_df preview |
| 22 | Copy/Paste Manual Translation | `apply_translations_from_text` + local parser |
| 23 | FIX | `sync_translate_stage` + plain robust `run_inpaint_render_all`; **calls `sync_translate_stage()` at cell-run time** |
| 24 | PATCH | mobile single-download (base64) + long-strip slicer wrapping RT-DETR/CTD |
| 25 | CONTROL STUDIO v4 | ipywidgets mobile UI, builds UI at cell-run time |
| 26 | one-liner | `render_all_pages(force=True)` at cell-run time |

[FACT] Configuration is a single in-memory dict `MANGABD_CONFIG` (physical 1), progressively extended by `setdefault` in later cells and overwritten by the patch layer. Secrets live in `MANGABD_SECRETS` (env vars / Colab userdata only); `save_config()` runs every key through a sanitizer that drops keys containing `api_key`, `token`, `secret`, or `password` (cell 1, lines 534–548) before writing `config_v12.json`.

[FACT] State layer: `MANGABD_MANIFEST` (per-session `manifest.json`, atomic writes via `.tmp` + `os.replace`, cell 3 lines 207–214), per-page artifact directories (`original.jpg`, `detections.json`, `text_mask.png`, `ocr.json`, `translation.json`, `inpainted.png`, `final.jpg`, `qa.json`, `preview.jpg`), and a `translation_df` pandas DataFrame persisted as CSV.

[FACT] There is no module isolation: all definitions flow into one kernel namespace, and later cells depend on names imported by earlier cells. Verified example: cell 10 uses `Path` (lines 199, 1072) but imports no `pathlib` — it works only because cell 1 ran `from pathlib import Path` (line 20) in the same kernel.

## 3. Actual Processing Pipeline

[FACT] Traced end-to-end from code (happy path):

1. **Upload** (cell 15): `upload_images()` → Colab upload → PIL decode with `ImageOps.exif_transpose` (line 134), cv2 `imdecode` fallback (line 153) → min-size check 50×50 (config lines 66–67) → `register_image_array()` → `init_page()` stores `original.jpg`, marks stage `upload`.
2. **Detection** (cell 6): `detect_page()` → `rtdetr_detect()` (RT-DETR-v2, `rtdetr_threshold` 0.30 line 73; classes 0=bubble, 1=text_bubble, 2=text_free, lines 459–463). If no candidates → CTD fallback. If candidates exist and `use_ctd_pixel_mask=True` (default, line 77) and no CTD mask yet → **CTD runs anyway** to produce a pixel mask (lines 1095–1120) → dedupe (IoU 0.50, line 76; `deduplicate_boxes` lines 147–196) → parent-bubble assignment (containment ≥ 0.55, line 81; smallest parent wins, lines 666–674) → heuristic classification (white-ratio 0.70 bubble / 0.50 thought, border variance, narrator top/bottom/width/aspect ratios 0.20/0.80/0.40/2.5, sfx area/white ratio 0.02/0.30 — config lines 84–92) → reading-order sort (`y // 50` bands, lines 215/222) → mask build: CTD mask preferred, threshold 60 default (line 78), close → connected-component clean (lines 700–704) → adaptive dilate radius 6 default (line 80; lines 716–742) → clip to regions with padding=10 (lines 815–819) → artifacts saved, stage `detect`.
3. **OCR** (cells 5+7): per region `ocr_region()` → context-padded crop (white pad for bubbles; `BORDER_REPLICATE` for sfx/overlay, lines 277–296) → preprocessing (upscale if h<40, bilateral filter, CLAHE, pad — lines 234–267) → `QwenVLWrapper.recognize()` (deterministic: `do_sample=False`, `max_new_tokens=512` read from config — cell 5 lines 405–406) → heuristic confidence (base **0.45**, capped **0.95** — cell 5 lines 293, 314, used at 424) → status ok / low_confidence (<0.50) / non_english / failed (cell 7 lines 183–192) → rows upserted into `translation_df`.
4. **Translation** (cell 8, redefined pieces in 19/22): default engine `manual` (cell 1 line 270) exports `ai_text_export.txt` for human translation and re-imports it. Auto engines: Gemini (`gemini-2.5-flash`, line 77), ChatGPT (`gpt-4o-mini`, temperature 0.3, max 512 tokens — lines 78, 513–514), NLLB (`facebook/nllb-200-distilled-600M`, cell 1 line 290; target `ben_Beng` line 101; forced-BOS fallback id **100362** line 565; `num_beams=4` line 102). Region-type-aware prompts, SFX glossary exact-match shortcut (lines 320–352), Bengali validation (`validate_bengali` line 143 writes real bools into `bengali_valid`, lines 1076/1304).
5. **Inpainting** (cell 9): loads cached `text_mask.png` (fallback: bbox mask, or re-detect) → mask prepared (close/clean) → **artifact masks are NOT re-dilated** because `redilate_artifact_mask` defaults to False (line 73; enforced at line 302) → LaMa Large primary (`unload_all(exclude=["lama"])` line 372; `lama_size` 1024 line 69; call at 385–394) → OpenCV `INPAINT_TELEA` fallback (line 340) → saves `inpainted.png`.
6. **Rendering** (cell 10 + monkey-patches from 11/12): `render_page()` → PIL canvas from inpainted image → per row with renderable Bengali: background-aware color (config line 67), per-type stroke, binary-search font fit bounded 8–48 px (`font_size_max` 48 line 61; self-test asserts `8 <= size <= 48` line 1128), grapheme-safe wrapping via `regex \X` with character-split fallback (lines 96–112) → centered draw; rotated path for tilted regions; **vertical-note renderer**: rows with `w < 90 and h > 2w` render on a transposed canvas and rotate by `vertical_rotate=-90`, with a CJK fallback font `NotoSansJP.ttf` downloaded at cell-run time (cell 11 lines 17–27) → saves `final.jpg`.
7. **QA** (cell 16): OCR/translation/render inspections; severity weights `critical: 20, warning: 7, info: 1` (lines 73–77); thresholds 0.65 / 0.35 (lines 66–67); page score /100; optional Qwen-based `visual_qa_page` exists (line 1352, uses `qwen.recognize` line 1426) but `visual_qa` defaults to **False** (line 69).
8. **Export** (cell 17): final images JPEG (`jpeg_quality` 92, line 70), translation CSV, ai.Text, quality report, manifest, config, session ZIP (`create_session_zip` line 457), before/after previews.

[FACT] Orchestrator (cell 15): `run_detection_ocr_all` (598), `run_translation_all` (615), `run_inpaint_all` (634, `require_translation=False` default), `run_render_all` (656, `require_translation=True` default), `run_inpaint_render_all` (678, `require_translation=True` default), `run_full_pipeline` (694 — pauses for manual translation, returns `"awaiting_manual_translation"`). All are resume-aware (skip stages marked done unless `force=True`).

[FACT] The effective pipeline depends on which definition was executed last. Verified definition counts (TEST RESULT T-4):

| Name | Defined in cells | Last def (sequential) |
|---|---|---|
| `run_inpaint_render_all` | 11, 12, 13, 15, 23 | **23** (plain inpaint+render with sync) |
| `kill_residual` | 11, 13, 14 | **14** (v3, pixel-level) |
| `render_bengali_text` | 10, 11, 12 | **12** (vertical-note wrapper) |
| `apply_container_types` | 11, 12 | **12** (simpler, weaker-guarded) |
| `restore_boxes` | 11, 12 | **12** |
| `translate_with_nllb` | 8, 19 | 19 |
| `rtdetr_detect` / `ctd_detect_boxes_and_mask` | 6, 24 | 24 (slicer wrappers, guarded by `_MBD_SLICED`) |

[FACT] Module-level side-effect calls exist in patch cells (TEST RESULT T-5): cell 14 calls `run_inpaint_render_all(force=True)` (line 40); cell 23 calls `sync_translate_stage()` (line 89); cell 20 calls `apply_translations_from_ai_file()`; cell 26 calls `render_all_pages(force=True)`; cells 11/12 download a font at cell-run time; cell 25 builds and displays the widget UI at cell-run time.

[FACT] The Control Studio UI (cell 25) duplicates orchestration in button callbacks, and its render button calls `run_inpaint_all(...)` then `run_render_all(...)` **directly** (lines 363–365) — bypassing every `run_inpaint_render_all` variant, including the quality-core wrap.

## 4. Current AI Models

[FACT] Model inventory (every row verified at the cited lines):

| Model | Where | Purpose | Verified evidence |
|---|---|---|---|
| `ogkalu/comic-text-and-bubble-detector` (RT-DETR-v2) | cell 1 line 232; cell 5 lines 582–598 | Primary detection (3 classes) | `RTDetrV2ForObjectDetection.from_pretrained`; cache `models/rt_detr_bubble` (cell 5 line 93); **no `torch_dtype` passed → loads float32** |
| ComicTextDetector (CTD, zyddnys) | cell 4 clone; cell 5 lines 85–90 | Fallback detector + pixel mask | weight `comictextdetector.pt` from zyddnys release **beta-0.3** (lines 87–90) |
| LaMa Large (zyddnys `inpainting_lama_mpe`) | cell 5 lines 706–710; cell 9 | Text removal | `class MangaBDLaMa(LamaLargeInpainter)`; `lama_size` 1024; unloads other models first |
| `Qwen/Qwen2.5-VL-3B-Instruct` | cell 1 line 248; cell 5 lines 789–801 | OCR | fp16 **when CUDA** — cell 1 lines 177–178 set `device=cuda` + `torch_dtype=float16`, cell 5 lines 77–80 gate on it; weights cached LOCAL `/root/.cache/huggingface/hub` (line 98) to avoid Drive I/O errors; processor cached to Drive (line 801); deterministic greedy |
| `facebook/nllb-200-distilled-600M` | cell 1 line 290; cell 8 lines 98, 587 | Offline translation | `ben_Beng` forced BOS with fallback id 100362; beams 4; cell 19 rewrites for newer `transformers` (`tokenizer.src_lang = ...`, line 116) |
| Gemini `gemini-2.5-flash` (API) | cell 8 line 77 | Cloud translation | requires `gemini_api_key`; default engine is `manual`, not gemini |
| GPT `gpt-4o-mini` (API) | cell 8 lines 78, 513–514 | Cloud translation | temperature 0.3, max 512 tokens |
| OvisOCR2 | cell 5 lines 842–848 | **Placeholder only** | `raise NotImplementedError` — not implemented |

[FACT] OCR "confidence" is a heuristic (base 0.45 + bonuses, cap 0.95 — cell 5 lines 293–314), NOT model token probability. Downstream QA thresholds therefore measure text-shape plausibility, not recognition certainty.

[HYPOTHESIS] RT-DETR float32 looks intentional (accuracy vs VRAM trade), but intent cannot be proven from code; the float32 fact itself is verified (no dtype argument in the `from_pretrained` call).

## 5. Important Files / Cells

[FACT] The only source file is the notebook. The most consequential cells for future work:

- **Physical 3** — storage/checkpoint core (`atomic_write_json`, `init_page`, `mark_stage_done`, `reset_page`, artifact IO, `translation_df` persistence). Nearly everything depends on it.
- **Physical 5** — `ModelManager` (lazy `ensure_*`, unload, GPU summary), `_run_async` (nest_asyncio), `QwenVLWrapper`, confidence helper.
- **Physical 6** — detection + classification + mask construction; the most algorithm-dense cell.
- **Physical 10** — renderer: font fit, grapheme wrapping, colors, rotated text, `render_all_pages` (line 982 — this is what cell 26 calls; the call is name-valid, contrary to what one might fear).
- **Physical 11–14** — quality patch layer: box-snap, mask filter, residual killers (v1 ×2, v3), `restore_boxes`, vertical-note render patch ×2.
- **Physical 15** — orchestrator; defines the `run_*` API.
- **Physical 19–26** — hotfix/UI layer including Control Studio and the download/slicer monkey-patches.

[FACT] Filename oddity: the source of truth is a `.txt` copy of an `.ipynb` named `...ipynb (3).txt` (browser duplicate suffix), indicating manual snapshot management rather than a git-native workflow.

[FACT] Git history provides **no attribution evidence** for the notebook: it entered history in a single commit (`27d8643`, "Add files via upload"); every other commit touches only `agents/` docs. There is no diff history of the notebook itself.

## 6. Strengths

[FACT]
1. **Solid checkpoint architecture** for a notebook: atomic JSON writes (tmp + `os.replace`, cell 3 lines 207–214), per-page artifact dirs, stage flags with resume, `reset_page(from_stage=...)`, session pointer, `events.jsonl`.
2. **Defensive secrets handling**: secrets only from env/Colab-userdata; sanitizer drops `api_key|token|secret|password` keys before config save (cell 1 lines 534–548); stored output shows `hf_token: not set`. My independent regex scan over the whole notebook JSON found no secret patterns (TEST RESULT T-2).
3. **Per-cell self-tests with hard failure** (`raise RuntimeError`) give fast environment diagnostics; stored outputs show the tested cells printing `SUCCESS` on the reference machine.
4. **Pragmatic manual-translation workflow** (ai.Text export format, file-or-paste import, "rescue" parsing for left-side Bengali — cell 19 lines 19–73): the most production-realistic human loop.
5. **Renderer quality features**: grapheme-safe Bengali wrapping (`regex \X`), background-aware colors, binary-search font fitting without truncation, per-type stroke, rotated and vertical-note paths.
6. **Memory-aware model lifecycle**: lazy `ensure_*` loads, `unload_all` before heavy stages, local HF cache for Qwen weights specifically to avoid Drive I/O errors (cell 5 line 96–98 comment).
7. **Verification-minded patches**: kill_residual v3 (cell 14) guards `crop.size == 0` (line 17) and skips non-solid boxes via `uniform_frac > 0.8` (line 23) — safer than v1; slicer dedupes with overlap to avoid losing boundary text; monkey-patches carry guard flags (`_QC_RENDER_PATCHED`, `_QC_FINAL_RENDER_PATCHED`, `_MBD_SLICED`, `__mbd_patched`) that prevent double-wrapping.

## 7. Weaknesses

[FACT]
1. **Order-dependent execution**: the notebook cannot be run fresh top-to-bottom (see Bug F-0/P-1 below). Effective behavior depends on which definition of `run_inpaint_render_all` / `kill_residual` / `apply_container_types` was executed last.
2. **Five definitions of one pipeline function**, three of one residual-killer, two render patches, two box-snaps, two NLLB translators — no single source of truth; the "winner" is implicit execution order.
3. **Quality-core orphaning in sequential runs**: the final sequential `run_inpaint_render_all` is cell 23's plain version; box-snap / mask-filter / residual-kill / box-restore then only run if the owner re-executes the quality cells after cell 23 — and the UI button bypasses all of it (cell 25 lines 363–365).
4. **Global monkey-patching** of `colab_files.download`, `rtdetr_detect`, `ctd_detect_boxes_and_mask`, `render_bengali_text` — invisible at call sites; partially mitigated by guard flags.
5. **Single 800 KB notebook as the only artifact**; no module decomposition, no versioned requirements (versions are runtime-resolved), no external tests.
6. **Colab-only coupling** (`google.colab.*`, `/content` paths) with no local/Jupyter fallback.
7. **Heuristic OCR confidence** presented as `confidence` — downstream thresholds inherit its semantics.
8. **Duplicated logic**: three Bengali validators (cell 8 `validate_bengali`, cell 16 `qa_validate_bengali`, cell 22 `_validate_bengali_local`), three special-marker checkers (cells 8/10/16), three ai.Text-format implementations (cell 8 `parse_ai_text`/`export_ai_text`, cell 22 `_parse_ai_text_local`, cell 25 `build_ai_text_content` — note: the third is a builder, not a parser), two box-snaps, two mask cleaners. Drift is already visible (marker sets differ — see F-4).
9. **Magic numbers** everywhere (0.30/0.55/0.60/0.65/0.85, radii 5/6/13, slices 1400/240, aspect 2.0/2.5, w<90, etc.) — some in config, many hardcoded in patch cells.

## 8. Potential Bugs

### F-0 (Critical) — fresh "Run All" crashes (confirms GLM-5.3's P-1)

[FACT] Cell 14 line 40 executes `run_inpaint_render_all(force=True)` at module level (bare call, not wrapped in try/except). In a fresh sequential run, the name at that moment is bound to **cell 13's** quality-core wrap (last definition before 14), which calls `run_inpaint_all` — a name defined only in cell 15 (line 634). Result: `NameError` on a fresh top-to-bottom run. Even if the name resolved, the call would launch the entire inpaint+render pipeline as a side effect of *executing a patch cell*.

[TEST RESULT] (static execution-order analysis, no notebook execution): cell 14's module-level call verified by AST; `run_inpaint_all` defined only in cell 15 per the definition map. The mechanism is unambiguous from code; runtime confirmation in Colab is still pending an actual run.

### F-1 (High) — the *surviving* box-snap variant lost cell 11's safety guards (extends GLM-5.3's P-5)

[FACT] Cell 11's `_snap_white_box` (lines 46–61) probes 5 candidate points, rejects components touching the image border (within 2 px), and caps component area at 4× the region area. Cell 12's `_snap_white_box` (lines 30–42), which **wins** in execution order (last definition of `apply_container_types`/`restore_boxes` is cell 12's), checks ONLY the center point, has NO border exclusion, and NO area cap — any white connected component with fill > 0.85 and dims ≥ 30 px qualifies, including page-scale components. `restore_boxes` (cell 12 lines 71–86) then paints a synthetic white rectangle with a black border over everything classified `narrator`. A misfire can therefore over-paint a much larger artwork area than GLM-5.3's P-5 described (its description matches the cell 11 variant).

### F-2 (Medium) — cell 23 executes pipeline logic at import time (new finding, not in GLM-5.3's P-list)

[FACT] Cell 23 line 89 calls `sync_translate_stage()` at module level. In a session where `translation_df` was loaded from disk (cell 3 does this), re-running cell 23 re-marks `translate` stages in the manifest as an import side effect. It is data-driven and comparatively benign, but it belongs to the same "patch cells do pipeline work at cell-run time" family as F-0.

### F-3 (Low/Medium) — one-liner cells 20/21/26 are import-time pipeline calls

[FACT] Cell 20 `applied = apply_translations_from_ai_file()` (executes a file-glob import at cell-run time; on a fresh session with no `/content/ai_text_export*.txt` it prints an error and does not crash); cell 21 prints the DataFrame; cell 26 `render_all_pages(force=True)` — the name IS defined (cell 10 line 982), so this is not a NameError, but on a warm session it re-renders every inpainted page as a side effect of "running a cell". These were not enumerated in GLM-5.3's P-list.

### F-4 (Low) — marker-set drift has a twist: cell 10's "nan" entry is dead code in sequential flow

[FACT] Marker sets differ: cell 8's `is_special_marker` has 6 markers (lines 198–205, no `"nan"`); cells 10 and 16 define local sets WITH `"nan"` (cell 10 lines 137–145, cell 16 lines 220–228). Nuance GLM-5.3 did not mention: cell 10 line 156–159 **prefers the global** `is_special_marker` when it exists — which it always does after cell 8 — so the effective render-skip set is cell 8's (no `"nan"`). The local cell-10 set with `"nan"` is dead code. The drift risk GLM-5.3 warned about is real, but the practical direction is inverted: a literal `"nan"` string reaching the renderer would be treated as renderable text by the effective set.

### F-5 (Low) — `kill_residual` v1 variants can crash on out-of-bounds boxes; v3 fixed this

[FACT] Cells 11 and 13's `kill_residual` compute `m = mask[y:y+h, x:x+w]` then `m.max()` (cell 11 line 111, cell 13 line 19) with no empty-crop guard — a box fully outside the mask bounds raises `ValueError: zero-size array to reduction`. Cell 14's v3 guards `crop.size == 0` (line 17–18). Low likelihood (requires coordinates beyond image bounds), but the inconsistency across three versions of the "same" function is exactly the redefinition jungle's cost.

### F-6 (Medium) — `recover_coordinates()` reverts more than box-snap (extends GLM-5.3's P-3)

[FACT] Cell 11 line 203 calls `recover_coordinates()` at module level (the call is an argument of a `print()` f-string — easy to miss in an AST top-level scan). Beyond GLM-5.3's P-3 (reverting snapped coordinates on re-execution), the function also resets `region_type` from `detections.json` (line 40) — undoing the `narrator` reclassification — and overwrites **any manual coordinate/region-type corrections** the owner made through the dashboard/QA workflow. Also, a precision: `apply_container_types` is NOT called at module level in cells 11/12, so on a first fresh pass nothing has been snapped yet; the revert only bites when cell 11 (or the quality wrap) is re-executed after a snap.

### Confirmed carry-overs from code inspection (with independent line evidence)

- [FACT] `_has_valid_trans` treats ANY text starting with `[` as invalid (cell 11 lines 84–86) — legitimate Bengali starting with `[` would be skipped by residual-kill/mask-filter (= GLM-5.3's P-8).
- [FACT] `mask_only_translated` permanently ANDs the stored mask down to translated regions (cell 11 line 96) and re-running it compounds the loss (= GLM-5.3's reliability risk 2).
- [FACT] `kill_residual`/`restore_boxes`/`mask_only_translated` mutate `inpainted`/`mask` artifacts **in place on disk** with no backup and no idempotency guard (cell 11 lines 96/117/130; cell 13 line 31) (= P-6).
- [TEST RESULT] `bengali_valid.astype(bool)` inflation (= P-7): local pandas 2.2.3 simulation (see T-6): a CSV round-trip where one row is empty yields `[True, False, nan]` → `astype(bool)` makes the EMPTY row count as valid Bengali (rows [1, 3] selected where only row 1 is real). The astype(bool) calls exist at cell 15 line 849, cell 23 line 42, cell 25 lines 122/219. A worse variant I hypothesized (string `"False"` becoming truthy for a whole object column) was **refuted** by the same test: `read_csv` parses `"True"/"False"` strings back to real bools even in mixed columns. GLM-5.3's calibration (Medium, NaN→True only) is exactly right.
- [FACT] OCR config keys `temperature`/`top_p` exist (cell 1 lines 253–254, both 1.0) but `generate()` only receives `max_new_tokens` and `do_sample` (cell 5 lines 405–406) — dead config (= P-9).
- [FACT] Cell 24's "proof" block (lines 133–147) requires an existing `02.jpg`, builds a 5× stacked fake strip, and runs whole-vs-sliced detection at cell-run time inside try/except (= P-10).
- [FACT] Cell 12's `_qc_render_vertical` has dead code `size, lines = 8, [text]` immediately overwritten (lines 116→120), and both vertical wrappers hardcode black `(0,0,0)` text color (cell 11 line 183; cell 12 line 148) (= P-11).
- [FACT] `deduplicate_boxes` suppresses by IoU only (cell 6 lines 147–196, threshold 0.50); a text box inside a bubble with IoU < 0.5 survives as a duplicate region → double OCR is code-plausible (= P-12; actual frequency unverified — runtime behavior is HYPOTHESIS until observed).

## 9. Performance Problems

[FACT] (each mechanism verified in code)
1. **Double detection per page**: when RT-DETR succeeds, CTD still runs by default to build the pixel mask (cell 6 lines 1095–1120; `use_ctd_pixel_mask` default True line 77) — two detection models per fresh detect.
2. **`clear_gpu_cache()` inside every OCR call**: `gc.collect()` + `torch.cuda.empty_cache()` per region (cell 5: `recognize` at 339 calls `clear_gpu_cache` at 343).
3. **Per-region OCR round-trips**: one `model.generate()` per crop, no batching — dominant wall-clock cost on long chapters.
4. **Model ping-pong across stages**: inpaint unloads everything then loads LaMa (cell 9 line 372); re-entering OCR unloads LaMa for Qwen; repeated cycles on stage re-runs (weights are cached, load time still paid).
5. **`save_manifest()` / CSV rewrite frequency**: manifest and `translation_df` rewritten on nearly every mutation — O(pages×regions) I/O, painful on Drive.
6. **Long-strip slicer** (cell 24): 1400 px slices with 240 px overlap multiply RT-DETR+CTD invocations on tall webtoons (correctness-motivated; largest throughput cost there).
7. **`apply_container_types`/`recover_coordinates`/`restore_boxes`** each `iterrows()` the whole DataFrame and re-save the CSV per call.

## 10. Reliability Risks

[FACT]
1. **Fresh-run failure** (F-0) — the notebook cannot bootstrap itself top-to-bottom.
2. **Artifact/checkpoint divergence**: shrunken masks + inpainted-image mutation persist on disk; the checkpoint still says `detect` done, so a later re-inpaint reuses the damaged mask (mask never rebuilt automatically).
3. **In-place artifact mutation** means a bad `kill_residual`/`restore_boxes` run is undoable only by full re-inpaint.
4. **Runtime dependency pinning absent**: `transformers` API drift already broke NLLB once (cell 19 exists to fix it); the same failure class applies to RTDetrV2 / Qwen processor APIs.
5. **Drive-as-storage fragility**: the code itself documents Drive I/O errors (Qwen moved to local cache); sessions/manifests/models on Drive remain exposed to mid-write unmounts (atomic JSON prevents corruption, not unmounts).
6. **Silent skip paths**: render skips non-Bengali/marker/empty rows with only a WARN log (cell 10 lines 878–880); an English passthrough yields a page that looks finished.
7. **`reset_checkpoint`** (cell 25 lines 230–245) empties `translation_df` and the manifest **in memory** and saves, but deletes **no per-page artifacts on disk** — orphaned dirs leak storage; same-named re-uploads get new suffixed ids rather than colliding.
8. **Widget-state vs kernel-state**: Control Studio callbacks capture function references at click time via `globals()` lookups; re-running core cells after opening the UI can silently rebind or drop functions.

[FACT] Corroborating runtime evidence: the stored cell-3 output contains a pandas `FutureWarning` about DataFrame concatenation with empty/all-NA entries (from `translation_df = pd.concat(...)` at cell 3 line ~963) — direct proof that the empty-row concat path is exercised in real sessions and that dtype drift around `translation_df` is a live concern, not just a theoretical one.

## 11. Qwen3.8-Max Modifications

[FACT] Git provides no attribution: the notebook arrived in a single upload commit; all later commits only touch `agents/` docs. Which model authored which cell cannot be determined from the repository.

[HYPOTHESIS] Based on internal evidence only (style shift, compressed patch formatting, banner comments like "Delete all old FIX/QC cells" / "replaces all FIX patches", reliance on core globals, mutual overrides), the patch/hotfix layer (physical 11–14, 19–26) is the post-original modification phase, while the structured core (0–10, 15–18) matches the original GLM-era architecture. This is a style-based inference, not proof.

[FACT] Behavioral deltas the patch layer introduces relative to the clean core (regardless of authorship — all verified in code):
1. Detection overrides: `ctd_mask_threshold` 60→55, `mask_base_dilate_radius` 6→5, `redilate_artifact_mask` → False (cell 11 lines 11–14 vs cell 6 lines 78/80, cell 9 line 73).
2. Fallback font `NotoSansJP.ttf` + `vertical_rotate=-90` (cell 11 lines 17–27), downloaded at cell-run time.
3. Vertical-note special-case rendering (`w<90 and h>2w`) with CJK fallback, patched twice (cells 11/12).
4. `translate_with_nllb` rewritten for newer `transformers` (`tokenizer.src_lang` attribute instead of call kwarg — cell 19 line 116).
5. Manual-translation "rescue" (left-side Bengali accepted — cell 19 lines 62–69).
6. `sync_translate_stage` (marks `translate` from data — cell 23 lines 28–67; called at cell-run time line 89).
7. `run_inpaint_render_all` de-hardened: cell 23 default `require_translation=False` vs cell 15's `True` (lines 71 vs 678).
8. Long-strip slicer wrapping RT-DETR+CTD (`SLICE_MODE=True` default, `SLICE_H=1400`, `OVERLAP=240`, trigger `h > w×2.0 and h > SLICE_H+OVERLAP` — cell 24 lines 55–58, 95; guarded by `_MBD_SLICED`).
9. `colab_files.download` globally replaced by base64 data-URI tap-links for files ≤ 25 MB (cell 24 lines 28–46, guarded by `__mbd_patched`).
10. Control Studio v4 widget UI with checkpoint reset (cell 25).

[UNKNOWN] Whether `SLICE_MODE=True` has been validated against non-strip pages; whether `restore_boxes`' synthetic boxes are a desired style; whether the "(3)" file is the owner's newest snapshot.

---

# REVIEW OF GLM-5.3

I independently analyzed the codebase FIRST (Sections 1–11 above), then checked GLM-5.3's report claim-by-claim. Result: **the audit is substantively accurate**. Of ~45 specific claims I could test against the code, ~41 confirmed exactly; 4 required correction or precision (listed after the table). I found no fabricated claims and no claim that misrepresents the code's intent.

## Verdict summary (every claim checked against extracted cell sources)

| # | GLM-5.3 claim | Verdict | My evidence |
|---|---|---|---|
| 1 | Repo = 1 notebook artifact, 27 code cells, 0 markdown, no .py/requirements/CI/tests | CONFIRMED | JSON parse: 27 code cells, 0 markdown; working-tree listing |
| 2 | Two strata: structured core (0–10, 15–18) + patch layer (11–14, 19–26) | CONFIRMED | Banner/AST analysis; consistent with my §2 map |
| 3 | Stored outputs: 2026-08-31 12:18, Python 3.13.15, T4, 14.56 GB, `/content/mangabd`, hf_token unset, exec counts cleared | CONFIRMED | Output forensics (T-3) |
| 4 | "Stored outputs prove cells 1–7 passed" | **INCORRECT as stated** | Outputs exist only for banner Cells 1, 2, 2.1, 3, 5, 6. Banner Cell 4 has NO stored output; banner Cell 7 (OCR) has none. See D-1 |
| 5 | P-1: cell 14 runs pipeline at module level → NameError on fresh Run-All | CONFIRMED | Cell 14 line 40 bare call; `run_inpaint_all` only in cell 15 (line 634); static order analysis |
| 6 | P-2: 5 definitions of `run_inpaint_render_all` (11,12,13,15,23); sequential final = cell 23 plain; quality wrap orphaned; vertical render patch survives | CONFIRMED | Definition map (T-4); `render_bengali_text` defs [10,11,12], nothing later redefines it |
| 7 | P-2 sub-claim: "in the owner's warm-kernel workflow the wrap wins" | **INSUFFICIENT_EVIDENCE** | Owner's actual execution order is undocumented; GLM-5.3 itself lists this as UNKNOWN #3. Should stay HYPOTHESIS. See D-2 |
| 8 | P-3: `recover_coordinates()` at cell-run time reverts box-snap | CONFIRMED (and extended) | Cell 11 line 203 (inside `print()` f-string — genuinely easy to miss); also resets `region_type` and manual edits (my F-6) |
| 9 | P-4: cell 10 uses `Path` without importing | CONFIRMED | Cell 10 imports lack pathlib; `Path(` at lines 199, 1072; provided by cell 1 line 20 |
| 10 | P-5: white-box snap misclassification + destructive synthetic restore | CONFIRMED but **UNDERSTATED** | The surviving cell 12 variant removed three of cell 11's guards (my F-1) — misfire blast radius is larger than described |
| 11 | P-6: in-place artifact mutation, no idempotency | CONFIRMED | Cell 11 lines 96/117/130; cell 13 line 31 |
| 12 | P-7: `bengali_valid.astype(bool)` NaN→True inflation | CONFIRMED | astype calls at 15:849, 23:42, 25:122/219 + my pandas TEST RESULT T-6 reproduces the inflation exactly |
| 13 | P-8: `_has_valid_trans` rejects any "[…" text | CONFIRMED | Cell 11 lines 84–86 |
| 14 | P-9: OCR temperature/top_p dead config | CONFIRMED | Keys exist (1:253–254); `generate()` gets only max_new_tokens/do_sample (5:405–406) |
| 15 | P-10: cell 24 proof block heavy side effect | CONFIRMED | Cell 24 lines 133–147 (02.jpg, 5× vstack, whole-vs-sliced detection) |
| 16 | P-11: cell 12 dead `size, lines = 8, [text]`; vertical renders hardcode black | CONFIRMED | 12:116→120; color `(0,0,0)` at 11:183 and 12:148 |
| 17 | P-12: IoU-only dedupe leaves nested duplicates | CONFIRMED (code-logical) | `deduplicate_boxes` 6:147–196, threshold 0.50; runtime frequency HYPOTHESIS |
| 18 | Model inventory: RT-DETR-v2 ogkalu / CTD beta-0.3 / LaMaLargeInpainter subclass / Qwen2.5-VL-3B fp16-on-CUDA with local cache + Drive processor cache / NLLB 600M ben_Beng fallback 100362 beams 4 / gemini-2.5-flash / gpt-4o-mini 0.3-512 / Ovis NotImplementedError | CONFIRMED (every row) | 1:232, 1:290, 1:248, 5:87–98, 5:582–598, 5:706–710, 5:789–801, 8:77–102, 8:513–514, 8:565, 9:340/372, 5:846–848 |
| 19 | RT-DETR float32; Qwen fp16 on CUDA | CONFIRMED | No dtype arg in RT-DETR load; fp16 gated at 5:77–80 with 1:177–178 config; stored output `torch.float16` consistent |
| 20 | Detection details: threshold 0.30, IoU 0.5, containment 0.55, y-bands 50 px, mask close→clean→adaptive-dilate→clip+10px, defaults 60/6 | CONFIRMED | 6:73/76/81/215/222/700–742/815–819/78/80 |
| 21 | OCR details: 40px upscale, bilateral, CLAHE, white-pad vs replicate, confidence 0.45→0.95 cap, thresholds 0.50/0.65 | CONFIRMED | 7:68–70/234–267/277–296; 5:293/314/424 |
| 22 | Translation details: manual default, SFX glossary, region-aware prompts, retry/backoff, rescue parsing | CONFIRMED | 1:270, 8:107/320–352, 19:19–73; retry present (25 hits) — exact "3× linear" constant not separately pinned, immaterial |
| 23 | Inpaint details: LaMa 1024, unload-first, TELEA fallback, artifact mask not re-dilated | CONFIRMED | 9:69/73/302/340/372/385–394 |
| 24 | Render details: font fit 8–48 binary search, grapheme `\X` wrap, rotated path, vertical patch, `render_all_pages` in cell 10 | CONFIRMED | 10:61/96–112/1128/982 |
| 25 | QA details: weights 20/7/1, thresholds 0.65/0.35, visual QA default OFF, Qwen visual QA exists | CONFIRMED | 16:73–77/66–67/69/1352/1426 |
| 26 | Export: JPEG q92, CSV, ai.Text, quality report, manifest, config, ZIP, previews | CONFIRMED | 17:70/125–183/219/251/338/381/404/457/700 |
| 27 | Upload: 50×50 min, EXIF transpose, cv2 fallback | CONFIRMED | 15:66–67/134/153 |
| 28 | Storage: atomic write tmp+os.replace; secrets never serialized; sanitizer keywords | CONFIRMED | 3:207–214; 1:534–548 |
| 29 | Cell 2.1 hotfix adds missing path keys | CONFIRMED | Cell 2 lines 39–51 (session/pages/logs/export/cache) |
| 30 | Secrets scan clean | CONFIRMED | My independent regex scan (T-2) |
| 31 | Monkey-patch inventory + guard flags | CONFIRMED | `_QC_RENDER_PATCHED` (12:141–152), `_QC_FINAL_RENDER_PATCHED` (11:176–187), `_MBD_SLICED` (24:61–122), `__mbd_patched` (24:43–46) |
| 32 | Slicer: SLICE_MODE=True, 1400/240, trigger h>2w | CONFIRMED | 24:55–58, 95 |
| 33 | Base64 download replacement ≤25MB | CONFIRMED | 24:28–46 |
| 34 | UI button calls run_inpaint_all/run_render_all directly (bypasses quality core) | CONFIRMED | 25:363–365 |
| 35 | reset_checkpoint leaves artifacts on disk | CONFIRMED | 25:230–245 (memory-only reset) |
| 36 | "Three ai.Text parsers (cell 8, cell 22 local, cell 25 builder)" | PARTIALLY_CONFIRMED (wording) | Cell 25's `build_ai_text_content` (25:153) builds the export text; it does not parse. Duplication is real (3 implementations of the format); "3 parsers" is imprecise |
| 37 | Marker-set drift: cells 10/16 include "nan", cell 8 does not | CONFIRMED literally, with nuance | Sets verified; but cell 10:156–159 prefers the global (cell 8) set, so the "nan" entry is dead in sequential flow (my F-4) |
| 38 | Double detection per page (CTD mask even when RT-DETR succeeds) | CONFIRMED | 6:1095–1120 |
| 39 | `clear_gpu_cache()` per OCR call | CONFIRMED | 5:339→343 |
| 40 | Silent render skips (WARN only) | CONFIRMED | 10:878–880 |
| 41 | No git attribution; single upload commit; style-based Qwen-era hypothesis; explicit UNKNOWN list | CONFIRMED (methodologically sound) | Git log; GLM_5_3.md §13 |

## Detailed challenges

### D-1 — "stored outputs prove cells 1–7 passed" is an over-claim (INCORRECT as stated)

GLM-5.3 (§7.3) states stored outputs prove banner cells 1–7 passed. Verified reality: outputs exist only for physical cells 0, 1, 2, 3, 5, 6 (banner Cells 1, 2, 2.1, 3, 5, 6). Physical cell 4 (banner "Cell 4: External Assets") and everything after have **no stored outputs**. The successful-run evidence therefore covers environment, config, storage, model-manager/detection setup — NOT the external-asset cell or OCR service. This matters because cell 4 is where zyddnys clone/patch and the libraqm render test live; its success in the owner's last saved session is UNPROVEN by the repo. Impact: low for conclusions (GLM-5.3's own §2 phrasing "partial, cells 0–6" is closer to correct, though even there cell 4 within 0–6 has no outputs), but the evidence discipline of this project requires the correction.

### D-2 — "in the owner's warm-kernel workflow the wrap wins" is presented more firmly than the evidence supports

P-2's second half states the quality wrap wins in the owner's warm-kernel workflow. But the owner's canonical execution order is undocumented (GLM-5.3 lists it as UNKNOWN #3 — an internal tension in the same document). Cell 23 physically comes after cells 11–14; an owner who runs cells in physical order ends with cell 23's plain version, same as a fresh run. The wrap only wins if the owner re-executes cells 11–13 after 23. Verdict: keep as HYPOTHESIS; do not build Phase-2 decisions on it. What is FACT: the effective pipeline differs depending on re-execution order, and the UI button always bypasses the wrap.

### D-3 — P-5 severity understated (see F-1)

GLM-5.3's P-5 describes the misfire risk using cell 11's guard set. The definitions that actually win execution order are cell 12's, which dropped the border-exclusion and 4×-area caps. The destructive potential of `restore_boxes` is therefore higher than the audit conveyed. This does not overturn P-5 — it strengthens it.

### D-4 — P-3 scope broader than stated (see F-6)

Confirmed, with two additions: `recover_coordinates()` also resets `region_type` from `detections.json` (undoing the narrator reclassification) and would clobber manual coordinate corrections; and the module-level call is inside a `print()` f-string (cell 11 line 203) — worth documenting precisely because it is the kind of call static tooling can miss (mine initially did).

---

# VISUAL REVIEW

**NO_VISUAL_EVIDENCE_AVAILABLE**

[FACT] Verified exhaustively: the notebook contains **zero image outputs** (0 `image/png`, 0 `image/jpeg` across all 27 cells; the only stored outputs are text streams in cells 0, 1, 2, 3, 5, 6), and the repository contains no image files of any kind (working tree = 1 notebook `.txt` + 5 agent docs).

[FACT] Consequently the following CANNOT be assessed from this repository by anyone, including GLM-5.3: text placement quality, font rendering, bubble-boundary respect, overflow/clipping, inpainting quality, art preservation, alignment, readability, or unwanted artifacts (residuals, synthetic boxes). Any claim about output quality in either agent log is unsupported until sample artifacts are committed.

[HYPOTHESIS] Quality-relevant code features (grapheme-safe wrap, background-aware color, vertical-note path, box-snap) suggest attention to these concerns — but code features are not visual evidence.

---

# TEST RESULTS

- **T-1 [TEST RESULT]** — Notebook JSON parses; all 27 code cells AST-parse with zero syntax errors.
- **T-2 [TEST RESULT]** — Secret scan over full notebook JSON (`ghp_`, `github_pat`, `sk-`, `AIza`, `hf_`, `Bearer`, `xox`, literal passwords): clean.
- **T-3 [TEST RESULT]** — Output forensics: outputs only in cells 0, 1, 2, 3, 5, 6; all `stream` type; no error outputs; no image outputs; `execution_count` None everywhere; timestamps 2026-08-31 12:18:37–38; environment values as listed in §2.
- **T-4 [TEST RESULT]** — Redefinition map (AST): `run_inpaint_render_all` ×5 (11,12,13,15,23); `kill_residual` ×3 (11,13,14); `render_bengali_text` ×3 (10,11,12); `apply_container_types`/`restore_boxes` ×2 (11,12); `translate_with_nllb` ×2 (8,19); `rtdetr_detect`/`ctd_detect_boxes_and_mask` ×2 (6,24). Sequential "winners" as in §3 table.
- **T-5 [TEST RESULT]** — Module-level call map: pipeline-executing side effects at cell-run time in cells 14 (`run_inpaint_render_all(force=True)`), 23 (`sync_translate_stage()`), 20 (`apply_translations_from_ai_file()`), 26 (`render_all_pages(force=True)`), plus font downloads in 11/12 and UI build in 25.
- **T-6 [TEST RESULT]** — P-7 pandas simulation (pandas 2.2.3, local, no project files):
  - Clean bool round-trip → dtype `bool`, count correct (no inflation).
  - CSV with one empty cell → `[True, False, nan]` (object dtype) → `astype(bool)` counts the EMPTY row as valid (rows [1, 3] selected; only row 1 is real). **Inflation mechanism CONFIRMED.**
  - Quoted `"True"/"False"` strings + empty cell → pandas still parses them to real bools → my anticipated worse variant (whole column truthy) **REFUTED** under standard `read_csv`.
- **T-7 [TEST RESULT]** — dtype resolution: `TORCH_DTYPE=torch.float16` requires `device=="cuda"` AND `torch_dtype=="float16"` in config AND CUDA available (cell 5 lines 77–80); cell 1 lines 177–178 set both automatically when CUDA is present → stored-output `torch.float16` on T4 is consistent with the current code. No contradiction.
- **T-8 [NOT PERFORMED]** — Notebook runtime execution (fresh Run-All, GPU stages): not possible in this review environment. All execution-order conclusions are static (AST + definition maps). They are mechanically unambiguous but should be confirmed once in Colab before Phase-2 refactoring.

---

# DISAGREEMENTS

| Topic | GLM-5.3 | GLM-5.3-Flash (this review) | Evidence | Resolution proposed |
|---|---|---|---|---|
| Proof coverage of stored outputs | "cells 1–7 passed" (§7.3) | Outputs prove only banner Cells 1, 2, 2.1, 3, 5, 6; Cell 4 & 7 unproven | T-3; output forensics | Adopt the narrower claim; treat cell 4 (assets/zyddnys patch) success as UNKNOWN for the last saved session |
| Warm-kernel pipeline winner | "the wrap wins" (P-2 second half) | Undetermined — depends on undocumented owner behavior; cell 23 physically last | D-2; cell order; TASK.md silent on order | Downgrade to HYPOTHESIS; ask owner for canonical order |
| P-5 blast radius | Misfire paints synthetic box (cell-11 style guards implied) | Surviving cell 12 variant lost border/area guards → page-scale over-paint possible | F-1; cell 12:30–42 vs cell 11:46–61 | Treat P-5 as High, not Medium |
| P-3 scope | Reverts snapped coordinates | Also resets region_type and destroys manual edits; call site is a print() f-string arg | F-6; cell 11:30–43, 203 | Keep P-3, add scope |
| ai.Text duplication count | "three parsers" | 2 parsers + 1 builder (duplication real, label imprecise) | 8:812, 22:42, 25:153 | Re-word in decision log |

None of these overturn GLM-5.3's overall conclusions. The audit's central findings (order-dependent fragility, orphaned quality core, in-place artifact mutation, heuristic confidence, no visual evidence) are all independently confirmed.

---

# REQUIRED CHANGES

(Phase-2 proposals ONLY — no code changed in Phase 1. Owner decision required before implementation.)

1. **Reconcile the pipeline entrypoint (P-1/P-2/F-0/F-2/F-3)** — one authoritative `run_inpaint_render_all`; remove or guard all module-level pipeline executions (cells 14, 20, 23-line-89, 26) so a fresh Run All survives. Suggested acceptance test: fresh kernel → Run All → no NameError, no unintended GPU work.
2. **Merge the two box-snap variants into one guarded implementation** (restore cell 11's 5-point probe, border exclusion, and 4× area cap inside the cell 12 lineage), and make `restore_boxes` opt-in. Highest art-preservation risk in the current code.
3. **Make quality-layer artifact mutation reversible/idempotent** — re-derive from `original` + `mask` per run, or write versioned artifacts; never AND-shrink the stored mask in place.
4. **Fix `bengali_valid` round-trip** — replace `.astype(bool)` consumers with an explicit coercion (e.g., `fillna(False).astype(bool)` on a normalized column, or persist 0/1). Verified by T-6.
5. **Commit visual evidence** — one small sample page + artifacts (original/detections/mask/inpainted/final) so both agents can finally review output quality; until then, rendering quality is unassessable for everyone.
6. **Pin the environment** (requirements.txt or Colab-tested versions) — the NLLB breakage proves the failure mode is real.
7. **Consolidate duplicates** — one Bengali validator, one marker set (decide whether `"nan"` belongs), one ai.Text implementation, one `kill_residual`.
8. **Document the canonical cell execution order** in the repo, or extract a package with an explicit composition root (notebook as thin driver).

---

# RECOMMENDATION

**APPROVE_WITH_CHANGES**

Reason: GLM-5.3's Phase 1 audit is independently confirmed as substantively accurate — I verified ~45 claims against the actual code and all but four hold exactly as written; the four corrections (D-1..D-4) adjust evidence precision and severity, not conclusions. Its recommended Phase-2 priorities (entrypoint reconciliation, canonical execution order, artifact mutation safety, visual evidence, environment pinning) match my independent analysis and should proceed to owner review WITH the corrections and new findings F-1..F-6 incorporated. No implementation should start before the owner decides the authoritative pipeline variant, since that decision changes which findings apply.

---

# CONFIDENCE

**HIGH** for static/structural findings: full notebook read, 27/27 AST-verified, every claim line-referenced, definition maps and output forensics mechanically derived.

**MEDIUM** for runtime-behavior claims: the notebook was NOT executed in this review environment (no Colab/GPU); execution-order conclusions are static and unambiguous, but T-8 (one confirming Colab run) remains open.

**Visual quality: NOT ASSESSABLE** — NO_VISUAL_EVIDENCE_AVAILABLE (verified: zero image outputs, zero image files in repo).

---

## STATUS

INDEPENDENT_REVIEW_COMPLETE — Phase 1 audit finished; no source code modified; only this file updated.

---

---

# MANGABD-002 — PHASE A INDEPENDENT INVESTIGATION & PROPOSAL REVIEW

Date: 2026-09-16. Rules observed: TASK_002 Phase A — independent investigation FIRST, review of GLM-5.3's analysis SECOND; no source code modified; evidence labels used throughout.

**Order of operations (integrity note):** the investigation in F2.1–F2.3 was completed — including the statement-level fresh-kernel simulator AND the six-scenario runtime reproduction — BEFORE agents/GLM_5_3.md sections T2.0–T2.11 and DECISION.md were read. The review in F2.4–F2.7 was performed against that completed independent analysis.

---

## F2.0 Method and Evidence Base

- **FE1 [TEST RESULT] — statement-level fresh-kernel simulator** (`m002_sim_v2.py`, kept outside the repo): AST replay of cells 0→26 in physical order, processing statements IN SOURCE ORDER (not per-cell bulk), tracking the module namespace exactly as a fresh kernel builds it. Handles: function/class defs, imports (incl. function-level imports as locals), assigns/augassigns, for/while/if/try/with bodies, `except … as` bindings, nested-def locals, comprehension scoping. For every module-level call it resolves the live binding (latest def ≤ call point) and checks the callee's FREE names (params + locals + function-level imports subtracted) against the namespace state at call time. False positives eliminated during development (documented): comprehension targets, function-level `from … import …` bindings, nested-def names, `except as` names, the `"output_images" in globals()` guarded read in cell 25's `collect_final_images`.
- **FE2 [TEST RESULT] — six-scenario runtime reproduction** (`m002_flash_repro.py`, outside the repo): executes VERBATIM cell-13 + cell-14 sources (extracted from the notebook JSON, unmodified) plus VERBATIM cell-11/12 helper defs (`_snap_white_box`, `_has_valid_trans`, `mask_only_translated`, `apply_container_types`, both `kill_residual` variants, the cell-13 `run_inpaint_render_all`) in controlled namespaces. All artifact IO stubbed; numpy/pandas/cv2 real. Scenarios: S1 fresh-local, S2 warm, S3 fresh+guard, S4 warm+guard, S5 fresh-with-Drive-data, S6 fresh-with-Drive-data+guard. No project files touched.
- **FE3 [FACT] — manual line-pinned reads**: cells 3, 9, 10, 11, 12, 13, 14, 15, 19, 20, 23, 24, 25, 26 read directly this session; every GLM-5.3 line citation in T2.1/T2.7 re-verified against source.
- **UNKNOWN (unchanged)**: no Colab runtime available in this review environment; T-8 (one confirming fresh Colab Run All) remains open for both agents.

---

## F2.1 Independent Investigation Results

### F2.1.1 Execution order and the single abort [TEST RESULT, FE1]

A fresh sequential run (Run All) executes cells 0–13 cleanly, then **aborts at physical cell 14, line 40** — `run_inpaint_render_all(force=True)` — with `NameError: name 'run_inpaint_all' is not defined`. FE1 found **exactly one abort-class site in the entire notebook**; every other module-level call (cells 0–13, 20:1, 23:89, 24's proof block, 25's UI build, 26:1) resolves cleanly, directly or through transitive closure, or guards itself (`try/except`, `in globals()` checks, existence checks). Cells 15–26 are name-resolution-safe but have never executed in a fresh sequential pass (they are unreachable today: Run All stops at 14).

### F2.1.2 Definition order and redefinition timeline [TEST RESULT, FE1+FE3]

| Name | Def sites (cell:line) | Sequential-final binding |
|---|---|---|
| `run_inpaint_render_all` | 11:190, 12:155, 13:35, 15:678, 23:71 | cell 23 |
| `run_inpaint_all` | 15:634 only | cell 15 |
| `run_render_all` | 15:656 only | cell 15 |
| `kill_residual` | 11:99 (v1), 13:4 (v2), 14:4 (v3) | cell 14 v3 |
| `apply_container_types` | 11:63, 12:44 | cell 12 (unguarded snap) |
| `restore_boxes` | 11:121, 12:71 | cell 12 |
| `mask_only_translated` | 11:88 only | cell 11 |
| `render_bengali_text` | 10:552 + wrappers 11:178, 12:143 (stacking, per DECISION N-2) | cell-12 wrapper chain |
| `translate_with_nllb` | 8, 19 | cell 19 |
| `run_test` | 13 cells (harness pattern) | last executed cell |

The load-bearing structural fact, derived independently and agreeing with GLM-5.3's T2.1.5: **every one of the five `run_inpaint_render_all` variants calls `run_inpaint_all`/`run_render_all`, which exist only in cell 15.** The failure is therefore POSITIONAL — any module-level call to this name placed before cell 15 cannot succeed on a fresh kernel, regardless of which variant is bound. Cell 14:40 is such a call.

### F2.1.3 The failure mechanism is a deferred NameError [TEST RESULT, FE2 S1]

`run_inpaint_render_all` IS defined at 14:40 (cell 13's def + `globals()` rebind at 13:45). The crash occurs when the bound body resolves `run_inpaint_all` (cell 13:39) at CALL time. This is why "the function exists" reasoning misses it, and why the bug is invisible in warm-kernel sessions.

### F2.1.4 Notebook state dependencies [FACT + TEST RESULT]

- `MANGABD_MANIFEST` / `translation_df` are loaded FROM DISK at cell 3 module level (`load_manifest()`, `load_translation_df()` at 3:992–993). Fresh KERNEL ≠ fresh DISK: `choose_base_directory()` (cell 1:67–103) PREFERS `/content/drive/MyDrive/MangaBD_V12` and actively mounts Drive when absent. A fresh runtime with Drive mounted loads the previous session's real pages and real translations. This distinction is central to challenge C-1 below.
- Sticky guard flags (`_QC_FINAL_RENDER_PATCHED`, `_QC_RENDER_PATCHED`, `_MBD_SLICED`, `colab_files.__mbd_patched` attribute) make re-application semantics history-dependent. [FACT]
- `globals()`-rebind idiom (`globals()["run_inpaint_render_all"] = …` at 11:200, 12:162, 13:45, 14:37) and the `kill_residual` rebind at 14:37 make binding resolution order-sensitive by design. [FACT]

### F2.1.5 Run All vs alternate execution paths [TEST RESULT, FE2 + FE1]

| Path | Behavior at cell 14 | Effective `run_inpaint_render_all` binding afterwards |
|---|---|---|
| Fresh Run All (literal, stop-on-error) | **NameError, run aborts** | cell 13's wrap (last executed def) |
| Fresh, continue past 14 manually | 14's call still fails; 15–26 then run | cell 23's plain version |
| Warm kernel, re-run cell 14 | Fires FULL pipeline as a side effect | whichever variant was last bound (23 normally) |
| Warm kernel, UI button (25:363–365) | Bypasses all variants: calls `run_inpaint_all`+`run_render_all` directly | n/a |

Same call site, four different outcomes — TASK_002 question 8 ("Run All can trigger a different implementation from manual reruns") is answered YES by mechanism, not just by observation.

### F2.1.6 Independent root-cause determination (formed BEFORE reading GLM-5.3's report)

1. **Direct mechanism:** cell 14:40 module-level call → cell-13 binding → call-time resolution of cell-15 names → NameError. Any forward pass fails here; no execution order within a single sequential pass can satisfy it (the call's dependency is defined LATER than the call).
2. **Structural cause:** the patch layer's "define-and-immediately-apply" pattern — cells 14:40, 20:1, 23:89, 26:1 all execute pipeline work at module level; cell 14 is the only one whose dependency graph points FORWARD. Five conflicting variants of the orchestrator with divergent semantics (`require_translation` defaults: 13→False, 15→True, 23→False) mean that "making the name exist" is NOT equivalent to "preserving behavior": which variant is live changes what the same call DOES.
3. **Process cause:** no fresh-run test ever existed; stored outputs (cells 0,1,2,3,5,6 only, no error outputs, exec_count None) show the last saved session never reached cell 14.

---

## F2.2 Independent Runtime Reproduction (FE2) — TEST RESULTS

Verbatim notebook code; stubbed IO only. `force`/`require_translation` recorded where relevant.

| Scenario | Kernel state | Code | Result | Evidence recorded |
|---|---|---|---|---|
| S1 | fresh-local (empty manifest, empty df) | current | **`NameError: name 'run_inpaint_all' is not defined`** | `apply_container_types()` ran (0 boxes, re-saved empty CSV); page loop no-op; crash at the `run_inpaint_all` line |
| S2 | warm (cell-15 names present) | current | OK — full pipeline fires | `run_inpaint_all(force=True, require_translation=False)` then `run_render_all(force=True, require_translation=False)` |
| S3 | fresh-local | GLM-5.3 guard | OK — clean skip, printed reason | no pipeline calls |
| S4 | warm | GLM-5.3 guard | OK — call sequence **identical to S2** | same as S2 |
| S5 | **fresh-with-Drive-data** (1 page, 2 translation rows, real snap/mask code paths) | current | **`NameError` — AFTER real mutations** | `save_translation_df()` called; **`translation_df` coordinates snapped + `region_type` bubble→narrator (persisted)**; **mask artifact rewritten** (`save_image_artifact(pid='p1', kind='mask')`); THEN crash |
| S6 | fresh-with-Drive-data | GLM-5.3 guard | OK — skip | **zero mutations** |

S5/S6 are the decisive rows: see challenge C-1. S2==S4 independently confirms GLM-5.3's E2 scenario D claim (`calls_B == calls_D`).

---

## F2.3 Review of GLM-5.3's MANGABD-002 Phase A Report

### F2.3.1 Verdict on the core question: root cause or symptom?

**GLM-5.3 found the ROOT CAUSE — not merely the symptom — and did so at three explicitly separated layers (T2.3).** All three layers are independently confirmed by my own analysis:

- **Layer 1 (immediate mechanism)** — CONFIRMED. The "deferred NameError" framing (name exists; BODY fails) is exactly right and is the non-obvious part of this bug. FE1+FE2 reproduce it precisely, including the empty-disk pre-crash behavior (S1 matches E2 scenario A, including the idempotent empty-CSV re-save GLM-5.3 describes).
- **Layer 2 (structural cause: define-and-immediately-apply patch pattern)** — CONFIRMED. My module-level side-effect map (14:40, 20:1, 23:89, 24's patch+proof, 26:1, font downloads 11/12) matches T2.1.3 exactly. The generalization in T2.1.5 ("every variant is hungry for cell-15 names; the position relative to cell 15 is the invariant") is correct and is genuinely stronger than a cell-specific explanation — it is what makes this a root cause rather than a one-off mistake.
- **Layer 3 (process cause: no fresh-run test ever existed)** — CONFIRMED as far as repository evidence can carry it; the stored-output forensics are consistent.

The proposal (T2.7) follows from this root-cause analysis: it targets the positional invariant (declare the dependency at the one site that violates it) instead of the surface symptom (a NameError). It does not resolve Layer 2/3 — by design; TASK_002's preservation requirements and DECISION.md owner questions (Q1/Q2) correctly forbid an agent from unilaterally picking a canonical variant. Declaring the dependency in code at the violating site IS the minimal correct response to the root cause, pending the owner's structural decision.

### F2.3.2 Claim-by-claim verification (T2 sections)

| GLM-5.3 claim | Verdict | My evidence |
|---|---|---|
| T2.1.1 cell placement matches banner intent; anomaly is the module-level call, not placement | **MOSTLY CONFIRMED** (see C-3) | banners verified at 11:3, 12:3; cells 13/14 have no banners |
| T2.1.2 definition timeline & winners | **CONFIRMED** (all line numbers match) | FE1 timeline identical |
| T2.1.3 module-level execution map; 14:40 the only abort; 20/23/26 fresh-safe | **CONFIRMED** | FE1 found the same single abort; FE3 verified 20's no-file return-0, 23's empty-df return-0, 24's try/except proof block, 26's empty-loop no-op |
| T2.1.4 guard-flag state machine & stickiness | **CONFIRMED** | FE3: flags at 11:187, 12:152, 24:122, `__mbd_patched` attribute at 24:46; wrapper-stack chain verified |
| T2.1.5 every variant needs cell-15 names | **CONFIRMED** | FE1 Phase-2 table identical |
| T2.2.1 exactly one abort; cells 15–26 name-safe | **CONFIRMED** | FE1 full-replay: same result |
| T2.2.2 scenario A/B/C/D matrix; deferred NameError; `calls_B == calls_D` | **CONFIRMED** | FE2 S1–S4 reproduce the matrix |
| T2.2.2 observation 2: "pre-crash work on fresh is provably empty … outcome-neutral by proof" | **REFUTED as a universal claim** (see C-1) | FE2 S5: real persisted mutations before the crash |
| T2.3 three-layer root cause | **CONFIRMED** | F2.1.6 |
| T2.4 contributing factors 1–7 | **CONFIRMED** (factor 2's "unconditional call fires even on zero pages" verified in FE2 S1) | |
| T2.5 answers to the ten questions | **CONFIRMED** — my answers match on all ten, including Q8's three-pipelines fork | F2.1.5 adds the Drive dimension to Q7 |
| T2.6 option evaluation | **CONFIRMED** — rejection reasoning is sound; see F2.5 for an additional reason to reject option 3 | |
| T2.7 proposed guard | **APPROVE WITH CORRECTED JUSTIFICATION** (see F2.5) | FE2 S3/S4/S6 |
| T2.8 regression risks R1–R6 | **CONFIRMED with one gap** (see C-2) | |
| E2's fresh-state model (empty manifest + empty df) | **INCOMPLETE** (see C-1) | FE2 S5/S6 |

**No fabricated claims found. No unsupported line citations found. Every checkable line number in T2.1–T2.8 matches the source.**

---

## F2.4 CHALLENGES TO GLM-5.3

### C-1 (SIGNIFICANT) — "The pre-crash work on fresh is provably empty" is false in the Drive-persisted scenario, which GLM-5.3's evidence base did not model

GLM-5.3's E2 reproduction models the fresh state as empty manifest + empty df ("artifact IO stubs returning None — fresh disk", T2.0). But the notebook itself distinguishes fresh KERNEL from fresh DISK:

- Cell 1 (`choose_base_directory`, 1:67–103) PREFERS `/content/drive/MyDrive/MangaBD_V12` and actively requests Drive mount when it is absent. Drive persistence is the notebook's designed primary storage, not an edge case.
- Cell 3 loads state from disk at module level (`load_manifest()`, `load_translation_df()` at 3:992–993).

Consequently a "fresh Colab runtime" for a Drive-using owner loads the previous session's REAL pages and REAL translation rows. In that state, FE2 scenario S5 (verbatim cell-13/14 code, real snap/mask code paths, real pandas/cv2) shows that cell 14's call performs PERSISTED MUTATIONS before crashing:

1. `apply_container_types()` (cell-12 variant) snaps box coordinates in `translation_df`, sets `region_type="narrator"` on snapped rows, and calls `save_translation_df()` → **CSV rewritten to disk**;
2. `mask_only_translated(pid)` runs per page and calls `save_image_artifact(pid, "mask", …)` → **stored masks irreversibly AND-shrunk**;
3. THEN `run_inpaint_all` raises NameError.

This is the same destructive class GLM-5.3 itself identified for warm kernels (N-1(c), R-3): on Drive-fresh it fires too, partially, before the abort. T2.2.2 observation 2 and T2.7 point 3 ("skipping the call on fresh discards NO work … outcome-neutral by construction, not by hope") are therefore over-generalized: they are proven ONLY for the empty-disk state.

**Direction of the correction matters:** this does NOT weaken the proposed guard — it STRENGTHENS it. FE2 S6 shows the guard skips ALL mutations in the Drive scenario. The guard is not merely "skips no-op work"; in the realistic Drive scenario it PREVENTS artifact corruption. But DECISION-grade justification must state the true reason: the guard converts cell 14 from "mutate-then-crash on Drive-fresh" and "fire full destructive pipeline on warm" into "declare dependency; fire only in the warm path that already works today". The empty-disk neutrality proof is insufficient support on its own.

Whether the owner actually runs with Drive persistence is UNKNOWN (GLM-5.3 T2.10 Q1 should be extended to ask exactly this).

### C-2 (MODERATE) — R1 omits the "fresh Run All becomes real pipeline work" dimension

With the guard, a fresh Run All + Drive data proceeds past cell 14 into: cell 20 (`apply_translations_from_ai_file()` — applies any `ai_text_export*.txt` found), cell 23 (`sync_translate_stage()` — marks translate stages), and cell 26 (`render_all_pages(force=True)` — a FORCED full re-render of every eligible page at Run-All time). GLM-5.3's R1 frames post-fix fresh-run risk as environmental failure of newly-reachable cells, but not as "fresh Run All silently triggers heavy, possibly hours-long GPU work and artifact overwrites over persisted data". DECISION.md proposal 1's acceptance test says "no NameError, no unintended GPU work" — the guard alone does not satisfy the second clause in the Drive scenario. This is not a blocker (cells 20/23/26 are the codebase's current intent once unblocked, and preserving them is TASK_002's mandate), but it MUST be in the owner-facing description of what fresh Run All will do after the fix. [FACT for the call sites; HYPOTHESIS for duration/cost]

### C-3 (MINOR) — "Cell ORDER is intended" rests on two banners that reference OLD numbering

T2.1.1 infers intended placement from banners in cells 11 and 12 ("Place: after Cell 10, before Cell 11" — original numbering where orchestrator = old Cell 11 = physical 15). The inference is reasonable and the physical arrangement does match, but cells 13 and 14 — the cells that actually break fresh runs — carry NO placement banner; they look like patch-session scratch cells ("RESIDUAL KILLER", "kill_residual v3") whose placement nobody reconsidered. The claim is acceptable as stated for the patch LAYER, but evidence for cells 13/14 specifically is thinner than T2.1.1 implies. Does not change the root cause or the fix.

### C-4 (COSMETIC) — Proposed comment says "the orchestrator (Cell 11)"

The guard's comment uses original numbering ("Cell 11") while every other object in the fix discussion uses physical numbering (cells 13/14/15). Future maintenance at 3 a.m. will be confused. Suggest: "the orchestrator cell (physical 15; banner numbering: Cell 11)". No functional impact.

---

## F2.5 Independent Regression-Risk Review of the Proposed Guard

My own assessment, independent of T2.8:

1. **Warm preservation: PROVEN, not assumed.** FE2 S4 reproduces S2's call sequence exactly (GLM-5.3's E2 scenario D claim independently confirmed). Re-running cell 14 warm still fires the pipeline; the owner's re-apply workflow is untouched.
2. **Fresh skip safety: PROVEN for empty-disk (S1→S3) and PROVEN BENEFICIAL for Drive (S5→S6: mutations prevented).** The fix is strictly safer than today's code in every modeled state.
3. **Guard-condition sufficiency: SOUND today.** The two checked names are exactly the ones missing at 14:40; every other free name of all five variants (`MANGABD_MANIFEST`, `apply_container_types`, `kill_residual`, `mask_only_translated`, `restore_boxes`, `sync_translate_stage`) is defined by cells ≤13; transitively, `run_inpaint_all`'s `inpaint_all_pages` (cell 9) and `run_render_all`'s `render_all_pages` (cell 10) also exist by cell 14. GLM-5.3's R3 staleness caveat is the correct ongoing-risk note.
4. **Partial-kernel edge cases: no behavior change vs today.** (a) Run 0–13, skip 14, run 15+, re-run 14 → guard passes → fires with cell-23 binding — identical to today's warm behavior. (b) Run 0–14 fresh (skip), run 15–26, re-run 14 → same as (a). (c) UI button path never touches the guard. Verified by FE2 semantics + FE1 timeline.
5. **Not an error-hider:** the guard is an explicit dependency declaration with a loud, greppable skip message; not a try/except, not a silent fallback, not a dummy variable. TASK_002's forbidden patterns are avoided. I checked the stronger objection — that the guard "institutionalizes" the define-and-apply pattern — and reject it for THIS task: resolving the pattern requires the owner decisions already gated in DECISION.md Q1/Q2; the guard changes zero semantics in any state where today's code does not crash.
6. **Additional reason to reject option 3 (move the call after cell 15)** — beyond GLM-5.3's diff-size/duplication argument: moving the call changes WHICH variant executes (cell-23's plain, or cell-15's `require_translation=True` depending on placement) relative to the owner's current warm re-apply semantics (cell-13's quality wrap, on the paths where it applies). The guard is the only minimal option that never executes fresh and preserves warm semantics exactly. [FACT for binding resolution; HYPOTHESIS for owner-workflow reliance]
7. **Condition on acceptance (from C-1/C-2):** the fix must be described to the owner as "removes the fresh abort AND the Drive-fresh pre-crash mutations", NOT as "makes fresh Run All a safe no-op". Fresh Run All with Drive data still performs real work at cells 20/23/26.

---

## F2.6 Answers to the Eight Verification Points Requested by the Owner

1. **Execution order** — intended: physical order (banner placement matches); actual fresh Run All: 0–13 OK, abort at 14:40. [TEST RESULT]
2. **Variable/function definition order** — five `run_inpaint_render_all` defs (11/12/13/15/23); `run_inpaint_all`/`run_render_all` ONLY at 15:634/656; the call at 14:40 necessarily precedes its dependency in any forward pass. [TEST RESULT]
3. **Function redefinitions** — full timeline in F2.1.2; `kill_residual` ×3 (11/13/14), `apply_container_types`/`restore_boxes` ×2 (11/12), `render_bengali_text` stacking wrappers (11/12), `translate_with_nllb` ×2 (8/19), detection wrappers ×2 (6/24). Which version is LIVE at each call point is order-dependent (FE1 Phase-4 map). [TEST RESULT]
4. **Notebook state dependencies** — disk-loaded `MANGABD_MANIFEST`/`translation_df` (cell 3, Drive-preferred base dir), sticky patch flags, `globals()` rebinds, stacked wrapper closures. Fresh kernel ≠ fresh disk. [FACT]
5. **Fresh-runtime behavior** — abort at 14:40 via deferred NameError; Drive-fresh additionally mutates translation_df + masks before the abort (S5). [TEST RESULT]
6. **Run All behavior** — stops at first uncaught exception; cells 15–26 unreachable today; with guard, reaches 15–26 including real pipeline work at 20/23/26 when data exists. [TEST RESULT + HYPOTHESIS on runtime cost]
7. **Possible alternate execution paths** — four-path matrix in F2.1.5; same call site, four outcomes; UI button bypasses all variants (25:363–365). [TEST RESULT]
8. **Regression risks of the proposed solution** — warm behavior preserved exactly (S2==S4); fresh skip strictly safer in both disk states (S1→S3, S5→S6); guard condition sufficient; risks R1–R6 confirmed with C-2's "real pipeline work" addition; acceptance condition in F2.5.7. [TEST RESULT]

---

## F2.7 FINAL VERDICT ON GLM-5.3's PHASE A

**CORRECT — root cause found and correctly layered; proposal APPROVED for Phase B with two evidence corrections and one documentation condition.**

- The core question "root cause or symptom?" is answered decisively: **root cause**. The positional invariant (T2.1.5 — every variant needs cell-15 names) plus the three-layer decomposition (T2.3) plus the define-and-immediately-apply pattern identification (Layer 2) go substantially beyond the NameError symptom.
- What is MISSING is not causal understanding but **evidence coverage of the Drive-persisted fresh state** (C-1) and **owner-facing disclosure of post-fix fresh-run behavior** (C-2). Neither changes the fix; both change the justification text and the risk register.
- Required before Phase C implementation:
  1. Amend T2.2.2/T2.7/T2.8 wording: empty-disk neutrality proof holds ONLY for the empty-disk state; Drive-persisted fresh currently mutates data pre-crash (cite FE2 S5/S6), and the guard prevents it.
  2. Add R1 note: post-fix fresh Run All + Drive data executes real pipeline work at cells 20/23/26 (including forced re-render).
  3. Fix the C-4 comment wording in the proposed patch (cosmetic, fold into Phase C).

No source code modified. Analysis scripts persisted outside the repo (`m002_sim_v2.py`, `m002_flash_repro.py`).

---

## STATUS

MANGABD-002 PHASE A COMPLETE (GLM-5.3-Flash): independent investigation + review finished; verdict = APPROVE_WITH_CORRECTED_JUSTIFICATION; awaiting Project Owner approval per TASK_002 Phase B/C gate.

**Confidence: HIGH** for the abort mechanism, the single-abort completeness, and the guard's warm preservation (static simulation + verbatim-code runtime reproduction, independently executed). **MEDIUM** for Drive-scenario behavior in the real owner environment (FE2 models Drive state with stubbed IO; real Drive round-trip untested). **UNKNOWN** remains T-8 (one confirming fresh Colab Run All) and whether the owner's workflow uses Drive persistence.

**Visual quality: NOT ASSESSABLE — NO_VISUAL_EVIDENCE_AVAILABLE** (re-verified this session: zero image outputs in the notebook, zero image files in the repository).

---

# MANGABD-002 — PHASE D INDEPENDENT VERIFICATION (GLM-5.3-Flash)

Date: 2026-09-27. Object under review: commit `829c383` ("WIP: MANGABD-002 Phase C — awaiting Phase D verification") on branch `mangabd-002-phase-c`, base `main`@`aabc592`. Rules observed: TASK_002 Phase D + DECISION.md §B.10; **no source code modified**; **no amend, no merge** (gating per §B.9 preserved); evidence labels used throughout; GLM-5.3's self-report (T2.13) was NOT trusted — every check below was re-executed independently against the pushed artifact in a fresh clone.

## PD.0 Method and Environment

- Fresh clone of `iskultri-scans/MangaBD-`; local branch `mangabd-002-phase-c` created at `origin/mangabd-002-phase-c`; verified HEAD = `829c38376dc387521bcebd1bb37f0b314bd2397e` and merge-base with `main` = `aabc592` (branch is exactly one commit ahead; `main` untouched). [FACT]
- Verification scripts rebuilt this session and persisted OUTSIDE the repo (workspace `scripts/`): `m002_sim_v2.py` (fresh-kernel simulator, FE1 contract rebuilt from F2.0), `m002_flash_repro.py` (six-scenario runtime reproduction, FE2 contract rebuilt from F2.0/F2.2), plus three purpose-built auditors (`m002_step1_audit.py`, `m002_step4_cites.py`, `m002_step5_scope.py`). [FACT]
- **Simulator calibration (prerequisite):** the rebuilt FE1 was run FIRST against the BASE notebook and required to reproduce Phase A's finding before any branch claim. Result on base: **exactly ONE abort-class site — `cells[14]` line 40, names `run_inpaint_all`/`run_render_all`, chain `<module> -> run_inpaint_render_all` (def at 13:35)** — identical to F2.1.1/F2.1.3. The rebuilt simulator also independently reproduced F2.1.2's definition timeline verbatim (`run_inpaint_render_all` 11:190, 12:155, 13:35, 15:678, 23:71; `run_inpaint_all` 15:634; `run_render_all` 15:656; `kill_residual` 11:99, 13:4, 14:4). Only after this calibration was the branch result accepted. [TEST RESULT]
- Numbering convention (verified against §B.9 "cells[14] … (physical cell 14; banner title 'kill_residual v3')"): all cell indices in this record are 0-based JSON `cells[N]` with 1-based line numbers. Under this convention the guard comment's "physical cell 15; banner numbering 'Cell 11'" is factually correct: `cells[15]` is the banner-"Cell 11" orchestrator that defines `run_inpaint_all` (15:634) and `run_render_all` (15:656). [FACT]

## PD.1 Step 1 — DIFF & SCOPE AUDIT: **PASS**

- `git diff main...HEAD --numstat`: exactly 2 files — `12 2  MangaBD_V12_ipynb_txt.ipynb (3).txt` and `86 5  agents/GLM_5_3.md`. Matches the expected +12/−2 and +86/−5 exactly. [FACT]
- **Mode-flip check (critical):** `git diff main...HEAD --summary` is EMPTY (no mode/rename entries); grepping the raw `git show 829c383` patch for `^(old mode|new mode|deleted file|new file|rename )` returns nothing; `git ls-tree -r HEAD` shows ALL 7 tracked files at mode `100644`. The mode-flip artifact (cf. history commit 5342653) is completely absent from this commit. [FACT]
- JSON parses (`nbformat=4, nbformat_minor=0`); cell count = 27; all 27 cells `ast.parse` cleanly, including the two edited cells (0-based `cells[14]`, 46 lines; `cells[26]`, 5 lines) — and under either indexing convention (sanity-checked both). [TEST RESULT]
- Notebook-level `metadata`/`nbformat` byte-identical between base and branch; in BOTH edited cell objects, every field except `source` is unchanged (`cell_type`, `execution_count`, `metadata`, `outputs` — all verified equal; no stale outputs shipped, no key added/removed). [FACT]

## PD.2 Step 2 — STATIC RE-CHECK (Cell 14 Guard): **PASS**

- Fresh-kernel simulation of the EDITED branch notebook: **abort-class site count = 0** (0 missing-name records; 1773 module-level call sites traversed, transitive closure included). The base's single abort site (`cells[14]`:40) is gone. [TEST RESULT]
- Definition timeline on branch is byte-for-byte the same def-site table as base (PD.0 calibration output) — §B.10.1's "definition timeline unchanged except cell 14's tail" holds; cells 15–26 remain name-resolution-safe (module-level calls at 20:1, 23:89, 26:1 all resolve; cell 15's module-level tail is self-test/prints + the intentional `raise RuntimeError` self-test gate). [TEST RESULT]
- Guard text: `cells[14]` lines 40–46 equal the §B.6 block **VERBATIM**, line by line, including the C-4-corrected comment `# the orchestrator cell (physical cell 15; banner numbering "Cell 11") defines` — programmatically compared against the DECISION.md §B.6 code block, not eyeballed. [FACT]

## PD.3 Step 3 — GUARD-LOGIC EQUIVALENCE (Runtime Matrix): **PASS** (9/9)

Verbatim sources from the PUSHED branch file (Guarded = branch `cells[14]`) and from the `main` blob (Current = base `cells[14]`, `run_inpaint_render_all(force=True)`); verbatim helper defs from `cells[11]`/`cells[12]` executed in binding order so the namespace at `cells[14]` reproduces a sequential fresh kernel (cell-12 versions of `apply_container_types`/`restore_boxes`/`_snap_white_box` win; `kill_residual` v2 from `cells[13]`, overridden by v3 inside `cells[14]` itself). Artifact IO stubbed; numpy/pandas/cv2 real; synthetic Drive state = 1 page `p1` (inpaint/render stages done), 2 translation rows, original/inpainted/mask artifacts present, with a snappable white box so the C-1 mutation chain is exercisable. [TEST RESULT]

| # | Scenario (disk, kernel, cells[14] variant) | Result | Evidence |
|---|---|---|---|
| S1 | Empty, Fresh, Current | **NameError: run_inpaint_all** (baseline) | `apply_container_types()` ran → 1× empty-CSV re-save; page loop no-op; 0 artifact writes; crash at the `run_inpaint_all` line |
| S3 | Empty, Fresh, Guarded | **OK-with-skip, zero mutations** | skip banner printed; 0 pipeline calls, 0 helper calls, 0 saves, df unchanged |
| S5 | Drive, Fresh, Current | **Mutate-then-crash (NameError)** | df row 0: `region_type` bubble→**narrator**, bbox (40,50,60,60)→(30,40,80,80) snapped; 1× `save_translation_df()` (persisted); **`save_image_artifact(p1, 'mask')`** with content visibly AND-shrunk; THEN `NameError: run_inpaint_all` — reproduces C-1/DR-A exactly |
| S6 | Drive, Fresh, Guarded | **OK-with-skip, ZERO mutations** | skip banner printed; 0 calls; df unchanged; 0 artifact saves; store snapshot byte-identical |
| S2 | Drive, Warm, Current | **Pipeline fires** | `run_inpaint_all(force=True, require_translation=False)` → `run_render_all(force=True, require_translation=False)` |
| S4 | Drive, Warm, Guarded | **Pipeline fires — call sequence IDENTICAL to S2** | recorded call tuples equal element-for-element; helper-call sequence, df delta, artifact saves and stdout all identical to S2 |

- Skip banner `⏭️ kill_residual v3 loaded; pipeline run skipped (orchestrator not loaded yet)` printed in BOTH fresh+guarded scenarios (S3, S6) — verified against the verbatim §B.6 string. [TEST RESULT]
- S2==S4 independently re-confirms the E2/DR-B==DR-D warm-preservation claim against the pushed artifact (the gap T2.13.4 explicitly left for Phase D is now closed). [TEST RESULT]
- Warm-path note: S2/S4 reproduce the known pre-existing warm destructive semantics (mask AND-shrink + inpainted rewrite on warm re-apply) — unchanged by this fix, exactly as §B.8's residual-scope note states. [TEST RESULT]

## PD.4 Step 4 — CELL 26 SEMANTIC SPOT-CHECK (`force=False`): **PASS** (30/30 cite checks)

- Cache gate verified at `cells[10]` (0-based; banner "Cell 10: Rendering Service"): `10:790 def render_page(page_id, force=False)`; `10:803 if is_stage_done(page_id, "render") and not force:` → `10:804 cached = load_image_artifact(page_id, "final")` → `10:806-808` early return "✅ Render cached" (no overwrite, no GPU work). **`force=False` is resume-aware: rendered+checkpointed pages cache-hit.** [FACT + TEST RESULT]
- Un-rendered or reset pages still render: pages failing `is_stage_done` take the full path; checkpoint-without-file (10:810–816) WARNs and calls `reset_page(page_id, from_stage="render")`, then falls through to re-render. Eligibility filtering at `render_all_pages` (10:982): inpaint stage (10:999–1000), translate stage when required (10:1002–1003), per-page force pass-through (10:1024). [FACT]
- `force=True` paths remain available: (a) UI 🎨 button — `on_final` (25:358) → same-idiom `in globals()` guard (25:363) → `run_render_all(force=True,require_translation=False)` (25:365) → forwards force via 15:669–672; (b) help text `render_all_pages(force=True)` (16:1340); (c) function-scoped recipe call (18:987). `render_all_pages` is defined exactly once (10:982) and never redefined. [FACT]
- `cells[26]` content: exactly 4 Bengali MANGABD-002 comment lines + exactly ONE AST statement, `render_all_pages(force=False)`; the comment block is the resume-aware rationale with the force escape hatches (🎨 button / `render_all_pages(force=True)`), matching the approved §B.11.2 bundle as recorded in T2.13.1/§B.11.2 (see PD.7 note on the approval text's provenance). [FACT]

## PD.5 Step 5 — SCOPE INVARIANT: **PASS**

- Per-cell byte comparison (JSON-dumped cell objects, base vs branch): **25 cells byte-identical** (0–13, 15–25); **changed cells = [14, 26] only**. [TEST RESULT]
- `cells[14]`: lines 1–39 byte-identical; base line 40 was exactly `run_inpaint_render_all(force=True)`; branch lines 40–46 = the §B.6 block. Single-region replacement. [FACT]
- Notebook diff = **exactly 2 hunks** (`@@ -11700,7 +11700,13 @@`, `@@ -18037,7 +18043,11 @@`); files changed = {notebook, `agents/GLM_5_3.md`} only; no other agent docs or source files touched. [FACT]
- Hash cross-check: base blob sha256 `1fee5e7c…` (803,682 B) → branch `448540f8…` (804,601 B), +919 B — **independently matches T2.13.1's recorded values**, and the git diff proves the delta is confined to the two edited regions. [TEST RESULT]

## PD.6 Verdict

**PHASE D APPROVED.** GLM-5.3's Phase C implementation is verified against the pushed artifact `829c383` in all five requested dimensions: scope & history hygiene (incl. zero mode flips), static fresh-kernel safety (0 abort sites on a calibrated simulator), runtime guard equivalence in both disk states with warm byte-equivalence, correct resume-aware `force=False` semantics at cell 26 with all force paths preserved, and a strictly minimal 2-hunk/25-cell-untouched diff. The implementation complies with TASK_002's forbidden-pattern rules (no try/except swallowing, no dummy variables, no silent fallback, no global hack — the `in globals()` idiom is the notebook's own, 25:363) and discharges the §B.6/R1(b) Run-All-time re-render disclosure via the Owner-approved §B.11.2 bundle.

Per the Owner-prescribed sequence: GLM-5.3 may now amend the WIP commit with the final message and merge to `main`, **after** this sign-off is relayed through the PM (Qwen3.8-Max) to the Project Owner per DECISION.md §B.9. This commit adds ONLY this Phase D record to `agents/GLM_5_3_FLASH.md` (a permitted investigation file); no source file touched; the WIP commit itself was not amended.

## PD.7 Scope notes, limitations, and non-blocking observations

1. **Deferred by design (not a blocker; per §B.10.6):** §B.10.4 (one confirming fresh Colab Run All — closes T-8) and §B.10.5 (warm-path UI functional check with a real upload) structurally require a live Colab runtime and remain with the Owner's first Run All. Static + local-runtime evidence stands per §B.10.6, as in Phases A/B. [UNKNOWN — unchanged]
2. **§B.11.2 approval text provenance:** the full 5-line cell-26 block is not quoted verbatim inside any repository document (T2.13.1 describes it; the original approval lives in the PM relay). Verified here against the repo evidence: 4-comment-lines + single-statement structure, resume-aware semantics, and the force escape hatches named in §B.11.2. [FACT for repo state; ASSUMPTION that the relayed approval text matches T2.13.1's description]
3. **Post-fix fresh Run All with Drive data** now performs real module-level work at cells 20/23/26 (translation-file apply, stage sync, resume-aware render) — this is the disclosed, Owner-approved behavior (§B.6 disclosure as amended by the §B.11.2 bundle), not a new risk introduced by the guard. With the bundled `force=False`, already-rendered pages cache-hit; only un-rendered/reset pages render. [FACT + TEST RESULT]
4. **Pre-existing conditions unchanged** (explicitly out of MANGABD-002 scope, tracked in MANGABD-001): the fresh-vs-warm `run_inpaint_render_all` variant fork (fresh-final binding = cell 23's plain variant — Owner Question 2), the warm-path destructive re-apply N-1(c) (reproduced unchanged in S2/S4), sticky QC guards, and the redefinition jungle. No regression in any of these was introduced by 829c383. [FACT]
5. Minor cosmetic observation for the record: `25:365` is spelled `run_render_all(force=True,require_translation=False)` (no space after the comma) — semantically identical to the cite in T2.13.3; no action required. [FACT]

## STATUS

MANGABD-002 **PHASE D COMPLETE — PHASE D APPROVED** (all 5 verification steps PASS; zero required fixes). Awaiting PM relay of this sign-off to the Project Owner; GLM-5.3 may then amend the WIP commit message and merge. T-8 (live Colab confirmation) remains the Owner's first fresh Run All.

**Confidence: HIGH** for all five verified dimensions (calibrated static simulation + verbatim-code runtime reproduction against the pushed bytes + programmatic verbatim/hash/diff audits). **MEDIUM** only for real-Drive/real-GPU environmental behavior, untestable outside Colab (deferred per §B.10.6).

---

## VISUAL REVIEW — S001_color_webtoon
Date: 2026-09-29
Reviewer: GLM-5.3-Flash

Scope: independent visual + pixel-level audit of `samples/S001_color_webtoon/` (original.jpg, text_mask.png, inpainted.png, final.jpg, detections.json, ocr.json, translation.json, metadata.json) against PROJECT_CONTEXT §8. Method: full-image inspection, per-region 2x–6x crops of all 6 detections from original/inpainted/final, programmatic mask-coverage and ink measurements (all coordinates below are in the 844×1200 source space, origin top-left). No file in `samples/` was modified; no source code touched.

### Per-Region Table

| # | Region Type | Original Text | Mask Quality | Inpaint Quality | Render Quality | Issues |
|---|-------------|---------------|--------------|-----------------|----------------|--------|
| 1 | overlay (vertical T/L note, box 10,81,61×298) | "T/L note: Koganei in hiragani is spelt こがねい while Otearai is spelt as おてあらい and both "U" is pronounce as "I" which is a vowel" | ⚠️ 99.7% box coverage; missed bottom glyph tips (→ 11-px speck residue) | ✅ 0 residue inside mask | ✅ vertical rotated Bengali, correct shaping, zero overflow (0 ink px beyond y=81..379 in x=10..70); ⚠️ CJK fallback glyphs half-size and pale | 11 dark residue specks (lum. down to 18) at (34–47, 370–381); こがねい/おてあらい/しゅ rendered ~50% size, mean ink luminance ~90 vs ~47.5 original; panel-border AA edge darkened at x≈75 over ~229 rows (cosmetic); OCR mis-transcribed source (see Metadata/OCR notes) |
| 2 | bubble (box 218,110,87×156) | "THE ONLY LETTER CORRECT IN THAT NAME WAS "!"" | ✅ 98.5% coverage; mask overreaches bubble edge at top-right (301–304, 110–126) | ✅ 32 "residual" px = preserved bubble-border strokes inside mask overlap, not text | ✅ 5 lines "এই নামের / একমাত্র / সঠিক / অক্ষর ছিল / "!"" inside bubble; 0 collateral px outside mask | Orphan last line `"!"` (typographic nit) |
| 3 | bubble, spiky shout (box 403,340,204×216) | "MY NAME'S KOGANEI YOU DUMBASS!" | ✅ 82.4% coverage (text-line blobs) | ✅ 502 flagged px = spiky border strokes at mask edge (x≈403–420 / 585–606), borders preserved in inpainted.png — not text residue | ✅ 3 lines centered, conjuncts correct; descenders extend below original text bbox to y≈550 but stay inside bubble | New-text px outside original mask (cluster (419,479)–(463,492) =209 px, (545,486)–(577,493) =110 px) are rendered glyph bodies inside the bubble — benign, not damage |
| 4 | bubble (box 76,361,103×109) | "WHO THE HELL IS THAT PERSON!?" | ✅ 91.2% | ✅ 0 residual px | ✅ "সেই ব্যক্তি কে?" 2 lines, clean fit; 0 collateral | Translation drops "the hell" intensity (MT quality, not render) |
| 5 | bubble over cloud/sky (box 197,672,128×140) | "WHO THE FUCK IS OTEARAH!? DOES THAT BITCH KNOW HIM OR SOMETHING!!?" | ✅ 96.1% | ✅ 14 flagged px = border overlap (318–322, 799–811); cloud texture at bubble edge preserved | ✅ 4 lines fit inside bubble; "OTEARAH" Latin retained per translation.json | ❌ MT garbage: "যৌনসঙ্গম" (= "sexual intercourse") for "fuck"; "এই বেশ্যা তাকে বা কিছু জানেন" garbled word order + wrong honorific register; punctuation spacing "! !" / "! ?" (tokenizer artifact) |
| 6 | rectangular caption box over building (box 101,880,131×204) | "THIS WAS THE RESULT OF MY MISTAKE … MY GIRLFRIEND" | ✅ 98.1% (mask covers whole box incl. border lines) | ✅ box borders reconstructed by LaMa (bottom-border dark px 280 = original 280; left/right/top verified visually in inpainted.png) | ✅ 9 lines, render bbox (113–218, 901–1055) inside interior with ≥7 px side / 16 px top / ~35 px bottom margins; conjunct স্বীকারোক্তি renders correctly | ❌ MT literalism: "she was into me" → "সে আমার ভিতরে ছিল" ("she was inside me") |

### Measurements

- Residual text pixels: **11 px** true original-text residue in final.jpg (specks at (34–47, 370–381), darkest luminance 18/24 — mask-missed glyph tips, region 1 bottom). Inside-mask "residuals" flagged programmatically (32+502+14 = 548 px in regions 2/3/5) were verified at 3x to be **preserved bubble-border strokes under mask overreach, zero actual glyph remnants**.
- Overflow lines: **0**. No rendered line crosses any bubble/box boundary; region 1 has 0 ink px beyond the original note's y-extent (81..379) within its column; region 6 render bbox clears all four borders.
- Color artifacts: **none observable and none possible in this sample** — the image is 100% grayscale (0.000% of pixels with channel spread >30 in both original and final). No halo, no color bleed, no smudge detected around any rendered block; inpainted-vs-original diff outside mask = 4 px total; final-vs-original diff outside mask = 389 px (0.038%), of which the four largest clusters (≤209 px) are new Bengali glyph bodies inside bubble 3 — benign — plus one 11-px residue speck and ≤13-px JPEG edge-noise clusters.
- Box-snap misfires: **0**. No synthetic white box drawn anywhere; all six regions rendered in place over inpainted artwork.
- SFX / non-text artwork: the only SFX-like marks are monochrome handwritten speed-line accents near (660–820, 240–380) — **byte-identical original→final (0 changed px)**; no pink Korean SFX exists anywhere in this sample. SFX non-translation policy respected.
- Mask global coverage: 13.5% of image (136,804 px). JPEG re-encode noise in final: negligible.

### Metadata Verdict

- Actual translation engine: **nllb** (translation.json is correct; metadata.json's `"translation_engine": "manual"` is **wrong**).
- Evidence (machine-translation fingerprints in translation.json content):
  1. R5: "WHO THE FUCK" → "কে ঐ যৌনসঙ্গম" — যৌনসঙ্গম = "sexual intercourse"; a literal noun-swap only an MT lexicon produces. Same line: "DOES THAT BITCH KNOW HIM OR SOMETHING" → "এই বেশ্যা তাকে বা কিছু জানেন! ?" — scrambled argument order and an unwarranted honorific verb (জানেন), a classic NLLB register error.
  2. R6: "ASSUMING THAT SHE WAS INTO ME" → "সে আমার ভিতরে ছিল" ("she was inside me") — word-for-word literalism.
  3. R1: "which is a vowel" → "যা একটি ভোকাল" — ভোকাল ("vocal", e.g. a singer) instead of স্বর ("vowel").
  4. Punctuation spacing artifacts "! !" and "! ?" on every doubled mark — NLLB tokenizer signature.
  5. If these were human post-edits, register/grammar errors of this density would not survive; the owner's own metadata note ("first fresh-run success") describes a pipeline run, not a manual pass.
- Per §8 "Produce natural Bengali translations": **not met at human-final quality** for regions 1, 5, 6 (region 3's "আমার নাম কোগানাই, তুমি বোকা!" is serviceable; regions 2/4 acceptable but flattened).
- Related OCR accuracy finding (§8 "Produce accurate OCR", region 1): the vertical note in original.jpg actually reads "…while **Otearai** is spelt as **おてあらい** and both **"U"** is pronounce as **"I"** which is a vowel", but ocr.json/translation.json record "Otarumi / おたるみ / しゅ / しゅ" — two mis-transcriptions by the `qwen` OCR engine that then propagated verbatim into the NLLB prompt and the rendered region-1 text.
- Secondary metadata nit: metadata.json `source_type` says "color webtoon long strip", but the artifact is a pure-grayscale B/W manga page (0 chroma); sample ID/name should be understood as pipeline-variant labeling, not color content.

### Plain-Text Summary (for GLM-5.3, who cannot see images)

The detection→inpaint→render chain worked on all six regions. Masks fully cover the original text; LaMa left zero glyph remnants inside masked areas (all programmatic "residuals" are bubble-border strokes the mask overlaps, preserved intact); the Bengali renderer produced correctly shaped, non-overflowing text in every region, including the rotated vertical overlay and the 9-line caption box. SFX untouched. The page is presentable at normal viewing zoom. Four concrete, code-actionable defects remain, ordered by severity:

1. Translation quality (regions 1, 5, 6; worst in 5): NLLB output is unusable-as-final for profanity/idiom: at region 5 (box 197,672 → 325,812) the rendered line 1 reads "কে ঐ যৌনসঙ্গম OTEARAH! !" — "যৌনসঙ্গম" (sexual intercourse) is a wrong-register noun for "fuck"; line 3–4 "বেশ্যা তাকে বা কিছু জানেন! ?" has scrambled syntax and an honorific verb. At region 6 (box 101,880 → 232,1084), line 3 "সে আমার ভিতরে ছিল" literally means "she was inside me". At region 1, "ভোকাল" replaces "vowel" (স্বর). Fix locus: translation stage (engine choice, profanity/idiom glossary, or human post-edit pass), not the render stage. Punctuation post-processing should also collapse NLLB's "! !" / "! ?" spacing, and region 2's wrap leaves an orphan line `"!"` (box 218,110 → 305,266) — a min-widow constraint in the line breaker would fix it.
2. CJK fallback font mismatch in region 1 render (x≈22–70, y≈85–375): the retained Japanese terms こがねい / おてあらい( rendered as おたるみ per bad OCR) / しゅ draw at roughly half the Bengali cap height and much lighter weight (mean ink luminance ≈90 vs ≈47.5 for the original note glyphs; surrounding Bengali is near-black). Fix locus: renderer font-fallback stage — scale CJK runs to the Bengali font's x-height/cap-height and use a matching weight (e.g. bold CJK face) so inline Latin/CJK matches the surrounding type.
3. Mask under-coverage at region 1 bottom: glyph tips the mask missed survive as ~11 dark specks (luminance 18–24) at x=34–47, y=370–381 in final.jpg. Fix locus: detection stage — dilate the region-1 mask a few px vertically (or extend the region quad to the text's true bottom ~y=384) so inpainting clears the tips; alternatively a post-render cleanup pass inside the detection box.
4. OCR mis-transcription of region 1 (qwen engine): image says "Otearai / おてあらい" and `"U" … "I"`; ocr.json/translation.json say "Otarumi / おたるみ / しゅ / しゅ". This corrupted both the translation and the rendered note. Fix locus: OCR stage — vertical-text handling for rotated side notes (rotate-then-OCR or a VLM pass), plus a consistency check that cross-references quoted glyph runs.

Cosmetic, non-blocking: panel-border AA edge at x≈75 (y≈120–350) darkened ~2 px where region-1 text strip re-encoded; region-3 descenders extend below the original text bbox to y≈550 but remain well inside the bubble interior. Neither requires action.

### Overall Verdict

**APPROVE_WITH_ISSUES.**

The visual pipeline (detection, masking, LaMa inpainting, Bengali rendering, SFX preservation, boundary respect) passes §8 on this sample and the archive is valid evidence — zero residual glyphs inside masked regions, zero overflow, zero box-snap misfires, zero artwork damage. The issues that block "final quality" are upstream of rendering: NLLB translation naturalness (regions 1/5/6), the CJK fallback font metrics in region 1, the 11-px mask-miss residue at (34–47, 370–381), and the region-1 OCR mis-transcription. metadata.json's `"translation_engine": "manual"` claim is contradicted by the artifact content and should be corrected to `nllb` (a documentation fix in a new metadata revision, since samples/ is immutable evidence). Recommended follow-up: a fix task for translation quality + vertical-note OCR + CJK fallback metrics + mask dilation, then a new sample run archived as S002 for re-review.

---

## MANGABD-003 — PHASE B REVIEW
Date: 2026-09-29
Reviewer: GLM-5.3-Flash (Independent Reviewer)

Scope: independent verification of GLM-5.3's Phase A proposals (agents/GLM_5_3.md "# MANGABD-003 — PHASE A", commit `b9c43a9`) against the actual notebook code and `samples/S001_color_webtoon/` artifacts. Method: fresh cell extraction from the current main notebook (27 cells, byte-identical blob to the MANGABD-002-verified merge), every cited *cell:line* re-read directly, Pillow API behavior tested locally, S001 pixel measurements re-run from the archived artifacts. Proposals only reviewed; NO source code changed; no `samples/` files touched. Citations: *physical-cell:line*.

### V-1 — CJK Fallback Glyph Size/Weight: **CONFIRMED WITH REQUIRED AMENDMENTS**

Verified facts (all checked against the notebook):
- `get_font_fb(size, bold=False)` accepts `bold` and never uses it — `ImageFont.truetype(..., int(size))` unconditionally (12:106–112; byte-identical copy 11:149–155). [FACT]
- The fallback font is the **variable** font `NotoSansJP[wght].ttf` (download URL 12:23) loaded via plain `truetype` → default instance wght=400; `set_variation` occurs **0 times** in the notebook (grep). [FACT]
- Pillow support: `FreeTypeFont.set_variation_by_axes` exists in modern Pillow (verified present and functional in local Pillow 11.3.0; added in the Pillow 8.x line, requires FreeType ≥ 2.9.1 which standard wheels incl. Colab ship). On a **static** font it raises `OSError` (tested locally with DejaVuSans) — the proposal's try/except is therefore mandatory and present. Colab's current Pillow (≥9.x) supports it. [TEST RESULT]
- `fit_font_size` calibrates with the **main font only** (10:415/416/424) and the vertical path calls it with **swapped dims** — `fit_font_size(text, h, w, ...)` at 12:120 (target_width=h=298, target_height=w=61). [FACT]
- Vertical predicate `w < 90 and h > 2*max(1,w)` (12:146) — region 1 (61×298) qualifies; overlay → `bold=False` (12:147). [FACT]
- Every vertical run is drawn with `fill=text_color+(255,)` and **no stroke_width** (12:134), while the core path gives overlays `stroke_width=1` (10:74, 10:523, 10:578–579). The layer is then rotated with **BICUBIC** resampling (12:135–136). [FACT]
- S001 final.jpg region 1 re-confirmed from the archived artifacts: CJK runs at ~50% of Bengali visual height; mean ink luminance ≈90 (pale) vs 47.5 for the original note's glyphs; residue specks still at (40–44, 375–378), min lum 18.0. [TEST RESULT — this reviewer]

PM's nuance — **upheld**: with `bold=False` for S001's overlay, the ignored-`bold` bug is **not operative** in this sample; the measured paleness is produced by (a) wght=400 JP hairlines, (b) no stroke on vertical runs, (c) BICUBIC rotation softening, plus (d) the em-ink size gap. The bold fix remains valuable as a latent fix (a vertical sfx/narrator region would pass `bold=True` and still render Regular) and as the carrier of the wght knob — but it is not the S001 culprit and the Phase A text correctly does not claim it is. Because BICUBIC softening persists after the fix, the §C.4 acceptance target (ink luminance ≤ 60) may require `fallback_font_wght=700` and/or `fallback_cjk_stroke=2` at S002 calibration — both are already config knobs, so no code change is needed, only tuning.

**Required amendments (blockers for Phase C implementation):**
1. **Scale-vs-fit overflow (PM's question) — the risk is real.** The proposal scales fallback runs at draw time (`get_font_fb(int(size*_fb_scale))`) **after** `fit_font_size` calibrated `size` using main-font metrics only. Per-line width is re-measured with the scaled fonts (centering self-adjusts), but there is **no re-check of the line total against the available column length** (`int(h) - 2*padding`). A kana share of ~11% (S001 R1) grows the longest line ~+2–3% — enough to clip the line-end glyph when the binary search finished tight against `available_width`; a kana-heavy note (+10–15%) clips hard at the 298-px layer boundary (negative `lx` / canvas-edge cut). **Amend:** after computing `total` with scaled fonts, if `total > int(h) - 2*padding`, retry the line at stepwise-reduced scale (e.g. 1.12 → 1.0) — or fold the fallback scale into `fit_font_size`'s measurement loop (scale-then-fit order).
2. **Baseline misalignment.** All runs share the top-left anchor `ly` (12:134). A 1.25× CJK font has a larger ascent, so its ink shifts DOWN by ~0.2 em relative to the line's Latin/Bengali ink, and its ink bottom can approach the next line box (lh = 1.18× main em, 12:121). Phase A's "65–70% em < 1.18× em" arithmetic holds for kana mid-band ink but ignores the anchor offset and is unproven for full-height kanji. **Amend:** baseline-align fallback runs using `f.getmetrics()` (draw at `ly_fb = ly + ascent_main − ascent_fb`), which fixes both the visual misalignment and the collision question in one move.
3. Cosmetic: the proposal says "two config setdefaults" but lists three knobs (`fallback_font_wght`, `fallback_cjk_scale`, `fallback_cjk_stroke`).

### V-2 — Mask-Miss Residue / Vertical Band: **CONFIRMED**

Verified facts:
- The proposal's insertion point is in the **live** fresh-Run-All mask path: `build_page_text_mask` (6:769–834), raw-mask branch, after the region clip (6:815–826) and before `return mask` (6:827); the function is called from `detect_page` (6:1207) and the mask saved as the artifact (6:1214). [FACT]
- **kill_residual is dead in the effective path — verified end-to-end.** Defined 3× (11:99, 13:4, 14:4 "v3"); called only at 11:197 and 13:42, both inside cells 11/13's `run_inpaint_render_all` wrappers. `run_inpaint_render_all` is defined 5× (11:190, 12:155, 13:35, 15:678, 23:71) — the **last definition (cell 23:71–84) is plain** (`sync_translate_stage` + `run_inpaint_all` + `run_render_all`, zero sweep calls), and the Control Studio 🎨 button calls `run_inpaint_all` + `run_render_all` directly (25:363–365). No sweep, box-restore, or mask filtering runs in the S001 flow. [FACT]
- Cell 14's v3 is structurally blind to this residue, as claimed: `uniform_frac > 0.8` solid-box gate (14:23) fails on a dense text column; `margin=5` strips the crop's border rows (14:28–29); the crop is box-limited (14:16) so y ≥ 380 is unreachable (quad bottom 379). [FACT]
- Residue re-measured independently from S001 artifacts: **11 px < lum 160, min luminance 18.0, concentrated at (40–44, 375–378)** (window 34–47 × 370–381). The proposed band [y+h−10, y+h+10] = **[369, 389]** covers every speck with ≥6 px margin. [TEST RESULT — this reviewer]
- Safety properties verified: config-gated (`mask_vpad_vertical` setdefault 10); predicate `rw < 90 and rh > 2*max(1,rw)` is **byte-identical to the live vertical-renderer predicate** (12:146), so bubble masks are untouched; the band is confined to the region's own x-range (10..71 for R1 — the panel border measured at x≈72–76 stays outside); and the band bottom `y+h+10` exactly equals cell 9's re-clip bound (`mask_clip_padding` = 10, 9:76 + 9:234–236), so the extension survives the inpaint-stage re-clip with no protrusion. Band area ≈ 20 rows × 61 px ≈ 6.7% of the R1 region. [FACT + TEST RESULT]
- Explicitly rejected alternatives (global dilation radius, lower CTD threshold, `redilate_artifact_mask`) are indeed the historical over-dilation class; `redilate_artifact_mask=False` is what cells 11/12 enforce (11:13/12:13) and cell 9 honors (9:302–303). [FACT]

No amendments required. One implementation note: the band is added **after** cell 6's clip, so it is not re-clipped in cell 6 itself — with the default vpad=10 this is exactly safe (cell 9 re-clips at +10), but if the Owner ever sets `mask_vpad_vertical > 10`, the excess is silently trimmed at cell 9; document the knob's effective ceiling (= `mask_clip_padding`) in the config comment.

### V-3 — Vertical-Note OCR: facts **CONFIRMED**; Layer 1 selection criterion **CHALLENGED**; Layer 2 **CONFIRMED**

Verified facts:
- ocr.json region 1: `confidence 0.95, status "ok", warnings []` — confidently wrong, exactly as Phase A states. [FACT]
- Geometry: region 1 `angle=0.0` → the rotated-crop branch (7:346–347, |angle|>5) never engages; the strip is passed upright; the prompt (7:75–85) is English-only extraction with no vertical/mixed-script guidance; the recognize call site is 7:392–394 (`qwen.recognize(preprocessed, prompt=prompt)` — the `prompt=` kwarg already exists, so Layer 1's calls are API-compatible). [FACT]

**CHALLENGED — the best-of-3 selector cannot select.** `score = confidence + language_score.en` is computed from **two text-derived heuristics, not model certainty**:
- `confidence` comes from `_estimate_ocr_confidence` (5:281–314): 0.45 base + 0.15 (len≥2) + 0.10 (len≥5) + 0.20 (en≥0.6) + 0.05 (no bracket chars), **capped at 0.95** — any ≥5-char Latin-dominant read saturates at 0.95 (all six S001 regions scored exactly 0.95 — the metric is saturated).
- `language_score` comes from `_language_scores` (5:247–278), which counts only ASCII-alpha vs Bengali characters — **kana are invisible to it** (S001 R1 contains kana yet scores en=1.0).
Consequences: (1) the correct rotated read, the wrong upright read, and even an upside-down Latin-looking garble all saturate at score ≈ 1.95 — the two metrics are blind to the exact failure mode (kana romanization); (2) `max()` over the list `(upright, rot_cw, rot_ccw)` resolves every tie toward the **first element = upright = the S001 failure mode**. As written, Layer 1 would spend 3 VLM calls and return the same misread. What could make a rotated misread win (PM's question): the tie-order above, an upright hallucination that drops kana (pure-English output scores the same 1.95), and the bracket-penalty being the only effective discriminator in practice.

**Required amendment (Layer 1):** (a) when the vertical predicate fires, **exclude the upright read from the candidate set** (2 VLM calls, not 3 — and the known-failure orientation can no longer win); (b) make the tie-break explicit: strict-`>` comparison starting from `ROTATE_90_CLOCKWISE`, so a rotated candidate always wins ties and the chosen orientation is deterministic; (c) append the chosen orientation + all candidate scores to the result (e.g. into `warnings` / the ocr sidecar) so S002 evidence can audit the selection; (d) keep Layer 2 as the hard net regardless. Optionally reward kana preservation in the score (kana-char ratio), since the vertical prompt now demands exact kana transcription — but (a)–(c) are the mandatory minimum.

**Layer 2 CONFIRMED non-blocking:** severity "warning" flows through `add_quality_issue` (16:165–187) into `manual_review_flags` only; `SEVERITY_WEIGHTS["warning"]=7` is a **score penalty** (16:73–77, 16:694–700), never a raise/abort; the QA runner wraps per-page inspection in try/except (16:823–830); and `manual_review_flags`/`quality_warnings` have **zero consumers outside cell 16** (grep across all 27 cells) — the flag cannot auto-fail or block the pipeline. [FACT]

Two factual amendments for Layer 2's implementation: (a) Phase A claims "`re` is already imported in cell 16" — **cell 16 contains no imports**; `re` is imported in cells 3/7/8. Runtime-safe under Run All order, but the snippet should add `import re` to be cell-standalone-safe and the claim corrected. (b) The translation_df-branch insert (~16:431) has no `region` object in scope — region geometry must be resolved from the detection records/manifest there; the artifact branch (~16:365) has it via `entry["region"]`.

### V-4 — Metadata rev2 + Manual Workflow: rev2 **CONFIRMED**; Edit A/B **CONFIRMED**; Edit C **CHALLENGED**

- **V-4a CONFIRMED.** The rev2 JSON matches Owner policy C.1 on all five points: engine=`nllb` ✓, `source_type: "B/W manga page"` ✓, `naming_note` documents the folder-name discrepancy ✓, folder NOT renamed (`sample_id` and path unchanged) ✓, rev1 preserved as `metadata.rev1.json` ✓. Provenance fields (`captured_at`, `notebook_commit: 9f4d82a`, `pipeline_variant`, `owner_notes`) are carried over correctly; the README one-liner satisfies the "document in metadata/README" clause. Documentation-only; zero risk. [FACT]
- **Wire-format surface verified — "2 parsers + 1 builder" is accurate:** builder `export_ai_text` (8:870–973; line templates at 8:939/8:941); parsers `parse_ai_text` (8:812–867, regex 8:843) and `_parse_ai_text_local` (22:42+, **independent regex at 22:70**, used whenever `parse_ai_text` is missing or raises — 22:203–209); parse consumers also at 8:999 and 19:44; appliers `apply_manual_translation` (8:1023–1092) / `_apply_translations_fallback` (22:267+). [FACT]
- **Edit A (unparsed-line report) CONFIRMED** — this is precisely the "silent line-loss visibility fix": parse behavior unchanged (8:843–846 skip verified), losses only counted and reported; the `("_unparsed", 0)` sentinel cannot collide with real keys (region ids ≥ 1) and empty-sided entries cannot be applied by the 22:220–233 loop. Wire format untouched. [FACT]
- **Edit B (pre-render coverage report) CONFIRMED** — report-only, reads existing `translation_df`, no format impact. [FACT]
- **Edit C (`|TYPE` header) CHALLENGED — violates the stated constraint and breaks the second parser as specified.** It changes the **builder's** emitted header (`[page:id|TYPE]`), i.e. it DOES alter the ai.Text wire format (additively, but materially for every downstream consumer), and the proposal amends **only** `parse_ai_text`'s regex. `_parse_ai_text_local`'s regex `^\[([^:\]]+):(\d+)\]\s*(.*)$` (22:70) **cannot match** `[02.jpg:1|overlay]` — after `(\d+)` consumes `1`, the next char is `|`, not `]`; the whole line fails and is **silently skipped** — reintroducing the exact silent-loss class Edit A fixes, in the fallback parser. Cell 19:44 and the cell-8 upload path (8:999) inherit the fixed parser, but any session where the fallback engages loses every line. **Amendment:** under the PM constraint ("wire format unchanged; silent line-loss visibility fix only"), **defer Edit C** to its own Owner-approved item; if the Owner still wants it, it must (i) update BOTH regexes identically (8:843 + 22:70), (ii) update the header docs (8:907–913) and the cell-8 parse tests (8:1549–1586), and (iii) re-verify 19:44/8:999 paths. [FACT + TEST RESULT]

### V-5 — Provider-Flexible Translation: architecture **CONFIRMED**; 2 required amendments; LiteLLM rejection **CONFIRMED**

Verified facts:
- Current state matches the proposal's premises: dispatcher branches gemini 8:747 / chatgpt 8:754 / nllb 8:761 / else→unknown 8:768–770; `switch_translator` hardcoded list 8:783; UI options manual/gemini/nllb at 25:276; `build_translation_prompt` used by gemini (8:448) and chatgpt (8:496) only — **NLLB passes raw text** (no prompt-builder call in 8:537–666) — so the prompt upgrade cannot perturb NLLB. [FACT]
- Secrets hygiene: `MANGABD_SECRETS` initialized from env/Colab userdata (1:383–430), UI writes into it (25:343), the adapter reads only from it, and `save_config`'s sanitizer (1:523–558) recursively strips dict keys containing "api_key"/"token"/"secret"/"password". The registry itself stores **no keys** — only base_url, model name, and an env-var *name*. [FACT]
- The OpenAI SDK is already a dependency (8:487) and the adapter mirrors the proven chatgpt call shape (8:487–519) with base_url/model parameterized; all four base_urls are correct OpenAI-compatible endpoints (OpenRouter `/api/v1`, DeepSeek root, DashScope compatible-mode, Ollama `/v1`). [FACT]
- **LiteLLM rejection CONFIRMED as sound**: dependency-tree weight directly threatens the fresh-Run-All reliability MANGABD-002 just stabilized, and model-string routing would move provider knowledge out of CONFIG; the ~35-line native adapter keeps the swap point (one function) intact. [ASSESSMENT]
- Dispatcher change is additive for existing engines: the `elif` inserted before the else leaves manual/gemini/chatgpt/nllb branches untouched, and no provider key collides with an existing engine name. `clean_translation`'s punctuation normalizer is shared by all auto engines (intended) while the manual path (`apply_manual_translation`) does not call `clean_translation` — manual text is never auto-edited. `translator_model` in the record dict (8:1128–1136) is a one-line additive sidecar field. [FACT]

**Required amendment 1 — the dispatcher snippet crashes as written.** `translate_with_retry` has signature `(translate_func, text, region_type="bubble")` (8:371) and invokes `translate_func(text, region_type)` **positionally** (8:390) — it accepts no `engine` kwarg and forwards none. The proposal's `translate_with_retry(translate_with_provider, text, region_type=region_type, engine=engine)` raises `TypeError` on the first provider call; even without the crash, the engine would silently stay `"openai"` for every provider. **Fix:** bind the engine via closure or partial — e.g. `translate_with_retry(lambda t, rt: translate_with_provider(t, rt, engine=engine), text, region_type=region_type)` — or generate per-provider thin wrappers analogous to the existing per-engine functions. Do NOT widen `translate_with_retry` with **kwargs (shared by all engines; unnecessary blast radius).

**Required amendment 2 — the sanitizer will eat the registry's key-name field.** `save_config` strips any dict **key** whose name contains the substring `api_key` (1:534–546). The proposed field name **`api_key_env` contains `api_key`** → on every `save_config()` (called at cells 2/4 and config writes) the entire `api_key_env` entry is removed from the persisted config; after the next fresh session loads the saved config, the adapter finds no env-name mapping and falls into the placeholder-key branch → guaranteed auth failures that no one will connect to the sanitizer. **Fix:** rename the registry field to something without the forbidden substrings — `key_env` is clean — and update the adapter (`prov.get("key_env")`) accordingly. Do NOT weaken the sanitizer. Also recommended (non-blocking): add the new provider env names to `SECRET_SOURCES` (1:407–411) so Colab userdata bootstraps them exactly like gemini/openai keys.

### BATCH PLAN REVIEW (batch1 = V-4a + V-2 + V-1; batch2 = V-3; batch3 = V-5)

**No regression coupling that breaks the single-hunk audit — CONFIRMED, with notes.**
- Cell sets per batch: batch1 = {samples docs, cell 6, cells 11+12}; batch2 = {cells 7+16}; batch3 = {cells 8+25}. **Zero cell overlap across batches** — no batch mixes changes to the same cell, so every cell carries at most one logical change and the per-cell single-hunk audit convention (MANGABD-002 precedent) survives. [FACT]
- Note 1 (mirror discipline): V-1 edits `get_font_fb`/`_qc_render_vertical` in **both** cells 11 and 12 (the shadowed copy must not resurface — the Phase A extraction shows the two copies byte-identical today, 11:149–155 ≡ 12:106–112). The batch-1 audit must therefore include a **mirror-equality check** across the two cells in addition to the per-cell hunk audit; a fix applied to only the live cell 12 would leave a stale shadow that resurfaces if cell order ever changes.
- Note 2 (attribution coupling, ordering): V-1 and V-2 both alter S001-region-1 pixels in S002, so a single S002 run attributes R1 improvements **jointly** to batch-1 items; if per-fix attribution is ever needed, an intermediate verification run between V-2 and V-1 would be required — not recommended; the §C.4 acceptance targets are already formulated jointly and per-fix attribution has no decision value. No ordering dependency exists between V-4a/V-2/V-1 (disjoint cells; distinct config keys; `setdefault` semantics are order-safe with old saved configs).
- Note 3 (cache interaction): batch2's OCR changes and batch3's sidecar schema addition only take effect for stages that actually re-run — a warm session with `qa`/`ocr` stages marked done will serve cached artifacts unless forced (`force=True` / `reset_page`); the S002 plan is a fresh Run All and is unaffected. Verify warm-session behavior with explicit force during Phase C testing.
- Note 4 (non-interaction): batch2's cell-16 flag reads detection geometry, not the translation sidecar schema, so batch3's `translator_model` addition cannot break it regardless of landing order. The proposed order (1→2→3) is also risk-ordered correctly (docs+geometry → OCR behavior → translation architecture).

### OVERALL VERDICT

**APPROVE_WITH_CHANGES.**

All five Phase A investigations are factually sound — every cited cell:line was re-verified against the notebook and every pixel claim re-measured against the S001 artifacts, with only one trivial factual slip (`re` import location). The architecture choices (live-path V-2 band, native OpenAI-compatible adapter, LiteLLM rejection, immutability-preserving metadata rev2) are endorsed. Phase C implementation is approved **subject to the required amendments**: (1) V-1 — post-scale line-width re-check (or scale-then-fit) + baseline alignment via font metrics; (2) V-3 Layer 1 — drop the upright candidate when the vertical predicate fires, explicit rotated-first tie-break, log chosen orientation + scores; (3) V-4b — defer Edit C (or amend to both parsers + docs + tests); (4) V-5 — `key_env` field rename (sanitizer compatibility) + closure-bound `engine` in the retry call. Items without amendments (V-2 entire, V-4a, V-3 Layer 2, V-5 architecture) may proceed as proposed. Per DECISION.md §C.3, Owner approval per V-item remains the gate before any Phase C code lands; this review discharges the Phase B verification step of that gate.

# MANGABD-003 — PHASE D VERIFICATION — BATCH 1 (GLM-5.3-FLASH, Independent Reviewer)

**Date:** 2026-09-30 · **Under review:** commit `2066dea` ("WIP: MANGABD-003 Phase C Batch 1 — awaiting Flash Phase D verification"), branch `mangabd-003-batch1` · **Base:** main @ `c2e5754` (TASK_003.md task book commit; merge-base = base, linear, single commit) · **Discipline:** TASK_003.md "VERIFICATION PROTOCOL (Phase D)" + RULES OF ENGAGEMENT 2–4 + DECISION.md §C gating. **No source code modified; no amend; no merge.**

**Method:** every check re-executed against the pushed bytes of `2066dea` (git-blob extraction, AST spans, byte compares, and a fresh runtime harness exec'd from those bytes). GLM-5.3's self-report (GLM_5_3.md T3.20–T3.24) was read for claims inventory only and NOT trusted; all numbers below are independently re-derived. Verification scripts: `m003b1_d1_audit.py`, `m003b1_d3_mirror_v1.py`, `m003b1_d6_v4a.py`, `m003b1_d8_runtime_v1v2.py`, `m003b1_d8_runtime_v4a.py`, `m003b1_d9_meta_ast.py` (reviewer sandbox), plus the MANGABD-002 Phase D instruments `m002_sim_v2.py` / `m002_flash_repro.py` re-run against this branch's notebook.

## PD.1 — DIFF & SCOPE AUDIT — PASS (35/35)

- **Topology:** HEAD `2066dea27864407e…`, parent = `c2e5754…`, `rev-list --count base..HEAD = 1`, merge-base = base. Linear, single WIP commit. [FACT]
- **numstat exact:** notebook +142/−21; GLM_5_3.md +50/−2; samples/README.md +2/0; samples/S001_color_webtoon/metadata.json +6/−3; metadata.rev1.json +9/0 (NEW). Total 5 files, **+209/−26**. [FACT]
- **Modes/renames:** exactly 4 M + 1 A; `create mode 100644` for the new file; zero D/R/C, zero mode-change lines; all five blobs 100644. [FACT]
- **Secret scan:** all 209 added lines scanned (ghp/github_pat/sk-/AKIA/AIza/hf_/PEM/bearer/xox/glab patterns) — **0 hits**. [FACT]
- **Changed cells exactly {6, 8, 11, 12, 22}** (source-field compare AND full-object compare agree; only `source` changed in every edited cell). **The other 22 cells byte-identical to main** — including Batch 2/3 cells {1, 7, 16, 25} (their content is NOT on this branch, per the PM's scope limit) and MANGABD-002 artifacts cells 14/26 (guard block 40–46 and cell-26 bundle verbatim). [FACT]
- Factual precision on GLM's report: it says "the other 23 cells byte-identical" — **the correct count is 22** (27 − 5). Arithmetic slip in prose only; the byte-identity claim itself holds for every unchanged cell. → Note N-A.

## PD.2 — TRANSPLANT FIDELITY vs the Phase-E-approved bytes — PASS

- Cells 6, 11, 12: source byte-identical to `f58cd3c` (branch `mangabd-003-phase-c`), sha16 `6db80c10…` / `8f17b472…` / `d6178521…`. The V-2 and V-1 changes on this branch are therefore the exact bytes that carry Phase E E3/E4 verification. [FACT]
- samples/S001_color_webtoon/metadata.json and samples/README.md byte-identical to `f58cd3c`; metadata.rev1.json byte-identical to main's rev1 metadata blob (sha16 `eabe49b7…`, matches Flash PE.1). Both JSONs re-parse. [FACT]

## PD.3 — MIRROR DISCIPLINE (Cells 11 & 12) — PASS

The TASK_003.md Rule-of-Engagement-2 check, re-derived on this branch:

- **`get_font_fb`: 690 chars, sha256-16 `a7d2d5bd61309c78`, byte-identical cells 11↔12.** **`_qc_render_vertical`: 2267 chars, sha256-16 `e27f769797d8ff4f`, byte-identical cells 11↔12.** Both shas equal the Phase E E3 record — no stale shadow, no drift. [FACT]
- Runtime mirror parity (RT-4): both cells' `_qc_render_vertical` exec'd in isolated namespaces with identical inputs → **output images byte-identical** (`tobytes()` equal). [TEST RESULT]
- The three module-level knob registrations (`MANGABD_CONFIG["rendering"].setdefault("fallback_font_wght", 600)` / `("fallback_cjk_scale", 1.25)` / `("fallback_cjk_stroke", 1)`) present in BOTH cells. [FACT]

## PD.4 — V-1 AMENDMENTS — PASS

**Amendment 2 — baseline alignment (headline check).** Shipped code: `asc_main = get_font(size, bold).getmetrics()[0]` … `ly_run = ly if im else ly + asc_main - f.getmetrics()[0]` — main runs keep the top-left anchor; fallback runs shift by the ascent difference of the ACTUAL drawn (scaled) fallback font, exactly the prescribed `ly_fb = ly + ascent_main − ascent_fb`. Runtime proof (RT-2, recorded draw calls on the pushed bytes): fallback run y − main run y = 4 − 15 = **−11 = asc_main − asc_fb = 21 − 32** (exact integer match). [TEST RESULT]

**Amendment 1 — scale-then-fit / overflow ladder (headline check).** Shipped code: `_measure_line(runs, scale)` measures the line WITH scaled fallback fonts; `while any(not im for _, im in runs) and total > int(h) - 2*padding and scale > 1.0: scale = 1.12 if scale > 1.12 else 1.0; widths, total = _measure_line(runs, scale)` — re-check against `int(h) − 2*padding`, stepped downgrade 1.25→1.12→1.0, re-measure INSIDE the loop, drawn widths taken from the post-ladder measurement (`zip(runs, widths)` after the ladder). Runtime proof (RT-1, 11-glyph CJK line in a 61×298 column): independent pre-measure confirms overflow at 1.25×; the pushed renderer requested fb size 27 (=1.25×22) then **24 (=1.12×22) for the final draw**; post-ladder width 264 ≤ limit 290. [TEST RESULT]

- **Residual (N-F, non-blocking):** a line that still overflows at the 1.0 floor draws at 1.0 (e.g. CJK-only lines that `fit_font_size` under-measures because it calibrates on main-font metrics — the very defect the ladder mitigates). The amendment's letter (stepwise retry with 1.0 floor) is fully implemented; the fold-into-fit alternative was optional and not taken. Accepted as designed.
- Knobs/stroke/wght: `sw = 0 if im else _fb_stroke` (stroke on fallback runs only), `stroke_fill` wired; `fallback_font_wght` default 600 with `if bold: wght = max(wght, 700)`; `set_variation_by_axes` wrapped in an OSError guard — **try/except delta vs main inside the mirror block = exactly 1** (main's `get_font_fb` truetype-fallback try is pre-existing). BICUBIC rotate and swapped-dims canvas `(int(h), int(w))` preserved. Variable-font wght accepted at runtime on NotoSansSC[wght] (RT-3). [FACT + TEST RESULT]

## PD.5 — V-2 (CELL 6 VERTICAL BAND) — PASS

- Band sits inside `build_page_text_mask` **after** the `mask_clip_to_regions` clip and **before** `return mask`; `detection_cfg.setdefault("mask_vpad_vertical", 10)`; `if vpad > 0` gate; two `cv2.rectangle` tip bands clamped via `max(0, …)`/`min(h, …)`; ceiling comment documents the effective cap = `mask_clip_padding` (cell-9 re-clip). [FACT]
- **Predicate on REGION dims:** `rw, rh = int(region["width"]), int(region["height"])` then `if rw < 90 and rh > 2 * max(1, rw):` — region dims, not crop dims, per the Phase B requirement. The renderer-side predicate (`w < 90 and h > 2*max(1, w)`, cells 11/12, 2 sites each, expression-identical across the mirror) is **semantically identical** (var-rename + whitespace only) — carried from Phase E N2; the shipped comment's "byte-identical" wording is imprecise. → Note N-B. [FACT]
- Runtime (RT-5/RT-6, band block exec'd verbatim): 61×298 region (S001 R1 shape) → bands set at BOTH column tips, clamped to image bounds, mid-column untouched; 100×300 → predicate silent, mask untouched; vpad=0 → no band; vpad=50 → extends, clamped, no OOB (ceiling is downstream, as documented); setdefault never overrides an existing knob value. [TEST RESULT]

## PD.6 — V-4a FRESH EDITS (CELLS 8 & 22 — first-time implementation) — PASS

**Cell 8 — Edit A (sentinel).** Diff vs main is **+15/−0 lines, all inside the `parse_ai_text` span**: docstring note, `unparsed = []` collector, `unparsed.append(line)` at the former silent skip (`if not match: continue` preserved), and the sentinel block — **conditional** (`if unparsed:`), added AFTER the parse loop, payload `{"original_text": "", "translated_text": "", "unparsed_lines": unparsed}` under key `("_unparsed", 0)`. Zero removed lines (pure insertion — parse behavior otherwise unchanged), zero V-5 identifiers anywhere in the diff (no engine/registry/provider residue in cell 8). [FACT]

**Sentinel safety — every consumer of `parse_ai_text` traced and exercised:**
- cell-22 `apply_translations_from_text`: reads the sentinel explicitly (`parsed.get(("_unparsed", 0))` + `isinstance` guard); its own `parsed.items()` loop safely falls through the sentinel's empty sides (both branches require non-empty text); printed parsed-count **excludes** the sentinel (`len(parsed) − (1 if unparsed_lines else 0)`). [FACT + TEST RESULT RT-12]
- cell-19 `apply_translations_from_ai_file` (unchanged bytes): iterates `parsed.items()`; sentinel has empty original/translated → neither branch fires → never enters the apply dict. Only impact: the pre-existing `🔎 Parsed entries` print includes the sentinel (+1) — cosmetic. → Note N-C. [FACT]
- cell-8 `translate_manual_upload`: `translations.update(parsed)` passthrough into the df-row-driven `apply_manual_translation` (byte-identical to main; looks up only `(page, region_id)` keys from df rows) — sentinel never looked up; the `✅ Parsed … entries` print is +1 cosmetic (N-C). [FACT]
- cell-8 module self-tests: samples contain zero unparsable lines → no sentinel → `len(parsed) == 3` regression holds (RT-9). [TEST RESULT]
- Degenerate crafted line `[_unparsed:0] …`: alone → survives as a normal entry (benign); with junk present → shadowed by the sentinel (benign, no crash). Standard flow cannot produce it (export emits real page filenames + df ids). → Note N-D. [TEST RESULT RT-10/RT-11]

**Cell 22 — Edit A report + Edit B coverage.** Touched lines (29) ALL inside `apply_translations_from_text`: (a) report block prints `⚠️ N unparsed line(s) …` with ≤3 previews (60 chars); (b) Edit B coverage after the apply count and before the next-command hint: iterates `translation_df`, skips empty originals and the six special markers (same set as `is_special_marker`), flags rows failing `_validate_bengali_local`, prints the `⚠️ M of T regions …` list (≤10) + render-safety hint. Report-only — no df mutation, no wire-format change, no new failure path (no `translation_df` reassignment). End-to-end runtime (RT-12, real `parse_ai_text` + real `apply_manual_translation` on a synthetic 4-row df): applied=2; warning printed with the junk line; `Parsed entries: 2` (sentinel excluded); coverage flags exactly `01.jpg:4`; **[SFX]-original row NOT flagged**; df rows 1–2 updated with engine=manual, row 4 untouched; `save_translation_df` called once. [TEST RESULT]

**Edit C DEFERRED — proven absent.** Parse regex line byte-identical to main (`^\[([^:\]]+):(\d+)\]`); zero `|TYPE` occurrences in cells 8/22; `_parse_ai_text_local` AST-identical to main (its path degrades to no sentinel report — RT-13: fallback parser applies 2/2, no warning, no crash). `export_ai_text`, `apply_manual_translation`, `build_translation_records_from_df`, `translate_manual_upload` all byte-identical to main. [FACT + TEST RESULT]

## PD.7 — FRESH-RUN REGRESSION (TASK_003 protocol item 1) — PASS

- **`m002_sim_v2.py` (fresh-kernel AST replay) on the Batch-1 notebook: abort-class SITE count = 0** (1773 module-level calls mapped; kill_residual/run_inpaint_render_all def sites all present in the 11→12→13→14→15→23 timeline). **Calibration intact:** the same instrument on the pre-002 base (`base@aabc592`) reports exactly 1 site at cells[14]:40 (`run_inpaint_all`) — the MANGABD-002 Phase D result, so the 0-site result is meaningful. [TEST RESULT]
- **`m002_flash_repro.py` (guard-logic equivalence, verbatim pushed bytes) on the Batch-1 notebook: ALL 9 EXPECTED-MATRIX CHECKS PASS** — S1 baseline NameError reproduced; S3/S6 fresh+guarded OK-with-skip with ZERO mutations (skip banner in both); S5 mutate-then-crash with persisted mutations reproduced; S2==S4 call-sequence identical (`force=True`, `require_translation=False`). Guard behavior is bit-for-bit the MANGABD-002-verified matrix. [TEST RESULT]

## PD.8 — RUNTIME HARNESS (reviewer's own, 30 checks) — PASS (14/14 + 16/16)

| # | Check | Result |
|---|---|---|
| RT-1 | ladder fires on overflow; 1.25× attempted (27) → 1.12× drawn (24); post-ladder width 264 ≤ 290 | PASS |
| RT-2 | baseline: fb_y − main_y == asc_main − asc_fb (exact, recorded draws) | PASS |
| RT-3 | wght accepted on variable font; bold/regular cached distinctly | PASS |
| RT-4 | mirror runtime parity: cell-11 vs cell-12 renders byte-identical | PASS |
| RT-5 | band: 61×298 fires (both tips, clamped); 100×300 silent | PASS |
| RT-6 | vpad=0 gate; vpad=50 clamped; setdefault semantics | PASS |
| RT-7/8/9 | sentinel lifecycle: mixed → exact junk list; all-valid → none; self-test sample → len==3 | PASS |
| RT-10/11 | crafted `[_unparsed:0]` edge → benign in both shapes | PASS |
| RT-12 | end-to-end apply: warning, count-exclusion, df-driven apply, coverage flags, [SFX] skip | PASS |
| RT-13 | fallback-parser path: applies, no sentinel report, no crash | PASS |

Sandbox boundary (carried from Phase E N4 → N-E): fonts stubbed to local files (DejaVu main, variable NotoSansSC fallback); the notebook's production font URLs, live Colab Pillow, and the full pipeline remain Owner-side validation.

## PD.9 — METADATA REV2 + FULL AST SWEEP — PASS (10/10)

`metadata_revision: 2`, `translation_engine: "nllb"`, `source_type: "B/W manga page"`, `naming_note` + `revision_note` present; `metadata.rev1.json` retains the original values (engine "manual", "color webtoon long strip"); README carries the naming-provenance pointer; **S001 directory NOT renamed**. All 27 cells AST-parse on the pushed bytes. [FACT]

## NOTES (all non-blocking)

- **N-A** — GLM_5_3.md prose slip: "the other 23 cells" → 22. Byte-claims unaffected.
- **N-B** — cell-6 comment "predicate byte-identical to the live vertical renderer" is semantically true, byte-imprecise (rw/rh vs w/h + whitespace). Phase E N2 adjudication carried forward; behavior verified identical over the same region population.
- **N-C** — pre-existing count prints (+1 with sentinel present): cell-8 upload prints, cell-19:46. Cosmetic; cell-22's new print correctly excludes the sentinel. A strict end-state fix would be a new Owner-approved item (same class as PE.7).
- **N-D** — sentinel key collision edge (`[_unparsed:0]` hand-written): benign in all traced paths; unreachable from the export flow. GLM's "(ids >= 1)" rationale is conventional (df ids are 1-based in practice), not enforced — acceptable given benign failure modes.
- **N-E** — sandbox boundary: live Colab validation (production fonts, SECRET_SOURCES bootstrap, full pipeline) remains Owner-side; recommended during the S002 acceptance run.
- **N-F** — ladder floor residual: lines overflowing even at 1.0 draw at 1.0 (re-wrap out of scope of the approved amendment; fold-into-fit alternative not taken).

## OUTSTANDING (per TASK_003 protocol, not satisfiable in this sandbox)

**S002 visual acceptance** (protocol item 2) — a fresh pipeline run archived under `samples/S002_…/` proving residue/CJK-size/OCR improvements. Requires the live Colab environment (Owner-side). This sign-off discharges the code-level Phase D; **merge to main should remain gated on the Owner's S002 acceptance**, per the same deferred-live-items structure as MANGABD-002 Phase D.

## OVERALL VERDICT

**PHASE D APPROVED.**

- **batch1 / V-4a (Edit A + Edit B, Edit C deferred): PASS** — first-time implementation verified statically and at runtime; sentinel safe in every consumer; wire format untouched.
- **batch1 / V-2 (cell-6 vertical band): PASS** — live path, region-dims predicate, knob + documented ceiling; runtime-verified firing population.
- **batch1 / V-1 (cells 11/12 CJK fallback): PASS** — mirror discipline held byte-for-byte (both shas == Phase E record); baseline alignment exact at runtime; overflow ladder steps 1.25→1.12→1.0 with in-loop re-measure.
- Scope: single commit on the task-book base; changed cells exactly {6, 8, 11, 12, 22}; Batches 2/3 provably absent (cells 1/7/16/25 byte-identical to main); MANGABD-002 artifacts verbatim; zero required fixes; 6 non-blocking notes.
- **Gating:** per DECISION.md §C and the PM relay — GLM-5.3 must NOT amend this commit or merge until the Owner accepts this sign-off; S002 visual acceptance remains the merge gate. Batches 2/3 remain unauthorized on this branch; the Phase-E-approved bytes on `mangabd-003-phase-c @ f58cd3c` stay available for verbatim transplantation when authorized.

# MANGABD-003 — S002 BATCH1 ACCEPTANCE MEASUREMENT (GLM-5.3-FLASH, Independent Reviewer)

**Date:** 2026-10-04 · **Artifacts under review:** `samples/S002_batch1/` (Owner upload `6b2d4ba`, extracted `f11a6eb`, main) — `final.jpg`, `inpainted.png`, `text_mask.png`, `original.jpg`, sidecars · **Render bytes:** metadata `notebook_commit: a007581` = the Phase-D-approved Batch-1 bytes; verified the main-branch notebook blob (carried by `f158091`) is byte-identical to `a007581`'s (empty diff) — the S002 run provably executed the verified code. **Baseline:** `samples/S001_color_webtoon/` (same page `02.jpg`). **Discipline:** TASK_003.md protocol item 2 + samples/README rules. **No source modified; samples untouched; no amend/merge.**

**Method:** all numbers re-derived by this reviewer from the pushed artifact bytes (numpy/PIL/cv2 instruments `m003_s002_p1_ab_residue_mask.py`, `m003_s002_p1b_probe.py`, `m003_s002_p1c_rendermaps.py`, `m003_s002_p1d_true_residue.py`, `p2_region1/p2v2_clean/p3_sweep/p4_metrics.py`, reviewer sandbox). Reading-frame convention: region-1 crop (10,81,61×298) un-rotated from `vertical_rotate=-90`; axis0 = advance (0..297 = img y−81), axis1 = across (glyph-height direction); glyph height = across extent. Luminance = PIL "L".

## S0 — A/B VALIDITY — PASS

- `original.jpg` byte-identical between S001/S002 (tobytes sha equal; max |diff| = 0). [FACT]
- Region geometry identical (all 6 boxes); only 3 `detector_score` float tails differ (~1e-7 detector nondeterminism, no coordinate impact). [FACT]
- Region-1 `translated_text` **byte-identical** between runs → every region-1 pixel difference isolates exactly the Batch-1 rendering changes (fallback scale/wght/stroke/baseline/ladder), with identical input text and identical main-font sizing. [FACT]
- Region-1 OCR text differs slightly between runs (S001 "…Otearai … おてあらい…", S002 "…Otarumi … おたるみ…"); `translation.json` `original_text` is identical for both. OCR is Batch-2 (V-3) scope, has no bearing on the rendered image (identical `translated_text`), and is not an acceptance gate here. → Note N-S2-A. [FACT]

## S1 — GATE 1 (V-2 RESIDUE WINDOW x34–47, y370–381): measured 19 px, expected 0 — LITERAL FAIL; FORENSIC RE-ATTRIBUTION: gate premise void, true residue = 0 in BOTH runs

- **Measurement (method validated):** S001 window = **11 px < lum 160, min 18.0, at (40–44, 375–378)** — reproduces the S001 review record exactly (same 11 coordinates). S002 window = **19 px, min lum 0.0**: the same 11 coordinates (values ±1) **plus 8 new pure-black px at (39–44, 370–371)**. [TEST RESULT]
- **Layer provenance at all 19 px:** `original` = 255 (white) at every one; `inpainted` = 254–255 at every one (both runs); dark only in `final`. → **all 19 px are RENDER INK drawn over a clean inpaint, not original-ink residue.** [TEST RESULT]
- **The 11 "specks" re-identified:** they are the right-clipped fragment of the flowed word **"যা"** at the end of rendered line 2 (the line fills the full 298-px column and is clipped at the canvas edge; the fragment `##/#####/######/####.#` at advance 294–297 is byte-stable ±1 across both runs). Present identically in S001. **Not residue; never was.** [TEST RESULT + visual at 8×]
- **The 8 new px:** tail of S002's bigger/darker しゅ (ゅ lower bar, advance 282–291) — i.e. the *intended* V-1 ink increase intruding into the window, not a defect. [TEST RESULT]
- **True-residue audit (whole region-1 box):** original-ink px left unmasked by the mask: **S001 = 0, S002 = 0**; `inpainted.png` dark px in x10–70/y355–385: **S001 = 0, S002 = 0**; original note's ink actually ends at y=371 (not ~384 as my S001 review estimated) and was already fully masked+inpainted in S001. [TEST RESULT]
- **RECORD CORRECTION (self, PE.7 precedent):** my S001 visual review's "11 px true original-text residue … mask-missed glyph tips" and the derived "extend the quad to the text's true bottom ~y=384" fix locus were **WRONG** — the specks were render ink (clipped "যা" fragment), there was no mask hole and no original-ink residue. Phase A's V-2 motivation and the Batch-1 gate metric inherited that mis-diagnosis. The V-2 band is therefore a **functional no-op for region-1 residue** (there was none to remove); the literal "0 px in window" target is **unachievable by any mask-side fix** because the px are renderer output. [FACT + TEST RESULT]

## S2 — GATE 2 (V-1 CJK INK/GEOMETRY): PASS on every specified criterion

| Metric | Gate | S002 measured | S001 reference |
|---|---|---|---|
| CJK ink mean luminance | ≤ 60 | **52.9** (A/B zones); pure-CJK comps 19.1–47.4 | 92.1 same zones (reproduces "~90") |
| CJK height vs Bengali runs | ≥ 80% | **11–13 px vs 7 px ink-median → 1.57–1.86** (100% of the line band) | zone across-extent 7–10 px, pale |
| Baseline alignment | ok | bottom Δ +3 px (JP glyph below-baseline ink overshoot; top Δ −3/−1) — code-level `ly_fb = ly + asc_main − asc_fb` was runtime-verified exact (Phase D RT-2) | — |
| Column-boundary overflow | none new | line1 [7..289] fits; line3 [120..176] **pixel-identical** both runs; line2 [0..297] clipped at the canvas edge **identically in S001** (pre-existing); render-ink bbox x[22..67] ⊂ box, y ≤ 378 | line1 [11..285]; line2 [0..297] |

- Line-1 shift [11..285]→[7..289] is the centered-layout signature of a wider line (bigger CJK), symmetric ±4 px — no overflow. [TEST RESULT]
- **Ladder evidence:** line-2 CJK height 11 px vs line-1's 13 px — consistent with a step-down (1.12 or the 1.0 floor) on the overflowing line, per the approved ladder design; line 2 still clips because it overflows even at the floor (Bengali-dominated content) — exactly the Phase D N-F residual. The clip is **not a Batch-1 regression** (identical in S001, whose CJK was half-size). [TEST RESULT]
- Visual (reading frame, 2×/8×, both runs): S001 CJK pale-gray, small; S002 CJK black, bold, seated on the line, clearly readable — the V-1 defect is visibly fixed. [TEST RESULT]

## S3 — GATE 3 (MASK BAND SAFETY): PASS

- Added mask px = **1011, all within x[10..71]** (0 outside; 0 in border strip x72–76); removed = 0; totals 136 804 → 137 815. Rows: top tip band 71–85, bottom tip band 374–389 — matches the approved `mask_vpad_vertical=10` tip bands. [TEST RESULT]
- `inpainted.png` A/B: 37 px changed (|d|>8) in 3 clusters — band edge (x70–71, y71–77) and border-AA (x75, y82–102 / y108–112), i.e. LaMa context effects around the new band; final border strip: 11 px changed (−13..−17), border dark-count 1092 → 1059 (marginally lighter overall); side-by-side at 3×: the double rule-line is visually identical, no encroachment, no new damage. **Panel border x≈72–76 untouched.** [TEST RESULT + visual]
- Whole page outside region-1's columns: **17 changed px** (x71–75 band/border AA only). [TEST RESULT]

## S4 — GATE 4 (NO NEW RESIDUALS / OVERFLOW / MISFIRES ELSEWHERE): PASS

- **Regions 2–6: ZERO changed px** between S001 and S002 finals — pixel-identical re-render; no regression, no misfire, no SFX/bubble damage anywhere else on the page. [TEST RESULT]
- Render ink outside any region box (+6 px pad): **0 px in both runs, all 6 regions** — zero box overflow anywhere. [TEST RESULT]
- New dark ink outside boxes (dark in S002, light in S001): 4 px at x=75 (border AA); "truly new ink over artwork": 1 px. Negligible. [TEST RESULT]
- Region-3/5 mask holes (321/33 px = the known preserved bubble-border strokes): byte-identical between runs — unchanged, as expected. [FACT]
- Top band area (rows 66–92): dark-over-light-original 57 px vs S001's 39 — the growth is line-1's re-centered/bolder render inside the region; no misfire. [TEST RESULT]

## NOTES (non-blocking)

- **N-S2-A** — Region-1 OCR wording differs between runs (S001/S002 ocr.json); Batch-2 (V-3) scope; no render impact; `translation.json` identical. The S002 acceptance says nothing about OCR accuracy.
- **N-S2-B** — **Pre-existing line-2 column-end clip (newly documented):** rendered line 2 fills the entire 298-px column in both runs; the trailing word "যা" is clipped to "য" (the "া" and part of য are lost; line 3 reads "একটি ভোকাল"). Identical in S001 — NOT a Batch-1 regression and outside the ladder's reachable range (overflow persists at the 1.0 floor; the fallback ladder only scales CJK). Candidate follow-up: re-wrap / fold-into-fit per the Phase B alternative (Owner-approved scope change required).
- **N-S2-C** — S002 metadata records the "plain path; quality wrap not invoked" Control-Studio variant; the rendered output (bold/dark CJK + baseline shift + centered wider lines) is only producible by the Batch-1 renderer, corroborating provenance. Live-font/production environment caveats remain Owner-side per N-E (Phase D).
- **N-S2-D** — CJK overshoots the ≥80% gate (157–186% of Bengali ink-median) — this is the approved `fallback_cjk_scale=1.25` design, not a defect; flagged only so the Owner can judge the aesthetic balance on the live sample.

## OVERALL VERDICT

**BATCH1 ACCEPT.**

- Every change Batch 1 actually introduced is verified correct in the rendered artifact: V-1 CJK is dark (52.9 ≤ 60; was 92.1), large (157–186% ≥ 80%; was ~50%), baseline-aligned (±3 px, code-exact per Phase D), no new overflow; V-2 band landed exactly as approved and is safe (0 px outside x10..71, border untouched); regions 2–6 are pixel-identical; zero new artifacts page-wide.
- The single literal gate miss (window 19 px ≠ 0) is **void as a residue metric**: forensics prove the window contains zero original-ink residue in either run — 11 px are a pre-existing clipped-glyph fragment (unchanged since S001) and 8 px are the intended V-1 ink. The metric was calibrated on my S001 mis-diagnosis, corrected above (S1, RECORD CORRECTION). No code or knob change can or should chase it.
- **No config tuning required** — `fallback_font_wght=700` / `fallback_cjk_stroke=2` are NOT needed: CJK ink (19–47 lum) is already darker than the Bengali body (~90) at the shipped defaults; raising weight/stroke would overshoot.
- Follow-ups queued (non-blocking): N-S2-B line-2 end-clip (pre-existing; needs an Owner-approved re-wrap item), N-S2-A OCR wording (Batch 2 territory).
- **Gating:** this acceptance discharges TASK_003 protocol item 2 for Batch 1; Batch 2 (V-3) may proceed per the task book's batch order. Samples/ and source untouched by this review; verdict recorded in a NEW commit (no amend/merge).

---

# MANGABD-002 — MERGE VERIFICATION ON MAIN @ 0d3bc57 (GLM-5.3-FLASH, Independent Reviewer)

Date: 2026-10-08. Trigger: PM Task 1 assignment (Qwen3.8-Max) — verify MANGABD-002 finalization on main. Method per DECISION.md §C: every claim re-verified against pushed bytes, no source changes, NEW commit only.

## M1 — MAIN HEAD CONTAINS THE MANGABD-002 CHANGES: PASS

- `f7eb7e6` ("MANGABD-002: fresh-run reliability fix", 2026-09-27, parent `aabc592`) is an **ancestor of main HEAD `0d3bc57`**. [TEST RESULT]
- PM-referenced `829c383` (Phase C WIP) vs `f7eb7e6`: **tree diff empty** — same parent, same tree, different message only. TASK_002.md's "amended → `f7eb7e6` (tree identical)" narrative verified byte-exact; `829c383` is a superseded pre-amend object (present locally on the stale `mangabd-002-phase-c` branch; the remote branch is deleted as the docs-sync message states). [TEST RESULT]
- Both fix regions byte-present in main HEAD's notebook: cell-14 dependency guard (`if ("run_inpaint_all" in globals()) and ("run_render_all" in globals()):` — JSON-escaped form, 1 occurrence) + skip-print + cell-26 `render_all_pages(force=False)` + Bengali comment block. All diff hunks `f7eb7e6..main` (old lines 5532..17255 = MANGABD-003 Batch 1 cells) do not intersect the fix regions (old lines ~11700 / ~18043). [TEST RESULT]
- Reviewer self-correction: my first grep for the guard line used unescaped quotes and falsely reported it missing; the JSON-escaped form is present. Instrument artifact, not repo damage. [TEST RESULT]

## M2 — FRESH-RUN RELIABILITY MAINTAINED ON MERGED MAIN: PASS

- `m002_sim_v2.py` on main HEAD (`0d3bc57`): **abort-class SITE count = 0** (27 code cells simulated; call map 1773). [TEST RESULT]
- Calibration: same instrument on the pre-002 base `aabc592` reports **exactly 1 site** (cells[14]:40, `run_inpaint_all`/`run_render_all` via `run_inpaint_render_all`) — the instrument remains meaningful. [TEST RESULT]

## M3 — DOCS ACCURACY (TASK_002.md + DECISION.md): PASS

- `agents/TASK_002.md` STATUS now reads **COMPLETE** with the closure narrative; every hash in it independently verified: `829c383`→`f7eb7e6` amend (tree identical), `e9802fb` (Phase D on the review branch) **replayed as `05d9bc6`** on main (both exist, both +77 lines to GLM_5_3_FLASH.md, same message), fast-forward merge to main, close-out docs `8deff7c` + `9f4d82a` — all four dated 2026-09-27; the 2026-10-08 sync note accurately describes the stale STATUS field as the only gap. [FACT + TEST RESULT]
- `agents/DECISION.md` **§B.13 "MANGABD-002 Phase C/D Completion Record (final)"** exists (line 497) with dates, participants, Owner approvals, and hash records; cross-references from the header and §B/§B.11 resolve. [FACT]

## M4 — NO UNINTENDED FILE CHANGES: PASS

- `0d3bc57` diff: **exactly 1 file (agents/TASK_002.md), 1 insertion / 1 deletion** — the STATUS line only. [FACT]
- `git diff --summary 48cdadd..0d3bc57`: empty — **no mode flips, no renames**. Repo-wide `ls-tree`: 26 files, **all 100644**. No other commits on main between `48cdadd` (my S002 acceptance) and `0d3bc57`. [TEST RESULT]

## M5 — OVERALL VERDICT (TASK 1)

**MANGABD-002 MERGE VERIFICATION: PASS.**

Main HEAD `0d3bc57` fully contains the MANGABD-002 finalization (code + docs); 0 abort sites maintained; TASK_002.md / DECISION.md updates accurate; zero unintended changes. The 2026-10-08 docs-sync commit is a faithful, minimal STATUS sync of work that had been on main since 2026-09-27. **MANGABD-002 remains CLOSED**, and its artifacts (cells 14/26) remain the protected baseline for MANGABD-003 batches. Samples/ and source untouched by this review; record in a NEW commit (no amend/merge).

---

# MANGABD-003 — PHASE D VERIFICATION — BATCH 2 / V-3 (GLM-5.3-FLASH, Independent Reviewer)

Date: 2026-10-08. WIP verified: `5e87050` ("WIP: MANGABD-003 Phase C Batch 2 — awaiting Phase D verification", 2026-10-08), branch `mangabd-003-batch2`, parent = main `0d3bc57`, single linear commit. Method per DECISION.md §C + TASK_003.md VERIFICATION PROTOCOL: independent re-verification of pushed bytes; **own analysis first, GLM-5.3's self-report (T3.25–T3.29) read only afterwards** for claims comparison. Instruments persisted OUTSIDE the repo (`scripts/m003b2_d1_audit.py`, `m003b2_d3_mirror_v3.py`, `m003b2_d6_v3.py`, `m003b2_d8_runtime_v3.py`). No source changes; NEW commit only.

## D1 — DIFF & SCOPE AUDIT: PASS (28/28)

- Topology: HEAD=`5e87050`, parent=`0d3bc57`, rev-list count=1, merge-base=base (linear). [TEST RESULT]
- numstat exact: notebook **+84/−1**, `agents/GLM_5_3.md` +54/−2; **2 files only**; no samples/ or metadata changes. [TEST RESULT]
- All blobs 100644 (repo-wide 26 files); only M entries; **no mode changes, no renames**; secret scan of all 138 added lines: **0 hits**. [TEST RESULT]
- **Changed cells (source AND object level) = exactly {7, 16}**; the other 25 cells byte-identical to main. [TEST RESULT]
- **Transplant fidelity:** cells 7/16 byte-identical to the Phase-E-approved `f58cd3c` (sha16 `4522a89c18f5ee8d` / `e31bfdc3a03ec9e2`). [TEST RESULT]
- Scope invariant: batch1 cells {6,8,11,12,22} + batch3 cells {1,25} byte-identical to main; mirror cells 11/12 identical to main AND `f58cd3c`. [TEST RESULT]
- MANGABD-002 artifacts: cells 14/26 byte-identical to main, guard lines 40–46 verbatim; cells 13/19 untouched. [TEST RESULT]

## D3 — MIRROR DISCIPLINE (cells 11 & 12, if applicable): PASS (15/15)

- Batch 2 does not edit the mirror pair; discipline = **no drift**. `get_font_fb` (690 ch, sha16 `a7d2d5bd61309c78`) and `_qc_render_vertical` (2267 ch, sha16 `e27f769797d8ff4f`) **byte-identical cells 11↔12**, equal to the Phase-E / Batch-1-Phase-D records. [TEST RESULT]
- Cells 11/12 byte-identical to main `0d3bc57` AND `f58cd3c` — the 11↔12 full-cell delta remains exactly the Phase-E-approved documented dead-preamble removal in cell 12. [TEST RESULT]
- 3 V-1 knob setdefaults (`fallback_font_wght`/`fallback_cjk_scale`/`fallback_cjk_stroke`) present in both cells; renderer-family predicate sites unchanged vs main (cell-6 mask band intact). [TEST RESULT]

## D6 — V-3 SEMANTIC CHECKS (static): PASS (30/30)

**Layer 1 (cell 7 `ocr_region`):**
- **L1a upright excluded when predicate fires:** vertical-branch candidates = `rotate_90_clockwise` + `rotate_90_counterclockwise` ONLY; the upright `qwen.recognize` exists solely in the `else` branch. [TEST RESULT]
- **L1b rotated-first tie-break:** `chosen = candidates[0]` (CW first); loop over `candidates[1:]` with **strict `>`** (no `>=` anywhere in the selection block) → ties go to CW. [TEST RESULT]
- **L1c audit trail:** `vertical_ocr = {"chosen_orientation": …, "candidate_scores": {…}}` + `result.setdefault("warnings", []).append("vertical OCR: chose … (candidates: …)")`; returned as the additive field `"vertical_ocr"` (None = not vertical); `ocr_page` persists the full result via `save_json_artifact(page_id, "ocr", ocr_results)` → warnings + vertical_ocr reach the **OCR sidecar**; translation_df row schema untouched (V-4 Edit C deferral respected). [TEST RESULT]
- **L1d predicate = REGION geometry** (`region.get("width"/"height")`), formula `rw_ < 90 and rh_ > 2 * max(1, rw_)` — the renderer-family predicate; the comment documents why crop dims would defeat the test (S001 R1 widens to ~95–113 px with context+padding). [TEST RESULT]

**Layer 2 (cell 16 `inspect_ocr_quality`):**
- **L2a `import re` in BOTH branches** (records branch annotated "cell-standalone-safe"; df branch `import re`). [TEST RESULT]
- **L2b region geometry from detection records:** records branch via the ocr sidecar's embedded region record (`ocr_page` writes `{"region": …, "ocr": …}`); df branch via `det_geo = {int(dr.get("id",-1)): dr for dr in load_json_artifact(page_id, "detections", default=[])}` — the df's own x/y/w/h deliberately NOT trusted ("detections are truth"); `load_json_artifact(page_id, artifact_name, default=None)` signature verified (cell 3). [TEST RESULT]
- **L2c severity="warning" at both flag sites;** `add_quality_issue` has **no raise path**; warning/critical route into `manual_review_flags_dict` (🟡/🔴) — never blocks a page; try/except census delta vs main = **0 new handlers**. [TEST RESULT]
- **L2d composite predicate identical at both sites** (`rw_<90 and rh_>2*max(1,rw_) and has_kana and has_latin`, ×2 each; kana `[\u3040-\u30FF\u3400-\u4DBF]`, Latin `[A-Za-z]`). [TEST RESULT]

**Call-count amendment:** 2 static recognize sites (1 rotated-loop + 1 upright else) → **runtime 2 VLM calls for vertical regions** (loop × 2 orientations), 1 for upright — TASK_003 amendment "2 VLM calls, not 3" satisfied. [TEST RESULT]

## D8 — RUNTIME REPRODUCTION + GUARD EQUIVALENCE: PASS (35/35)

- **Guard equivalence:** cells {11,12,13,14,26} byte-identical batch2↔main ⇒ the Phase-D-approved `m002_flash_repro` 9/9 matrix carries over by identity. `m002_sim_v2` on `5e87050`: **0 abort sites**; calibration on `aabc592`: exactly 1 site (instrument meaningful). TASK_003 protocol item 1: PASS. [TEST RESULT]
- Runtime harness = **verbatim exec of pushed bytes** (`ocr_region` + deps from cell 7; `add_quality_issue`/`qa_is_special_marker`/`inspect_ocr_quality` from cell 16; real cv2/numpy/pandas; stubs only at the environment boundary: model_manager/qwen, crop fns, artifact IO, is_english_text, log_event):
  - **RT-1** wide 200×100 → exactly 1 upright call; `vertical_ocr` None. **RT-2** vertical 61×298 (S001 R1 REGION dims) → exactly 2 calls; received image #1 == true CW rotation, #2 == true CCW (`np.array_equal`), upright never sent. [TEST RESULT]
  - **RT-3** tie (equal scores) → chosen `rotate_90_clockwise` (CW text returned). **RT-4** CCW strictly greater (0.75+0.3 > 0.7+0.3) → chosen `rotate_90_counterclockwise` (CCW text returned). [TEST RESULT]
  - **RT-5** warning names chosen orientation + both scores; `candidate_scores` = `round(conf + language_score.en, 4)` exactly. **RT-7** sidecar receives the full ocr_result incl. `vertical_ocr` + warnings. [TEST RESULT]
  - **RT-6 predicate boundaries:** rw=90 → upright (strict <); rh == 2·rw → upright (strict >); rh == 2·rw+1 → vertical; 61×298 → vertical. [TEST RESULT]
  - **RT-8** records branch: vertical kana+Latin (61×298) → exactly 1 flag, severity warning, category ocr, routes to `manual_review_flags` 🟡. **RT-9 negatives:** kana-only / Latin-only / horizontal-mixed / rh==2·rw mixed → NO flag. [TEST RESULT]
  - **RT-10** df branch: df row claims 200×300 (box-snapped), detection record 61×298 → flag fires from **detection geometry**. **RT-11** missing detection → `geo={}` → predicate false → no flag, no crash. **RT-12** non-vertical detection → no flag. **RT-13** warning-only path never raises. [TEST RESULT]

## D9 — AMENDMENT COVERAGE + SELF-REPORT COMPARISON

- PM Layer 1 (a)/(b)/(c) + Layer 2 (a)/(b) and TASK_003.md Strict Amendments 1–5: **all implemented and runtime-proven** (D6/D8). Optional Phase-B items (kana-preservation scoring, vertical prompt variant) correctly NOT implemented — not part of the mandated minimum, and the Phase-E-approved bytes never carried them. [FACT]
- Self-report comparison (read only AFTER my analysis): GLM-5.3 T3.25–T3.29 checked against my measurements — changed-cell set, numstat, transplant shas, mirror shas, REGION-dims predicate rationale, runtime behaviors, negative controls, df-branch detections-as-truth, secret scan, MANGABD-002 artifacts: **all consistent** with my independent results; line citations verified (cell 7: 394–435 / 417–419 / 421–430 / 465–466; cell 16: 371 / 396 / 375–387 / 460–476). Grounding claims independently re-verified against real artifacts: S001 `detections.json` — R1 61×298 fires, R2 87×156 correctly silent (156 < 174), R3–R6 non-vertical; main cells 7/16 byte-identical to `1cd8acf` (transplant-source stability). **No unsupported claims found.** [FACT]

## NOTES (all non-blocking)

- **N-B2-1 (reviewer instrument self-corrections):** my D3a first asserted full-cell 11↔12 identity and D6-X2 first asserted 3 static recognize sites — both were wrong instrument expectations, corrected during the run (cell-12 dead-preamble removal is the Phase-E-approved state; 2 static sites = 1 loop × 2 orientations = the amendment's "2 VLM calls"). No repo impact. [FACT]
- **N-B2-2:** candidate score = `confidence + language_score["en"]` — deterministic, applied equally to both candidates; as an English-ness proxy for Japanese content it is semantically unusual, but the comparative use is sound and matches the Phase-E-approved bytes. Owner awareness only. [FACT]
- **N-B2-3 (carried from Phase E N3):** kana regex covers kana + CJK Ext-A, NOT the main CJK block 4E00–9FFF — kanji-only vertical notes will not trigger the Layer-2 flag; consistent with the S001 failure mode; unchanged by this batch. [FACT]
- **N-B2-4:** `import re` executes per loop iteration in the records branch — harmless (module cache), style-only. [FACT]

## OVERALL VERDICT

**PHASE D — BATCH 2 (V-3): APPROVED.**

- **108/108 instrument checks PASS** (D1 28 · D3 15 · D6 30 · D8 35); zero required fixes; all 5 TASK_003.md Strict Amendments + both Phase B Layer-2 factual amendments implemented and runtime-proven; scope invariant and MANGABD-002 artifacts intact; fresh-run safety maintained (0 abort sites, calibrated).
- **Gating preserved:** GLM-5.3 must NOT amend/merge until Owner acceptance is relayed via PM/Owner. **Merge gate = Owner-side S003 visual acceptance run** (live Colab + live `qwen.recognize`) proving the region-1 OCR fix on a fresh sample — TASK_003 protocol item 2, same pattern as Batch 1 (Flash Phase D `a007581` → merge gate S002 `48cdadd`). N-S2-A's S002 region-1 misread is exactly the defect this batch targets; Layer 2 will flag any residual misread for mandatory manual review even where Layer 1's rotated reads may still err.
- Batch 3 (V-5, cells 8/25) remains unauthorized on this branch; the Phase-E-approved bytes stay available on `mangabd-003-phase-c @ f58cd3c` for transplantation when the PM authorizes. Samples/ and source untouched by this review; verdict recorded in a NEW commit (no amend/merge).

---

# S003 ACCEPTANCE MEASUREMENT — MANGABD-003 BATCH 2 (V-3) vs S002 BASELINE

Date: 2026-10-11. Trigger: PM assignment — GLM-5.3 archived `samples/S003_batch2/` (commit `28da345`; metadata `notebook_commit: 671e5d3`, i.e. exactly the batch-2 state this reviewer Phase-D-approved in `74f5d8c`). Independent pixel-level + sidecar audit against `samples/S002_batch1/`. Method: artifact forensics (md5, normalized JSON diff, per-region pixel diff via numpy/scipy connected components), cell-code re-extraction from `origin/mangabd-003-batch2`, and Layer-2 predicate re-simulation from the archived sidecars. No self-report consulted. `samples/` and source code untouched; analysis scripts persisted outside the repo.

## P — PRE-CHECKS

- md5 across the 8 archived artifacts: `original.jpg`, `inpainted.png`, `text_mask.png` are **BYTE-IDENTICAL** S002==S003; only `final.jpg` (+4 sidecars) differ. Same source page, same inpaint, same mask — the A/B isolates the batch-2 delta to OCR→render of region 1. [TEST RESULT]

## G1 — V-3 (VERTICAL OCR) SIDECAR AUDIT: PASS

- `ocr.json` region 1 contains the `vertical_ocr` audit field: `chosen_orientation: "rotate_90_clockwise"`, `candidate_scores: {"rotate_90_clockwise": 1.95, "rotate_90_counterclockwise": 1.95}`. [TEST RESULT]
- Region 1 text now reads "…Otearai is spelt as おてあらい…"; zero occurrences of the S001/S002 misreads "Otarumi" / "おたるみ" / "しゅ" anywhere in the sidecar set. [TEST RESULT]
- Code cross-check @ `671e5d3` cell 7 (L394-432): predicate uses REGION geometry (`rw < 90 and rh > 2 * max(1, rw)` — not preprocessed dims), upright excluded (rotated-only candidate list), strict `>` tie-break with CW first. R1 geometry 61×298 → 61<90 ∧ 298>122 → vertical path fires; scores tied 1.95/1.95 → strict `>` keeps CW. Artifact semantics match code semantics exactly. [FACT + TEST RESULT]
- Regions 2-6 carry `"vertical_ocr": null` — field added uniformly, `None` = not vertical, per the Phase-D-approved design. [TEST RESULT]

## G2 — LAYER-2 QA FLAG: PASS

- Code @ `671e5d3` cell 16: records branch L367-383 and df branch L460-474 flag "Vertical mixed-script note (kana + Latin) — OCR unreliable" with `severity="warning"`; `add_quality_issue` maps warning → 🟡 (L180) and routes to `manual_review_flags` only (comment L369-370: "can never fail/block the page"). `import re` present at L371 (cell-standalone-safe); df-branch geometry sourced from `det_geo` detection records. Both Phase-B amendments in place. [FACT]
- Predicate re-simulated against the archived sidecars: **exactly region 1 fires** (geom ✓, kana ✓, latin ✓) → 🟡 warning; regions 2-6 do not fire (geometry non-vertical). Expected flag count = 1. [TEST RESULT]
- Non-blocking empirically confirmed: all 6 regions `"status": "ok"`, and the pipeline ran to completion producing the full artifact set including `final.jpg`. [TEST RESULT]

## G3 — NO REGRESSIONS OUTSIDE REGION 1: PASS

- Per-region diff of `final.jpg` (S002 vs S003, 1200×844): **regions 2-6 diff = 0 exactly** (max 0 — pixel-identical, not even JPEG noise). [TEST RESULT]
- Outside the exact R1 quad: 238 px differ at all, amplitude distribution {1: 134, 2: 59, 3: 34, 4: 10, 6: 1} — max amplitude 6. All 45 px with diff>2 hug the R1 quad boundary (y=80 top edge, x=71 right edge, y=379-383 bottom edge) → JPEG 8×8 block spill of the re-rendered region, not independent defects. Zero clusters ≥ threshold 8; zero new mask/render defects outside region 1. [TEST RESULT]
- `text_mask.png` byte-identical → zero new mask defects anywhere on the page. [TEST RESULT]

## G4 — V-1 / V-2 PRESERVATION: PASS

- **V-2 mask band**: mask active columns include the full band x[10..71] (62/62 columns active; activity rows y[71..422] ⊇ R1 quad y[81..379]); byte-identity with S002 proves the batch-1 band is untouched. [TEST RESULT]
- **V-1 dark CJK ink**: S003 R1 ink statistics — px(lum<60)=948 mean 14.2; px(lum<80)=1346 mean 31.1; darkest cluster 197 px, mean lum 9.0, min 0. Near-black kana present, far under the ≤60 gate; parity with S002 (means 27.2 / 12.7) under changed text content. Visual crop (evidence: `R1_S001/S002/S003` upscales) confirms dark こがねい and おてあらい glyph runs embedded in the vertical Bengali layout. [TEST RESULT]

## SCOPE / SIDECAR DELTAS (S002 → S003)

- `ocr.json`: region 1 text + warning + `vertical_ocr`; `page_id` "02.jpg" → "02_2.jpg" on all regions (cosmetic; documented in metadata "rendered as 02_2.jpg"). Nothing else changed — confidences, language scores, texts of regions 2-6 untouched. [TEST RESULT]
- `translation.json`: region 1 only (correction propagates to Bengali). `detections.json`: page_id only; all 6 region geometries identical — detector deterministic across runs. `metadata.json`: expected sample fields. [TEST RESULT]
- `pipeline_variant` no longer carries S002's "(plain path; quality wrap not invoked)" note — metadata wording only; the exact pixel-identity of regions 2-6 proves render-path equivalence empirically. [FACT]

## OBSERVATIONS (NON-BLOCKING)

- Region 1 OCR nits persist: stray ")" in "こがねい)", "hiragani"/"pronounce" spellings. Mixed-script OCR imperfection is precisely why the mandatory 🟡 manual-review flag exists; no gate violated. [FACT]
- The CW/CCW tie at 1.95 made the strict-`>` tie-break carry real weight: CW is the correct orientation for tategaki (top-to-bottom) and the empirically correct reading おてあらい validates the choice. [TEST RESULT]
- Region 5 bubble "OTEARAH" spelling is pre-existing S002 OCR output (byte-unchanged), outside batch-2 scope. [FACT]

## VERDICT

**BATCH2 ACCEPT.**

All four gates PASS on measured evidence: V-3 sidecar audit complete with correct orientation audit trail and the corrected reading; 🟡 manual-review flag fires exactly once, non-blocking; regions 2-6 pixel-identical with zero defects elsewhere; batch-1 V-1/V-2 fixes intact. The batch-2 merge gate is satisfied from this reviewer's seat.

---

# MANGABD-003 BATCH 3 (V-5: PROVIDER-FLEXIBLE TRANSLATION) — PHASE D VERIFICATION

Date: 2026-10-11 (session TZ Asia/Dhaka). Target: `mangabd-003-batch3` @ `1753b1a` (WIP), base = main @ `6ce6cd2` (ancestry verified). Scope of evidence: git blobs of both refs, cell-level AST analysis, verbatim-code runtime harness (scripts persisted outside the repo), fresh-kernel simulation, guard-equivalence repro. GLM-5.3's self-report (`agents/GLM_5_3.md`, changed in the WIP commit) was NOT read — verdict is independent. No source code modified; no amend/merge.

## D1 — SCOPE & REGRESSION: PASS

- Cell-level diff `6ce6cd2..1753b1a`: **changed cells = exactly {1, 8, 25}** (+6, +80/-1, +19/-1 lines); 27 cells in both refs; notebook top-level metadata unchanged (nbformat 4, same metadata keys); file-level: notebook + `agents/GLM_5_3.md` only; **no mode flips, no renames** (`git diff --summary` empty). [TEST RESULT]
- All 24 unchanged cells **byte-identical** to main, explicitly including the protected baselines: MANGABD-002 cells 14 (guard) & 26 (`force=False`); Batch-1 mirror cells 11/12; Batch-2 V-3 cells 7 & 16. [TEST RESULT]
- **V-4a `_unparsed` sentinel (cell 8) fully intact**: occurrence count 3 in both refs (shifted uniformly +69 by the three preceding hunks — arithmetic consistent with the hunk sizes +19/+37/+10/+3); the sentinel region (docstring contract, `unparsed = []` init, `translations[("_unparsed", 0)]` block) is **BYTE-IDENTICAL** to main (sha256 908223ba47d852b8…). The hunk-based patch claim is verified: only one line removed in cell 8 (the old `valid_engines` literal). [TEST RESULT]
- **Sentinel FUNCTIONALLY verified** (verbatim `parse_ai_text` executed in isolation): valid `[page:id] eng → ben` lines parse to real keys; malformed line collected under `("_unparsed", 0)` with `unparsed_lines`; `#` comment lines skipped (not mis-flagged). [TEST RESULT]
- **Fresh-run regression: `m002_sim_v2` on batch3 = abort-class SITE count 0** (27 code cells, call map 1776); instrument calibration holds — same simulator on base `aabc592` reports exactly 1 site (cells[14]:40 `run_inpaint_all`). [TEST RESULT]
- **Guard-logic equivalence on batch3 (`m002_flash_repro_b3` variant, cells 11-14 verbatim): S1-S6 scenario matrix ALL PASS** (fresh→NameError baseline; fresh+guard→OK-with-skip zero mutations; warm paths fire with identical call sequences). [TEST RESULT]

## D2 — PHASE B AMENDMENTS (V-5): PASS

- **Amendment 1 (closure-bound engine)** — the dispatcher inside cell 8 `translate_text` contains verbatim: `translate_with_retry(lambda t, rt: translate_with_provider(t, rt, engine=engine), text, region_type=region_type)`. Runtime proof with the verbatim `translate_with_retry` (byte-identical to main, 46 lines, signature `(translate_func, text, region_type="bubble")`, calls `translate_func(text, region_type)`): (a) closure path with two transient failures succeeds on attempt 3; (b) **counterfactual confirmed — passing `engine=` as a kwarg to the wrapper raises `TypeError: unexpected keyword argument 'engine'`**, exactly the failure the closure avoids; (c) retry exhaustion (always-empty output) returns `""` after 1+max_retries attempts. [FACT + TEST RESULT]
- **Amendment 2 (`key_env`, sanitizer survival)** — registry uses `key_env` (14 occurrences in cell 8; **zero `"api_key_env":` dict fields**). Runtime test with the REAL `save_config` sanitizer extracted verbatim from cell 1 (`forbidden_keys = [api_key, token, secret, password]`, recursive dict-key strip): nested provider dict → **`key_env` PRESERVED**, `api_key_env` stripped at provider/top-level/nested; `token`/`secret`/`password` stripped; string VALUES (`model: "deepseek-chat"`, `key_env: "deepseek_api_key"`) survive (sanitizer strips keys, not values). [TEST RESULT]
- **Amendment 3 (LiteLLM rejected)** — `litellm` occurrences in the whole notebook: **0**; native adapter is 29 lines, OpenAI-SDK only. [TEST RESULT]

## D3 — SECRETS (CELL 1): PASS

- `SECRET_SOURCES` additions, **purely additive (+6 lines, zero removals)**: `qwen_api_key → [QWEN_API_KEY, DASHSCOPE_API_KEY]`, `deepseek_api_key → [DEEPSEEK_API_KEY]`, `openrouter_api_key → [OPENROUTER_API_KEY]`; ollama deliberately absent with explanatory comment (local server, no key). The existing bootstrap loop (env vars → Colab userdata → `MANGABD_SECRETS[k]=v` + primary env export) covers the new entries without modification. [FACT]
- Adapter key handling runtime-verified (verbatim `translate_with_provider`, stubbed `openai` SDK): unknown provider → `""` + WARN; missing key → `""` + WARN naming the exact `key_env`; with key → correct `base_url`/`model`/`api_key` through to the client call; ollama (`key_env: None`) → placeholder key `"ollama"`, no secrets lookup, no spurious WARN. [TEST RESULT]

## D4 — DEFAULT MODELS: PASS

- Registry: `deepseek → "deepseek-chat"`, `openrouter → "openai/gpt-4o-mini"` (in-code comment "Owner default: Batch 3 directive 4"); openai → `gpt-4o-mini`, qwen → `qwen-plus`, ollama → `qwen2.5:7b`. [FACT]
- Authorization trail: `agents/DECISION.md` L550 documents the open item "(a) per-provider default models (proposed: gpt-4o-mini / qwen-plus / deepseek-chat / qwen2.5:7b (local) / Owner's choice on OpenRouter)" — the four non-OpenRouter defaults match the DECISION.md proposal exactly; the OpenRouter default is the Owner's choice conveyed by the Batch 3 directive (PM attestation). Change from the original f58cd3c proposal bytes is therefore **authorized and documented**. [FACT]

## D5 — INTEGRATION & WIRING: PASS

- Engine chain end-to-end (all links statically verified): `on_provider` (cell 25) → `run_translation_all(engine=…, force=True)` (cell 15, signature `(engine=None, force=False)`) → `translate_all_pages(engine=…)` → `translate_page(page_id, engine=…)` → `translate_text(text, engine=…, region_type=…)` → provider `elif` → closure → retry → adapter. [FACT]
- Provider `elif` is the **last engine branch before the final `else` (unknown-engine warning)** — no shadowing possible; provider names ∩ legacy engines = ∅; `switch_translator` validates against the dynamic `valid_engines` (legacy + registry keys). [FACT]
- Cell 25 wiring: 7/7 checks PASS (button defined, handler defined, `fn(engine=mode_sel.value, force=True)`, wiring tuple, 4 provider options in mode_sel, secret-hint panel, `on_nllb` intact). `translator_model` sidecar field additive with row-level override precedence. AST parse OK for cells 1/8/25. [TEST RESULT]
- Free-name audit of new defs against the fresh-kernel namespace: all resolve (one instrument false positive — `exc` from `except … as exc` binds via ExceptHandler.name, invisible to Store-scan; verified benign). [TEST RESULT]

## OBSERVATIONS (NON-BLOCKING)

1. Cell 25 relabels NLLB "(offline auto)" → "(experimental)" — consistent with DECISION.md L554 policy ("NLLB not used per policy"); inside the single logical change of cell 25. [FACT]
2. `translate_with_retry`'s `except Exception` swallows any error inside the try (including dependency NameErrors) into the retry/fail-soft path — **pre-existing behavior, byte-identical to main**; noted because it surfaced during harness calibration (my incomplete stub), not a batch-3 defect. [FACT]
3. The adapter's blanket `except Exception → ""` mirrors the existing chatgpt adapter's fail-soft contract; empty translations route through existing QC/retry plumbing. [FACT]
4. Harness artifacts: `scripts/b3_scope.py`, `b3_preserve.py`, `b3_inspect.py`, `b3_runtime_harness.py`, `b3_h7_static.py`, `m002_flash_repro_b3.py`, `nb_batch3.json` — all outside the repo. Two instrument fixes during calibration (retry-stub missing `clean_translation`; wrong `parse_ai_text` sample format) were harness-side, not notebook-side. [FACT]

## VERDICT

**PHASE D APPROVED.**

Scope exactly {1, 8, 25}; V-4a sentinel byte-intact and functional; all three Phase B amendments implemented and runtime-proven (closure prevents the demonstrated TypeError; `key_env` survives the real sanitizer; no LiteLLM); secrets bootstrap additive; defaults authorized per DECISION.md + Batch 3 directive; zero regressions against MANGABD-002/Batch-1/Batch-2 baselines; 0 abort sites maintained; guard equivalence S1-S6 pass. Per TASK_003.md protocol, the merge gate is the Owner's visual acceptance run (S004) — recommended exercise: one provider engine (e.g. deepseek) plus the manual-edit round-trip on a fresh Run All.

---

# MANGABD-004 — PHASE B REVIEW (GLM-5.3-Flash, 2026-10-13)

Target: GLM-5.3's Phase A (`agents/GLM_5_3.md` §MANGABD-004, commit `c196505`, docs-only — verified `git show --stat`). Method per PROJECT_CONTEXT: independent investigation FIRST against notebook bytes (`main @ 37dc72e` for cells ≠1/8/25, `mangabd-003-batch3 @ 1753b1a` for cells 1/8/25 — Phase A's own dual-baseline convention, re-verified: the V-5 payload is NOT on main; main's notebook tops out at Batch 2 `6ce6cd2`), S003 artifacts, and fresh upstream fetches (`zyddnys @ d6de6ab` — same commit Phase A cites; HF `preprocessor_config.json` re-fetched independently); THEN claim-by-claim challenge of Phase A. Evidence scripts persisted outside the repo (`/home/z/my-project/scripts/m4_*.py`, extractions in `/home/z/my-project/m4_work/`). No source changes; this commit touches only this file.

## PB1 — DIRECTIVE 1: OPENROUTER-EXCLUSIVE (A2)

- **Current-state inventory (A2.1): CONFIRMED.** Spot-verified against bytes: registry 5 providers `cell 8:86–97` (openai/qwen/deepseek/ollama/openrouter with `key_env` fields), dispatcher branches (gemini :803, chatgpt :810, nllb :817, providers :824–832 closure, unknown :834), `translate_with_gemini` :446, `translate_with_chatgpt` :494, NLLB trio :589–756, `switch_translator` :844–870, cell 25 `mode_sel` **7 options** :276–283 (manual/gemini/openrouter/deepseek/qwen/ollama/nllb), `gemini_key` :294–295, cell 1 `SECRET_SOURCES` 6 families :407–416, sanitizer :529–576 (Phase-D-runtime-proven), cell 19 NLLB override :93–157, cell 15 `quick_start_auto(engine="gemini")` :898, cell 17 gemini-specific leak test :963–973. [FACT]
- **Key-never-in-CONFIG (A2.2): CONFIRMED.** Sanitizer strips any dict key containing api_key/token/secret/password recursively; in-CONFIG keys would be silently deleted at the cell-1 `save_config()` call. Consistent with my Batch 3 Phase D D2 runtime proof. [FACT]
- **Registry-reduction mechanics (A2.3): CONFIRMED except one claim — CHALLENGED.** "valid_engines collapses automatically to ["manual","openrouter"] — zero logic change" is **FALSE for the legacy prefix**: `valid_engines = ["manual", "gemini", "chatgpt", "nllb"] + list(providers)` (cell 8:850–852) — only the registry tail is dynamic; the legacy four are a hardcoded literal. Consequence: A2.5's removal list (which omits 850–852) leaves `switch_translator("nllb")`/`("gemini")` **accepted** post-M4, and A2.6's "rejected by the dynamic list with the existing WARN — correct degradation" is wrong as specified — the engines are accepted, then fail through the dispatcher into the unknown-engine `else` (WARN + empty string). Fail-soft, but contradictory UX and a spec defect. → **Amendment 1.** [FACT: bytes; TEST RESULT: reachability map]
- **Registry consumers degrade gracefully (A2.6 sidecar claim): CONFIRMED.** `translator_engine` values are written (cell 8:1159/1320/1339) and read only at cell 8:1225 as a registry lookup that returns `{}` for unknown names; the only engine-value comparison outside the dispatcher is `engine == "manual"` (cell 15:718), which survives. Old artifacts stay readable. [FACT]
- **3-layer key UX (A2.4): CONFIRMED compatible with "keys never persisted"**, with a wording requirement — Amendment 7. Session layer writes `MANGABD_SECRETS` + `os.environ` (mirrors the proven `on_gemini` capture, cell 25:345–347); persist layer is Colab `userdata.set` — which is exactly the surface cell 1's bootstrap already reads (`SECRET_SOURCES` loop :419–440), so the design adds no new storage class. The cell-1:443 promise covers CONFIG/manifest; userdata is an Owner-controlled allowed surface per A2.4's own recap. Rejected alternatives (CONFIG literal; key-as-notebook-string) correctly rejected. [FACT + judgment]

## PB2 — DIRECTIVE 2: MANUAL COPY-PASTE PRIMARY (A3)

- **Current-flow audit (A3.1): CONFIRMED** in full — three payload paths (`build_ai_text_content` cell 25:153–165; `show_text_for_translation` cell 22:107–182 with COPY banners; `export_ai_text` cell 8:954–1057), disabled `ta_src` with no copy button, strict parser + V-4a sentinel + 3-snippet warning at cell 22:235–245, lenient 5-arrow local parser (`→ ➔ ➡ -> =>` cell 22:59, 84–90), Bengali-left rescue. [FACT]
- **Byte-truth of the "2 parsers + 1 builder" constraint:** it is **2 parsers + 2 builders** (`export_ai_text` AND `build_ai_text_content`); Phase A's A3.5 enumeration actually covers all four load-bearing sites correctly — the PM shorthand undercounts builders, the proposal does not. [FACT]
- **Quality case (A3.2): CONFIRMED.** All four quoted NLLB rows exist verbatim in `samples/S003_batch2/translation.json` (R5 "যৌনসঙ্গম" clinical-term profanity failure + "! !" artifacts; R3 "বোকা" softening; R4 intensity collapse; R1 meta-note translated with stray ")"). The artifacts contain an additional uncited defect that strengthens the case: R6 "SHE WAS INTO ME" → "সে আমার ভিতরে ছিল". [FACT: artifact diff]
- **System prompt template (A3.3): CONFIRMED** — format rules match parser semantics exactly (header regex, LAST-arrow `rsplit`, `#` banners skipped, `[SKIP:OCR_FAILED]` copy-through); glossary reuse sites verified (`build_glossary_prompt_lines` cell 8:323–346 def, call :294; `REGION_TYPE_INSTRUCTIONS` precedent :254–260). Edit-C deferral respected: single-line contract kept, region-type-tag-in-payload rejected (A3.5), sentinel stays the visible violation path. [FACT + proposal confirmed sound]
- **Paste-back hardening (A3.4-4): CHALLENGED on spec — silent line-loss risk is real.** `_strip_llm_wrappers` as specified ("removing … common LLM preambles as the first non-empty non-header line") is under-defined: applied globally, it can silently eat a wrapped continuation of a data line (LLM-wrapped long lines) BEFORE the parser sees it — no sentinel, no warning, **silent region loss**. → **Amendment 3** (prefix-zone restriction). Fences-only removal is safe as drafted. [FACT: mechanism analysis]
- **Builder reuse: amendment.** "reusing build_ai_text_content's row walk" reads as re-implementation; require `build_external_ai_copy` to **delegate** to `build_ai_text_content` (single source of truth) or carry a byte-coherence test — a third divergent row-walk is the classic drift vector this notebook has already suffered twice (prompt duplicated at cell 7:75–85 vs cell 5:350–358). → **Amendment 4.** [judgment, precedent FACT]
- **Clipboard UI (A3.4-1/2): CONFIRMED** — degrade path (visible textarea + select + manual Ctrl+C) cannot hard-fail; `navigator.clipboard` → `execCommand('copy')` fallback ordering is correct for Colab iframes; per-page scoping is sensible. Live-behavior items correctly parked as A7-D7 UNKNOWN. [judgment]

## PB3 — DIRECTIVE 3: LAMA CAPACITY AUDIT (A4)

- **Upstream semantics: ALL CONFIRMED against `d6de6ab` source read this session.** `LamaMPEInpainter._infer` (zy:inpainting_lama_mpe.py:56–118): cap on **max dimension** (`if max(image.shape[0:2]) > inpainting_size`, L64), `resize_keep_aspect` = `ratio = size/max(h,w)` with rounding (zy:utils/generic.py:251–255), pad-to-/8 by tiny stretch (L67–79), bf16 autocast with fp32 weights incl. the fp16-darkens comment (L97–107), resize-back (L115–116), masked-only composite (L117). `InpainterConfig.inpainting_size = 2048` with "too large will result in OOM" (zy:config.py:297–298); precision default bf16 "use bf16 while you can" (:299–300); default inpainter = `lama_large`. Notebook: `lama_size` 1024 (cell 9:69) passed as 4th positional arg — the config field is genuinely never read on this path (config supplies only precision). [FACT]
- **844×1200 @ 1024 scaling path: independently recomputed — CONFIRMED.** ratio 1024/1200 = 0.8533 → `round(844×0.8533)=720`, so the page is inferred at **720×1024** (no /8 pad needed: 720=8·90, 1024=8·128), then the masked area is upscaled back 1.17× bilinear. "Silently downscaled 0.85×" is accurate; page dims verified from `original.jpg` = 844×1200. [TEST RESULT: arithmetic + artifact]
- **Throttle verdict (A4.2): CONFIRMED** — factor 2 vs upstream config default; at 2048 the Owner's pages run native (1200 ≤ 2048; only pad-to-848). The "512px = training resolution, not an inference limit" point is properly framed (fully convolutional: FFCResNetGenerator, `large_arch → n_blocks=18` verified at zy:L640–645, ngf=64, 3 downsamples, max_features=1024). Whether quality is *empirically* better at native vs 1024-with-1.17×-upscale round-trip remains an S007 acceptance question — Phase A already gates it there; the mechanism argument (native avoids an information-destroying downscale-upscale round trip inside the masked region) is sound. [FACT: architecture; empirical: delegated to S007]
- **Ladder OOM-safety: CONFIRMED with evidence Phase A did not have.** (a) **Retry idempotency is FACT, not assumption**: upstream `_infer` copies inputs at entry (L57–58) and rebinds only locals (L63–79) — the caller's `image_bgr`/`prepared_mask` are never mutated, so an OOM'd rung can be safely retried at the next size. (b) Exception taxonomy is correct for CUDA async OOM (`torch.cuda.OutOfMemoryError` + RuntimeError-message match); `clear_gpu_cache` (gc + empty_cache + synchronize) exists at cell 5:143–150. (c) **T4 headroom, evidence-derived**: the 1024 rung (720×1024 = 0.74 MP) is field-proven across S001–S003; the native-2048 rung for Owner pages (848×1200 = 1.02 MP) is **1.38× the proven-safe area** — even with linear activation scaling that bounds peak near ~1.4× a proven-safe rung, comfortably inside T4 budget, and no downscale at all. The 2048×2048 worst case (4.2 MP = 5.7× proven-safe) is genuinely borderline — the ladder's reason to exist; Phase A's "borderline" characterization stands. VRAM numbers remain honestly HYPOTHESIS-tagged with a concrete Phase D measurement plan (`max_memory_allocated` per rung, <12 GB gate). → **Amendment 5** (exception scope must exclude the notebook's own deterministic `RuntimeError("LaMa returned empty result")` — non-OOM errors belong to the existing OpenCV fallback, not ladder retries). [FACT: source; HYPOTHESIS: absolute VRAM, properly tagged]
- **Rejected alternatives (P3): CONFIRMED sound** — tiling vs FFT global field (FourierUnit operates on the full canvas), unconditional-native vs webtoon tall-strips, INTER_NEAREST mask patch vs composite using the ORIGINAL full-res mask (upstream `mask_original` copied at L58 before any resize, used at L117 — verified). Mask-discipline protection (A4.4: cell 9:70–76 `redilate_artifact_mask=False`/`mask_clip_to_regions=True`/`mask_clip_padding=10`) — bytes verified, correct protected-baseline designation. Supply-chain finding (A4.6: cell 4 `git pull --quiet` / `clone --depth 1` every run, :210–248) — verified; hash-recording proposal is proportionate; hard-pinning correctly surfaced as decision D5. [FACT]

## PB4 — DIRECTIVE 4: OCR AUDIT (A5)

- **Pixel budget: CONFIRMED, independently.** HF `preprocessor_config.json` re-fetched this session: `min_pixels=3136, max_pixels=12,845,056` (patch 14, merge 2); processor constructed with NO overrides (cell 5:800–805). Measured S003 crops from `detections.json`: R1 61×298 (18.2 kpx), R2 87×156, R3 204×216 (44.1 kpx, largest), R4, R5, R6 131×204 — i.e. **16–56 visual tokens per region, 0.09–0.34% of the pixel cap**. "Pixel budget is NOT the bottleneck" is conclusively supported. [TEST RESULT × 2]
- **Prompt/decode/confidence facts: CONFIRMED.** Single generic prompt duplicated at cell 7:75–85 and cell 5:350–358 (fallback); greedy decode (`do_sample=False, num_beams=1, max_new_tokens=512`, cell 1:248–254 → cell 5:404–408); `_estimate_ocr_confidence` = 0.45+0.15+0.10+0.20(en)+0.05(clean), **capped 0.95** (cell 5:281–315) — any ≥5-char English text maxes it, and all six S003 regions read exactly 0.95 (my sidecar dump). Saturation diagnosis is correct; P2's recalibration caution (V-3 selector score `confidence + language_score.en` + QC thresholds 0.50/0.65) is accurate. [FACT + TEST RESULT]
- **Defect list (A5.2): PARTIALLY CHALLENGED.** R1 (hiragani/stray ")"/pronounce), R2, R5 verified against artifacts. **R6 misclassified**: visual inspection of the artwork crop shows "SHE **SUDDENLY** CALLED…" complete and mid-crop — "SUDENLY" is a **doubled-letter glyph miss**, not crop-edge truncation, and the sentence is not cut (OCR tail matches artwork tail). R2 likewise: artwork reads `THE ONLY LETTER CORRECT IN THAT NAME WAS "I"!` — the quoted "I" was dropped **mid-crop** (Phase A's "likely the quoted glyph" was right; its crop-edge framing was not). → **Amendment 6a.** [TEST RESULT: visual crops R2/R6, persisted in m4_work]
- **Prompt-map P1 + "prompt is top lever": CONFIRMED as a cheap, low-risk lever; CHALLENGED as the sole top lever.** The evidence-backed defect taxonomy after V-3 is: R2/R6-class = mid-crop glyph-resolution misses at ~18–20 px line height; R1 = tiny 61 px-wide vertical strip; only format/romanization/SFX classes are plausibly prompt-bound. The P1 bubble rider as drafted ("partially cut off at the crop edge") targets a mechanism that produced **none** of the observed defects. → **Amendment 6b**: retarget the bubble rider (e.g. "transcribe quoted letters and doubled letters exactly; preserve every glyph") and — the missing cheap lever — a **config-gated upscale A/B**: crops run through smart_resize at ≈1:1 (R6: 131×204 → 140×196 — height *downscaled* 0.96×); 6 regions upscaled 2–4× would still sit under 1% of the pixel cap and add ~40 image tokens per region. The 12.8 MP headroom is the *argument for* upscaling, not against it; P5's de-motivation ("removes the motivation for super-resolution") does not follow from the no-cap-hit finding. Targets exactly the R1/R2/R6 defect classes. **Fairness constraint (blocking for B4):** any prompt/preprocessing change must apply **identically to both V-3 orientation candidates** (cell 7:394–432) or the CW/CCW score comparison becomes apples-to-oranges; V-3 plumbing (vertical_ocr fields, 🟡 flag, strict-`>` tie-break) stays byte-stable; and the stale duplicate fallback prompt (cell 5:350–358) must be updated or removed in the same hunk-set. [TEST RESULT: crop grid math; judgment]
- **P3 sfx dual-pass: CONFIRMED with caveat** — S003 has zero SFX regions (verified: R1 overlay + 5 bubbles), so the feature is untestable against archived samples; Phase A itself marks SFX accuracy UNKNOWN and defers measurement to S005/S006 — consistent. Default-ON-for-sfx is acceptable because the region_type gate makes it a no-op on current pages. [FACT: sample inventory]

## PB5 — DEAD-CODE LIST (A2.5): ENTRY-BY-ENTRY REACHABILITY

Cross-cell symbol map over all 27 cells (both refs), each candidate's every reference accounted for:

| A2.5 entry | Verdict |
|---|---|
| cell 8: gemini_model/openai_model (77–78) | REMOVABLE — residual refs live only inside removed adapters [FACT] |
| cell 8: registry openai/qwen/deepseek/ollama (86–94) | REMOVABLE — all consumers iterate the registry dynamically [FACT] |
| cell 8: NLLB config (114–122) + print (154) | REMOVABLE — consumers are exactly the removed branches/trio/UI [FACT] |
| cell 8: translate_with_gemini (446–483) | REMOVABLE — callers: dispatcher :803 + on_gemini, both removed [FACT] |
| cell 8: translate_with_chatgpt (494–545) | REMOVABLE — callers: dispatcher :810 + cell 18 example text, removed [FACT] |
| cell 8: NLLB trio (589–756) | REMOVABLE — callers: dispatcher :817, cell 19 override (removed), on_nllb/btn_nllb (removed); `ensure_nllb` ref at cell 19:102 is inside the removed override [FACT] |
| cell 8: dispatcher branches (803–822) | REMOVABLE **but see Amendment 1 — valid_engines literal at 850–852 is NOT in the list and does NOT auto-collapse** [FACT — the one functional gap] |
| cell 8: V-5 self-test subset (1584–1757) | OK with per-branch pruning guidance; Phase D sha16 gate will enforce [FACT] |
| cell 19: NLLB override (93–157), rescue half stays | REMOVABLE — rescue path has zero nllb references [FACT] |
| cell 25: btn_gemini/btn_nllb, gemini_key, 5 mode options, on_gemini/on_nllb, wiring, panels | REMOVABLE — **plus one latent item**: `rebuild_mode_panel`'s trailing `else:` branch (cell 25:430–431) references `btn_nllb`; unreachable once options are trimmed, but a dead branch naming a deleted widget is a NameError landmine — delete it or convert to explicit `elif` in the same edit-set → **Amendment 2** [FACT] |
| cell 15: quick_start_auto default (898); cell 18: text (599, 971–973) | REMOVABLE/EDITABLE [FACT] |
| cell 1: SECRET_SOURCES → {openrouter, hf} + MANGABD_SECRETS trim | REMOVABLE — hf_token consumers verified live (cell 5:779–787); cell 25:428 ref is a comment only [FACT] |
| cell 17: leak-test key generalization (963–973) | REQUIRED and correctly scoped [FACT] |
| Deliberately-kept list (manual plumbing, cell 22, cell 20/21, sentinel, closure, retry, glossary, export_ai_text) | All verified present and live [FACT] |
| **Missed (cosmetic):** cell 1:271 `translation.allowed_engines = ["manual","gemini","chatgpt","nllb"]` | No consumer anywhere (grep: definition only), so stale value is harmless drift — but add to the edit list for coherence → part of **Amendment 1** [FACT] |

Net: the ~−260-line list is **substantively sound** — exactly one functional omission (Amendment 1), one latent-landmine note (Amendment 2), one cosmetic addition. The ±20% HYPOTHESIS tag on line counts is fair.

## PB6 — BATCH PLAN M4-B1..B4 (A6): OVERLAP / COUPLING

- **B1 {8,22,25} → B2 {1,8,15,17,18,19,25}** sequenced on B1's merged head: overlap {8,25} is real but managed by sequencing; the B1→B2 (keyless-first) order is right — the Owner's primary workflow works before any key exists. D6 correctly left to PM. [judgment: sound]
- **B3 {9, +25 hint}**: no overlap with B4; mask-discipline bytes (cell 9:70–76) already designated protected; `inpaint_size_effective` meta addition is inside the single `mark_stage_done` call site (:569–579) — single-logical-change convention holds. [FACT]
- **B4 {7, +5}: touches Batch-2 protected territory.** Cell 7 contains the V-3 dual-candidate selector, 🟡 plumbing, and tie-break — all merged, S003-accepted bytes. The prompt-map insertion is a new hunk in the same cell as V-3's scoring; per the single-hunk audit convention this batch needs: sha16 of cell 7 baseline, V-3 plumbing byte-stability check, both-candidates-same-prompt fairness test, and the S008 regions-2–6 regression Phase A already specifies. → folded into **Amendment 6b** (B4 spec). [FACT: cell structure; requirement]
- M002 cells {14, 26} and Batch-1 mirror cells {11,12}: untouched by all four batches. [FACT]

## REQUIRED AMENDMENTS (all concrete, none structural)

1. **(Blocking for B2 spec)** Add cell 8:850–852 to the edit list: trim the hardcoded legacy prefix to `["manual"] + registry keys`; correct A2.3's "collapses automatically" and A2.6's "rejected by the dynamic list" claims — as written they are false.
2. **(Blocking for B2 spec)** Cell 25 `rebuild_mode_panel`: delete or make explicit the `else:` branch referencing the deleted `btn_nllb` (cell 25:430–431).
3. **(Blocking for B1 spec)** `_strip_llm_wrappers`: strip ONLY (a) pure-fence lines, and (b) non-header lines occurring BEFORE the first header-matching line; never strip any line matching `^\[[^:\]]+:\d+\]` or anything after the first header. Otherwise the guard itself becomes a silent region-loss channel.
4. **(B1 spec)** `build_external_ai_copy` must delegate to `build_ai_text_content` for the row walk (or carry a byte-coherence test); do not write a third copy.
5. **(B3 spec)** Ladder `except` scope: OOM-class errors only (`torch.cuda.OutOfMemoryError` + RuntimeError-with-OOM-message); deterministic non-OOM errors (e.g. empty-result) go straight to the existing OpenCV fallback; keep per-rung `inpaint_size_effective` recording. OOM-retry idempotency is now FACT (upstream `_infer` never mutates caller arrays).
6. **(A5 corrections)** (a) Reclassify R6 "SUDENLY" as a doubled-letter glyph miss and R2 as a dropped quoted glyph — both mid-crop; not crop-edge truncation. (b) Retarget the P1 bubble rider accordingly, and ADD a config-gated 2–4× crop-upscale A/B to the S008 acceptance (pixel-headroom evidence above); B4 must keep identical prompts across both V-3 candidates and refresh the cell 5:350–358 fallback prompt duplicate.
7. **(Wording)** Persistence invariant: allowed persistent surface = Colab userdata (Owner-controlled, already bootstrapped by cell 1); forbidden surfaces = notebook bytes / CONFIG / manifest / artifacts. Say exactly that in the STEP 0 panel copy.

## OBSERVATIONS (NON-BLOCKING)

1. Phase A's citation discipline is excellent — every spot-checked cell:line and upstream citation matched bytes (registry, dispatcher, sanitizer, mode_sel 7 options, REGION_TYPE_INSTRUCTIONS :254–260, zy config :297–300 comments verbatim, large_arch n_blocks=18). Zero fabricated citations found. [FACT]
2. A3.2's table actually UNDERSELLS the case: R6's "she was into me" → "সে আমার ভিতরে ছিল" is an uncited additional NLLB defect. [FACT]
3. A2.4's layer-1 status line and A3.4's status feedback both print to the Studio console — consistent with the existing `say()` pattern; no new surfaces. [FACT]
4. The A7-D1 supersede recommendation (close M003-Batch 3 as implemented+approved-but-not-S004-accepted) is coherent with this review: M4-B2 re-authors ~60 lines of Phase-D-proven patterns, and S004 against a 5-provider surface would validate code B2 deletes. Owner call, correctly framed. [judgment]

## VERDICT

**PHASE B: CONFIRMED WITH AMENDMENTS.**

All four Phase A tracks stand on independently re-verified evidence: the LaMa throttle arithmetic, upstream semantics, OCR pixel-budget conclusion, dead-code inventory, and quality case are CONFIRMED against notebook bytes, S003 artifacts, upstream `d6de6ab` source, and fresh HF/visual checks. Two functional spec defects (Amendments 1–2), two hardening requirements (3–4), one correction-plus-addition (6), and one scope exclusion (5) must be incorporated into the batch specs before implementation; none alters the architecture. With those folded in, M4-B1..B4 are cleared to proceed to Phase C/implementation planning under the standing per-batch protocol (branch → single-hunk → self-verify → Flash Phase D → Owner S-sample → squash-merge).

---

# MANGABD-004 — PHASE D VERIFICATION (GLM-5.3-Flash, independent reviewer, 2026-10-13)

Object under review: commit `ab2aa36` (branch `mangabd-004-b1-b2`, "WIP: MANGABD-004 Phase C B1+B2"), base `main @ 97a683a` (my Phase B review). Method: Phase D discipline per precedent — every check re-executed independently against the pushed bytes BEFORE reading `GLM_5_3.md` §Phase C; no source changes; no amend/merge. Instruments persisted outside the repo (`/home/z/my-project/scripts/m004d_*.py` + `m004d_stubs.py`, `m004d_nsbuild.py`; extraction `/home/z/my-project/m004d_work/`).

**Execution summary: 154 runtime checks + full static audit. Per-gate: E1 PASS · E2 FAIL (1 required fix) · E3 PASS · E4 PASS · E5 PASS · E6 listed. Overall: APPROVED_WITH_FIXES.**

## D1 — E1 DIFF & SCOPE AUDIT: PASS

- Topology: single linear commit `ab2aa36`, parent `97a683a`. numstat: notebook +629/−416, `GLM_5_3.md` +89/−2; 2 files, no renames (with `--find-renames`), `diff --summary` empty (no mode flips), all blobs 100644. [TEST RESULT: git plumbing]
- Secret scan on all 718 added lines: **0 hits** (ghp/gh_/sk-/sk-or-/AIza/hf_/credential-literal patterns). [TEST RESULT]
- Notebook JSON valid both refs (nbformat 4.0, 27 code cells); **27/27 cells AST-parse both refs**; cell-level and notebook-level metadata byte-identical for all 27 cells. [TEST RESULT: m004d_extract.py]
- Changed cells (0-based source comparison): **exactly {1, 8, 15, 17, 18, 19, 22, 25}**; other 19 byte-identical, including MANGABD-003 protected cells 6/7/11/12/16 and M002 guards 14/26. Per-cell deltas match the self-report exactly (c1 +23/−7 · c8 +398/−300 · c15 +1/−1 · c17 +5/−3 · c18 +2/−4 · c19 +2/−73 · c22 +39/−7 · c25 +168/−30 = +638/−425). [TEST RESULT]
- **ADJUDICATION of the disclosed 17/18 additions — both within scope, no behavior change beyond engine-name resolution:**
  - Cell 17 (+5/−3, c17:963–971): the config-export leak test is a NEGATIVE assertion (`secret_leak` must be False); the hunk generalizes the probed key family `gemini_api_key` → `openrouter_api_key` with identical semantics. Legacy-engine reference cleanup only. PASS.
  - Cell 18 (+2/−4, c18:597, 969–972): dashboard Commands HTML and the command cheat-sheet — `run_translation_all(engine="gemini")` → `"openrouter"`, and the 3-line gemini/chatgpt/nllb block → 1 openrouter line (`engine="manual"` line retained below, comment-documented). All three deleted engines are dead post-purge; keeping them would reference non-existent engines. PASS.
- Cell 19 shrink (−73): removes ONLY the "Fix NLLB src_lang" hotfix section (the `translate_with_nllb` override + banner line); the rescue half (`apply_translations_from_ai_file`, c19:19) stays intact — Flash PB5 "rescue half stays" honored. [FACT]

## D2 — E2 PURGE COMPLETENESS (B1): FAIL — one required fix (RF-1)

- **RF-1 (REQUIRED FIX): cell 1:288–293 — a dead `"nllb"` config block survives inside the live `MANGABD_CONFIG` literal:**
  ```python
  "nllb": {
      "model_id": "facebook/nllb-200-distilled-600M",
      "source_lang_code": "eng_Latn",
      "target_lang_code": "ben_Beng",
      "num_beams": 4,
      "max_length": 512,
  },
  ```
  This is a LIVE (non-comment) reference to NLLB model ids in the pushed bytes — the E2 gate ("zero LIVE references … NLLB model ids … outside comments") FAILS as written. It is inert data: a branch-wide consumer scan finds **zero** readers of `translation["nllb"]` (cell 8's block and consumers are gone; cell 19's hotfix is gone), and the residue also lands in the saved `config_v12.json` on disk. Behavior impact: none. Fix radius: 6 lines, single hunk, config literal — no sentinel, no coupling. This is the same category as my Phase B `allowed_engines` cosmetic finding (c1:271), which Phase C fixed; the sibling block 17 lines below was missed because the self-report's "16 legacy symbols" battery did not include the model-id string / dict literal. **Required before merge; everything else below is green.**
- Legacy-symbol sweep (branch, all 27 cells, case-insensitive, 23 terms incl. translate_with_gemini/chatgpt/nllb, ensure_nllb, get_nllb_bengali_bos_id, btn_nllb, gemini_key, GEMINI/OPENAI key env names, gemini_model/openai_model, genai, forced_bos, Seq2Seq): **0 live code references remain.** Remaining hits, all adjudicated: 2 comment-only mentions (c25:323 `gemini_key`, c25:538 `btn_nllb` — documentation of the removal, comment-only per my PB5 precedent); self-test rejection call-sites `switch_translator("nllb"/"gemini"/"chatgpt")` (c8:1628–1630 — these ARE the purge proof); UI copy naming ChatGPT/Claude/Gemini as paste destinations for the B2 workflow (c22/c25 — legitimate); `openai` SDK + `openai/gpt-4o-mini` for the OpenRouter adapter (legitimate). [TEST RESULT: m004d_e1e2_static.py, m004d_e2_broad.py]
- **valid_engines runtime:** verbatim cell 1+8 exec → `providers == {openrouter}` exactly; `switch_translator("openrouter")=True`, `("nllb")/("gemini")/("chatgpt")=False` with engine unchanged, `("manual")=True`; `valid_engines` is now dynamic `["manual"] + list(providers keys)` (c8:663–665) — Amendment 1 implemented, the hardcoded literal is gone. [TEST RESULT: m004d_h1_e2.py]
- **Sanitizer:** real `save_config` re-run post-registry writes `key_env` pointer to the disk file, no forbidden key names, no secret value; control test injects `api_key_env` → stripped from the REAL written file; nested `sanitize()` unit-probe preserves `key_env` / strips `api_key_env` at all levels (V-5 semantics intact). [TEST RESULT]
- **Dispatcher closure-bound:** monkeypatched fake adapter through the verbatim `translate_text` path returns `("ঢাকা", "openrouter", [])` with the closure passing `engine=`/`region_type=` through; flaky-adapter retry succeeds at attempt 3 through the closure; counterfactual `translate_with_retry(..., engine=...)` raises TypeError. `translate_with_retry` source **md5-identical to main** (`f954a15c`); `parse_ai_text`, `apply_manual_translation`, `export_ai_text`, `clean_translation`, `validate_bengali`, `get_translation_status` all byte-identical to main. [TEST RESULT]
- **SECRET_SOURCES:** `{openrouter_api_key: [OPENROUTER_API_KEY], hf_token: [HF_TOKEN, HUGGINGFACE_TOKEN]}` — hf_token kept; with-key re-exec of cell 1 loads the key from env into `MANGABD_SECRETS` + re-sets `os.environ`; no-key exec prints the banner (see D5). No secret anywhere in the diff. [TEST RESULT]

## D3 — E3 B2 SAFETY (manual copy-paste): PASS

- **Payload structure** (verbatim `build_external_ai_copy`): system prompt TOP + `══════════ TEXT TO TRANSLATE ══════════` banner (exactly once) + OCR text block BELOW; region_count == df rows; `build_external_ai_copy(page="02.jpg")` returns only that page (3/4); **delegation proven** — it calls `build_ai_text_content(page=page)` (Amendment 4; no third row-walk; `page=None` → all pages). [TEST RESULT]
- **Prompt coverage** (12 checks): register তুই/তুমি/আপনি; profanity-preserving (শালা/মাদারচোদ/মাগি + "DO NOT sanitize"); anger/emotional-intensity; cultural nuance (idioms/puns); SFX onomatopoeia (বুম); name transliteration incl. the S003-grounded কোগানেই/ওতেআরাই; [PAGE:ID] preservation; arrow separator; no-fences/no-preamble; [SKIP:OCR_FAILED] copy-through; one-line-in/one-line-out; glossary merged via the shared `build_glossary_prompt_lines("sfx")` path. [TEST RESULT]
- **`_strip_llm_wrappers` prefix-zone spec** (Amendment 3): code inspection confirms (a) pure-fence strip anywhere, (b) non-header preamble strip ONLY before the first data header, (c) hardening beyond the letter — any line CONTAINING a header pattern is never stripped (contains-header guard). **Silent-region-loss impossibility proven by an invariant battery on 7 adversarial replies** (fenced+postamble, glued fence-header, wrapped continuation, header-like preamble, glued-open+mid-fences, junk-only, empty): (a) no header-bearing line is ever removed; (b) every `[pg:id]` header is either parsed OR its full line appears in the V-4a `_unparsed` sentinel (visible); (c) sentinel fires with the offending text in every junk case. Fence-glued data lines reach the sentinel visibly, never silently dropped. Trailing postamble on a clean reply → visible 1-line unparsed warning while all regions still apply — per spec (visible > silent). [TEST RESULT: m004d_h2_b2.py]
- **V-4a sentinel path untouched:** `parse_ai_text` (c8), `_parse_ai_text_local`, `_validate_bengali_local`, `_apply_translations_fallback` (c22) all **byte-identical to main** (md5 a794681c / 5fa7f6da / 4dc9e50e / 583d662d); functional sentinel test passes (junk → `("_unparsed", 0)` with the line text). [TEST RESULT]
- **Round-trip:** payload → simulated external-LLM reply (preamble + ``` fence + 3 lines + closing fence + postamble) → paste-back → `apply_translations_from_text` → **3/3 applied**, df `translated_text` exact, `translator_engine="manual"`, `bengali_valid=True`, status updated; genuine-junk reply → 2/3 applied + sentinel warning names the broken line (visible). [TEST RESULT]

## D4 — E4 REGRESSION GUARDS: PASS

- **m002_sim_v2** on the branch notebook: **0 abort-class sites** (call map full); base `97a683a` calibration also 0 — instrument meaningful, M002 invariant preserved. [TEST RESULT]
- **Protected bytes:** cells 6/7/11/12/16 byte-identical to main (sha256 verified; c7 `4522a89c…`, c16 `e31bfdc3…` match the Phase-E-approved f58cd3c lineage); cell-14 guard + cell-26 `render_all_pages(force=False)` byte-identical and verbatim-present. [TEST RESULT]
- **ai.Text wire format:** old-format export file parses via BOTH branch parsers; strict + lenient outputs **identical to the base parsers** extracted from main (keys + full payload equality); coverage = 4 regions. Backward compat intact. [TEST RESULT]
- **Control Studio callbacks:** verbatim cell 25 exec under widget stubs; **all 15 buttons clicked** (14-button sweep + double-click-armed reset) — **zero NameError at click time**; missing upstreams degrade via `_safe()` to visible guidance. `on_or` wiring proven with a recording stub: called with `engine="openrouter", force=True`, model box applied to the registry on click (A2.4 layer-3). `on_apply` applies a fenced reply from the UI: 3/3 rows. [TEST RESULT: m004d_h3_studio.py]
- **Amendment-2 landmine GONE:** `rebuild_mode_panel` with `mode="nllb"` (unknown) runs without error and renders the `⚠️ অজানা mode` bubble; AST of the function contains no `btn_nllb`/`gemini_key` Name references; openrouter/manual/file subpanels all render. [TEST RESULT]

## D5 — E5 KEY UX (3 layers) + persistence invariant: PASS

- **Layer 1 — cell-1 banner:** no-key exec prints the boxed banner with the exact secret name `OPENROUTER_API_KEY`, the 🔑-sidebar path, and the STEP 0 pointer, plus "manual copy-paste needs no key"; with-key exec prints no banner. [TEST RESULT]
- **Layer 2 — STEP 0 panel:** first section of `studio_root` = "STEP 0 • 🔑 OPENROUTER KEY (auto translation)" containing `key_status` mirror, `or_key` Password, session-save and Colab-persist buttons, and the Amendment-7 security bubble (allowed surface = Colab userdata ONLY; forbidden = notebook/CONFIG/manifest/artifact). Status mirrors refresh from one updater. [TEST RESULT]
- **Layer 3 — model widget:** `or_model` pre-filled `openai/gpt-4o-mini` from the registry; click applies it to the registry (D4). [TEST RESULT]
- **No key ever reaches config/artifacts:** with `sk-or-v1-HARNESS-SECRET-…` set through the real UI callbacks: key ABSENT from `MANGABD_CONFIG` (JSON dump), every file on the (virtualized) disk incl. `config_v12.json`/manifest, `build_ai_text_content`, the copy payload, `build_translation_records_from_df` output, and `MANGABD_EVENTS`; key PRESENT only in `MANGABD_SECRETS`, `os.environ`, and Colab `userdata` — the three allowed surfaces. `userdata.set` failure degrades to plain instructions without crashing (A7-D7 fallback path exercised). [TEST RESULT]
- **translator_model sidecar (additive):** manual/empty rows → `""`; engine rows → registry model; row-level value wins. [TEST RESULT]

## D6 — E6 D7 DEFERRALS (Owner-side S005 checks; not attempted here)

1. `userdata.set("OPENROUTER_API_KEY", …)` dialog behavior in live Colab (the 🔐 persist button; designed fallback message verified offline).
2. Clipboard-write permission inside Colab output iframes (`navigator.clipboard` + `execCommand` fallback; visible textarea keeps manual Ctrl+C working regardless).
3. S005 acceptance proposal (per self-report C5, endorsed): fresh page → Upload → Detect+OCR → COPY FOR EXTERNAL AI → real external LLM → paste reply → Apply → render; metrics = parse rate on clean replies, sentinel behavior on preamble/wrapped/glued variants, register/profanity quality read vs the S003 NLLB baseline (A3.2), plus one live OpenRouter run with the Owner key.

## OBSERVATIONS (NON-BLOCKING)

1. **N-1:** `google-genai>=0.3.0` remains in cell 0's pip list; after the purge nothing imports it. Cell 0 is out of this batch's scope (byte-identical) — cleanup candidate for B4 or Owner housekeeping. [FACT]
2. **N-2:** cell 17's leak test is vacuous when no key is loaded (condition requires a non-empty secret) — pre-existing semantics carried over from the gemini era, unchanged by this batch. [FACT]
3. **N-3:** cell 22's file-based rescue path (`apply_translations_from_ai_file`) deliberately does NOT strip wrappers (self-report C5 disclosure) — machine-generated content, sentinel stays visible; coherent, endorsed. [judgment]
4. **N-4:** every trailing-postamble clean reply will show a 1-line unparsed warning by design (Amendment 3, visible > silent). If S005 finds it noisy, the fix is a Owner-taste tuning of the strip spec, NOT a silent-drop. [judgment]
5. **N-5:** self-report C0–C5 line claims spot-checked against bytes — per-cell deltas, amendment table, disclosure of the 17/18 additions and comment-only refs all accurate; the ONLY omission is the RF-1 residue (their legacy-symbol battery missed the model-id dict literal). [FACT]
6. **N-6:** "MANGABD-003 Batch 3 SUPERSEDED per A7-D1 (Owner approved skipping S004)" is a PM-relayed process decision — not verifiable from repo bytes; recorded as relayed. [ASSUMPTION]

## VERDICT

**MANGABD-004 PHASE C (B1+B2): APPROVED_WITH_FIXES.**

All five verification gates pass with one exception: **RF-1 — delete the dead `"nllb"` config block (cell 1:288–293, 6 lines, zero consumers, zero behavior change)** to satisfy the E2 purge gate as written. Everything else — purge completeness, closure dispatch, sanitizer survival, B2 payload/strip/round-trip safety, V-4a and wire-format preservation, M002 regression guards, Studio callback resolution, the 3-layer key UX with the persistence invariant — is verified green against the pushed bytes (154 runtime checks; instruments re-runnable from `/home/z/my-project/scripts/m004d_*.py`).

RF-1 may be landed by GLM-5.3 as a single follow-up commit on this branch (no amend of `ab2aa36`; same no-merge discipline) and re-verified with a scope audit of that one hunk; alternatively the Owner may waive it at S005 — my recommendation is to fix, since it is mechanical and the E2 gate is explicit.

**Gating preserved: merge remains gated on the Owner's S005 acceptance run (D6 items included). No amend, no merge from either agent until Owner acceptance via PM relay.**

## D-ADDENDUM — RF-1 DELTA VERIFICATION (fix commit `3c57583`)

**Object:** delta `f460143..3c57583` — single linear fix commit, parent = my Phase D report commit (no amend of `ab2aa36`, no merge; prescribed discipline followed). Re-verified from pushed bytes with 49 fresh checks (32 static `m004rf1_delta.py` + 17 runtime `m004rf1_runtime.py`; artifacts `m004d_work/rf1/`).

**Item 1 — diff scope: PASS.** numstat: notebook **0 insertions / 7 deletions** (single hunk `@@ -909,13 +909,6 @@`), self-report `GLM_5_3.md` +18/−1 docs-only, my FLASH file untouched, no renames/mode changes, secret scan on all 18 added delta lines = 0. Changed cells == **{1} exactly**; all top-level notebook fields identical; POST cell 1 == PRE cell 1 minus exactly 7 contiguous lines at 0-indexed 288..294 whose content byte-matches the dead nllb dict, with correct anchors (prompt-subdict closer above, `"translation"` closer below). **Citation reconciliation [FACT]:** my RF-1 cited "cell 1:288–293 (6 lines)" — the actual block is 7 lines including its own `},` closer (my citation under-counted by off-by-one); the landed deletion covers the complete block and nothing else. `PRE notebook == ab2aa36 notebook` (my report commit changed no notebook bytes).

**Item 2 — purge scan: PASS.** Tokenizer/regex dual-classifier over all 27 POST cells, 8 terms case-insensitive: **zero live (code-token) legacy hits notebook-wide.** nllb-family string-literal hit: only `c8:1628 switch_translator("nllb")` — the rejection self-test (D2 adjudication, purge proof). Comment-only: `c8:660`, `c19:2`, `c25:538` (removal documentation; PB5 precedent). Model-id/lang-code strings `facebook/nllb`, `nllb-200`, `eng_Latn`, `ben_Beng` = **0 occurrences anywhere, including comments**. `num_beams` hits (c1:252, c5:407, c5:973) adjudicated out-of-scope: generic OCR/Qwen generation config, byte-identical to main; main's second cell-1 occurrence `"num_beams": 4,` was the nllb block's own and is gone with it.

**Item 3 — save_config round-trip: PASS.** Real verbatim post cell-1+cell-8 exec in the sandbox: cell-1-time config on disk has **zero nllb residue** (inverts my E2-7 finding at `ab2aa36`); live `save_config()` → saved config deep-scan **no nllb key/value anywhere**; registry intact (`providers == {openrouter}`, `key_env == "openrouter_api_key"`, base_url/model intact, engine `manual`); `api_key_env` control still stripped live; no forbidden key names or secret values on disk; switch matrix rejects nllb/gemini/chatgpt. **PRE-vs-POST saved-config delta == exactly the `translation.nllb` subtree removed** (volatile session-id values normalized) — RF-1's on-disk persistence defect is gone with zero collateral config change. [TEST RESULT]

**Item 4 — regression guards: PASS.** `m002_sim_v2` fresh-kernel sim: **0 abort-class sites on both PRE (control) and POST**, identical 27-cell / 1838-call-map parity. 27/27 cells AST-parse. Protected cells 6/7/11/12/14/16/26 byte-identical PRE→POST **and** vs main `97a683a`; Phase C scope cells 8/15/17/18/19/22/25 untouched by the delta (== `f460143` bytes). [TEST RESULT]

**Instrument notes (harness-side, not repo defects):** two instrument bugs were caught and fixed mid-round and are recorded for ledger clarity — (1) parent-hash comparison used the abbreviated form against the full SHA (topology was in fact correct); (2) the pre/post saved-config diff initially mislabeled `value` deltas as additions and did not normalize session-stamped path *values* under stable keys (`paths.events_file`/`paths.manifest_file` embed the per-run session dir; cell-1 code is byte-identical between refs, so the asymmetry was harness-environment noise by construction). After fixes: static 32/32, runtime 17/17.

## ADDENDUM VERDICT

**RF-1: CLOSED.**

The fix is exactly what RF-1 prescribed — byte-surgical removal of the dead nllb config block, zero collateral change, all regression guards holding. With E2 now green and E1/E3/E4/E5 unchanged (their cells byte-identical through the delta), the Phase D verdict for Phase C (B1+B2) at `3c57583` is: **APPROVED** (E2's sole required fix landed and verified; non-blocking observations N-1..N-6 carry over unchanged).

**Gating: RF-1 is no longer a gate item. Merge remains gated solely on the Owner's S005 acceptance run (D6 deferral items included). No amend, no merge from either agent until Owner acceptance via PM relay.**

---

# MANGABD-004 — S005 ACCEPTANCE MEASUREMENT

**Object:** `samples/S005_manual` + `samples/S005_openrouter` (pushed to main @ `48fa3ca`; artifacts extracted via `git show`, untouched in place). Both samples: `original.jpg`/`inpainted.png`/`ocr.json`/`text_mask.png` md5-identical across the two paths (same upstream pipeline run, two translation paths). Page `02_1.jpg`, notebook commit `7f0e653` per metadata. Instruments: `scripts/s005_audit.py` (32 JSON/codepoint checks), `scripts/s005_pixels.py` (6 pixel checks + 12 crops), visual glyph reads from crops. 38 instrument checks + visual reads; evidence tags per discipline.

## S1 — TRANSLATION QUALITY (S005_openrouter vs S001/S002 NLLB): PASS

Baseline defects reproduced verbatim in S002 first [FACT]: R5 `কে ঐ যৌনসঙ্গম OTEARAH! ! এই বেশ্যা তাকে বা কিছু জানেন! ?` (যৌনসঙ্গম = "sexual intercourse" for FUCK; বেশ্যা = "prostitute"; honorific জানেন; scrambled order; untranslated OTEARAH; spaced `! !`); R6 `যে সে আমার ভিতরে ছিল` (literal "was inside me") + garbled purpose-clauses; R1 `Otarumi/おたるみ` misread; R4 register dropped (`সেই ব্যক্তি কে?`).

S005_openrouter [TEST RESULT]:
- **R5:** `ওটিয়ারা কে মাদারচোদ!? ওই কুত্তার মেয়ে কি তাকে চিনে বা কি!!?` — যৌনসঙ্গম GONE; **মাদারচোদ** (strong expletive) carries FUCK register; **কুত্তার মেয়ে** natural Bengali bitch idiom; **no** honorific (জানেন/আপনি absent); **no** scrambled order; no spaced `! !`. Render matches sidecar (crop-verified).
- **R6:** `আমার ভুল ছিল সে আমাকে পছন্দ করে বলে মনে করলাম। …গার্লফ্রেন্ড হবেনা।` — ভিতরে ছিল GONE; "was into me" → **পছন্দ করে** (likes me); confession-refusal semantics complete; danda `।` renders correctly.
- **R4:** `সালা সে কে!?` — THE HELL register preserved (NLLB dropped it). **R2:** one-letter-correct meaning kept. **R3:** `কোগানেই` correct transliteration (NLLB had কোগানাই); note "তুমি বোকা" is milder than DUMBASS — acceptable, intensity carried by R4/R5 neighbors.
- **R1:** corrected `Otearai/おてあらい` (not Otarumi); model even repaired the OCR typo "hiragani"→হিরাগানা. Register naturalness overall: colloquial, consistent punctuation (`!?`/`!!?` attached), idiomatic; minor clunk in R6 (`প্রস্তাব সরাসরি নাকি দিলো—বলে দিলো`) — non-blocking.
- **Minor defect found [FACT]:** R1 kana tail is mixed-script — sidecar codepoints contain `おてあら` + **Bengali ই** (`\u0987`) instead of い (`\u3044`); render shows the Bengali glyph mid-kana-run. Cosmetic, meaning intact.

## S2 — MANUAL COPY-PASTE WORKFLOW (S005_manual): PASS (evidence via pixels; sidecar lost to disclosed overwrite)

- **Sidecar `translator_engine: "manual"`: NOT PRESENT — [FACT] `S005_manual/translation.json` is byte-identical (md5-verified) to S005_openrouter's (6/6 rows `openrouter` + nemotron).** The later OpenRouter auto-translation in the same Colab session overwrote the sidecar before ZIP download (disclosed in metadata `sidecar_note`; render `final.jpg` 19:26:20 < sidecar mtime 19:29:10). This is an Owner-side capture-process artifact, NOT a notebook defect: B2's apply→sidecar write behaved as designed; the archive simply post-dates a subsequent run.
- **Compensating pixel evidence [TEST RESULT]:** manual render `final.jpg` differs from S005_openrouter's by **33,663 px** (metadata claimed 33,273; within JPEG tolerance) — **100% confined to the 6 detected regions (0 outside)**; per-region diffs R1..R6 = 7097/3685/8457/2122/3044/9258 → **all 6 regions re-rendered with the manual text; zero silent line-loss**. Manual phrasing differs from the openrouter sidecar (`হিরাগানায় বানান` vs `হিরাগানায় লেখা হয়` etc.) — independent manual translation confirmed.
- **Profanity preserved (crop-read verbatim):** R3 `আমার নাম কোগানেই, গাধার বাচ্চা!` — **গাধার বাচ্চা present** ✓; R5 `ওটেআরাহ আবার কেন শালা!!? ওই মাগি কি তারে চেনে নাকি!!?` — **শালা + মাগি present** ✓ (মাগি cruder than openrouter's কুত্তার মেয়ে — register faithfully carried); colloquial object-marking `তারে চেনে` natural; no honorific. R4 manual is milder (`ওই লোকটা আবার কে!?` — no expletive; not in the PM's expected-profanity list; noted).
- **`_unparsed` sentinel:** no sidecar evidence survives (overwritten) — [UNKNOWN at sidecar level]; pixel level: 6/6 regions show real translations, no sentinel text, no missing-region junk → sentinel did not fire, and if it had, output would have been visibly rendered [TEST RESULT].

## S3 — SIDECAR AUDIT (both samples): PASS with 1 adjudicated mismatch

- **`vertical_ocr` audit field: PRESENT** in R1 only (`chosen_orientation: rotate_90_clockwise`, `candidate_scores` cw/ccw 1.95/1.95; R2–R6 null) — Batch 2 V-3 audit intact [FACT].
- **`translator_model`: artifact records `nvidia/nemotron-3-ultra-550b-a55b:free` uniformly (6/6 rows) — NOT the PM-relayed `apodex/apodex-1.1-mini:free`.** Metadata `model_note` discloses the same and flags it to PM. [FACT] The sidecar mechanism itself works (per-row model recorded = model actually used; registry→box→adapter sync per cell 25:431-438). All quality findings in S1 judge the nemotron outputs. **Provenance mismatch = PM/Owner adjudication item, not a pipeline defect.**
- **`detections.json` geometry identical across S001/S002/S005_manual/S005_openrouter [TEST RESULT]:** field-level recursive diff = **0 geometry diffs** (x/y/w/h/quad/angle/region_type/parent). Byte-level diffs are benign: `page_id` naming (`02_1.jpg` vs `02.jpg`) across all 6 regions, plus 7th-decimal detector-score float noise vs S001 only (e.g., 0.8977065682 vs 0.8977066278). Detector stable.
- R2–R6 OCR text byte-identical between S005 and S002 (OCR pipeline stable); R1 differs exactly by the V-3 correction.

## S4 — VISUAL RENDERING QUALITY (both samples): PASS

- **"Regions 2–6 pixel-identical to S002" is unsatisfiable as literally written** — the translations differ between samples, so text pixels must differ. Measured per intent (Batch 1 fixes intact) [TEST RESULT]: (a) **outside-region pixels: 0 diffs vs S002 final for BOTH S005 samples** (threshold |dL|>8 over 1,012,800 px) — the base render is untouched, **zero new mask/render defects outside translated regions**; (b) in-region ink metrics consistent with Batch 1 style: R1 dark CJK luminance 33.1 (manual) / 26.9 (openrouter) ≤ 60 (S002: 31.0) — dark-ink fix intact; R2–R6 dark/mid component counts and luminance in family with S002.
- **R1 vertical note: corrected OCR rendered in BOTH paths** — kana run おてあら… clearly present (not おたるみ), T/L note text legible, dark ink ≤ 60 [TEST RESULT].
- **Minor render defect found [FACT]:** R1's trailing danda renders as a **tofu box** in both S005 finals, while R6's danda renders perfectly → R1-specific font-fallback artifact on the mixed CJK/Bengali line (danda after a kana run resolves to a CJK-font run without U+0964). Cosmetic, single glyph, meaning unaffected. Candidate small RF for a future batch (force script itemization / ZWSP after CJK runs); non-blocking.

## S5 — NO REGRESSIONS: PASS

- Batch 1/2 fixes preserved: dark ink ≤ 60 (S4), mask band + no banding outside regions (S4, 0 outside diffs), vertical OCR audit + corrected R1 reading (S3).
- MANGABD-002 reliability: `m002_sim_v2` fresh-kernel sim on branch HEAD `7f0e653` notebook = **0 abort-class sites** (27 cells, call-map 1838 — identical to Phase D/RF-1 baselines) [TEST RESULT].

## OBSERVATIONS (NON-BLOCKING)

1. **N-A (adjudication to PM):** translator_model provenance — relay said `apodex/apodex-1.1-mini:free`, artifact says `nvidia/nemotron-3-ultra-550b-a55b:free` (disclosed in metadata). Either the relay mis-stated the model or the Studio model box held a different registry value at translate time; the sidecar records what actually ran. Quality verdicts here are valid for the nemotron outputs.
2. **N-B (process recommendation):** manual-path sidecars are lost if another translation path runs later in the same session. Recommendation: download the ZIP immediately after each path, or have the Studio apply step snapshot `translation.json` per path (e.g., `translation.manual.json`) — future enhancement, not a defect. Optional: Owner may re-capture a clean manual-only run for sidecar-level proof; pixels already carry the evidence.
3. **N-C:** R1 mixed-script kana tail `おてあらই` in both paths (LLM text quirk; cosmetic).
4. **N-D:** R1 trailing-danda tofu after kana runs (renderer font fallback; candidate future RF).
5. **N-E:** manual R6 may carry a light translator addition at the tail (`ওই সব!`-like); unresolvable at crop resolution, non-blocking.

## VERDICT

**S005 ACCEPTANCE: BOTH ACCEPT.**

- **S005_openrouter: ACCEPT** — every PM-cited NLLB defect is fixed in the OpenRouter output (R5 expletive register, R5 syntax/honorific, R6 idiom), register naturalness is strongly improved, 6/6 regions translated, sidecars complete and self-consistent.
- **S005_manual: ACCEPT** — profanity preserved verbatim as specified (গাধার বাচ্চা / শালা / মাগি), zero silent line-loss (6/6 regions re-rendered, 0 outside-region pixels touched), sentinel clean at pixel level. The `engine: "manual"` sidecar sub-item fails only because of the disclosed post-render overwrite — compensating pixel evidence is conclusive; workflow itself verified functional.
- Two gate sub-items fail as literally written and are adjudicated non-blocking with compensating evidence: the manual sidecar engine marker (S2) and the translator_model relay mismatch (S3, N-A).
- Minor cosmetic items for the backlog: R1 kana tail (N-C), R1 danda tofu (N-D).

**Process note: with S005 accepted, MANGABD-004 Phase C (B1+B2) has now passed both gate conditions I set in Phase D (RF-1 closed at `3c57583`; Owner S005 acceptance measured here). Merge to main is now unblocked from the verification side — remaining sequence per PM/Owner relay.**

---

# MANGABD-005 — PHASE D VERIFICATION (BATCH 1) (GLM-5.3-Flash, 2026-10-14)

**Object under review:** commit `05bee82` on branch `mangabd-005-b1`, base main `5e70507` (parent verified — single linear commit, merge-base == base). Scope of review: B3 "LaMa full resolution + OOM ladder", declared Cell-9-only. Method: full re-execution of every check against pushed git bytes (no reliance on author-run scripts); instruments persisted at `scripts/m005d_e1_audit.py` + `scripts/m005d_e2_runtime.py`, artifacts in `m005d_work/`. No source changes; no amend; no merge. Instrument total: **46 checks + 3 fresh-kernel sim runs, all green.**

## E1 — DIFF & SCOPE: PASS (15/15 static checks) [TEST RESULT]

- Topology: `05bee82` parent == `5e70507`; numstat notebook **+270/−19**, `agents/GLM_5_3.md` **+45/−1** docs-only; `GLM_5_3_FLASH.md` untouched by author; delta = exactly 2 files; `diff --name-status` all plain `M`; `diff --summary` empty (zero mode/rename/new-file events); secret scan over all 315 added delta lines (ghp/gho/PAT/sk-/AKIA/AIza/xox/PEM) → **0 hits**.
- Cell scope: both refs valid ipynb JSON, 27 cells; **changed cells == {9} exactly** under both JSON-object compare and source-byte compare; all top-level notebook fields (nbformat/metadata/…) identical.
- Protected cells byte-identical vs base: union set {1, 6, 7, 8, 11, 12, 14, 15, 16, 17, 18, 19, 22, 25, 26} = MANGABD-002 {14, 26} + MANGABD-003 {6, 7, 11, 12, 16} + MANGABD-004 Phase C {1, 8, 15, 17, 18, 19, 22, 25}.
- **AST: 27/27 parse clean on both refs** (27 code cells); cell 9 is a code cell.
- The delta decomposes into exactly the 5 declared hunks: migration block (replaces `setdefault("lama_size", 1024)`), `_is_cuda_oom` helper, ladder body inside `lama_inpaint_full`, `inpaint_size_effective` in stage meta, self-tests 8–10. No stray edits inside cell 9.

## E2 — LADDER SEMANTICS: PASS (Amendment 5 verified by injection on verbatim cell-9 bytes) [TEST RESULT]

Harness fidelity: cell-9 source read from the `05bee82` git blob (sha-verified against the diffed extraction); cell-5 `_run_async` + `clear_gpu_cache` exec'd **verbatim**; fake `torch.cuda.OutOfMemoryError` implemented as a **RuntimeError subclass** (mirrors real torch), storage/log stubs. Two instrument-side bugs found and fixed during harness shakedown (asyncio/gc kernel-state seeding; exec-time self-test traffic contaminating measurement channels — fixed by snapshot-then-reset). Zero repo impact; documented per RF-1 precedent.

- **OOM-only retries, both classifier paths:** message-match `RuntimeError("CUDA out of memory…")` at 2048 → steps down, success at 1536 (sizes [2048, 1536], 1 cache-clear); `torch.cuda.OutOfMemoryError` subclass with a message NOT containing "out of memory" → also classified OOM → steps down (isinstance branch is message-independent).
- **Every non-OOM exception goes straight to fallback:** non-OOM `RuntimeError` → propagates after **exactly 1 rung attempt, 0 cache-clears**; page-level integration confirms landing: `engine=opencv`, `fallback_used=True` (E5.4 probe). Empty result (`None`) → deterministic `RuntimeError("LaMa returned empty result")` after 1 rung, **no ladder retry** (raise sits outside the rung try — structural Amendment 5 guarantee).
- **Mid-ladder non-OOM:** OOM at 2048 then non-OOM at 1536 → immediate raise; 1024 never attempted.
- **All-rungs OOM (mixed classification):** full ladder [2048, 1536, 1024] attempted, 3 cache-clears, exactly **one** `RuntimeError("LaMa OOM at every ladder size [2048, 1536, 1024] — …")`; `last_size_effective` stays None.
- **clear_gpu_cache between rungs:** count == number of OOM rungs in every scenario (1/1/3/1 as applicable); guarded call, WARN logged per rung.
- **Ladder arithmetic [owner, 2048, 1536, 1024], owner rung = config value when set:** owner 1024 → [1024]; 1536 → [1536, 1024]; 2048 → [2048, 1536, 1024]; 3072 → [3072, 2048, 1536, 1024] — healthy first-rung success + all-OOM full traversal, each ending in the single ladder RuntimeError.

## E3 — CONFIG FLOW & DISCLOSURE PC-C1.1: PASS (revert adjudicated; cleanup scheduled, not blocking)

- **FACT:** cell **1:295 still hardcodes `"lama_size": 1024`** (cell 1 protected, byte-identical base==branch; fresh `MANGABD_CONFIG = {` dict literal at cell 1:180).
- **Effective 2048 at inpaint call time — PROVEN:** fresh verbatim cell-9 exec seeded with the exact cell-1 inpainting literal (AST-extracted) fires the migration → startup print `LaMa size : 2048`, config `lama_size == 2048`, and the first ladder rung called at 2048. Explicit owner values respected (1536/2048 no stomp); missing `inpainting` key → setdefault+upgrade → 2048. The override is conditional **assignment** (None|1024 → 2048), as disclosed.
- **Order-robustness ADJUDICATION — revert is REAL, runtime-proven:** simulating a warm-kernel cell-1 re-run after cell 9 (config replaced by the fresh cell-1 literal) → `lama_size` reverts to 1024 and the next inpaint runs a **single rung [1024]** (`cfg.get("lama_size", 2048)` cannot save it — key present). Self-healing proven: re-running cell 9 re-fires the migration (1024 → 2048).
- **Ruling — the 1-line cell-1 cleanup does NOT need to be pulled into an earlier batch; B3 stands without it.** Reasons: (i) the revert is unreachable in the canonical fresh Run All (cell 1 precedes cell 9; m002-sim flow); (ii) it self-heals on any cell-9 re-run; (iii) consequence is quality-only — 1024 is exactly pre-B3 behavior and the most VRAM-safe rung, ladder still armed; (iv) it is no longer silent — stage meta `inpaint_size_effective` records the effective rung per page; (v) fixing it requires touching cell 1, outside this batch's authorized "Cell 9 ONLY" scope — pulling it in would break E1's exactly-{9} and the single-logical-change convention. **Requirement:** schedule the cell-1:295 literal cleanup (1024→2048) in the next batch authorized to touch cell 1, or a standalone 1-line micro-batch, before MANGABD-005 closes. PC-C1.1 disclosure verified accurate.

## E4 — MEMORY ORDERING: PASS

- **Static:** exactly two `model_manager.` touches in all of cell 9 — `unload_all(exclude=["lama"])` (L398) then `ensure_lama()` (L405), both inside `lama_inpaint_full` (source span 386–482); no other load/unload path exists in the cell. The unload block is byte-identical to the M004-audited state (unchanged diff context).
- **Runtime:** event order `[("unload_all", ("lama",)), ("ensure_lama",)]` observed before every injected inpaint call across all scenarios. Between rungs only `clear_gpu_cache()` runs — no model loads. Per code path, nothing else loads concurrently at the native rung.
- Live T4 magnitudes remain **HYPOTHESIS** (E6 deferral — sandbox has no torch/CUDA; ordering is what Phase D could prove, and it is proven).

## E5 — REGRESSIONS: PASS

- **m002_sim_v2 fresh-kernel sim:** calibration on pre-002 base `aabc592` → **exactly 1 abort site** (cells[14]:40 — reproduces the Phase A calibration); base main `5e70507` → **0 sites**; branch `05bee82` → **0 sites**. Call map 1838 → 1874 (+36 = the new self-test calls in cell 9); no new abort-class findings.
- Protected cells byte-identical (see E1); 27/27 AST.
- **Self-tests 10/10 on pushed bytes:** verbatim cell-9 exec in the harness reports `Cell 9 completed, tests_passed=10, tests_total=10`, zero ❌, `Cell 9 result: SUCCESS`; new B1 tests named in output (steps-down / Amd5 no-retry / all-rungs single-error).
- **Stage meta records `inpaint_size_effective`** — integration-proven on `inpaint_page`: OOM step-down page → `engine=lama, fallback_used=False, inpaint_size_effective=1536`, artifact saved; all-rungs-OOM page → `engine=opencv, fallback_used=True, inpaint_size_effective=None`, 3 ladder WARNs + 1 fallback WARN logged; non-OOM page → opencv, None.
- In-cell protected baselines intact: mask discipline constants, `unload_others` block, OpenCV-Telea path, `min_mask_pixels` gate, §8 live-test gate (`RUN_LIVE_INPAINT_TEST = False`) — all outside the 5 hunks (byte-verified).

## E6 — DEFERRALS (recorded, NOT attempted, per directive)

1. **Live T4 VRAM measurement per rung** with the <12 GB gate at the native rung — Owner-side; requires real CUDA. Contract-level proof delivered here (size argument handed to `lama.inpaint` per rung; ladder traversal).
2. **S007 acceptance sample** (native-rung `inpainted.png` vs S003 baseline diff + visual quality) — Owner-side acceptance run; remains the merge gate.

## OBSERVATIONS (NON-BLOCKING)

1. **N-1 (nano):** `int(_lama_size_legacy)` would raise ValueError on a non-numeric config value — unreachable via any notebook-produced config (sole source is the cell-1 literal), fails loud at cell-9 load. Note only.
2. **N-2:** a deliberate owner value of 1024 gets **no step-down rungs** (fixed rungs are strictly below owner; 1024 is the floor) — spec-conformant, but the Owner should know that selecting 1024 removes OOM-ladder protection.
3. **N-3 (cosmetic, disclosed by author):** §8 keeps its number after tests 8–10 were inserted in §7 — non-renumber accepted.
4. **N-4:** author's 44-check self-verification suite NOT relied upon; all evidence above re-executed by independent instruments (46 checks + 3 sims).

## VERDICT

**MANGABD-005 BATCH 1 (B3): APPROVED.**

- E1 PASS — scope exactly {9}, protected bytes intact, secrets clean, AST 27/27.
- E2 PASS — OOM-only ladder semantics proven by fault injection on verbatim bytes, both OOM classifiers, Amendment 5 structurally guaranteed.
- E3 PASS — effective 2048 proven; warm cell-1 re-run revert confirmed and adjudicated bounded/self-healing/observable; cell-1 cleanup scheduled as tracked follow-up (non-blocking).
- E4 PASS — unload→ensure ordering proven statically and at runtime; no concurrent loads.
- E5 PASS — 0 abort sites with calibration reproduced; 10/10 self-tests; stage meta records the effective rung.
- E6 — Owner-side deferrals stand (T4 VRAM gate; S007 acceptance). **Merge gate remains the Owner's S007 acceptance run.**

---

# MANGABD-005 — S007 ACCEPTANCE MEASUREMENT (B3 merge gate)

Reviewer: GLM-5.3-Flash · 2026-10-14 · Measure-only run: **zero source/sample changes, no amend/merge.**

**Inputs (FACT):** Owner archive `S007_mangabd005_02.zip` @ main `8445328` (7 files: original.jpg, text_mask.png, detections.json, ocr.json, inpainted.png, final.jpg, translation.json; all rasters 844×1200). Baseline `samples/S003_batch2/` @ main (extracted via `git show`; repo samples untouched). Branch under gate: `mangabd-005-b1` @ `05bee82` (notebook blob `8c4a5b87`). Instruments: `s007_measure.py` / `s007_localize.py` / `s007_visual.py`; artifacts + zoom crops in `s007_work/` (outside repo).

## G1 — PROVENANCE + RUNG: STAGE META ABSENT → PIXEL-EVIDENCE FALLBACK (as directed)

- **FACT — the archive carries no metadata:** no `metadata.json`, no stage-meta sidecar; `detections.json`/`ocr.json`/`translation.json` contain **no** `notebook_commit`, `engine`, or `inpaint_size_effective` fields (union of per-region keys checked). Therefore both metadata sub-gates — `notebook_commit == 05bee82 blob (8c4a5b87…)` and `engine=lama ∧ inpaint_size_effective=1200` — are **UNVERIFIABLE from the archive as delivered**. Said explicitly, per the gate directive; the rung claim is carried by pixel evidence only, and 1200 specifically cannot be distinguished from 1536/2048 by pixels alone (residual uncertainty recorded, not adjudicated away).
- **FACT — upstream provenance holds:** `original.jpg` md5 `446b3575…` and `text_mask.png` md5 `2d74dcb7…` are **byte-identical to S003's** → same page, same mask, clean A/B basis. `detections.json` geometry field-identical across all 6 regions except `page_id` naming (`02.jpg` vs S003's rendered `02_2.jpg`), **zero detector-score noise**; per-region OCR payloads identical (file byte-diff = embedded region naming only). `page_id=02.jpg` matches the task claim.
- **Pixel evidence on engine/rung (HYPOTHESIS-grade consistency, not proof):**
  - Reconstruction everywhere is texture-synthesis class — **no OpenCV-Telea signature** (no directional smear/wash plates in any mask interior inspected at 4×–10×). OpenCV fallback is pixel-excludable as the primary engine.
  - In-mask *artwork* strokes preserved through the mask are **fuller-weight in S007 than S003** (r2 stroke window x285–305/y100–140: original 227 dark px → S003 104 → S007 115; the delta sits on the stroke's AA fringe). This is the expected signature of **native-resolution processing (no 1200→1024→1200 resample round-trip)** vs the S003-era rung. (HYPOTHESIS: S003 ran at 1024 — consistent with that era's hardcoded cell-1:295 literal; S003's metadata discloses no inpaint fields, so this is inference, not fact.)

## G2 — INPAINT QUALITY A/B vs S003 `inpainted.png` (mask ∩ bbox, lum<160) [TEST RESULT]

| region | zone px | S007 ink | S003 ink | Δ | strict ≤ |
|---|---|---|---|---|---|
| r1 (vertical TL note) | 18,178 | 0 | 0 | 0 | ✓ |
| r2 | 13,370 | 52 | 46 | **+6** | ✗ by 6 px |
| r3 (spiky bubble) | 36,309 | 558 | 619 | −61 | ✓ |
| r4 | 10,241 | 0 | 0 | 0 | ✓ |
| r5 | 17,228 | 37 | 40 | −3 | ✓ |
| r6 (box) | 26,226 | 0 | 0 | 0 | ✓ |
| **total** | | **3,636** | **3,714** | **−78** | ✓ |

- **r2 +6 px adjudicated — not residual text (pixel-map evidence):** 45 of S007's 52 px are the **same physical remnant** as S003's (overlap map: both=45, only-S007=7, only-S003=1). The 7 unique px have lum 115–153 — AA fringe of the artwork stroke both runs preserve inside the mask; S007's reconstruction carries marginally fuller stroke weight (closer to the original's 227 dark px). The bold fragment nearby is **unmasked original text kept identically by both runs** (mask-coverage map, x285–295/y121–136) — inherited coverage limitation, not an S007 artifact. Strict letter of the gate fails by 6 px (0.045% of zone); gate intent — "no more residual TEXT than S003" — is satisfied. Documented per the S005 letter-vs-intent precedent; Owner may overrule.
- **r3's 558/619 px identified:** reconstructed **hatch/screentone texture** at the bubble's bottom tip (dense thin strokes crossing the mask), not text. Pixel map at the densest cell: the bold diagonal stroke is dark in original AND both inpaints (preserved artwork); original text strokes removed by both; window totals S007 307 vs S003 332.
- **Tight zones at 4×–10× — S007 smoother in all four inspected:** r1 column border line (S003 grey streak + ragged edge → S007 clean); r6 box border (S003 grey wash bleeding into the column → S007 removed, edges crisper); r5 bubble-border tip (S007 termination cleaner, screentone identical); r4 stroke edge (S007 tighter AA). Consistent with native-rung reconstruction.

## G3 — NO NEW DAMAGE: PASS [TEST RESULT]

- Outside-mask, inpainted A/B (S007 vs S003): p50=0, p99=0, max |Δ|=33, **1 px >16, 0 px >64** — essentially byte-identical artwork.
- Inpaint bleed vs own original (outside mask): S007 2 px >16, max 44 — same class as S003's own bleed (2 px >16, max 25).
- final.jpg A/B outside mask: 588 px >64, **100% within region bboxes (dist=0)** — the translated-text replacement class (by design), not artwork. Same class in S003 (which has more: 176 vs 81 px >64 for final-vs-original outside regions+6px) — **S007 cleaner than baseline**, zero new holes or smears; speed-lines/clouds/borders/building sentinels visually identical (crops at 3×).

## G4 — RENDER PARITY: PASS [TEST RESULT]

- All 6 translated regions have text blocks present: new-ink 894–3,807 px per region, mean lum 27–87 (dark). Overflow band (+10 px outside bbox): 0–4 px per region, all at lum 155–159 — sub-threshold AA fringe, **no glyph overflow**.
- r1 vertical note: dark (ink p50 lum 74), seated (per-band x-center σ p50 8.6 px over 23 bands), correct vertical layout. Kana render as dark in-column blocks — **the same Batch-1 signature as the S002 and S003 baselines** (inherited CJK-fallback tofu class, N-D backlog; unchanged, not a regression).
- r2–r6: proper Bengali shaping at 3× (conjuncts ক্ষরটা/শালা/স্ত্রী correct, danda intact, r6's 10-line block fits its box exactly). `translator_engine=manual`, `bengali_valid=true` ×6.

## VERDICT

**S007: ACCEPT** — G2/G3/G4 PASS on measurement (G2 with the documented r2 letter-deviation: +6 AA-fringe px on a shared inherited remnant, pixel-map-evidenced, zero new text residual, total −78); G1 stage meta **absent from archive** — reported as such, pixel fallback consistent with native-rung LaMa and excludes OpenCV fallback, with the 1200-specific value left UNVERIFIABLE (metadata, not pixels, can prove it).

- **The merge gate for `mangabd-005-b1` is discharged from the verification side.**
- Recommendations (non-blocking): (1) future acceptance archives should include `metadata.json` with `notebook_commit` + per-page stage meta — Phase D E5 already proves the notebook emits `inpaint_size_effective`, so the field exists and was simply not exported into the zip; (2) N-D kana-fallback tofu in r1 remains a known cosmetic backlog item, unchanged since Batch-1.
- Artifacts: measurement JSON `s007_work/measure_summary.json`; 20 evidence crops `s007_work/crops/`; instruments `scripts/s007_{measure,localize,visual}.py`. Repo: report-only commit, samples/ and notebook untouched.

---

# MANGABD-005 — PHASE D VERIFICATION (BATCH 2): LENIENT PASTE-BACK PARSER (GLM-5.3-Flash, 2026-10-15)

**Object:** commit `122e353` on `mangabd-005-b2` (base = `main @ 8445328`, single linear parent, no amend/merge). All checks re-executed on the pushed bytes (`git show` extraction, sha256-chained cell custody: cell 8 `e6ab34c1b7280249`→`49c65fe11e19ac41`, cell 22 `c3f27c598b84b59f`→`952d5abff984b2f4`, cell 25 `0de59d248995c5e0`→`f92f6395d1478330`; notebook blob `7f94b553e60e43eb`→`a88d62adfa0b7ec4`). No source or sample changes. Instruments (all re-runnable, artifacts in `m005b2_work/`): `m005b2_e1_audit.py` 13 checks; `m005b2_e2_runtime_v2.py` 53 checks (verbatim-byte exec); `m005b2_e6_static.py` 18 checks (AST + 3-way merge + merge-tree); `m002_sim_v2.py` on base/branch/merged notebooks.

## INSTRUMENT DISCLOSURE — three reviewer-harness bugs found and fixed mid-verification

All three were bugs in MY instrument, not in the branch. After each fix the affected suite was re-run from scratch on the same pushed bytes; the tallies below are the post-fix runs. [FACT]

1. **BUG-1 selftest event-read:** cell 8 emits `log_event("Cell 8 completed", level="INFO", tests_passed=…, tests_total=…)` — the counts arrive as **kwargs**. My stub dropped `**kw` and the reader indexed slot 2 of a 2-tuple → `tests_passed=None` false-FAIL. Fix: stub stores `(level, msg, kwargs)`; reader now reports event kwargs `tests_passed=22 tests_total=22`, cross-checked against a statically-extracted `run_test` name inventory (23 static call sites = 22 runtime tests + the network-gated "Live translation test", which is skipped-not-failed in the harness; all 22 runtime names ✅ in stdout, zero ❌, `Cell 8 result: SUCCESS`).
2. **BUG-2 AST def-delta:** my first def-delta sliced each `def` from header line to the next `def ` line, so module-level code appended after a def was attributed to it — false-flagging `switch_translator` (the new B2 regex/comment block sits between it and the new helpers) and `run_test` (the new module-level Tests 16–22 follow it), and in cell 22 `_validate_bengali_local` (the `_LOCAL_*` block was inserted before `_parse_ai_text_local`). Fix: per-def `ast.dump()` equality (comment/blank-line immune) + `ast.get_source_segment` byte equality for the byte-identity claims.
3. **BUG-3 apply parity:** the parity harness passed a **dict** to `apply_translations_from_text`, which takes the **raw paste text** and parses internally → both refs applied 0 → "0 vs 0" false-FAIL. Fix: identical paste text through both refs' verbatim cell-22 bytes; count/df/save/fields compared.

## E1 — SCOPE: PASS (13/13 + 3 field checks)

- `git show --numstat`: notebook +623/−70, `agents/GLM_5_3.md` +51/−0, exactly 2 files touched; `agents/GLM_5_3_FLASH.md` untouched by this commit; no mode changes, no renames, no binary, all blobs 100644. Secret scan (api-key/token/private-key patterns) 0 hits. [TEST RESULT]
- Cells: 27 vs 27; changed cells exactly **{8, 22, 25}**; the other 24 cells byte-identical to base. On the three changed cells the non-source fields (`execution_count`/`outputs`/`metadata`/`cell_type`) are byte-identical to base — only `source` changed. AST parse **27/27 both refs**. [TEST RESULT]

## E2 — SEMANTICS (verbatim bytes): PASS (24 checks: 19 battery + 5 end-to-end)

- **Unescape before any regex AND before `_strip_llm_wrappers` header detection** — verified both statically (apply-flow pre-unescape block precedes the wrapper-strip call in `apply_translations_from_text`) and end-to-end: paste `Here is your translation:` + ``` fence + **escaped** `[02.jpg:1]/[02.jpg:2]` data lines + postamble through the REAL combined cell8→cell22 flow → **base applies 0** ("No valid lines found" — the escaped header never sets `seen_header`, the whole reply is eaten by the M004-Amendment-3 preamble zone: the silent-drop gap, proven present) → **branch applies 2/2** with `⚠️ 1 unparsed line(s)` (postamble) and `📋 Lenient variants used: unescaped=2, …` visible; df updated with engine `manual`, `bengali_valid=True`. Gap closed, visibly. [TEST RESULT]
- **Single-line blob split:** one-line two-tag blob → both entries + `split_blobs=1` + leading junk reported via sentinel. **FIRST-arrow split:** `→ -> => ⇒ ➔ ➡` all 6 accepted; multi-arrow `Go → now → যাও` → original `Go`, translation `now → যাও` (first arrow). [TEST RESULT]
- **Arrowless:** Bengali-only accepted (`original_text=""`, `arrowless` counted); mixed English+Bengali accepted; English-only → unparsed with the `source-only line? (no Bengali after tag)` hint. [TEST RESULT]
- **Placeholders:** `X→ / () / (-) / - / N/A / n/a` → 6 skips, zero entries, `skipped_lines` len 6; good line on the same paste still applies. **Stem-match:** `[02.jpg:1]` vs session `{02_1.jpg}` → unique accept + 🟡 `stem_notes`; `[02:1]` vs `{02.jpg, 02_1.jpg}` → ambiguous → unparsed report; zero candidates (`09.jpg`) → raw page kept (surfaces as the parsed-N vs applied-M gap at apply time, never silent); exact-key hit → no sentinel. **Duplicates:** last-wins + counted. **V-4a sentinel:** present-with-full-payload when anything is reportable, absent on clean strict pastes (M004 output parity). [TEST RESULT]
- **Variant summary on both apply paths:** the one-line `📋 Lenient variants used: …` prints in `apply_translations_from_text` upstream of the apply fork, proven printing on BOTH sub-paths — the `apply_manual_translation` path (combined cell8+cell22 E2E, engine `manual`) and the `_apply_translations_fallback` path (cell-22-standalone parity run, engine `manual_paste`). See NOTE N-1 for the file-upload flow reading. [TEST RESULT]

## E3 — OWNER FIXTURES: PASS

- Fixture (a) escaped+arrowless: 2/2 entries, `original_text=""`, `unescaped=2, arrowless=2`; (b) escaped+arrow: 2/2 with originals + `unescaped=2`; (c) raw+arrow: 2/2 strict, NO sentinel. 100% parse on all three. Tag-less junk through the real cell-22 apply path: 0 applied, unparsed report visible, df untouched. Local mirror parity: `_parse_ai_text_local` output == `parse_ai_text` output on fixtures (a)/(b)/(c). `ai.Text` export byte-preserved: `export_ai_text` source-segment byte-equal base↔branch; payload body keeps the `[02.jpg:1] Hello →` wire format. [TEST RESULT]
- **Provenance (disclosed, PC2-C3):** the three fixtures are shape-constructed with S005-attested Bengali text — no literal Owner sample text existed in the repo/relay. This is why the merge gate below stays a live retest. [FACT]

## E4 — SYSTEM PROMPT / COPY PAYLOAD: PASS

- Rule 5 — `5. NEVER escape brackets with backslashes; keep tags exactly [page:id]; one line per region.` — added to `manual_copy_prompt` (cell 8 config). There is exactly ONE COPY payload construction site (`btn_copy_ai` → `on_copy_ai` → `build_external_ai_copy`, whose TOP delegates to `_build_external_ai_system_prompt`, which embeds `manual_copy_prompt` + glossary). Verified **dynamically**: `build_external_ai_copy()` (all pages) and `build_external_ai_copy(page=…)` payloads both contain rule 5 + `TEXT TO TRANSLATE` + the 2-region wire body. `build_ai_text_content` + `build_external_ai_copy` are source-segment byte-identical base↔branch — the amendment rides the template, builders untouched (V3.17). [TEST RESULT]
- UI hints: cell-22 `show_text_for_translation` instruction block + `step_3_manual_translate_paste` placeholder, cell-25 `ta_tgt` placeholder (exactly 1 non-def top-level statement changed) + `on_copy_ai` say() hint — all carry the lenient acceptance copy (escaped `\[ \]`, `->`/`=>`/`⇒`, শুধু-বাংলা lines). [TEST RESULT]

## E5 — REGRESSIONS: PASS

- **Cell-8 self-tests 22/22**: event kwargs `tests_passed=22 tests_total=22`; all 22 runtime test names green in stdout; zero ❌; `Cell 8 result: SUCCESS`; no RuntimeError (any failed test raises). [TEST RESULT]
- **m002_sim_v2 fresh-kernel sim**: base `8445328` = 0 abort sites, branch `122e353` = 0 abort sites, **merged (B1 cell 9 + B2 cells 8/22/25) = 0 abort sites**; instrument calibration reproduced (pre-002 `aabc592` = exactly 1 abort site, cells[14]:40). [TEST RESULT]
- **Apply semantics unchanged**: `apply_manual_translation` source-segment byte-identical; `_apply_translations_fallback` AST-identical; parity run (same paste, both refs) → count 3/3 equal, DataFrames **byte-equal** (translated_text/status/translator_engine/bengali_valid identical: `manual_paste`/`translated`/True on the fallback path, `manual`/valid on the combined path), save fired once on both sides. **Protected cells**: 24 non-target cells byte-identical; **B1 cell 9 untouched** here (== base main state, pre-B3). [TEST RESULT]

## E6 — ADJUDICATIONS

- **Tests 4/5 baseline updates = directive conformance, not drift.** Base Test 4 expected `parsed[("page2.jpg",1)]["translated_text"] == ""` — a silent empty entry for a `No translation →` line; branch Test 4 expects the placeholder-skip contract (`("page2.jpg",1) not in parsed` + sentinel `placeholder_skipped==1` + len 3 = 2 entries + sentinel) — this IS directive step 6 ("placeholder … skip+visible report"). Base Test 5 expected the M004 last-arrow rsplit (`"Go → now → যাও এখন"` → `"যাও এখন"`); branch Test 5 expects FIRST-arrow (`"now → যাও এখন"`, original `"Go"`, renamed `parse_ai_text arrow-first (B2)`) — this IS directive step 4 ("translation = text after the FIRST arrow"). Both updates are disclosed in the code comments and in PC2-C1/C3 ("directive supersedes"), and no `rsplit` split remains in either B2 parser. **CONFORMANT.** [FACT]
- **Disjoint-cell coexistence for the future merge: VERIFIED.** Per-cell 3-way merge (base `8445328` / ours B2 `122e353` / theirs B1 tip `93de3f8`): zero cell conflicts; merged notebook = B2 bytes on all cells except cell 9 = B1's; AST 27/27 on the merged bytes; m002 sim on the merged notebook = 0 abort sites. `git merge-tree --write-tree` (B1 tip × B2): the **notebook auto-merges cleanly** (disjoint cell regions); the sole conflict is `agents/GLM_5_3.md` — exactly the Owner's disclosed docs-reconciliation note (both branches append a CURRENT-PHASE header entry). Trivial docs conflict, flagged for PM, no notebook risk. [TEST RESULT]

## NOTES (NON-BLOCKING)

1. **N-1 ("both apply paths" reading + upload flow):** I read "both apply paths" as the two apply sub-paths of the paste flow (`apply_manual_translation` / `_apply_translations_fallback`) — the variant summary prints on both (proven above). The **file-upload flow** (`translate_manual_upload` → pop → `apply_manual_translation`) does not print the parse report — but neither did the M004 base (the sentinel was silently carried, never printed; B2's pop is strictly an improvement for count truthfulness). If the PM intended the upload flow to print the variant summary too, that is a 2-line follow-up for a future cell-8-authorized batch; no B2 gate depends on it.
2. **N-2 arrow superset (disclosed):** `➔/➡` kept — M004's cell-22 parser already accepted them (`arrow_candidates` in base), so B2 is strictly more lenient, aligned with the batch goal.
3. **N-3 placeholder scope (disclosed):** the check also applies to the post-arrow translation side (`English → N/A` → skip+report) — safer than applying an "N/A" as literal text.
4. **N-4 docs at merge:** besides `GLM_5_3.md` (disclosed), `agents/GLM_5_3_FLASH.md` now carries review records on BOTH branches (B1: Phase D + S007; B2: this report) — a second trivial docs conflict of the same reconciliation class at merge time.
5. **N-5 double-unescape safety:** the apply-flow pre-unescape count merges with the parser's own count (`unescaped=2` shown exactly once in the E2E, 2+0) — idempotent replace, verified live.

## VERDICT

**MANGABD-005 BATCH 2 (LENIENT PASTE-BACK PARSER): APPROVED.**

| Gate | Result |
|------|--------|
| E1 SCOPE (cells {8,22,25}, 24 byte-identical, secrets/mode, AST 27/27) | **PASS** |
| E2 SEMANTICS (unescape-first gap closure, blob split, FIRST-arrow, arrowless rule, placeholders, stem-match, duplicates, V-4a, variant summary) | **PASS** |
| E3 OWNER FIXTURES (a/b/c 100%, junk reported-not-applied, export byte-preserved) | **PASS** |
| E4 SYSTEM PROMPT (rule 5 in every COPY payload, dynamic; UI hints) | **PASS** |
| E5 REGRESSIONS (self-tests 22/22, sim 0/0/0 calibrated, apply parity, B1 cell 9 untouched) | **PASS** |
| E6 ADJUDICATIONS (Tests 4/5 = directive conformance; coexistence verified) | **CONFORMANT / VERIFIED** |

- Zero repo-side fixes required; the three mid-verification failures were reviewer-instrument bugs (disclosed above), fixed and re-run to completion on the pushed bytes.
- **Merge gate: Owner live retest with a REAL ChatGPT escaped-bracket reply** (fixtures were shape-constructed; the live reply is the literal-text proof). The retest should exercise: fully-escaped reply inside a ``` fence, arrowless Bengali-only lines, and at least one placeholder line — the exact shapes proven here end-to-end.
- At merge time: reconcile the two docs headers (`GLM_5_3.md`, `GLM_5_3_FLASH.md`) — trivial, both disclosed.

---

# MANGABD-005 — PHASE D ADDENDUM: B2 RF-2 DELTA VERIFICATION (GLM-5.3-Flash, 2026-10-16)

Object: `2c4635d` @ `mangabd-005-b2`, parent `11bbd1f` (= my Phase D report commit; rebase claim verified — chain `2c4635d`→`11bbd1f`→`122e353`→`8445328`). Claimed delta: cell-8 self-test block ONLY (5 anchored patches, +65 source lines 2210→2275) + `agents/GLM_5_3.md` record (+13). All checks re-run on the pushed bytes. Instruments: `scripts/m005rf2_{extract,r1c_r2,runtime,r5_adjudication}.py`; artifacts `m005rf2_work/` (scope_summary.json, r1c_r2_static.json, rf2_runtime_summary.json 31/31, rf2_r5_summary.json 20/20). No source or sample changes; report-only commit.

## R1 SCOPE — PASS

- `git show --stat 2c4635d`: exactly 2 files (notebook +73/−4 JSON lines; `agents/GLM_5_3.md` +13). No `samples/`, no other `agents/` files, no mode/rename.
- Cell-level byte compare: rf2 vs `11bbd1f` → changed cells = **{8} exactly**; rf2 vs `122e353` → changed cells = **{8} exactly**; 26 non-target cells byte-identical to BOTH refs. Cell-8 non-source fields and all top-level notebook fields identical.
- Functional spans vs `122e353`: ALL 40 top-level defs/assigns BYTE-IDENTICAL except exactly the 5 self-test loci (`_b2_saved_df` save site 1957→1962 via comment+sentinel block; 3 one-line finally checks 2078→2083, 2125→2130, 2089→2094; Test 23 insertion +60 lines). `parse_ai_text` / `export_ai_text` / `apply_manual_translation` / `translate_manual_upload` / `_strip_llm_wrappers` / `_mbd_*` / `run_test` / builders: BYTE-IDENTICAL → **the Phase D E2/E3/E4 approval carries over unchanged**.
- Secret scan on the added source lines: 0 hits.

## R2 SENTINEL DISCIPLINE — PASS (exhaustive scan, not spot-check)

- `"__unset__"` string: **0 occurrences** in RF-2 cell 8 (pre-fix: 4 — saves 1957/2089, `==` checks 2078/2125).
- `_B2_UNSET = object()`: 1 definition (line 1961); 4 save sites, all `globals().get("translation_df", _B2_UNSET)` (1962, 2094, 2151, 2172); 4 checks, all `is _B2_UNSET` (2083, 2130, 2177, 2198).
- Exhaustive AST inventory of EVERY `Compare` and EVERY boolean context (`If`/`While`/`IfExp`/`BoolOp`/`not`) whose operands name a df-carrying identifier (`translation_df`, `_b2_saved_df`, `_saved_df22`, `_rf2_saved`, `_rf2_outer`, `_rf2_df`): **zero bare-DataFrame truthiness, zero df-vs-string equality**; every entry is identity (`is`/`is not`), `len()`, `is None`, `hasattr`, or `.columns` membership. (Elementwise `translation_df["page_id"] == page_id` masks exist only inside filter subscripts in pre-existing functional code — byte-identical to `122e353`, never in boolean context.)

## R3 LIVE-STATE EXEC — PASS (verbatim bytes, sha-chained)

- **Sandbox**: 23/23 self-tests (event kwargs `tests_passed/tests_total` = 23/23; "live-state save/restore (RF-2)" green), `translation_df` ABSENT post-exec (pop path), engine restored to manual, session tmpdir file-census empty (traceless).
- **Live-state (the directive scenario)**: pre-seeded real 2-row `translation_df` (exact 21-column cell-3 schema) before exec → 23/23, zero ❌ lines, post-exec `translation_df` **IS the pre-seeded object** (id equality), `pickle.dumps` **byte-identity**, len unchanged, file census empty.
- **Negative control**: PRE-FIX bytes (`122e353`) in the SAME live-state harness → `ValueError: The truth value of a DataFrame is ambiguous. Use a.empty, a.bool(), a.item(), a.any() or a.all()` — the Owner's exact error — traceback frame = **pre-fix line 2078** (`if _b2_saved_df == "__unset__":`, the battery finally), fired AFTER Tests 1–21 ran green (21 run_test greens, last = "placeholder skip+report (B2)"); Test 22 never reached. The fix provably targets the real defect.
- **Kernel state at the pre-fix crash**: `translation_df` = the bare empty swap df (len 0, no columns); the restore never executed; the pre-seeded object detached but unmutated. This is the deterministic **kernel rows=0** mechanism (adjudicated in R5).

## R4 REGRESSIONS — PASS

- `m002_sim_v2`: calibration `aabc592` = 1 abort site (`cells[14]:40`); base `8445328` = 0; **RF-2 `2c4635d` = 0**. Wire format unchanged (R1 functional-span byte-identity).

## R5 OWNER DATA ADJUDICATION (new) — ANSWERED

1. **Can the pre-fix battery explain the emptied CSV? NO — the battery is disk-inert.** AST scan with write-capable call set (`save_translation_df`, `save_translation_artifact`, `save_json_artifact`, `atomic_write_json`, `to_csv`/`to_json`, `open`, `write_text`/`write_bytes`, `mark_stage_done`, `unlink`/`remove`): the ENTIRE module-level self-test region of the pre-fix bytes (Tests 1–21 + battery save/finally + Test 22) contains ZERO direct disk-write calls; the whole cell-8 module level (non-def statements) likewise zero; and the **transitive closure** confirms it — the battery's callees are `parse_ai_text`, `_strip_llm_wrappers`, `apply_sfx_glossary` (pure str→str, config-read only), `switch_translator` (in-memory config only), validators/prompt builders (pure); the save-transitive functions (`apply_manual_translation`, `translate_page`, `translate_manual_upload`, …) are **never called** in the battery. No `unlink`/`remove` anywhere in the 27 cells.
2. **What the pre-fix battery DOES explain — kernel rows=0, deterministically**: the battery save captures the live df, swaps `translation_df = pd.DataFrame()` (bare, column-less), and the ValueError aborts the finally BEFORE the restore → kernel df = bare empty (proven in R3 negative control). This is the only df-state mutation the battery performs.
3. **Disk rows=0 mechanism (runtime-proven on verbatim bytes)**: `save_translation_df()` (extracted verbatim from pushed cell-3 bytes) on a bare empty df adds the 21 columns as `""` and writes a **header-only 21-column CSV** — 0 rows on disk. The notebook's unconditional `save_translation_df()` call sites persist whatever the kernel df currently is: cell 3:968 (upsert end), 3:1164 (cell-3 Test-8 cleanup; conditional on `page_id` being in columns), 8:1455 (translate_page success path; unreachable with a bare df — early return), 10:947, 11:42/79, 12:66 (repair utilities; a bare column-less df raises KeyError before their saves). Guarded sites (`applied>0`/`deleted>0`: 8:1188, 16:1176/1258/1319, 22:582) cannot fire on an empty df. Note: a plain cell-3 re-run is disk-safe (module-level `load_translation_df()` at cell-3:993 reloads disk BEFORE the self-tests run). **Which specific action persisted the empty CSV in the Owner's live session is not recoverable from repo bytes [UNKNOWN — Owner session history]**; what IS excluded from bytes: the battery itself, and any direct file deletion. Consistent possibilities: any post-crash save firing while the kernel df was empty, or the CSV already being row-less in that session (data living in sidecars/in-flight).
4. **Recovery path (rebuild translation_df from per-page translation.json sidecars): SCHEMA-SOUND.** Sidecar record fields: `id`(int), `region_type`, `original_text`, `translated_text`, `translator_engine`, `translator_model` (sidecar-only M004-B1 additive field — not a df column, not consumed on rebuild), `bengali_valid`(bool), `status`. The notebook's own chain rebuilds the full schema: cell-7 OCR reload path rebuilds rows from `ocr.json` via `build_ocr_row` — which emits EXACTLY the 21 `TRANSLATION_DF_COLUMNS` (set-equal, statically verified) — → `upsert_translation_rows`; then `translate_page`'s cache path (stage done) loads the per-page `translation.json` records and applies them via `apply_manual_translation` keyed `(page|page_id, int(id))` — recomputing `bengali_valid = validate_bengali` (≥1 codepoint U+0980–U+09FF), the status ladder (`untranslated`/`marker`/`translated`/`non_bengali`), `translator_engine="manual"`, then saving. **Runtime-proven with verbatim RF-2 functions**: 2/2 applied, text restored, `bengali_valid` recomputed (True for Bengali; False + `status=non_bengali` for non-Bengali), engine=manual on both rows. Caveats: (i) `translation.json` alone restores only the translation-bearing fields — the full 21-column schema needs the `ocr.json` side of the chain (both are per-page sidecars, both survive a CSV wipe); (ii) recovery should reload the df (cell 3) BEFORE re-running translate flows so `translate_page` takes the cache path — its empty-df early-return (cell 8:~1345) writes `save_json_artifact(page_id, "translation", [])` + marks stage done, which would overwrite an un-rebuilt page's sidecar.

## REVIEWER INSTRUMENT DISCLOSURES (zero repo impact)

(a) config stub pre-seeded `providers={}`, defeating cell-8's `setdefault` registry → `KeyError: 'openrouter'` at line 189; fixed by an empty `translation` stub. (b) traceback captured as a string then `extract_tb`'d; fixed by keeping the live tb object (enabled the line-2078 frame mapping). (c) section-scoped green counter initially counted `switch_translator`'s informational `Translator engine:` prints (same 2-space ✅ shape as `run_test`); fixed by exclusion. (d) first module-level write-scan walked into def bodies; fixed with a non-def filter. All shakedown defects were in my instruments, not the repo.

## RF-2 VERDICT

**RF-2: CLOSED.**

| Check | Result |
|-------|--------|
| R1 scope (cell 8 + GLM_5_3.md record only; functional spans byte-identical to 122e353) | **PASS** |
| R2 sentinel discipline (zero string-sentinel, zero df-in-boolean; exhaustive scan) | **PASS** |
| R3 live-state exec (23/23 sandbox + live-state; exact-object restore + pickle byte-identity; traceless) | **PASS** |
| R3 negative control (pre-fix bytes reproduce the Owner's exact ValueError @ battery finally, post-Tests-1–21) | **PASS** |
| R4 m002_sim_v2 0 abort sites (calibration intact); wire format unchanged | **PASS** |
| R5 owner-data adjudication (battery disk-inert; kernel rows=0 deterministic; 0-row CSV write mechanism proven; recovery path schema-sound) | **ANSWERED** |

- The Phase D **APPROVED** verdict carries: functional spans are byte-identical to `122e353`; the RF-2 delta is confined to the authorized cell-8 self-test block; the fix is regression-proven in both directions (fixed bytes green in sandbox AND live-state; pre-fix bytes crash with the Owner's exact error).
- Merge-gate note: the Owner live retest remains outstanding for the **parser** (real escaped-bracket reply = literal-text proof, Phase D scope). The RF-2 crash was in the self-test battery, not the parser — the retest now also exercises the fixed battery in a genuinely live session (cell 3 pre-loaded df), which Test 23 simulates.

---

# MANGABD-005 — PHASE D ADDENDUM: B2 RF-3 (+RF-4) DELTA VERIFICATION (GLM-5.3-Flash, 2026-10-17)

Delta verified on pushed bytes only: `29c17ba` (my RF-2 CLOSED) → `c5f51c4` (RF-3: trailing-arrow fallback + Owner 10-section prompt + Test 24, 7 anchored patches, cell 8 only) → `fe879fe` (RF-4: bare [SKIP] marker-skip, 6 anchored patches, cell 8 only). Linear chain confirmed (`fe879fe` → `c5f51c4` → `29c17ba`); both commits touch exactly the notebook + `agents/GLM_5_3.md` (numstat + `git diff --summary`: no mode/rename/new-file changes). Custody sha256 (pushed notebook bytes): base `b9784e6f…`, RF-3 `63ebd490…`, RF-4 `59aef8e2…`; cell-8 sha16: base `80315623688c6fed` → RF-3 `1f814c307d4f5001` → RF-4 `fbce8f78274296c7`. [FACT]

## R1 SCOPE — PASS

Changed cells = {8} exactly on BOTH hops (26 other cells byte-identical to `29c17ba`); cell-8 non-source fields + notebook top-level fields identical; all 27 cells code-type. Cell 8: 2275→2657 (+382) → 2832 (+175) source lines = the disclosed +382/+175. Def-level delta: RF-3 changes `parse_ai_text` ONLY; RF-4 additionally changes `apply_manual_translation`; hunk census = 7 (RF-3) + 6 (RF-4) — each hunk maps to a disclosed patch locus (module-level: prompt block, Test 24, Test 25; in-def: fallback/counter/print, marker check, apply guard). `export_ai_text` / `translate_manual_upload` / `translate_page` / the prompt span / cells 22+25 all byte-identical → Phase D APPROVED + RF-2 CLOSED verdicts carry. GLM_5_3.md deltas = the two RF records only. [FACT]

## R2 TRAILING-ARROW — PASS

Fallback verified on the fe879fe namespace: post-FIRST-arrow empty/whitespace + pre-arrow Bengali → pre-arrow becomes the translation with `original_text=""`, `trailing_arrow` counted (probes incl. `->`/`=>` arrow variants and trailing-whitespace post-arrow). English-only pre-arrow + empty post-arrow stays a REPORTED placeholder skip (no entry, `placeholder_skipped=1`, sentinel `skipped_lines` carries the line) — Tests 4/21 contract preserved, 23/23 regression gate green. The `📋 Lenient variant used: trailing-arrow=N` print is inside `parse_ai_text` itself (cell line 1234; AST) and every parse path funnels through `parse_ai_text` (upload c8:1399, cell-22 paste c22:390) → structurally visible on ALL paths. V-4a never silent: sentinel `("_unparsed", 0)` rides the stats on a trailing-arrow-only parse; a multi-category paste shows `trailing_arrow=1` AND `placeholder_skipped=1` simultaneously. [TEST RESULT]

## R3 PROMPT FIDELITY — PASS

`manual_copy_prompt` = the Owner-authored 10-section localization-engine prompt as a raw triple-quoted literal: all 10 numbered section headers + ROLE AND OBJECTIVE preamble + FINAL DIRECTIVE present; section 1 contains the literal backslash-bracket sequence `"\[PAGE:ID]"` (the raw-string justification); kana strings `こがねい`/`おてあらい` verbatim in the Test 24 Owner-paste fixture; old M004 template fully purged from cell 8 (zero matches outside the disclosure comment). Payload chain: `_build_external_ai_system_prompt()` (cell 8) reads the config key dynamically → payload == template verbatim + the glossary rider (merge path preserved); cell 25 is byte-identical and calls the builder dynamically (c25:186–187); `MANGABD_CONFIG` is defined only at cell 1:180 with no disk-load overwrite before cell 8 → `setdefault` lands the new prompt in every fresh kernel while preserving Owner-editable semantics. [TEST RESULT]

## R4 TEST 24 + LIVE-STATE — PASS

Verbatim-bytes exec (sha-chained): sandbox 25/25 and live-state 25/25 (pre-seeded real 21-col df + harness canary save hook). Independent replication (fixture extracted from pushed bytes via AST literal_eval, expected values derived mechanically by MY OWN FIRST-arrow split, not copied from the repo's fixture): Owner's real 6-line trailing-arrow paste → 6/6 entries byte-exact, `original_text==""` all, `trailing_arrow=6`, visible `trailing-arrow=6` line; real `apply_manual_translation` → applied=6, `translator_engine=manual` all, `bengali_valid` all True, `status=translated` all, save shielded (single guarded call). Live-state: post-exec df IS the pre-seeded object with pickle byte-identity; battery traceless (file census empty); harness canary identity preserved through the Test 24/25 monkeypatch-restore cycles (8 save sites, all `_B2_UNSET`-disciplined). Negative control: PRE-FIX bytes (29c17ba) parse the same paste → 0 entries, `placeholder_skipped=6`, no `trailing_arrow` key, no rescue print — the defect reproduced and RF-3 proven as the fix. [TEST RESULT]

## R5 REGRESSIONS — PASS

25/25 self-tests in both sandbox and live-state (23 prior + Test 24 + Test 25). RF-2 sentinel invariants carried (exhaustive AST scan of the full 2832-line cell 8): `__unset__` string 0 hits; `_B2_UNSET = object()` 1 def (line 2277); save sites 8 = 6 df-saves + 2 save-fn saves (2278/2410/2467/2488/2530/2656 df; 2531/2657 save-fn); `is _B2_UNSET` checks 8; zero bare-DataFrame truthiness; zero dangerous df==scalar equality (all flagged compares are len()/is None/elementwise masks — safe). m002_sim_v2: calibration `aabc592` = exactly 1 site (cells[14]:40) reproduced, base `8445328` = 0, RF-4 `fe879fe` = **0 abort sites**. Wire format: parse entry shape + sentinel key unchanged; stats keys purely additive (`trailing_arrow`, `marker_skipped`); apply return int + df schema unchanged; export path untouched; cells 22/25 byte-identical. [TEST RESULT]

## R6 ADJUDICATIONS

**(a) whole-pre-arrow semantics — ACCEPT (as disclosed).** On normal arrowed lines the translation comes from the post-arrow side ONLY (verified: `English source → বাংলা` → `original_text="English source"`, translation untouched by source) — the fallback fires exclusively on an EMPTY post-arrow, so no source leakage is possible on normal lines. The disclosed caveat stands: a hypothetical English-prefix+Bengali-suffix line with a dangling arrow applies the full mixed pre-arrow (arrowless-rule semantics; matches the Owner's real T/L-note line, where the prefix is intended content; 5 of the Owner's 6 real lines are pure Bengali). [TEST RESULT]
**(b) parse-level counter print — ACCEPT.** The cell-8-only scope is the PM's own RF discipline; the print lives inside `parse_ai_text` so it fires on every parse path including the cell-22 flow, carrying count + reason. Merging `trailing-arrow`/`marker-skip` into cell-22's combined `📋 Lenient variants used:` line requires a cell-22 edit — correctly deferred as a 1-line future authorized RF. Also accepted: the English-only negative reports via the placeholder-skip channel (not `unparsed_lines`) — forced by the directive's own Tests 4/21 gate, verified at runtime. [ADJUDICATION]
**(c) BARE [SKIP] — RF-4 LANDED, end-to-end verified.** Parse level: `[02.jpg:3] SOME TEXT → [SKIP]` → no entry, `marker_skipped=1`, `"(marker)"` reason in the sentinel skip report, visible `⏭️ marker-skip: 1` print; `[SKIP:OCR_FAILED]` (set-member), `[skip]` (case-insensitive) likewise. Apply level (belt-and-braces, after `clean_translation`): quoted `'"[SKIP]"'`, plain-string dict shape (the cell-22 paste loop's exact shape), and dict-entry shape (cache-rebuild shape) all refused with the visible `⏭️ Marker translation not applied` print; zero save calls when all rows refused; real Bengali NOT over-blocked (control applied 1/1, status=translated). Negative control on pre-fix bytes (c5f51c4): both `[SKIP]` and `[SKIP:OCR_FAILED]` stored as LITERAL translations (`applied=1` each, `status=non_bengali`/`marker`), save hook FIRED — the verify-first gate's defect reproduced; the micro-fix was required and is proven. [TEST RESULT]

## REVIEWER INSTRUMENT DISCLOSURES (zero repo impact)

(i) fixture extraction: module-level AST walk missed the try-nested `_rf3_sample` (fixed: full-tree walk + `literal_eval`); (ii) my sentinel save-site matcher treated `globals().get`'s receiver as a Name instead of a Call (returned 0; ground truth via grep = 8 sites, matcher fixed, counts now match the record); (iii) my multi-category print expectation was wrong — placeholder skips ride the sentinel `skipped_lines` (cell-22 prints them; parse-level prints are the RF-3/RF-4 categories only, per GLM-5.3's disclosure 3) — check corrected, not code; (iv) payload check initially demanded equality (the glossary rider makes `startswith` + rider-present the correct assertion — that rider IS the preserved merge path); (v) first m002 check asserted only returncode — tightened to parse "abort-class SITE count". All defects were in my instruments, none in the repo.

## RF-3 (+RF-4) VERDICT

**RF-3: CLOSED** (and RF-4, landed mid-round as a PM pre-ruled micro-fix, verified in the same round: **CLOSED**).

| Check | Result |
|-------|--------|
| R1 scope (cell 8 + GLM_5_3.md records only; 26 cells byte-identical to 29c17ba; spans = disclosed 7+6 patches) | **PASS** |
| R2 trailing-arrow (fallback semantics, English-only skip, counter+print all paths, V-4a never silent) | **PASS** |
| R3 prompt fidelity (10 sections verbatim, `\[PAGE:ID]` literal, kana fixture, config-key payload, zero cell-25 change) | **PASS** |
| R4 Test 24 (independent 6/6 byte-exact + trailing_arrow=6 + visible line; save shielded; live-state identity/pickle/traceless) | **PASS** |
| R5 regressions (25/25 both modes; sentinels carried; m002 calibration 1 / base 0 / RF-4 0; wire format additive-only) | **PASS** |
| R6a no source leakage on normal arrowed lines (whole-pre-arrow semantics disclosed + accepted) | **PASS** |
| R6b parse-level counter print | **ACCEPT** |
| R6c bare [SKIP] end-to-end (RF-4 marker-skip + visible report; negative control reproduced literal storage) | **PASS** |

- Phase D APPROVED + RF-2 CLOSED carry: the only functional-span changes are the disclosed parser fallback / marker check / apply guard inside `parse_ai_text` + `apply_manual_translation`; everything else byte-identical.
- Non-blocking observation (pre-existing, NOT an RF-3 regression): a double-arrow line `English → বাংলা →` stores `বাংলা →` (trailing arrow retained in the translation; applied=1) — FIRST-arrow split with empty-post-arrow fallback not applicable; cosmetic; future RF only if the Owner ever produces double-arrow lines. GLM-5.3's RF-4 disclosure 3 (quoted markers undercount at parse level while the apply guard still blocks storage) also noted as accepted division of labor.
- Merge gate unchanged: Phase D + RF-2 CLOSED + RF-3/RF-4 delta CLOSED + **Owner live retest** (now exercises the trailing-arrow fallback, the new prompt, and the marker-skip path with real ChatGPT output) + Owner merge authorization.
- Report-only NEW commit on `mangabd-005-b2`; no source/sample changes; no amend/merge.

---

# MANGABD-006 — PHASE B REVIEW (EXTENSION)

Independent review of GLM-5.3's §A.1 EXTENDED BENCHMARK (agents/GLM_5_3.md), commit `e06c045` on `main` (parent `520680c` = Phase A original). Date: 2026-10-19. Rules observed: investigation FIRST against the extended benchmark artifacts, THEN challenge of the 7 directive items; pushed bytes only; no source changes; evidence labels throughout. Reviewer branch: `mangabd-006-flash-ext-review` (cut from `main @ e06c045`).

## P0 SCOPE & TRACEABILITY (what is and is not verifiable, and why)

- **P0.1 Docs-only scope — PASS.** `e06c045` touches exactly ONE file, `agents/GLM_5_3.md` (+83/−2); the two deletions are the header CURRENT-PHASE paragraph (extended with the extension summary) and the Phase A closing line (replaced by §A.1). Parent `520680c` likewise touched only `agents/GLM_5_3.md` (+168/−0). No notebook cell, no sample artifact, no source file changed in either commit. [FACT — git diff]
- **P0.2 THE EXTENDED BENCHMARK ARTIFACTS ARE NOT IN THE PUSHED TREE — the central limitation of this review.** The §A.1 report and its commit message claim as evidence: `scripts/m006_phaseA_ext_bench.py`, `scripts/m006_phaseA_ext_ovis2.py`, `scripts/m006_phaseA_ext_metrics.py`, `m006_bench/results/metrics_ext.json`, the five raw per-engine JSONs (`baberu.json`, `kellenok.json`, `paddle_v6.json`, `paddle_v6_up.json`, `ovis2.json`), and cached weights under `m006_ext/`. **None of these exist in the repo tree at `e06c045` (git ls-tree: zero hits for m006/scripts/bench), and none exist in this reviewer's sandbox** (exhaustive find over `/home/z`: no m006_bench, no m006_ext, no metrics_ext.json, no m006 scripts; my prior-session work dirs m004d/m005*/s007 all present — nothing M006). The closing line "All benchmark instruments and result JSONs are preserved and re-runnable (`scripts/m006_*`, `scripts/m006_phaseA_ext_*`, `m006_bench/`, `m006_ext/`)" is TRUE of the author's sandbox and FALSE of the repository; the same defect already existed in the Phase A original (520680c claims `scripts/m006_phaseA_bench.py` + `m006_bench/` — equally uncommitted). [FACT]
- **P0.3 Consequence, precisely stated.** Every MEASURED number in §A.1 (the 0.031 / 0.016 / 0.244 / 0.101 / 1.000 / 0.195 rows and all per-region values) is **UNVERIFIED-BYTES-UNAVAILABLE**: I cannot recompute CERs from raw engine outputs because the outputs are not shared. What I CAN and DID verify from pushed bytes: (a) docs-only scope (P0.1); (b) full internal-consistency arithmetic of every reported aggregate against the reported per-region tables (§P2); (c) cross-table coherence with the Phase A M2 rows quoted inside §A.1 (§P2 C8); (d) ground-truth anchoring against the archived `samples/*/translation.json` (§P3); and everything externally checkable — the five HF model cards, the official PP-OCRv6 claims, the "+13%" figure, the OvisOCR2 repetition pathology, and all five licenses — re-verified INDEPENDENTLY today against live sources (§P4). The evaluation HARNESS is reproducible from repo bytes (GT derivable from archived samples; crops reconstructible from `detections.json` + the byte-identical original, md5 `446b3575…`) — **only the engine OUTPUTS are missing.** Minimal closure ask: commit the five raw per-engine JSONs (a few hundred KB) + the three ext scripts; everything else can be re-derived. [FACT / requirement]

## P1 INSTRUMENT

Reviewer instrument `m006b_ext_consistency.py` (this sandbox, `scripts/`): recomputes every mean / EN-bubble / N2 aggregate from the §A.1.2 per-region table, re-checks the dominance and unique-best claims, cross-checks F16 resource numbers vs the A.1.2 table, chain-weight arithmetic, and the quoted Phase A rows vs M2.2. 9 check groups, results below.

## P2 INTERNAL-CONSISTENCY RESULTS (from pushed bytes only)

- **C1 means — PASS (8/8).** kellenok (0.103+0.045+0.000+0.000+0.030+0.006)/6 = 0.0307→0.031 ✓; baberu 0.0677→0.068 ✓; proxy 0.0213→0.021 ✓; v6-default 0.2435→0.244 ✓; v6-upscale 0.1010→0.101 ✓; v4 0.1202→0.120 ✓; v5 0.1837→0.183 ✓ (within 6×3dp-rounding slop); ovis2-guarded 0.1948→0.195 ✓. [TEST RESULT]
- **C2 EN-bubble (R2–R6 mean) — PASS (8/8).** kellenok/baberu 0.0162→0.016; proxy 0.0224→0.022 (matches M2.1); v6-default 0.2796→0.280; v6-upscale 0.1148→0.115; ovis2 0.2164→0.216; v4 0.0918→0.092; v5 0.1854→0.185. Note the directive's "baberu 0.016 vs proxy 0.021" compares EN-bubble to the proxy's MEAN; the correct apples-to-apples pair is 0.016 vs 0.022 (EN-bubble vs EN-bubble) — which is exactly what F10 uses ("numerically BETTER than the VLM proxy's 0.022"). Comparison VALID as reported. [TEST RESULT]
- **C3 N2 match — PASS.** kellenok/baberu N2 0.333 = exactly 2/6 = {R3, R4} (the two zero-CER regions) — internally forced; requires the single-char errors in R2/R5/R6 to be alphanumerics (non-alnum errors would vanish under N2 stripping and raise the count). v6 rows 1/6 = {R3} ✓; proxy 3/6 ✓ possible ({R3,R4}+R6 if its 1-char R6 error is non-alnum); ovis2 0 ✓. All values coherent. [TEST RESULT]
- **C4 dominance claims — PASS.** F12 "kellenok wins or ties every region vs v4" ✓ (0.103<0.262, 0.045<0.114, 0=0, 0.000<0.069, 0.030<0.091, 0.006<0.185); "strictly dominates v5" ✓ (0.103<0.175, 0.045<0.091, 0=0, 0.000<0.690, 0.030<0.076, 0.006<0.070) — TRUE on the reported numbers. [TEST RESULT]
- **C5 F12 "no unique-best region except R1-upscale" — DEFECTIVE SENTENCE (the one real internal defect found).** Recomputed per-region argmin over ALL rows of the extension comparison table: **R2's unique best is v6-DEFAULT at 0.023** (runner-up 0.045, kellenok/baberu/proxy) — a second v6 unique-best region the sentence denies. Also, under the plain reading "unique best overall", R1-upscale (0.032) is NOT a unique best either (proxy 0.016 is better); the sentence only survives under the unstated reading "unique best among LOCAL engines, excepting R2". The chain CONCLUSION survives regardless — 0.023-vs-0.045 on one region does not justify carrying v6's R4 (0.345) + R6 (1.000) failures, and chain semantics (M3.3: retry on exception/empty/marker only) cannot exploit a per-region best-engine anyway — but the F12 sentence as written is false against its own table and must be corrected. [TEST RESULT — AMENDMENT A1]
- **C6 F16 resource numbers — PASS.** Every F16 envelope value equals its A.1.2 table source (0.16 s/384 MB, 1.12 s/624 MB, 6.9 s/1628 MB, 10.1 s/2442 MB); v6-upscale 8.5–9.3 s / 3095 MB inside F16's "7–9 s / 3.1 GB"; header's "88 s/region" vs table 87.8 ✓. [TEST RESULT]
- **C7 chain weights — PASS.** det 1.8 + rec 21.2 = 23 MB (kellenok) + 243 MB (baberu) = 266 MB = A.1.5's "~266 MB". [TEST RESULT]
- **C8 quoted Phase A rows — PASS.** The proxy/v4/v5 rows re-quoted in the extension's per-region table are byte-equal to M2.2 originals; extension's proxy EN-bubble 0.022 = M2.1. No drift was introduced when old rows were copied forward. [TEST RESULT]
- **C9 THE KELLENOK/BABERU R2–R6 IDENTITY — FLAGGED UNKNOWN, must be resolved before B1 locks the registry.** The two engines report IDENTICAL CERs to 3dp on ALL FIVE EN regions (R2 0.045, R3 0.000, R4 0.000, R5 0.030, R6 0.006) while differing on R1 (0.103 vs 0.325). Two architectures this different (v6-finetune det+rec DB/CTC vs DINOv2+GQA char decoder) agreeing to the last digit on 5/6 regions is possible innocently — GT is short (R3 30 / R4 29 / R2 45 / R5 66 / R6 ~158 chars, §P3), exact reads on R3/R4 force identical 0.000, and a shared GT artifact NFKC does not fold (e.g. the curly quote in R2's `WAS "!!`) would produce the SAME error count for any honest engine; C3's alnum requirement is satisfiable by homoglyph-class artifacts (both engines emit canonical Latin where GT holds a lookalike). But an aggregation/copy defect in `m006_phaseA_ext_metrics.py` is EQUALLY consistent with the printed table. Not adjudicable without `kellenok.json` + `baberu.json` — which are not in the tree (P0.2). [UNKNOWN — AMENDMENT A2]

## P3 GT ANCHORING (archived samples, repo bytes)

GT re-extracted from `samples/S003_batch2/translation.json` (= S005_manual, both ACCEPT archives): R1 the こがねい/おてあらい T/L note with the disclosed stray `)`, R2 `THE ONLY LETTER CORRECT IN THAT NAME WAS "!!` (45 ch), R3 `MY NAME'S KOGANEI YOU DUMBASS!` (30 ch), R4 `WHO THE HELL IS THAT PERSON!?` (29 ch), R5 `WHO THE FUCK IS OTEARAH!? …` (66 ch, OTEARAH artifact), R6 the 158-char confession with `SUDENLY`. Checks: F9's claimed kellenok R4 output `WHO THE HELL IS THAT PERSON!?` is GT-verbatim, consistent with CER 0.000 and with N2 = {R3,R4}; the reported single-region CERs correspond to 2/45 (R2), 2/66 (R5), 1/~158 (R6) char errors — all plausible engine behavior. Cosmetic: F10 says "R6 GT 175 chars" (actual ~158) and "R2/R5 within one character" (arithmetic says two each: 0.045×45, 0.030×66) — immaterial to any conclusion, noted for accuracy. [FACT + TEST RESULT]

## P4 EXTERNAL VERIFICATION (independent, 2026-10-19, live web)

Every claim in §A.1 that has an external referent was re-checked against the live source TODAY. **Every one of them verified TRUE — zero external-claim defects found.** [LIT]

- **E1 kellenok card (hf.co/Kellenok/PP-OCRv6_manga):** license tag `apache-2.0` ✓; datasets `deepghs/AnimeText` + `hal-utokyo/Manga109-s` ✓; base `PaddlePaddle/PP-OCRv6_small_rec` ✓; dict 18,708 symbols ✓; ONNX det FP32 1.73 MB / rec FP32 21.2 MB / FP16 0.92+10.6 MB ✓ (report's "det 1.8 MB" = 1.73 MiB in MB — consistent); author benchmarks e2e manga 10.03% / webtoon 6.21% / illustration 16.36%, rec comictxt 8.37%, SFX 26.14% ✓ ALL exact; card's recommended DB post-processing `thresh=0.15, box_thresh=0.25, unclip_ratio=1.4, long side 960` ✓ EXACTLY matches the A.1.0 port disclosure; `examples/onnx_openvino.py` exists as the claimed port basis ✓. The A.1.1 research row for kellenok is verbatim-faithful to the live card. [LIT]
- **E2 baberu card (hf.co/genshiai-daichi/baberu-ocr):** license `apache-2.0` ✓; DINOv2 + 6-layer GQA char-level decoder, 115M, 14,630-symbol vocab ✓; Manga109 lCER 0.0359 vs manga-ocr 0.0422 ✓; EN per-bubble 0.054 vs PaddleOCR-VL 0.081 ✓; vintage western comics 0.1488 ✓; v1.1 256-char ceiling ✓. Card additions the report omitted (cosmetic): effective garble threshold ~190 chars/bubble (below the 256 spec — operationally relevant for long-bubble pages; R6 ~158 ch fits), dakuten/handakuten confusion, small-kana drops. [LIT]
- **E3 OvisOCR2 card + paper (hf.co/ATH-MaaS/OvisOCR2, arXiv 2607.13639):** license `apache-2.0` ✓; base Qwen3.5-0.8B ✓ (card displays 0.9B params vs the report's "0.8B" — naming variance, immaterial); OmniDocBench v1.6 overall 96.58, first end-to-end model to top it ✓. **F13's load-bearing claim CONFIRMED VERBATIM: the card itself ships a `_clean_truncated_repeats` method + a "repeated outputs" disclaimer — the repetition pathology is acknowledged by the authors**, and community experience independently corroborates ("the repetition loops are its one real vice and a detect-and-retry guard fully contains them"). [LIT]
- **E4 PP-OCRv6 official claims:** arXiv 2606.13108 ("PP-OCRv6_medium achieves 83.2% recognition accuracy and 86.2% detection Hmean, outperforming PP-OCRv5_server by +5.1 [+4.6]…"), PaddleOCR GitHub docs, and the PaddlePaddle HF blog all state **+5.1% recognition / +4.6% detection** ✓ = the report's verified pair. A targeted search for the directive's "+13%" figure returned **zero official sources** — F11's "+13% found in NO official source" CONFIRMED. One nuance worth recording: PaddlePaddle's own announcement post says "+4.9% detection", i.e. official sources are internally split 4.6/4.9 (docs vs announcement); the report used the durable docs/arXiv pair — correct choice, and it further justifies refusing the unofficial "+13%". [LIT]
- **E5 Unlimited-OCR (hf.co/baidu/Unlimited-OCR):** exists ✓; **MIT** confirmed by three independent secondary sources + the docling integration issue ✓; "push DeepSeek-OCR one step further" ✓; released 2026-06-22 ✓; 3B-class bf16 ≈ 6.67 GB single-file safetensors ✓ (3B×2B ≈ 6.7 GB — self-consistent); image-text-to-text + trust_remote_code ✓. [LIT]
- **E6 license audit (the directive's item 7) — F15 CONFIRMED, with one gap (A5):** all five model licenses independently verified today: Unlimited-OCR MIT; PP-OCRv6_medium Apache-2.0; OvisOCR2 Apache-2.0; kellenok Apache-2.0; baberu Apache-2.0. No Open-RAIL-M among the five; Surya weights remain the only restricted item in the record ✓. **GAP: F15 audits MODEL licenses only — training-data provenance is unaudited.** kellenok trains on hal-utokyo/Manga109-s (the 87-of-109-book commercial subset, available for commercial use "under the following conditions" per the Manga109 project/HF dataset card) + deepghs/AnimeText (community-scraped); baberu benchmarks/trains on Manga109-v2026 lineage. Apache-2.0 WEIGHTS do not by themselves clear DATASET conditions for commercial deployment. For this project (fan scanlation pipeline) risk is low, but D12 should add a provenance-check line item before any commercial use. [LIT — AMENDMENT A5]

## P5 THE SEVEN DIRECTIVE ITEMS — INVESTIGATE-THEN-CHALLENGE VERDICTS

**Item 1 — Kellenok superiority: ACCEPT (consistent), with two caveats.**
(a) *R4 perfect read:* the 0.000 cannot be recomputed (P0.2) but everything checkable is coherent — the claimed output is GT-verbatim (P3), the aggregate/N2 arithmetic forces {R3,R4} exact (C3), and the author's own card rates rec manga CER 5.63% on harder corpora, so 0.000 on 6 clean crops is plausible, not suspicious. [CONSISTENT-UNVERIFIED]
(b) *Manga-specialization attribution:* supported by the same-lineage contrast (generic v6_medium R4 0.345/0.379 vs v6-manga-finetuned 0.000) — BUT the pair differs in BOTH training data AND tier (medium 19M-rec vs small ~21MB-rec), so it is not a perfect control; and generic v4 (different lineage, no manga data) also reads R4 at 0.069, so R4 is not universally hard — the specialization claim is directionally convincing, not experimentally isolated. Also state the boundary the report omits: the card's own SFX CER is 26.14% — manga-specialization fixes stylized DIALOGUE caps (R4 class), not SFX-class text; do not extrapolate F9 to SFX regions. [AMENDMENT A3]
(c) *Line boxes:* guaranteed by the architecture (DB det + minAreaRect → per-line polygons, same post-processing the port disclosure implements) and confirmed present in the card's example pipeline; the "40 page-level boxes" count itself is unverifiable (raw outputs absent). Fine for M6-B2 design purposes. [ACCEPT]

**Item 2 — baberu complementarity: ACCEPT with RE-JUSTIFICATION demand (A2/A4).**
(a) *EN-bubble 0.016 vs proxy:* correct apples-to-apples is 0.016 vs 0.022 (EN-bubble vs EN-bubble; the 0.021 the directive quotes is the proxy's mean incl. R1) — F10 states it correctly; VERIFIED consistent (C2). Card corroboration: author's own EN per-bubble lCER 0.054 on harder corpora; 0.016 on these 5 clean bubbles is plausible. [ACCEPT]
(b) *No manga-ocr-style EN hallucination:* consistent with EN-bubble 0.016 vs manga-ocr's measured 0.481 (M2), and with the card's design intent (char-level multilingual decoder, EN benchmark row); raw outputs unavailable → CONSISTENT-UNVERIFIED. Note baberu's OWN card discloses a stylized-text weakness class (vintage western comics 0.1488 vs PaddleOCR-VL 0.0256) — supports kellenok-first ordering; the report could have cited this. [ACCEPT]
(c) *R1 kana handling:* the F10 report (rot90cw 0.325 best, upright JP-hallucinates like manga-ocr, kana こがねい read correctly even upright) is coherent with the F4 V-3 pattern and is correctly carried into the adapter design ("both reuse the V-3 rotation ladder", A.1.4). YES — the V-3 ladder is required for baberu exactly as for the original engines. [ACCEPT]

**Item 3 — v6 rejection validity: ACCEPT (the strongest-argued exclusion in the report).**
(a) *R6-empty is a real detection failure, not input-passing:* the discriminating logic is in the report's own data — the SAME runner, SAME crop RECOVERS R6 to 0.006 under the 960/min det policy, which proves the crop reaches the detector and convicts the DEFAULT policy; the mechanism (default `max`-type limit only ever downsizes, never upscales small crops — documented PaddleOCR limit_type semantics) explains why all max-side probes 660/960/1280 reproduced the empty result identically. Sound. [ACCEPT — CONSISTENT-UNVERIFIED on the numbers]
(b) *Scale-adjustment workaround new failure modes:* the report itself measures them — R2 0.023→0.159 (7×), R4 0.345→0.379, 9.3 s/region, 3.1 GB RSS. Adjudication: the workaround trades a catastrophic R6 for real R2/R4 degradation plus 8× latency and 2× RAM — NOT chain-adoption-worthy; D11's honest answer is NO for a blanket policy (a size-conditional small-crop policy is the only defensible variant, and kellenok's pixel-budget rule already covers that niche). Consistent with the report's own F12. [ACCEPT]
(c) *"+13%":* independently CONFIRMED absent from every official source (E4); the report's substitution of the verified +5.1/+4.6 pair and its explicit disclosure of the unverifiable directive figure is exactly the right honesty move. Directive figure REJECTED. [CONFIRMED]

**Item 4 — OvisOCR2 problems: loops CONFIRMED real; "intrinsic" wording OVERSTATED; exclusion ACCEPTED anyway.**
(a) *Repetition loops real:* measured raw 1.000 with the R3 `DUMBASS!` loop to the 512-token cap; independently corroborated by the card's own `_clean_truncated_repeats` + "repeated outputs" disclaimer (E3) and by community experience. NOT a harness artifact. [CONFIRMED]
(b) *"(not prompt-tunable)" — NOT ESTABLISHED:* the report discloses NO prompt sweep and NO sampling-parameter sweep; what was measured is loops under the production prompt with default greedy decoding. "Intrinsic under default decoding" is supported; "intrinsic (not prompt-tunable)" as a categorical claim is not. This does not change the verdict: with the shipped-guard-class cleaning, the guarded diagnostic is 0.195 — still 6× worse than kellenok 0.031, at 88 s/region CPU and 2.4 GB — so exclusion from the chain rests on quality + cost + task-class + (c), all sufficient WITHOUT the untunability claim. Amend the wording. [AMENDMENT A4]
(c) *LTR order:* the T2 page-level run (one disclosed run; `R1→R2→R4→R3→R5→R6` LTR doc order vs the GLM-5V-confirmed RTL `R3→R2→R4→R5→R6→R1`, Kendall tau +1.000 algorithm) is n=1 as disclosed — but the doc-parser class design makes LTR document order the expected default, and ONE counterexample is decisive for a can't-use predicate. M4.1 region-level RTL ordering stays REQUIRED; a doc-parser VLM cannot replace it. [ACCEPT]
(d) *Guard salvageable?* As a chain OCR fallback: no (0.195 ≫ 0.031 at 88 s/region). As a GPU page-parser adjunct with its shipped guards (M6-B3a): yes — which is precisely where the report parks it. [ACCEPT]

**Item 5 — Chain ordering: ACCEPT the order, with three hardening amendments.**
(a) *openrouter before local engines — defensible.* Zero VRAM, zero load cost, VLM class measured best on this exact corpus (F1: proxy 0.021 vs local best 0.031), and the M3.1 design already self-disables the cloud step when no key exists ("cloud skipped silently if no key") — offline runs pay nothing. The real residual risk is the configured-key-but-dead-network case: a 30 s timeout per region per page before the local engines fire, and M3.2's circuit breaker trips on LOAD ERROR only — a network timeout is not a load error. **A6: extend the breaker to consecutive cloud timeouts (e.g. 2 consecutive → skip cloud for the page run).** Also honest-labeling: the openrouter rows remain UNMEASURED (the position rests on the proxy standing in for gemini/gpt-4o-mini); the M6-B3 Colab items close this. [ACCEPT + A6]
(b) *baberu vs kellenok — complementary or redundant?* Challenge SUSTAINED: per the report's OWN table, baberu ties kellenok on EN-bubble (0.016), is identical R2–R6 (C9 flag), and is WORSE on R1 (0.325 vs 0.103). F10/A.1.4's justification ("its failures are covered upstream by kellenok") argues quality complementarity — but chain semantics (M3.3: retry on exception/empty/marker ONLY) can never exploit quality differences; baberu is reached only when kellenok RAISES or returns empty/marker. Its honest justification is FAILURE-MODE complementarity: kellenok's det is a 1.7 MB tiny model whose det-empty on unusual crops is a plausible failure class (the v6 R6 det-empty precedent proves the class), and baberu's bubble-level reader is precisely the different shape that survives det failure. That argument is not made in the report. Keep baberu at position 4 (243 MB, zero VRAM, 1.1 s cold — cheap insurance), but re-justify on failure-mode grounds, and D9's "bubble specialist invoked selectively" alternative is the tighter fit to the evidence. **A4: rewrite the baberu justification.** [ACCEPT position / CHALLENGE justification]
(c) *Chain quality gate (new, from the extension's own evidence):* the M3.3 `engine_reject` (min_text_len + reject-markers) would NOT catch degenerate output — OvisOCR2's repetition loops produce long, non-empty, marker-free text that sails through. OvisOCR2 is excluded, but the pathology class (any engine looping on an unseen page) is now measured in this record. **A7: add a cheap degenerate-output reject (consecutive n-gram repetition ratio) to `engine_reject`, so a looping engine is skipped down the chain instead of poisoning the region.** [AMENDMENT A7]

**Item 6 — VRAM feasibility: ACCEPT (arithmetic and architecture both check).**
kellenok (23 MB ONNX) + baberu (243 MB ONNX) declared `device: "cpu"` consume ZERO VRAM by construction — ONNX Runtime's CPU EP allocates system RAM (measured RSS 384/624 MB, trivial against Colab's ~12.7 GB), leaving qwen (~6.7 GB, LIT) + CTD + LaMa the T4's ~15 GB usable exactly as the B1 E4-proven ordering requires. Runtime-conflict question: onnxruntime and torch are independent runtimes sharing nothing but numpy — no loader, allocator, or CUDA-context conflict is possible for CPU-EP engines; the kellenok runner needs onnxruntime+numpy+cv2-class deps and baberu ships onnxruntime+numpy+pillow, neither importing torch. Version-pin note: onnxruntime 1.31.0 recorded in A.1.0; if GPU ONNX is ever wanted, the CPU package must be swapped for onnxruntime-gpu (trivial, note for B1). OvisOCR2/Unlimited-OCR swap-class arithmetic verified: 6.7 + 7–9 GB > 15 GB with CTD/LaMa competing → Unlimited-OCR cannot co-reside; ovis2 (~2.5–3.5 GB) fits numerically but violates the single-resident-VLM discipline — swap-class is the policy-consistent ruling. [FACT + arithmetic — ACCEPT]

**Item 7 — License audit: CONFIRMED CLEAN (models), with the provenance gap (A5).** See E6: all five verified today against live sources; F15's "no Open-RAIL-M, nothing that blocks production use" is TRUE for model weights; the ONE gap is training-data provenance (Manga109-s 87-book commercial-subset conditions; AnimeText community provenance) — add to D12 before any commercial deployment; for the current fan-work use, non-blocking. [CONFIRMED + A5]

## P6 AMENDMENTS (numbered; all report-level, none blocking the chain direction)

- **A1** Correct the F12 sentence: R2 (v6-default, 0.023) IS a unique-best region per the extension's own table; the defensible claim is "v6's unique-best niches (R1-upscale 0.032, R2-default 0.023) are single-region and do not offset its R4+R6 failures; chain semantics cannot exploit per-region best-engine selection anyway".
- **A2** Resolve C9 before B1 registry freeze: commit `kellenok.json` + `baberu.json` raw outputs and either demonstrate the identical R2–R6 values are shared-GT-artifact (per-region diffs showing the same error counts on different engine outputs) or fix the aggregation. If the values were copied, kellenok's true EN-bubble may differ and the baberu justification changes again.
- **A3** Add the specialization boundary to F9: same-lineage control is confounded by tier (medium vs small); v4's 0.069 shows R4 is not universally hard; card SFX CER 26.14% — no extrapolation to SFX-class regions.
- **A4** Reword F13: "intrinsic under default greedy decoding with the production prompt" — no prompt/sampling sweep was run, so "not prompt-tunable" is unproven (and unnecessary: the exclusion stands on 0.195 vs 0.031, 88 s/region, doc-parser class, LTR order). Rewrite the baberu chain justification on FAILURE-MODE complementarity (det-empty coverage), not quality complementarity.
- **A5** Extend the license audit (F15/D12) with training-data provenance: Manga109-s commercial-subset conditions + AnimeText provenance check before commercial use; record baberu card's ~190-char effective garble threshold in the research row.
- **A6** Extend the M3.2 circuit breaker to consecutive cloud timeouts (dead-network-with-key case: 30 s × regions × pages today).
- **A7** Add a degenerate-output reject (repetition-ratio) to M3.3 `engine_reject` — the measured OvisOCR2 pathology class, cheap insurance for any chain member.
- **A8 (process, the P0 fix)** Commit the extension instruments + five raw per-engine JSONs (small) to the repo or a work archive, and fix the "preserved and re-runnable" closing line to name where. Until then, the MEASURED tags in §A.1 carry the qualifier UNVERIFIED-BYTES-UNAVAILABLE in any downstream gate decision.

## P7 REVIEWER INSTRUMENT DISCLOSURES (zero repo impact)

(i) first tolerance pass flagged v5 mean 0.1837-vs-0.183 and kellenok/baberu N2 0.333-vs-0.3333 as failures — both were my instrument's over-tight tolerances (6×3dp rounding slop; display rounding of 2/6), fixed, no report defect; (ii) my C5 argmin initially used only the six extension engines before adding the quoted Phase A rows — the R2 finding holds either way (0.023 < 0.045). Both fixed in `m006b_ext_consistency.py`.

## PHASE B (EXTENSION) VERDICT

**ACCEPT WITH AMENDMENTS — the extension is externally truthful and internally coherent; the chain direction (qwen → openrouter_vision → kellenok → baberu → [paddle_v4 optional]; v5/v6/OvisOCR2/Unlimited-OCR excluded) is endorsed, D8–D12 are well-posed.** What carries the acceptance: (1) every externally checkable claim in §A.1 verified TRUE against live sources today — model cards verbatim-faithful, official v6 claims exact, "+13%" genuinely absent, OvisOCR2's pathology author-acknowledged, all five licenses clean; (2) every internally computable aggregate reproduces (C1–C4, C6–C8); (3) the exclusions are argued from the report's own measurements and survive my challenges. What binds it: A1 (F12 sentence defect — must correct), A2 (C9 identity flag — must resolve with raw JSONs BEFORE M6-B1 locks the registry), A8 (artifacts uncommitted — the reviewability debt; MEASURED rows stay UNVERIFIED-BYTES-UNAVAILABLE until the JSONs land). A3–A7 are amendments to text/design, non-blocking. The kellenok-first local chain and the v6 rejection are, on all available evidence, CORRECT decisions; the baberu slot is defensible but currently justified by the wrong argument.
