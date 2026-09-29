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

## MANGABD-003 — PHASE E VERIFICATION

**Reviewer:** GLM-5.3-Flash (Independent Reviewer) · **Date:** 2026-09-29
**Object under review:** commit `f58cd3c` ("WIP: MANGABD-003 Phase C — awaiting Phase E verification", tree `3ac8d3a3`) on branch `mangabd-003-phase-c`; merge-base = `main @ 1cd8acf` (linear, single commit on top of base).
**Rules:** TASK_002 Phase D discipline + DECISION.md §C. GLM-5.3's self-report (agents/GLM_5_3.md Phase C record) was **not trusted for any check** — every claim below was re-executed against the pushed bytes. No source changes; no amend; no merge.
**Method:** reviewer-local scripts (repo-external, under reviewer `scripts/`): `m003_e1_audit.py`, `m003_e2_static.py`, `m003_e2_census2.py`, `m003_cell_diff.py`, `m003_e3_mirror.py`, `m003_v5_deep.py`, `m003_v5_branches.py`, `m003_e5_runtime.py`, `m003_e6_regression.py`. All executed code segments were extracted **verbatim** from `git show HEAD:` blobs with sha256 recorded at each step.

### PE.1 E1 — DIFF & SCOPE AUDIT: **PASS**

- `git diff main...HEAD --numstat`: notebook `287/23`; agents/GLM_5_3.md `75/2` (77 changed lines total); samples/README.md `2/0`; samples/S001_color_webtoon/metadata.json `6/3`; metadata.rev1.json `9/0` (status **A**, new file). **Total 5 files, +379/−28 — exact match to the Phase E brief.** [FACT]
- Raw diff entries: all `100644 → 100644`; the new file is `000000 → 100644`. **Zero mode changes, zero renames/copies.** [FACT]
- Secret-pattern scan of all **379 added lines** (GitHub PAT, `sk-`, AKIA, AIza, slack, PEM headers, bearer, JWT, hf_, DeepL): **0 hits**. No env-var *values* in code; added secret references are env-var *names* only (SECRET_SOURCES, cell 1). [TEST RESULT]
- Cell-level scope: 27 cells both sides; changed cells = **exactly {1, 6, 7, 8, 11, 12, 16, 25}**; the other **19 cells byte-identical** to main (list verified cell-by-cell). Within every edited cell only the `source` field changed (outputs/metadata untouched). Notebook top-level metadata, nbformat 4.0 identical. [FACT]
- `metadata.rev1.json` is **byte-identical** to `main:samples/S001_color_webtoon/metadata.json` (sha256 `eabe49b73ab3…`, 315 B, re-parses as JSON) — verbatim preservation proven at blob level. [FACT]

### PE.2 E2 — STATIC RE-CHECK: **PASS** (with one letter-vs-spirit note, N1)

- Notebook JSON re-parses; 27 cells; **all 27 AST-parse** clean. [TEST RESULT]
- **MANGABD-002 artifacts intact VERBATIM:** `cells[14]` guard block lines 40–46 present word-for-word (⏭️ skip banner + `run_inpaint_render_all(force=True)` gate) and `cells[26]` = 4 Bengali comments + `render_all_pages(force=False)`; both cells **byte-identical to main** (and hence to the Phase D-approved state). [FACT]
- try/except census (multiset AST diff of all 27 cells, HEAD minus main): **exactly 4 new handlers**, no fewer, no more:
  1. cell 11 + cell 12: `except OSError: pass` around `set_variation_by_axes([wght])` — **the prescribed guard** (E2 brief explicitly sanctions it). Pass-body is by design; on OSError the variable font keeps its default instance and the stroke compensation carries the weight, per the in-code comment. [FACT]
  2. cell 8: `except Exception → log_event(f"{engine} translation failed: …", level="WARN"); return ""` inside `translate_with_provider` — **exact shape-match of main's chatgpt adapter** (`except Exception → log_event("ChatGPT translation failed: …"); return ""`), verified against main's bytes. Non-silent: WARN log + empty-string contract identical to existing engines. [FACT]
  3. cell 25: `except Exception as e: print(f"❌ {e}")` inside the new `on_provider` callback — **clone of the pre-existing `on_nllb` callback's error surface**. Non-silent: visible in the console output widget. [FACT]
