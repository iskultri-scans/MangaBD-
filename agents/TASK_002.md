# MangaBD — Task 002

## TASK ID

MANGABD-002

## STATUS

OPEN

## TASK TYPE

Execution Reliability / Notebook Stabilization

---

# OBJECTIVE

Make the current MangaBD Colab notebook reliably executable from a completely fresh runtime.

The target behavior is:

Fresh Colab runtime
→ Open notebook
→ Run All
→ Pipeline executes in the intended order
→ No execution-order-dependent NameError or undefined-state failure
→ Existing MangaBD functionality remains intact

---

# IMPORTANT

Do NOT assume that the issue identified during MANGABD-001 has only one cause.

Investigate the actual current notebook.

The exact root cause must be determined from repository evidence.

Do not blindly implement a previously suggested fix.

---

# PHASE 1 — INVESTIGATION

GLM-5.3 and GLM-5.3-Flash must first investigate independently.

Determine:

1. The intended execution order.
2. The actual execution order.
3. All relevant function/class/variable definitions.
4. Any redefinitions or overrides.
5. Variables that depend on earlier notebook state.
6. Variables/functions that may be undefined in a fresh runtime.
7. Whether execution history changes behavior.
8. Whether Run All can trigger a different implementation from manual reruns.
9. Whether there are hidden state dependencies.
10. Whether fixing one issue could create a regression elsewhere.

---

# SUCCESS CONDITION

A successful solution should make the notebook's execution behavior deterministic and understandable.

The solution should NOT simply hide errors.

Do not use:

- unnecessary try/except
- silent fallbacks
- dummy variables
- global hacks
- execution-order workarounds that hide the real problem

unless there is strong technical justification.

---

# PRESERVATION REQUIREMENTS

Preserve existing working functionality.

Do not unnecessarily change:

- OCR behavior
- translation behavior
- inpainting behavior
- Bengali rendering
- model selection
- output format
- quality logic

unless the investigation proves that a change is required.

---

# REQUIRED PROCESS

## Phase A — Independent Investigation

GLM-5.3:

- Investigate the root cause.
- Document evidence.
- Propose one or more solutions.
- Do NOT modify source code yet.

GLM-5.3-Flash:

- Independently investigate the same problem.
- Review GLM-5.3's proposal after completing its own analysis.
- Challenge unsupported assumptions.
- Check regression risks.
- Do NOT modify source code yet.

---

## Phase B — Decision

After both investigations:

- Compare findings.
- Resolve disagreements using repository evidence.
- Record the recommended solution in DECISION.md.
- Do NOT implement until the Project Owner approves.

---

## Phase C — Implementation

Only after explicit Project Owner approval:

GLM-5.3 may implement the approved solution.

The implementation must be minimal and targeted.

---

## Phase D — Verification

GLM-5.3-Flash must independently review the implementation.

Verify:

1. Fresh-runtime behavior.
2. Execution order.
3. No new undefined-state errors.
4. Existing functionality is preserved.
5. No unnecessary code changes.
6. No hidden regressions.

Where actual Colab execution is possible, perform the strongest practical test.

If full runtime execution is impossible, clearly document the limitation.

---

# EVIDENCE RULE

Use:

FACT
HYPOTHESIS
ASSUMPTION
TEST RESULT
UNKNOWN

Do not present assumptions as facts.

---

# FILES ALLOWED TO CHANGE

During investigation:

Only:

- agents/GLM_5_3.md
- agents/GLM_5_3_FLASH.md
- agents/DECISION.md

During implementation:

Only files necessary for the approved fix.

---

# USER APPROVAL

NOT YET REQUESTED

---

# FINAL SUCCESS CRITERIA

The task is VERIFIED only when:

- Root cause is understood.
- Proposed fix is reviewed by both agents.
- Project Owner approves the change.
- GLM-5.3 implements it.
- GLM-5.3-Flash independently verifies it.
- No significant regression is discovered.
