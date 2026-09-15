# GLM-5.3 — Lead Developer Log

## ROLE

Lead Developer / Software Architect

---

## CURRENT PHASE

Initial Codebase Audit — PHASE 1 COMPLETE

NO IMPLEMENTATION YET.

---

## MISSION

You are the Lead Developer for MangaBD.
Your first responsibility is NOT to write code.
Your first responsibility is to understand the current project completely enough to safely work on it later.

The project was originally developed with assistance from GLM-5.3 and GLM-5.3-Flash, but was later modified using Qwen3.8-Max.
Therefore, your previous knowledge of the project may be outdated.
The CURRENT REPOSITORY is the source of truth.

---

## EVIDENCE FORMAT USED IN THIS REPORT

- FACT: directly verified in the current repository code.
- HYPOTHESIS: technically plausible explanation, still needs verification.
- ASSUMPTION: accepted without evidence because evidence is unavailable.
- TEST RESULT: verified by executing a safe static/logical test (no project files modified).
- UNKNOWN: cannot currently be determined.

---

# REVIEW REPORT

## 1. Executive Summary

**[FACT]** The repository contains exactly one source artifact: `MangaBD_V12_ipynb_txt.ipynb (3).txt` — a Google-Colab Jupyter notebook (nbformat 4, ~800 KB JSON, **27 code cells, zero markdown cells**) — plus 5 agent/process documentation files under `agents/`. There is no `.py` module tree, no `requirements.txt`, no CI, and no tests outside the notebook's per-cell self-tests.

**[FACT]** The notebook implements a Bengali manga/manhwa translation pipeline for Google Colab (GPU T4 profile): upload → detect → OCR → translate → inpaint → render → QA → export, with a session/checkpoint system persisted to Google Drive (`/content/drive/MyDrive/MangaBD_V12`) or local fallback (`/content/mangabd`).

**[FACT]** The codebase has two clearly distinct strata:
1. A **structured V12 core** (cells 1–10 and 11–14 as numbered in their banners, i.e. notebook indices 0–10 and 15–18): consistent banner headers, config-driven design, per-cell self-tests, checkpoint-aware page manager, model manager with lazy loading.
2. A **patch/hotfix layer** (notebook indices 11–14 "QUALITY CORE"/"RESIDUAL KILLER", and 19–26: NLLB hotfix, copy/paste translation, stage-sync fix, mobile-download + long-strip slicer, Control Studio v4 UI, and three one-liner execution cells).

**[TEST RESULT]** The patch layer introduces a **critical execution-order hazard**: notebook cell index 14 (`kill_residual v3`) executes `run_inpaint_render_all(force=True)` at module level, but `run_inpaint_all`/`run_render_all` are only defined in notebook cell index 15. A fresh sequential "Run All" fails with `NameError`. The notebook only works when cells are run interactively/out of order in a warm kernel — which matches how the project owner actually uses Colab.

**[TEST RESULT]** `run_inpaint_render_all` is defined **5 times** (notebook indices 11, 12, 13, 15, 23). Because cell 15 and cell 23 both redefine it in "plain" form, the QUALITY CORE pipeline wrap (box-snap, mask filtering, residual killer, box restore) is **orphaned** in a sequentially-run session: the functions exist but no active pipeline path calls them. The only quality-core feature that survives is the monkey-patched vertical-note renderer, because nothing redefines `render_bengali_text` afterwards.

**[FACT]** No secrets are embedded in the notebook (scanned for `ghp_`, `sk-`, `AIza`, `hf_`, `Bearer` patterns — all clean). Secrets are read from env vars / Colab userdata at runtime and stripped from any saved config.

**Overall assessment:** the V12 core is well-engineered for a notebook project, but the accumulated patch layer has created a fragile, order-dependent runtime where the *effective* pipeline depends on which cells were last executed. This must be reconciled before any further development.

---

## 2. Current Architecture

**[FACT]** Repository layout:

```
MangaBD-/
├── MangaBD_V12_ipynb_txt.ipynb (3).txt   # the entire application (27 code cells)
└── agents/
    ├── PROJECT_CONTEXT.md
    ├── TASK.md
    ├── GLM_5_3.md          (this file)
    ├── GLM_5_3_FLASH.md
    └── DECISION.md
```

