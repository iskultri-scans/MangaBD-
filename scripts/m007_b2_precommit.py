#!/usr/bin/env python3
r"""MANGABD-007 B2 — pre-commit audit (staged tree).

Gates (all must be GREEN before `git commit`):
  P1 scope: staged == {notebook (M), agents/GLM_5_3.md (M)}
      + exactly the 6 M007-B2 instrument adds (RF-9 lesson applied at
      Phase C time: build / content5 / content8 / verify / precommit /
      6-patch manifest JSON); zero deletes
  P2 modes: all staged 100644, no mode changes
  P3 secret scan on ALL added lines
  P4 AST: staged notebook cells compile 27/27 warnings-as-errors
  P5 base integrity: 25 non-target cells byte-identical to dcd96c0
      (re-asserted from the staged tree)
  P6 wiring probes on the staged bytes: S05-1 (ensure_embedding +
      _embedding_load_failed defined once each, the Bengali diagnostic
      template, Test 10 present) + S05-2 (iterative unescape loop,
      escape_warn + trailing_backslash counters, Tests 31-32)
  P7 docs markers: MANGABD-007 Phase C (Batch 2) record + S05-1/S05-2
      follow-up-closure disclosure + CURRENT PHASE WIP entry; the B1 /
      M005 / M006 records intact
  P8 instruments: the 5 staged .py files AST-clean + the manifest
      JSON-parses with exactly 6 patches (guard against empty-blob
      false-pass)
"""
import ast
import json
import re
import subprocess
import sys
import warnings

REPO = "/home/z/my-project/MangaBD"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "dcd96c0"
INSTRUMENTS = {
    "scripts/m007_b2_build.py",
    "scripts/m007_b2_content5.py",
    "scripts/m007_b2_content8.py",
    "scripts/m007_b2_verify.py",
    "scripts/m007_b2_precommit.py",
}
MANIFEST = "scripts/m007_b2_patches.json"

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
check("P1b added == exactly the 6 M007-B2 instruments (RF-9 lesson at Phase C time)",
      added == INSTRUMENTS | {MANIFEST}, f"added={sorted(added)}")
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

# P5: 25 non-target cells byte-identical to dcd96c0 (staged tree)
base_raw = run("git", "show", f"{BASE_REF}:{NB_NAME}").stdout
base_nb = json.loads(base_raw)
drift = [i for i in range(27) if i not in {5, 8}
         and json.dumps(nb["cells"][i]) != json.dumps(base_nb["cells"][i])]
check(f"P5 25 non-target cells byte-identical to {BASE_REF} (staged tree)",
      not drift, f"drift={drift}")
changed = sorted(i for i in range(27)
                 if json.dumps(nb["cells"][i]) != json.dumps(base_nb["cells"][i]))
check("P5b staged changed cells exactly {5, 8}", changed == [5, 8], f"changed={changed}")

