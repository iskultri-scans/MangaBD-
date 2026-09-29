# GLM-5.3 — Lead Developer Log

## ROLE

Lead Developer / Software Architect

---

## CURRENT PHASE

MANGABD-003 — **PHASE C COMPLETE — implemented per Owner-approved Flash-amended scope; WIP commit on branch `mangabd-003-phase-c`, awaiting Phase E verification (Flash) via PM/Owner relay** (2026-09-29)

Task: MANGABD-003 Phase C — implement exactly the Owner-approved scope (relay: PM): Batch 1 = V-4a (metadata rev2) + V-2 (cell-6 vertical band) + V-1 (cells-11/12 CJK fallback incl. Flash amendments 1+2, mirror discipline); Batch 2 = V-3 Layer 1 (cell-7 rotated-only OCR candidates) + Layer 2 (cell-16 warning flag); Batch 3 = V-5 (provider registry + adapter + closure dispatcher + switch_translator + Control Studio + SECRET_SOURCES + translator_model). Phase D reconciliation folded in: every amended item re-confirmed against code with line citations before implementation (all CONFIRMED — no rebuttals; 3 factual precisions recorded, see T3.14). NO source changes beyond the enumerated scope. Full record: "# MANGABD-003 — PHASE C IMPLEMENTATION RECORD" below.

(Historical: MANGABD-002 — fresh-Colab execution reliability — **COMPLETE, Phase D verified, merged to main**, closed 2026-09-27; closure record below and in DECISION.md §B.13.)

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

## STATUS (MANGABD-001 — historical)

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

---
---

# MANGABD-002 — PHASE A INVESTIGATION REPORT (GLM-5.3)

## Fresh-Colab Execution Reliability

Date: 2026-09-15. Rules observed: TASK_002 Phase A — investigation and proposal only; no source code modified; evidence labels used throughout; no assumption that the MANGABD-001 findings are complete or single-caused.

---

## T2.0 Method and Evidence Base

This investigation did NOT rely on the MANGABD-001 audit text. It re-derived the execution behavior from the current repository using two purpose-built, read-only analyses plus targeted manual reads:

- **E1 [TEST RESULT] — Fresh-kernel static simulator** (`fresh_run_sim.py`, `fresh_run_sim2.py`, kept out of the repo in the analysis workspace): AST-level replay of cells 0→26 in sequential order, tracking the module-level namespace exactly as a fresh kernel builds it. For every module-level statement it records definitions (assign/def/class/import/for/with/`globals()[k]=v`/delete), evaluates simple guards (`not globals().get("X")`, `"X" in globals()`, `getattr(obj,"X",False)`, tracked constants), and checks every `Name` load in executed expressions. For every module-level call to a user-defined function it resolves the callee to the binding that exists at that moment and performs a **transitive interprocedural free-name check** (callee → called user functions → …, latest-binding rule, depth 12). Known analyzer limitation: it models name resolution, not value-dependent behavior; guarded (`try/except`) sites are classified non-aborting.
- **E2 [TEST RESULT] — Runtime reproduction** (`fresh_repro.py`): executes the REAL verbatim source of physical cells 13 and 14 (extracted from the notebook, unmodified) inside a controlled namespace that reproduces the fresh-kernel state at that point: empty `MANGABD_MANIFEST` with `"pages": {}` (structure verified from `create_empty_manifest`, cell 3:251–261), empty `translation_df` WITH all columns (verified from `empty_translation_df`, cell 3:833–834, and `TRANSLATION_DF_COLUMNS`, cell 3:123), artifact IO stubs returning None (fresh disk), and record-keeping stubs for the cell-11/12 quality helpers. Cell 15 names (`run_inpaint_all`, `run_render_all`) are ABSENT — exactly the fresh state. Four scenarios: fresh+warm × current+guarded.
- **E3 [FACT] — Manual reads**: cells 3 (state init), 11–15, 19–26 read line-by-line this session; banner placement comments verified; `save_translation_artifact`/`apply_manual_translation` located (both cell 8); cell 24 imports and proof-block `try/except Exception` verified; cell 25 imports verified.

Analyzer false-positives found and eliminated during development (documented for reproducibility): (a) `_D` flagged as missing in cell 26's transitive closure — actually a function-local `from PIL import ImageDraw as _D` inside `_qc_render_vertical` (cell 12:118); fixed by counting in-function imports as bound; (b) cell 20's `applied = apply_translations_from_ai_file()` is an Assign-RHS call, initially outside the interprocedural check; fixed. One remaining cosmetic limitation: `__mbd_patched` is set as an ATTRIBUTE on the `colab_files` module object (cell 24:46), not a namespace name, so the simulator reports "never set" — the patch itself IS applied on fresh (guard `not getattr(colab_files,'__mbd_patched',False)` evaluates True).

---

## T2.1 The Execution Graph (as it exists in the current notebook)

### T2.1.1 Cell placement vs. intended order [FACT]

The banner comments inside the patch cells state their intended position: cell 11 line 3 — "Place: after Cell 10, before Cell 11. Delete all old FIX/QC cells."; cell 12 line 3 — "Place: after Cell 10, before Cell 11". The physical arrangement (patch cells 11–14 between renderer cell 10 and orchestrator cell 15) MATCHES this stated intent. Therefore the cell ORDER is intended; the anomaly is not placement but the **module-level pipeline call at the end of cell 14**, which cannot succeed in a fresh sequential run at this position and can only have been authored and tested inside a warm kernel.

### T2.1.2 Definition timeline and sequential winners [TEST RESULT, E1]

| Name | Definition sites (cell:line) | Sequential-final binding |
|---|---|---|
| `run_inpaint_render_all` | 11:190 (+globals 11:200), 12:155 (+162), 13:35 (+45), 15:678, 23:71 | **cell 23** (plain + `sync_translate_stage`) |
| `run_inpaint_all` | 15:634 only | cell 15 |
| `run_render_all` | 15:656 only | cell 15 |
| `kill_residual` | 11:99, 13:4, 14:4 (+globals 14:37) | **cell 14** (v3, pixel-level) |
| `apply_container_types` | 11:63, 12:44 | **cell 12** (unguarded snap) |
| `restore_boxes` | 11:121, 12:71 | **cell 12** |
| `mask_only_translated` | 11:88 only | cell 11 |
| `recover_coordinates` | 11:30 only | cell 11 |
| `render_bengali_text` | 10:552; wrappers 11:178 (+186), 12:143 (+151) | **cell 12 wrapper → cell 11 wrapper → cell 10 original** (stacked, see T2.1.4) |
| `translate_with_nllb` | 8, 19:93 | cell 19 |
| `sync_translate_stage` | 23:28 | cell 23 |
| `render_all_pages` | 10:982 | cell 10 |

Namespace growth (module-level names visible after each cell): 00:34 01:80 02:86 03:135 04:176 05:212 06:252 07:275 08:307 09:324 10:359 11:376 12:378 13:378 14:378 15:407 16:438 17:459 18:477 19:478 20:478 21:478 22:485 23:489 24:514 25:571 26:571. No `del` statements exist anywhere; names are never removed once defined.

### T2.1.3 Module-level execution map [TEST RESULT, E1]

Unguarded module-level calls to user functions, with callee resolution at call time:

| Site | Callee | Callee def | Direct missing names | Transitive missing | Fresh verdict |
|---|---|---|---|---|---|
| 0:283, 0:314, 0:354, 1:103, 1:424, 1:596/597, 3:992/993, 4:410/416, 25:261–273, 25:415 | env/config/storage/UI helpers | same/earlier cells | — | — | SAFE |
| **14:40** | `run_inpaint_render_all` | **cell 13** | **`run_inpaint_all`, `run_render_all`** | same | **ABORT — the only one** |
| 20:1 (Assign-RHS) | `apply_translations_from_ai_file` | cell 19 | — | — | SAFE (no export file → prints, returns 0) |
| 23:89 | `sync_translate_stage` | cell 23 | — | — | SAFE (empty df → warning, returns 0) |
| 26:1 | `render_all_pages` | cell 10 | — | — | SAFE (no eligible pages → returns []) |

Additional module-level side effects (non-call): font downloads in 11/12 (network, `try/except`-guarded), `colab_files.download` patch + slicer wrap in 24 (guards evaluated True on fresh → applied), UI construction in 25 (ipywidgets `display`), `recover_coordinates()` invoked as a `print()` f-string argument at 11:203 (fresh: empty df → returns 0, benign; warm re-run: reverts coordinates/region_type — MANGABD-001 P-3/F-6). The designed per-cell self-tests (cells 0, 1, 3–10, 15–18) run inside `try/except` pairs (full test / degraded fallback) and are non-aborting by construction; their failures are loud-by-design environment diagnostics, not order bugs.

### T2.1.4 Guard-flag state machine and stickiness [FACT]

On a fresh sequential run the four patch guards all evaluate "not yet applied" and their bodies execute: `_QC_FINAL_RENDER_PATCHED` set at 11:187, `_QC_RENDER_PATCHED` at 12:152, `_MBD_SLICED` at 24:122, `__mbd_patched` (module attribute) at 24:46. Because the two render patches use DIFFERENT flag names, they stack rather than replace (N-2 from MANGABD-001, now statically confirmed): after cell 12, `render_bengali_text` = cell-12 wrapper, whose `_qc_orig_render` = cell-11 wrapper, whose `_base_render` = cell-10 original.

**Stickiness (hidden state dependency):** in a warm kernel, re-running cell 11 or 12 AFTER their flags are set skips the wrapper re-application entirely — the guard bodies are dead on re-run. The wrapper functions themselves call `_qc_render_vertical` / helper names via global lookup at call time, so re-running a cell still rebinds the INNER helpers, but an EDITED WRAPPER CONDITION WOULD NEVER TAKE EFFECT in that session. Same pattern for `_MBD_SLICED` (slicer never re-wraps; only the `SLICE_MODE` global it reads can be flipped). This is a concrete "execution history changes behavior" mechanism (TASK_002 question 7).

### T2.1.5 Callee "hunger" of every `run_inpaint_render_all` variant [TEST RESULT, E1]

| Def site | Free names (globals needed at call time) |
|---|---|
| 11:190 | MANGABD_MANIFEST, apply_container_types, kill_residual, mask_only_translated, restore_boxes, **run_inpaint_all**, **run_render_all** |
| 12:155 | MANGABD_MANIFEST, apply_container_types, restore_boxes, **run_inpaint_all**, **run_render_all** |
| 13:35 | MANGABD_MANIFEST, apply_container_types, kill_residual, mask_only_translated, restore_boxes, **run_inpaint_all**, **run_render_all** |
| 15:678 | **run_inpaint_all**, **run_render_all** |
| 23:71 | **run_inpaint_all**, **run_render_all**, sync_translate_stage |

**Every variant requires `run_inpaint_all`/`run_render_all`, which are defined only in cell 15.** Therefore ANY module-level call to this name placed anywhere before cell 15 fails on a fresh kernel, regardless of which variant is bound. Cell 14 is such a call. This generalizes the root cause beyond "cell 13's wrap is hungry" — the position of the call relative to cell 15 is the invariant that matters.

---

## T2.2 The Fresh-Run Failure Path [TEST RESULT — statically AND runtime proven]

### T2.2.1 Static proof (E1)

Replaying cells 0→26 with the fresh-kernel simulator yields EXACTLY ONE abort-class finding in the entire notebook:

```
cell 14 line 40: call run_inpaint_render_all:
    callee-def-cell 13, callee-missing ['run_inpaint_all', 'run_render_all']
```

Every other unguarded module-level call (including transitive closure over the callee graph) resolves cleanly. Therefore: on a fresh Colab "Run All", cells 0–13 execute (with their designed self-tests and patch side effects), the run **aborts at physical cell 14, line 40**, and cells 15–26 never execute in that pass. This also means everything after cell 14 has NEVER been exercised in a fresh sequential run — the stored outputs (physical 0,1,2,3,5,6 only) are consistent with this: even the owner's own saved session never went past the early cells.

### T2.2.2 Runtime reproduction (E2) — verdict matrix

Executing the verbatim cell 13 + cell 14 sources in the simulated kernel states:

| Scenario | Kernel | Cell-14 code | Result | Recorded calls |
|---|---|---|---|---|
| A | fresh (cell-15 names absent) | current | **`NameError: name 'run_inpaint_all' is not defined`, raised at cell_14.py line 40** | `apply_container_types` (returned 0, no-op) then crash |
| B | warm (cell-15 names present) | current | OK — **entire pipeline fires as a definition-cell side effect** | `apply_container_types`, `run_inpaint_all(force=True, require_translation=False)`, `run_render_all(force=True, require_translation=False)` |
| C | fresh | proposed guard | OK — clean skip with printed reason | none |
| D | warm | proposed guard | OK — **call sequence identical to B** (`calls_B == calls_D: True`) | same as B |

Two load-bearing observations from scenario A:

1. **The failure is a deferred NameError, not a missing callee.** The name `run_inpaint_render_all` EXISTS at cell 14:40 (bound by cell 13:45's `globals()` reassignment). The crash happens when the bound function's BODY resolves `run_inpaint_all` (cell 13, line 39) — a name that will only exist after cell 15. This is why the bug is invisible to naive "is the function defined?" reasoning and why it survives in the owner's workflow: in a warm kernel the body resolves fine.
2. **The pre-crash work on fresh is provably empty.** Before reaching the failing line, the wrap calls `apply_container_types()` — which iterates the empty `translation_df`, changes nothing, and re-saves the empty CSV (idempotent). The page loops see `MANGABD_MANIFEST["pages"] == {}`. Therefore skipping the call on fresh discards NO work — the guard in scenario C is outcome-neutral by construction, not by hope.

### T2.2.3 What happens after the abort (and after a fix)

In Colab, "Run All" stops at the first uncaught exception. With the current code the notebook's fresh-run state at termination is: cells 0–13 executed, `run_inpaint_render_all` bound to cell 13's wrap, `kill_residual` bound to v3, render patches stacked, orchestrator/UI/hotfix cells (15–26) never run. If the owner then runs the remaining cells manually, the binding of `run_inpaint_render_all` ends at cell 23's plain variant — the quality-core wrap is orphaned (MANGABD-001 P-2, scenario (b) of N-1). Any fix that unblocks fresh Run-All must therefore be evaluated against this semantic fork: fresh-run final binding = cell 23 plain; owner's warm re-apply workflow = whichever quality cell was re-run last. This fork is a pre-existing property of the codebase, NOT something the minimal fix introduces — but the proposal below documents it explicitly (see T2.6/T2.7).

---

## T2.3 Root Cause (three layers)

**Layer 1 — Immediate mechanism [FACT]:** physical cell 14, line 40, executes `run_inpaint_render_all(force=True)` at module level. At that point in a fresh sequential run the name is bound to cell 13's quality-core wrap, whose body references `run_inpaint_all` and `run_render_all` — defined only in physical cell 15 (lines 634, 656). Python resolves function-body globals at call time → `NameError` → Run All aborts. All five variants of the callee share this dependency (T2.1.5), so the failure is positional: any pre-cell-15 module-level call to this name fails on a fresh kernel.

**Layer 2 — Structural cause [FACT]:** the patch layer (cells 11–14, 19–26) follows a "define-and-immediately-apply" authoring pattern: each hotfix cell both (re)defines its functions AND executes pipeline work at module level to apply the fix right away (cell 14:40 pipeline run; cell 23:89 stage sync; cell 20:1 file import; cell 26:1 re-render; cell 11:203 coordinate recovery inside a print). This pattern is only sound in a WARM kernel where later cells have already run — i.e., the patch layer was authored against the owner's interactive workflow, never against a fresh sequential execution. The cell placement itself is intended (banner comments, T2.1.1); the immediate-execution statements are the anomaly.

**Layer 3 — Process cause [FACT]:** no fresh-run test has ever existed. The stored outputs prove the last saved session ran only early cells; execution counts were cleared; the artifact is a manual `.txt` snapshot of a `.ipynb`. The notebook's "known-good" state lives in warm Colab kernels, not in the repository, so a fresh-run regression could persist unnoticed across the entire patch-layer era.

---

## T2.4 Contributing Factors (complete, evidence-tagged)

1. **Five redefinitions of `run_inpaint_render_all`** (T2.1.2) — the pre-cell-15 bindings are the most name-hungry variants (7 free names), maximizing the chance that an early call fails. [FACT]
2. **Cell 13's wrap calls `run_inpaint_all` unconditionally** (line 39), before any page iteration or emptiness check — the NameError fires even on a zero-page session. A guard like `if MANGABD_MANIFEST["pages"]:` before the call would have made fresh runs accidentally survive. [FACT]
3. **The immediate-execution pattern** across patch cells (Layer 2) — cell 14 is the only instance whose dependencies are not yet defined on fresh; the others (20, 23, 26) happen to be fresh-safe by luck of placement, not by design. [FACT]
4. **Sticky patch guards** (`_QC_*`, `_MBD_SLICED`, `__mbd_patched`) make re-application semantics depend on session history (T2.1.4). [FACT]
5. **`globals()`-rebinding idiom** (`globals()["run_inpaint_render_all"] = ...`) at 11:200, 12:162, 13:45, 14:37 makes the binding timeline order-dependent and defeats static "def-before-use" intuition. [FACT]
6. **No execution-order documentation, no CI, no fresh-run smoke test** — the failure mode was structurally invisible to the owner's workflow. [FACT]
7. **Post-abort surface never exercised**: cells 15–26 have never run in a fresh sequence; their module-level code is statically safe (E1) but runtime-unproven on fresh (designed self-tests may legitimately fail on environment problems — network installs in cell 0/4, GPU availability). [FACT + UNKNOWN]

---

## T2.5 Answers to TASK_002's ten investigation questions

1. **Intended execution order** — physical order matches the banners' stated placement (patches between renderer and orchestrator); the intended RUN model is interactive/warm (evidenced by the define-and-apply pattern and by cell 14's call that can only work warm). [FACT + inference]
2. **Actual execution order (fresh Run All)** — cells 0–13, abort at 14:40. [TEST RESULT]
3. **All relevant definitions** — T2.1.2 timeline. [TEST RESULT]
4. **Redefinitions/overrides** — T2.1.2 winners column; render patches stack (T2.1.4). [TEST RESULT]
5. **Variables depending on earlier state** — `MANGABD_CONFIG` (progressive `setdefault` + patch overrides), `MANGABD_MANIFEST` / `translation_df` (loaded-from-disk vs fresh — including the MANGABD-001 P-7 dtype drift), `_qc_orig_render` / `_base_render` captured references, all guard flags. [FACT]
6. **Undefined in fresh runtime** — exactly `run_inpaint_all`, `run_render_all`, at exactly one site (14:40), via exactly one bound variant (cell 13). Complete by transitive closure over all module-level calls. [TEST RESULT]
7. **Execution history changes behavior** — yes: last-run binding wins; sticky guards; stacked patches; disk-loaded vs fresh state. [FACT]
8. **Run All vs manual reruns trigger different implementations** — yes: fresh Run-All (fixed) ends with cell-23 plain binding; warm re-run of 11–14 re-binds the quality wrap AND executes it; the UI button bypasses all variants (25:363–365). Same code, three pipelines. [FACT]
9. **Hidden state dependencies** — guard flags (incl. module-attribute flag `__mbd_patched`), `globals()` preference blocks (cell 10:150/156), kernel-global name leaks (e.g., `Path` used in cell 10 via cell 1's import). [FACT]
10. **Fixing one issue could create a regression elsewhere** — analyzed in T2.7 (main risks: newly-reachable cells 15–26 on fresh; preserved fresh-vs-warm semantic fork; guard-coupling staleness). [FACT + HYPOTHESIS where runtime-unproven]

---

## T2.6 Solution Design Space

Evaluated options (smallest-safe-first; TASK_002 constraints: no error-hiding, no unnecessary try/except, no dummy variables, preserve working functionality):

| # | Option | Verdict | Rationale |
|---|---|---|---|
| 0 | Do nothing / document only | REJECT | fails the task objective (fresh Run-All must work). |
| 1 | **Dependency guard around the 14:40 call** | **RECOMMENDED** | see T2.7. Fresh: skips provably-empty work, prints reason, Run-All proceeds. Warm: behavior byte-identical (E2 scenario D == B). 4-line diff, one cell. |
| 2 | Delete the 14:40 call outright | REJECT (as primary) | smaller diff than 1 but CHANGES warm-kernel behavior (re-running cell 14 would no longer re-apply the pipeline) — violates preservation without evidence the owner doesn't use that flow. |
| 3 | Move the call to a new end-of-notebook cell | REJECT (for 002) | behavior-equivalent to 2 in warm kernels unless the owner changes habits; moves code across cells (bigger diff); duplicates cell 26's intent. Revisit as structural follow-up. |
| 4 | Reorder cells (move 11–14 after 15) | REJECT | reshuffles every redefinition winner, invalidates the MANGABD-001 maps, contradicts the banners' stated intended placement, highest regression risk. |
| 5 | Early stub definitions of `run_inpaint_all`/`run_render_all` | REJECT | explicitly forbidden by TASK_002 (dummy variables); also silently changes fresh semantics. |
| 6 | Structural fix: single composition root / extracted package | DEFER | the correct end-state (already logged as DECISION.md Alternative B) but far beyond 002's minimal scope; blocked on owner decisions (canonical pipeline variant, DECISION.md Q1/Q2). |

---

## T2.7 RECOMMENDED PROPOSAL (for GLM-5.3-Flash to independently review)

### Proposed change — physical cell 14, line 40 only

Current (cell 14, lines 36–40):

```python
globals()["kill_residual"] = kill_residual
print("✅ kill_residual v3 active: pixel-level, box-only, face/border-safe")

run_inpaint_render_all(force=True)
```

Proposed:

```python
globals()["kill_residual"] = kill_residual
print("✅ kill_residual v3 active: pixel-level, box-only, face/border-safe")

# MANGABD-002: run_inpaint_render_all needs run_inpaint_all/run_render_all,
# which the orchestrator (Cell 11) defines LATER in a fresh Run All.
if ("run_inpaint_all" in globals()) and ("run_render_all" in globals()):
    run_inpaint_render_all(force=True)
else:
    print("  ⏭️ kill_residual v3 loaded; pipeline run skipped (orchestrator not loaded yet)")
```

### Why this is the smallest safe change

1. **One cell, one statement, +5/-1 lines.** No other cell's source changes; no definition moves; no binding timeline changes (the `def`s and `globals()` rebinds are untouched).
2. **Warm-kernel behavior is preserved exactly** — E2 scenario D reproduces scenario B's call sequence identically (`calls_B == calls_D: True`). The owner's interactive re-apply workflow is unaffected.
3. **Fresh-run skip is outcome-neutral by proof, not by hope** — E2 scenario A shows the pre-crash work on fresh is one no-op `apply_container_types()` call (empty DataFrame, zero pages, idempotent CSV re-save). Nothing of value is skipped.
4. **It does not hide the error — it declares the dependency.** This is not a `try/except` and not a silent fallback: the guard makes the cell's dependency on the orchestrator explicit in code, and the else-branch prints a visible, greppable reason. The forbidden patterns in TASK_002 (unnecessary try/except, silent fallback, dummy variables, global hacks) are all avoided.
5. **No other module-level call needs the same treatment** — cells 20/23/26 are fresh-safe by construction (E1 transitive closure + E3 manual reads: no-file → return 0; empty df → return 0; no eligible pages → return []). Adding guards there would be unnecessary change, which TASK_002 forbids.

### What this fix deliberately does NOT change (and why)

- **The fresh-vs-warm pipeline fork remains.** After a fresh Run-All, `run_inpaint_render_all` ends bound to cell 23's plain variant; the owner's warm re-apply still re-binds the quality wrap. WHICH variant should be canonical is DECISION.md Owner Question 2 — explicitly out of scope for MANGABD-002. The fix makes the notebook's fresh behavior deterministic and documented; it does not silently pick a winner.
- **The warm-kernel destructive scenario N-1(c) remains.** Re-running cell 14 in a warm kernel with pages loaded still fires force-inpaint + irreversible mask shrink. That is a separate defect class (artifact mutation safety, DECISION.md proposals 2–3) and must not be smuggled into a reliability fix.
- **The sticky guards, stacked render patches, and redefinition jungle remain.** All documented (T2.1.4, T2.4); all deferred to the structural phase pending owner decisions.

### Implementation notes (Phase C, only after approval)

- The notebook is stored as `MangaBD_V12_ipynb_txt.ipynb (3).txt` (JSON with a `.txt` extension). The edit must be applied to `cells[14].source` in the JSON programmatically, then verified: JSON re-parse OK, 27 cells unchanged in count, AST re-parse of cell 14 OK, `git diff` shows exactly one hunk in one file.

---

## T2.8 Regression Risk Analysis (for the proposed guard)

| # | Risk | Likelihood | Impact | Mitigation / note |
|---|---|---|---|---|
| R1 | Cells 15–26 module-level code runs fresh for the first time; a latent runtime failure there becomes the new first-stop | Medium | Medium | E1 proves name-resolution safety for ALL of them; remaining risks are environmental (cell 0/4 network installs, GPU presence) and the designed self-tests, which fail LOUDLY by design — that is correct behavior, not a regression of this fix. Documented expectation-setting for the owner. |
| R2 | Fresh Run-All leaves the plain (cell 23) pipeline bound; owner expects quality-core | Low | Medium | Pre-existing fork (T2.2.3), not introduced by the fix; flagged as DECISION.md Q2. The fix's printed skip message makes the fresh path visible in logs. |
| R3 | Guard-coupling staleness: if a future edit changes which `run_inpaint_render_all` variant is bound at cell 14, the guard's name set may no longer match its true dependencies | Low | Low | All five current variants need exactly these two names (T2.1.5), so the guard is complete today; the code comment states the dependency; hunger table in this report gives reviewers the check procedure. |
| R4 | A future rename of `run_inpaint_all` would turn a hard crash into a printed skip (error softening) | Low | Low | The else-branch prints loudly; a rename is a code-change event that goes through review anyway. |
| R5 | Notebook JSON edit corrupts the artifact | Low | High | Phase C protocol: programmatic edit + JSON re-parse + AST re-validation + single-hunk diff + Flash review (T2.9). |
| R6 | Owner's warm workflow silently diverges from fresh (fix works warm, but owner never notices fresh is now different) | Medium | Low | Intended outcome of the task (deterministic fresh behavior); documented here and in DECISION.md. |

---

## T2.9 Verification Plan (Phase D — for GLM-5.3-Flash)

1. **Static re-check**: re-run the fresh-kernel simulator against the edited notebook → abort-count must be 0; definition timeline unchanged except cell 14's source.
2. **Diff audit**: `git diff` shows exactly one hunk in `MangaBD_V12_ipynb_txt.ipynb (3).txt`; no other file changed; JSON parses; 27 cells; cell 14 AST-parses; the two `def`s and `globals()` rebinds in cells 13/14 byte-identical.
3. **Guard-logic equivalence**: re-run the four-scenario runtime reproduction (E2) with the edited cell 14 → A-variant becomes OK-with-skip, B/D sequences still identical.
4. **Colab run (strongest practical test, requires owner or a Colab-capable environment)**: fresh runtime → Run All → expect: no NameError; visible skip line after "kill_residual v3 active"; all self-test banners print; notebook runs to the end (environment permitting). Then upload one page via the UI and run Detect+OCR to confirm the pipeline still executes normally (the guard must NOT have disabled anything in the warm path).
5. **Limitation to document if Colab is unavailable**: static + local-runtime evidence only (as in this Phase A); full fresh-runtime confirmation deferred.

---

## T2.10 Open Questions / Owner Inputs Needed

1. Does the owner ever rely on "fresh Run All" as their canonical workflow (vs. interactive warm-kernel use)? Affects how much weight R2 carries. [UNKNOWN]
2. DECISION.md Q1/Q2 (canonical execution order; which pipeline variant is canonical) — still unanswered; they gate the structural follow-up but NOT this minimal fix. [UNKNOWN]
3. Was the cell-14 immediate-execution call ever intentionally used as "re-apply quality core" in the owner's workflow? (Its existence implies yes; the fix preserves it either way.) [UNKNOWN]

---

## T2.11 Phase A Status

INVESTIGATION COMPLETE. Proposal (T2.7) ready for GLM-5.3-Flash's independent review. No source code modified. Analysis artifacts (simulator + reproduction scripts) kept in the analysis workspace, outside the repository, and described in T2.0 for reproducibility.

---

## STATUS

MANGABD-002 PHASE A COMPLETE — investigation + proposal documented in this file (sections T2.0–T2.11).

MANGABD-002 PHASE B COMPLETE — second-pass review of GLM-5.3-Flash's investigation + review (agents/GLM_5_3_FLASH.md §F2.0–F2.7) performed; all four challenges C-1..C-4 independently verified against the repository and UPHELD (T2.12 below); final engineering proposal written to agents/DECISION.md (§B.6).

MANGABD-002 **COMPLETE — Phase D APPROVED and merged to main.** Owner approval received (§B.6 guard + bundled §B.11.2 cell-26 `force=False`); both edits applied programmatically to `MangaBD_V12_ipynb_txt.ipynb (3).txt` (T2.13 below). Verification: 29/29 checks PASS (GLM-5.3) + 5/5 steps PASS (GLM-5.3-Flash Phase D, fresh clone, commit `e9802fb`). Final history: WIP `829c383` amended → `f7eb7e6` (final message; tree identical), Flash's `e9802fb` replayed → `05d9bc6` (tree/author/message preserved), fast-forward merged to `main`, pushed. Trees verified identical by empty diff before any force-push.

**No source code was modified during MANGABD-001 or MANGABD-002 Phases A/B/D (agent docs only, as permitted). Phase C modified the notebook exactly once — the two Owner-approved hunks (T2.13), now merged to main and closed (DECISION.md §B.13).**

---

# MANGABD-002 — PHASE B SECOND-PASS ADDENDUM (GLM-5.3)

Date: 2026-09-16. Inputs: my Phase A report (T2.0–T2.11), Flash's independent investigation + review of my proposal (F2.0–F2.7, verdict APPROVE_WITH_CORRECTED_JUSTIFICATION, challenges C-1..C-4), and the actual repository. Per protocol, no challenge was accepted on authority — each was re-verified against the code in a fresh session, and the decisive one was re-reproduced at runtime. Full merged record: agents/DECISION.md §B.1–B.12.

## T2.12 Second-Pass Findings

### T2.12.1 Adjudication of Flash's four challenges

| ID | Verification performed this session | Verdict |
|---|---|---|
| **C-1** ("pre-crash work provably empty" is false on Drive-persisted state) | Five-component code chain line-pinned: cell 1:80–94 (active Drive-mount request + Drive preference over local fallback) → cell 3:992–993 (module-level `load_manifest()`/`load_translation_df()`) → cell 13:36 (`apply_container_types()`) → cell 13:37–38 (per-page `mask_only_translated()`) → cell 13:39 (crash line). Mutation carriers: cell 12:57–66 (coordinate snap + `region_type="narrator"` + unconditional `save_translation_df()` at 12:66), cell 11:91–96 (mask `cv2.bitwise_and` + `save_image_artifact` at 11:96). Then **my own runtime reproduction** (`scripts/fresh_repro_drive.py`, workspace): verbatim cells 13+14 + verbatim AST-extracted cell-11/12 helper defs, real cv2/numpy/pandas, in-memory Drive-state artifact store (1 page, 2 rows, real images/masks). DR-A (fresh+Drive+current): row coords snapped (55,65,110,70)→(52,62,116,76), region_type bubble→narrator, CSV rewritten, mask AND-shrunk 13,800→9,600 px, THEN NameError at cell_14.py:40→cell_13.py:39. DR-C (fresh+Drive+guarded): ZERO mutations, clean skip. DR-B==DR-D (warm preserved). ED-A/ED-C reproduce Phase A's empty-disk matrix. | **UPHELD.** My T2.2.2 observation 2 / T2.7 point 3 were over-generalized — proven only for empty disk, and my E2 could not have seen the Drive case because it stubbed the quality helpers. Correction accepted on my own evidence, not Flash's authority. The correction STRENGTHENS the guard (DR-C prevents corruption rather than skipping no-ops). |
| **C-2** (R1 omitted the "post-fix fresh Run All does real work" dimension) | Verified: cell 20:1 `apply_translations_from_ai_file()`, cell 23:89 `sync_translate_stage()`, cell 26:1 `render_all_pages(force=True)` (forced full re-render). | **UPHELD.** Folded into amended R1 and the owner-facing disclosure (DECISION §B.6). |
| **C-3** ("cell order is intended" rests on 11/12 banners only) | Verified: `Place:` banners at 11:3 and 12:3 only; cells 13:1/14:1 carry title-only banners. | **UPHELD.** T2.1.1's scope narrowed to the patch layer; cells 13/14 read as patch-session scratch cells. Root cause/fix unaffected. |
| **C-4** (guard comment used old "Cell 11" numbering) | Verified in my own T2.7 text. | **UPHELD.** Comment corrected (physical cell 15 + banner numbering noted); corrected wording already executed in DR-C/DR-D. |

Also found in Flash's review, one wording nit that changes no conclusion: F2.5.3 lists `sync_translate_stage` as "defined by cells ≤13" (it is cell 23:28). Guard sufficiency still holds because the only variant needing it (23:71) can only bind after 23:28 executes in the same cell, and no `del` exists anywhere.

### T2.12.2 Corrections to my Phase A report

1. **T2.2.2 observation 2 and T2.7 point 3 — RETRACTED as universal claims.** "Pre-crash work is provably empty / outcome-neutral by construction" holds ONLY for the empty-disk state. On Drive-persisted state the pre-crash work is destructive and persisted (T2.12.1 DR-A). The guard's justification is upgraded, not weakened: it prevents artifact corruption in the realistic Drive scenario.
2. **T2.4 factor 2 — wording corrected.** Cell 13's wrap calls `run_inpaint_all` (13:39) unguarded and before the kill/restore loop, but NOT "before any page iteration": the `mask_only_translated` loop (13:37–38) precedes it. (My own T2.2.2 obs. 2 already acknowledged "the page loops" — the Phase A text was internally inconsistent; the Drive dimension makes the inconsistency material.)
3. **T2.1.1 — scope narrowed** per C-3.
4. **T2.7's warm-preservation claim — sub-case precision added.** Warm re-apply has two sub-cases (re-run 13→14 fires the quality wrap; re-run 14 alone in a fully-warm kernel fires the last-bound variant, normally cell 23's plain). The guard is variant-agnostic (all five variants need exactly the two checked names — T2.1.5), so it is correct under both.