**[FACT]** Notebook metadata: `accelerator: GPU`, `colab.gpuType: T4`, kernel `python3`. Stored outputs (partial, cells 0–6 only) prove a successful run on **2026-08-31 12:18** with Python 3.13.15, CUDA available, **14.56 GB GPU**, base dir `/content/mangabd` (Drive was NOT mounted), `hf_token: not set`.

**[FACT]** The 27 notebook cells map to these components (indices are physical cell order):

| Index | Banner name | Component |
|---|---|---|
| 0 | Cell 1 | Environment doctor, package install, libraqm check |
| 1 | Cell 2 | CONFIG, secrets, session dirs, logger |
| 2 | Cell 2.1 Hotfix | Adds missing `paths` keys (session/pages/logs/export/cache) |
| 3 | Cell 3 | Session storage & checkpoint manager (manifest, artifacts, translation_df) |
| 4 | Cell 4 | zyddnys repo clone+patch, fonts, libraqm render test |
| 5 | Cell 5 | ModelManager + GPU memory controller + QwenVLWrapper |
| 6 | Cell 6 | Detection service (RT-DETR + CTD) |
| 7 | Cell 7 | OCR service (Qwen VL) |
| 8 | Cell 8 | Translation service (manual/gemini/chatgpt/nllb) |
| 9 | Cell 9 | Inpainting service (LaMa + OpenCV fallback) |
| 10 | Cell 10 | Rendering service (Pillow + libraqm Bengali) |
| 11 | QUALITY CORE FINAL | config overrides, NotoSansJP fallback font, box-snap, mask filter, kill_residual v1, vertical renderer patch |
| 12 | QUALITY CORE container-aware | same family, simpler box-snap, restore_boxes, vertical renderer patch (2nd) |
| 13 | RESIDUAL KILLER | kill_residual v1 (again) + pipeline wrap w/ mask filter |
| 14 | kill_residual v3 | pixel-level, box-only residual eraser; **executes pipeline at cell run** |
| 15 | Cell 11 | Upload/input & pipeline orchestrator (run_* batch functions) |
| 16 | Cell 12 | Quality inspector & manual review |
| 17 | Cell 13 | Export, preview & download |
| 18 | Cell 14 | Dashboard, session log & final review |
| 19 | Hotfix | `apply_translations_from_ai_file` rescue + NLLB src_lang fix |
| 20 | (one-liner) | executes `apply_translations_from_ai_file()` |
| 21 | (one-liner) | prints translation_df preview |
| 22 | Copy/Paste Manual Translation | `apply_translations_from_text` + fallback |
| 23 | FIX | `sync_translate_stage` + robust `run_inpaint_render_all` |
| 24 | PATCH | mobile single-download + long-strip slicer |
| 25 | CONTROL STUDIO v4 | ipywidgets mobile UI |
| 26 | (one-liner) | `render_all_pages(force=True)` |

**[FACT]** Configuration is a single in-memory dict `MANGABD_CONFIG` (cell 1), progressively extended by `setdefault` in every later cell, sanitized and saved to `config_v12.json`. Secrets live in a separate `MANGABD_SECRETS` dict that is never serialized.

**[FACT]** State layer: `MANGABD_MANIFEST` (per-session `manifest.json`, atomic writes via tmp+`os.replace`), per-page artifact directories (`original.jpg`, `detections.json`, `text_mask.png`, `ocr.json`, `translation.json`, `inpainted.png`, `final.jpg`, `qa.json`, `preview.jpg`), and a `translation_df` pandas DataFrame persisted as CSV+JSON.

**[FACT]** All heavy imports and global monkey-patches flow through the notebook's shared kernel namespace; there is no module isolation. Multiple cells rely on names imported by *earlier* cells (e.g. cell 10 uses `Path` without importing it — it works only because cell 1 imported `pathlib.Path` into the kernel).

---

## 3. Actual Processing Pipeline

**[FACT]** Traced end-to-end flow (happy path):

