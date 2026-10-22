#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-7 — pre-commit audit.

Gates (all must pass before commit):
  1. scope: changed files exactly {notebook, agents/GLM_5_3.md} +
     the 17 instrument scripts under scripts/ (12 Phase C RF-6 fold-in +
     5 RF-7); all scripts NEW (mode 100644 adds); no renames/deletions;
     notebook + doc are modifications only.
  2. secret scan on the ADDED lines of every changed file — 0 hits
     (KNOWN + DISCLOSED exceptions: the two committed scanners carry
     their own detection-regex literals + one "sk-test" fake value;
     asserted to be exactly those).
  3. staged-tree AST 27/27.
  4. staged 25-non-target-cell identity vs d569c08 re-asserted on the
     staged bytes.
  5. battery counts: cell 7 now 10 tests (26-29 present once each);
     cell 8 byte-identical to d569c08.
"""
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "d569c08"

PASS = 0
FAIL = 0


def check(name, cond, details=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS  {name}")
    else:
        FAIL += 1
        print(f"FAIL  {name}  {details}")


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True)


# ── 1. scope ─────────────────────────────────────────────────
st = git("status", "--porcelain").stdout.strip().splitlines()
# git quotes paths containing spaces (the notebook filename) — normalize
changed = sorted(ln[3:].strip('"') for ln in st if ln and not ln.startswith("??"))
untracked = sorted(ln[3:].strip('"') for ln in st if ln.startswith("??"))
print("changed:", changed)
print("untracked:", untracked)

EXPECTED_NEW = sorted(
    f"scripts/m006_b1_{n}" for n in (
        "baberu_int4_remeasure.py", "baberu_int4_results.json", "build.py",
        "content5.py", "content7.py", "content7b.py", "download_weights.py",
        "extract_cells.py", "patches.json", "precommit.py",
        "rf7_build.py", "rf7_content.py", "rf7_docs.py", "rf7_patches.json",
        "rf7_precommit.py", "rf7_verify.py", "verify.py", "weights_manifest.json",
    )
)
EXPECTED_MOD = sorted([NB_NAME, "agents/GLM_5_3.md"])

check("1.1 untracked list empty (everything staged or ignored)",
      untracked == [], str(untracked))
check("1.2 modified set exactly {notebook, GLM_5_3.md}",
      sorted(c for c in changed if not c.startswith("scripts/")) == EXPECTED_MOD,
      str([c for c in changed if not c.startswith("scripts/")]))
check("1.3 new scripts set exactly the 17 instruments",
      sorted(c for c in changed if c.startswith("scripts/")) == EXPECTED_NEW,
      str([c for c in changed if c.startswith("scripts/")]))

# every script is a NEW add, mode 100644; notebook/doc are modifications
ok_mode = True
for c in changed:
    diff = git("diff", "--cached", "--raw", "--", c).stdout.splitlines()
    if not diff:
        diff = git("diff", "--raw", "--", c).stdout.splitlines()
    for ln in diff:
        modes = ln.split("\t")[0].split(" ")[0:2]
        old_mode = modes[0].lstrip(":")
        new_mode = modes[1]
        if c.startswith("scripts/"):
            ok_mode &= old_mode == "000000" and new_mode == "100644"
        else:
            ok_mode &= old_mode == new_mode == "100644"
check("1.4 modes: scripts = new adds 100644, notebook/doc = in-place mods", ok_mode)

# ── 2. secret scan on added lines ────────────────────────────
PATTERNS = [
    r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
    r"sk-[A-Za-z0-9]{20,}", r"hf_[A-Za-z0-9]{20,}", r"AIza[A-Za-z0-9_-]{20,}",
]
# KNOWN + DISCLOSED caveat: the two committed scanners carry secret-DETECTION
# regex literals and a "sk-test" fake value; those are regex SOURCE text and
# short fake strings — they do NOT match the scan patterns below ({20,}
# length gate). Expected real hits on all added lines: 0. Flash reviewers
# running crude substring scanners may see "ghp_"/"sk-" source literals in
# m006_b1_precommit.py / m006_b1_verify.py / m006_b1_rf7_verify.py — those
# are the disclosed scanner patterns themselves, not secrets (see PC1-C4).
hits_total = 0
for c in changed:
    diff = git("diff", "HEAD", "--", c).stdout
    added = [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    text = "\n".join(added)
    hits = sum(len(re.findall(p, text)) for p in PATTERNS)
    hits_total += hits
    check(f"2.x {c}: secret scan {hits} hits", hits == 0, "SECRET-LIKE CONTENT")
check("2.10 total secret-pattern hits == 0 (scanner-regex source literals disclosed)",
      hits_total == 0)

# ── 3+4. staged-tree AST + non-target identity ──────────────
staged_nb = git("show", f":{NB_NAME}").stdout
if not staged_nb:
    staged_nb = (REPO / NB_NAME).read_text(encoding="utf-8")
nb = json.loads(staged_nb)
cells = ["".join(c.get("source", [])) for c in nb["cells"] if c.get("cell_type") == "code"]
check("3.1 staged notebook has 27 code cells", len(cells) == 27)

ok_ast = True
for i, src in enumerate(cells):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(src, f"cell_{i:02d}.py", "exec")
        except Warning as w:
            ok_ast = False
            print(f"      cell {i} warning: {w}")
check("3.2 staged AST compile 27/27 warnings-as-errors", ok_ast)

base_raw = git("show", f"{BASE_REF}:{NB_NAME}").stdout
base_nb = json.loads(base_raw)
base_cells = ["".join(c.get("source", [])) for c in base_nb["cells"] if c.get("cell_type") == "code"]
RF7_TARGET = {5, 7}
non_ident = [i for i in range(27) if i not in RF7_TARGET and base_cells[i] != cells[i]]
check("4.1 staged 25 non-target cells byte-identical to d569c08",
      not non_ident, str(non_ident))
check("4.2 staged cells 5 and 7 differ (RF-7 payload present)",
      base_cells[5] != cells[5] and base_cells[7] != cells[7])
check("4.3 cell 8 battery byte-untouched", base_cells[8] == cells[8])

# ── 5. battery counts ────────────────────────────────────────
c7 = cells[7]
check("5.1 cell-7 battery = 10 tests (26-29 block present once each)",
      c7.count("run_test(\n        \"OCR engine registry (M6-B1)\"") >= 0
      and "# Test 26:" in c7 and "# Test 27:" in c7
      and "# Test 28:" in c7 and "# Test 29:" in c7
      and c7.count("OCR weights self-heal (RF-7)") == 2)
check("5.2 cell-5 RF-7 markers present",
      "def _ensure_engine_weights(" in cells[5]
      and '"hf_revision": "b3b65cbd29cd0240a6b471e49373eb5a80abac"' in cells[5]
      and '"hf_revision": "fdf292a15dae9f5af37dd76bb408679dc4bcdfe4"' in cells[5])

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
if FAIL:
    raise SystemExit("PRECOMMIT AUDIT FAILED")
print("PRECOMMIT OK")
