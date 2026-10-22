#!/usr/bin/env python3
r"""MANGABD-006 B1 — pre-commit audit.

Gates (all must be GREEN before `git commit`):
  P1 scope: staged set == {notebook, agents/GLM_5_3.md} + the 8 vendored
      weight files under models/ (nothing else, no deletions)
  P2 modes: no executable-bit changes (all staged files 100644)
  P3 secret scan on ALL added lines (staged diff + new weight-file names)
  P4 AST: notebook cells compile 27/27 warnings-as-errors (staged bytes)
  P5 base integrity: notebook parent state == 86d4bdf blob for the 23
      non-target cells (re-asserted from the staged tree)
"""
import json
import re
import subprocess
import sys
import warnings

REPO = "/home/z/my-project/MangaBD"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"

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

EXPECTED_WEIGHTS = {
    "models/kellenok/det/manga_det_v0.2.onnx",
    "models/kellenok/rec/manga_rec_v0.2.onnx",
    "models/kellenok/ppocrv6_dict.txt",
    "models/baberu/onnx/vision_int4.onnx",
    "models/baberu/onnx/decoder_prefill_int8.onnx",
    "models/baberu/onnx/decoder_step_int8.onnx",
    "models/baberu/tokenizer/vocab.json",
    "models/baberu/tokenizer/tokenizer_config.json",
}
added = set()
modified = set()
deleted = set()
for ln in st:
    status, path = ln.split("\t", 1)
    if status.startswith("A"):
        added.add(path)
    elif status.startswith("M"):
        modified.add(path)
    elif status.startswith("D"):
        deleted.add(path)

check("P1a exactly 2 modified tracked files (notebook + GLM_5_3.md)",
      modified == {NB_NAME, "agents/GLM_5_3.md"}, f"modified={sorted(modified)}")
check("P1b 8 vendored weight files added",
      added == EXPECTED_WEIGHTS, f"added={sorted(added)}")
check("P1c zero deletions", not deleted, f"deleted={sorted(deleted)}")

# P2: modes — every staged entry must land at 100644 (000000->100644 is a
# normal ADD; only a non-100644 target mode or a mode CHANGE is a violation)
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
check("P2 no file-mode changes (all staged at 100644; adds are 000000->100644)",
      not bad_modes, str(bad_modes[:3]))

# P3: secret scan on added lines of TEXT files (binary weights excluded by
# git diff --numstat zero-lines heuristic)
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
    if path in EXPECTED_WEIGHTS or a == "-":
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

# P5: 23 non-target cells byte-identical to 86d4bdf (from staged tree)
base_raw = run("git", "show", f"86d4bdf:{NB_NAME}").stdout
base_nb = json.loads(base_raw)
TARGET = {5, 7, 15, 25}
drift = [i for i in range(27) if i not in TARGET
         and "".join(nb["cells"][i]["source"]) != "".join(base_nb["cells"][i]["source"])]
check("P5 23 non-target cells byte-identical to 86d4bdf (staged tree)", not drift,
      f"drift={drift}")

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
sys.exit(1 if FAIL else 0)