1. **Upload** (cell 15): `upload_images()` → Colab file dialog → decode (PIL w/ EXIF transpose, cv2 fallback) → min-size check (50×50) → `register_image_array()` → `init_page()` stores `original.jpg` and marks stage `upload`.
2. **Detection** (cell 6): `detect_page()` → `rtdetr_detect()` (RT-DETR-v2, threshold 0.30, classes 0=bubble/1=text_bubble/2=text_free) → if no candidates, **CTD fallback**; if candidates exist and `use_ctd_pixel_mask=True` (default), **CTD runs anyway to produce a pixel mask** → dedupe (IoU 0.5, score-priority) → parent-bubble assignment (containment ≥0.55, smallest bubble wins) → heuristic region classification (narrator/bubble/thought/sfx/overlay using white-ratio, border variance, position/aspect rules) → reading-order sort (LTR, y-banded at 50px) → mask build (CTD pixel mask preferred, bbox fallback; close→clean→adaptive dilate→clip to regions+10px) → artifacts saved, stage `detect`.
3. **OCR** (cells 5+7): per region `ocr_region()` → context-padded crop (white border for bubbles, replicated border for sfx/overlay) → preprocessing (upscale <40px, bilateral filter, CLAHE, pad) → `QwenVLWrapper.recognize()` (deterministic greedy, max 512 new tokens) → heuristic confidence + English-score → status ok/low_confidence/non_english/failed/empty → rows upserted into `translation_df`.
4. **Translation** (cell 8, patched by 19/22): engine `manual` (default) exports `ai_text_export.txt` in `[page:id] English → বাংলা` format for human translation, then re-imports via upload/paste with a "rescue" path for left-side-Bengali. Auto engines: Gemini (`gemini-2.5-flash`), ChatGPT (`gpt-4o-mini`), NLLB-200-distilled-600M (offline). Region-type-aware prompts, SFX glossary exact-match shortcut, retry w/ linear backoff (3×), Bengali validation.
5. **Inpainting** (cell 9): `inpaint_page()` → loads cached `text_mask.png` (fallback: bbox mask from regions, or re-detect) → mask prepare (uint8, close, clean; artifact masks NOT re-dilated by default) → **LaMa Large** (unload others first; 1024px) → OpenCV TELEA fallback → saves `inpainted.png`.
6. **Rendering** (cell 10 + monkey-patches): `render_page()` → PIL canvas from inpainted → per row with valid Bengali text: background-aware color, per-type stroke, binary-search font fit (8–48px, no truncation, min-size fallback), grapheme-safe wrapping (`regex \X`) → centered draw; rotated path for tilted regions; **vertical-note renderer patched in** (w<90 and h>2w → render on transposed canvas, rotate −90°, CJK fallback font NotoSansJP for non-Bengali runs) → saves `final.jpg`.
7. **QA** (cell 16): OCR/translation/render inspections with severity weights (critical=20, warning=7, info=1) → page score /100 → manual review flags; optional Qwen-based visual QA (default OFF).
8. **Export** (cell 17): final images (JPEG q=92), translation CSV, ai.Text, quality report, manifest, config, session ZIP, before/after previews.

**[FACT]** Orchestrator (cell 15) exposes `run_detection_ocr_all`, `run_translation_all`, `run_inpaint_all`, `run_render_all`, `run_inpaint_render_all`, `run_full_pipeline`; every batch function is resume-aware (skips stages already marked done unless `force=True`).

**[FACT]** The Control Studio UI (cell 25) duplicates orchestration inside button callbacks, including its own `_sync_translate()`, and its "Inpaint + Render" button calls `run_inpaint_all`/`run_render_all` **directly**, bypassing even cell 23's `run_inpaint_render_all`.

---

## 4. Current Models

**[FACT]** Model inventory (all verified in code):

