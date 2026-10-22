#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-8 — pre-commit audit.

Gates (all must pass before commit):
  1. scope: changed files exactly {notebook, agents/GLM_5_3.md} +
     the 6 NEW RF-8 instrument files under scripts/; all scripts NEW
     (mode 100644 adds); no renames/deletions; notebook + doc are
     modifications only.
  2. secret scan on the ADDED lines of every changed file — 0 hits
     (the already-committed scanners keep their disclosed regex
     literals + fake "sk-test" values; nothing new in that class).
  3. staged-tree AST 27/27.
  4. staged 24-non-target-cell identity vs 0b5d11d re-asserted on the
     staged bytes.
  5. battery counts: cell 7 = 10 tests (Tests 26-29 present once
     each); cell 8 byte-identical to 0b5d11d.
  6. cell-0 onnxruntime pin present in the staged bytes.
"""
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "0b5d11d"

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
        "rf8_build.py", "rf8_content.py", "rf8_docs.py",
        "rf8_patches.json", "rf8_precommit.py", "rf8_verify.py",
    )
)
EXPECTED_MOD = sorted([NB_NAME, "agents/GLM_5_3.md"])

check("1.1 untracked list empty (everything staged or ignored)",
      untracked == [], str(untracked))
check("1.2 modified set exactly {notebook, GLM_5_3.md}",
      sorted(c for c in changed if not c.startswith("scripts/")) == EXPECTED_MOD,
      str([c for c in changed if not c.startswith("scripts/")]))
check("1.3 new scripts set exactly the 6 RF-8 instruments",
      sorted(c for c in changed if c.startswith("scripts/")) == EXPECTED_NEW,
      str([c for c in changed if c.startswith("scripts/")]))

ok_mode = True
for c in changed:
    diff = git("diff", "--cached", "--raw", "--", c).stdout.splitlines()
    if not diff:
        diff = git("diff", "--raw", "--", c).stdout.splitlines()
    for ln in diff:
        head = ln.split("\t")[0]
        old_mode, new_mode = head.lstrip(":").split(" ")[:2]
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
# KNOWN + DISCLOSED caveat (unchanged class from RF-7): the committed
# scanners carry secret-DETECTION regex literals and short fake values
# ("sk-test") — none of them match the {20,}-anchored patterns below.
hits = []
for c in changed:
    diff = git("diff", "--cached", "--", c).stdout
    if not diff:
        diff = git("diff", "--", c).stdout
    added = [ln[1:] for ln in diff.splitlines() if ln.startswith("+") and not ln.startswith("+++")]
    for ln in added:
        for pat in PATTERNS:
            if re.search(pat, ln):
                hits.append((c, pat, ln[:120]))
check("2.1 secret scan 0 hits on all added lines",
      hits == [], str(hits[:4]))

# ── 3. staged AST ────────────────────────────────────────────
staged_nb = git("show", ":0:" + NB_NAME).stdout
if not staged_nb:
    staged_nb = git("show", f":{NB_NAME}").stdout
nb = json.loads(staged_nb)
cells = ["".join(c.get("source", [])) for c in nb["cells"]]
assert len(cells) == 27, f"staged cell count {len(cells)}"
ok_ast = True
for i, src in enumerate(cells):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(src, f"staged_cell_{i:02d}.py", "exec")
        except Warning as w:
            ok_ast = False
            print(f"      cell {i} warning: {w}")
check("3.1 staged AST 27/27 (warnings-as-errors)", ok_ast)

# ── 4. staged 24-non-target identity vs 0b5d11d ──────────────
base_raw = git("show", f"{BASE_REF}:{NB_NAME}").stdout
base_nb = json.loads(base_raw)
base_cells = ["".join(c.get("source", [])) for c in base_nb["cells"]]
RF8_TARGET = {0, 5, 7}
diff_cells = [i for i in range(27) if base_cells[i] != cells[i]]
check("4.1 staged changed cells exactly {0, 5, 7}", diff_cells == [0, 5, 7],
      str(diff_cells))
check("4.2 staged 24 non-target cells byte-identical to 0b5d11d",
      all(base_cells[i] == cells[i] for i in range(27) if i not in RF8_TARGET))

# ── 5. battery counts ────────────────────────────────────────
c7 = cells[7]
check("5.1 cell 7: Tests 26-29 present once each",
      c7.count("Test 26:") == 1 and c7.count("Test 27:") == 1
      and c7.count("Test 28:") == 1 and c7.count("Test 29:") == 1)
check("5.2 cell 8 byte-identical to 0b5d11d (battery 25/25 untouched)",
      cells[8] == base_cells[8])

# ── 6. cell-0 onnxruntime pin in staged bytes ────────────────
c0 = cells[0]
check("6.1 cell-0 staged: onnxruntime>=1.31.0 in DETECTION_PACKAGES",
      c0.count('"onnxruntime>=1.31.0"') == 1
      and c0.index('"onnxruntime>=1.31.0"') > c0.index("DETECTION_PACKAGES = [")
      and c0.index('"onnxruntime>=1.31.0"') < c0.index("TRANSLATION_API_PACKAGES"))

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
if FAIL:
    raise SystemExit("RF-8 PRECOMMIT FAILED")
print("PRECOMMIT ALL GREEN")