- **Note N1 (non-blocking):** the E2 brief's letter says "no NEW try/except anywhere except the prescribed OSError guard" — the letter is exceeded by the two handlers in (2)/(3). They are within Owner-approved V-5 scope (a provider adapter and a UI button callback cannot exist without them), they mirror pre-existing approved patterns exactly, and neither hides errors. Spirit upheld ("no dummy variables, no silent fallbacks, no error hiding" — verified: no bare `except:`, no pass-only *new* handlers outside the prescribed guards, no TODO/FIXME/Ellipsis stubs, no `_ =`/dummy assignments in added code). Flagged for Owner awareness only. [ASSESSMENT]

### PE.3 E3 — MIRROR EQUIVALENCE: **PASS**

Committed-state extraction (AST spans, exact source incl. decorators):

| Function | cell 11 | cell 12 | Byte-identical |
|---|---|---|---|
| `get_font_fb` | 690 chars / 14 lines, sha256 `a7d2d5bd61309c78` | 690 chars / 14 lines, sha256 `a7d2d5bd61309c78` | **YES** |
| `_qc_render_vertical` | 2267 chars / 40 lines, sha256 `e27f769797d8ff4f` | 2267 chars / 40 lines, sha256 `e27f769797d8ff4f` | **YES** |

Both cells now carry ONE canonical block; cell 12's 4 dead preamble lines (`size, lines = 8, [text]`, `# fit with swapped dims`, local `ImageDraw as _D` import, dummy `d = _D.Draw(...)`) were removed exactly as documented in GLM's mirror-premise note — behavior-preserving (immediately rebound / unused). The single-hunk mirror discipline from Phase B Note 1 is satisfied. [TEST RESULT]

### PE.4 E4 — PER-AMENDMENT VERIFICATION

#### BATCH 1 (V-4a + V-2 + V-1): **PASS**

**V-1 — all four required amendments present in the canonical block. [FACT]**
- (a) Post-scale recheck + stepwise ladder: `while any(not im for _, im in runs) and total > int(h) - 2*padding and scale > 1.0: scale = 1.12 if scale > 1.12 else 1.0; widths, total = _measure_line(runs, scale)` — fires only when the line actually contains fallback runs, re-measures at every step, terminates at 1.0. Order verified: `fit_font_size` first (main-font metrics, swapped dims), scale applied per-line after.
- (b) Baseline alignment: `asc_main = get_font(size, bold).getmetrics()[0]` before the loop; `ly_run = ly if im else ly + asc_main - f.getmetrics()[0]` — exactly the amended formula (ly_fb = ly + ascent_main − ascent_fb).
- (c) THREE config setdefaults present at module level in **both** cells 11 and 12: `fallback_font_wght` (600), `fallback_cjk_scale` (1.25), `fallback_cjk_stroke` (1) — idempotent on sequential execution.
- (d) Stroke: `sw = 0 if im else _fb_stroke` and `draw.text(..., stroke_width=sw, stroke_fill=text_color+(255,))` — applied to fallback runs only. `get_font_fb` additionally honors bold via `wght = max(600, 700 if bold)` through the prescribed OSError-guarded `set_variation_by_axes`; cache key `(int(size), bool(bold))` correctly separates the two variants.

**V-2 — CONFIRMED in the live mask path. [FACT]**
- Band inserted in `build_page_text_mask` (cell 6) **after** the `mask_clip_to_regions` clip block (lines 815–825) and **before** `return mask` (line 845); in-scope variables verified (`h` from `image_bgr.shape[:2]` at 783, `detection_cfg = MANGABD_CONFIG["detection"]` at 785, `regions` = function param).
- Knob: `detection_cfg.setdefault("mask_vpad_vertical", 10)` (833); `if vpad > 0` gate; two filled `cv2.rectangle` bands at each column tip, clamped to image bounds.
- Predicate (838): `rw < 90 and rh > 2 * max(1, rw)` on region dims. Live vertical-renderer predicate (11:215 / 12:172): `w < 90 and h > 2*max(1, w)`. **Semantically identical including the `max(1, ·)` guard**; textual form differs only by variable names (w→rw, h→rh) and `2 *` vs `2*` whitespace — see note N2.
- Comment (827–832) documents the effective ceiling = `mask_clip_padding` (10) with the cell-9 re-clip to boxes+10 — matches the clip call (`padding=10`, line 819) and the Phase B arithmetic.