| Model | Where | Purpose | Loading | Notes |
|---|---|---|---|---|
| `ogkalu/comic-text-and-bubble-detector` (RT-DETR-v2, HF) | cell 5→6 | Primary text/bubble detection | `RTDetrV2ForObjectDetection.from_pretrained`, cache in Drive `models/rt_detr_bubble`, float32, `.eval()` | threshold 0.30; 3 classes |
| ComicTextDetector (CTD, zyddnys) | cell 4 clone → cell 5/6 | Fallback detector + pixel text mask | weight `comictextdetector.pt` downloaded from zyddnys GitHub release beta-0.3; async `load(DEVICE)` | detection_size 1024 |
| LaMa Large (zyddnys `inpainting_lama_mpe`) | cell 4→5→9 | Text removal / inpainting | `LamaLargeInpainter` subclass w/ model-dir override; async load | 1024px; unloads other models first |
| `Qwen/Qwen2.5-VL-3B-Instruct` | cell 5→7 | OCR (English extraction) | `Qwen2_5_VLForConditionalGeneration` (fallback `Qwen2VL...`), fp16 on CUDA, `device_map="auto"`, **local HF cache** `/root/.cache/huggingface/hub` to avoid Drive I/O errors; processor cached to Drive | deterministic greedy; heuristic confidence (NOT token probs — admitted in code comment) |
| `facebook/nllb-200-distilled-600M` | cell 8 (redefined in 19) | Offline translation | `AutoModelForSeq2SeqLM`, cache Drive `models/nllb`, forced BOS `ben_Beng` (fallback id 100362), beams=4 | cell 19 fixed `src_lang` API break for newer transformers |
| Gemini `gemini-2.5-flash` (API) | cell 8 | Cloud translation | `google-genai` SDK, needs `gemini_api_key` | default engine is `manual`, not gemini |
| GPT `gpt-4o-mini` (API) | cell 8 | Cloud translation | `openai` SDK, temperature 0.3, max 512 tokens | optional |
| OvisOCR2 | cell 5 `ensure_ovis()` | **Placeholder only** | raises `NotImplementedError` | config `experimental.ovis_ocr_enabled=False` |

**[FACT]** OCR confidence is a heuristic (base 0.45 + length bonuses + English-score bonus + artifact-char penalty, capped 0.95), explicitly documented in-code as "not real token probability".

**[HYPOTHESIS]** RT-DETR is intentionally loaded in float32 (no fp16) for accuracy at the cost of ~2× VRAM; on a 12GB+ T4 this coexists with Qwen-3B fp16 only thanks to the aggressive `unload_all` calls before each heavy stage.

---

## 5. Important Files / Cells

**[FACT]** The only source file is the notebook. The most consequential cells for future work:

- **Cell 3 (index 3)** — storage/checkpoint core: `atomic_write_json`, `init_page`, `mark_stage_done`, `reset_page`, artifact IO, `translation_df` persistence. Nearly everything depends on it.
- **Cell 5 (index 5)** — `ModelManager` (lazy `ensure_*` per model, unload, GPU summary), `_run_async` (nest_asyncio), `QwenVLWrapper`.
- **Cell 6 (index 6)** — detection + classification + mask construction; the most algorithm-dense core cell.
- **Cell 10 (index 10)** — renderer: `fit_font_size` (binary search), grapheme wrapping, colors, rotated text.
- **Cells 11–14 (indices 11–14)** — quality patch layer: `apply_container_types` (white-box snap→narrator), `mask_only_translated`, `kill_residual` (3 versions), `restore_boxes` (synthetic white box + black border), vertical-note renderer monkey-patch.
- **Cell 15 (index 15)** — orchestrator; defines the `run_*` API the UI and one-liner cells call.
- **Cells 19–26 (indices 19–26)** — hotfix/UI layer incl. Control Studio and the download/slicer monkey-patches.

**[FACT]** Filename oddity: the source of truth is a `.txt` copy of an `.ipynb` named `MangaBD_V12_ipynb_txt.ipynb (3).txt` (browser download duplicate suffix "(3)"), indicating manual file-management rather than git-native workflow.

---

## 6. Qwen3.8-Max Modifications

**[FACT]** Git provides **no attribution evidence**: the entire notebook entered history in a single commit (`27d8643`, 2026-09-13, "Add files via upload"). All other commits only touch `agents/` docs (2026-09-14). There is no diff history of the notebook.

**[HYPOTHESIS]** Based on internal evidence (style, comment language density, guard flags, banner comments like "Delete all old FIX/QC cells", "replaces all FIX patches"), the **patch/hotfix layer (indices 11–14, 19–26) is the post-original modification phase** — most plausibly the Qwen3.8-Max era (and/or owner-driven interactive fixes), while the structured V12 core (indices 0–10, 15–18) matches the "original GLM-era architecture". Supporting signals: the core uses a uniform generator-like template (banners, numbered sections, self-tests, Bengali+English mixed comments); the patches use a different compressed style, rely on the core's globals, and repeatedly override each other.

**[ASSUMPTION]** The stored partial outputs (2026-08-31) and the "(3)" filename suffix indicate the owner iterated interactively in Colab and saved snapshots; the uploaded snapshot is the state the owner considered current.

**[UNKNOWN]** Which specific model authored which specific patch cell cannot be determined from the repository. Any claim beyond the style-based hypothesis above would be fabrication.