# P6: wiring probes on staged bytes
CELL = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}
probes = [
    ("P6a cell-5 ensure_embedding defined exactly once",
     CELL[5].count("def ensure_embedding(self, force=False):") == 1),
    ("P6b cell-5 _embedding_load_failed defined exactly once",
     CELL[5].count("def _embedding_load_failed(self, exc):") == 1),
    ("P6c cell-5 Bengali diagnostic template (directive-exact)",
     'f"⚠️ Embedding model load failed: {reason}। "' in CELL[5]
     and 'f"Feature disabled: semantic search। "' in CELL[5]
     and "Fix: !pip install sentence-transformers OR check " in CELL[5]),
    ("P6d cell-5 graceful degrade: returns None, never raises in the handlers",
     CELL[5].count("return self._embedding_load_failed(exc)") == 3
     and "return None" in CELL[5]),
    ("P6e cell-5 Test 10 present (pass + fail arms)",
     CELL[5].count("Embedding graceful degrade (S05-1)") == 2),
    ("P6f cell-5 cached-failure short-circuit",
     'if self.errors.get("embedding") and not force:' in CELL[5]
     and 'self.errors.pop("embedding", None)' in CELL[5]),
    ("P6g cell-8 iterative unescape loop (S05-2 item 1)",
     r'while "\\[" in line or "\\]" in line:' in CELL[8]
     and r'new_line = line.replace("\\[", "[").replace("\\]", "]")' in CELL[8]),
    ("P6h cell-8 residual-escape validation warn (S05-2 item 2)",
     CELL[8].count('stats["escape_warn"] += 1') == 1
     and "residual escaped bracket" in CELL[8]),
    ("P6i cell-8 trailing-backslash strip (S05-2 item 3)",
     CELL[8].count('stats["trailing_backslash"] += 1') == 1
     and r'if line.endswith("\\"):' in CELL[8]
     and r'line = line.rstrip("\\")' in CELL[8]),
    ("P6j cell-8 Tests 31-32 present (pass + fail arms each)",
     CELL[8].count("double-escaped fixture 100% parse (S05-2)") == 2
     and CELL[8].count("mixed-escape fixture 100% parse (S05-2)") == 2),
    ("P6k cell-8 stats counters initialized",
     '"escape_warn": 0,  # M007 B2 S05-2: residual \\[ \\] after unescape' in CELL[8]
     and '"trailing_backslash": 0,' in CELL[8]),
    ("P6l cell-1 byte-identical to base (scope discipline)",
     json.dumps(nb["cells"][1]) == json.dumps(base_nb["cells"][1])),
]
for name, cond in probes:
    check(name, cond)

# P7: docs markers on staged bytes
glm = run("git", "show", ":agents/GLM_5_3.md").stdout
check("P7a GLM_5_3.md: MANGABD-007 Phase C (Batch 2) record present",
      "# MANGABD-007 — PHASE C (BATCH 2): S05-1/S05-2 HARDENING" in glm)
check("P7b GLM_5_3.md: S05-1/S05-2 follow-up-closure disclosure present",
      "## PC7B-2 Disclosure — this batch closes S05-1/S05-2" in glm
      and "(a) S05-1 closure." in glm and "(b) S05-2 closure." in glm)
check("P7c GLM_5_3.md: CURRENT PHASE header entry present (WIP, awaiting Phase D)",
      "**MANGABD-007 — BATCH 2 (B2) PHASE C DELIVERED (WIP on branch `mangabd-007-b2`"
      in glm)
check("P7d GLM_5_3.md: record tail marker present",
      "— End of MANGABD-007 Phase C (Batch 2) record" in glm)
check("P7e GLM_5_3.md: prior records intact (B1 Phase C + PC-M1 + M005 + M006)",
      "# MANGABD-007 — PHASE C (BATCH 1): CELL-1 LAMA_SIZE CLEANUP" in glm
      and "# MANGABD-007 — BATCH 1 (B1) MERGE COMPLETION RECORD" in glm
      and "# MANGABD-005 — PHASE C (BATCH 1)" in glm
      and "# MANGABD-006 — BATCH 2 (M6-B2) MERGE COMPLETION RECORD" in glm
      and "MANGABD-006 disposition: TASK CLOSED" in glm)
check("P7f GLM_5_3.md: RF-9 provenance block present",
      "RF-9 lesson applied at Phase C source" in glm)
check("P7g GLM_5_3.md: verification summary present (44/44)",
      "44/44 ALL GREEN" in glm and "32/32" in glm and "10/10" in glm)

# P8: instruments AST-clean + manifest valid (guard against empty-blob false-pass)
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
check("P8a 5 staged instruments non-empty + AST-clean", ok_instr)
mf = run("git", "show", f":{MANIFEST}").stdout
ok_manifest = False
try:
    patches = json.loads(mf)
    ok_manifest = (isinstance(patches, list) and len(patches) == 6
                   and {p["cell"] for p in patches} == {5, 8}
                   and all(set(p) == {"cell", "name", "old", "new"} for p in patches))
except Exception as e:
    print(f"      {MANIFEST}: {e}")
check("P8b manifest JSON-parses: exactly 6 patches, cells {5, 8}, full old/new pairs",
      ok_manifest)

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
sys.exit(1 if FAIL else 0)