**V-4a — CONFIRMED. [FACT]**
- rev2 metadata.json: `translation_engine: "nllb"`, `source_type: "B/W manga page"`, `naming_note` (folder intentionally NOT renamed, Owner decision quoted, "0 chroma, Flash-measured"), plus `metadata_revision: 2` and a `revision_note` crediting the visual review — all present.
- rev1 preserved verbatim (PE.1); README pointer line added (naming provenance + both metadata files); folder NOT renamed (no R entries; all sample paths unchanged).

#### BATCH 2 (V-3): **PASS**

**V-3 Layer 1 (cell 7, `ocr_region`) — CONFIRMED. [FACT]**
- Candidate set = [ROTATE_90_CLOCKWISE, ROTATE_90_COUNTERCLOCKWISE] **only**; upright is excluded from the vertical path (preserved verbatim as the `else:` branch).
- Selection: `chosen = candidates[0]` (CW) then `if cand["score"] > chosen["score"]` — strict `>`, deterministic rotated-first tie-break.
- Audit trail: `vertical_ocr = {"chosen_orientation": …, "candidate_scores": {…}}` written into the OCR record (sidecar field, additive; `None` for non-vertical), plus a `warnings` entry naming the chosen orientation and both scores.
- Predicate uses REGION dims (`rw_, rh_ = int(region.get("width", 0)), int(region.get("height", 1))`), NOT the preprocessed crop dims; the in-code reconciliation note (crop context + overlay border + preprocess padding widening S001 R1 to ~95–113 px, defeating a crop-dims test) matches the Phase B finding this amendment came from.

**V-3 Layer 2 (cell 16, both branches) — CONFIRMED. [FACT]**
- Severity `warning` only → `add_quality_issue` routes it into `manual_review_flags_dict` → `manual_review_flags` (🟡); `add_quality_issue` contains no raise paths; the checks themselves are dict lookups + `re.search` on strings with defaults — cannot raise/abort/block a page. Degrades safe: missing detections artifact → `det_geo={}` → geometry defaults → predicate false → no flag.
- `import re` present **inside both snippets** (artifact branch line 371 with the Phase B attribution comment; df branch line 396) — cell-standalone-safe.
- Geometry provenance: artifact branch uses `region = item.get("region", {})` (line 292) from the **ocr sidecar entries**; df branch builds `det_geo` from `load_json_artifact(page_id, "detections")` keyed by `int(dr["id"])` and looks up with the row's `region_id` (both int) — the Phase B amendment (detections are truth, df x/y/w/h may be box-snapped) is implemented as amended.

#### BATCH 3 (V-5): **PASS**

- **Registry field `key_env`:** 14 occurrences of `key_env` in cell 8, zero code references to `api_key_env` anywhere in the notebook. The raw substring `api_key_env` appears exactly **2×, both inside explanatory comments** (cell 8:82, 8:84) documenting the sanitizer hazard — no dict key, variable, or accessor uses it. [FACT]
- **Adapter:** `translate_with_provider` (cell 8:555) uses the existing `openai` SDK (`from openai import OpenAI`, per-provider `base_url`/`model` from the registry, key from `MANGABD_SECRETS[key_env]`, ollama placeholder-key branch, missing-key → WARN + `""`).
- **Dispatcher:** new `elif engine in MANGABD_CONFIG["translation"].get("providers", {}):` binds `translate_with_retry(lambda t, rt: translate_with_provider(t, rt, engine=engine), text, region_type=region_type)` — **verbatim the closure fix prescribed in Phase B amendment 1**. `translate_with_retry` is **byte-identical** main↔HEAD (46 lines, signature `(translate_func, text, region_type="bubble")`; def at main 8:371, positional invocation at main 8:390 — the two brief-cited lines) — no `**kwargs` widening. [FACT + TEST RESULT]
- **switch_translator:** `valid_engines = ["manual", "gemini", "chatgpt", "nllb"] + list(providers.keys())` — dynamic from the registry.
- **UI (cell 25):** `mode_sel` options extended (openrouter/deepseek/qwen/ollama; NLLB relabeled "experimental" per Owner policy); new `btn_provider` + `on_provider` (engine from `mode_sel.value`, `force=True`, error surface cloned from `on_nllb`); binding list extended by exactly one pair; mode_panel provider hint names the Colab secret `<m>_api_key` consistently with SECRET_SOURCES.
- **SECRET_SOURCES (cell 1):** `qwen_api_key` (QWEN_API_KEY, DASHSCOPE_API_KEY), `deepseek_api_key` (DEEPSEEK_API_KEY), `openrouter_api_key` (OPENROUTER_API_KEY) added; ollama deliberately absent (commented).
- **translator_model:** additive record-dict field (8:1201-area), row-level value wins via `or`-chain, provider model resolved from registry, manual/gemini/nllb leave it empty — sidecar-only, no wire-format change.
- **Legacy branches byte-untouched:** `manual` / `gemini` / `chatgpt` / `nllb` branch bodies in `translate_text` extracted from both versions and compared — **byte-identical** (the only chain delta is the inserted providers `elif`; `else:` identical too). [TEST RESULT]
- **clean_translation:** pre-existing normalizer (quote/prefix/whitespace) present and unchanged; the adapter applies it to model output (8:580). **Manual apply path:** `apply_manual_translation` and `translate_manual_upload` are **byte-identical to main** — Phase C added nothing to any manual path. See PE.7 for a required clarification of this gate item.