**[FACT]** Notable *behavioral* deltas the patch layer introduces relative to the clean core (regardless of authorship):
1. Detection config overrides: `ctd_mask_threshold` 60→55, dilate radius 6→5, `redilate_artifact_mask=False`.
2. Fallback font `NotoSansJP.ttf` + `vertical_rotate=-90` added to rendering config.
3. Vertical-note special-case rendering (w<90, h>2w) with CJK fallback.
4. `translate_with_nllb` rewritten for newer `transformers` tokenizer API (`tokenizer.src_lang` attribute instead of call kwarg).
5. Manual-translation "rescue" logic (left-side Bengali accepted as translation).
6. `sync_translate_stage` (marks `translate` done from data, not from pipeline execution).
7. `run_inpaint_render_all` de-hardened (no longer requires translate stage).
8. Long-strip slicer wrapping RT-DETR+CTD (slice 1400px, overlap 240px, trigger h>2w, `SLICE_MODE=True` by default).
9. `colab_files.download` globally replaced by base64 data-URI tap-links (≤25MB).
10. Control Studio v4 widget UI with checkpoint reset.

---

## 7. Strengths

**[FACT]**
1. **Solid checkpoint architecture** for a notebook: atomic JSON writes, per-page artifact dirs, stage flags with resume, `reset_page(from_stage=...)`, `current_session.txt` pointer, `events.jsonl` structured log.
2. **Defensive secrets handling**: env/Colab-userdata sources only, sanitizer strips any key containing `api_key|token|secret|password` before saving config; verified self-test "No secrets leaked into config".
3. **Per-cell self-tests with hard failure** (`raise RuntimeError` on failure) give fast environment diagnostics; stored outputs prove cells 1–7 passed on the reference machine.
4. **Pragmatic manual-translation workflow** (ai.Text format, paste-or-file, rescue parsing) — the most production-realistic part of the human loop.
5. **Multi-engine translation** with retry/backoff, glossary and SFX shortcuts, region-type-aware prompts.
6. **Renderer quality features**: grapheme-safe Bengali wrapping, background-aware colors, binary-search font fitting without truncation, stroke per region type, rotated text path.
7. **Memory-aware model lifecycle**: lazy load, unload-before-heavy-stage, local HF cache for Qwen to avoid Drive I/O errors.
8. **Verification-minded patches**: kill_residual v3 explicitly guards against touching non-solid-box regions (face/art safety); slicer uses overlap + dedupe to avoid losing boundary text.

---

## 8. Weaknesses

**[FACT]**
1. **Order-dependent execution** (critical): the notebook cannot be run fresh top-to-bottom (see §9 P-1). Effective behavior depends on which definition of `run_inpaint_render_all` / `kill_residual` / etc. was executed last.
2. **Five definitions of one pipeline function**, three of one residual-killer, two render-patches, two NLLB translators — no single source of truth; the "winner" is implicit.
3. **Quality-core is orphaned in sequential runs**: cells 15 & 23 override the wrapped pipeline, and the UI button bypasses it entirely; box-snap / mask-filter / residual-kill / box-restore silently stop being called.
4. **Global monkey-patching** of `colab_files.download`, `rtdetr_detect`, `ctd_detect_boxes_and_mask`, `render_bengali_text` — behavior is invisible at call sites and fragile to re-runs (partially guarded via `_QC_RENDER_PATCHED`, `_MBD_SLICED`, `__mbd_patched` flags).
5. **Single 800KB notebook as the only artifact**; no module decomposition, no versioned requirements (versions are `>=` ranges resolved at runtime), no external tests.
6. **Colab-only coupling** throughout (`google.colab.files/userdata/drive`, `/content` paths) with no local/Jupyter fallback.
7. **Heuristic OCR confidence** presented as `confidence` — downstream QA thresholds (0.35/0.50/0.65) therefore measure text-shape plausibility, not recognition certainty.
8. **Duplicated logic**: three Bengali validators, three special-marker checkers, two mask cleaners, two dedupes, three ai.Text parsers (cell 8, cell 22 local, cell 25 builder) — drift risk already visible (marker sets differ: cell 10/16 include `"nan"`, cell 8 does not).

---

## 9. Potential Bugs

