# MangaBD — Visual Evidence Archive

This directory permanently closes the **NO_VISUAL_EVIDENCE_AVAILABLE** gap
recorded in `agents/DECISION.md` (audit finding 18: "Zero image outputs in the
notebook and zero image files in the repo — NO_VISUAL_EVIDENCE_AVAILABLE;
output quality is unassessable by anyone until sample artifacts are committed").

## Purpose

Each subdirectory of `samples/` is an immutable archive of the complete visual
output of one real pipeline run — the original input, the detection mask, the
inpainted intermediate, the final rendered image, and the JSON sidecars that
document what the pipeline did at each stage. Until now, every claim about
MangaBD's output quality was unverifiable, because no image ever left the
Colab session where it was produced. The artifacts archived here are that
missing evidence chain, and they allow any reviewer — the Project Owner,
GLM-5.3, or GLM-5.3-Flash — to assess real output quality directly.

## Contents

| Sample | Description |
|--------|-------------|
| `S001_color_webtoon/` | First fresh "Run All" success on a color webtoon long strip (the second test image), produced with the MANGABD-002-verified notebook. See its `metadata.json` for provenance. |
| `S002_batch1/` | MANGABD-003 Batch 1 acceptance run — the same source page as S001 (`02.jpg`, 844×1200) re-run for controlled A/B, produced with the Batch-1 notebook (branch `mangabd-003-batch1`, head `a007581`: V-1 CJK fallback metrics + V-2 vertical mask band + V-4a; squash-merged to `main` in `f158091`). Fresh Run All + Control Studio UI, plain path (quality wrap not invoked), engine `nllb`. See its `metadata.json` for provenance. |
| `S003_batch2/` | MANGABD-003 Batch 2 (V-3) acceptance run — the same source page as S001/S002 (`02.jpg`, 844×1200, processed as `02_2.jpg`) re-run for controlled A/B, produced with the Batch-2 notebook (branch `mangabd-003-batch2`, head `671e5d3`: V-3 vertical-note OCR, cells 7 & 16; Flash Phase D approved `74f5d8c`; Flash S003 acceptance verdict BATCH2 ACCEPT `352c16b`; squash-merged to `main` 2026-10-11). Fresh Run All + Control Studio UI, engine `nllb`; region 1 carries the `vertical_ocr` audit trail. See its `metadata.json` for provenance. |
| `S005_manual/` | MANGABD-004 (B1+B2) S005 acceptance run, manual copy-paste path — page `02_1.jpg` (844×1200), fresh Run All + Control Studio UI on branch `mangabd-004-b1-b2` head `7f0e653` (Flash Phase D APPROVED_WITH_FIXES `f460143`, RF-1 CLOSED at `3c57583`). The manual workflow output is `final.jpg` (rendered 19:26:20 from the B2 external-AI paste-back); its `translation.json` sidecar was overwritten by the later OpenRouter run in the same session, so the manual translations survive only in `final.jpg` pixels — see `metadata.json` sidecar_note for the full evidence chain. |
| `S005_openrouter/` | MANGABD-004 (B1+B2) S005 acceptance run, OpenRouter auto-translation path — same session front-end (detection/OCR/inpaint shared with S005_manual), engine `openrouter`, model `nvidia/nemotron-3-ultra-550b-a55b:free` per the machine-written sidecar (registry value synced from the Control Studio STEP 3 model box; the PM relay specified `apodex/apodex-1.1-mini:free` — see `metadata.json` model_note). Register/profanity preservation vs the NLLB baseline (S001/S002) is the quality read. |

(S001's folder name is a rev1 pipeline-variant label retained by Owner decision; its content is a B/W manga page produced by NLLB — see its `metadata.json` naming_note and `metadata.rev1.json` for the original wording.)

## Chain of custody

1. The Project Owner produced the sample during a fresh Colab run and uploaded
   it to the repository root as a ZIP (commit `59be2ff`, "Add files via
   upload", 2026-09-29).
2. GLM-5.3 extracted and verified the archive into `samples/<sample_id>/`,
   added this README and per-sample `metadata.json`, and removed the ZIP from
   the repo root.

## Rules

- Artifacts in this directory are **evidence, not working files**. Never edit,
  re-generate, rename, or overwrite them; corrections belong in a new sample
  directory with a new sample ID.
- New samples follow the same pattern: Owner uploads the ZIP, an agent
  extracts it to `samples/<sample_id>/`, writes a `metadata.json` recording
  provenance (date, notebook commit, pipeline variant, source type), and
  removes the ZIP from the root.
- Visual quality assessment of archived samples is performed by GLM-5.3-Flash
  as an independent review; verdicts are recorded in `agents/DECISION.md`.