### T2.12.3 New observations (in neither agent's prior report)

1. **The guard idiom is native to the codebase:** cell 25's UI handler (25:363–366) already gates the same names with `if "run_inpaint_all" in globals() and "run_render_all" in globals(): … elif "run_inpaint_render_all" in globals(): …`. The fix adopts the notebook's own established pattern.
2. **Even empty-disk fresh writes once:** the unconditional `save_translation_df()` at 12:66 — idempotent empty-CSV rewrite on empty disk (Phase A noted this), mutation-carrier on Drive.
3. **`require_translation` divergence verified at the signature level:** 15:678 defaults `True`; 11:190/12:155/13:35/23:71 default `False` — "name exists" ≠ "behavior preserved" (supports Layer-2 root cause and the option-3 rejection).

### T2.12.4 Final proposal (unchanged executable code; C-4-corrected comment)

See DECISION.md §B.6 for the final patch text and the corrected five-point justification. The guard condition, call, and else-branch are byte-identical to my Phase A T2.7 proposal; only the comment changed (physical numbering). Regression register R1 amended (C-2), R2–R6 unchanged; residual-risk note added (warm-path N-1(c) and Drive-fresh mutation class remain, by scope decision). Verification strategy (DECISION §B.10) now includes the six-scenario Drive-state matrix as the Phase D baseline.

### T2.12.5 Phase B status

COMPLETE. DECISION.md carries the full merged record (§B.1–B.12), decision status **WAITING_FOR_USER**. Awaiting Project Owner approval of the §B.6 patch (and optional inputs §B.11.2–B.11.4: cell-26 force question, Drive usage, workflow questions) before any Phase C implementation.

---

# MANGABD-002 — PHASE C IMPLEMENTATION RECORD (GLM-5.3)

Date: 2026-09-27. Authorization: Project Owner approval (relayed via PM) of **exactly two edits in one file** — (1) DECISION.md §B.6: Cell 14 dependency guard, verbatim, C-4-corrected comment; (2) the bundled §B.11.2 Cell 26 change: `render_all_pages(force=False)`, semantics pre-verified by the PM against render_page/render_all_pages cache logic in physical cell 10. Per the relayed protocol: no other cell, no refactor, no try/except, no dummy variables, no def/globals() rebind change, **no commit / no push** (Phase D gated).

## T2.13.1 What changed

| # | Location (notebook JSON) | Before | After |
|---|---|---|---|
| EDIT 1 | `cells[14].source`, line 40 (last of 40) | `run_inpaint_render_all(force=True)` | 7-line §B.6 block: 3-line MANGABD-002 comment (physical cell 15; banner "Cell 11" noted) + `if ("run_inpaint_all" in globals()) and ("run_render_all" in globals()):` → `run_inpaint_render_all(force=True)`; `else:` → `print("  ⏭️ kill_residual v3 loaded; pipeline run skipped (orchestrator not loaded yet)")`. Cell 14: 40 → 46 source lines. |
| EDIT 2 | `cells[26].source` (entire, 1 line) | `render_all_pages(force=True)   # শুধু render আবার (inpaint লাগবে না)` | 4-line Bengali MANGABD-002 comment (resume-aware rationale + force escape hatches) + `render_all_pages(force=False)`. Cell 26: 1 → 5 source lines. |

**Method (script: `scripts/phase_c_apply.py`, workspace):** `json.load` → assert hard preconditions on both targets → mutate `cells[14].source[39]` and `cells[26].source` → write `json.dumps(nb, indent=2, ensure_ascii=False)` with no trailing newline.

**Serializer safety (decisive):** before any mutation, a round-trip assertion proved that this exact dump recipe reproduces the pre-edit file **byte-identically** (803,682 bytes; sha256 `1fee5e7c…`). Post-edit: 804,601 bytes (sha256 `448540f8…`), +919 bytes, git numstat **+12/−2** lines — the byte delta is provably confined to the two edited regions.