### PE.5 E5 — INDEPENDENT RUNTIME SPOT-CHECKS: **5/5 PASS**

Own harness; every executed segment extracted verbatim from the pushed bytes (sha256 recorded; e.g. `_qc_render_vertical` 2267 ch `e27f769797d8ff4f`; `ocr_region` vertical block 1244 ch `272e66e41f9f`; `save_config` 969 ch `87f2eb223ddc`; dispatcher elif 446 ch `66c92a3689ab` — the only transformations for standalone exec were dedent, leading `elif`→`if`, and dropping the outer-chain `else:`; condition/body bytes untouched). Dependencies stubbed at module boundaries (fake fonts/`ImageDraw`, fake `cv2`, fake `openai`, stubbed `qwen.recognize`); real PIL canvas for paste/rotate.

- **(a) Ladder — PASS.** Overflowing scaled line (budget 392 px): fallback sizes requested `[12, 11, 10]` + final draw re-request at 10 → ladder walked 1.25→1.12→1.0 with a re-measure at **every** step; second scenario stopped at 1.12 once the re-measured total fit (`[12, 11]` + draw). Baseline exact: fb run y = 24 + 8 − 14 = 18 (= ly + ascent_main − ascent_fb); main run y = ly. Stroke: `1` on the fallback run, `0` on the main run, `stroke_fill = text_color + (255,)`.
- **(b) Tie-break — PASS.** Equal scores (1.7 / 1.7) → **CW wins** (`rotate_90_clockwise`), 2 recognize calls, both scores + orientation written to `vertical_ocr`, warning appended. CCW strictly greater (1.75 > 1.7) → CCW wins. Wide region (100×300) → exactly **1** upright call, no rotated candidates, `vertical_ocr is None`.
- **(c) Adapter shape — PASS.** qwen: `OpenAI(api_key=<qwen_api_key secret>, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")`, `model="qwen-plus"`, temperature 0.3, max_tokens 512, roles [system, user] — field-for-field the chatgpt pattern; the chatgpt reference adapter passes **no** `base_url` (SDK default), so the per-provider `base_url` is exactly the provider adapter's addition. Ollama: placeholder key, `http://localhost:11434/v1`. Dispatcher closure: retry stub captured `(func, text, region_type)` — engine **not** forwarded to `translate_with_retry`; calling the captured func produced the qwen-engine result (binding proven end-to-end).
- **(d) Sanitizer control — PASS.** Committed `save_config` run against a probe registry: persisted keys = `['base_url', 'key_env', 'model']` — **`key_env` survives**, `api_key_env` (control) **stripped**, legacy `gemini_api_key`/`auth_token` still stripped. Key-name check confirmed keys-only (values untouched).
- **(e) Predicate truth table — PASS.** All committed copies (cell 6 mask band; cell 7 selector; cell 16 artifact-branch and df-branch): 61×298 → **True**, 100×300 → **False**; the composite flag predicate additionally requires kana+latin (pure non-kana text suppresses the flag); the committed regexes fire on S001-like text `おてあらい U/I`. Grounding: S001 `detections.json` region 1 is exactly **61×298, region_type=overlay** (region 2, 87×156, correctly does NOT fire: 156 < 174).

### PE.6 E6 — REGRESSION GUARDS: **PASS**