**[TEST RESULT]** (verified by static execution-order analysis; no files modified)
- **P-1 (Critical):** cell index 14 line 40 runs `run_inpaint_render_all(force=True)` at module level → calls cell-13's definition → references `run_inpaint_all` (defined only in index 15) → `NameError` on fresh sequential run. Also triggers heavy GPU work as a side effect of *defining* a patch.
- **P-2 (Critical):** `run_inpaint_render_all` final definition after sequential run = cell 23's (plain inpaint+render with sync). QUALITY CORE wrap from cells 11–13 is dead code in that state; conversely, in the owner's warm-kernel workflow the wrap wins. Same code, two different pipelines.
- **P-3 (High):** cell 11's `recover_coordinates()` executes at cell-run time and mutates `translation_df` from artifacts — on a fresh run this is a no-op, but if run *after* `apply_container_types` (which snaps coords to white boxes), it **reverts** snapped coordinates back to detection coords (detections.json is treated as "আসল সত্য"/ground truth), silently undoing box-snap.

**[FACT]**
- **P-4 (Medium):** cell 10 uses `Path` without importing it (works only via kernel-global leak from earlier cells); same pattern for other cross-cell name reliance — any cell refactor breaks at a distance.
- **P-5 (Medium):** `apply_container_types` reclassifies any box that snaps to a large white region as `narrator`; a *thought bubble* or white SFX panel with ≥85% fill can be mis-typed, after which `restore_boxes` paints a synthetic black-bordered white rectangle over it — destructive to artwork if misfired.
- **P-6 (Medium):** `restore_boxes`/`kill_residual`/`mask_only_translated` mutate the `inpainted`/`mask` artifacts **in place** on disk; re-running them compounds edits (no idempotency guard, no backup of pre-patch inpaint).
- **P-7 (Medium):** `translation_df["bengali_valid"].astype(bool)` (cells 15, 23, 25) — if the column round-trips through CSV with any empty/NaN cell (object dtype), NaN→`True`, inflating "valid Bengali" counts and falsely marking pages translated. Core paths write real bools, but marker rows and fallback paths write `""`.
- **P-8 (Medium):** `_has_valid_trans` treats ANY text starting with `[` as invalid — legitimate Bengali text beginning with `[` (rare but legal) would be skipped by residual-kill/mask-filter.
- **P-9 (Low):** OCR config keys `temperature`/`top_p` are never passed to `generate()` — dead config inviting false confidence.
- **P-10 (Low):** cell 24's "proof" block executes CTD (downloads/loads the model) and requires an existing `02.jpg` page at cell-run time; wrapped in try/except, but a heavy, session-dependent side effect of running a "patch" cell.
- **P-11 (Low):** cell 12's `_qc_render_vertical` sets `size, lines = 8, [text]` then immediately overwrites both — dead code; and vertical rendering hardcodes text color `(0,0,0)` ignoring background-aware colors (cell 11 version takes a `text_color` param but wrappers pass `(0,0,0)` anyway).
- **P-12 (Low):** `deduplicate_boxes` suppresses by IoU only — a text box fully inside a bubble box with IoU<0.5 survives as duplicate region; parent-bubble logic compensates only for rendering grouping, not for double OCR.

---

## 10. Performance Bottlenecks

**[FACT]**
1. **Double detection per page**: when RT-DETR succeeds, CTD still runs (default `use_ctd_pixel_mask=True`) to build the pixel mask → two detection models per page on every fresh detect.
2. **`clear_gpu_cache()` inside every OCR call** (`QwenVLWrapper.recognize`) — `gc.collect()` + `torch.cuda.empty_cache()` per text region (dozens per page) adds measurable overhead and allocator churn.
3. **Per-region OCR round-trips**: one `model.generate()` per region crop (no batching) — the dominant wall-clock cost on long chapters.
4. **Pipeline ping-pong of models**: inpaint unloads all models then loads LaMa; re-render unloads nothing but OCR re-entry unloads LaMa for Qwen (`ensure_qwen(unload_others=…)` path) — repeated load/unload cycles across stage re-runs (mitigated by Drive-cached weights but still slow).
5. **`save_manifest()` on nearly every mutation** (stage marks, meta updates, errors) with full JSON rewrite per page — O(pages×regions) IO on Drive-backed storage.
6. **Long-strip slicer** (cell 24): slices at 1400px w/ 240px overlap then dedupes — for very tall strips this multiplies RT-DETR+CTD invocations (correctness-motivated, but the single largest throughput cost on webtoon strips).
7. **`apply_container_types`/`recover_coordinates`/`restore_boxes`** each re-`iterrows()` the whole DataFrame and re-save CSV per call — fine at 10s of pages, degrading at 100s.

