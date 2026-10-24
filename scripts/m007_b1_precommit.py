#!/usr/bin/env python3
r"""MANGABD-007 B1 — pre-commit audit (staged tree).

Gates (all must be GREEN before `git commit`):
  P1 scope: staged == {notebook (M), agents/GLM_5_3.md (M)}
      + exactly the 3 M007 instrument adds (RF-9 lesson applied at
      Phase C time); zero deletes
  P2 modes: all staged 100644, no mode changes
  P3 secret scan on ALL added lines
  P4 AST: staged notebook cells compile 27/27 warnings-as-errors
  P5 base integrity: 26 non-target cells byte-identical to 292369a
      (re-asserted from the staged tree)
  P6 wiring probes on the staged bytes: cell-1 literal 2048 exactly once
      + zero 1024-literal remnants; cell-9 byte-untouched with the
      migration block + ladder intact
  P7 docs markers: MANGABD-007 Phase C record + §E.1 follow-up-closure
      disclosure + header entry present; M005/M006 records intact
  P8 instruments: the 3 staged .py files AST-clean
"""
import ast
import json
import re
import subprocess
import sys
import warnings

REPO = "/home/z/my-project/MangaBD"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "292369a"
INSTRUMENTS = {
    "scripts/m007_b1_build.py",
    "scripts/m007_b1_verify.py",
    "scripts/m007_b1_precommit.py",
}

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


def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True, cwd=REPO)


# P0: stage everything first (audit BEFORE commit, on the staged set)
run("git", "add", "-A")
st = run("git", "diff", "--cached", "--name-status").stdout.strip().splitlines()
print("staged:")
for ln in st:
    print("   ", ln)

added, modified, deleted = set(), set(), set()
for ln in st:
    status, path = ln.split("\t", 1)
    if status.startswith("A"):
        added.add(path)
    elif status.startswith("M"):
        modified.add(path)
    elif status.startswith("D"):
        deleted.add(path)

check("P1a modified == {notebook, agents/GLM_5_3.md}",
      modified == {NB_NAME, "agents/GLM_5_3.md"}, f"modified={sorted(modified)}")
check("P1b added == exactly the 3 M007 instruments (RF-9 lesson at Phase C time)",
      added == INSTRUMENTS, f"added={sorted(added)}")
check("P1c zero deletions", not deleted, f"deleted={sorted(deleted)}")

# P2: modes
modes = run("git", "diff", "--cached", "--raw").stdout.strip().splitlines()
bad_modes = []
for ln in modes:
    m = re.match(r":(\d{6}) (\d{6}) ", ln)
    if not m:
        bad_modes.append(ln)
        continue
    old_mode, new_mode = m.group(1), m.group(2)
    if new_mode != "100644" or (old_mode != "000000" and old_mode != new_mode):
        bad_modes.append(ln)
check("P2 no file-mode changes (all staged at 100644)", not bad_modes, str(bad_modes[:3]))

# P3: secret scan on added lines
numstat = run("git", "diff", "--cached", "--numstat").stdout.strip().splitlines()
added_text = 0
scanned_text = 0
suspicious = []
PATTERNS = [
    r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
    r"sk-[A-Za-z0-9]{20,}", r"hf_[A-Za-z0-9]{20,}", r"AIza[A-Za-z0-9_-]{20,}",
    r"xox[baprs]-[A-Za-z0-9-]{20,}", r"Bearer\s+[A-Za-z0-9._-]{20,}",
    r"(?i)api_key\s*=\s*['\"][A-Za-z0-9]{16,}", r"(?i)password\s*=\s*['\"][^'\"]{6,}",
    r"(?i)secret\s*=\s*['\"][A-Za-z0-9]{12,}",
]
for ln in numstat:
    parts = ln.split("\t")
    if len(parts) != 3:
        continue
    a, d, path = parts
    if a == "-":
        continue
    added_text += int(a)
    diff = run("git", "diff", "--cached", "-U0", "--", path).stdout
    for dline in diff.splitlines():
        if dline.startswith("+") and not dline.startswith("+++"):
            scanned_text += 1
            for pat in PATTERNS:
                if re.search(pat, dline):
                    suspicious.append((path, pat, dline[:100]))
check(f"P3 secret scan: 0 hits on {scanned_text} added lines ({added_text} additions)",
      not suspicious, str(suspicious[:3]))

