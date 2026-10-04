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