---

## 11. Reliability Risks

**[FACT]**
1. **Fresh-run failure** (P-1) — the single biggest reliability problem: the documented notebook cannot bootstrap itself.
2. **Artifact/checkpoint divergence**: `mask_only_translated` (quality layer) permanently shrinks the stored mask to translated regions only; if the user later adds translations and re-runs inpaint **without** regenerating the mask, the earlier-removed regions stay visible — checkpoint says "detect done", so mask is never rebuilt.
3. **In-place artifact mutation** (P-6) means a bad `kill_residual`/`restore_boxes` run cannot be undone except by full re-inpaint.
4. **Runtime dependency pinning absent**: `transformers>=4.49,<5` etc. resolved live — the cell-19 NLLB fix exists precisely because an upstream API broke; same class of breakage can recur (e.g. RTDetrV2, Qwen processor APIs).
5. **Drive-as-storage fragility**: the code itself acknowledges Drive I/O errors (Qwen moved to local cache); sessions, manifests, and models on Drive remain exposed to Colab/Drive hiccups mid-write (atomic JSON mitigates corruption, not unmounts).
6. **Silent skip paths**: render skips non-Bengali/marker/empty rows with only a WARN log; a mistranslated English passthrough yields a page that *looks* rendered but shows English text over inpainted art.
7. **`reset_checkpoint`** (UI) empties manifest and translation_df but does NOT delete per-page artifacts on disk → orphaned page dirs that a later same-named upload can collide with (page_id dedup appends hex suffix, so old artifacts leak storage instead of corrupting — medium risk).
8. **Widget-state vs kernel-state**: Control Studio captures function references at button-click time via `_safe()`; if the user re-runs core cells after opening the UI, callbacks silently bind to stale/missing functions.

**[HYPOTHESIS]** The stored partial outputs (only cells 0–6, execution counts cleared) suggest the owner's last saved snapshot came from an interrupted or partially-cleaned session; the true "known-good" runtime state lives in the owner's Colab kernel, not in the repo.

---

## 12. Maintainability Risks

**[FACT]**
1. **Redefinition jungle** (5× `run_inpaint_render_all`, 3× `kill_residual`, 2× render-patch, 2× NLLB, 2× detection wrappers) with cross-cell dependencies — any edit requires simulating the full cell execution order mentally.
2. **No tests outside the notebook**; the per-cell self-tests are good but run only in Colab with GPU/network.
3. **Mixed languages (Bengali/English) in comments and prints** — fine for the current owner, raises friction for collaboration and grep-ability.
4. **Magic numbers everywhere** (thresholds 0.30/0.55/0.60/0.65/0.85, radii 5/6/13, slices 1400/240, aspect 2.0/2.5, w<90, etc.) — some in config, many hardcoded in patch cells.
5. **The `.txt`-of-an-`.ipynb` with "(3)" suffix** signals manual snapshot management; risk of editing/committing a stale copy.
6. **800KB single file** — code review via GitHub UI is impractical; diffs of the notebook are near-unreadable.

---

## 13. Unknowns / Questions

**[UNKNOWN]**
1. Which patch cells (11–14, 19–26) were authored by Qwen3.8-Max vs. the owner vs. GLM-era iterations — no git evidence exists.
2. Whether the owner's canonical workflow is: (a) fresh Run-All (currently impossible, P-1), (b) run cells 0–10+15–18 then patch cells, or (c) some other manual order. The intended execution order is nowhere documented.
3. Whether the QUALITY CORE wrap (box-snap etc.) is *currently desired* in the final pipeline, or whether the plain cell-23 behavior is the accepted latest state — the two produce visibly different outputs.
4. Actual output quality on real pages: no rendered images, masks, or session exports exist in the repo — **NO_VISUAL_EVIDENCE_AVAILABLE** for text placement, overflow, inpainting quality, or art preservation.
5. Whether `SLICE_MODE=True` (cell 24) has been validated against non-strip pages for regression (dedupe could merge legitimate distinct regions in dense pages).
6. Which Colab Python/transformers version the last successful full run used (stored outputs show Python 3.13.15 on 2026-08-31 but only cells 1–7 completed in that snapshot).
7. Whether the NLLB fallback BOS id `100362` is still correct for the pinned transformers version at runtime.
8. Whether `ogkalu/comic-text-and-bubble-detector` remains available/unchanged upstream (remote dependency, unpinned revision).
9. Whether `restore_boxes`' synthetic black-bordered white rectangles are an accepted stylistic choice by the owner or a temporary workaround.
10. Whether the "(3)" file is the newest notebook — the owner may hold a newer local copy.