- **NLLB (cell 19 version):** cell 19 **byte-identical** to main (sha256 `3e3153c2009d`). Cell 8's `translate_with_nllb` dispatcher branch byte-identical (PE.4 batch 3). [FACT]
- **recover_coordinates (cell 11) / restore_boxes (cells 11+12) / apply_container_types (cells 11+12):** function bodies **byte-identical** main↔HEAD (shas `5ad21679c42e`, `c8a9f5f5419f`, `da3284c80be5`, `f82ca5047fc2`, `2d652385f521`) despite living in edited cells — V-1 edits did not perturb them. [FACT]
- **Slicer + download patches:** slicer references confined to cell 24 (byte-identical); download defs in cells 3/4/5/17/24 (all byte-identical) and cell 25 (`download_all_pages_zip`, `download_ai_text_once` — both byte-identical). Cell-12/25 "patch" matches are the `_QC_RENDER_PATCHED` flag idiom / comments, not patch logic. (Method note: a first-pass substring sweep false-positived on "dis**patch**er" in cell 8; refined to word boundaries.) [FACT]
- **Control Studio (cell 25):** `_safe` target set unchanged (`apply_translations_from_text`, `run_detection_ocr_all`, `run_translation_all`, `upload_images`) and **all resolve** to defs in the HEAD notebook; button bindings 13 → 14 with the only addition `btn_provider → on_provider`; every referenced callback defined; zero load-name globals dropped vs main (no renamed globals). [TEST RESULT]

### PE.7 Self-correction of a Phase B record (reviewer's own)

Phase B stated as [FACT]: "the manual path (`apply_manual_translation`) does not call `clean_translation` — manual text is never auto-edited." **That claim is wrong.** `apply_manual_translation` (cell 8:1092–1161) calls `clean_translation(translated_text)` at **8:1138 — on main, before Phase C** (the function is byte-identical in this commit). Phase C therefore satisfied the E4 item "manual apply path does NOT call clean_translation" in the only sense available to it: it introduced **no** `clean_translation` call into any manual path and modified nothing there. Practical impact is small — `clean_translation` strips surrounding quotes, `"Translation:"-style` prefixes, and collapses whitespace; it does not remove Bengali punctuation — but "manual text is never auto-edited" was inaccurate as written. If the Owner's intent is the strict end-state (manual input must bypass the normalizer), that is a **new change outside Phase C's approved scope** and should be an explicitly approved follow-up item, not a Phase E rejection ground. [ASSESSMENT]

### PE.8 Non-blocking observations

- **N2 — predicate textual form:** the V-2/V-3 predicates are semantically identical to the live renderer predicate but not byte-equal as raw strings (variable rename + `2 * ` whitespace). The brief's "byte-identical" is satisfied in the only realizable sense (same boolean expression over region dims, including `max(1, ·)`); runtime equivalence proven in E5e across all four sites. If the Owner wants literal text equality, it is a whitespace-only touch-up. [ASSESSMENT]
- **N3 — flag regex coverage:** `[\u3040-\u30FF\u3400-\u4DBF]` covers kana + CJK Extension A but **not** the main CJK block (4E00–9FFF): a vertical note mixing **kanji-only** + Latin will not flag. Consistent with the issue title ("kana + Latin") and the S001 failure mode; warning-only feature; worth widening if kanji-heavy vertical notes appear in S002. [ASSESSMENT]
- **N4 — sandbox boundary:** E5 executed committed bytes against stubbed module boundaries (qwen/`openai`/drive); live Colab behavior (real `qwen.recognize` confidence semantics, provider auth against real endpoints, `set_variation_by_axes` on Colab's Pillow) remains Owner-environment validation during the S002 fresh run — same limitation class as MANGABD-002 Phase D §B.10.4/§B.10.6. [ASSESSMENT]

### PE.9 Overall verdict

**PHASE E APPROVED.**

| Batch | Scope | Verdict |
|---|---|---|
| batch1 | V-4a + V-2 + V-1 | **PASS** (all amendments implemented; mirror equality holds) |
| batch2 | V-3 L1 + L2 | **PASS** (selector redesign + non-blocking flags as amended) |
| batch3 | V-5 | **PASS** (key_env + closure + registry/UI/SECRET_SOURCES/sidecar as amended; legacy branches byte-untouched) |

E1–E6 all PASS; zero required fixes. Notes N1–N4 are recorded for Owner awareness and none is a merge blocker. **Gating:** this sign-off is to be relayed through PM (Qwen3.8-Max) to the Project Owner; per DECISION.md §C, GLM-5.3 must NOT amend or merge until the Owner accepts. Recommended next steps: Owner-side live Colab validation (provider keys via SECRET_SOURCES bootstrap, `set_variation_by_axes` on Colab Pillow, fresh Run All) and the S002 acceptance run, which jointly attributes R1 improvements to batch-1 items as planned (Phase B Note 2).
