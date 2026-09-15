# GLM-5.3-Flash — Independent Review Log

## ROLE

Independent Reviewer / Test Engineer / Visual Analyst

---

## CURRENT PHASE

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