---

## 14. Recommended Next Investigations

**[FACT-based proposal; no code changes made.]**

Priority order for Phase 2 (after GLM-5.3-Flash's independent review and owner decisions):

1. **Reconcile the pipeline-entrypoint chaos (P-1/P-2)** — decide the ONE authoritative `run_inpaint_render_all` (plain vs. quality-core vs. sync+quality-core), delete or archive the losing definitions, and remove the module-level execution from patch cells. This unblocks fresh Run-All.
2. **Establish the canonical cell execution order** and document it in the repo (or better: extract a `mangabd/` module package with an explicit composition root, keeping the notebook as a thin driver).
3. **Snapshot-based artifact mutation** — make `kill_residual`/`restore_boxes`/`mask_only_translated` write to versioned artifacts (or re-derive from `original` + `mask` each run) so they become idempotent and reversible.
4. **Add real visual regression evidence** — commit one small sample page + its artifacts (original/mask/inpainted/final) to the repo so both agents can review output quality concretely (currently NO_VISUAL_EVIDENCE_AVAILABLE).
5. **Pin the environment** (`requirements.txt` / Colab badge with tested versions) to stop silent upstream breakage (the NLLB incident proves the failure mode).
6. **Consolidate duplicated helpers** (Bengali validators, marker checkers, parsers, dedupe) into one definition each.
7. **Investigate P-7 (bengali_valid dtype)** with a quick pandas round-trip test once a sample session exists.

---

## STATUS

REVIEW_COMPLETE (Phase 1 audit finished; no source code modified)

**Audit coverage:** all 27/27 notebook cells read end-to-end; all agent docs read; git history inspected; safe static analyses executed (AST syntax, execution-order, redefinition map, secret scan, output forensics). Next: await GLM-5.3-Flash independent review, then compare findings in agents/DECISION.md.

---

# POST-REVIEW ADDENDUM — 2026-09-15 (after GLM-5.3-Flash's independent review)

Flash's review (APPROVE_WITH_CHANGES) challenged 5 claims. Every challenge was re-verified against the repository before acceptance — details and evidence in `agents/DECISION.md`. Corrections accepted into the record:

1. **D-1 — §7.3 over-claim.** Stored outputs prove ONLY banner Cells 1, 2, 2.1, 3, 5, 6 (physical 0,1,2,3,5,6) passed. Cell 4 has no stored output; my §2 "cells 0–6" is likewise imprecise. Cell 4's status in the last saved session: UNKNOWN.
2. **D-2 — P-2 second half downgraded to [HYPOTHESIS].** "The wrap wins in the owner's warm-kernel workflow" is undocumented (my own UNKNOWN #2/#3). Superseded by the three-scenario model (DECISION.md N-1).
3. **D-3 / F-1 — P-5 severity upgraded to High.** The effective box-snap variant is cell 12's (center-point-only, no border exclusion, no 4× area cap), not cell 11's guarded version my P-5 described. Blast radius larger; art-preservation risk highest in codebase.
4. **D-4 / F-6 — P-3 scope extended.** `recover_coordinates()` also resets `region_type` and clobbers manual corrections; call site is a print() f-string argument (cell 11:203).
5. **D-5 — §8.8 wording.** "Three ai.Text parsers" corrected to 2 parsers + 1 builder (cell 25's `build_ai_text_content` builds, does not parse).

Flash's new findings F-1..F-6 and test results T-1..T-8 were independently re-verified in this session; all confirmed (T-6 reproduced exactly on pandas 2.2.3). The comparison itself produced five new findings (N-1..N-5, recorded in DECISION.md), notably the three-scenario entrypoint model that resolves the latent P-1×P-2 tension present in BOTH reports.

No source code modified in this session. Comparison complete — see `agents/DECISION.md` (STATUS: REVIEW_COMPARISON_COMPLETE, awaiting owner decisions).
