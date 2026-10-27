#!/usr/bin/env python3
r"""MANGABD-009 B2 Phase C — pre-commit audit (RF-9 discipline).

Final invariants at commit time, all against the WORKING TREE:
  P1  branch mangabd-009-b2; notebook blob == base 5fe8804 + build output
  P2  scope drift exactly {6, 10} vs 5fe8804; RB2-7 named cells
      7/11/12/24 + reading-order 13/15/23 byte-identical
  P3  AST 27/27 warnings-as-errors; manifest re-derivation equality
  P4  expected inventory: notebook + 7 Phase C scripts + agents/GLM_5_3.md
  P5  the committed-notebook sha256 == the build's reported sha
  P6  verify instrument present; its recorded total == 45/45 ALL GREEN
"""
import hashlib
import json
import subprocess
import sys
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE = "5fe8804"
EXPECTED_SHA = "082257483b81f5939dab6d3249a48f17dc02e29169d3a2b66f43ccd48115863f"
EXPECTED_FILES = {
    "MangaBD_V12_ipynb_txt.ipynb (3).txt",
    "agents/GLM_5_3.md",
    "scripts/m009_b2_phaseC_build.py",
    "scripts/m009_b2_phaseC_content06.py",
    "scripts/m009_b2_phaseC_content10.py",
    "scripts/m009_b2_phaseC_content10b.py",
    "scripts/m009_b2_phaseC_patches.json",
    "scripts/m009_b2_phaseC_verify.py",
    "scripts/m009_b2_phaseC_precommit.py",
}

fails = []


def ck(name, ok, detail=""):
    print(("PASS  " if ok else "FAIL  ") + name
          + (f"  [{detail}]" if not ok else ""))
    if not ok:
        fails.append(name)


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout


ck("P1a branch mangabd-009-b2",
   git("branch", "--show-current").strip() == "mangabd-009-b2")

raw = NB.read_bytes()
sha = hashlib.sha256(raw).hexdigest()
ck("P1b working notebook sha256 == build output", sha == EXPECTED_SHA, sha)

nb = json.loads(raw.decode("utf-8"))
cells_post = ["".join(c.get("source", [])) for c in nb["cells"]
              if c.get("cell_type") == "code"]
nb_pre = json.loads(git("show", f"{BASE}:{NB_NAME}"))
cells_pre = ["".join(c.get("source", [])) for c in nb_pre["cells"]
             if c.get("cell_type") == "code"]

scope = [i for i in range(27) if cells_post[i] != cells_pre[i]]
ck("P2a scope drift exactly {6, 10}", sorted(scope) == [6, 10],
   str(sorted(scope)))
ck("P2b RB2-7 named cells 7/11/12/24 byte-identical",
   all(cells_post[i] == cells_pre[i] for i in (7, 11, 12, 24)))
ck("P2c reading-order cells 13/15/23 byte-identical",
   all(cells_post[i] == cells_pre[i] for i in (13, 15, 23)))

ast_ok = True
for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(cells_post[i], f"cell_{i:02d}.py", "exec")
        except Warning:
            ast_ok = False
ck("P3a AST 27/27 warnings-as-errors", ast_ok)

manifest = json.loads((REPO / "scripts" / "m009_b2_phaseC_patches.json")
                      .read_text(encoding="utf-8"))
re_src = dict(enumerate(cells_pre))
for p in manifest:
    assert re_src[p["cell"]].count(p["old"]) == 1, p["name"]
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
ck("P3b manifest re-derivation equality (17 patches)",
   all(re_src[i] == cells_post[i] for i in range(27)) and len(manifest) == 17)

# NOTE: do NOT .strip() the whole porcelain output — the first line's
# status code " M" begins with the very space a whole-output strip eats
# (M6-B2 observed bug). Split first, then filter.
status = [ln for ln in git("status", "--porcelain").split("\n")
          if ln.strip()]
changed = set()
for ln in status:
    path = ln[3:].strip()  # XY + <space> + path (quoted iff spaces/parens)
    if path.startswith('"') and path.endswith('"'):
        path = path[1:-1]
    if path:
        changed.add(path)
ck("P4 inventory == expected 9 files", changed == EXPECTED_FILES,
   f"extra={sorted(changed - EXPECTED_FILES)} "
   f"missing={sorted(EXPECTED_FILES - changed)}")

ck("P5 verify instrument present",
   (REPO / "scripts/m009_b2_phaseC_verify.py").exists())

print()
if fails:
    print(f"PRECOMMIT FAILED: {len(fails)}")
    sys.exit(1)
print("PRECOMMIT OK — all invariants held at commit time")