**NOT done (scope discipline):** cells 0–13 and 15–25 byte-identical (full-sweep verified); no refactor; no try/except; no dummy variables; no def/globals() rebind changes; no key/metadata changes in either cell object; no commit, no push.

## T2.13.2 Verification checklist outputs (DECISION §B.9, extended for 2 hunks) — 29/29 PASS

```
PASS | JSON re-parses after edit | 804601 bytes
PASS | cell count still exactly 27 | count=27
PASS | all cells still cell_type=code
PASS | cell 14/26 keys unchanged (no key added/removed)
PASS | cells[14] source AST-parses | 46 lines
PASS | cells[26] source AST-parses | 5 lines
PASS | BONUS: all 27 cells AST-parse (R5 hardening)
PASS | cell 13 source byte-identical to pre-edit
PASS | cell 14: lines 1-39 byte-identical (only line 40 replaced)
PASS | cell 14: pre-edit line 40 was exactly the module-level call
PASS | cell 14: new content is exactly lines 40-46 = §B.6 guard block
PASS | cell 13 def/globals()-rebind statements byte-identical
PASS | cell 14 def/globals()-rebind statements byte-identical | 2 statements compared
PASS | BONUS: all 25 non-edited cells byte-identical (full sweep) | cells 0-13, 15-25 identical
PASS | cell 26 text is exactly the approved 5-line block
PASS | cell 26 has exactly ONE statement (the call) | 1 top-level statement(s)
PASS | cell 26 statement is render_all_pages(force=False)
PASS | cell 26 token stream: 4 comment lines, no other statements
PASS | cite intact: cell 10:790 def render_page(page_id, force=False)
PASS | cite intact: cell 10:803 cache check (is_stage_done and not force)
PASS | cite intact: cell 10:804 final.jpg artifact load
PASS | cite intact: cell 10:982 def render_all_pages(force=False, require_translation=True)
PASS | cite intact: cell 10:1024 per-page force pass-through
PASS | cite intact: cell 25:365 UI force path run_render_all(force=True, require_translation=False)
PASS | cite intact: cell 15:656 def run_render_all (UI force target)
PASS | git diff (notebook): EXACTLY TWO HUNKS | found 2 hunk(s)
PASS | no other file changed (source scope; agent docs updated separately per protocol) | modified: ['MangaBD_V12_ipynb_txt.ipynb (3).txt']
PASS | notebook diff = 12 insertions / 2 deletions (7+5 in, 1+1 out) | numstat: 12  2
PASS | file mode preserved 100644 | mode=0o644
TOTAL: 29 checks, 29 PASS, 0 FAIL
```

Log saved to workspace `phaseC/verification_log.txt`; full diff saved to `phaseC/notebook.diff`. Two measurement points, both recorded: (1) the scope check first ran BEFORE this doc update — strict snapshot: `modified: ['MangaBD_V12_ipynb_txt.ipynb (3).txt']`, 29/29 PASS; (2) after this doc update (the protocol-mandated non-source follow-up), the full checklist was re-run in the final state — 29/29 PASS with the scope invariant expressed precisely as "no file changed outside the approved scope (notebook + permitted agent-doc record)". Git status at completion: notebook + this file, both uncommitted, both mode 100644.

## T2.13.3 Semantic re-confirmation of EDIT 2 (independent re-verification, line cites from the post-edit file)

1. **Cache check — already-rendered pages become a no-op.** `render_page` (cell 10:790, `def render_page(page_id, force=False)`) gates on `if is_stage_done(page_id, "render") and not force:` (10:803), then `cached = load_image_artifact(page_id, "final")` (10:804); a non-None cached final returns immediately with "✅ Render cached" (10:806–808) — **no final.jpg overwrite, no GPU work**. With `force=False` at cell 26, every page whose render stage is done AND final.jpg exists is a cache hit.
2. **Resume-awareness — un-rendered / reset pages still render.** Pages with a missing render stage fail `is_stage_done` (10:803) and take the full render path; the checkpoint-without-file case (10:810–816) WARNs and calls `reset_page(page_id, from_stage="render")` (10:812–816) then falls through to re-render. `render_all_pages(force=False, require_translation=True)` (10:982) filters eligibility (inpaint stage 10:999–1000; translate stage 10:1002–1003 when required) and forwards force per page — `render_page(page_id, force=force)` (10:1024). `render_all_pages` is defined exactly once (cell 10) and never redefined (only wrapper `run_render_all`, cell 15:656, forwards `force`/`require_translation` verbatim at 15:669–672).
3. **Warm-caveat (intended, bounded behavior change).** A warm re-run of cell 26 no longer forces a full re-render; it now cache-hits. The force paths that remain: (a) Control Studio UI 🎨 button — `on_final` (cell 25:358) → same-idiom guard (25:363) → `run_render_all(force=True,require_translation=False)` (25:365) → `render_all_pages(force=True, …)` via 15:669–672 → `render_page(force=True)`; (b) explicit `render_all_pages(force=True)` (suggested by help text 16:1340; used inside the full-pipeline recipe function at 18:987, which is function-scoped, not module-level); (c) direct `run_render_all(force=True, …)` calls.
4. **Net delta of EDIT 2, precisely:** on Run All, already-rendered pages skip re-render (cache hit); every other page renders exactly as before. This discharges the R1(b) Run-All-time GPU-hours / artifact-overwrite disclosure for cell 26 per the Owner's decision — and is independent of EDIT 1's guard semantics.

## T2.13.4 Runtime re-verification against the EDITED file (not a hand-edited copy)

`scripts/phase_c_runtime_check.py` (workspace) loads cells 13/14 **verbatim from the edited notebook JSON** and executes them in simulated kernel states:

- **E (fresh + edited):** cell 14 executes OK — no NameError; stdout = `✅ kill_residual v3 active: …` followed by `  ⏭️ kill_residual v3 loaded; pipeline run skipped (orchestrator not loaded yet)`; **zero** pipeline calls recorded.
- **F (warm + edited):** pipeline fires exactly as pre-fix: `apply_container_types` → `run_inpaint_all(force=True, require_translation=False)` → `run_render_all(force=True, require_translation=False)`.
- **G (warm + PRE-EDIT cell 14 baseline):** call sequence **identical to F** — warm behavior preserved exactly.

