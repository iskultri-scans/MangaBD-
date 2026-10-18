# GLM-5.3 — Lead Developer Log

## ROLE

Lead Developer / Software Architect

---

## CURRENT PHASE

**MANGABD-005 (QUALITY BATCHES) — BATCH 2 (LENIENT PASTE-BACK PARSER) CLOSED: SQUASH-MERGED TO MAIN (`7ec691b`, 2026-10-18; full record "# MANGABD-005 — BATCH 2 MERGE COMPLETION RECORD" / PC-M2 below); branch `mangabd-005-b2` deleted local+remote; MANGABD-005 FULLY CLOSED (B1 `4d9b787` + B2 `7ec691b`).** (Branch cut from `main @ 8445328`, 2026-10-15; PM Qwen3.8-Max relay of Owner authorization.) Scope cells {8, 22, 25} ONLY — the PM-spec 8-step lenient normalization pipeline (markdown unescape BEFORE any regex → single-line multi-tag blob split → tag regex → FIRST-arrow split incl. `->`/`=>`/`⇒` → arrowless Bengali-only accept / English-only unparsed-with-hint → placeholder skip+report → page stem-match (unique accept 🟡 / ambiguous unparsed) → duplicate count), V-4a sentinel preserved never-silent, one-line variant summary print, copy-payload System Prompt rule 5, wire format byte-identical, 22 cell-8 self-tests (Owner's three real sample shapes 100% + negative fixture reported-not-applied), 60-check verify suite ALL GREEN, m002_sim_v2 0 abort sites both sides. Full record: "# MANGABD-005 — PHASE C (BATCH 2)" below. **Branch chain since Phase C (122e353): Flash Phase D APPROVED `11bbd1f` → RF-2 DataFrame-safe sentinel `2c4635d` → Flash RF-2 delta CLOSED `29c17ba` → RF-3 trailing-arrow + Owner prompt `c5f51c4` → RF-4 bare [SKIP] marker-skip `fe879fe` → Flash RF-3(+RF-4) delta CLOSED `08ad231` (gate fully discharged) → **OWNER LIVE ACCEPT — ZERO DEFECTS** (extensive live end-to-end Colab testing of the B2 lenient paste-back parser, the trailing-arrow fallback (RF-3), and the new 10-section system prompt; Owner verdict relayed via PM Qwen3.8-Max, 2026-10-18) → Owner merge authorization → squash-merge to main executed as `7ec691b`. Self-test battery 25; records in the sections below.**

**MANGABD-005 (LAMA FULL RESOLUTION) — BATCH 1 (B3) CLOSED: SQUASH-MERGED TO MAIN (`4d9b787`, 2026-10-15); branch `mangabd-005-b1` deleted local+remote.** Gate chain: Phase C `05bee82` → Flash Phase D APPROVED `5113f00` (46 checks + 3 sims on the pushed bytes: E1 scope {9}-only, E2 OOM-only ladder fault-injection, E3 effective-2048 + cell-1 warm-rerun revert adjudicated, E4 unload_all→ensure_lama order, E5 m002_sim_v2 0 abort sites) → Owner S007 ACCEPT `93de3f8` (844×1200 native-rung archive vs the S003 baseline, G1–G4 — merge gate discharged) → Owner merge authorization (PM relay, 2026-10-15) → squash-merge `4d9b787` (staged bytes md5-identical to the branch tip `93de3f8`). Tracked follow-ups logged in DECISION.md §E.1: cell-1:295 lama_size cleanup, r1 kana tofu (N-D), acceptance-zip metadata.json export. Completion record: "# MANGABD-005 — BATCH 1 MERGE COMPLETION RECORD" below. Phase C implementation (delivered on the branch, 2026-10-14): Cell-9-ONLY implementation of the Phase-A A4.3-P1 proposal — `lama_size` working default 1024→2048 (max-dim ≤ 2048px pages, incl. the Owner's 844×1200, now run NATIVE — no pre-inpaint downscale); OOM-safe resolution ladder `[owner, 2048, 1536, 1024]` with CUDA-OOM-ONLY retries (Flash Phase B Amendment 5: every other error, incl. the deterministic empty-result error, goes straight to the existing OpenCV-Telea fallback) and `clear_gpu_cache()` between rungs; legacy-1024 migration at cell-9 config load (the cell-1 dict hardcode — same 1024 — is OUT OF SCOPE per the directive's "Cell 9 ONLY" and is disclosed in §PC-C1 — now logged as a tracked follow-up in DECISION.md §E.1); stage meta gains `inpaint_size_effective`; `unload_all(exclude=["lama"])` → `ensure_lama()` VRAM ordering re-verified byte-stable and runtime-proven; 3 new embedded self-tests (7→10). 44-check verification suite ALL GREEN (scripts/m005_b1_build.py + scripts/m005_b1_verify.py): full cell-9 runtime exec with fake LaMa/torch stubs, 4-case migration matrix, ladder-arithmetic battery over owner sizes {1024, 1536, 2048, 3072}, `inpaint_page` integration (OOM step-down → meta 1536 / all-rungs OOM → OpenCV fallback, meta None), m002_sim_v2 0 abort sites (pre- and post-patch). Full record: "# MANGABD-005 — PHASE C (BATCH 1)" below. [TEST RESULT]

MANGABD-005 Batch 1 (this entry): PM directive (Qwen3.8-Max relay, 2026-10-14, authorized by Project Owner) — MANGABD-005 opened; first task Batch 1 = B3 (LaMa Full Resolution) per the MANGABD-004 Phase A findings (§A4): the 1024 throttle silently downscales every Owner page ~0.85× before inpainting while upstream LaMa Large defaults to 2048 and is fully convolutional (no architectural constraint). Fix ladder: native-first + OOM-safe step-down. Branch `mangabd-005-b1` from `main @ 5e70507` (= the M004 squash-merge state, blob-verified). Rules of engagement honored: single-logical-change audit convention, Cell 9 only, record here, WIP commit, push + notify for Flash's Phase D verification. [FACT]

**MANGABD-004 (ARCHITECTURE & WORKFLOW REVAMP) — CLOSED: B1+B2 SQUASH-MERGED TO MAIN (`156df93`, 2026-10-14); branch `mangabd-004-b1-b2` deleted local+remote. Gate chain: Phase A `c196505` → Flash Phase B CONFIRMED WITH AMENDMENTS `97a683a` → Phase C B1+B2 `ab2aa36` → Flash Phase D APPROVED_WITH_FIXES `f460143` → RF-1 landed `3c57583` → Flash RF-1 CLOSED / Phase C APPROVED `7f0e653` → Owner S005 samples archived `48fa3ca` → Flash S005 verdict BOTH ACCEPT `c5fe8a9` → Owner merge authorization (PM relay) → squash-merge `156df93`. B3 (LaMa ladder) + B4 (OCR prompt map) proposed but never authorized within M004 (§A6) — B3 now authorized, implemented, and MERGED (MANGABD-005 Batch 1 CLOSED — see the MANGABD-005 entries above). MANGABD-003 Batch 3 SUPERSEDED per A7-D1 (Owner approved skipping S004)**

Merge completion (this entry, 2026-10-14): executed the Owner's numbered final-merge directive (PM relay) on Flash's S005 acceptance verdict **BOTH ACCEPT** (`c5fe8a9`, S1–S5 all PASS) — squash-merged `mangabd-004-b1-b2` (5 commits, linear on merge-base `97a683a`, tip `c5fe8a9`) into `main` as one commit after byte-level md5 verification of all 3 changed files against the branch tip; pushed; branch deleted local + remote; this docs sync (DECISION.md STATUS + §D.1, this file's §C7) follows as a separate commit per the directive's sequencing. Full record: §C7 below.

RF-1 (this entry): Flash Phase D verdict on `ab2aa36` — APPROVED_WITH_FIXES; one required fix: the dead `"nllb"` dict survived in the live `MANGABD_CONFIG` literal (cell 1:288–293 0-indexed = source lines 289–295 1-indexed; model id `facebook/nllb-200-distilled-600M`; zero consumers; lands in saved `config_v12.json`). Landed as a single follow-up commit on the same branch (Flash's prescribed path: no amend of `ab2aa36`, no merge): byte-level surgical removal of the 7 source lines / 7 raw JSON lines, single hunk, 0 insertions. 33-check verification suite ALL GREEN incl. fresh `save_config()` round-trip on real cell-1+cell-8 code (no nllb in saved JSON, registry/key_env intact) and m002_sim_v2 (0 abort sites, output identical to pre-fix modulo line numbers). Full record: "# MANGABD-004 — PHASE C" §C6 below.

MANGABD-004 Phase C (this entry): PM directive (Qwen3.8-Max relay, 2026-10-13) — Owner approved implementation of **M4-B1 (OpenRouter exclusive + dead-code purge)** and **M4-B2 (advanced manual copy-paste system)** as one cohesive branch from `main @ 97a683a`, incorporating all Flash Phase B amendments. Implemented across cells {1, 8, 15, 17, 18, 19, 22, 25} (−425/+638 lines, 46 anchored patches, all 19 out-of-scope cells byte-identical). Runtime-proven: cell 8's 15 self-tests pass end-to-end in a fake-globals harness (incl. 6 new B1/B2 tests); full B2 round-trip payload → fenced LLM reply → paste-back → apply 3/3; fresh-run simulator 0 abort sites (M002 baseline preserved). Full record: "# MANGABD-004 — PHASE C" below.

MANGABD-004 Phase A: PM directive (Qwen3.8-Max relay, 2026-10-13) — Owner's 4 core directives audited and proposed, NO implementation code written: (1) OpenRouter-exclusive translation (registry reduction to 1 provider on the V-5 adapter, dead-code removal list, 3-layer API-key UX for Colab); (2) Manual copy-paste promoted to PRIMARY translation with a full professional System Prompt template + clipboard UI proposal, grounded in measured S003 NLLB quality defects; (3) LaMa Large audit — verdict: throttled (lama_size 1024 vs upstream default 2048, every Owner page silently downscaled ~0.85×; proposal: OOM-safe resolution ladder, native-res inference for 844×1200 pages); (4) Qwen2.5-VL-3B OCR audit — pixel budget is NOT the bottleneck (12.8MP default, crops run native-res); levers are the single generic prompt (region-type prompt map proposed), decode safety, saturated heuristic confidence. Full record: "# MANGABD-004 — PHASE A" below (evidence tags FACT/HYPOTHESIS/TEST RESULT; cell:line citations against `mangabd-003-batch3 @ 1753b1a` for cells 1/8/25, `main @ 37dc72e` for all others, zyddnys `d6de6ab` for upstream). Implementation plan M4-B1..B4 proposed, gated on Owner authorization + 7 decision items (A7-D1..D7).

MANGABD-003 status: **BATCH 1 MERGED (`f158091`) · BATCH 2 MERGED (`6ce6cd2`) · BATCH 3 (V-5) IMPLEMENTED on branch `mangabd-003-batch3 @ 1753b1a`, Flash Phase D APPROVED `37dc72e` — **SUPERSEDED by the MANGABD-004 Owner pivot (A7-D1 option b, PM relayed 2026-10-13: S004 skipped, M4-B1/B2 branch from main)**; the V-5 openrouter subset (adapter/registry/key_env/closure/SECRET_SOURCES/translator_model — all Phase-D-proven patterns) was RE-AUTHORED inside M4 rather than transplanted, per the Phase A recommendation. Branches `mangabd-003-batch3` + `mangabd-003-phase-c` preserved untouched as historical byte source.**

(Historical: MANGABD-002 — fresh-Colab execution reliability — **COMPLETE, Phase D verified, merged to main**, closed 2026-09-27; Flash merge re-verification on main PASS `1a0309d`, 2026-10-08; closure record below and in DECISION.md §B.13.)

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

# MANGABD-003 — PHASE C IMPLEMENTATION RECORD — BATCH 1 (GLM-5.3)

**Date:** 2026-09-30 · **Branch:** `mangabd-003-batch1` (WIP, awaiting Flash Phase D) · **Base:** `origin/main @ c2e5754` (linear, single commit on top of base) · **Scope authority:** `agents/TASK_003.md` (Owner task book, this commit's parent) + PM authorization message limiting execution to **Batch 1 (V-4a + V-2 + V-1); Batches 2/3 explicitly not yet authorized**.

## T3.20 Context — how this branch relates to the prior full-scope Phase C

- A prior Phase C implementation covering ALL THREE batches exists on branch `mangabd-003-phase-c` (commit `f58cd3c`) and carries Flash's **Phase E verdict: APPROVED, E1–E6 all PASS, zero required fixes** (review commit `830a552`, 2026-09-29, "sign-off for PM relay"). That branch is **untouched by this work** — no amend, no force-push, no merge; it remains the standing evidence for the Phase E approval and the available byte source for Batches 2/3 when their authorizations arrive. [FACT]
- The Owner subsequently formalized the task book (`agents/TASK_003.md`, main `c2e5754`, 2026-09-30) restructuring execution into **per-batch commits with Flash verification after each batch** ("implementation MUST proceed in this exact order", "VERIFICATION PROTOCOL (Phase D): after GLM-5.3 implements a batch, GLM-5.3-Flash will …"). The PM's authorization implements that structure: Batch 1 first, on a WIP branch, Batches 2/3 withheld. This branch therefore **re-lands Batch 1 from main** rather than building on the all-at-once branch. [FACT]
- Construction policy, stated up front for the auditor: **V-2 (cell 6), V-1 (cells 11/12) and the V-4a samples-docs corrections are transplanted VERBATIM from `f58cd3c`** — those exact bytes already carry Flash's Phase E approval (E4 per-amendment verification + E1 scope audit), so re-deriving them would only create divergence risk; the transplant is sha256-verified below. **The V-4a manual-workflow edits (Edit A + Edit B) are implemented fresh on main's cell-8/cell-22 base** — they were excluded from the prior relayed scope ("V-4b Edits A/B … NOT implemented") and are now MANDATED by TASK_003.md's Strict Amendments ("Implement Edit A … and Edit B … DEFER Edit C"); they exist in no prior commit. [FACT]

## T3.21 Phase D reconciliation (folded in, per protocol) — every Batch-1 amendment re-confirmed against code before implementation

All 5 applicable amendment items **CONFIRMED, zero rebuttals**. Citations use the *physical-cell:line* convention on the pre-edit baseline (main `c2e5754`; notebook blob sha256 `448540f8…` — byte-identical to the MANGABD-002-verified merge, unchanged by `c2e5754` which added only `agents/TASK_003.md`).

| # | Amendment (source) | Verdict | Code evidence |
|---|---|---|---|
| 1 | V-1 amend 1 — scale-vs-fit overflow ladder (Phase B) | **CONFIRMED** (transplant) | Implemented in the `f58cd3c` canonical block; Phase E E4 re-verified the exact while-ladder on these bytes. Presence re-asserted in BOTH cells this session (verify-suite V2). |
| 2 | V-1 amend 2 — baseline alignment `ly_fb = ly + asc_main − asc_fb` (Phase B) | **CONFIRMED** (transplant) | Same bytes; Phase E E4(b) verified the formula; re-asserted in both cells (verify-suite V2). |
| 3 | V-2 — no amendments; document `mask_vpad_vertical` ceiling = `mask_clip_padding` (Phase B note) | **CONFIRMED** (transplant) | Cell-6 band block carries the ceiling comment; re-asserted (verify-suite V3). |
| 4 | V-4 amend 1 — implement Edit A + Edit B (TASK_003.md Strict Amendments) | **CONFIRMED** (fresh) | Baseline sites re-read this session: silent skip at cell-8 `parse_ai_text` 8:845–846 (`if not match: continue`); report block at cell-22 `apply_translations_from_text` 22:235–238; apply-count print at 22:257. Sentinel safety re-derived: `apply_manual_translation` (8:1023–1092) is **df-row-driven** (iterates `translation_df` rows and looks the dict up by key — a `("_unparsed", 0)` entry is never looked up); cell-22's 22:220–233 loop skips empty-sided entries (Bengali-rescue edge lands in `translations` but is inert for the same df-driven reason); upload path 8:995–1005 (`translations.update(parsed)` → same df-driven apply); cell-19:44 loop idiom identical; cell-8 module-level self-tests 8:1549–1586 use a sample with **zero unparsable lines** so a conditional sentinel keeps `len(parsed)==3` true (regression-tested at runtime, V5c). |
| 5 | V-4 amend 2 — DEFER Edit C, do not alter the ai.Text wire format | **CONFIRMED** (deferred) | Not implemented; proven untouched: parse regex 8:843 (`^\[([^:\]]+):(\d+)\]\s*(.*)$`), export header doc 8:878, `_parse_ai_text_local` (cell 22:42+) AST-identical to main; `export_ai_text` / `apply_manual_translation` / `build_translation_records_from_df` / `translate_manual_upload` byte-identical to main (verify-suite V4). |

**Factual precisions recorded for the auditor** (same class as the prior session's notes, no action required): (1) TASK_003.md's batch line reads "V-4a: Manual Workflow Polish (Unparsed-line report only. Edit C is DEFERRED)" while its mandatory Strict Amendments section reads "Implement Edit A (unparsed-line report) and Edit B (pre-render coverage)" — the amendments section is the operative enumeration ("Flash WILL reject the PR if these are missing"), so **both Edit A and Edit B are implemented**; the "only" phrasing is read as contrasting with deferred Edit C. (2) Flash's Phase B batch plan assigns "samples docs" to batch 1, so the V-4a **metadata rev2 corrections are included** (transplanted, see T3.22) even though TASK_003.md's batch line does not re-list them. (3) TASK_003.md numbers the post-batch review **"Phase D"**; the prior flow called the executed all-batch review "Phase E" (commit `830a552`). This record follows the task book's numbering.

## T3.22 Changes (5 files; per-cell single-logical-change honored)

**Notebook** (`MangaBD_V12_ipynb_txt.ipynb (3).txt`, +142/−21 in the JSON text): changed cells = **exactly [6, 8, 11, 12, 22]**; the other **23 cells byte-identical to main** — including cells 1/7/16/25 (Batch 2/3 content absent) and cells 14/26 (MANGABD-002 Phase-D artifacts, guard block + cell-26 bundle, intact verbatim). Within every edited cell only the `source` field changed.

1. **Cell 6 — V-2 vertical band** (TRANSPLANT, byte-identical to `f58cd3c`): `build_page_text_mask` raw-mask branch; band at 6:833–843 (post-edit), after the `mask_clip_to_regions` clip and before `return mask`; `detection_cfg.setdefault("mask_vpad_vertical", 10)`, `if vpad > 0` gate, two filled `cv2.rectangle` bands (column tips) clamped to image bounds; predicate `rw < 90 and rh > 2 * max(1, rw)` on **region** dims; comment documents the effective ceiling = `mask_clip_padding` (cell-9 re-clip).
2. **Cells 11 & 12 — V-1 CJK fallback canonical block** (TRANSPLANT, byte-identical to `f58cd3c`): `get_font_fb` (module-level knobs `fallback_font_wght`/`fallback_cjk_scale`/`fallback_cjk_stroke` setdefaults; wght via OSError-guarded `set_variation_by_axes`, `if bold: wght = max(wght, 700)`) + `_qc_render_vertical` (1.25× scale on fallback runs, stroke 1 with `stroke_fill`, **overflow ladder** `while … total > int(h) - 2*padding and scale > 1.0: scale = 1.12 if scale > 1.12 else 1.0` with re-measure, **baseline alignment** `ly_run = ly if im else ly + asc_main - f.getmetrics()[0]`). Knobs sit at 11:150+ / 12:107+ (post-edit).
3. **Cell 8 — V-4a Edit A (unparsed-line report)** (FRESH): four surgical insertions in `parse_ai_text` (8:812–886 post-edit) — collector init `unparsed = []` (8:833); `unparsed.append(line)` at the former silent skip (8:849–850); sentinel entry before return (8:875–884): `translations[("_unparsed", 0)] = {"original_text": "", "translated_text": "", "unparsed_lines": unparsed}` — present **only when** unparsed lines exist; docstring note (8:826–829). **Parse behavior otherwise unchanged** (same regex, same skip semantics — the line is still excluded from real entries, now counted and carried). **Edit C NOT implemented.**
4. **Cell 22 — V-4a Edit A report print + Edit B coverage report** (FRESH): in `apply_translations_from_text` (22:185–301 post-edit) — (a) at 22:235–243, reads the sentinel (`parsed.get(("_unparsed", 0))`, `isinstance` guard so the `_parse_ai_text_local` fallback path — which has no sentinel — degrades to no report, by design) and prints `⚠️ N unparsed line(s) — check headers/line-wraps: <first 3, 60 ch each>`; the `🔎 Parsed entries` count now **excludes the sentinel** (`len(parsed) - (1 if unparsed_lines else 0)`) so the printed arithmetic stays self-consistent; (b) at 22:267–285 (**after** the `✅ Applied translations` count, **before** the "Next command" hint), Edit B: iterates `translation_df` (guarded on existence), skips empty originals and the six special markers (`[EMPTY]/[OCR_FAILED]/[SFX]/[SKIP:OCR_FAILED]/[TRANS_FAILED]/[UNTRANSLATED]` — same set as `is_special_marker`, cell 8:190–208), flags rows where `_validate_bengali_local(translated_text)` is false (cell 22's own local helper — cell-standalone, NaN-immune, literally "without valid Bengali"), prints `⚠️ M of T regions still without valid Bengali (first 10): page:id list` + a render-safety hint. Page label mirrors the export header (`page` → `page_id` → `?` fallback) so the list matches what the translator sees in ai.Text. **Both blocks are print/report-only** — no df mutation, no wire-format change, no new failure path.

**Samples docs** (TRANSPLANTS, byte-identical to `f58cd3c`): `samples/S001_color_webtoon/metadata.json` (+6/−3) — rev2 (`translation_engine: "nllb"`, `source_type: "B/W manga page"`, `naming_note`, `metadata_revision: 2`, `revision_note`); `samples/S001_color_webtoon/metadata.rev1.json` (+9, new) — rev1 preserved verbatim (sha256 `eabe49b7…`, byte-identical to main's rev1 metadata blob — matches Flash PE.1); `samples/README.md` (+2) — naming-provenance pointer line. The 7 pipeline artifacts (images + 3 sidecars) untouched.

**This file** (agents/GLM_5_3.md): this record + CURRENT PHASE header.

## T3.23 Verification (this session; scripts `phase_c003_b1_build.py` / `phase_c003_b1_verify.py` under GLM-5.3 `scripts/`, outputs re-runnable)

- **Build-time (18 checks, all PASS):** preconditions — notebook base blob sha256 = `448540f8…` (main state); round-trip writer byte-faithful (`json.dumps(indent=2, ensure_ascii=False)`, no trailing newline); `f58cd3c` vs main differ only in cell `source` fields (all 27 cells, all non-source keys compared); every old-block matched EXACTLY ONCE before each edit; every edited cell AST-parses post-edit; Jupyter source-list reconstruction convention validated per edited cell. Post-write: JSON re-parse, 27 cells, all 27 AST-clean; changed-cell set vs main = exactly [6, 8, 11, 12, 22]; **cells 1/7/16/25 byte-identical to main (Batches 2/3 absent)**; **cells 6/11/12 byte-identical to `f58cd3c`** (transplant fidelity — hence Flash's E3 mirror shas `a7d2d5bd…`/`e27f7697…` and E4 amendment verifications describe these exact bytes).
- **Static suite (44 checks, all PASS):** mirror equality re-derived by AST-span extraction — `get_font_fb` 689 ch, sha16 `d285c8f966c96008`, **identical cells 11↔12**; `_qc_render_vertical` 2266 ch, sha16 `90d76499c6748f26`, **identical cells 11↔12** (excludes the 1 trailing newline Flash's span includes — 690/2267 ch; same bytes); all 10 V-1 amendment patterns present in BOTH cells; all 5 V-2 patterns + insertion-point check in cell 6; all 10 V-4a patterns across cells 8/22; Edit-C-deferred proof (regex/header/`_parse_ai_text_local` untouched; `|TYPE` count = 0); `export_ai_text`/`apply_manual_translation`/`build_translation_records_from_df`/`translate_manual_upload` byte-identical to main.
- **Runtime suite (8 scenarios, all PASS; functions exec'd verbatim from the edited notebook, `stdout` captured):** (V5a) mixed content → 3 valid entries + sentinel carrying exactly the 2 unparsable lines; (V5b) all-valid → no sentinel; (V5c) **cell-8 module-level self-test regression** — sample from 8:1551 → `len(parsed)==3`, translations intact (self-test assertion still passes on fresh Run All); (V5d) comment-only → `{}` early-return unchanged; (V6a) end-to-end apply on a synthetic 4-row `translation_df`: return=2, `⚠️ 1 unparsed line(s)` shown with the line text, `Parsed entries: 2` (sentinel excluded), coverage prints `1 of 4 regions still without valid Bengali` listing `03.jpg:1`, **`[SFX]` row not flagged**, df mutated exactly as the real df-driven apply would; (V6b) full coverage → no warning; (V6c) fallback-parser path (`parse_ai_text` absent from globals) → works unchanged, no sentinel report, no crash; (V6d) non-Bengali garbage translation → flagged by coverage.
- **Pre-commit diff audit:** `git diff --numstat` = notebook `142/21`, README `2/0`, metadata.json `6/3`, metadata.rev1.json `9/0` (new file, mode `000000→100644`); all other entries `100644→100644`, zero renames; secret-pattern scan of all 163 added lines (PAT/`sk-`/AKIA/AIza/hf_/PEM/bearer/xox) — **0 hits**; MANGABD-002 artifacts (cells 14/26) byte-identical to main.

## T3.24 Status

**BATCH 1 COMPLETE — WIP, awaiting GLM-5.3-Flash Phase D verification** (TASK_003.md "VERIFICATION PROTOCOL (Phase D)"): no fresh-run regression (m002_sim_v2/m002_flash_repro equivalents), amendment presence, mirror equality, Edit A/B behavior, then the S002 visual acceptance run per the task book. **Batches 2/3 (V-3 cells 7/16; V-5 cells 8/25) are NOT implemented on this branch by instruction** — their Phase-E-approved bytes remain available on `mangabd-003-phase-c @ f58cd3c` for verbatim transplantation when the PM authorizes the next batch. **No amend/merge/push-to-main before Flash sign-off is relayed via PM/Owner** (DECISION.md §C gating + Phase E's relay instruction). Note for the Phase D reviewer: the V-4a Edit A/B changes touch **cell 8 (parse function only) and cell 22** — TASK_003.md's batch plan did not enumerate cells for V-4a; the cell placement follows the Phase A/Phase B-confirmed proposal exactly (Edit A: cell 8 + cell 22; Edit B: cell 22), which adds cell 22 to the batch-1 cell set and makes cell 8 shared with the future batch 3 (different functions, one logical change per batch — the single-hunk convention is honored per batch).

---

# MANGABD-003 — PHASE C IMPLEMENTATION RECORD — BATCH 2 (GLM-5.3)

## T3.25 Context — authorization, branch topology, construction policy

- Authorization: PM assignment (Qwen3.8-Max, 2026-10-08) under `agents/TASK_003.md` — Batch 2 = **V-3: Vertical-Note OCR (Cells 7 & 16) ONLY**; constraints: no cells outside scope, no Batch 1/3 changes, TASK_003.md VERIFICATION PROTOCOL, evidence tags, single-hunk audit per cell. Flash's S002 Batch-1 acceptance (commit `48cdadd`, 2026-10-04) closed the Batch-1 gate and stated "Batch 2 (V-3) may proceed per the task book's batch order." [FACT]
- Branch `mangabd-003-batch2` created from `main @ 0d3bc57` (post-batch-1-merge main: `f158091` squash-merge + `f11a6eb` S002 archive + `48cdadd` Flash S002 acceptance + `0d3bc57` MANGABD-002 TASK_002.md status sync). Notebook base blob sha256 `db86143b…` — cells 6/8/11/12/22 = Batch-1 state (Flash Phase D approved), all others = MANGABD-002-verified state. [FACT]
- Construction policy: **both cells transplanted VERBATIM from `f58cd3c`** (branch `mangabd-003-phase-c`) — those bytes carry Flash's **Phase E verdict** ("batch2 V-3 L1 + L2: PASS — selector redesign + non-blocking flags as amended", E4 + E5b/e runtime). Verified pre-transplant: `f58cd3c`'s cells 7/16 differ from main ONLY in `source`; main's cells 7/16 are byte-identical to `1cd8acf` (f58's parent — the V-3 sites were untouched on main since Phase B); `f58cd3c`'s changed-cell set vs its parent = exactly {1, 6, 7, 8, 11, 12, 16, 25}, so the cell-7/16 deltas are **V-3-only** (single logical change per cell). Zero re-derivation, zero divergence risk. [FACT]
- Note on the PM's amendment list vs the task book: the PM's Layer-1 (a)–(c) + Layer-2 (a)/(b) items map 1:1 onto TASK_003.md's five V-3 Strict Amendments (1→L1a, 2→L1b, 3→L1c, 4→L2a, 5→L2-severity); PM's "(d) Keep Layer 2 as hard net" = the Phase B "keep Layer 2 as the hard net regardless" clause (implemented as the warning-severity safety net that flags regardless of Layer-1 selection). No conflict. [FACT]

## T3.26 Phase D reconciliation (folded in, per protocol) — every V-3 amendment re-confirmed against code before implementation

All 5 TASK_003.md Strict Amendments + both Phase B Layer-2 factual amendments **CONFIRMED, zero rebuttals**. Citations: *physical-cell:line* on the transplant source (`f58cd3c` cell 7 / cell 16), independently re-derived this session from the git blobs (script `phase_c003_b2_reconcile.py`); pre-edit baseline insert points cited on main.

| # | Amendment (source) | Verdict | Code evidence (f58cd3c bytes) |
|---|---|---|---|
| 1 | Drop the upright candidate when the vertical predicate fires — 2 VLM calls, not 3 (TASK_003.md amend 1; Phase B L1a) | **CONFIRMED** | Cell 7 `ocr_region` 7:394–435 (post-edit): candidate tuple = `("rotate_90_clockwise", cv2.rotate(preprocessed, cv2.ROTATE_90_CLOCKWISE))` and `("rotate_90_counterclockwise", …COUNTERCLOCKWISE)` **only** (7:405–410); the upright read is preserved verbatim as the `else:` branch (7:431–432) for non-vertical regions. Runtime: exactly 2 `qwen.recognize` calls for a 61×298 region, upright image never sent (verify A1a–A1c). |
| 2 | Explicit tie-break: strict `>` starting from ROTATE_90_CLOCKWISE (TASK_003.md amend 2; Phase B L1b) | **CONFIRMED** | 7:417–419: `chosen = candidates[0]` (CW is first) then `for cand in candidates[1:]: if cand["score"] > chosen["score"]: chosen = cand` — strict `>`, CW-first, deterministic. Runtime: equal scores → CW wins; CCW strictly greater (1.75 > 1.7) → CCW wins (verify A2/A3). |
| 3 | Audit trail: append chosen orientation + all candidate scores to result warnings / OCR sidecar (TASK_003.md amend 3; Phase B L1c) | **CONFIRMED** | 7:421–430: `vertical_ocr = {"chosen_orientation": …, "candidate_scores": {…}}` + `result.setdefault("warnings", []).append(f"vertical OCR: chose {chosen['orientation']} (candidates: {…})")`; returned in the record as the additive sidecar field `"vertical_ocr": vertical_ocr` (7:465–466; `None` for non-vertical). Runtime: exact dict + warning verified (A1e/A1f). |
| 4 | Cell 16 snippet MUST include `import re` (TASK_003.md amend 4; Phase B L2a — "cell 16 contains no imports") | **CONFIRMED** | Cell 16 artifact-branch snippet 16:371 (`import re  # cell-standalone-safe (Flash Phase B: re not imported in this cell)`) and df-branch snippet 16:396 (`import re`). Both inside the function bodies. Runtime: segments exec'd in a namespace with **no `re`** → both branches work (verify B0). |
| 5 | Layer 2 severity stays "warning" (score penalty only, no abort) (TASK_003.md amend 5; Phase B "hard net") | **CONFIRMED** | Both flags (16:375–387 artifact branch; 16:466–476 df branch) call `add_quality_issue(..., severity="warning", ...)`; `add_quality_issue` (16:142–187) has no raise path, routes warning/critical into `manual_review_flags_dict` → `manual_review_flags` (score penalty via `SEVERITY_WEIGHTS`), never blocks. Runtime: 🟡 routing, no exception (verify B1–B3). |
| 6 | (Phase B factual L2b) df-branch insert has no `region` object in scope — geometry from detection records, not df x/y/w/h | **CONFIRMED** | 16:392–400: `det_geo = {}` + `if "load_json_artifact" in globals(): det_geo = {int(dr.get("id", -1)): dr for dr in load_json_artifact(page_id, "detections", default=[])}`; lookup at 16:462 `geo = det_geo.get(region_id, {})`. Artifact branch keeps `region = item.get("region", {})` (16:292) from the ocr sidecar entries. Runtime: df claims 1000×50, detections truth 61×298 → flag fires from detections (verify B7); loader absent → det_geo={} → predicate false, no crash (B8). |
| 7 | (Phase B, optional) kana-preservation scoring / vertical prompt variant | **NOT IMPLEMENTED — not in the mandated minimum** | Phase B: "(a)–(c) are the mandatory minimum"; the optional kana-score reward and vertical/mixed-script prompt variant were not part of the Phase-E-approved bytes; the default OCR prompt is forwarded unchanged to both candidates (7:407/412 → `prompt=prompt`, verified at runtime A1d). Kept exactly as approved — flagging for the Phase D reviewer's awareness. |

**Factual precision for the auditor:** the predicate at cell 7 (7:403–404: `rw_, rh_ = int(region.get("width", 0)), int(region.get("height", 1)); if rw_ < 90 and rh_ > 2 * max(1, rw_):`) uses **REGION dims** — the Phase B/E-adjudicated form (crop context + overlay border + preprocess padding widen S001 R1 to ~95–113 px, defeating a crop-dims test). Its textual form is semantically identical to the live vertical-renderer predicate (Batch-1 cells 11/12) but not byte-equal as a raw string (var-rename `rw_`/`rh_` + `2 * ` spacing) — Phase E note N2 already adjudicated this class as satisfied. Runtime: predicate fires on region dims even when the crop is wide (verify A5).

## T3.27 Changes (1 file; per-cell single-logical-change honored)

**Notebook** (`MangaBD_V12_ipynb_txt.ipynb (3).txt`, **+84/−1** in the JSON text): changed cells = **exactly [7, 16]**; the other **25 cells byte-identical to main** — including cells 6/8/11/12/22 (Batch 1, Flash Phase D approved + S002-accepted) and cells 14/26 (MANGABD-002 artifacts, intact verbatim). Within both edited cells only the `source` field changed (all non-source cell fields compared across all 27 cells, main vs transplant source).

1. **Cell 7 — V-3 Layer 1** (TRANSPLANT, byte-identical to `f58cd3c`; cell 1072→1112 lines): inside `ocr_region` (def at 7:324) — the single `result = qwen.recognize(preprocessed, prompt=prompt)` call site (main 7:394) is replaced by the vertical-selection block 7:394–435 (rotated-only candidates, per-candidate score = `confidence + language_score.en`, CW-first strict-`>` selection, `vertical_ocr` audit dict, warnings append) + verbatim upright `else:` branch; additive sidecar field `"vertical_ocr"` in the return record 7:465–466. **Everything else in cell 7 is byte-identical to main** (preprocess, clean, status helpers, df builder, page pipeline, module self-tests — which still pass on whole-cell exec). 41 added / 1 removed lines.
2. **Cell 16 — V-3 Layer 2** (TRANSPLANT, byte-identical to `f58cd3c`; cell 1623→1666 lines): inside `inspect_ocr_quality` (def at 16:256) — three pure insertions, zero removals: (a) artifact-branch flag 16:367–387 (`import re` + kana/Latin regexes + composite predicate + `add_quality_issue(severity="warning")`); (b) df-branch geometry resolution 16:392–400 (`import re` + `det_geo` from `load_json_artifact(page_id, "detections")` keyed by `int(dr["id"])`); (c) df-branch flag 16:460–476 (lookup `geo = det_geo.get(region_id, {})` + the same composite predicate + the same warning-severity issue). All other cell-16 content (QA globals, `add_quality_issue`, score weights, other inspectors, fix helpers, module tail) byte-identical to main. 43 added / 0 removed lines.

**This file** (agents/GLM_5_3.md): this record + CURRENT PHASE header. No other files touched; `samples/` untouched.

## T3.28 Verification (this session; scripts `phase_c003_b2_build.py` / `phase_c003_b2_b2_reconcile.py`→`phase_c003_b2_verify.py` under GLM-5.3 `scripts/`, outputs re-runnable, log at `phaseC003b2/verify_log.txt`)

- **Reconciliation preconditions (3 checks, all PASS):** `f58cd3c` vs main differ only in cell `source` fields (all 27 cells); main cells 7/16 byte-identical to `1cd8acf` (base stability — V-3 sites untouched on main since Phase B); `f58cd3c` changed-cell set vs parent = exactly {1, 6, 7, 8, 11, 12, 16, 25} → V-3 confined to 7/16.
- **Build-time (14 checks, all PASS):** base blob sha256 = `db86143b…` (main state); round-trip writer byte-faithful; reconstruction convention validated per transplanted cell; both cells AST-parse; post-write JSON re-parse, 27 cells, all 27 AST-clean; **changed-cell set vs main = exactly [7, 16]**; Batch 1 preserved (cells 6/8/11/12/22 byte-identical to main); Batch 3 absent (cells 1/2/25 byte-identical to main); MANGABD-002 artifacts intact (cells 14/26); transplant fidelity (cells 7/16 byte-identical to `f58cd3c`); **mirror discipline re-verified: `get_font_fb` span 690 ch sha16 `a7d2d5bd61309c78` and `_qc_render_vertical` span 2267 ch sha16 `e27f769797d8ff4f`, byte-identical cells 11↔12 — equal to the Phase D/E records** (Batch-1 mirror untouched by this batch).
- **Runtime suite (16 checks, all PASS; cell 7 exec'd WHOLE from the built bytes with stubbed module boundaries — real cv2 4.13.0 rotations, stubbed `qwen.recognize`/`model_manager`/crop/log; cell 16 segments (`add_quality_issue`, `qa_is_special_marker`, `inspect_ocr_quality`) exec'd verbatim in a namespace WITHOUT `re`):**
  - A0 whole-cell exec of built cell 7 completes — module dependency checks + config defaults + **cell-7 self-test battery 6/6 SUCCESS** (incl. `translation_df column compatibility`, seeded from cell 3's `TRANSLATION_DF_COLUMNS` as a fresh Run All would have).
  - A1a–g (real S001 detections.json region 1, 61×298 overlay): exactly 2 VLM calls; call order [CW, CCW] **proven by image bytes** (each received image `np.array_equal` to `cv2.rotate(preprocessed, ROTATE_90_*)`, preprocessed recomputed via the exec'd cell's own `preprocess_for_ocr`); upright image NEVER sent; default prompt forwarded to both; `vertical_ocr` dict exact (`{"chosen_orientation": "rotate_90_clockwise", "candidate_scores": {"rotate_90_clockwise": 1.7, "rotate_90_counterclockwise": 1.7}}`); warning names chosen orientation + both scores; result text = chosen candidate's text.
  - A2 tie → CW wins (strict `>`); A3 CCW 1.75 > 1.7 → CCW wins + its text returned; A4a–d wide region (100×300): exactly 1 upright call, image unrotated, `vertical_ocr is None`, no vertical warning; A5 vertical region + WIDE crop (300×100) → predicate still fires (region-dims, 2 rotated calls).
  - B0 segments exec in namespace without `re` (cell-standalone-safe import); B1 **real S001 ocr.json + detections.json**: V-3 flag fires exactly once (region 1), severity "warning", category "ocr", routed to `manual_review_flags` as 🟡 with no 🔴; B4–B6 negative controls: pure-Latin / wide-region / pure-kana → no flag (composite predicate needs kana AND Latin AND vertical geometry); B7 df branch: flag fires from DETECTIONS geometry (df row claims 1000×50, det truth 61×298); B8 `load_json_artifact` absent → `det_geo={}` → no flag, no crash.
  - C0 predicate census: cell 7 bare predicate ×1, cell 16 composite (`… and has_kana and has_latin`) ×2; C-S001/C-S002 grounding over the real archived detections: vertical predicate fires **exactly for region 1 (61×298)** in both samples (region 2 87×156 correctly silent: 156 < 174).
- **Pre-commit diff audit:** `git diff --numstat` vs main = notebook `84/1` (single file); raw diff single `M` entry, mode `100644→100644`, zero renames; secret-pattern scan of all 84 added lines (PAT/`sk-`/AKIA/AIza/hf_/PEM/bearer/xox/glab) — **0 hits**; working tree clean apart from the notebook + this record.

## T3.29 Status

**BATCH 2 COMPLETE — WIP on branch `mangabd-003-batch2`, awaiting GLM-5.3-Flash Phase D verification** (TASK_003.md "VERIFICATION PROTOCOL (Phase D)"): fresh-run regression check (m002_sim_v2/m002_flash_repro equivalents), amendment presence (5/5 + 2 Phase-B factual, this record T3.26), runtime behavior of the selector and both flags, then the **S003 visual acceptance run** proving the region-1 OCR fix on a fresh sample (Owner-side, live Colab + live `qwen.recognize`; N-S2-A recorded that S002's region-1 OCR is still misread — exactly the V-3 target). **Batch 3 (V-5, cells 8/25) NOT implemented** — its Phase-E-approved bytes remain on `mangabd-003-phase-c @ f58cd3c` for transplantation when the PM authorizes. **No amend/merge/push-to-main before Flash sign-off is relayed via PM/Owner** (DECISION.md §C gating). Known non-blocking notes carried from Phase E for the reviewer: N3 (flag regex covers kana + CJK Ext-A, not the main CJK block 4E00–9FFF — kanji-only vertical notes won't flag; consistent with the S001 failure mode), N4 (sandbox boundary — live `qwen.recognize` confidence semantics are Owner-side validation), N-S2-A (S001/S002 region-1 OCR texts still carry the misread this batch fixes; Layer 2 will flag them for mandatory manual review even where Layer 1's rotated reads may still err).

---

# MANGABD-003 — BATCH 2 PHASE D APPROVAL RECEIPT & GATE STATUS (GLM-5.3, docs sync — no source changes)

## T3.30 Phase D approval acknowledged; merge gate = Owner S003 (2026-10-09)

- **Flash Phase D verdict (received on this branch): APPROVED.** Commit `74f5d8c` (2026-10-08), 69 lines appended to `agents/GLM_5_3_FLASH.md` on top of WIP `5e87050`. Instrument result: **D1 28 + D3 15 + D6 30 + D8 35 = 108/108 PASS, zero required fixes.** D1: changed cells exactly {7,16}; transplant fidelity to `f58cd3c` (sha16 `4522a89c18f5ee8d` / `e31bfdc3a03ec9e2`); Batch 1 {6,8,11,12,22} + Batch 3 {1,25} + MANGABD-002 {14,26} cells byte-identical to main; secret scan 0 hits. D3: mirror no-drift (`get_font_fb` `a7d2d5bd61309c78`, `_qc_render_vertical` `e27f769797d8ff4f`, cells 11↔12). D6: all 5 TASK_003 V-3 Strict Amendments + both Phase B Layer-2 factual amendments implemented (optional kana-scoring/prompt variant correctly absent). D8: verbatim exec of the pushed bytes — exactly 2 VLM calls for vertical regions (rotation bytes proven via `np.array_equal`), tie → CW, strict-greater → CCW, predicate boundary strictness, records-branch + df-branch flags with negative controls, **0 abort sites** (guard equivalence with main carries the Phase-D-approved M002 matrix). D9: my self-report T3.25–T3.29 checked against Flash's independent measurements — **all consistent, no unsupported claims found.** [FACT]
- **Non-blocking reviewer notes acknowledged, no action required this session:** N-B2-1 (Flash instrument self-corrections — no repo impact); N-B2-2 (candidate score = `confidence + language_score["en"]` — an English-ness proxy applied comparatively to both rotated candidates; semantically unusual but sound, matches the approved bytes — Owner awareness); N-B2-3 (kana regex covers kana + CJK Ext-A, not the main CJK block 4E00–9FFF — kanji-only vertical notes will not flag; carried from Phase E N3); N-B2-4 (records-branch `import re` executes per loop iteration — harmless, style-only). [FACT]
- **Gating honored — no amend / no merge / no push-to-main.** Flash's Phase D record: "GLM-5.3 must NOT amend/merge until Owner acceptance is relayed via PM/Owner. Merge gate = Owner-side S003 visual acceptance run (live Colab + live `qwen.recognize`) proving the region-1 OCR fix on a fresh sample — TASK_003 protocol item 2, same pattern as Batch 1 (`a007581` → S002 `48cdadd`)." The Owner's 2026-10-08 directive defers T-8 (live Run-All) to the next live session. The WIP commit message stays as-is until the Owner's merge authorization; this sync is a NEW docs-only commit. [FACT]
- **MANGABD-002 (PM Task 1) confirmed closed:** Flash merge verification on main `1a0309d` (2026-10-08) — M1–M5 all PASS (main contains the finalization; 0 abort sites maintained; docs accurate; zero unintended changes); **MANGABD-002 remains CLOSED**, cells 14/26 stay the protected baseline. Local mirrors synced ff-only this session: main → `1a0309d`, this branch → `74f5d8c`, `mangabd-003-phase-c` → `830a552`. [TEST RESULT]
- **S003 preparation for the Owner's live session (for PM relay):** run branch `mangabd-003-batch2` @ `74f5d8c`, same `02.jpg` page (carries the region-1 vertical note — N-S2-A: S001/S002 region-1 OCR still misread, the exact V-3 target), fresh Run All with live `qwen.recognize`. Acceptance evidence to look for: region-1 OCR reads the rotated note correctly; `vertical_ocr` audit (chosen orientation + candidate scores) present in the OCR sidecar + warnings; Layer-2 🟡 flag on any residual misread; zero regressions elsewhere. Archive per the S002 pattern (extract → verify → metadata.json + README pointer → remove ZIP from root) as `samples/S003_batch2/`. After Owner acceptance: amend WIP → final message, squash-merge to main, DECISION.md record, branch cleanup — Batch 1 precedent. [ASSUMPTION: S003 archive id/naming follows the S002 pattern; final naming at Owner's discretion]
- Batch 3 (V-5, cells 8/25) remains unauthorized; Phase-E-approved bytes stay on `mangabd-003-phase-c @ f58cd3c`+`830a552` for transplantation when the PM authorizes. [FACT]

---

# MANGABD-003 — BATCH 2 MERGE COMPLETION RECORD (GLM-5.3)

## T3.31 Batch 2 merged to main; branch deleted; Batch 3 gated (2026-10-11)

- **Merge executed per the Owner's numbered directive** (relayed via PM Qwen3.8-Max, 2026-10-11) on Flash's S003 acceptance verdict **BATCH2 ACCEPT** (`352c16b`, 2026-10-11 14:34 UTC; full 52-line record read before acting). All four gates verified PASS: **G1** V-3 sidecar audit (region-1 `vertical_ocr` field, corrected reading "Otearai is spelt as おてあらい…", zero occurrences of the S001/S002 misreads "Otarumi"/"おたるみ"/"しゅ", 1.95/1.95 tie resolved CW per the strict-`>` tie-break, code↔artifact semantics match at `671e5d3`, regions 2–6 `vertical_ocr: null`); **G2** 🟡 manual-review flag fires exactly once on R1 (routed to `manual_review_flags` only, all 6 regions `status: ok`, pipeline ran to completion); **G3** regions 2–6 pixel-identical (diff = 0 exactly), `text_mask.png` byte-identical to S002, out-of-quad deltas = JPEG 8×8 block spill hugging the R1 quad boundary only; **G4** V-2 mask band x[10..71] fully active (62/62 columns) + V-1 dark CJK ink mean 14.2 ≤ 60. [FACT]
- **Pre-merge state verified this session:** local main fast-forwarded `28da345` → `352c16b` (ff-only); branch head `671e5d3` with the notebook blob `98b1e73…` byte-identical across `5e87050`/`74f5d8c`/`671e5d3` (the two post-WIP commits are docs-only) — i.e. exactly the bytes Flash Phase-D-approved (D1 transplant-fidelity sha16 `4522a89c18f5ee8d` / `e31bfdc3a03ec9e2`) and S003-accepted. Merge-base = `0d3bc57`. [TEST RESULT]
- **Squash-merge + conflict resolution:** `git merge --squash origin/mangabd-003-batch2` — the notebook and this file staged clean; `agents/GLM_5_3_FLASH.md` hit the expected append-conflict (both sides appended Flash records at the file end since `0d3bc57`: main `1a0309d` M002-verification + `352c16b` S003-acceptance; branch `74f5d8c` Batch-2 Phase D). Resolved by the persisted script `b2_merge_resolve.py` (outside the repo): pure-append verification (base is a byte-prefix of all three sides), blocks reassembled in commit-date order `1a0309d` (Oct 8 21:04) → `74f5d8c` (Oct 8 21:05) → `352c16b` (Oct 11 14:34), **155/155 appended lines preserved (34 + 69 + 52)**, all three section headers + verdicts present and ordered, zero conflict markers. [TEST RESULT]
- **The "amend the WIP commit" directive is effectuated by the squash itself** (Batch 1 precedent `f158091`): the WIP `5e87050` bytes land on `main` exactly once, inside the single merge commit carrying the final message "MANGABD-003 Batch 2: V-3 vertical-note OCR — Flash Phase D approved (74f5d8c), S003 visual acceptance (352c16b)"; the branch's intermediate messages never reach `main`, and the branch is deleted immediately after the merge. [FACT]
- **Squash commit contents (5 files):** notebook +84/−1 (changed cells exactly {7, 16}; the other 25 cells byte-identical to `0d3bc57` — Batch-1 {6, 8, 11, 12, 22}, Batch-3-absent {1, 2, 25}, MANGABD-002 artifacts {14, 26}); `agents/GLM_5_3.md` (T3.25–T3.30 from the branch + this T3.31 + CURRENT PHASE header); `agents/GLM_5_3_FLASH.md` +69 (the Phase D record, chronologically ordered); `agents/DECISION.md` (STATUS header, Batch-2 merge paragraph, "modified exactly three times" correction, new §C.6 Batch 2 Merge Record); `samples/README.md` (S003 pointer row updated to the merged state following the S002-row pattern — 1 line, disclosed). Branch `mangabd-003-batch2` deleted (local + remote) after the push; `mangabd-003-phase-c` (`f58cd3c` + `830a552`) preserved untouched as the Batch-3 byte source. [FACT]
- **Pre-commit audit:** single `M` entry per file, all modes 100644, zero renames; secret-pattern scan (PAT/`sk-`/AKIA/AIza/hf_/PEM/bearer/xox/glab) of all added lines — 0 hits; working tree clean after the commit. The merge commit hash is reported in the PM relay (this record sits inside the merge commit and cannot self-cite). [TEST RESULT]
- **Batch 3 (V-5: Provider-Flexible Translation, cells 8 & 25): PLANNING PHASE ONLY — implementation gated on explicit Owner authorization.** Transplant source: `mangabd-003-phase-c @ f58cd3c` (Phase-E-approved V-5 bytes; Flash E4/E5 runtime records). Phase A proposal: DECISION.md §C.2 V-5 row — provider registry in CONFIG (OpenAI/Qwen/DeepSeek/Ollama/OpenRouter, all OpenAI-compatible endpoints) + one ~35-line `translate_with_provider` adapter on the already-required OpenAI SDK + dispatcher `elif` + dynamic `switch_translator` + UI options + `translator_model` in sidecars + prompt upgrade (profanity/idiom/register rules) + "! !" punctuation normalizer; LiteLLM rejected (dependency weight vs Colab fresh-run reliability). Open Owner items (§C.3): per-provider default models for the registry; S004 translation provider choice. Intended protocol when authorized: same batch pattern — branch from this merge commit, verbatim transplant of cells 8/25, Flash Phase D, Owner S004 acceptance run, merge on authorization. [FACT]
# MANGABD-004 — PHASE A: INVESTIGATION & ARCHITECTURAL PROPOSAL (GLM-5.3, 2026-10-13)

PM directive received (Qwen3.8-Max relay, 2026-10-13): deep-dive investigation + Phase A architectural plan for the Owner's 4 core directives (OpenRouter-exclusive translation; manual copy-paste as PRIMARY translation method with a professional system prompt; LaMa Large full-potential audit; Qwen2.5-VL-3B OCR audit). **No implementation code written this phase** — source notebook and all other agent files untouched; this file is the sole deliverable location, per the directive.

## A0 Evidence conventions & audit references

- Evidence tags follow this log's standing convention: FACT / HYPOTHESIS / TEST RESULT / ASSUMPTION / UNKNOWN (defined at file head).
- **Cell citations** `cell N:L` = 0-indexed notebook cell index, line number within that cell's source. Cells **1, 8, 25** are cited against **`mangabd-003-batch3 @ 1753b1a`** (the V-5 state, Flash Phase D approved `37dc72e`; the most advanced provider code in existence and the direct starting point for MANGABD-004). All other cells are **byte-identical** on `main @ 37dc72e` and the branch (verified: Flash Phase D D1 + re-verified this session by extraction — only cells 1/8/25 differ, +6/+80/−1/+19/−1 lines respectively), so their citations are valid on both refs.
- **Upstream citations** `zy:<path>:L` = zyddnys/manga-image-translator, default branch HEAD **`d6de6ab` (2026-10-11)**, fresh shallow clone made this session. NOTE: cell 4 clones `--depth 1` and `git pull`s on every run (cell 4:226–248) — the Colab copy tracks upstream HEAD unpinned; see A4.6.
- **Artifact citations** `S003` = `samples/S003_batch2/` on main (the Owner's most recent live acceptance run, 2026-10-11; 6 regions, page 844×1200).
- Every quantitative VRAM/latency claim in A4/A5 that could not be executed in this (CPU-only) sandbox is tagged HYPOTHESIS with a concrete Phase B/D measurement plan; nothing below requires trust in unmeasured numbers for the architectural decisions.

## A1 Baseline snapshot (2026-10-13)

- `origin/main` = `37dc72e` (Flash: MANGABD-003 Batch 3 V-5 **PHASE D APPROVED**; scope exactly {1,8,25}; V-4a sentinel intact; 3 Phase B amendments runtime-proven; defaults authorized; 0 abort sites; **merge gate = Owner S004**). Local main fast-forwarded and verified this session. [FACT]
- `mangabd-003-batch3` = `1753b1a` (WIP, remote-verified) — the V-5 implementation awaiting S004. `mangabd-003-phase-c` = `830a552` (byte source, preserved). [FACT]
- MANGABD-003 merged so far: Batch 1 (`f158091`) + Batch 2 (`6ce6cd2`). MANGABD-002 closed. Notebook: 27 code cells, 0 markdown. [FACT]
- **Interaction flagged immediately (decision item D1, A7):** the MANGABD-004 pivot supersedes most of V-5's multi-provider surface (4 of 5 registry providers + gemini/chatgpt/nllb natives get deleted), while V-5's *OpenRouter-specific* payload (adapter, `key_env` discipline, closure dispatcher, SECRET_SOURCES pattern, translator_model sidecar) is precisely the seed M4 builds on. Running the originally-planned S004 (multi-provider acceptance) would spend an Owner live session validating code that M4-B1 immediately deletes. Options and recommendation: A7-D1. [FACT + recommendation]

---

## A2 Directive 1 — OpenRouter-exclusive translation architecture

### A2.1 Current provider inventory (complete, with citations)

**Cell 8 (Translation Service, 1827 lines @ 1753b1a):**

| Element | State | Citation |
|---|---|---|
| Default engine | `"manual"` | cell 8:70 |
| `gemini_model` / `openai_model` config | set (gemini-2.5-flash / gpt-4o-mini) | cell 8:77–78 |
| Provider registry (5 providers, all OpenAI-compatible) | openai / qwen / deepseek / ollama / **openrouter** | cell 8:86–97 |
| NLLB config block (model_id, lang codes, beams, max_length) | set (facebook/nllb-200-distilled-600M) | cell 8:114–122 |
| `translate_with_gemini` (google-genai SDK) | 38 lines | cell 8:446–483 |
| `translate_with_chatgpt` (openai SDK, native) | 52 lines | cell 8:494–545 |
| `translate_with_provider` (openai SDK, registry-driven) | 29 lines | cell 8:551–585 |
| NLLB trio (`get_nllb_bengali_bos_id` / `ensure_nllb` / `translate_with_nllb`) | 167 lines | cell 8:589–756 |
| Dispatcher branches | gemini :803, chatgpt :810, nllb :817, providers :824–832 (closure), unknown :834 | cell 8:763–841 |
| `switch_translator` valid_engines (legacy 4 + dynamic registry) | 7+ engines | cell 8:844–870 (list at 850–852) |
| `translator_model` sidecar resolution (registry lookup + row override) | additive V-5 | cell 8:1229–1238 |
| Cell-8 self-tests incl. fake-SDK provider tests | V-5 test suite | cell 8:1584–1757 |

**Cell 25 (Control Studio v4, 459 lines):** engine buttons `btn_gemini`/`btn_nllb`/`btn_provider` (cell 25:267–269); `mode_sel` 7 options (cell 25:276–283); `gemini_key` Password widget (cell 25:294–295); `on_gemini` (key capture + forced run, cell 25:345–353); `on_nllb` (cell 25:354–361); `on_provider` (engine from `mode_sel`, cell 25:362–370); button wiring (cell 25:409–414); `rebuild_mode_panel` gemini/provider/nllb panels (cell 25:416–433). [FACT]

**Cell 1 (Config/Secrets):** `MANGABD_SECRETS` init {gemini, openai, hf} (cell 1:383–387); `SECRET_SOURCES` 6 key families + ollama-absent comment (cell 1:407–417); bootstrap loop env→userdata→secrets + primary-env export (cell 1:419–440); **`save_config` sanitizer strips any dict key containing api_key/token/secret/password** (cell 1:529–576, forbidden list at 540–545). [FACT]

**Other cells:** cell 19 hotfix = manual-translation rescue (cell 19:22+) **plus a runtime override of `translate_with_nllb`** (cell 19:93–157, the "src_lang fix"); cell 15 `quick_start_auto(engine="gemini")` default (cell 15:898); cell 18 printed command examples incl. gemini/chatgpt/nllb (cell 18:599, 971–973); cell 17 secret-leak self-test is gemini-key-specific (cell 17:955–975); cell 3 `TRANSLATION_DF_COLUMNS` carries `translator_engine` as a *value* column — no schema change needed for any engine consolidation (cell 3:123–145). [FACT]

### A2.2 Findings

- The V-5 architecture is already **one OpenAI-compatible adapter + a registry** (cell 8:551–585): OpenRouter-exclusivity is a *registry reduction*, not a rewrite. The openrouter entry (cell 8:95–96) is exactly the M4 target shape: `base_url https://openrouter.ai/api/v1`, `model openai/gpt-4o-mini`, `key_env openrouter_api_key`. [FACT]
- **The key cannot live in `MANGABD_CONFIG`**: `save_config` runs at cell 1:602 immediately and recursively strips any key containing "api_key" (cell 1:540–545) — an in-CONFIG key would be silently deleted on the first save. This is why V-5 used `key_env` + `MANGABD_SECRETS` (Flash Phase D D2 runtime-proven). Any M4 key UX must write to `MANGABD_SECRETS` / env / Colab userdata — never CONFIG. [FACT]
- The Colab userdata bootstrap (cell 1:419–440) already resolves `OPENROUTER_API_KEY` from env or the userdata secret of the same name, exports it to the environment, and prints loaded/not-set status — but as ONE line among six in a log-style block (cell 1:438–440), which the Owner evidently does not find discoverable enough (the directive's "without digging" complaint). [FACT]
- A working in-UI key-entry precedent exists and is proven on mobile: the `gemini_key` Password widget + capture in `on_gemini` (cell 25:294–295, 345–347). [FACT]
- Native gemini/chatgpt adapters and the whole NLLB stack (cell 8:589–756 + cell 8:114–122 + cell 19:93–157 + cell 25 branches) become dead code under exclusivity; NLLB is additionally policy-deprecated (DECISION.md L554, "NLLB not used per policy"; relabeled "(experimental)" in cell 25:280 during V-5). [FACT]
- zyddnys upstream itself has moved to OpenAI-compatible-ecosystem translators (zy:requirements.txt pins `transformers==5.19.0`; recent commit "restrict ChatGPT to GPT-6 Luna", `d6de6ab`) — irrelevant to M4 directly, but confirms the ecosystem direction: single OpenAI-compatible client, many endpoints. [FACT]

### A2.3 Proposed target architecture (Phase B design, not yet implemented)

**Registry (cell 8:86–97 →):** reduce to exactly one provider:

```python
MANGABD_CONFIG["translation"].setdefault("providers", {
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",
                   "model": "openai/gpt-4o-mini",          # Owner-editable default
                   "key_env": "openrouter_api_key"},
})
```

- `translate_with_provider` (cell 8:555–585) is retained **verbatim in shape** — it already routes any registry entry through the OpenAI SDK with per-provider base_url/model. Two OpenRouter-specific additions proposed: (a) **attribution headers** via `OpenAI(..., default_headers={"HTTP-Referer": <repo-or-colab-url>, "X-Title": "MangaBD V12"})` — optional, OpenRouter-app identification; (b) log `response.usage` token counts into `log_event` for cost visibility. Both are additive and fail-soft. [HYPOTHESIS: exact header names/usage field per current OpenRouter docs to be re-verified at Phase B implementation time — the SDK `default_headers` kwarg itself is standard OpenAI-SDK API.]
- **Optional (config-gated, default OFF): server-side model fallback** — OpenRouter supports a `models` array (ordered fallback list) on the chat-completions request, passable through the SDK as `extra_body={"models": [...]}`. Proposal: `MANGABD_CONFIG["translation"]["openrouter_fallback_models"] = []` — empty = off. This gives the Owner free resilience (e.g. primary + 1 cheaper fallback) with zero code branching. [HYPOTHESIS: API shape to verify against live OpenRouter docs in Phase B; the config knob itself is inert when empty.]
- **Dispatcher (cell 8:763–841):** delete gemini/chatgpt/nllb branches; keep the provider-closure branch (cell 8:824–832, Flash Phase B amendment 1 — the closure binding MUST be preserved verbatim to keep the `translate_with_retry` signature untouched). Unknown-engine `else` stays. `switch_translator` (cell 8:844–870) keeps its dynamic valid_engines construction — it collapses automatically to `["manual", "openrouter"]` when the registry shrinks, zero logic change. [FACT: mechanics; the collapse follows from cell 8:850–852 reading the registry keys.]
- **`translator_model` sidecar (cell 8:1229–1238):** unchanged — registry lookup for the openrouter engine keeps working; manual rows leave it empty as today. [FACT]
- **Default model:** keep `openai/gpt-4o-mini` (the Owner-selected Batch-3 default, cell 8:96) unless the Owner names another; the model becomes a first-class visible field in the Studio (A2.4) so changing it is a UI action, not a code edit. [ASSUMPTION: Owner retains gpt-4o-mini as default until told otherwise.]

### A2.4 API-key UX for Colab (the "highly visible, easily accessible" requirement)

Constraint recap: the key may live in (a) Colab userdata secret `OPENROUTER_API_KEY` (persistent across sessions, set via the 🔑 sidebar or `userdata.set()`), (b) an env var, (c) `MANGABD_SECRETS` (kernel session only) — never CONFIG (sanitizer, cell 1:540–545). [FACT]

**Proposal — three reinforcing layers, ordered by discoverability:**

1. **Control Studio "STEP 0 · 🔑 OPENROUTER KEY" panel** (top of the Studio, above STEP 1–2; cell 25:443–451 assembly): a `Password` widget + two buttons — "💾 Save for this session" (writes `MANGABD_SECRETS["openrouter_api_key"]` + `os.environ["OPENROUTER_API_KEY"]`, mirroring cell 25:345–347's proven gemini capture) and "🔐 Save to Colab Secrets (persistent)" (`userdata.set("OPENROUTER_API_KEY", value)` in try/except with a plain-language fallback message) — plus a status line showing ✅ loaded / ⚪ not set (read from `MANGABD_SECRETS` at panel build). This is the single most discoverable surface the notebook has (the Studio is the Owner's actual cockpit; S003 metadata's `pipeline_variant` = "fresh Run All + Control Studio UI"). [FACT: Studio is the cockpit; HYPOTHESIS: `userdata.set()` interactive confirmation behavior on current Colab needs one live check in Phase B/D — if the dialog is unavailable, button 2 degrades gracefully to instructions text.]
2. **Cell 1 startup banner:** when `openrouter_api_key` is not loaded, the secrets section (cell 1:437–441) prints a 3-line boxed instruction naming the exact secret name and the 🔑-sidebar path, plus "or use STEP 0 in the Control Studio below" — turning today's one-line "⚪ not set" log into an actionable prompt. [FACT: current one-line behavior at cell 1:440.]
3. **Model field in the provider panel:** the STEP 3 openrouter panel (today cell 25:426–429, a static hint) gains a small `Text` widget pre-filled from the registry model, applied on the translate click (`MANGABD_CONFIG["translation"]["providers"]["openrouter"]["model"] = value`) — so "route to any model" is a one-widget action, matching the Owner's stated intent of switching Gemini/Claude/GPT/DeepSeek freely. [FACT: intent is the directive's own words; mechanics are the existing widget pattern.]

Rejected alternatives: (a) key-as-CONFIG-literal — impossible (sanitizer, above); (b) key pasted into the notebook's first cell as a Python string — persists in the .ipynb file itself = secret-at-rest in a file the Owner shares/versions; the userdata/widget paths keep the key out of the notebook bytes (cell 1:443 already promises "Secrets CONFIG বা manifest-এ save হবে না"). [FACT + judgment]

### A2.5 Dead-code removal list (Phase B, cell-level)

- cell 8: `gemini_model`/`openai_model` defaults (77–78); registry entries openai/qwen/deepseek/ollama (86–94); NLLB config (114–122) + NLLB print line (154); `translate_with_gemini` (446–483); `translate_with_chatgpt` (494–545); NLLB trio (589–756); dispatcher branches gemini/chatgpt/nllb (803–822); V-5 self-tests covering removed engines (subset of 1584–1757 — prune per-branch, keep provider/closure/sanitizer/sidecar tests).
- cell 19: `translate_with_nllb` override (93–157) — the rescue-manual half (cell 19:22+) STAYS.
- cell 25: `btn_gemini`/`btn_nllb` (267–268); `gemini_key` (294–295); `mode_sel` 5 removed options (276–281); `on_gemini`/`on_nllb` (345–361); wiring tuples (409–414); mode panels gemini/nllb (424–425, 430–431).
- cell 15: `quick_start_auto` default engine → "manual" (898). cell 18: command-example text (599, 971–973) → manual/openrouter only.
- cell 1: `SECRET_SOURCES` trimmed to `{openrouter_api_key, hf_token}` (407–417 — **hf_token must stay**: RT-DETR/Qwen/LaMa weights download via HF, cell 5:777–787); `MANGABD_SECRETS` init trimmed (383–387).
- cell 17: generalize the secret-leak self-test's key name (965–967) from gemini to openrouter.
- **Deliberately NOT removed:** `manual` engine plumbing, cell 22, cell 20/21, V-4a `_unparsed` sentinel (cell 8:881–951), `apply_manual_translation`, closure dispatcher, retry helper, glossary system (feeds the A3 system prompt), `export_ai_text`. [FACT: all cited]

Estimated net diff (A2 + A3.4 UI together, single batch): notebook ≈ −260/+180 lines across cells 1/8/15/18/19/22/25 — the largest single batch in project history, hence the split recommendation in A6. [HYPOTHESIS: line estimates ±20%.]

### A2.6 Risks & compatibility

- **Squash-merge lineage:** M4-B1 must branch from a decided base (A7-D1: `main @ 37dc72e` if V-5 is superseded, or post-S004 main if Batch 3 merges first). The V-5 bytes on `mangabd-003-batch3` are NOT re-transplantable verbatim under exclusivity (they contain the 5-provider registry) — the openrouter subset is small enough to re-author cleanly inside M4 code. [FACT: registry size; judgment: re-author.]
- **Sidecar/consumer compatibility:** `translator_engine` values "gemini"/"chatgpt"/"nllb"/provider names appear in existing artifact JSONs (S003 translation.json shows `engine=nllb`). Old artifacts remain readable (values are strings; nothing switches on them at load). `switch_translator("nllb")` post-M4 → rejected by the dynamic list (cell 8:854–859) with the existing WARN — correct degradation. [FACT: mechanics; no consumer parses engine names except logs.]
- **Colab secret-name continuity:** the `OPENROUTER_API_KEY` userdata name is already what cell 1 bootstraps (cell 1:416) — no renaming, existing saved secrets keep working. [FACT]
- **Fresh-run regression surface (M002 baseline):** all deletions are function-defs + dict entries inside cells 1/8/25/19; the abort-class simulator baseline (0 sites on `37dc72e`-lineage) must be re-run in Phase D. Flash's D-pattern (scope sha16 per changed cell + guard-equivalence S1–S6) applies unchanged. [FACT: protocol; HYPOTHESIS: no new abort sites introduced — verified in Phase D.]

---
## A3 Directive 2 — Manual copy-paste as PRIMARY translation, with professional System Prompt

### A3.1 Current copy-flow audit (what the Owner actually copies today)

Three parallel paths produce the "copy" payload, all bare (no system prompt anywhere):

1. **Control Studio (primary path):** `build_ai_text_content()` (cell 25:153–165) builds `# MangaBD V12 — ai.Text` + `# Format: [page:id] English → বাংলা` + per-page `# ═══ Page: ... ═══` comment banners + `[page:id] English →` lines (OCR-failed → `[SKIP:OCR_FAILED]` sentinel, cell 25:162). `btn_load_src`/`on_load_src` (cell 25:263, 318–319) pours this into `ta_src`, a **disabled** Textarea the Owner must manually select with mouse/finger and Ctrl+C — there is no copy button and no clipboard integration. Paste-back: `ta_tgt` + `on_apply` (cell 25:336–344) → `apply_translations_from_text`. [FACT]
2. **Standalone cell 22:** `show_text_for_translation()` (cell 22:107–182) prints the export between `──── COPY FROM BELOW ────` / `──── COPY UNTIL HERE ────` banners (cell 22:166–170) — same bare format, plus triple-quote paste instructions. [FACT]
3. **File export:** `export_ai_text()` (cell 8:954–1057) writes `ai_text_export.txt` + JSON sidecar with the same header (cell 8:991–998). [FACT]

**The paste-back side is already robust** — this is a strong foundation for the external-LLM round-trip: `parse_ai_text` (cell 8:881–951) tolerates `#` comment banners (skipped, 913–914), uses LAST-arrow split `rsplit("→", 1)` (929–931) so arrows inside the English text survive, and quarantines malformed lines under the V-4a `("_unparsed", 0)` sentinel (941–949) which `apply_translations_from_text` surfaces as a visible warning with the first 3 offending snippets (cell 22:235–243). The cell-22 local parser additionally accepts 5 arrow variants `→ ➔ ➡ -> =>` (cell 22:59, 84–90) — LLMs frequently emit ASCII `->` — and the rescue path accepts Bengali-on-the-left (cell 22:230–233). [FACT]

### A3.2 Evidence — why manual-external-LLM becomes primary (the quality case, measured)

S003's live NLLB output (the current best automated engine the Owner has run) demonstrates exactly the "robotic literal translation" failure the directive targets (samples/S003_batch2/translation.json, all 6 regions, engine=nllb): [FACT]

| Original (OCR) | NLLB Bengali | Defect class |
|---|---|---|
| "WHO THE FUCK IS OTEARAH!? DOES THAT BITCH KNOW HIM OR SOMETHING!!?" (R5) | "কে ঐ **যৌনসঙ্গম** OTEARAH! ! এই বেশ্যা তাকে বা কিছু জানেন! ?" | Profanity translated as a clinical anatomy term ("sexual intercourse"); broken punctuation "! !" and "! ?"; ungrammatical "তাকে বা কিছু জানেন" |
| "MY NAME'S KOGANEI YOU DUMBASS!" (R3) | "আমার নাম কোগানাই, তুমি **বোকা**!" | Insult softened to "you are silly" (childish register) |
| "WHO THE HELL IS THAT PERSON!?" (R4) | "সেই ব্যক্তি কে?" | Intensity ("the hell", "!?") dropped entirely; stiff word order |
| T/L note R1 | Bengali translation of a *meta* translator note, kana preserved mid-sentence with OCR's stray ")" | Note treated as dialogue; glossary/romanization conventions absent |

A strong external chat LLM with a proper persona prompt handles register, profanity and idiom far better than a 600M seq2seq model — this is the quality rationale behind the Owner's decision. The S003 dialogue (angry teen register, profanity, mockery) is the precise use-case the system prompt below is engineered for. [HYPOTHESIS: external-LLM superiority on register/profanity — high confidence, universally observed; final proof = S005 acceptance sample. The architecture does not depend on it: manual stays the primary and openrouter remains the auto fallback.]

### A3.3 Proposed System Prompt template (exact text, machine-merged with CONFIG)

Storage: `MANGABD_CONFIG["translation"]["manual_copy_prompt"]` (setdefault at cell 8 config block) — visible, Owner-editable, sanitizer-safe (no forbidden substrings in the key). Builder `build_external_ai_copy(page=None, region_id=None)` merges: prompt template + glossary lines (cell 8:323–346 `build_glossary_prompt_lines` reused verbatim — sfx glossary included for sfx-heavy pages) + the `[page:id] →` line block (reusing `build_ai_text_content`'s row walk, cell 25:157–164 / cell 8:1014–1027 logic). [FACT: reuse sites; proposal]

```
You are an expert Bengali manga/manhwa localizer with years of scanlation
experience. You translate English (and mixed Japanese-English) comic text
into natural, living Bengali — the way real Bengali speakers actually talk in
this situation — NEVER stiff, word-by-word, textbook translation.

YOUR TASK
Below is a numbered list of text regions from a manga/manhwa page. Each line
looks like:
    [PAGE:ID] English text →
Write your Bengali translation on the SAME line, AFTER the "→" arrow.

STRICT FORMAT RULES — THE OUTPUT IS MACHINE-PARSED:
1. Keep every [PAGE:ID] tag EXACTLY as given. Do not rename, renumber,
   reorder, merge or split lines. One input line → exactly one output line.
2. Output ONLY the completed lines. No preamble, no explanations, no
   headers, no markdown, no code fences, no quotation marks around lines.
3. Copy lines containing [SKIP:OCR_FAILED] unchanged (write nothing after
   the arrow).
4. Keep the arrow "→" as the separator on every line.

VOICE — THE MOST IMPORTANT PART:
- Dialogue must sound like real speech. Match the Bengali register to WHO
  is speaking: close friends/rivals/teens → তুই; polite strangers/adults →
  আপনি; standard তুমি otherwise. Keep it consistent per character.
- PRESERVE emotional intensity EXACTLY:
  * Slang stays slang. Localize to natural Bengali equivalents.
  * Profanity stays profanity — DO NOT sanitize or soften. Translate
    "fuck/shit/bitch/dumbass" with real Bengali curses of matching heat
    (শালা, বেটা চোদ, মাদারচোদ, মাগি, গাধা as register and heat dictate).
    Turning an angry line polite is a translation ERROR.
  * Shouting, mockery, teasing, sarcasm, shy/quiet lines each keep their
    distinct flavor and punctuation energy (!!, !?).
- Cultural nuance: localize idioms into Bengali equivalents rather than
  translating literally. If a pun cannot survive, choose the funniest
  natural Bengali that fits the scene.
- Names: transliterate consistently into Bengali script
  (Koganei → কোগানেই, Otearai → ওতেআরাই). Keep honorifics if present.
- T/L or translator notes in the text: translate the note's meaning
  concisely; if the line explains Japanese spelling, keep the kana exactly
  as written.
- SFX lines: short, punchy, onomatopoeic Bengali (BOOM → বুম!, THUD →
  ধপাস!, GASP → হাঁপ!). Never expand SFX into full sentences.
- Narration/overlay text: clear, slightly literary Bengali. Bubble
  dialogue: spoken Bengali.

GLOSSARY (must-follow renderings):
<auto-merged from CONFIG glossary + sfx_glossary, if non-empty; else this
section is omitted entirely>
```

Then the payload block, visually separated:

```
══════════ TEXT TO TRANSLATE ══════════
[02.jpg:1] T/L note: ... →
[02.jpg:2] THE ONLY LETTER CORRECT IN THAT NAME WAS "!! →
...
```

Rationale for each prompt section traced to observed failures: register/profanity rules target R3/R5 (S003); kana/note rules target R1; SFX rules target the sfx_glossary system (cell 8:349–379); format rules exist because the paste-back parser keys on `[page:id]` + last-arrow (cell 8:916, 929–931); the glossary merge reuses the proven prompt-injection path (cell 8:307–312). [FACT: defect mapping; proposal: prompt]

### A3.4 UI / cell modifications (Phase B design)

1. **New Studio button `btn_copy_ai` "📋 COPY FOR EXTERNAL AI"** in the manual-paste panel (replacing/augmenting `btn_load_src`, cell 25:422 flow "Load → বাংলা লেখো/পেস্ট → Apply"): builds the two-part payload via `build_external_ai_copy()`, renders it in a raw HTML `<textarea>` (NOT the disabled widget — raw HTML gives JS a selection handle), and injects a one-shot JS copy: `el.select(); el.focus(); document.execCommand('copy')` with a `navigator.clipboard.writeText(...)` first attempt and automatic fallback between the two (Colab output iframes have inconsistent clipboard-permission grants; `execCommand` on a selected in-DOM textarea is the most reliable path; the textarea stays visible so manual Ctrl+C always works as the ultimate fallback). Status feedback printed to the Studio console ("📋 Copied N regions — paste into ChatGPT/Claude/Gemini, then paste the reply below"). [HYPOTHESIS: clipboard behavior in current Colab needs one live verification in Phase B/D — the design degrades to "textarea visible + select() + manual Ctrl+C" which cannot fail.]
2. **Per-page scoping:** `page_dd` (cell 25:296, already exists for downloads) gains a "current page only" toggle next to the copy button — full-session copies get long; the S003 page had 6 regions, but a 50-page session would exceed chat context. Default: current page (the Owner works page-by-page per the Studio flow). [judgment, config-gated]
3. **`show_text_for_translation()` (cell 22:107–182) upgraded** to emit the same two-part payload between the COPY markers (single source of truth: it calls `build_external_ai_copy()` when present, falls back to today's bare format). `step_3_manual_translate_paste()` (cell 22:379–445) unchanged otherwise. [proposal]
4. **Paste-back hardening (cell 22 `apply_translations_from_text`, ~8 lines):** pre-parse `_strip_llm_wrappers(content)` removing lines that are pure markdown fences (``` / ```text / ```markdown) and common LLM preambles ("Here are the translations:" as the first non-empty non-header line) BEFORE `parse_ai_text` — today those lines land in the V-4a sentinel and produce a scary-looking warning even when every data line parsed fine. The sentinel itself stays untouched (it is a merged, protected V-4a artifact). [FACT: current behavior; proposal: guard]
5. **`ta_tgt` placeholder text** (cell 25:292) updated to show the full expected format including the `[page:id]` echo, teaching the format at the point of use. [cosmetic]

### A3.5 What deliberately does NOT change

- The ai.Text line format `[page:id] English → বাংলা` — it is load-bearing across: `parse_ai_text` regex (cell 8:916), 5-arrow local parser (cell 22:59), rescue path (cell 22:230–233), fallback applier's page-normalization map (cell 22:310–329), `export_ai_text` (cell 8:986–1040), V-4a sentinel quarantine, and Flash's D-harnesses. The system prompt *wraps* the format; it does not alter it. [FACT]
- An optional `(bubble)`/`(sfx)` region-type tag after `[page:id]` was considered and is **rejected for Phase B**: it lands inside `original_text` after the arrow split (harmless for apply, but changes sidecar bytes and every Flash harness that fingerprints cell-22 behavior) for marginal prompt value — the SFX rules are already unconditional in the prompt. Revisit only if S005 shows the external LLM mishandling SFX vs dialogue. [judgment]

---
## A4 Directive 3 — LaMa Large inpainting audit (cell 9 + cell 5 + upstream)

### A4.1 Current implementation facts

- Engine: `lama` with OpenCV-Telea fallback (cell 9:68–69, 322–356, 541–562). Model = **LaMa Large** (`lama_large_512px.ckpt`, `large_arch=True`, `use_mpe=False`) via zyddnys `LamaLargeInpainter` subclassed in cell 5:699–745 with a Drive-backed model dir override (cell 5:718). [FACT]
- Working resolution: **`lama_size = 1024`** (cell 9:69) passed explicitly as the 4th positional arg to `lama.inpaint(...)` (cell 9:385–396). The `InpainterConfig()` constructed fresh at cell 9:383 uses upstream defaults — its own `inpainting_size` field (zy:config.py:297, default **2048**) is *never read by our call path*; our explicit 1024 arg governs. [FACT]
- Upstream resize semantics (zy:inpainting_lama_mpe.py:56–118, `_infer`): if `max(H,W) > inpainting_size` → `resize_keep_aspect` BOTH image and mask to the cap (zy:utils/generic.py:251–255, INTER_LINEAR_EXACT); then pad-to-/8 by a tiny cv2.resize stretch (lines 67–79); inference under `torch.autocast(bf16)` with fp32 weights (lines 97–107 — upstream comment: fp16/bf16 *weights* darken LaMa output; autocast is the sanctioned mode); resize back to original dims (115–116); composite `inpainted*mask + original*(1-mask)` so **only masked pixels come from the upscaled inference** (117). [FACT]
- Precision: `InpainterConfig()` default `inpainting_precision = bf16` (zy:config.py:299–300, "use bf16 while you can") → cell 9 already runs the recommended precision. [FACT]
- VRAM hygiene: `unload_others=True` → `model_manager.unload_all(exclude=["lama"])` BEFORE `ensure_lama()` (cell 9:370–377 → cell 5:563–571, each unload followed by `clear_gpu_cache()` = gc + `torch.cuda.empty_cache()`, cell 5:143–148). This is correct sequencing: RT-DETR/Qwen/CTD are released before LaMa loads. [FACT]
- Failure path: LaMa exception → OpenCV Telea inpaint (radius 5, cell 9:322–356) with `fallback_used=True` in stage meta — a large silent quality downgrade (Telea smear vs LaMa texture synthesis). [FACT]
- Architecture: LaMa Large = `FFCResNetGenerator` with n_blocks=18 (vs 9 base), ngf=64, 3 downsamples, max_features=1024, FFC ratio 0.75, LFU disabled (zy:inpainting_lama_mpe.py:545–614, 636–651) — **fully convolutional, no fixed-size constraint, no MPE** → native-resolution inference is architecturally legal; VRAM is the only constraint. [FACT]

### A4.2 Verdict: is LaMa throttled?

**YES — by a factor of 2 versus upstream's own default, and it silently down-scales every page the Owner actually runs.** [FACT]

- Upstream default working size = **2048** (zy:config.py:297, doc-comment "too large will result in OOM"); MangaBD runs **1024** (cell 9:69). [FACT]
- Concrete effect on the Owner's real pages (S003: 844×1200): 1200 > 1024 → the page is down-scaled to 720×1024 (0.853×) for inference, then the inpainted result is bilinearly up-scaled back 1.17× and composited inside the text masks. Fine texture (screentone, hair strands, speed lines) inside inpainted bubbles is softened accordingly. [FACT: arithmetic; TEST RESULT: page dims from samples/S003_batch2/original.jpg = 844×1200]
- The 512px in the checkpoint filename (`lama_large_512px.ckpt`) refers to the model's *training* resolution, not an inference limit (fully convolutional — see A4.1); upstream nevertheless defaults to 2048 working size, and the MangaBD choice of 1024 is a conservative VRAM posture, not a model constraint. [FACT + inference]

### A4.3 Proposal — maximize quality with T4-safe VRAM management

**P1 (core): replace the fixed cap with an OOM-safe resolution ladder in `lama_inpaint_full` (cell 9:362–408, ~+25 lines).**

```
effective_ladder = [owner_lama_size] + [s for s in (2048, 1536, 1024) if s < owner_lama_size]
for size in ladder:
    try:    result = run lama.inpaint(..., size, ...)
    except (torch.cuda.OutOfMemoryError, RuntimeError-with-"out of memory"):
            clear_gpu_cache(); log "LaMa OOM at {size} → retrying {next}"; continue
else: OpenCV fallback (existing path, cell 9:541–552)
```

- Default `lama_size` raised **1024 → 2048** (= upstream default). For the Owner's 844×1200 pages this means **full native-resolution inference (no resize at all — 1200 < 2048; only the ≤8px pad-to-/8 stretch applies)**. Larger pages (e.g. 1600×2400 scans) still get 0.85× — matching today's behavior for those, strictly better for standard pages. [FACT: cap semantics; proposal]
- VRAM budget (bf16-autocast activations + fp32 weights, all other models unloaded): S003 page at native 848×1200 ≈ **3–5 GB peak** → comfortable on T4 (≈15 GB usable); 2048×2048 worst-case ≈ 9–14 GB → borderline, which is exactly what the ladder absorbs; 1024 floor ≈ 2–3 GB → the currently-proven-safe mode stays as guaranteed fallback. [HYPOTHESIS: numbers are architecture-derived estimates, not measurements — Phase D plan: Flash runs the ladder on a live T4 with `torch.cuda.max_memory_allocated()` instrumentation per rung and reports the measured ladder; acceptance gate = 844×1200 page completes at native with measured peak < 12 GB.]
- The ladder changes failure semantics from "immediate Telea downgrade" to "graceful degradation with a logged, observable reason" — the stage meta (cell 9:569–579) gains `inpaint_size_effective` so every run records which rung actually ran. [proposal]

**P2 (UX): make `lama_size` Owner-visible** — add it to the STEP 4 panel hint line in the Studio (cell 25:447) and to the cell 9 startup print (already printed at cell 9:85). One-line visibility, no widget needed (the Owner changes it rarely). [proposal]

**P3 (rejected alternatives, with rationale):** (a) *Tiling/patch inference* — rejected: LaMa's global receptive field is FFT-based over the whole canvas (zy:FourierUnit:187–260); tiles would sever global context and produce seams/inconsistency exactly where manga backgrounds are continuous; the OOM ladder achieves the memory goal without the quality tax. (b) *Native unconditional (size=0/huge)* — rejected as default: zyddnys treats >2048 as OOM-prone (zy:config.py:298) and webtoon tall-strips (cell 24 slicer) could exceed 6000px; the ladder's top rung respects the owner value if they explicitly set higher. (c) *Mask resize to INTER_NEAREST* — upstream-internal (zy:inpainting_lama_mpe.py:65–66); patching zyddnys code at cell-4 runtime is invasive; effect is ≤1px mask-boundary wobble and the composite uses the original full-res mask anyway (line 117). Not worth the supply-chain surface. [FACT + judgment]

### A4.4 Additional quality observations (non-blocking, Phase C candidates)

- `redilate_artifact_mask=False` + `mask_clip_to_regions=True` + `mask_clip_padding=10` (cell 9:70–76) — the V-1/V-2-era mask discipline from Batch 1/2 is untouched by this audit and must remain byte-stable in any M4-B2 diff (protected baseline). [FACT]
- The `opencv_radius=5` Telea fallback could be raised to `cv2.INPAINT_NS` as a slightly better last-resort, but with the ladder in place the fallback should almost never fire; not worth the diff. [judgment]
- `inpaint_time_sec` is already recorded per page (cell 9:577) — Phase D regression tracking for the 2048 default comes free. [FACT]

### A4.6 Supply-chain note (new finding, from this audit)

Cell 4 clones zyddnys `--depth 1` and `git pull`s on EVERY run (cell 4:226–248) — the LaMa implementation, its precision handling, and the resize semantics tracked above are **upstream-HEAD-unpinned** and can drift under us mid-project (upstream moved 2026-10-11, `d6de6ab`, "update dependencies"). All A4 facts cite `d6de6ab`. Proposal (Phase B, cell 4, ~4 lines): record the resolved HEAD hash into `MANGABD_CONFIG["runtime"]["zyddnys_commit"]` (via `git -C ... rev-parse HEAD`) at clone/pull time so every session's artifacts are traceable to the exact upstream code that produced them; pinning a fixed commit is the stronger option but changes the "always latest" behavior the Owner has implicitly run so far — flagged as decision item A7-D5. [FACT: unpinned pull; proposal: hash recording]

---

## A5 Directive 4 — OCR audit (Qwen2.5-VL-3B, cell 7 + cell 5)

### A5.1 Current pipeline facts

- Model: `Qwen/Qwen2.5-VL-3B-Instruct` (cell 1:248), loaded fp16 on cuda (cell 5:77–80 — fp32 on CPU), `device_map="auto"`, local HF cache (cell 5:786–798). ~7.5 GB weights on T4. [FACT]
- Decode: greedy — `do_sample=False`, `num_beams=1`, `max_new_tokens=512` (cell 1:249–254 → cell 5:404–408). No repetition penalty configured. [FACT]
- **Pixel budget: no practical cap.** `AutoProcessor.from_pretrained` (cell 5:800–805) ships with `min_pixels=3136, max_pixels=12,845,056` (≈3584×3584, verified against the model repo's `preprocessor_config.json` fetched this session) — bubble crops (tens-of-thousands of px) are processed at **native resolution** with patch-14/merge-2 dynamic tiling. The OCR stage is NOT resolution-starved; quality levers lie elsewhere. [TEST RESULT: config fetched from HF hub; FACT: cell 5:800–805 passes no overrides]
- Prompt: ONE generic prompt for every region type (cell 7:75–85 = cell 5:350–358 fallback): "Extract all English text visible in this image exactly as written. Do not translate. Do not explain. Preserve readable punctuation. Return only the raw text content. If there is no readable text, return empty string." — no region-type awareness, no stylized-font guidance, no mixed-Japanese guidance, no multi-line/reading-order guidance. [FACT]
- Preprocessing (cell 7:208–313): BGR→RGB; upscale only if h<40px (×≥2, cubic); bilateral d=5 σ50/50; CLAHE clip 2.0 (8×8) on L; pad max(4, min(h,w)//10) — white constant for bubbles, BORDER_REPLICATE for sfx/overlay (cell 7:279–297). [FACT]
- Confidence: **heuristic, not model-derived** — `_estimate_ocr_confidence` (cell 5:281–315): 0.45 base + length bumps + language-ratio + punctuation bonus, capped 0.95. Every S003 region reads exactly 0.95 regardless of difficulty — the V-3 orientation selector's score (`confidence + language_score.en`, cell 7:412–414) and the QC thresholds (cell 7:68–69: 0.50/0.65) therefore run on a nearly-saturated signal. [FACT: mechanism + S003 evidence — all 6 regions conf=0.95]
- Post-processing: `clean_ocr_output` (cell 7:106–136) strips model prefixes then **collapses ALL whitespace to one line** (cell 5:230–241 `_clean_ocr_text` same); multi-line bubble structure is destroyed at the df boundary (by design — the ai.Text format is single-line; noted as A3.5 constraint). [FACT]
- Vertical text: V-3 Layer-1 rotated-candidates selector (cell 7:394–432) — S003-proven, Flash Phase D + S003 accepted; out of M4 scope except as the *pattern donor* for A5.3-P3. [FACT]

### A5.2 Observed accuracy defects (S002/S003 evidence)

- S002 R1 misread "Otearai" → "Otarumi" — fixed by V-3 rotation (S003 accepted). [FACT, historical]
- S003 residuals (post-V-3): R1 "hiragani" (→ hiragana), stray ")" surviving from "こがねい)", "pronounce" (→ pronounced); R2 `THE ONLY LETTER CORRECT IN THAT NAME WAS "!!` — a letter was dropped before the quote mark (likely the quoted glyph); R5 "OTEARAH" (real spelling per R1 note is "Otearai" — same-name inconsistency across regions); R6 truncation at crop edge ("SUDENLY" sic, sentence cut). [FACT: from S003 ocr.json + Flash Phase D/S003 records]
- No SFX regions in S003's 6-region page (all bubble/overlay) — the SFX/stylized-font failure mode named in the directive is not yet *measured* in any archived sample; treat as the first S005/S006 acceptance target. [FACT: sample inventory; UNKNOWN: actual SFX accuracy]

### A5.3 Proposals (ordered by leverage-per-risk)

**P1 — Region-type-aware prompt map (cell 7, ~+30 lines; highest leverage, lowest risk).** Mirror the proven `REGION_TYPE_INSTRUCTIONS` precedent from the translation side (cell 8:254–260): a `OCR_PROMPTS` dict keyed by `region.get("region_type")` with a shared base instruction plus per-type riders, e.g.:
- base (all): current generic prompt, plus "Transcribe each text block in natural reading order (top-to-bottom; if the lettering is Japanese-style vertical, follow its columns)" and "If the text mixes English with Japanese kana/kanji, transcribe BOTH exactly as written, including any romanized readings."
- `sfx`: "This is a stylized sound effect — letters may be warped, distorted, outlined, or hand-drawn. Transcribe the letters as written, in order. Do not 'correct' or normalize the styling."
- `overlay`: "This is a sign/label/annotation; keep exact capitalization."
- `bubble`/`thought`/`narrator`: "Hand-lettered comic dialogue; keep line groupings; if a word is partially cut off at the crop edge, still transcribe the visible part." (targets R2/R6 class defects)

This reuses the V-5 config-driven pattern (`MANGABD_CONFIG["ocr"]["prompts"]`, setdefault-registered, prompt still overridable per run). Flash D-verification: static prompt-map presence + harness that proves the correct rider is selected per region_type. [proposal; defect→rider mapping is FACT-traced above]

**P2 — Decode safety + real confidence (cell 5, ~+15 lines).** (a) Add `repetition_penalty` (default 1.05, config-gated) to `generate_kwargs` (cell 5:404–408) — VLMs are known to loop on glyph repetition in stylized text; greedy+no-penalty is the worst-case decode for that failure. (b) OPTIONAL and flagged for recalibration: derive confidence from actual token probabilities via `model.generate(..., output_scores=True, return_dict_in_generate=True)` → geometric-mean token prob. This turns the saturated 0.95s into a real signal and would materially improve the V-3 orientation selector — but it **changes the sidecar `confidence` semantics**, so the QC thresholds (0.50/0.65, cell 7:68–69) and the V-3 tie-break scale would need re-calibration against archived S001–S003 outputs. Recommend implementing behind `MANGABD_CONFIG["ocr"]["real_confidence"] = False` (default off) and calibrating in a dedicated micro-batch before flipping on. [HYPOTHESIS: decode-loop risk; FACT: threshold coupling; proposal]

**P3 — Dual-candidate preprocessing for sfx (cell 7, ~+20 lines, config-gated default ON for sfx only).** Extend the V-3 two-candidate pattern: for `region_type == "sfx"`, run OCR twice — current preprocessing vs. an aggressive binarization variant (Otsu on the L channel + contrast stretch) — and keep the higher `confidence + language_score.en`, recording `sfx_ocr_variant` in warnings/sidecar exactly like `vertical_ocr` (cell 7:422–430). Cost: +1 VLM call per sfx region (S003 had zero sfx; typical pages have a handful); benefit: robustness to the two dominant SFX renderings (outlined-on-art vs. high-contrast lettering). [proposal, pattern-precedent FACT]

**P4 — Optional cloud OCR via OpenRouter vision models (Phase C+ candidate, NOT in the first M4 batch).** Once OpenRouter is the sole provider (A2), a `ocr_engine: "openrouter_vision"` variant becomes ~40 lines (base64 the crop, send to a vision-capable model with P1's prompt) — unifying key management and unlocking GPT-4o/Gemini-class OCR for hard pages while keeping local Qwen as free default. Rejected for the first batch: per-region API cost, latency, and it couples OCR availability to the key — the Owner's primary flow (manual copy-paste) must work keyless. [judgment]

**P5 — Preprocessing micro-tuning (cell 7, low priority).** CLAHE clipLimit 2.0→2.4 for low-contrast dark scans (config knob); nothing else — the A5.1 pixel-budget finding removes the motivation for super-resolution upscaling for typical crops. [judgment]

---
## A6 Proposed implementation plan (for PM/Owner authorization — nothing below is started)

Batches follow the MANGABD-003 protocol: branch from the decided base → per-cell single-logical-change → static + harness self-verification (scripts persisted, re-runnable) → WIP push → Flash Phase D (scope sha16 per changed cell + fresh-run regression + guard-equivalence S1–S6 + runtime proofs) → Owner S-sample live acceptance → squash-merge on authorization → DECISION.md record → branch cleanup. [FACT: protocol]

- **M4-B1 "MANUAL PRIMARY"** — A3 in code: `manual_copy_prompt` config + `build_external_ai_copy()` + Studio copy button (JS clipboard w/ fallback) + per-page scoping + cell-22 prompt payload + `_strip_llm_wrappers` guard + placeholder updates. Cells: 8, 22, 25 (+25-only widget work). ~+120/−15 lines. No engine changes, no key dependencies — the Owner's primary workflow works with zero API keys. S005 acceptance: copy → external LLM → paste → apply round-trip on a fresh page; parse-rate and unparsed-sentinel behavior compared against S003-class runs. [proposal]
- **M4-B2 "OPENROUTER EXCLUSIVE"** — A2 in code: registry reduction + adapter headers/usage + dead-code removal (A2.5 list) + STEP 0 key panel + model widget + cell-1 banner + SECRET_SOURCES trim + cell 15/18/19 text + cell 17 test generalization. Cells: 1, 8, 15, 17, 18, 19, 25. ~−260/+160 lines net. Depends on B1's cell-8/25 state → sequenced after B1 on the same lineage (B2 branch from B1's merged head). S006 acceptance: one live openrouter translation run + key-entry UX flow (STEP 0 session-save path at minimum; userdata persist path if Colab allows). [proposal]
- **M4-B3 "LAMA FULL POTENTIAL"** — A4.3-P1/P2: OOM ladder + default 2048 + `inpaint_size_effective` meta + Studio hint. Cells: 9 (+25 one hint line). ~+30/−2 lines. S007 acceptance: the Owner's 844×1200 reference page at native rung, visual side-by-side vs S003 inpainted.png, measured VRAM peak from Phase D instrumentation. [proposal]
- **M4-B4 "OCR PROMPT UPGRADE"** — A5.3-P1 (+P2's repetition_penalty, +P3 if Phase D agrees): prompt map + decode knob + optional sfx dual-pass. Cells: 7 (+5 for generate_kwargs). ~+60/−4 lines. S008 acceptance: fresh OCR run on the S003 page (regression: no new errors on regions 2–6) + an SFX-bearing page for the new prompt's target behavior. [proposal]
- P2-real-confidence flip and P4-openrouter-vision-OCR are deliberately deferred to standalone micro-batches (threshold recalibration / cost surface). [proposal]

Rationale for the B1→B2 order: B1 is the Owner's stated PRIMARY method, is keyless (works even while the OpenRouter key UX is being validated), and touches cells 8/22/25 in additive mode — so B2's deletions land on already-updated cells with one acceptance cycle in between instead of one mega-review. If the PM prefers the directive's 1→2 grouping as a single batch, B1+B2 merge into one M4-B1 of ~−260/+280 lines across 7 cells — workable, but Flash's per-cell single-logical-change review and the Owner's acceptance burden both get materially heavier. [judgment, decision item A7-D6]

## A7 Decision items & open questions for PM/Owner relay

- **D1 — MANGABD-003 Batch 3 (V-5) disposition vs. the M4 pivot.** Options: (a) run S004 + merge Batch 3 first (closes M003 cleanly at the cost of an Owner session validating code M4-B2 then deletes); (b) **supersede (my recommendation)**: close M003 with Batch 3 recorded as "implemented `1753b1a`, Flash Phase D APPROVED `37dc72e`, superseded by the MANGABD-004 Owner pivot before S004 acceptance; branch + `mangabd-003-phase-c` preserved as historical byte source"; M4-B2 branches from `main @ 37dc72e` and re-authors the ~60-line openrouter subset (adapter/registry/key_env/closure/SECRET_SOURCES/translator_model — all V-5-proven patterns) rather than transplanting the 5-provider payload. Saves one full acceptance/merge cycle; costs the "clean close" of (a). Owner call. [recommendation + FACT: both branch states verified]
- **D2 — OpenRouter default model & fallback list** (A2.3): confirm `openai/gpt-4o-mini` stays as shipped default + whether to enable the fallback-models knob at all initially. [decision]
- **D3 — Bengali register rules in the system prompt** (A3.3): the তুই/তুমি/আপনি mapping and the explicit profanity examples are MY drafting choices from the S003 defect evidence; the Owner (a Bengali speaker) should confirm/adjust the register table and curse-word register before S005 — this is taste, not engineering. [decision]
- **D4 — LaMa default 2048** (A4.3): confirm the ladder default; alternatively keep 1024 default with the ladder still protecting against OOM at higher owner-chosen sizes. [decision]
- **D5 — zyddnys pinning** (A4.6): record-commit-hash (proposed, low risk) vs. hard-pin a commit (behavior freeze, diverges from "always latest"). [decision]
- **D6 — batch split B1/B2** (A6): split (recommended) vs. single combined batch. [decision]
- **D7 — UNKNOWN, needs live Colab:** `userdata.set()` dialog behavior for the STEP 0 persist button (A2.4); clipboard-write permission in current Colab output iframes (A3.4). Both have designed fallbacks that cannot hard-fail; both get checked in the first Phase B/D live session. [UNKNOWN]

**No source code, no other agent files, no branches were modified in this phase.** All work this phase: read-only audits (both refs + upstream clone `d6de6ab`), offline arithmetic on archived samples, and this document. Scripts used for extraction/inspection live outside the repo (`/home/z/my-project/m004/` scratch, incl. cell extractions of both refs and the upstream shallow clone — reusable as the Phase B starting audit kit).


---

# MANGABD-004 — PHASE C: IMPLEMENTATION RECORD (GLM-5.3, 2026-10-13)

PM directive received (Qwen3.8-Max relay, 2026-10-13): implement **M4-B1 (OpenRouter Exclusive + Dead Code Cleanup)** and **M4-B2 (Advanced Manual Copy-Paste System)** in one cohesive branch, incorporating all Flash Phase B amendments (review `97a683a`, CONFIRMED WITH AMENDMENTS). Branch `mangabd-004-b1-b2` created from `main @ 97a683a` (notebook blob `98b1e739…` verified pre-edit). MANGABD-003 Batch 3 recorded as SUPERSEDED per A7-D1 (Owner approved skipping S004).

## C0 Scope, method & invariant

- **Cells edited: {1, 8, 15, 17, 18, 19, 22, 25}** — 46 anchored patches, every one an exact old-string match asserted to occur exactly once (no fuzzy matching, no line-number guesswork); multi-line anchors were byte-sliced from the pre-edit cell source itself. Build script: `/home/z/my-project/scripts/m4_b1b2_build.py` (+ `m4_b1b2_patches{,2,3}.py` payloads), re-runnable from a clean checkout. [TEST RESULT]
- **Net diff: −425/+638 lines** (cell 1 −7/+23; cell 8 −300/+398; cell 15 −1/+1; cell 17 −3/+5; cell 18 −4/+2; cell 19 −73/+2; cell 22 −7/+39; cell 25 −30/+168). The PM's ~260-line purge target is met and exceeded on the removal side: cell 8 alone sheds `translate_with_gemini` (44 lines) + `translate_with_chatgpt` (58) + the NLLB trio (~170) + NLLB config (9) + 3 dispatcher branches (~20) + gemini/openai model cfg, plus cell 19's NLLB override (−73) and cell 25's legacy widgets/handlers (−30) — ≈390 gross legacy lines removed; the additions are the B2 copy-paste system, STEP 0 key UX, and 6 new self-tests. [TEST RESULT: git diff]
- **Invariant held: all 19 out-of-scope cells byte-identical to main @ 97a683a; all non-source cell fields (outputs/execution_count/metadata) identical for all 27 cells; JSON writer byte-faithful round-trip pre- and post-edit.** Cells 7/9/16 (V-3, LaMa, Batch-2 protected territory) untouched. [TEST RESULT: verify script V2.1–V2.3]
- Per-cell sha16 (new source): c1 `202dea00a22b50ea` · c8 `e6ab34c1b7280249` · c15 `d0047ad95135c1ba` · c17 `230fef5cb64cd816` · c18 `9df9d67c80c2f737` · c19 `d1fe619d88a1b533` · c22 `c3f27c598b84b59f` · c25 `0de59d248995c5e0`. [TEST RESULT]

## C1 B1 — OpenRouter exclusive (per cell)

**Cell 8 (Translation Service, 1748 → 1846 lines):**
- Header engines comment now `manual (PRIMARY — external-AI copy-paste, keyless)` + `openrouter (SOLE cloud provider)` (cell 8:4–5).
- **Provider registry** (cell 8:82–86): exactly one entry — `{"openrouter": {"base_url": "https://openrouter.ai/api/v1", "model": "openai/gpt-4o-mini", "key_env": "openrouter_api_key"}}` via setdefault. The `key_env` (not `api_key_env`) field-name discipline is carried over from V-5 with its explanatory comment (sanitizer survival — Flash M003 Phase B amendment 2, runtime-proven Flash Phase D D2). [FACT]
- **gemini_model/openai_model setdefaults and the whole NLLB config block deleted**; config print block now reports the OpenRouter model + manual-copy status (cell 8:193–197).
- **translate_with_provider** (cell 8:518–590): re-authored on the V-5-proven registry-driven shape (OpenAI SDK, base_url/model/key_env from CONFIG) rather than transplanted from the 5-provider payload (A2.6 re-author recommendation). OpenRouter-specific additions per A2.3, both additive/fail-soft: attribution headers `HTTP-Referer`/`X-Title` on the client constructor, and `response.usage` token counts logged via log_event with defensive getattr access.
- **Dispatcher** (cell 8:638–648): gemini/chatgpt/nllb branches deleted; the provider branch binds the engine via closure — `lambda t, rt: translate_with_provider(t, rt, engine=engine)` — keeping `translate_with_retry`'s `(translate_func, text, region_type)` signature untouched (Flash M003 Phase B amendment 1; PM directive B1-amendment 3; do-NOT-widen note in the comment).
- **switch_translator valid_engines** (cell 8:662–668): `["manual"] + list(providers keys)` — the hardcoded legacy literal is GONE (Flash M004 Amendment 1: it did NOT auto-collapse). `switch_translator("nllb"/"gemini"/"chatgpt")` now returns False with the existing WARN; runtime-proven by in-notebook Test 11.
- **translator_model sidecar** (cell 8:1075–1082): V-5 pattern, additive — registry lookup by engine name; manual rows leave it empty; row-level override wins. Old artifact JSONs stay readable (engine values are strings; nothing switches on them at load — Flash PB1 confirmed).
- **Live-test block** (cell 8:1728–1732): `LIVE_TRANSLATION_ENGINE = "openrouter"` + updated comment.
- Sections renumbered 6–12 (cosmetic coherence after the 6/7/8 purge).

**Cell 1 (Config/Secrets):** `MANGABD_SECRETS` trimmed to `{openrouter_api_key, hf_token}` (cell 1:383–386; **hf_token stays** — RT-DETR/Qwen/LaMa weights download via HF, cell 5 consumers verified live in Phase B). `SECRET_SOURCES` = `{openrouter_api_key: [OPENROUTER_API_KEY], hf_token: [HF_TOKEN, HUGGINGFACE_TOKEN]}` (cell 1:409–413) — secret NAME unchanged, so existing saved Colab secrets keep working. `allowed_engines` stale CONFIG value updated to `["manual", "openrouter"]` (cell 1:247; Flash PB5 cosmetic item). **Key-not-set banner** (cell 1:441–455, A2.4 layer-2 + Amendment 7 wording): boxed instruction with the exact secret name, the 🔑-sidebar path, and the STEP 0 pointer; states that manual copy-paste needs no key.

**Cell 15:** `quick_start_auto(engine="openrouter")` (cell 15:898). **Cell 17:** leak-test key family generalized gemini → openrouter (cell 17:967–971, Flash PB5 REQUIRED item). **Cell 18:** command examples now openrouter/manual only (cell 18:599, 971–972). **Cell 19:** the NLLB src_lang override section removed entirely (−73 lines); the manual-translation rescue half stays intact (cell 19:19 `apply_translations_from_ai_file`, `qa_validate_bengali` rescue path preserved — Flash PB5 "rescue half stays").

**Default model decision (D2):** shipped `openai/gpt-4o-mini` — the Owner-authorized Batch-3 default (Flash Phase D "defaults authorized"). The PM directive offered `apodex/apodex-1.1-mini:free` as an alternative; switching is now a one-widget UI action (model box, cell 25:318/431–434), so no code change is needed if the Owner prefers it. [decision recorded for Phase D/Owner]

## C2 B2 — Advanced manual copy-paste (per cell)

**Cell 8:**
- **`manual_copy_prompt`** CONFIG template (cell 8:132–194): the A3.3 system prompt verbatim — expert Bengali manga/manhwa localizer persona; machine-parse format rules keyed to the parser semantics ([PAGE:ID] preservation, LAST-arrow, `[SKIP:OCR_FAILED]` copy-through, no fences/preamble); VOICE section preserving slang, profanity (শালা/বেটা চোদ/মাদারচোদ/মাগি/গাধা register guidance), anger/emotional tone, cultural nuance, name transliteration, T/L-note handling, SFX onomatopoeia. Sanitizer-safe key name. Register/curse-word wording remains Owner-taste item A7-D3 (S005 review). [FACT: implemented; wording per Phase A spec]
- **`_build_external_ai_system_prompt()`** (cell 8:385–417): merges template + glossary via the SAME `build_glossary_prompt_lines` merge path the auto-engine prompt uses (single-sourced glossary; sfx call includes the base set).
- **`_strip_llm_wrappers()`** (cell 8:695–727, with `_HEADER_LINE_RE`/`_HEADER_ANY_RE`/`_PURE_FENCE_RE` at 703–705): Flash Amendment 3 prefix-zone spec — strips ONLY pure fence lines (anywhere) and non-header lines before the first data header; never strips header-matching lines, never a non-fence line after the first header, and (hardening beyond the amendment's letter, in its spirit) never a line CONTAINING a header pattern — fence-glued data lines reach the V-4a sentinel visibly instead of being silently dropped. [FACT: spec; TEST RESULT: in-notebook Test 14 proves all three cases]
- 6 new self-tests (Tests 10–15, cell 8:1608–1760): registry shape (incl. `api_key_env` absence — sanitizer survival), valid_engines rejection of all 3 legacy engines, closure dispatch via a monkeypatched fake adapter (call-path proof without SDK/network), manual_copy_prompt/system-prompt builder, _strip_llm_wrappers battery (fenced/wrapped/glued), full paste-back round-trip.

**Cell 22:**
- `apply_translations_from_text` now pre-cleans content via `_strip_llm_wrappers` before parser selection (cell 22:228–237) — the single paste-back funnel (Studio `on_apply`, `on_import`, `step_3` UI, and `apply_pasted_translation` alias all route here). The V-4a `("_unparsed", 0)` sentinel is untouched and remains the visible path for post-header unparseables (Flash PB2 wire-format constraint honored). Cell 19's file-based rescue path deliberately does NOT strip (machine-generated content; sentinel stays visible) — noted as a conscious scope decision.
- `show_text_for_translation()` (cell 22:140–152) emits the two-part payload via `build_external_ai_copy()` when available (runtime globals() lookup — cell 25 runs later), with the bare-format fallback preserved for standalone use. Trailing instructions rewritten for the external-AI workflow (cell 22:190–196).
- Cell header comment documents the new PRIMARY workflow.

**Cell 25 (Control Studio, 441 → 579 lines):**
- **STEP 0 · 🔑 OPENROUTER KEY panel at the very top** (cell 25:557–564, A2.4 layer-1): key status line (✅ loaded / ⚪ not set), `or_key` Password widget, "💾 Save Key (এই session)" (MANGABD_SECRETS + os.environ — mirrors the V-5-proven capture pattern) and "🔐 Save to Colab Secrets" (`userdata.set("OPENROUTER_API_KEY", …)` in try/except with a plain-language fallback message — A7-D7 degrade path). The panel carries the Amendment 7 persistence-invariant wording verbatim: allowed persistent surface = Colab userdata ONLY; forbidden = notebook bytes / CONFIG / manifest / artifacts.
- **OpenRouter mode panel** (cell 25:528–533): model Text widget pre-filled from the registry, applied to CONFIG on the translate click (A2.4 layer-3 — "route to any model" is a one-widget action); `on_or` callback is the V-5 `on_provider` pattern with engine="openrouter". Key entry is NOT duplicated here (ipywidgets single-parent constraint) — the panel carries a read-only `key_status2` mirror + a pointer to STEP 0; both status mirrors are set by one updater (`_refresh_key_status`, cell 25:402–409), so no state drift is possible.
- **`btn_copy_ai` "📋 COPY FOR EXTERNAL AI"** + `on_copy_ai` (cell 25:447–488): builds the two-part payload, renders it in a visible raw-HTML textarea (unique box id per click) and injects one-shot JS — `navigator.clipboard.writeText` first, `document.execCommand('copy')` fallback, the box stays visible so manual select+Ctrl+C ALWAYS works (A3.4-1 degrade path; clipboard-permission D7 parked with a cannot-fail fallback). Status feedback via the Studio console `say()` pattern.
- **Per-page scoping** (A3.4-2): `scope_sel` THIS PAGE / ALL PAGES toggle (default THIS PAGE — the Owner works page-by-page) + `copy_page_dd` populated from translation_df on panel rebuild and after OCR (cell 25:410–416, 357–360). Zero-hard-fail: no page selected → falls back to all pages.
- **`build_ai_text_content(page=None)`** (cell 25:153–170): the ONE row walk, now with an optional page filter; all consumers (copy payload, ta_src load, export) delegate here. **`build_external_ai_copy(page=None)`** (cell 25:173–195): TOP = system prompt (cell 8 builder), separator `══════════ TEXT TO TRANSLATE ══════════`, BOTTOM = `build_ai_text_content(page=page)` — **delegates, no third row-walk** (Flash Amendment 4); returns (payload, region_count).
- `mode_sel` reduced to 2 options (manual PRIMARY / openrouter auto); `rebuild_mode_panel`'s trailing `else` is now a defensive unknown-mode message referencing NO deleted widget (Flash Amendment 2 — the btn_nllb NameError landmine is gone; the only remaining `btn_nllb`/`gemini_key` mentions in the cell are two comment lines documenting the removal, comment-only per Flash's own PB5 precedent).
- `ta_tgt` placeholder teaches the paste-back format + auto-clean note.

## C3 Flash Phase B amendment compliance (all 5 applicable)

| Amendment | Where it landed | Proof |
|---|---|---|
| 1 — valid_engines literal must be hand-updated | cell 8:662–668 dynamic `["manual"] + registry keys` | in-notebook Test 11 (nllb/gemini/chatgpt all rejected, runtime) |
| 2 — rebuild_mode_panel else-branch btn_nllb landmine | cell 25:534–537 defensive else, no deleted-widget refs | verify V4.2/V4.3 (code-lines grep + runtime AST) |
| 3 — _strip_llm_wrappers prefix-zone spec | cell 8:695–727 (+ hardening: header-containing lines never stripped) | in-notebook Tests 14/15 + harness V6.13–V6.15 |
| 4 — build_external_ai_copy must delegate | cell 25:173–195 delegates to build_ai_text_content | harness V6.5/V6.8/V6.9 (single row-walk counted) |
| 7 — persistence invariant wording | cell 25:562 + cell 1:441–455 banner | verify V4.6 |
(Amendments 5/6 are B3/B4-scoped — untouched by this batch, per the PM's scope directive.)

## C4 Verification record (all green; scripts persisted, re-runnable)

1. **Static:** AST-parse all 27 cells; untouched-cell byte-stability; non-source field identity; JSON byte-faithful writer round-trip. [TEST RESULT: verify V1–V2]
2. **Reference battery:** 16 legacy symbols absent from all code lines (comment-only documentation mentions remain — Flash PB5 precedent); 26 required new symbols present; hf_token kept. [TEST RESULT: V3]
3. **Runtime harness A — cell 8 full exec** (fake MANGABD_CONFIG/log_event/get_page/MANGABD_SECRETS): all **15 self-tests pass**, `Cell 8 result: SUCCESS`, engine restored to manual after the switch test, adapter restored after the monkeypatch test. This is the same proof class Flash used in Phase D for V-5 amendments. [TEST RESULT: V5]
4. **Runtime harness B — B2 round-trip** (cells 8+22+25-builder-slice in one namespace, fake 2-page translation_df): payload two-part structure verified (prompt on TOP, separator, OCR block; glossary merged; [SKIP:OCR_FAILED] carried); region count 6/3 by scope; **simulated external-LLM reply (preamble + fences) applies 3/3 with zero sentinel warnings**; translation_df updated with valid Bengali; wrapped continuation → sentinel VISIBLE (not silent); raw-payload paste → prompt auto-stripped, no crash; fence-glued data line kept. [TEST RESULT: V6]
5. **Fresh-run regression (M002 protocol):** static simulator v2 on the new notebook — **0 abort-class findings**; guard states, render_bengali_text binding chain, and the run_inpaint_render_all hunger table all byte-match the pre-edit baseline. New module-level calls (cell 25's mbtn batch + rebuild_mode_panel at cell 25:543) are all same-cell SAFE. [TEST RESULT]
6. **Comment-only refs disclosed:** cell 25:323 and cell 25:536 mention `gemini_key`/`btn_nllb` inside comments documenting their removal; zero functional references remain. [FACT]

## C5 Known-opens / notes for Phase D & Owner

- **A7-D7 live-Colab UNKNOWNs** (unchanged, designed fallbacks): `userdata.set()` dialog behavior for the STEP 0 persist button; clipboard-write permission in Colab output iframes. First live session (S005) checks both; neither can hard-fail the flow.
- **S005 acceptance proposal:** fresh page → Upload + Detect+OCR → COPY FOR EXTERNAL AI → paste into a real external LLM → paste reply → Apply → render. Metrics: parse-rate (0 unparsed on clean reply), sentinel behavior on wrapped/preamble variants, and a translation-quality read of the register/profanity handling vs the S003 NLLB baseline rows (A3.2 table). Plus the OpenRouter path with the Owner's key (S006-class live check was originally B2-scoped; both can ride one session if the Owner prefers).
- **Scope note:** the PM's B1 cell list said {1, 8, 15, 19, 25}; cells 17 (leak-test generalization) and 18 (command examples) were also edited — both items are on Flash's Phase B REQUIRED/EDITABLE list which the PM's directive incorporates by reference ("incorporating all of Flash's required amendments"), and leaving them would dangle references to purged key families/engines. Disclosed here for Phase D scope verification.
- **D3 register wording** (তুই/তুমি/আপনি table + curse-word register) ships as drafted from the S003 defect evidence; Owner taste review at S005 per Phase A.
- Cell 19's file-based rescue path is deliberately unstripped (machine-generated content; V-4a sentinel stays visible there) — Phase D may confirm or amend.
- Scripts (outside repo, re-runnable): `/home/z/my-project/scripts/m4_b1b2_build.py`, `m4_b1b2_patches{,2,3}.py`, `m4_b1b2_verify.py`; cell extractions `/home/z/my-project/m4c_cells/`; per-cell unified diff `/home/z/my-project/m4_work_diff.txt`.

**Branch `mangabd-004-b1-b2` — WIP commit, pushed for Flash Phase D verification. No other agent files or branches touched.**

## C6 RF-1 — Phase D required fix (2026-10-13)

**Trigger:** Flash Phase D verdict on `ab2aa36` = APPROVED_WITH_FIXES (`f460143`, E1/E3/E4/E5 PASS); sole required fix RF-1 — E2 purge gate: dead `"nllb"` config block survives in the live `MANGABD_CONFIG` literal (Flash citation cell 1:288–293 = 1-indexed source lines 289–295: `"nllb"` dict with `facebook/nllb-200-distilled-600M`, `eng_Latn`/`ben_Beng`, `num_beams: 4`, `max_length: 512`); zero consumers after the B1 purge; also lands in the saved `config_v12.json`.

**Change (exactly one hunk, nothing else touched):** removed those 7 source lines / 7 raw JSON lines (raw file lines 911–917 0-based) from `MANGABD_CONFIG["translation"]` (block sat between the `"prompt"` closer and the `"translation"` closer). Method: byte-level surgical line deletion on the raw notebook file (no JSON re-serialization) via `scripts/rf1_fix.py` — exact-content block match asserted unique, context anchors asserted, string-surgery equivalence proven, then all structural gates re-asserted (26/26 non-cell-1 sources byte-identical; non-source cell fields + top-level notebook fields identical; cell-1 AST parse). git numstat: **1 file, 0 insertions, 7 deletions, single hunk**.

**Verification — 33 checks ALL GREEN (`scripts/rf1_verify.py`):**
1. 27/27 AST parse; JSON round-trip byte-faithful. [V1]
2. Surgical scope: 1 file / 7 del / 0 ins / single hunk; cell 1 = pre minus exactly 7 contiguous lines; 26/26 other cells + all non-source fields byte-identical. [V2]
3. Notebook-wide scan: **zero live (non-comment) nllb/model-id references** — `facebook/nllb-200-distilled-600M`, `eng_Latn`, `ben_Beng` = 0 hits anywhere (incl. comments); remaining `nllb` mentions all adjudicated per Flash D2: c8:1628 `switch_translator("nllb")` rejection self-test (the purge proof), comment-only c8:660 / c19:2 / c25:538 (removal documentation, PB5 precedent). [V3]
4. Fresh `save_config()` round-trip on REAL cell-1 + cell-8 code (sandbox; two disclosed injections — minimal `MANGABD_ENV` from cell 0, `BASE_DIR` — everything else verbatim, real `OPENROUTER_API_KEY` env bootstrap): cell 1 self-tests SUCCESS; cell 8 15/15 self-tests; saved JSON deep-scan → **no nllb block**; `providers == ['openrouter']` with `key_env: 'openrouter_api_key'` + `base_url` + `model` intact; `api_key_env` control stripped live; pre-vs-post saved-config delta = **exactly the removed nllb block** (sandbox/SESSION_ID/created_at normalized). [V4]
5. m002_sim_v2 fresh-kernel contract: **0 abort sites** (post-fix); pre-fix control also 0; outputs identical modulo cell-1 line refs (each ref above the block shifted exactly −7, refs below unchanged) — behavioral equivalence proven. [V5]

**Commit:** follow-up on `mangabd-004-b1-b2` (on top of Flash's `f460143`, not amending `ab2aa36` — Flash's prescribed discipline), message: `MANGABD-004 RF-1: remove dead nllb config block (Phase D required fix)`. Pushed; merge remains gated on Flash RF-1 re-verification + Owner S005 (PM relay).

---

# MANGABD-004 — MERGE COMPLETION RECORD (GLM-5.3)

## C7 B1+B2 merged to main; branch deleted; MANGABD-004 CLOSED (2026-10-14)

- **Merge executed per the Owner's numbered final-merge directive** (relayed via PM Qwen3.8-Max, 2026-10-14) on Flash's S005 acceptance verdict **BOTH ACCEPT** (`c5fe8a9`, 2026-10-13 23:14 UTC; the branch was fetched and the full verdict record read from `agents/GLM_5_3_FLASH.md` §"MANGABD-004 — S005 ACCEPTANCE MEASUREMENT" before acting — S1–S5 all PASS). PM-relayed findings: OpenRouter path fixes every cited NLLB defect (R5, R6, R4, R1); manual path pixel-level proof of profanity/slang rendering; the manual-sidecar overwrite (engine: openrouter) adjudicated a documented session artifact, not a workflow defect; zero regressions; Batch 1/2/3 fixes intact. [FACT]
- **Pre-merge state verified this session:** `git fetch` → `origin/mangabd-004-b1-b2` advanced `7f0e653` → `c5fe8a9` (docs-only, +61 lines in GLM_5_3_FLASH.md); local branch ff-synced to `c5fe8a9`; main at `48fa3ca` (the S005 samples archive) up to date with origin/main; working tree clean; merge-base = `97a683a`; branch-vs-base diff = exactly 3 files (notebook + the two agent logs). [TEST RESULT]
- **Squash-merge:** `git merge --squash mangabd-004-b1-b2` on main — clean apply, zero conflicts (main has touched only samples/ + the two root ZIPs since `97a683a`). Pre-commit byte verification: working-tree notebook / `agents/GLM_5_3.md` / `agents/GLM_5_3_FLASH.md` md5-identical to the branch tip `c5fe8a9` (`08ad1b52059324bfda4ddcd0feddb1fc` / `615779d227591fb83e5cbd2d352f1098` / `0a14de61d1814e26ad902943152c1407`) — exactly the bytes Flash Phase-D-approved, RF-1-verified, and S005-accepted; staged diff = the same 3 files, nothing else. Commit **`156df93`** (full gate-chain message, MANGABD-004 CLOSED); pushed `48fa3ca..156df93` to origin/main. [TEST RESULT]
- **Squash commit contents (3 files, +905/−425):** notebook **+629/−423** (changed cells exactly {1, 8, 15, 17, 18, 19, 22, 25}; the other 19 cells byte-identical to `97a683a`); `agents/GLM_5_3.md` +106/−2 (Phase A + Phase C C0–C6 records + CURRENT PHASE headers, merged from the branch); `agents/GLM_5_3_FLASH.md` +170/−0 (Phase B review + Phase D verification with D-ADDENDUM + S005 acceptance measurement). Branch `mangabd-004-b1-b2` deleted local + remote immediately after the push (local tip at deletion `c5fe8a9`); the five branch commits (`ab2aa36`, `f460143`, `3c57583`, `7f0e653`, `c5fe8a9`) remain citable provenance — their net content lives exactly once, in `156df93`. [FACT]
- **Docs sync (this commit, sequenced after the squash per the PM directive):** `agents/DECISION.md` — STATUS header rewritten (MANGABD-004 B1+B2 merged, TASK CLOSED), "source modified exactly three times" corrected to four times, new §D.1 B1+B2 Merge Record; this file — CURRENT PHASE header rewritten + this §C7 record. Zero notebook/source changes in the docs commit. [FACT]
- **Pre-commit audit (docs commit):** 2 modified files, modes 100644, zero renames; secret-pattern scan (PAT/`sk-`/AKIA/AIza/hf_/PEM/bearer/xox/glab) of all added lines — 0 hits; working tree clean after commit; merge + docs commits both pushed and verified on origin/main. [TEST RESULT]
- **MANGABD-004 disposition: CLOSED.** B1 (OpenRouter-exclusive translation + dead-code purge) and B2 (advanced manual copy-paste) delivered, verified, accepted, merged. B3 (LaMa OOM-safe resolution ladder 2048→1536→1024→Telea) and B4 (OCR region-type prompt map) remain unauthorized proposals (Phase A §A6) — any future pursuit requires a fresh Owner directive and a fresh Phase A→D cycle on the then-current main. MANGABD-003 Batch 3 remains SUPERSEDED (A7-D1); branches `mangabd-003-batch3` + `mangabd-003-phase-c` preserved untouched as historical byte source. Next task awaits the Owner's directive. [FACT]

---

# MANGABD-005 — PHASE C (BATCH 1) (GLM-5.3, 2026-10-14)

## PC-C0 Scope, method & invariants

- **Directive (PM Qwen3.8-Max relay, Project-Owner authorized, 2026-10-14):** MANGABD-005 Batch 1 = B3 "LaMa Full Resolution". Target: **Cell 9 (Inpainting Service) ONLY** — "Do NOT touch any other cells." Fix: (a) upgrade the LaMa configuration to its full potential (up to 2048, upstream LaMa Large default); (b) OOM-safe resolution ladder — max-dim ≤ 2048 → NATIVE (no downscale), larger pages step down safely within VRAM limits; (c) verify `unload_all(exclude=["lama"])` runs before LaMa loads (T4 OOM prevention). Verification: self-tests for the ladder logic; m002_sim_v2 still 0 abort sites. Rules: single-hunk audit convention; record in this file; WIP commit on branch `mangabd-005-b1`; push and notify for Flash Phase D. All honored. [FACT]
- **Spec lineage:** Phase A §A4.3-P1 (`c196505`) — ladder `[owner_lama_size] + [s for s in (2048, 1536, 1024) if s < owner_lama_size]`, default 1024→2048, `inpaint_size_effective` in stage meta — as CONFIRMED by Flash Phase B (`97a683a`): retry idempotency is FACT (upstream `_infer` copies inputs at entry, zy `inpainting_lama_mpe.py:57–58`), exception taxonomy correct, T4 headroom analysis accepted, and **Amendment 5** folded in: the notebook's own deterministic `RuntimeError("LaMa returned empty result")` must NOT be ladder-retried — non-OOM errors belong to the existing OpenCV fallback. Phase A's P2 cell-25 hint-line and P3 rejected alternatives (tiling; unconditional-native; INTER_NEAREST mask resize) are NOT in this batch (cell 25 out of scope per the directive). [FACT]
- **Base state verified before any edit:** branch `mangabd-005-b1` cut from `main @ 5e70507`; working-tree notebook blob == `5e70507` == `156df93` (the M004 squash-merge content, md5 `08ad1b52059324bfda4ddcd0feddb1fc`); 27 cells extracted to `cells_m005/` (cell 9 sha16 `c4590252da2f7772`, 888 source lines); m002_sim_v2 pre-patch control: **0 abort sites**. [TEST RESULT]
- **Build method:** `scripts/m005_b1_build.py` — 5 anchored patches (each old-string asserted to occur EXACTLY once in cell 9), JSON writer proven byte-faithful on the pre-edit file (identical discipline to M004 Phase C / RF-1), AST gate before write-back. Invariants asserted post-edit: 26 non-cell-9 sources byte-identical to `5e70507`; non-source cell fields (metadata/outputs/execution_count) identical; top-level notebook fields identical. [TEST RESULT]

## PC-C1 Implementation — one logical change in cell 9 (5 anchored hunks, 888→1139 source lines; raw JSON +270/−19)

1. **Config default + legacy migration (patch 1, cell 9 §2):** `setdefault("lama_size", 1024)` replaced by a disclosed migration block: `_lama_size_legacy = cfg.get("lama_size")`; `if _lama_size_legacy is None or int(_lama_size_legacy) == 1024: cfg["lama_size"] = 2048`. **DISCLOSURE (for PM adjudication, zero functional impact either way):** the live 1024 in every fresh session actually originates from **cell 1:295** (`"lama_size": 1024` in the `MANGABD_CONFIG` literal) — cell 9's old `setdefault` never fired because the key always exists after cell 1; Phase A (§A4.1) and Flash Phase B both cited the throttle as cell 9:69 and neither flagged the cell-1 twin. Cell 1 is outside this batch's authorized scope ("Cell 9 ONLY"), so the default upgrade is implemented at cell-9 config-load time in the one cell we may touch. The upgrade is safe against deliberate Owner overrides: 1024 was **never Owner-selectable** (no widget exposes `lama_size` — Phase A P2; `config_v12.json` is write-only, nothing loads it back — verified this session), so 1024-in-config ≡ legacy default, while any other explicit value (e.g. 1536, 3072) is respected untouched. `config_v12.json` saved by future sessions will record 2048. Recommended 1-line cell-1 cleanup in a future authorized batch. [FACT + disclosure]
2. **`_is_cuda_oom(exc)` helper (patch 2, cell 9 §5):** message-match first (`isinstance(exc, RuntimeError) and "out of memory" in str(exc).lower()` — catches the legacy async-CUDA form), then belt-and-braces `isinstance(exc, torch.cuda.OutOfMemoryError)` under try/except (NameError-safe if torch is somehow absent; AttributeError-safe on old torch). Non-OOM errors return False. [FACT]
3. **OOM-safe resolution ladder (patch 3, inside `lama_inpaint_full`):** `ladder = [lama_size] + [r for r in (2048, 1536, 1024) if r < lama_size]`; the rung `try` wraps ONLY the `_run_async(lama.inpaint(...))` call. On OOM: save `last_oom`, `clear_gpu_cache()` (guarded — cell 5:139 helper, NameError-safe), WARN `log_event` + console line, `continue` to the next rung. On any non-OOM exception: bare `raise` — immediate propagation to `inpaint_page`'s existing `except` → OpenCV-Telea fallback (protected baseline, byte-stable). The deterministic `RuntimeError("LaMa returned empty result")` raise sits **outside the rung try** (structural guarantee of Amendment 5 — verified V3.7 by source-span check and V6.1 by call-count). Success path per rung: empty-check → `lama_inpaint_full.last_size_effective = size` (function attribute; zero call-signature changes — the optional live test at cell 9 §8 and any external callers keep working) → defensive resize-back → `return`. All-rungs-OOM: ONE `RuntimeError("LaMa OOM at every ladder size {ladder} — last error: …")` (caller's fallback then logs `fallback_used=True`). `cfg.get("lama_size", 2048)` — legacy 1024 default literal purged. [FACT]
4. **Stage meta (patch 4, `inpaint_page`):** meta dict gains `"inpaint_size_effective"` = `getattr(lama_inpaint_full, "last_size_effective", None)` when `engine_used == "lama"`, else `None` — every run records the rung that actually ran (lands in the manifest + sidecars; `inpaint_time_sec` regression tracking unchanged). [FACT]
5. **Embedded self-tests 8–10 (patch 5, cell 9 §7; count 7→10):** fake `model_manager`/`ensure_lama`→`_FakeLama` (async `inpaint` returning coroutines for the REAL `_run_async`) + counting `clear_gpu_cache`, all monkeypatched with save/restore in `finally` (M004-B1 cell-8 Test-12 pattern). Test 8: OOM at 2048 → success at 1536; asserts `sizes == [2048, 1536]`, `last_size_effective == 1536`, exactly 1 cache-clear, and **event order `[("unload_all", ("lama",)), ("ensure_lama",)]`** (the directive's VRAM-hygiene requirement, runtime-proven). Test 9: non-OOM `RuntimeError` and `None`-result each fail after exactly ONE rung attempt (Amendment 5 semantics). Test 10: all rungs OOM via `torch.cuda.OutOfMemoryError` instance → single RuntimeError naming the ladder; `sizes == [2048, 1536, 1024]`; `last_size_effective` stays `None`. [TEST RESULT]

**Byte-stable protected baselines inside cell 9 (verified):** mask discipline (`redilate_artifact_mask=False`, `mask_clip_to_regions=True`, `mask_clip_padding=10`, `mask_base_dilate_radius=6`), `unload_others=True` + `unload_all(exclude=["lama"])` block, `opencv_radius=5` TELEA fallback path, min_mask_pixels gate, cache/checkpoint logic, `inpaint_all_pages`, the §8 optional live LaMa test. Cell 9 section numbering untouched (Tests 8–10 live inside §7 Self-tests; §8 "Optional live LaMa test" keeps its number — cosmetic non-renumber, disclosed). [TEST RESULT]

## PC-C2 Verification record (44 checks, ALL GREEN; scripts persisted, re-runnable)

- **V1 integrity:** 27/27 AST-parse; `json.dumps(indent=2, ensure_ascii=False)` byte-identical to the on-disk file post-edit (no serialization drift anywhere in the 838 KB notebook). [TEST RESULT]
- **V2 scope:** exactly cell 9 differs vs `main @ 5e70507`; 26/26 others byte-identical; all non-source cell fields + top-level fields identical. [TEST RESULT]
- **V3 reference battery:** legacy literals gone (`setdefault("lama_size", 1024`, `cfg.get("lama_size", 1024)`); all new symbols present (ladder comprehension, `_is_cuda_oom`, `torch.cuda.OutOfMemoryError`, message-match, `last_size_effective` set/reset, `inpaint_size_effective`, final RuntimeError, `MANGABD-005 B1` markers); protected-baseline keys intact; **source order `unload_all(exclude=["lama"])` < `ensure_lama()` < ladder**; empty-result raise outside the OOM-try span. [TEST RESULT]
- **V4 migration matrix (exec of the REAL cell-9 config slice, 4 fresh namespaces):** `1024 → 2048` (the cell-1-dict case), `missing → 2048` (setdefault case), `1536 → 1536` (explicit value respected, no stomp), `2048 → 2048`. [TEST RESULT]
- **V5 runtime (exec FULL cell 9, fake globals + torch/manga_translator stubs, real numpy/cv2/asyncio):** clean exec; "Cell 9 result: SUCCESS"; **10/10 self-tests pass, zero ❌**; migration fired during exec (1024→2048); startup print now reads `LaMa size : 2048`; monkeypatch restore discipline proven (`model_manager` and `clear_gpu_cache` identity-restored; `lama_size` restored); `last_size_effective` left `None` after the all-OOM test. [TEST RESULT]
- **V6 ladder contract (real cell-9 functions, fake LaMa):** arithmetic over owner sizes — `1024 → [1024]` (today's behavior preserved for a deliberate 1024), `1536 → [1536, 1024]`, `2048 → [2048, 1536, 1024]`, `3072 → [3072, 2048, 1536, 1024]` (webtoon/oversize owner override respected), each ending in exactly one RuntimeError; **844×1200 page → single rung, size arg 2048** (upstream `zy d6de6ab` semantics: no resize when max(H,W) ≤ cap ⇒ native inference — the contract-level proof; live-T4 proof is Phase D per the Phase A plan); `torch.cuda.OutOfMemoryError` instance → steps down to 1536; result-shape resize-back preserved; **`inpaint_page` integration:** OOM step-down → `engine=lama`, `inpaint_size_effective=1536`, `fallback_used=False`, artifact saved, completion log; all-rungs OOM → OpenCV-Telea fallback, `engine=opencv`, `inpaint_size_effective=None`, `fallback_used=True`, 3 rung WARNs + 1 fallback WARN logged. [TEST RESULT]
- **V7 m002_sim_v2 (fresh-kernel static simulator) on post-patch cells:** **0 abort sites** (pre-patch control also 0); all unguarded module-level calls SAFE; sim output delta vs pre-patch = 1 informational line (cell-9 namespace-growth count) — no new hunger, no new abort-class findings; the migration if/else, helper defs, and Tests 8–10 are either simple defines or guarded try-bodies in the simulator's model. [TEST RESULT]
- **VRAM hygiene (directive item 3):** `unload_all(exclude=["lama"])` still runs BEFORE `ensure_lama()` — proven three ways: source-order check (V3.6), runtime event order inside Test 8 (`[("unload_all", ("lama",)), ("ensure_lama",)]`), and the block is byte-stable from the Phase-A-audited state (cell 9:370–377 → cell 5:563–571 with per-unload `clear_gpu_cache`, cell 5:143–148). [TEST RESULT]

## PC-C3 Known-opens / notes for Phase D, PM & Owner

- **VRAM magnitudes remain HYPOTHESIS-tagged** (Phase A §A4.3): the sandbox cannot measure a live T4. Phase D instrumentation plan stands: run the ladder on a real T4 with `torch.cuda.max_memory_allocated()` per rung; acceptance gate = the Owner's 844×1200 page completes at the native 2048 rung with measured peak < 12 GB. The ladder exists precisely to absorb the 2048×2048 worst case.
- **Native-resolution proof here is contract-level** (the size argument handed to `lama.inpaint` is 2048; upstream no-resize semantics for max-dim ≤ cap are cited from `zy d6de6ab`): the pixel-level side-by-side (Phase A's S007-style acceptance: the Owner's 844×1200 reference page, native rung, vs the S003 `inpainted.png` baseline) awaits Phase D + the Owner acceptance session, per the standing batch protocol.
- **cell 1:295 twin hardcode disclosure** (PC-C1.1): behavior is fully delivered by the cell-9 migration; the 1-line cell-1 cleanup (`"lama_size": 1024` → `2048`) is recommended for the next batch that is authorized to touch cell 1, so the literal matches the effective default. Flagged for PM adjudication — no action required for correctness.
- **Line-count delta vs Phase A estimate:** Phase A's "~+30/−2" covered the ladder core only; this batch adds ~165 lines of embedded self-tests (directive's explicit self-test requirement, M004-B1 precedent). Core ladder + migration + meta ≈ +86.
- **Flash Phase D re-runnable instruments:** `scripts/m005_b1_build.py` (anchored patch definitions + invariants), `scripts/m005_b1_verify.py` (44 checks), `scripts/m005_extract_cells.py` (baseline extraction + sha16 inventory), `scripts/m005_sim2.py` (parameterized m002_sim_v2), extraction dirs `cells_m005/` (pre) + `cells_m005_post/` (post).

---

# MANGABD-005 — BATCH 1 MERGE COMPLETION RECORD (GLM-5.3, 2026-10-15)

## PC-M1 Batch 1 (B3) merged to main; branch deleted; B1 CLOSED (2026-10-15)

- **Merge executed per the Owner's numbered final-merge directive** (relayed via PM Qwen3.8-Max, 2026-10-15) on Flash's S007 acceptance verdict **ACCEPT** (`93de3f8`; the remote branch was fetched and the verdict read from `agents/GLM_5_3_FLASH.md` before acting — G1–G4 all adjudicated, "verdict ACCEPT discharges mangabd-005-b1 merge gate"). PM-relayed verdict highlights: the Owner's 844×1200 page completed at the native 2048 rung (no OpenCV signature, in-mask strokes fuller-weight than the S003 baseline, tight zones r1/r4/r5/r6 all smoother), total ink 3636 vs 3714 (−78) with the r2 +6px deviation adjudicated AA fringe of a shared preserved stroke (zero new text residual), outside-mask cleaner than the baseline (81 vs 176 px>64; zero holes/smears), all 6 regions present/dark, r1 kana N-D tofu inherited unchanged (Batch-1 signature, non-regression), Bengali shaping correct. Directive: squash-merge (05bee82 + 5113f00 + 93de3f8) into main → delete branch local+remote → DECISION.md gate-chain record + tracked follow-ups → this file's completion record + CURRENT PHASE reconciliation (B1-closed and B2-in-progress coexisting) → report the merge hash → do NOT touch `mangabd-005-b2`. All executed. [FACT]
- **Pre-merge state verified this session:** `git fetch` → no new commits; local `main` @ `8445328` = origin/main (the S007 zip upload; notebook blob byte-identical to `5e70507`-lineage main); `origin/mangabd-005-b1` @ `93de3f8` (local branch pointer stale @ `05bee82` — the merge used the remote tip); `origin/mangabd-005-b2` @ `122e353` untouched throughout; working tree clean; merge-base = `5e70507`; branch-vs-base diff = exactly 3 files (notebook + the two agent logs — the Flash Phase D and S007 commits are docs-only, `agents/GLM_5_3_FLASH.md` +121). [TEST RESULT]
- **Squash-merge:** `git merge --squash origin/mangabd-005-b1` on main — clean 3-way apply, zero conflicts; `S007_mangabd005_02.zip` (added on main @ `8445328` after the branch fork, never touched by the branch) correctly preserved by the merge — the staged diff excludes it, and the file remains tracked (1,903,763 bytes) post-merge. Pre-commit byte verification: staged notebook / `agents/GLM_5_3.md` / `agents/GLM_5_3_FLASH.md` md5-identical to the branch tip `93de3f8` (`cc8d5aa24f850acefdf9623ba185be08` / `f0845873ac3b3b20b05668317c3a1f81` / `4357ea9ce2f98065fe8c3f6105c0ff3a`) — exactly the bytes Flash Phase-D-approved (`5113f00`) and S007-accepted (`93de3f8`); secret scan of added lines = 0 hits. Commit **`4d9b787`** (full gate-chain message, B1 CLOSED + B2-untouched note); pushed `8445328..4d9b787` to origin/main. [TEST RESULT]
- **Squash commit contents (3 files, +436/−20):** notebook **+270/−19** (changed cells exactly {9}; the other 26 cells byte-identical — single-logical-change convention held); `agents/GLM_5_3.md` +45/−1 (Phase C record PC-C0–PC-C3 + CURRENT PHASE header entries, from the branch); `agents/GLM_5_3_FLASH.md` +121/−0 (Phase D verification `5113f00` + S007 acceptance `93de3f8`, in commit order). Branch `mangabd-005-b1` deleted local + remote immediately after the push (local pointer at deletion `05bee82`, remote `93de3f8` — nothing lost: the net content lives exactly once, in `4d9b787`; the three branch commits remain citable provenance). [FACT]
- **Docs sync (this commit, sequenced after the squash per the PM directive, M004 §D.1/§C7 precedent):** `agents/DECISION.md` — STATUS header entry (MANGABD-005 B1 merged, TASK OPEN with Batch 2 in progress), "source modified exactly four times" corrected to five times, new §E.1 Batch 1 Merge Record with the gate chain + the three tracked follow-ups; this file — CURRENT PHASE header reconciled (new B2-in-progress cross-reference entry + the B1 entry rewritten to CLOSED with its gate chain + the M004 cross-ref updated) + this PC-M1 record. Zero notebook/source changes in the docs commit. [FACT]
- **Tracked follow-ups (per the directive, logged in DECISION.md §E.1; none blocking):** (1) cell-1:295 `lama_size` literal cleanup — align the pre-migration literal to the effective 2048 default in the next cell-1-authorized batch (behavior already delivered by the cell-9 migration; Flash E3 adjudicated the warm cell-1 re-run revert as bounded/self-healing/observable); (2) r1 kana tofu (N-D) — the cosmetic CJK-fallback backlog item, unchanged since the Batch-1 signature; (3) acceptance-zip metadata.json export — future acceptance zips should carry `notebook_commit` + per-page stage meta (`inpaint_size_effective` is already emitted; G1 then needs no pixel fallback). [FACT]
- **MANGABD-005 disposition: BATCH 1 CLOSED; TASK OPEN.** B3 (LaMa full resolution) delivered, verified, accepted, and merged as `4d9b787`. Batch 2 (lenient paste-back parser) remains in progress on `mangabd-005-b2 @ 122e353` — Phase C + 60-check self-verification delivered on the branch, awaiting Flash Phase D and the Owner's acceptance sample; NOT authorized to merge. When the B2 gate chain completes, its squash-merge must reconcile this file's CURRENT PHASE header (the B1-closed entries here + the branch's B2 records) and DECISION.md (§E.1 + a new Batch 2 merge record). Next gate: Flash Phase D on the pushed B2 bytes. [FACT]

---

# MANGABD-005 — PHASE C (BATCH 2): LENIENT PASTE-BACK PARSER (GLM-5.3, 2026-10-15)

## PC2-C0 Scope, method & invariants

- **Directive** (PM Qwen3.8-Max relay of Owner authorization, 2026-10-15): MANGABD-005 Batch 2 — "LENIENT PASTE-BACK PARSER (Owner pain point)". Branch `mangabd-005-b2` from main; scope **cells {8, 22, 25} ONLY** (parse_ai_text; _parse_ai_text_local + apply flow; paste-back UI + copy-payload builder/System Prompt). Goal: **any paste containing [page:id] tags must apply, regardless of cosmetic format.** Hard guarantees: V-4a sentinel + unparsed report preserved (never silent); one-line summary print of variants used (unescaped N, arrowless M, stem-matched K); copy-payload System Prompt amendment ("NEVER escape brackets with backslashes; keep tags exactly [page:id]; one line per region."); self-tests MUST include the Owner's three real samples as fixtures (escaped+arrowless Bengali-only / escaped+arrow / raw+arrow — 100% parse each) + a negative fixture (tag-less junk → reported, not applied); m002_sim_v2 = 0 abort sites; wire format export unchanged; WIP commit → Flash Phase D. [FACT]
- **Base state:** branch cut from `main @ 8445328` (the Owner's S007 zip upload; the notebook blob is byte-identical to `5e70507`/`156df93` — md5 `08ad1b52…`), so the B2 baseline == the M004-merged content. Batch 1 (B3 LaMa ladder) is NOT in this branch's base — it lives on `mangabd-005-b1` (05bee82 → Flash Phase D APPROVED 5113f00 → S007 ACCEPT 93de3f8, gate discharged, unmerged). The two batches touch **disjoint cell sets** (B1: cell 9; B2: cells 8/22/25), so both can merge independently; the ONLY overlap is this docs file — the B1 branch and this branch each add their own MANGABD-005 CURRENT-PHASE entry, which will need a trivial docs reconciliation at merge time (flagged for PM; neither branch's notebook bytes conflict). [FACT]
- **Method:** `scripts/m005_b2_build.py` — 14 anchored patches (every old-string asserted to occur EXACTLY once in its cell), byte-faithful JSON round-trip writer proven on the pre-edit file, AST gate on all edited cells, all 24 non-target cells asserted byte-identical post-edit, non-source cell fields (execution_count/outputs/metadata) untouched. Verification: `scripts/m005_b2_verify.py` (60 checks, all green) + `scripts/m005_b2_extract_cells.py` (post-build cell inventory for the sim) + `scripts/m005_sim2.py` (m002_sim_v2). [TEST RESULT]

## PC2-C1 Implementation (14 anchored hunks, cells 8/22/25 only)

**Cell 8 (7 hunks, 1846 → 2211 lines, sha16 `49c65fe11e19ac41`):**
1. `manual_copy_prompt` STRICT FORMAT RULES gains rule 5 — the PM amendment text verbatim: "NEVER escape brackets with backslashes; keep tags exactly [page:id]; one line per region." (This is the copy-payload TOP part; cell-25's builder delegates to it, so the amendment rides every COPY FOR EXTERNAL AI payload.)
2. Module-level lenient regexes after `_PURE_FENCE_RE`: `_MBD_B2_ARROW_RE` (`->|=>|→|⇒|➔|➡` — the PM's four arrows PLUS the two legacy heavy arrows cell 22 already accepted, kept accepted: strictly more lenient, disclosed), `_MBD_B2_TAG_RE` (unanchored, for the blob split), `_MBD_B2_LINE_RE` (the PM-spec line regex, leading-whitespace tolerant).
3. `parse_ai_text` fully rewritten lenient + helpers `_mbd_page_stem` (strip extension + trailing `_<digits>`, case-insensitive), `_mbd_session_pages` (page + page_id columns, guarded), `_PLACEHOLDER_REMAINDERS` (`{"", "()", "(-)", "-", "n/a"}` — lowercase compare). Pipeline in the PM's exact order; **step 4 FIRST-arrow split supersedes the M004 last-arrow rsplit (directive text: "translation = text after FIRST arrow")**; step 5 arrowless remainder: Bengali codepoints → accepted as translation-only (`original_text=""`), else unparsed with the hint `source-only line? (no Bengali after tag)`; step 6 placeholder check applies to BOTH the no-arrow remainder and the post-arrow translation; step 7 page resolution exact-first → unique stem (accept + note) → ambiguous (unparsed report) → **zero candidates keeps the raw page** (the apply-side parsed-N vs applied-M count gap surfaces it visibly — no silent drop, no over-rejection); step 8 duplicates last-wins (existing semantics) + counted. The V-4a `("_unparsed", 0)` sentinel is EXTENDED (`unparsed_lines` / `skipped_lines` / `stem_notes` / `stats{unescaped,arrowless,stem_matched,duplicates,placeholder_skipped,split_blobs}`) and attaches whenever ANY report field is non-empty — a fully strict parse produces NO sentinel (M004 output parity for clean pastes).
4. `translate_manual_upload` pops the sentinel before merging (count truthfulness for the file-upload path).
5-7. Self-tests: **Test 4** updated to the placeholder-skip contract ("No translation →" is now a reported skip, not a silent empty entry); **Test 5** updated to the FIRST-arrow contract (renamed "parse_ai_text arrow-first (B2)"; the old "arrow-safe" expectation `translated=="যাও এখন"` was the M004 last-arrow behavior, superseded by directive step 4 — disclosed spec change, not a silent baseline edit); **Tests 16-22** new: Owner sample (a) escaped+arrowless Bengali-only, (b) escaped+arrow, (c) raw+arrow (100% parse each, stats asserted), tag-less junk negative fixture (sentinel-only, zero data entries), single-line multi-tag blob split, placeholder battery (4 skips + 1 good), stem-match/ambiguous battery with monkeypatched `translation_df` (save/restore in finally). Tests 16-21 run inside a deterministic empty-session sandbox (`translation_df = pd.DataFrame()` forced, restored in finally) so cell 8 re-runs mid-session stay deterministic.

**Cell 22 (5 hunks, 486 → 674 lines, sha16 `952d5abff984b2f4`):**
8. `_parse_ai_text_local` rewritten as a self-contained mirror of the cell-8 pipeline (local regexes/helpers with distinct `_LOCAL_*` names — no redefinition cross-talk; the fallback works when cell 8 is not loaded) + same extended sentinel.
9. `apply_translations_from_text` gains the **pre-unescape step BEFORE `_strip_llm_wrappers`** (PM step 1 "before any regex"): escaped header lines now set the wrapper-stripper's `seen_header` flag, so wrapped continuations after fully-escaped replies reach the V-4a sentinel instead of being silently eaten by the Amendment-3 preamble zone — a gap found and closed during design (V5.13 proves it). The pre-unescape count merges into the summary line (double-unescape safe, idempotent).
10. Apply-flow report block rewritten: reads the extended sentinel, prints the V-4a ⚠️ unparsed warning (unchanged semantics, now ALSO fires when the sentinel is stats-only), the ⏭️ placeholder-skip report, the 🟡 stem-match notes, and the **one-line variant summary** `📋 Lenient variants used: unescaped=N, arrowless-Bengali=M, stem-matched=K, duplicates=D, skipped=S`. Entry-count arithmetic fixed to subtract the sentinel whenever present. Existing apply semantics preserved verbatim (`apply_manual_translation` first, `_apply_translations_fallback` fallback, normal/rescue counting, pre-render coverage report).
11-12. Paste-back UI hints: `show_text_for_translation`'s instruction block and `step_3_manual_translate_paste`'s Textarea placeholder now advertise the lenient acceptance (escaped brackets, `->`/`=>`/`⇒` arrows, arrowless Bengali-only lines).

**Cell 25 (2 hunks, 579 → 579 lines, sha16 `f92f6395d1478330`):**
13-14. `ta_tgt` paste-back Textarea placeholder + `on_copy_ai`'s final say() hint extended with the lenient acceptance (Bengali UI copy, consistent with the cell's style). The copy-payload BUILDER itself (`build_ai_text_content` / `build_external_ai_copy`) is byte-identical — the System Prompt amendment lands via the cell-8 template (V3.17).

## PC2-C2 Verification record (scripts/m005_b2_verify.py — 60 checks ALL GREEN)

1. **V1** AST 27/27; writer byte-faithful post-edit; no invalid-escape (SyntaxWarning/DeprecationWarning) compile of the 3 edited cells. **V2** scope exactly {8,22,25}: 24 other cells + all non-source fields byte-identical to `main @ 8445328`.
2. **V3 static battery (18 checks):** rule 5 present; old `rsplit` splits purged from both parsers; FIRST-arrow + placeholder + stem + sentinel-extension + unescape + blob-split markers present in both parsers; `translate_manual_upload` pop; apply summary/skip/stem prints; UI hints; tests 16-22 present; **wire format: `export_ai_text` source byte-identical, cell-25 builder source byte-identical, `apply_manual_translation` source byte-identical** (apply semantics kept).
3. **V4 runtime (7 checks):** cell 8 execs clean in the fake-globals harness; "Cell 8 result: SUCCESS"; **all 22 self-tests present + passing** (the 15 M004 tests with Tests 4/5 contract-updated + 7 new B2 tests); zero ❌; engine restored; system prompt carries rule 5.
4. **V5 runtime apply battery (24 checks):** Owner fixtures (a)/(b)/(c) apply 2/2 each with the correct summary line (unescaped=2, arrowless=2 / 0; strict paste (c) prints NO summary — M004 output parity); df updated with Bengali + `manual` engine; M004 fenced reply regression 3/3 with no unparsed warning; postamble 3/3 + sentinel visible; **junk 0-applied visible** ("No valid lines found"); placeholder paste 0-applied + ⏭️ + `skipped=3`; **stem-match: paste `[02.jpg:1]` applies to session `02_1.jpg` with the 🟡 note + `stem-matched=1`**; single-line blob 2/2; duplicate paste last-wins + `duplicates=1`; local-parser parity on fixtures (a)/(b); escaped reply + wrapped continuation → 1 applied + sentinel visible (the pre-unescape gap fix); cell-25 builder slice execs clean; payload = 6 regions, two-part, rule 5 on TOP; raw payload paste-back 0-applied, no crash, skip report visible (M004 V6.14 semantics preserved).
5. **V6 regression:** m002_sim_v2 — baseline (main) 0 abort sites, B2 cells **0 abort sites**.
6. **V7 wire-format runtime smoke:** `export_ai_text` runs clean; txt header + `[page:id] original → translation` lines + `[SKIP:OCR_FAILED] →` preserved; JSON sidecar 6-key schema, 6 rows.

## PC2-C3 Known-opens / notes for Phase D & PM

- **Spec-superseded tests (disclosed, not silent):** cell-8 Tests 4/5 were updated because the directive's step 4 (FIRST arrow) and step 6 (placeholder skip) redefine the M004 parse contract. Test 5's old expectation (`"Go → now → যাও এখন"` → `"যাও এখন"`) is now `"now → যাও এখন"` — the FIRST-arrow semantics, per directive. Flash should confirm this reading (V5.3b + Test 5).
- **Fixture provenance:** the Owner's three real samples were specified by shape ("escaped + arrowless Bengali-only lines", "escaped + arrow lines", "raw + arrow lines"); no literal sample text was available in the repo/relay. Fixtures were constructed with S005-attested Bengali content ("সালা সে কে!?", "মাদারচোদ!? কুত্তার মেয়ে" — the S005 manual-path translations). If the Owner has literal sample text, Phase D can swap fixtures without design change.
- **Arrow-set superset (disclosed):** PM step 4 lists `->, =>, →, ⇒`; the implementation also keeps `➔`/`➡` which cell-22's M004 parser already accepted — strictly more lenient, aligned with the batch goal.
- **Placeholder scope (disclosed):** step 6's placeholder check is applied both to the no-arrow remainder (as specified) and to the post-arrow translation (e.g. "English → N/A" → skip+report) — the translation side is part of the remainder; skipping an "N/A" translation is safer than applying it as literal text.
- **Sentinel attachment:** the extended sentinel attaches whenever any report field is non-zero (including stats-only pastes); `translate_manual_upload` and the cell-22 apply loop both treat it as report-only (pop / skip), so no count inflation anywhere.
- **Docs-merge note:** B1 (`mangabd-005-b1`) and this branch each edit GLM_5_3.md's CURRENT PHASE header; notebook bytes are disjoint (cell 9 vs cells 8/22/25) — reconcile the header at merge time (trivial docs conflict, flagged to PM).
- **Re-runnable instruments:** `scripts/m005_b2_build.py`, `scripts/m005_b2_verify.py`, `scripts/m005_b2_extract_cells.py`, `scripts/m005_sim2.py`, `cells_m005_b2/` (post-build inventory).

---

# MANGABD-005 — B2 REQUIRED FIX RF-2: DATAFRAME-SAFE SELF-TEST SENTINEL (GLM-5.3, 2026-10-15)

## PC2-RF2 Owner live-run crash → identity sentinel + live-state fixture

- **Defect (live-only, functional code NOT at fault).** The Owner's live Colab run of this branch (cell 8) crashed in the self-test battery's finally block (~line 2078): `if _b2_saved_df == "__unset__":` → `ValueError: The truth value of a DataFrame is ambiguous.` Root cause: a live session's cell 3 pre-loads `translation_df`, so the battery's save captured a **DataFrame**; `df == "__unset__"` evaluates to a boolean DataFrame and `if` on it is ambiguous. Sandboxes had no pre-existing df (saved value was the string sentinel), hence 22/22 there — a harness blind spot, not a parser defect. [FACT — PM relay with the Owner's traceback]
- **Second instance found and fixed (same class, same block).** Test 22's save/finally used the identical string-sentinel pattern (`_saved_df22`); once the battery's finally was fixed, the same crash would fire one block later in a live session. Both sites are inside the cell-8 self-test block (the authorized scope); both now use the identity sentinel. [TEST RESULT — V5 negative control + code]
- **Fix (PM directive items 1-2, cell 8 self-test block ONLY, 5 anchored patches):** (1) `_B2_UNSET = object()` identity sentinel — all four save sites (`_b2_saved_df`, `_saved_df22`, and Test 23's inner/outer saves) use `globals().get("translation_df", _B2_UNSET)`; both finally checks use `is _B2_UNSET` (never evaluates the DataFrame); the string literal `__unset__` is fully purged from cell 8. (2) New **Test 23 (live-state regression fixture)**: pre-seeds a real 2-row DataFrame (pages `live_1.jpg`/`live_2.jpg` — non-colliding with battery page ids) into `globals()["translation_df"]` BEFORE a battery-shaped save/overwrite/restore cycle, then asserts the restore returns the **exact same object** with `pickle.dumps` **byte-identity**; an outer save/restore wrapper keeps the test itself traceless in both sandbox and live states. Self-test battery: 22 → 23. [TEST RESULT]
- **Verification (scripts/m005_b2_rf2_build.py + m005_b2_rf2_verify.py — 34 checks ALL GREEN):** V1 static — AST clean, sentinel counts (1 definition, 4 saves, 4 `is` checks), `__unset__` purged, functional spans (`parse_ai_text`/`export_ai_text`/`apply_manual_translation`) byte-identical to `122e353`, new cell 8 == old + EXACTLY the 5 patches (re-derivation equality), difflib opcodes = the 5 patches (patch 1 splits into an adjacent insert+replace pair). V2 scope — 26 non-target cells byte-identical to `122e353`; cell-8 non-source fields + top-level notebook fields identical. V3 runtime sandbox — cell 8 execs clean, 23/23 self-tests green, zero failures, `translation_df` absent post-exec (pop path), engine restored to manual, copy-payload rule 5 intact. **V4 runtime live-state (the directive scenario)** — pre-seeded real 2-row `translation_df` before exec: 23/23 self-tests green, zero failures, and post-exec `translation_df` IS the pre-seeded object, pickle-byte-identical (restore path). V5 negative control — the PRE-FIX bytes (122e353) crash in the same live-state harness with the Owner's exact ValueError, AFTER the battery ran (finally block, not mid-test). V6 — m002_sim_v2 on post-RF-2 cells: **0 abort sites**; only cell 8 differs from the Phase C extraction (`cells_m005_b2` → `cells_m005_b2_rf2`). [TEST RESULT]
- **Invariants held:** no other cell touched (cell 8 only, +65 source lines 2211→2276); wire format untouched (functional spans byte-identical); M004-B1 test patterns (Test 22's save/restore discipline) preserved modulo the sentinel swap; notebook written by the byte-faithful JSON writer (round-trip proven pre-edit, 26-cell byte-identity post-edit). Re-runnable: `scripts/m005_b2_rf2_build.py` (5 anchored patches + static gates), `scripts/m005_b2_rf2_verify.py` (34 checks), `scripts/m005_sim2.py`, extraction dirs `cells_m005_b2_rf2/` (post) vs `cells_m005_b2/` (Phase C). [FACT]
- **Status:** landed as follow-up commit on `mangabd-005-b2` (no amend of `122e353`, no merge — Flash's prescribed RF path from the M004 precedent); branch pushed for **Flash delta verification** (delta = the 5 cell-8 patches only). B2 merge gate unchanged: Flash Phase D + Owner acceptance + Owner merge authorization. [FACT]

---

# MANGABD-005 — B2 REQUIRED FIX RF-3: TRAILING-ARROW PARSER FALLBACK + NEW SYSTEM PROMPT + OWNER FIXTURE (GLM-5.3, 2026-10-17)

## PC2-RF3 Owner live-retest edge case → trailing-arrow fallback + Owner-authored 10-section prompt + Test 24

- **Defect (live retest, parser path — third paste-back shape from the Owner's real ChatGPT replies).** ChatGPT placed the Bengali BEFORE the arrow and left the arrow EMPTY at line end: `[02.jpg:1] English source → বাংলা অনুবাদ →` / the Owner's real sample `[02.jpg:1] T/L note: … উচ্চারিত হয় →`. `parse_ai_text` splits at the FIRST arrow, sees empty text-after-arrow → `""` lands in `_PLACEHOLDER_REMAINDERS` → placeholder skip → **0 apply**; the Owner had to delete the trailing arrow by hand to apply. Root-cause layer: the placeholder-skip check (B2 step 6, post-arrow side) fires before any Bengali-content inspection of the pre-arrow side, so a translation that arrived LEFT of a dangling arrow was unrescuable. [FACT — PM relay with the Owner's 6-line real output]
- **Fix Part 1 — trailing-arrow fallback (parse_ai_text, AFTER the FIRST-arrow split, BEFORE the placeholder check).** If the text-after-arrow is empty/whitespace-only AND the text-before-arrow contains Bengali codepoints (`validate_bengali`), the pre-arrow text becomes the translation with `original_text = ""` — exactly the B2-step-5 arrowless-rule semantics, which is also what the Owner's manual workaround (delete the arrow → arrowless path) did. New stats category `"trailing_arrow"`; English-only pre-arrow + empty post-arrow **stays a reported placeholder skip, never an apply** (Tests 4/21 contract preserved — required by the directive's 23/23 regression gate). [TEST RESULT — V3.10/V3.12/V5]
- **Fix Part 2 — Owner-authored system prompt (verbatim replacement).** `MANGABD_CONFIG["translation"]["manual_copy_prompt"]`: the M004 register/rules template is replaced by the Owner's 10-section localization-engine prompt (format contract / natural Bengali / profanity fidelity / JP-KR expressions / address forms / emotional voice / short reactions / OCR errors / consistency / final silent QC / final directive), all line breaks preserved, as a **raw triple-quoted literal** because section 1 contains the literal backslash-bracket sequence `"\[PAGE:ID]"` (a non-raw literal would raise SyntaxWarning under the project's warnings-as-errors gate — the Phase C escape-level lesson applied preemptively). The builder chain is untouched: `_build_external_ai_system_prompt()` (cell 8) reads the config key dynamically and cell 25's clipboard builders call it dynamically, so the new prompt rides every COPY payload with zero cell-25 changes; glossary merge path unchanged (V3.7). A7-D3 (Owner taste review of the prompt wording) is discharged by construction — the wording is the Owner's own. [TEST RESULT]
- **Fix Part 3 — Test 24 (the Owner's real 6-line trailing-arrow output as a fixture).** All 6 lines (T/L note with kana `こがねい`/`おてあらい`… verbatim from the relay, including the unclosed quote in line 2) parse → 6/6 entries with `original_text == ""` and byte-exact expected translations; `trailing_arrow == 6`; visible summary line asserted (`"trailing-arrow=6"` in captured stdout); then a REAL `apply_manual_translation` call against a 6-row session df → **applied == 6** with `translator_engine=manual`, `bengali_valid` all True, `status` all `translated`; negative control `[02.jpg:9] English →` → reported placeholder skip, no entry. [TEST RESULT]
- **Live-state hardening (RF-2 lesson, applied by design not by directive):** `save_translation_df` is defined in cell 3 — BEFORE cell 8 in every live sequential run — so Test 24's apply would otherwise call the REAL save and write the throwaway 6-row fixture df over the Owner's live CSV. Test 24 therefore monkeypatches `save_translation_df` with a no-op counter (saved/restored in the finally, `_B2_UNSET` identity-sentinel pattern) and asserts the shield fired exactly once; the battery stays disk-inert in both fresh and warm kernels (V4.8 canary proof). [TEST RESULT]
- **Verification (`scripts/m005_b2_rf3_preflight.py` + `m005_b2_rf3_build.py` + `m005_b2_rf3_verify.py` — 42 checks ALL GREEN):** preflight — baseline battery green, defect reproduced on pre-fix bytes (0 apply / placeholder_skipped=6), all 6 expected values byte-exact vs the FIRST-arrow split, `clean_translation` no-op on all 6. Build — 7 anchored patches (each old-string/splice-span unique-asserted; the 50-line old template removed by a marker-bounded span splice whose ACTUAL removed bytes are recorded in the patch manifest), byte-faithful JSON writer proven pre-edit, AST gate no-warnings, 26 non-target cells byte-identical. Verify V1 static — fallback/counter/print markers; Owner prompt present (all 11 headers) + old template fully purged; RF-2 sentinel invariants carried (1 def, 5 df saves, 6 `is` checks, 1 save-fn save, `__unset__` still absent); functional spans `export_ai_text`/`apply_manual_translation`/`translate_manual_upload` byte-identical to `29c17ba`; **re-derivation equality: old cell 8 + EXACTLY the 7 manifest patches == new cell 8**; difflib non-equal opcodes = 7. V2 scope — 26 non-target cells byte-identical to `29c17ba`; cell-8 non-source fields + top-level fields identical; **cells 22 + 25 byte-identical** (paste flow + payload builders). V3 runtime sandbox — 24/24 self-tests (23 RF-2 + Test 24), zero failures, `translation_df` popped post-exec, engine restored, new prompt in payload with glossary, old wording absent, Owner paste 6/6 with visible `trailing-arrow=6` line, negative skip. V4 runtime live-state (pre-seeded real df + canary save hook) — 24/24 green, post-exec df IS the pre-seeded object pickle-byte-identical, canary save NEVER called + still installed (disk shield). V5 negative control — PRE-FIX bytes (29c17ba) parse the Owner's exact paste to 0 entries + placeholder_skipped=6: the defect reproduced and RF-3 proven as the fix. V6 — m002_sim_v2: **0 abort sites**; only cell 8 differs from the RF-2 extraction. [TEST RESULT]
- **Invariants held:** cell 8 ONLY (+382 source lines, 2276→2658; notebook raw +435/−53); every other cell byte-identical to `29c17ba`; wire format + apply semantics + export path untouched (functional spans byte-identical); V-4a sentinel never silent — the trailing-arrow rescue is counted AND printed; single logical change per RF (parser fallback + its Owner-specified prompt/fixture riders, one commit). [FACT]
- **Interpretation disclosures (for Flash delta check):** (1) *"the Bengali portion (after the source text)"* is implemented as **the whole pre-arrow text** when it contains Bengali — the arrowless-rule semantics; for the Owner's 6 real lines (5 pure Bengali + 1 mixed T/L note) this is exactly the desired behavior and keeps the T/L note's `T/L note: Koganei-কে…` prefix intact instead of severing it mid-name; a hypothetical English-prefix+Bengali-suffix line would apply the full mixed text. (2) The directive's *"new category in the summary print"*: the combined `📋 Lenient variants used:` line lives in the **cell-22** paste flow — outside RF-3's cell-8-only scope — so the `trailing-arrow` count surfaces via a parse-level visible line (`📋 Lenient variant used: trailing-arrow=N …`) emitted by `parse_ai_text` itself on EVERY parse path (paste-back, file upload, self-tests); merging the category into the cell-22 line is a 1-line cell-22 change for a future authorized RF. (3) The negative case reports via the placeholder-skip channel (`skipped_lines` + `placeholder_skipped` + cell-22 `⏭️` print), not `unparsed_lines` — forced by the directive's own 23/23 regression gate (Tests 4/21 assert the placeholder-skip contract). (4) New prompt semantics vs parser markers: the prompt instructs `[SKIP]` (bare) after the arrow for unrecoverable regions, superseding the old `[SKIP:OCR_FAILED]`-copy-unchanged convention; a literal `[SKIP]` is NOT in `is_special_marker`'s set — flagged for PM (cosmetic, prompt-side intent vs marker set, no parser change made).
- **Status:** follow-up commit on `mangabd-005-b2` (no amend, no merge — the prescribed RF path); branch pushed for **Flash delta verification** (delta = the 7 cell-8 patches + this GLM_5_3.md record only, on top of Flash's RF-2 CLOSED @ 29c17ba). B2 merge gate unchanged: Flash Phase D + RF-3 delta check + Owner live retest + Owner merge authorization. [FACT]
- **Re-runnable instruments:** `scripts/m005_b2_rf3_preflight.py`, `scripts/m005_b2_rf3_build.py` (7 anchored patches + manifest), `scripts/m005_b2_rf3_verify.py` (42 checks), `scripts/m005_b2_rf3_patches.json` (manifest), `scripts/m005_sim2.py`, `cells_m005_b2_rf3/` (post-RF-3 extraction). [FACT]

---

# MANGABD-005 — B2 REQUIRED FIX RF-4: BARE [SKIP] MARKER-SKIP HANDLING (GLM-5.3, 2026-10-17)

## PC2-RF3 disclosure (4) → PM pre-ruling → verify-first gate DISCHARGED (defect confirmed) → conditional micro-fix landed

- **PM pre-ruling (conditional micro-fix).** The PM pre-ruled on the PC2-RF3 interpretation disclosure (4) ("new prompt's bare `[SKIP]` vs `is_special_marker` set — prompt-side intent, no parser change"): FIRST verify end-to-end on the c5f51c4 bytes whether the line `[02.jpg:3] SOME TEXT → [SKIP]` would be stored/applied as literal translation text; only if so, implement the micro-fix (cell 8 ONLY: after translation extraction, `translation.strip().upper() in {"[SKIP]", "[SKIP:OCR_FAILED]"}` or `is_special_marker(translation)` → do NOT apply; visible skip report with reason "marker"; new variant counter "marker-skip"); if already a clean visible skip, record evidence and commit NOTHING. [FACT — PM directive]
- **Verify-first gate (`scripts/m005_b2_rf4_preflight.py`) — DEFECT CONFIRMED on c5f51c4, both apply shapes, with save-hook persistence.** The Owner's new 10-section prompt (RF-3 Part 2, section 6) instructs the external AI: *"If a source region is genuinely untranslatable … use "[SKIP]" after the arrow."* End-to-end on the c5f51c4 cell-8 bytes: (a) **PARSE** — the line matches the tag regex, the FIRST-arrow split extracts `translated_text="[SKIP]"`; the RF-3 trailing-arrow fallback does not fire (post-arrow non-empty); `[SKIP]` is NOT in `_PLACEHOLDER_REMAINDERS` and NOT in `is_special_marker`'s set (only `[SKIP:OCR_FAILED]` is a member) → a raw entry is appended and **NO sentinel/report attaches** (stats all zero) — the line is invisible except as a would-be translation. (b) **APPLY dict-shape** (`translate_page` cache-rebuild / `translate_all_pages` flow) — `clean_translation` is a no-op on `[SKIP]` → **stored literally**: `translated_text="[SKIP]"`, `translator_engine="manual"`, `bengali_valid=False`, `status="non_bengali"`, `applied=1`, and `save_translation_df` FIRES (the literal persists to the CSV/JSON artifacts in a live run). (c) **APPLY string-shape** — the cell-22 paste loop extracts `translated_side` into a plain-string dict → same literal storage (the Owner's live paste path). (d) **`is_special_marker` arm** — `[02.jpg:4] OTHER → [SKIP:OCR_FAILED]` is also stored literally (status="marker", still counted as applied). Controls already clean pre-fix: empty post-arrow → visible placeholder skip; export-side `[SKIP:OCR_FAILED] →` (marker pre-arrow, empty post-arrow) → visible placeholder skip. **Verdict: the micro-fix is REQUIRED.** [TEST RESULT]
- **Fix (6 anchored patches, cell 8 ONLY, `scripts/m005_b2_rf4_build.py`):** (1) `parse_ai_text` docstring — step 6 gains the marker-skip rule. (2) Stats dict gains `"marker_skipped": 0` (the PM's "marker-skip" variant counter — name snake_case-normalized to match the `placeholder_skipped`/`trailing_arrow` siblings, disclosed below). (3) **The marker check, AFTER translation extraction** (and after the disjoint placeholder check, inside the arrow branch): `_marker_t = translated_text.strip()`; if `_marker_t.upper() in ("[SKIP]", "[SKIP:OCR_FAILED]")` or `is_special_marker(_marker_t)` → `stats["marker_skipped"] += 1`, `skipped.append(f"{page_raw}:{region_id} → {translated_text!r} (marker)")`, `continue` — never an entry, never applied, reason "marker" visible in the skip report. (4) Parse-level visible print `⏭️ marker-skip: N ([SKIP]/special-marker translation(s) reported, not applied)` (RF-3 trailing-arrow pattern — the combined lenient-variant line is cell-22 = out of the cell-8-only scope; the entries also ride the sentinel's `skipped_lines`, so the cell-22 `⏭️ … skipped:` print shows them with the "(marker)" reason). (5) **Apply-level guard** in `apply_manual_translation`, AFTER `clean_translation` (belt-and-braces): the same condition → visible `⏭️ Marker translation not applied: {page}:{region_id} → …` + row skipped. Covers plain-string dicts (the cell-22 paste loop's shape), quoted markers `'"[SKIP]"'` that `clean_translation` unwraps after the parse check, and the `translate_page` cache-rebuild dict shape. (6) **Test 25** — the PM self-test: 4-line fixture (bare `[SKIP]`, set-member `[SKIP:OCR_FAILED]`, case-insensitive `[skip]` → parse-level skips with counter=3, reason "(marker)", visible print asserted; quoted `"[SKIP]"` → parse keeps the entry, apply guard refuses it after unquoting); apply dict-shape `applied==0`, df untouched (all `translated_text` empty, `status` untranslated), save hook never called; string-shape (the cell-22 loop's exact dict) refused with the visible guard print; save shield `_B2_UNSET` + monkeypatch counter per the RF-2/RF-3 battery discipline. Battery: 24 → 25. [TEST RESULT]
- **Verification (`scripts/m005_b2_rf4_preflight.py` + `m005_b2_rf4_test25.py` + `m005_b2_rf4_build.py` + `m005_b2_rf4_verify.py` — 51 checks ALL GREEN):** V1 static — AST no-warnings; marker check / counter / print / apply guard present exactly once each; RF-2/RF-3 invariants carried (sentinels: 6 df-saves, 2 save-fn saves, 8 `is _B2_UNSET` checks, `_B2_UNSET = object()` 1 def, `__unset__` still absent; `trailing_arrow` counter intact); functional spans `export_ai_text` + `translate_page` + the Owner 10-section prompt span **byte-identical to c5f51c4**; **re-derivation equality: old cell 8 + EXACTLY the 6 manifest patches == new cell 8**; difflib non-equal opcodes bounded. V2 scope — 26 non-target cells byte-identical to c5f51c4; cell-8 non-source fields + top-level fields identical; **cells 22 + 25 byte-identical** (paste flow + payload builders). V3 runtime sandbox — 25/25 self-tests, zero failures, `translation_df` popped post-exec; PM line → no entry + `marker_skipped=1` + "(marker)" reason + visible print; `[SKIP:OCR_FAILED]` / `[SFX]` (pure `is_special_marker` arm) / `[skip]` (case-insensitive arm) all marker-skipped; trailing-arrow fixture 6/6 with counter + print (RF-3 intact); empty post-arrow still a placeholder skip (Tests 4/21 contract); export-side marker + empty arrow still a placeholder skip; apply dict-shape `applied=0`, df untouched, no save; apply string-shape `applied=0` + guard print; quoted `"[SKIP]"` unwrapped then refused; **real Bengali still applies (no over-blocking)**. V4 runtime live-state — pre-seeded real df + canary save hook: 25/25 green, post-exec df IS the pre-seeded object pickle-byte-identical, canary NEVER called (Test 25 traceless in a warm kernel). V5 negative control — PRE-FIX bytes (c5f51c4): parse keeps the `[SKIP]` entry; apply stores the literal (dict and string shapes, `applied=1`, `status="non_bengali"`) — the defect reproduced and RF-4 proven as the fix. V6 — m002_sim_v2: **0 abort sites**; only cell 8 differs from the RF-3 extraction. V7 export smoke — txt format (header + arrow + `[SKIP:OCR_FAILED] →` marker line shape) + JSON sidecar schema (page/page_id/id/region_type/original_text/translated_text) unchanged. [TEST RESULT]
- **Invariants held:** cell 8 ONLY (+175 source lines, 2658→2833); every other cell byte-identical to c5f51c4; wire format + apply semantics + export path untouched (`export_ai_text`/`translate_page`/prompt spans byte-identical); V-4a never-silent — marker skips are counted AND printed AND carried in the sentinel's skip report; RF-3's `[SKIP:OCR_FAILED] →` export-side round-trip channel unchanged; one logical change, one commit. [FACT]
- **Interpretation disclosures (for Flash delta check):** (1) The PM's counter name "marker-skip" is normalized to the stats key `marker_skipped` (codebase snake_case convention, sibling of `placeholder_skipped`/`trailing_arrow`; nothing reads the hyphenated form). (2) The parse-level check covers the **arrow branch only** — an arrowless `[SKIP]` line already lands in the visible unparsed report via the English-only rule (`validate_bengali("[SKIP]")` is False); a trailing-arrow line ending in a marker is rescued by the RF-3 fallback only for Bengali, else stays a reported placeholder skip. (3) **Quoted markers are NOT caught at parse level** (the quotes survive the FIRST-arrow split; the parse check sees `'"[SKIP]"'`) — they are caught by the apply-level guard after `clean_translation` unwraps them: a deliberate division of labor (parse owns the counter/report, apply owns post-clean final defense), so the counter may undercount quoted variants while the guard still prevents storage. (4) The apply guard is print-only (no counter — the parse level owns the counter); cache-rebuild nuance: a page whose translation records are ALL markers now rebuilds to 0 applied rows (idempotent, no data loss — the df was empty by the rebuild precondition) instead of "applying" the marker literals once. (5) `is_special_marker` itself was NOT modified — bare `[SKIP]` is still not a set member (the PM's 2-set arm handles it); adding it to the shared set would change `get_translation_status` semantics for AUTO-path translations (e.g. `translate_text`'s marker pass-through at c8:836), which is outside this directive.
- **Status:** follow-up commit on `mangabd-005-b2` (no amend of `c5f51c4`, no merge — the prescribed RF path); branch pushed for **Flash delta verification** (delta = the 6 cell-8 patches + this GLM_5_3.md record only, on top of RF-3 @ c5f51c4). B2 merge gate unchanged: Flash Phase D + RF-3 delta check + RF-4 delta check + Owner live retest + Owner merge authorization. [FACT]
- **Re-runnable instruments:** `scripts/m005_b2_rf4_preflight.py` (verify-first gate / negative control), `scripts/m005_b2_rf4_test25.py` (Test 25 source module), `scripts/m005_b2_rf4_build.py` (6 anchored patches + manifest), `scripts/m005_b2_rf4_verify.py` (51 checks), `scripts/m005_b2_rf4_patches.json` (manifest), `scripts/m005_sim2.py`, `cells_m005_b2_rf4/` (post-RF-4 extraction). [FACT]

---

# MANGABD-005 — BATCH 2 MERGE COMPLETION RECORD (GLM-5.3, 2026-10-18)

## PC-M2 Batch 2 (B2) merged to main; branch deleted; MANGABD-005 FULLY CLOSED (2026-10-18)

- **Merge executed per the Owner's numbered final-merge directive** (relayed via PM Qwen3.8-Max, 2026-10-18) on the Owner's live verdict **OWNER LIVE ACCEPT — ZERO DEFECTS** ("The workflow is officially bulletproof") after extensive live end-to-end Colab testing of the B2 lenient paste-back parser, the trailing-arrow fallback (RF-3), and the new 10-section system prompt. Directive: squash-merge all branch commits (Phase C, Flash Phase D, RF-2, RF-3, RF-4) into `main`; delete the branch local+remote; record the merge in DECISION.md with the gate chain; reconcile this file's CURRENT PHASE so MANGABD-005 is fully CLOSED (both B1 and B2); report the merge hash. [FACT]

- **Pre-merge state verified this session:** `git fetch` → remote advanced `fe879fe` → **`08ad231`** (Flash "MANGABD-005 B2 RF-3 (+RF-4) delta verification — CLOSED", docs-only `GLM_5_3_FLASH.md` +56 — the final gate-chain link) → local ff-synced; `main` @ `9baf062` = origin (B1 squash `4d9b787` + B1 docs sync); tree clean. Gate chain fully discharged: Phase D APPROVED (`11bbd1f`) + RF-2 delta CLOSED (`29c17ba`) + RF-3/RF-4 delta CLOSED (`08ad231`) + Owner live retest (the Owner's own Colab session, per this directive) + Owner merge authorization (this directive). [FACT]

- **Squash-merge:** `git merge --squash origin/mangabd-005-b2` on main — the notebook auto-merged cleanly (disjoint cell sets: B1 {9} on main vs B2 {8,22,25} on branch, exactly as Flash Phase D E6 proved via per-cell 3-way merge + merge-tree); the sole conflicts were the two docs files — precisely the overlaps disclosed since Phase C ("the two header edits will need reconciliation at merge time") and cross-noted at the B1 merge: `GLM_5_3.md` CURRENT PHASE header + task-records tail, `GLM_5_3_FLASH.md` review-records tail. Resolution = union of authoritative records: CURRENT PHASE kept the branch's B2 entry (chain completed to the merge) + main's B1 CLOSED entry + main's updated M004 cross-ref, dropping each side's stale cross-reference entry (main's B2-WIP @ `122e353` view; branch's B1-not-yet-merged view); the task records and the FLASH records kept both sides' full sections in chronological order (B1 records first, then B2 records). [FACT]

- **Merged-state verification (`scripts/m005_b2_merge_resolve.py`, 51 checks ALL GREEN; 2 test-side defects found+fixed mid-run — a wrong-direction V2.1 assertion and a test-name transcription typo — zero repo impact, zero implementation-side findings):** the merged notebook was proven **byte-equal to the deterministic reconstruction** (main's JSON object + the branch's cells 8/22/25 sources) — B1 + B2 coexist with zero merge artifacts; per-cell 3-way byte mapping (cells {8,22,25} == branch tip `08ad231`, cell {9} == main `9baf062`, the 23 others == base `8445328` across all refs); non-source cell fields + top-level fields identical to base; AST 27/27 warnings-as-errors; the cell-8 self-test battery **25/25** green, exec'd from the merged file itself; `m002_sim_v2` **0 abort sites**; the S007 acceptance zip preserved (1,903,763 bytes, untouched). [TEST RESULT]

- **Squash commit:** **`7ec691b`** (full hash `7ec691b367ecc00e521932eec6f57f61d8644ca6`), pushed `9baf062..7ec691b`; contents 3 files +1574/−121 — notebook **+1295/−120** (changed cells exactly {8,22,25}; md5 `fdb6f4b85b4ec9fe70e32743ab323ab0`), `GLM_5_3.md` +93/−1, `GLM_5_3_FLASH.md` +186/−0. Pre-commit audit (`scripts/m005_b2_merge_precommit.py`): exactly 3 staged files, no mode changes, no unmerged paths, secret scan **0 hits on 1,574 added lines** (10 strict patterns). Branch `mangabd-005-b2` deleted (local + remote) immediately after the push (local pointer `08ad231` = the merged remote tip; the seven branch commits `122e353`/`11bbd1f`/`2c4635d`/`29c17ba`/`c5f51c4`/`fe879fe`/`08ad231` remain citable provenance, their net content preserved exactly once, in `7ec691b`). [FACT]

- **Docs sync (this commit, sequenced after the squash per the PM directive, M004 §D.1/§C7 + M005-B1 §E.1/PC-M1 precedent):** `agents/DECISION.md` — STATUS header rewritten (MANGABD-005 TASK CLOSED, both batches merged), new **§E.2 Batch 2 Merge Record** (authorization chain / merge / merged-state verification / tracked follow-ups / disposition), "source modified exactly five times" corrected to **six times** (+ the B2 entry), the B1 STATUS entry's trailing B2-in-progress clause updated to closed. This file — CURRENT PHASE B2 entry's merge references backfilled with the hash `7ec691b` + this PC-M2 record. Zero notebook/source changes in the docs commit. [FACT]

- **Tracked follow-ups (carried forward; none blocking):** the three B1 follow-ups remain open as logged in DECISION.md §E.1 (cell-1:295 lama_size cleanup, r1 kana tofu N-D, acceptance-zip metadata.json export); two non-blocking B2 observations from Flash `08ad231` recorded in DECISION.md §E.2 (double-arrow cosmetic; cell-22 combined summary-line consolidation available at any future cell-22-authorized batch). [FACT]

- **MANGABD-005 disposition: TASK CLOSED (B1 + B2).** B1 (B3 LaMa full resolution) delivered, verified, accepted, and merged as `4d9b787`; B2 (lenient paste-back parser + trailing-arrow fallback + the Owner's professional system prompt + bare [SKIP] marker-skip) delivered, verified, live-accepted, and merged as `7ec691b`. No batches remain open or authorized. MANGABD-003 Batch 3 remains SUPERSEDED (A7-D1; branches preserved untouched as historical byte source). Next task awaits the Owner's directive. [FACT]

- **Re-runnable instruments:** `scripts/m005_b2_merge_resolve.py` (conflict resolution + 51-check merged-state verification), `scripts/m005_b2_merge_precommit.py` (staged audit), `scripts/m005_sim2.py`, `cells_m005_b2_merge/` (merged-main extraction) — plus all Phase C / RF-2 / RF-3 / RF-4 instruments on record in the sections above. [FACT]