# P4: AST on the STAGED notebook bytes
nb_staged = run("git", "show", f":{NB_NAME}").stdout
nb = json.loads(nb_staged)
ok_ast = True
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(src, f"staged_cell_{i:02d}.py", "exec")
        except (Warning, SyntaxError) as w:
            ok_ast = False
            print(f"      cell {i}: {w}")
check("P4 staged notebook AST 27/27 warnings-as-errors",
      ok_ast and len(nb["cells"]) == 27)

# P5: 26 non-target cells byte-identical to 292369a (staged tree)
base_raw = run("git", "show", f"{BASE_REF}:{NB_NAME}").stdout
base_nb = json.loads(base_raw)
drift = [i for i in range(27) if i != 1
         and json.dumps(nb["cells"][i]) != json.dumps(base_nb["cells"][i])]
check(f"P5 26 non-target cells byte-identical to {BASE_REF} (staged tree)",
      not drift, f"drift={drift}")

# P6: wiring probes on staged bytes
CELL = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}
probes = [
    ("P6a cell-1 literal now 2048, exactly once",
     CELL[1].count('"lama_size": 2048,') == 1),
    ("P6b cell-1 zero 1024-literal remnants",
     '"lama_size": 1024' not in CELL[1]),
    ("P6c cell-9 fully byte-identical to base (staged)",
     json.dumps(nb["cells"][9]) == json.dumps(base_nb["cells"][9])),
    ("P6d cell-9 migration block intact (legacy guard)",
     "_lama_size_legacy = MANGABD_CONFIG[\"inpainting\"].get(\"lama_size\")" in CELL[9]
     and 'if _lama_size_legacy is None or int(_lama_size_legacy) == 1024:' in CELL[9]
     and 'MANGABD_CONFIG["inpainting"]["lama_size"] = 2048' in CELL[9]),
    ("P6e cell-9 ladder tuple intact",
     "ladder = [lama_size] + [r for r in (2048, 1536, 1024) if r < lama_size]" in CELL[9]),
    ("P6f cell-1 inpainting block shape preserved (engine/fallback keys)",
     '"engine": "lama"' in CELL[1] and '"fallback_engine": "opencv"' in CELL[1]
     and '"lama_size": 2048,' in CELL[1].split('"inpainting": {')[1].split("}")[0]),
]
for name, cond in probes:
    check(name, cond)

# P7: docs markers on staged bytes
glm = run("git", "show", ":agents/GLM_5_3.md").stdout
check("P7a GLM_5_3.md: MANGABD-007 Phase C record present",
      "# MANGABD-007 — PHASE C (BATCH 1): CELL-1 LAMA_SIZE CLEANUP" in glm)
check("P7b GLM_5_3.md: record closes the MANGABD-005 B1 §E.1 follow-up (disclosed)",
      "Closes tracked follow-up #1 of the MANGABD-005 B1 chain" in glm
      and "DECISION.md §E.1 item 1" in glm)
check("P7c GLM_5_3.md: CURRENT PHASE header entry present (WIP, awaiting Phase D)",
      "**MANGABD-007 — BATCH 1 (B1) PHASE C DELIVERED (WIP on branch `mangabd-007-b1`"
      in glm)
check("P7d GLM_5_3.md: record tail marker present",
      "— End of MANGABD-007 Phase C (Batch 1) record" in glm)
check("P7e GLM_5_3.md: M005/M006 records intact",
      "# MANGABD-005 — PHASE C (BATCH 1)" in glm
      and "# MANGABD-006 — BATCH 2 (M6-B2) MERGE COMPLETION RECORD" in glm
      and "MANGABD-006 disposition: TASK CLOSED" in glm)
check("P7f GLM_5_3.md: instrument provenance block present (RF-9 lesson)",
      "RF-9 lesson applied at Phase C" in glm)

# P8: instruments AST-clean + non-empty (guard against empty-blob false-pass)
ok_instr = True
for path in sorted(INSTRUMENTS):
    src = run("git", "show", f":{path}").stdout
    if not src.strip():
        ok_instr = False
        print(f"      {path}: EMPTY staged blob (not staged?)")
        continue
    try:
        ast.parse(src)
    except SyntaxError as e:
        ok_instr = False
        print(f"      {path}: {e}")
check("P8 3 staged instruments non-empty + AST-clean", ok_instr)

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
sys.exit(1 if FAIL else 0)
