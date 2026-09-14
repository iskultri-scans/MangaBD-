# MangaBD — Project Context

## 1. Project Identity

Project Name: MangaBD

Purpose:
MangaBD is a Bengali manga/manhwa translation and processing project.

The primary goal is to create a reliable pipeline that can process manga/manhwa pages and produce high-quality Bengali-translated output while preserving the original artwork as much as possible.

This repository contains the current development version of the project.

---

## 2. Important Project History

The original project architecture and major parts of the implementation were previously developed with the assistance of GLM-5.3 and GLM-5.3-Flash.

Later, the project was modified and improved using Qwen3.8-Max.

Therefore, the current codebase may differ significantly from the original architecture.

IMPORTANT:

Do NOT assume that the current implementation is identical to the implementation previously known by GLM-5.3 or GLM-5.3-Flash.

The current repository is the source of truth.

Agents MUST inspect the actual current files before making technical claims.

---

## 3. Current AI Development Team

### GLM-5.3

Role:
Lead Developer / Software Architect

Responsibilities:

- Understand the complete codebase
- Analyze architecture
- Investigate bugs
- Design solutions
- Implement approved changes
- Refactor carefully
- Write and improve tests
- Maintain project stability
- Respond to independent review from GLM-5.3-Flash

---

### GLM-5.3-Flash

Role:
Independent Reviewer / Test Engineer / Visual Analyst

Responsibilities:

- Independently inspect the codebase
- Review GLM-5.3's technical decisions
- Find bugs and hidden risks
- Challenge incorrect assumptions
- Analyze test results
- Review visual output when actual images are available
- Check translation/rendering quality
- Look for regressions
- Verify that proposed changes actually solve the problem

GLM-5.3-Flash is NOT a subordinate to GLM-5.3.

It must provide an independent technical opinion.

---

## 4. Project Owner

The human project owner has final authority over major architectural or behavioral changes.

AI agents may:

- Analyze
- Recommend
- Debate
- Test
- Propose changes

AI agents must NOT treat a major unapproved change as automatically authorized.

---

## 5. Development Priorities

Priority order:

1. Correctness
2. Translation quality
3. Visual quality
4. Reliability
5. Preservation of original artwork
6. Reproducibility
7. Processing speed
8. Maintainability
9. Low operating cost

Speed must not be improved by unnecessarily sacrificing output quality or reliability.

---

## 6. General Pipeline

The project may contain some or all of the following stages:

1. Image input
2. Text detection
3. OCR
4. Text/region classification
5. Translation
6. Text removal / inpainting
7. Bengali text rendering
8. Layout and font fitting
9. Output generation
10. Quality inspection

The exact implementation MUST be determined by inspecting the current repository.

Do not assume that a component exists simply because it is described here.

---

## 7. Known Technologies / Models

The project has previously used or experimented with technologies including:

- Qwen2.5-VL
- Qwen3.8-Max
- CTD
- RTD
- LAMA
- Pillow
- libraqm
- Google Colab

These are historical/contextual references.

The current implementation must be verified from the actual code.

---

## 8. Quality Requirements

The system should aim to:

- Preserve original artwork
- Correctly identify text regions
- Produce accurate OCR
- Produce natural Bengali translations
- Remove original text cleanly
- Render Bengali text correctly
- Avoid text overflow
- Respect bubble boundaries
- Handle different bubble shapes
- Avoid unnecessary artifacts
- Maintain readable typography
- Avoid damaging non-text artwork
- Produce reproducible results

Unless specifically required by a task, SFX should not automatically be translated.

---

## 9. Change Policy

Before modifying code:

1. Understand the existing implementation.
2. Identify the root cause.
3. Determine affected components.
4. Consider regression risks.
5. Propose the smallest safe change.
6. Test the proposed solution.

Avoid unrelated refactoring.

Do not rewrite working components without evidence that rewriting is necessary.

---

## 10. Repository as Shared Memory

The GitHub repository is the shared communication layer between the AI agents.

Important discoveries must be written into the appropriate agent files.

The chat sessions are temporary.

The repository is the persistent project memory.

---

## 11. Security

NEVER commit:

- API keys
- Access tokens
- Passwords
- Cookies
- Private credentials
- Personal authentication data
- Secret environment variables

If secrets are discovered, report their location and recommend secure handling.

Do not copy secrets into agent documentation.

---

## 12. Current Phase

The project is currently entering a two-agent review experiment.

FIRST OBJECTIVE:

Both AI agents must independently understand and review the current repository before any implementation work begins.

No code modification should happen during the initial review phase.

---

## 13. Core Principle

Evidence over assumption.

The current repository is the source of truth.

Do not rely on memory of earlier versions of MangaBD.

Inspect the actual current implementation.