RESULT: fresh-safe=True, warm-preserved=True. (Phase A/B reproductions E2/DR used a hand-substituted guard string; this run is the first against the edited artifact itself, closing that gap for Phase C. The Drive-state six-scenario matrix against the edited file remains Flash's Phase D item, DECISION §B.10.3.)

## T2.13.5 Phase C status

**PHASE C COMPLETE — PHASE D APPROVED — MERGED TO MAIN — TASK CLOSED.** Deliverables returned via Owner: (1) edited notebook file; (2) full git diff (+12/−2, exactly 2 hunks, 1 file, file mode 100644); (3) verification checklist outputs (29/29 PASS); (4) this record. **Phase D outcome:** GLM-5.3-Flash APPROVED (5/5 steps: diff/scope audit incl. mode-flip check, calibrated static re-check with 0 abort sites, 9/9 runtime guard-equivalence matrix incl. Drive state, 30/30 cell-26 citation checks, 25-cell byte-identity scope audit) — record at agents/GLM_5_3_FLASH.md §PD.0–PD.7, verification commit `e9802fb`. **Final merge (Owner-prescribed sequence):** WIP `829c383` reworded with the final message → `f7eb7e6` (tree identical; Flash's Phase D commit `e9802fb` replayed on top → `05d9bc6`, tree/author/message preserved; trees verified identical by empty diff before any push); branch force-pushed with lease; fast-forward merged to `main` (`aabc592 → 05d9bc6`); DECISION.md marked complete (`8deff7c`); review branch deleted. Merged notebook verified byte-identical to the Phase-C-verified artifact (blob `583fa89…`, file sha256 `448540f8…`). Deferred to the Owner's first Run All: §B.10.4 live Colab confirmation (T-8) and §B.10.5 warm-path UI functional check (per §B.10.6).

---

# MANGABD-003 — PHASE A INVESTIGATION & PROPOSALS (GLM-5.3)

## S001 Visual Evidence → Code-Actionable Defects (investigation only; NO source changes)

**Mandate:** Owner task relayed 2026-09-29. Input evidence: GLM-5.3-Flash's S001 visual review (agents/GLM_5_3_FLASH.md §"VISUAL REVIEW — S001_color_webtoon", commit `f7aabbc`, verdict APPROVE_WITH_ISSUES), the archived artifacts in `samples/S001_color_webtoon/`, and the current notebook (blob identical to the MANGABD-002-verified merge; cells re-extracted and verified against the Phase-C state — only cells 14/26 differ, exactly the two Phase-C edit sites).

**Owner binding policy decisions (recorded verbatim in DECISION.md §C.1):** (1) manual translation is permanent core workflow — improve, never remove; production auto-translation must be provider/model-flexible across OpenAI, Qwen, DeepSeek, Ollama, OpenRouter; NLLB is testing/experimental only, not canonical production. (2) metadata corrected to engine=nllb, source_type=B/W manga page; folder `S001_color_webtoon` NOT renamed — naming discrepancy documented in metadata/README.

Citations below use the project convention *physical-cell:line* against the current notebook (cell N = zero-based notebook cell index; extraction verified this session).

## V-1 — CJK Fallback Glyph Size/Weight (vertical T/L note)

### Evidence

- **[FACT]** The vertical-note render path is a 3-layer monkey-patch: cell 11 "QUALITY CORE FINAL" defines `_split_runs`/`get_font_fb`/`_qc_render_vertical` (11:138–174) and wraps `render_bengali_text` (11:176–187); cell 12 "QUALITY CORE (container-aware)" **redefines all three identically** (12:94–139) and wraps again (12:141–152). Cell 12 executes last, so the outermost wrapper uses the globals as last defined: the effective vertical renderer is **cell 12's** `_qc_render_vertical`, with cell 12's `get_font_fb`. The non-vertical path falls through to the cell-10 core `render_bengali_text`.
- **[FACT]** `_main_font_ok` (12:89–92) classifies Bengali (0x0980–0x09FF), Latin (0x0000–0x00FF), and punctuation ranges as "main font"; **everything else — including kana/kanji — goes to the fallback font**. `_split_runs` (12:94–103) splits each line into main/fallback runs.
- **[FACT]** `get_font_fb(size, bold=False)` (12:106–112) accepts `bold` but **never uses it**: it loads `MANGABD_CONFIG["rendering"]["font_fallback"]` at `int(size)` unconditionally. The fallback font is `NotoSansJP[wght].ttf` — a **variable font** downloaded to `NotoSansJP.ttf` (12:19–23). PIL's `ImageFont.truetype` loads a variable font at its **default instance (wght=400, Regular)**; no `set_variation_by_axes` call exists anywhere in the notebook (grep: 0 hits).
- **[FACT]** The main font pair is NotoSansBengali-Regular/Bold static hinted TTFs (cell 4:398–408; variable font is only the 3rd URL fallback). `fit_font_size` (10:365–443) measures and calibrates the font size **using only the main font** (`get_font(mid, bold)` 10:415, `split_text_to_lines` 10:416, `measure_text` 10:424) — fallback runs then render at that same pixel size with **no compensation** (12:129, 12:133).
- **[FACT]** `_qc_render_vertical` draws every run with `draw.text(..., fill=text_color+(255,))` — **no `stroke_width` on any run** (12:134), even though the core path gives overlay regions `stroke_width=1` (10:74 `stroke_width_overlay`, 10:578–579, 10:523). So the vertical path renders BOTH scripts lighter than the core path would.
- **[TEST RESULT — Flash, pixel-measured]** Region 1 CJK runs (こがねい / おたるみ / しゅ) render at ~50% of Bengali visual height, mean ink luminance ≈90 (pale gray) vs Bengali near-black; the ORIGINAL note's glyphs measured 47.5. Rendering used bold=False (wrapper 12:147: overlay not in ["sfx","narrator"]).

### Root cause (two independent components)

1. **Size:** at equal em size, NotoSansBengali glyph ink (conjunct stacks) fills ~70–80% of the em, while NotoSansJP kana ink fills ~50–55% (kana are lowercase-height glyphs). `fit_font_size` calibrates to the Bengali metrics, so CJK runs inherit a size one visual-step smaller. Flash's "~50%" measurement matches this metric gap.
2. **Weight/paleness:** the JP variable font renders at default wght=400 with thinner hairline strokes than NotoSansBengali Regular at the same size; anti-aliased ~1px strokes average to mid-gray (luminance ≈90). `get_font_fb`'s ignored `bold` parameter and the missing `stroke_width` on fallback runs leave no mechanism to compensate.

### Proposed minimal change (Phase C candidate — 2 functions, mirrored in cells 11 AND 12 so the shadowed copy cannot resurface)

**Edit 1 — `get_font_fb` (cell 11:149–155 and cell 12:106–112, identical text):** honor bold and the variable-font weight axis, with config knobs and hard failure fallback:

```python
_FB_CACHE = {}
def get_font_fb(size, bold=False):
    key = (int(size), bool(bold))
    if key in _FB_CACHE: return _FB_CACHE[key]
    try:
        f = ImageFont.truetype(MANGABD_CONFIG["rendering"]["font_fallback"], int(size))
        # MANGABD-003 V-1: match Bengali visual weight (variable font default is wght=400)
        wght = int(MANGABD_CONFIG["rendering"].get(
            "fallback_font_wght", 700 if bold else 600))
        try:
            f.set_variation_by_axes([wght])          # no-op on static fonts / old Pillow
        except Exception:
            pass                                      # stroke fallback below compensates
    except Exception:
        f = get_font(size, bold)
    _FB_CACHE[key] = f
    return f
```

**Edit 2 — `_qc_render_vertical` CJK draw calls (cells 11:164–171 and 12:126–134):** scale fallback runs and add a matched stroke. Replace the two `f = get_font(size, bold) if im else get_font_fb(size, bold)` sites' fallback branch and the draw call:

```python
        _fb_scale = float(MANGABD_CONFIG["rendering"].get("fallback_cjk_scale", 1.25))
        _fb_stroke = int(MANGABD_CONFIG["rendering"].get("fallback_cjk_stroke", 1))
        for t2, im in runs:
            f = get_font(size, bold) if im else get_font_fb(int(size * _fb_scale), bold)
            widths.append(draw.textlength(t2, font=f)); total += widths[-1]
        ...
        for (t2, im), ww in zip(runs, widths):
            f = get_font(size, bold) if im else get_font_fb(int(size * _fb_scale), bold)
            sw = 0 if im else _fb_stroke
            draw.text((lx, ly), t2, font=f, fill=text_color+(255,),
                      stroke_width=sw, stroke_fill=text_color+(255,)); lx += ww
```

Plus two config setdefaults next to the existing `font_fallback` (11:26–27 / 12:26–27): `fallback_font_wght=600`, `fallback_cjk_scale=1.25`, `fallback_cjk_stroke=1`.

### Regression risk — LOW

- The scale/stroke apply **only to fallback (CJK) runs inside vertical notes** — the horizontal core path, all Bengali runs, and the wrap logic are untouched. Run widths are measured per-run with the actual font used, so centering (`lx = (int(h)-total)//2`) self-adjusts (12:131).
- Vertical fit: CJK ink at 1.25× em ≈ 65–70% em, still under the line height (1.18× em from the main font, 12:121) — no line overlap.
- `set_variation_by_axes` is wrapped in try/except (static font or old Pillow → no-op; stroke then carries the weight). Calibrated against Flash's measurements: 1.25× addresses the ~50% ink-height gap; wght 600 + stroke 1 addresses the ≈90 vs ≈47.5 luminance gap. Both knobs are CONFIG-tunable for S002 calibration without further code edits.
- Known non-goal: the variable-font default instance also means bold CJK currently cannot exist; Edit 1 fixes that too (wght 700 when bold).

## V-2 — 11-px Mask-Miss Residue at Region 1 Bottom

### Evidence

- **[TEST RESULT — Flash]** 11 dark residue specks (luminance 18–24) at x=34–47, y=370–381 in final.jpg — mask-missed glyph tips of the vertical note's bottom glyphs; true ink bottom ≈ y=384 while the detection quad bottom is y=379 (box 10,81,61×298, detections.json).
- **[FACT]** Mask build (cell 6, `detect_page` → `build_page_text_mask` 6:769–834): CTD raw confidence map → threshold 55 (6:792; set to 55 by 11:11/12:11) → MORPH_CLOSE 5×5 ×2 (6:796–806) → `clean_binary_mask` min_area=3 (6:808) → `adaptive_dilate_mask` (6:813) with **base radius 5** (6:716–742; cells 11/12 set 5, adaptive cap 15 from stroke width) → clip to region boxes +10 (6:815–826). Saved as the `mask` artifact (6:1214).
- **[FACT]** Inpaint prepare (cell 9 `prepare_mask_for_inpaint` 9:268–312): cleans (9:294–300, close 3×3 + drop components <3 px), does **NOT** re-dilate artifact masks (9:302–303, `redilate_artifact_mask=False`), clips again to boxes+10 (9:305–309, `mask_clip_padding=10`). LaMa then consumes this mask. Cell 9 therefore faithfully preserves whatever cell 6 produced — the miss originates upstream.
- **[FACT]** The glyph tips are dark ink (lum 18) but outside the CTD **confidence** map's flagged region; +5 px dilation from the last covered row (~y≈368–370) reaches only ~y≈373–375, leaving y≈375–381 uncovered inside the box and y=380–384 outside it.
- **[FACT]** The residue-sweep safety nets are **dead code in the effective fresh-run path**: `kill_residual` is defined three times (cell 11:99–118 mask-based dilate=13; cell 13:4–32 same; cell 14:4–35 "v3" pixel-level), and `run_inpaint_render_all` is defined five times (cells 11, 12, 13, 15, 23) — the last two definitions are **plain** `run_inpaint_all + run_render_all` with no cleanup (15:678–691, 23:71–84). The Control Studio 🎨 button (25:358–370) calls `run_inpaint_all`/`run_render_all` directly. So in the S001 fresh Run All, **no residue sweep, no box restore, and no mask-filtering ran at all**. (This was already flagged as the "orphaned quality-core" hazard in the MANGABD-001 review; S001 is the first archived confirmation that a real defect slips through because of it.)
- **[FACT]** Even if cell 14's v3 sweep ran, region 1 would be skipped: its solid-box gate `uniform_frac > 0.8` (14:23) fails on a dense vertical text column; margin=5 (14:28–29) strips the bottom rows of the crop; and the crop is box-limited so y≥380 is out of reach. All three sweeps are structurally blind to this residue.

### Root cause

Under-coverage at the bottom of tall vertical-note columns: the CTD confidence map + 5 px adaptive dilation + the detection quad (bottom 379 < true ink 384) collectively miss the bottommost glyph tips; every later stage either preserves the mask faithfully (cell 9) or is unreachable (dead kill_residual chain).

### Proposed minimal change — config-gated vertical band extension in `build_page_text_mask` (cell 6, after the clip block at 6:822–825, before `return mask` at 6:827)

```python
        # MANGABD-003 V-2: vertical-note tip coverage — extend the mask a few px
        # along the column axis ONLY for tall-narrow regions (no global dilation).
        vpad = int(detection_cfg.get("mask_vpad_vertical", 10))
        if vpad > 0:
            for region in regions:
                rw, rh = int(region["width"]), int(region["height"])
                if rw < 90 and rh > 2 * max(1, rw):   # same predicate as the vertical renderer
                    x, y = int(region["x"]), int(region["y"])
                    cv2.rectangle(mask, (x, max(0, y - vpad)),
                                  (x + rw, min(h, y + vpad)), 255, -1)
                    cv2.rectangle(mask, (x, max(0, y + rh - vpad)),
                                  (x + rw, min(h, y + rh + vpad)), 255, -1)
```

with `MANGABD_CONFIG["detection"].setdefault("mask_vpad_vertical", 10)` (cell 6 config block). Justification for 10: Flash's residue spans y=370–381 vs box bottom 379 — the band [y+h−10, y+h+10] = [369, 389] covers every measured speck with 1–2 px margin; 10 also equals the existing clip padding (6:819, 9:236), so the band survives cell 9's re-clip exactly (y+h+10 ≤ clip bound).

### Regression risk — LOW, and specifically NOT the historical over-dilation class

- The extension is confined to the region's **own column width (x..x+rw)** and only along the column axis; only tall-narrow regions (the vertical-note predicate already used by the renderer, 12:146) are touched. Bubble masks — where the historical border-damage failures happened — are untouched (the predicate excludes them), and the global `mask_base_dilate_radius` stays 5.
- Region 1 specifics: column x=10..71; the panel border Flash measured at x≈75 is outside the x-range; the band re-inpaints ≤20 rows of a 298-row white column (≤7% of region area) that the renderer immediately overdraws.
- Worst case if a vertical note sits flush against artwork below: the band would inpaint ≤10 px of that artwork's top edge. Mitigation: `mask_vpad_vertical` is a single config knob (set 0 to disable, or 6 for conservative mode); S002 re-review will verify with the same pixel measurements Flash used on S001.
- Explicitly rejected alternatives: raising `mask_base_dilate_radius` globally (reintroduces the over-dilation failure class on every region); lowering `ctd_mask_threshold` (adds noise pixels page-wide with no geometric guarantee); re-enabling `redilate_artifact_mask` (same global-dilation class at the inpaint stage).

## V-3 — OCR Mis-transcription of the Vertical Mixed-Script Note

### Evidence

- **[TEST RESULT — Flash]** The original region-1 note reads "…while **Otearai** is spelt as **おてあらい** and both **"U"** is pronounce as **"I"** which is a vowel"; ocr.json/translation.json record "**Otarumi** … **おたるみ** … **しゅ … しゅ**" — two kana-romanization mis-transcriptions that propagated verbatim into the NLLB prompt and the rendered note.
- **[FACT]** ocr.json region 1: `confidence 0.95, status "ok", warnings []` — the engine was **confidently wrong**. Any confidence-gated QA (existing cell 16 thresholds: low 0.65 / critical 0.35, 16:270–282) cannot catch this failure.
- **[FACT]** `ocr_region` (7:324–427) crops with `crop_bubble_with_context(context_ratio=0.15)` (7:349–353) — region 1's `angle=0.0` (detections.json), so the rotated-crop branch (7:346–347, requires |angle|>5) never engages; the tall 61×298 strip is passed as-is to the VLM.
- **[FACT]** `preprocess_for_ocr` (7:208–313) upscales/denoises/CLAHE/pads — **no rotation for vertical text**; overlay regions get BORDER_REPLICATE padding (7:279–287).
- **[FACT]** The OCR prompt (7:75–85) is: "Extract all English text visible in this image exactly as written. Do not translate. …" — an English-only instruction with no vertical-text or mixed-script guidance, while the note is English + kana typeset vertically (rotated 90°).

### Root cause

A geometric/linguistic double mismatch: the VLM receives a rotated (vertical) mixed-script strip but is prompted for horizontal English-only extraction, and VLMs systematically garble rotated CJK (romanizing kana by shape-adjacency: おてあらい→おたるみ, quoted "U"/"I"→"しゅ"). The pipeline has no vertical-region special-casing at OCR time (even though the renderer already special-cases exactly these regions — same predicate 12:146).

### Proposed change — two independent layers (Owner offered either/or; both are small)

**Layer 1 (preprocess, primary) — dual-orientation OCR for tall-narrow regions** (cell 7, inside `ocr_region`, replacing 7:392–394):

```python
    # MANGABD-003 V-3: vertical notes — try both orientations, keep the better read
    rh, rw = preprocessed.shape[:2]
    is_vertical_note = rw < 90 and rh > 2 * max(1, rw)
    if is_vertical_note:
        rot_cw = cv2.rotate(preprocessed, cv2.ROTATE_90_CLOCKWISE)
        rot_ccw = cv2.rotate(preprocessed, cv2.ROTATE_90_COUNTERCLOCKWISE)
        results = []
        for cand in (preprocessed, rot_cw, rot_ccw):
            r = qwen.recognize(cand, prompt=prompt)
            score = float(r.get("confidence", 0.0)) + float(
                r.get("language_score", {}).get("en", 0.0))
            results.append((score, r))
        result = max(results, key=lambda t: t[0])[1]
    else:
        result = qwen.recognize(preprocessed, prompt=prompt)
```

Best-of-three by confidence + English score; the correct orientation of a vertical note reads horizontally after one of the two 90° rotations, and the wrong rotation degrades both metrics — the max is a robust selector. Prompt tweak (same edit): when `is_vertical_note`, swap in `MANGABD_CONFIG["ocr"]["vertical_prompt"]` — the default prompt plus "The text may contain Japanese kana mixed with English. Transcribe every character exactly as written; do not romanize kana."

**Layer 2 (QA safety net, per the Owner's explicit option) — mandatory manual-review flag in cell 16's `inspect_ocr_quality`** (insert after the short-text check, artifact branch ~16:365; mirror in the translation_df branch ~16:431):

```python
            # MANGABD-003 V-3: mixed-script vertical notes are misread-prone (S001 evidence)
            rw_, rh_ = int(region.get("width", 0)), int(region.get("height", 1))
            has_kana = bool(re.search(r"[\u3040-\u30FF\u3400-\u4DBF]", text))
            has_latin = bool(re.search(r"[A-Za-z]", text))
            if rw_ < 90 and rh_ > 2 * max(1, rw_) and has_kana and has_latin:
                issues.append(add_quality_issue(
                    page_id, region_id, "ocr",
                    "Vertical mixed-script note (kana + Latin) — OCR unreliable",
                    severity="warning",
                    suggestion="Mandatory manual verification of this OCR text",
                ))
```

(`re` is already imported in cell 16; severity "warning" auto-adds the region to `manual_review_flags` via 16:172–185.) Even if Layer 1's best-of-three still misreads, Layer 2 guarantees the region lands on the manual-review list — the S001 failure mode (confident 0.95, silent) becomes impossible to miss.

### Regression risk — LOW

- Layer 1 costs 2 extra VLM calls **only for tall-narrow regions** (typically 0–1 per page); same Qwen instance, no new dependency. Non-vertical regions take the identical single call path. Mis-selection risk: the wrong orientation scored higher — bounded by Layer 2's flag and by S002 re-review; the two metrics (confidence + en score) both degrade on rotated text, and S001's wrong-orientation baseline scored 0.95 only because NO rotation was offered.
- Layer 2 can only ADD a warning-severity flag; it cannot fail a page (score weight is the existing "warning" class) and fires only on the narrow geometry+script predicate. False positives (a correctly-read vertical note) cost one manual glance — intended per Owner policy (manual review is the core workflow).

## V-4 — Metadata Correction & Manual Workflow Improvement

### V-4a — Corrected `samples/S001_color_webtoon/metadata.json` (rev 2, exact proposed content)

- **[FACT]** Current metadata (rev 1, written verbatim per the Owner's instruction) says `translation_engine: "manual"` and `source_type: "color webtoon long strip"`.
- **[TEST RESULT — Flash, evidence-based]** engine is **nllb** (translation.json `translator_engine: "nllb"` on all 6 regions + 5 MT fingerprints: "যৌনসঙ্গম" for "fuck", "সে আমার ভিতরে ছিল" for "she was into me", "ভোকাল" for "vowel", "! !" / "! ?" tokenizer spacing, honorific-register errors); the page is **100% grayscale (0 chroma pixels)** — a B/W manga page, not a color webtoon.
- Flash's review also required that samples remain immutable evidence and the fix land as "a new metadata revision". The Owner's policy: correct the values, do NOT rename the folder. Proposal satisfies all three: **revise metadata.json in place to rev 2, preserve the original as `metadata.rev1.json`** (the pipeline artifacts — images and the three sidecars — remain byte-untouched):

```json
{
  "sample_id": "S001_color_webtoon",
  "captured_at": "2026-09-29",
  "notebook_commit": "9f4d82a",
  "pipeline_variant": "fresh Run All success (MANGABD-002 verified)",
  "source_type": "B/W manga page",
  "translation_engine": "nllb",
  "owner_notes": "first fresh-run success; second test image",
  "metadata_revision": 2,
  "revision_note": "rev2 (2026-09-29, MANGABD-003 Phase A): corrected translation_engine manual->nllb and source_type color webtoon long strip->B/W manga page per GLM-5.3-Flash visual review (commit f7aabbc); rev1 preserved verbatim in metadata.rev1.json",
  "naming_note": "Folder name S001_color_webtoon is pipeline-variant labeling from rev1 and is intentionally NOT renamed (Owner decision 2026-09-29); the actual content is a grayscale B/W manga page (0 chroma, Flash-measured)"
}
```

Also one line added to `samples/README.md`'s Contents table: "(S001's folder name is a rev1 pipeline-variant label retained by Owner decision; content is a B/W manga page — see its metadata.json naming_note.)"

**Risk — NONE** (documentation only; no code; evidence chain preserved via rev1 sidecar).

### V-4b — Manual translation workflow improvements (preserve the core loop)

**[FACT]** Current manual loop: `export_ai_text()` (8:870–973) writes `[page.jpg:1] English → Bengali` one line per region + JSON sidecar; the translator edits in any text editor (or the Control Studio COPY-PASTE textarea, 25:286–289); `parse_ai_text` (8:812–867) re-reads it with `rsplit("→", 1)` (8:855–857 — correctly tolerant of arrows inside the English side); `apply_translations_from_text` (22:185–264) adds a rescue for Bengali-pasted-before-the-arrow (22:230–233); `apply_manual_translation` (8:1023–1092) validates Bengali (8:1076) and stamps `translator_engine="manual"`. The UI (25:261–289) has load-original / paste / apply / file-upload buttons; cell 20/21 apply+display.

**[FACT]** Gaps found (all cheap to fix, none require touching the core loop):

1. **Silent line loss** — `parse_ai_text` skips any line that does not match `^\[page:id\]` (8:843–846) with no report; a translator's hard-wrapped line (mobile editors wrap long text with real newlines) is **silently dropped**, and a typo'd header loses that region's translation. This is the single biggest correctness risk in the manual path.
2. **No diff feedback on import** — the apply step reports only a count (22:257); nothing tells the translator WHICH regions are still missing before render.
3. **No context in the export** — one flat line per region: no region type, no confidence/low-confidence marker, no page-position hint, so the translator cannot triage (e.g. the S001-style vertical note that needs the most care).

**Proposed improvements (3 small edits, all preserving the format and loop):**

- **Edit A (validation, cell 8 `parse_ai_text`, ~8:843–846 + return):** count non-comment, non-empty lines that fail the header regex and return them in the dict under a `("_unparsed", 0)` sentinel key; `apply_translations_from_text` (22:235–238 print block) then prints them as `⚠️ N unparsed lines (check headers/line-wraps): <first 3 shown>`. Silently-lost translations become visible losses.
- **Edit B (coverage report, cell 22 after 22:257):** after apply, compute `missing = regions without valid Bengali` from `translation_df` and print `⚠️ M of T regions still untranslated — page:id list (first 10)` so the Owner knows whether pressing 🎨 is safe. (Data already in the df; 6 lines of code.)
- **Edit C (context, cell 8 `export_ai_text`, ~8:941):** change the line prefix to `[page:id|TYPE] ` (e.g. `[02.jpg:1|overlay]`) **keeping the arrow suffix identical**; extend the header comment (8:907–913) to document it; `parse_ai_text` regex becomes `^\[([^:\]|]+):(\d+)(?:\|([a-z_]+))?\]` — old headerless files still parse (the `|TYPE` group is optional), so **old exports remain valid inputs**. Region type already exists per row (8:949 records include it). Translators can now see which lines are overlays/vertical notes.

**Rejected (scope discipline):** per-region crop thumbnails in the export (would change the file format materially), inline editor widgets in the UI (Colab-textarea instability; the paste box already works on mobile), and auto-translation pre-fill of the manual export (Owner keeps manual pure; can be done by choice via the NLLB button then exporting).

**Regression risk — LOW.** Edits A/B are print/report-only. Edit C is backward-compatible by construction (optional regex group) and its failure mode is cosmetic (unknown type → group None). The core apply path (`apply_manual_translation`) is untouched.


## V-5 — Translation Engine Architecture (provider/model flexibility)

### Evidence

- **[FACT]** Cell 8 hardcodes exactly three auto engines: `translate_with_gemini` (google-genai SDK, 8:427–464), `translate_with_chatgpt` (OpenAI SDK, default base_url, 8:475–526), `translate_with_nllb` (transformers, 8:537–666). The dispatcher `translate_text` branches on literal engine names (8:747 gemini / 8:754 chatgpt / 8:761 nllb / 8:768–770 unknown-engine → empty). `switch_translator` validates against a hardcoded list `["manual", "gemini", "chatgpt", "nllb"]` (8:783). UI offers manual/gemini/nllb only (25:276).
- **[FACT]** The OpenAI SDK is already a dependency (chatgpt path), and `OpenAI(api_key=…, base_url=…)` accepts any OpenAI-compatible endpoint — which covers **all five Owner-required providers**: OpenAI (native), DeepSeek (`https://api.deepseek.com`, OpenAI-compatible per their docs), Qwen DashScope compatible-mode (`https://dashscope.aliyuncs.com/compatible-mode/v1`), Ollama (`http://localhost:11434/v1`, key optional), OpenRouter (`https://openrouter.ai/api/v1`; also fronts qwen/deepseek/gemini models).
- **[FACT]** Shared translation assets are already provider-neutral: `build_translation_prompt` (8:244–301, region-type aware + glossary lines), `translate_with_retry` (8:378–416, 3 retries w/ backoff), `clean_translation` (8:154–187), SFX glossary short-circuit (8:733–737).
- **[TEST RESULT — Flash]** NLLB quality is unusable-as-final for profanity/idiom (S001 regions 1/5/6: "যৌনসঙ্গম" for "fuck", "সে আমার ভিতরে ছিল" for "she was into me", "! !" tokenizer spacing) — confirming the Owner's policy to demote NLLB to experimental.
- **[FACT]** `MANGABD_SECRETS` is a flat dict with runtime key injection already proven in the UI (25:343 writes `gemini_api_key` from a Password widget); the sanitizer strips keys before config save, so adding provider keys follows an established pattern.

### Proposed architecture — provider registry + one OpenAI-compatible adapter (NO new dependencies; NO core-loop rewrite)

**Why not LiteLLM:** it would add a large dependency tree to a Colab notebook whose fresh-run reliability MANGABD-002 just stabilized (dependency surface = pip-install failure modes), and its model-string routing would move provider knowledge OUT of the Owner's CONFIG. The native adapter is ~35 lines, uses the already-required OpenAI SDK, and keeps every knob in `MANGABD_CONFIG`. (If the Owner later wants LiteLLM's provider list, the adapter's call site is a single function to swap.)

**Design (Phase C candidate — 3 edits in cell 8 + 1 in cell 25):**

1. **Registry (cell 8 config block, after 8:78):**

```python
MANGABD_CONFIG["translation"].setdefault("providers", {
    "openai":     {"base_url": "https://api.openai.com/v1",
                   "model": "gpt-4o-mini",        "api_key_env": "openai_api_key"},
    "qwen":       {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
                   "model": "qwen-plus",           "api_key_env": "qwen_api_key"},
    "deepseek":   {"base_url": "https://api.deepseek.com",
                   "model": "deepseek-chat",       "api_key_env": "deepseek_api_key"},
    "ollama":     {"base_url": "http://localhost:11434/v1",
                   "model": "qwen2.5:7b",           "api_key_env": None},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",
                   "model": "google/gemini-2.0-flash-001", "api_key_env": "openrouter_api_key"},
})
```

   Models are CONFIG values — switching DeepSeek-chat→DeepSeek-reasoner or pointing OpenRouter at any of its 300+ models is a config edit, zero code. (Default models to be confirmed by the Owner in Phase B.)

2. **Adapter (cell 8, after `translate_with_chatgpt` ~8:526):**

```python
def translate_with_provider(text, region_type="bubble", engine="openai"):
    """OpenAI-compatible provider adapter (openai/qwen/deepseek/ollama/openrouter)."""
    prov = MANGABD_CONFIG["translation"].get("providers", {}).get(engine)
    if not prov:
        log_event(f"Unknown provider: {engine}", level="WARN"); return ""
    api_key_env = prov.get("api_key_env")
    api_key = MANGABD_SECRETS.get(api_key_env, "") if api_key_env else "ollama"
    if api_key_env and not api_key:
        log_event(f"{engine} API key not set ({api_key_env})", level="WARN"); return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url=prov["base_url"])
        prompt = build_translation_prompt(text, region_type=region_type)
        response = client.chat.completions.create(
            model=prov.get("model", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": (
                    "You are a professional English-to-Bengali manga translator. "
                    "Return only the Bengali translation.")},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3, max_tokens=512,
        )
        return clean_translation(response.choices[0].message.content.strip())
    except Exception as exc:
        log_event(f"{engine} translation failed: {str(exc)[:120]}", level="WARN")
        return ""
```

   Note: Ollama accepts any non-empty key string as auth placeholder; real auth is the local server. `translate_with_chatgpt` remains as a legacy alias for saved configs and is behaviorally identical to `translate_with_provider(engine="openai")`.

3. **Dispatcher (cell 8, insert before the `else` at 8:768):**

```python
    elif engine in MANGABD_CONFIG["translation"].get("providers", {}):
        result = translate_with_retry(
            translate_with_provider, text, region_type=region_type, engine=engine,
        )
```

   and `switch_translator` valid list (8:783) becomes `["manual", "gemini", "chatgpt", "nllb"] + list(MANGABD_CONFIG["translation"].get("providers", {}).keys())`. Sidecar fidelity: `translate_page` already records `translator_engine`; **add `"translator_model"` to the record dict** (8:1128–1136 build_translation_records_from_df — one line, backward-compatible additive field) so S002+ evidence shows which model produced each run.

4. **UI (cell 25, 25:276):** extend options to `[("📝 MANUAL","manual"), ("💎 GEMINI","gemini"), ("🌐 OPENROUTER","openrouter"), ("🐉 DEEPSEEK","deepseek"), ("☁️ QWEN","qwen"), ("🖥️ OLLAMA (local)","ollama"), ("📚 NLLB (experimental)","nllb")]`, and add one Password box + handler mirroring the gemini-key pattern (25:290–291, 25:341–349) for the selected provider's key. NLLB relabeled "experimental" per Owner policy.

5. **Prompt upgrade for LLM providers (quality, addresses Flash's translation findings):** extend `build_translation_prompt`'s rules (8:262–270) with two lines: "Render profanity/idiom with natural colloquial Bengali equivalents — never clinical/literal word swaps." and "Fix grammar and word order into natural Bengali; preserve the speaker's register (casual manga dialogue, not honorific unless clearly politeness-marked)." Plus a 2-line punctuation normalizer in `clean_translation` (8:184–186 whitespace block): `text = re.sub(r"!\s+!", "!!", text); text = re.sub(r"!\s+\?", "!?", text)` — kills the NLLB "! !" tokenizer artifact class on every engine at zero risk.

**Switching providers via CONFIG (Owner requirement, verbatim satisfied):** `MANGABD_CONFIG["translation"]["engine"] = "deepseek"` (or `switch_translator("deepseek")`, or the UI selector) — the core loop (`translate_page` → `translate_text` → adapter) is untouched; model/base_url/key all live in the providers dict. Multi-provider A/B: change `engine` between runs; sidecars record engine+model per run.

### Regression risk — MEDIUM-LOW

- Existing engines (manual/gemini/chatgpt/nllb) keep their exact branches — the new `elif` only adds a branch, so saved sessions and configs behave identically. The adapter is additive; the OpenAI SDK call mirrors the proven chatgpt path (8:487–517) with only base_url/model parameterized.
- Real risks: (a) per-provider auth quirks (Ollama key placeholder, OpenRouter optional `HTTP-Referer` header) — surfaced as logged WARN + empty translation, which the existing retry/failure path already handles; (b) provider models' output style variance — mitigated by the shared prompt + `clean_translation`, and per-run `translator_model` in sidecars keeps S002 evidence honest; (c) key management surface grows by 4 keys — same pattern as gemini (Password widget → MANGABD_SECRETS, sanitizer strips on save).
- Prompt additions apply to gemini/provider paths only if appended to the shared builder — they also reach NLLB's… no: `build_translation_prompt` is used by gemini/chatgpt/provider only; `translate_with_nllb` passes raw text (8:640s) — NLLB is unaffected (experimental, unchanged).

## S002 Re-run Plan (proposal for Flash's re-review after Phase C)

1. **Page:** the SAME page as S001 (the "02.jpg" B/W page). Rationale: identical quads/detections make every V-fix a controlled A/B against S001's archived measurements — Flash can re-run the exact pixel checks (region-1 CJK ink height/luminance, residue scan at 34–47×370–381, OCR cross-check, border integrity at x≈75) and any delta is attributable to the fix, not the input.
2. **Translation engine:** **an LLM provider through the new adapter — recommend `deepseek` (`deepseek-chat`) as primary**, with `openrouter` as fallback if the Owner's key situation prefers it; **NLLB explicitly NOT used** (Owner policy: experimental only). The Owner supplies the API key via the UI Password box at runtime (same as the gemini-key flow). Manual post-edit of the three S001-garbage regions (1/5/6) remains available per the core-workflow policy — but S002 should first be reviewed un-post-edited to grade the raw LLM engine.
3. **Procedure:** fresh Colab session → fresh Run All (MANGABD-002-verified flow, notebook at the Phase-C commit) → upload 02.jpg → detect+OCR → translate with deepseek → inpaint+render (Control Studio 🎨 or cell 26) → export → Owner ZIPs the same 7 artifact types → GLM-5.3 archives as `samples/S002_bw_manga_llm/` (name carries corrected conventions from the start; metadata.json rev1 with engine=deepseek, source_type="B/W manga page", model recorded) → Flash re-reviews against the S001 baseline.
4. **Acceptance targets for Flash (from S001 measurements):** zero residue specks at the region-1 band; CJK ink height ≥ 0.8× Bengali run height and ink luminance ≤ 60 (vs S001's ~50%/≈90); region-1 OCR contains "Otearai"/"おてあらい" (or is flagged for manual review via V-3 Layer 2); no new border damage anywhere (diff-vs-S001 outside masks); translation naturalness on regions 1/5/6 graded pass/fail vs the S001 NLLB baseline.

## Phase A Status

**COMPLETE — INVESTIGATION & PROPOSALS ONLY. NO SOURCE CODE CHANGED** (verified: `git status` clean on the notebook; all notebook evidence cited from a read-only re-extraction). Awaiting Owner approval per V-item before any Phase B/C implementation. Suggested phasing for Phase C: V-4a (docs-only, zero risk) + V-2 (1 hunk, cell 6) + V-1 (2 mirrored functions, cells 11/12) as batch 1; V-3 (cell 7 + cell 16) as batch 2; V-5 (cell 8 + cell 25) as batch 3 — each batch independently verifiable and revertable, per the MANGABD-002 change-control precedent.


---

# MANGABD-003 — PHASE C IMPLEMENTATION RECORD (GLM-5.3)

**Mandate:** Owner-approved Phase C exactly per Flash's Phase B enumerated scope (relay: PM; Phase A = commit `b9c43a9`; Flash Phase B = commit `1cd8acf`, verdict APPROVE_WITH_CHANGES). Phase D reconciliation folded in: before implementing each amended item, the amendment was re-confirmed against the code with a line citation; a rebutted amendment would NOT have been implemented. **Result: all amendments CONFIRMED and implemented; zero rebuttals; three factual precisions recorded (T3.14) — none blocking, none changing an amendment's required action.**

**Method:** fresh cell extraction from the main notebook (27 cells, blob sha256 `448540f8…` = the MANGABD-002-verified merge; byte-identical writer `json.dumps(nb, indent=2, ensure_ascii=False)` re-asserted on the pre-edit file); programmatic JSON edits with hard preconditions (each old block must match exactly once; per-cell source-list reconstruction convention validated pre-edit; AST-parse after every edit); pre-edit cell snapshots in `/home/z/my-project/phaseC003/`; verification scripts in `/home/z/my-project/scripts/` (`phase_c003_apply.py`, `phase_c003_v4a.py`, `phase_c003_patch_detgeo.py`, `phase_c003_verify.py`, `phase_c003_runtime1.py`, `phase_c003_runtime2.py`).

## T3.14 Phase D reconciliation (folded-in) — verdicts with citations

| # | Amendment (Flash Phase B / Owner relay) | Verdict | Citation (pre-edit, physical-cell:line) |
|---|----------------------------------------|---------|------------------------------------------|
| 1 | V-1 amend 1: post-scale overflow re-check needed | **CONFIRMED** | `fit_font_size` calibrates with the main font only (10:415 `get_font(mid, bold=bold)`, 10:416 `split_text_to_lines`, 10:424 `measure_text`); vertical path calls it with swapped dims (12:120 `fit_font_size(text, h, w, …)`); pre-edit run loop re-measured per-run widths but never compared `total` to `int(h)-2*padding` (12:126–131) |
| 2 | V-1 amend 2: baseline-align via `getmetrics()` | **CONFIRMED** | all runs shared the top-left anchor `ly` (12:134 `draw.text((lx, ly), …)`); `lh = get_line_height(get_font(size, bold))` (12:121) = `(ascent+descent)*1.18` with `line_spacing_factor` default 1.18 (10:243–253, setdefault at 10:63) |
| 3 | V-1 amend 3 (cosmetic): three knobs, not two | **CONFIRMED** | Phase A text said "two config setdefaults" while listing three knobs; implemented as THREE setdefaults |
| 4 | V-2: no amendments; document ceiling | **CONFIRMED** | insertion point verified live (6:769–834; clip block 6:815–826; `return mask` 6:827); cell 9 re-clips artifact masks to boxes+`mask_clip_padding`=10 (9:76, 9:234–236) → effective band ceiling = 10; documented in the knob comment |
| 5 | V-3 L1 (a)–(c): rotated-only candidates, strict-'>' tie-break, audit logging | **CONFIRMED** | `confidence` = `_estimate_ocr_confidence` (5:281–314): 0.45+0.15(len≥2)+0.10(len≥5)+0.20(en≥0.6)+0.05(no brackets), capped 0.95 — saturated for ≥5-char Latin reads; `_language_scores` (5:247–278) counts ASCII-alpha vs Bengali only — kana invisible (S001 R1 en=1.0 despite kana); pre-edit `max()` tie resolves to first element (upright = S001 failure mode). All three sub-amendments implemented |
| 6 | V-3 L2 (a): `import re` inside the snippet | **CONFIRMED** (with precision) | `re` is NOT imported in cell 16 (imports are json/Path/datetime/pandas, 16:17–21) — operative fact correct, action required. Precision: Flash's phrasing "cell 16 contains no imports" is imprecise (the cell does import json/pandas/etc., just not `re`); no effect on the amendment's action |
| 7 | V-3 L2 (b): df-branch has no `region` object — resolve geometry from detection records | **CONFIRMED** | df branch iterates `page_rows` with `region_id`/`text` only (16:373–377, 16:425–431); `region` exists only in the artifact branch (`region = item.get("region", {})`, 16:295). Implemented as `det_geo` built from `load_json_artifact(page_id, "detections", default=[])` — the same id→record idiom as cell 11's `recover_coordinates` (11:33), guard-free by design (detection ids are int-able pipeline-wide) |
| 8 | V-5 amend 1: dispatcher must bind engine via closure | **CONFIRMED** | `translate_with_retry(translate_func, text, region_type="bubble")` (8:372) invokes `translate_func(text, region_type)` positionally (8:390) — no engine kwarg; Phase A's `engine=` kwarg call would TypeError. Implemented exactly as the scope's lambda |
| 9 | V-5 amend 2: registry field must be `key_env` | **CONFIRMED** | `save_config` sanitizer `forbidden_keys = ["api_key","token","secret","password"]` + `any(bad in str(key).lower() …)` strip (1:535–548) would delete any `api_key_env` key on every save. Implemented `key_env`; T7 test proves providers survive sanitize while an `api_key_env` control IS stripped (sanitizer unweakened) |
| 10 | V-5: SECRET_SOURCES provider env names | **CONFIRMED** (location precision) | SECRET_SOURCES lives in **cell 1** (1:407–411), not "cell 2" as the relay stated (Flash cited it correctly); implemented in cell 1 where the code is |

**Factual precisions recorded (no amendment rebutted, no item skipped):**

1. **Mirror premise (V-1):** pre-edit, `get_font_fb` WAS byte-identical across cells 11/12 (11:149–155 ≡ 12:106–112, incl. the preceding `_FB_CACHE = {}`), but `_qc_render_vertical` was NOT — cell 12's copy carried 4 dead preamble lines (`size, lines = 8, [text]`, `# fit with swapped dims`, local `ImageDraw as _D` import, dummy `d = _D.Draw(...)`) and a 2-line paste tail vs cell 11's 1-liner (semantically identical). The Owner requirement "byte-identical after the edit" is satisfied by replacing both regions with ONE canonical 61-line block (cell 12's live semantics + V-1); dropping the dead lines is behavior-preserving (immediately rebound / unused).
2. **V-3 Layer 1 predicate source (my own Phase A correction, not a Flash amendment):** Phase A's snippet tested `preprocessed.shape` — defective: S001 region 1 (61×298) passes crop context (+9/+44 px, 6:872–873 `max(8, min(100, dim*0.15))`), overlay border (+8 px/side, 6:878–886 `max(8, min(30, w//8))`), and preprocess pad (+9 px/side, 7:263–287 `max(4, min(h,w)//10)`) → preprocessed ≈ 95–113 px wide → `rw < 90` would NOT fire for the exact S001 defect. Corrected to the REGION dims (`region.get("width"/"height")` — the parameter is in scope in `ocr_region`), keeping the predicate expression byte-identical to the renderer's (12:146).
3. **Scope fidelity:** V-4b Edits A/B (unparsed-line report, coverage report) are NOT in the Owner's enumerated Phase C scope (only V-4a is) — not implemented, per "SCOPE (exactly; nothing else)". Same for Phase A's proposed prompt upgrade and "! !" normalizer (not enumerated) — deferred with V-4b. `translator_model` is additive-only: one sidecar field in `build_translation_records_from_df` resolving provider models from the registry (a row-level `translator_model`, if ever set, wins; manual/gemini/nllb rows leave it empty).

## T3.15 What changed (per batch, post-edit cell:line)

**Batch 1:**
- **V-4a** — `samples/S001_color_webtoon/metadata.json` → rev2 (engine=nllb, source_type="B/W manga page", `metadata_revision`: 2, `revision_note`, `naming_note`; provenance fields carried over verbatim: sample_id/captured_at/notebook_commit/pipeline_variant/owner_notes); `samples/S001_color_webtoon/metadata.rev1.json` = the previous file byte-verbatim; one-line pointer added under the Contents table in `samples/README.md`. The 7 pipeline artifacts are byte-untouched (size-verified: 377597/8339/1424967/354649/2704/5176/2666 bytes).
- **V-2** — cell 6, ONE contiguous insert between the region-clip block and the raw-mask-branch `return mask` (post-edit 6:827–845): `detection_cfg.setdefault("mask_vpad_vertical", 10)` + gated band (two rectangles, top `[y−vpad, y+vpad]` and bottom `[y+h−vpad, y+h+vpad]`, x confined to the region's own column) for `rw < 90 and rh > 2 * max(1, rw)` regions; comment documents the effective ceiling (=`mask_clip_padding`, 10 — excess trimmed at cell 9's re-clip).
- **V-1** — cells 11 (post-edit 11:148–208) and 12 (post-edit 12:105–165): the regions from `_FB_CACHE = {}` through `_qc_render_vertical`'s return replaced with ONE canonical 61-line block (byte-identical in both cells): 3 setdefaults (`fallback_font_wght` 600, `fallback_cjk_scale` 1.25, `fallback_cjk_stroke` 1); `get_font_fb` honors bold via `set_variation_by_axes([wght])` inside `try/except OSError` (static-font fallback; `wght = max(wght, 700)` when bold); `_qc_render_vertical` scales fallback runs (`int(size*scale)`), measures per-run with the actual fonts, **Flash amend 1**: per-line while-retry ladder `while any(not im …) and total > int(h)-2*padding and scale > 1.0: scale = 1.12 if scale > 1.12 else 1.0` (per-line scale, monotone, floor 1.0); **Flash amend 2**: `ly_run = ly + asc_main - f.getmetrics()[0]` for fallback runs; stroke `_fb_stroke` + `stroke_fill` on fallback runs only. The monkey-patch wrappers, `_main_font_ok`, `_split_runs`, and all other cell-11/12 functions are untouched.

**Batch 2:**
- **V-3 Layer 1** — cell 7: (i) recognize site replaced (post-edit 7:391–438): when the REGION-dims predicate fires, candidates = `[ROTATE_90_CLOCKWISE, ROTATE_90_COUNTERCLOCKWISE]` ONLY (upright excluded — 2 VLM calls); strict-`>` selection starting from CLOCKWISE (`chosen = candidates[0]`, replace only if strictly greater — deterministic rotated-first tie-break); score = confidence + `language_score.en` (unchanged metrics); chosen orientation + all candidate scores appended to the chosen result's `warnings` AND returned as a structured `vertical_ocr` dict; (ii) return dict gains `"vertical_ocr": vertical_ocr` (post-edit 7:432; `None` for non-vertical regions — additive field). Non-vertical regions take the identical single-call path; the `|angle|>5` rotated-crop branch is untouched.
- **V-3 Layer 2** — cell 16, three inserts inside `inspect_ocr_quality`: (i) artifact branch flag (post-edit 16:367–381, after the short-text check): `import re` (cell-standalone) + kana/latin regexes + `rw_ < 90 and rh_ > 2 * max(1, rw_)` predicate → warning-severity issue; (ii) df-branch preamble (post-edit 16:394–399): `import re` + `det_geo` dict comprehension from the detection records; (iii) df-branch flag (post-edit 16:474–488, after the last check): same predicate via `det_geo` geometry. Severity "warning" only — flows into `manual_review_flags`, cannot fail/block a page (zero new raise/abort sites in cell 16).

**Batch 3:**
- **V-5, cell 8** (5 sites): (i) provider registry (post-edit 8:82–98): `MANGABD_CONFIG["translation"].setdefault("providers", {...})` with openai/qwen/deepseek/ollama/openrouter — fields `{base_url, model, key_env}` (**key_env**, sanitizer-safe; comment documents why); (ii) adapter `translate_with_provider(text, region_type, engine)` (post-edit 8:533–570): registry resolution → `MANGABD_SECRETS[key_env]` (ollama placeholder when `key_env=None`) → OpenAI SDK client with per-provider `base_url` → `build_translation_prompt` → `chat.completions.create(model=prov["model"], temperature=0.3, max_tokens=512)` → `clean_translation`; (iii) dispatcher `elif engine in …providers` (post-edit 8:783–792) binding the engine via **closure** — `translate_with_retry(lambda t, rt: translate_with_provider(t, rt, engine=engine), text, region_type=region_type)` — `translate_with_retry`'s signature NOT widened; (iv) `switch_translator` valid list (post-edit 8:807–810) = static four + `list(providers.keys())`; (v) `build_translation_records_from_df` gains additive `"translator_model"` (post-edit 8:1158–1167; row-level value wins, else registry model by engine, else "").
- **V-5, cell 25** (5 sites): `btn_provider` button; `mode_sel` options = MANUAL / GEMINI / OPENROUTER / DEEPSEEK / QWEN / OLLAMA (local) / NLLB **(experimental)** (NLLB relabeled per Owner policy; value stays "manual" default); `on_provider` callback → `run_translation_all(engine=mode_sel.value, force=True)`; callback registration; `rebuild_mode_panel` provider branch (HTML hint: Colab secret `'<m>_api_key'`; Ollama: no key). No new Password widget (not in enumerated scope — keys bootstrap via SECRET_SOURCES).
- **V-5, cell 1** (1 site): SECRET_SOURCES gains `qwen_api_key` [QWEN_API_KEY, DASHSCOPE_API_KEY], `deepseek_api_key` [DEEPSEEK_API_KEY], `openrouter_api_key` [OPENROUTER_API_KEY] (post-edit 1:407–420; ollama deliberately absent — local server, no key).

**Explicitly out of scope — untouched (verified):** V-4b Edit C (deferred per Flash) AND Edits A/B (not enumerated); NLLB translator function and its dispatcher branch (test-only status unchanged); manual engine default (`engine=manual`) and `apply_manual_translation`/cell-22 paste path; `restore_boxes`/box-snap (`_snap_white_box`, `apply_container_types`); no cell reordering (first line of every cell unchanged); no new module-level pipeline calls (only `print` in cell 8 and an `mbtn` assignment in cell 25); try/except added ONLY at the two prescribed sites (`except OSError` in both get_font_fb copies; the adapter's `except Exception` mirroring the proven chatgpt shape) — the initially-drafted guarded det_geo loop was replaced with cell 11's guard-free comprehension idiom before commit.

## T3.16 Verification outputs

**Static checklist — ALL PASS** (`phase_c003_verify.py`, 55 checks): notebook JSON re-parses; 27 cells; AST-parse all 27; MIRROR — full V-1 block, `get_font_fb`, and `_qc_render_vertical` byte-identical across cells 11/12, 3 setdefaults identical in both, `_main_font_ok`/`_split_runs` untouched; monkey-patch wrappers unchanged; V-1 content (OSError guard, bold, ladder, baseline, stroke, cache key); V-2 content (knob, predicate form, two rectangles, ceiling doc, clip→band→return order); V-3 L1 (2 recognize sites — upright only in else, strict '>', region-dims predicate, audit into warnings+sidecar, rotated-crop branch untouched); V-3 L2 (import re ×2, regex ×2, warning-only, det_geo, zero new raises); V-5 (5 `key_env`: entries, no `api_key_env` dict key, adapter, closure, no signature widening, dynamic valid list, sidecar field, UI options, SECRET_SOURCES); out-of-scope guards (V-4b absent, NLLB untouched, manual default, apply_manual_translation untouched, cell 22 untouched, no new module-level calls, no reordering, try/except delta exactly as prescribed); no secret patterns; metadata rev2/rev1 fields; sidecar JSONs still parse.

**Runtime tests — ALL PASS** (39 checks, `phase_c003_runtime1.py` + `phase_c003_runtime2.py`; real edited code exec'd from the notebook with mocked collaborators):
- **T1 `_qc_render_vertical`** (real PIL render, DejaVu main + kana-capable fallback): ladder re-measures on overflow (2nd pass at reduced size) and draws at the reduced scale; baseline alignment exact (`ly + asc_main − asc_fb`, ±1 px); fallback runs stroked (w=1, fill), main runs unstroked; pure-main lines take the identical single-pass path; real-`get_font_fb` smoke render without crash.
- **T2 `get_font_fb`**: loads the real fallback font; distinct cache keys per (size, bold); `set_variation_by_axes` OSError is survivable (except path, load intact) on both a variable and a static font; load-failure falls back to the main font.
- **T3 `ocr_region`**: exactly 2 VLM calls for a vertical region, upright image never sent, CW+CCW both tried; tie resolves to CLOCKWISE; strictly-better CCW wins; `vertical_ocr` sidecar has chosen orientation + both candidate scores; warnings carry the audit line; the CW read ("Otearai") beats the S001 upright misread pattern; non-vertical regions: 1 call, `vertical_ocr=None`, no audit warning.
- **T4 Layer 2 snippets** (exec'd verbatim from cell 16): fires on vertical kana+Latin in BOTH branches; silent for bubbles / pure-Latin / pure-kana / missing geometry; df-preamble builds `det_geo` from detection records (id-less record → −1).
- **T5 dispatcher closure**: `translate_with_retry` entered with its exact 3-arg signature; engine bound correctly (deepseek, ollama) with positional `(t, rt)`.
- **T6 `translate_with_provider`** (fake OpenAI SDK): returns cleaned translation; base_url/model/api_key all from the registry; prompt via `build_translation_prompt`; system message present; ollama key placeholder; missing key → "" + WARN; unknown provider → "" + WARN.
- **T7 sanitizer interplay**: the providers registry SURVIVES `save_config`'s sanitize (key_env clean) while an `api_key_env` control IS stripped — the sanitizer is unweakened; registry values match the approved defaults.

**Environment notes (verification-only, no production impact):** (1) this sandbox venv's FreeType lacks variation-axis support — `set_variation_by_axes` raises `OSError` and leaves corrupted metrics on the failed call; the ladder test therefore used clean-metrics fonts, and the OSError fallback path is what this venv exercises. On Colab (standard Pillow wheels) the wght path runs — Flash verified `set_variation_by_axes` functional on Pillow 11.3.0 (Phase B). (2) The venv's filesystem view hides some font files visible to the system python — irrelevant to the notebook.

## T3.17 Diff audit (pre-commit, working tree vs `1cd8acf`)

- **Files:** notebook `MangaBD_V12_ipynb_txt.ipynb (3).txt` (+287/−23), `samples/README.md` (+2/−0), `samples/S001_color_webtoon/metadata.json` (+6/−3), `samples/S001_color_webtoon/metadata.rev1.json` (new, 10 lines) + this file (agents/GLM_5_3.md). Scope = {notebook, samples/S001_color_webtoon/*, agents/GLM_5_3.md} + the README one-liner explicitly mandated by the V-4a item; DECISION.md and GLM_5_3_FLASH.md untouched.
- **Hunk structure (git -U3):** notebook 19 hunks; per-cell logical changes — cells 6 (1 region), 11 (old lines 148–174, one contiguous replacement region), 12 (old lines 105–139, one contiguous replacement region), 7 (2 regions), 16 (3 regions), 8 (5 regions), 25 (5 regions), 1 (1 region). Cells 6/11/12 are literal single-region edits; cells 7/8/16/25 carry the multiple disjoint sites the Owner's own V-3/V-5 enumeration requires — every cell carries exactly ONE logical change (the audit convention per Flash Phase B batch note); the 7/9 git-diff runs inside the cell-11/12 regions are line-matching artifacts within one replaced function region (verified: all changed old-line indices lie inside 148–174 / 105–139 respectively, prefix and tail identical).
- **Modes:** all 100644 (samples + docs). **Secrets:** diff scan clean (no ghp_/sk-/AIza/hf_/Bearer patterns). **Notebook integrity:** 27 cells, all AST-parse; 19 untouched cells byte-identical; cell outputs/metadata untouched (only edited cells' `source` changed).

## T3.18 Phase C status

**COMPLETE — WIP.** Commit on branch `mangabd-003-phase-c` (message: "WIP: MANGABD-003 Phase C — awaiting Phase E verification"), pushed for Flash's Phase E inspection. Main held at `1cd8acf`. Per protocol: DO NOT amend/merge until Flash sign-off is relayed via PM/Owner. Next: Phase E (Flash) verification of the pushed WIP — suggested checks: the mirror byte-identity, the T3.16 checklist re-run, S002 fresh Run All (deepseek-chat via the new adapter, keys via Colab secrets per SECRET_SOURCES), Flash's S001 pixel measurements re-run on S002 (§C.4 acceptance targets: zero residue at the region-1 band; CJK ink height ≥0.8× Bengali; ink luminance ≤60 — `fallback_font_wght=700` / `fallback_cjk_stroke=2` are already config knobs if 600/1 undershoot; region-1 OCR correct or flagged; no new border damage; translation naturalness on regions 1/5/6).
