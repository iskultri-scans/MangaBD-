#!/usr/bin/env python3
r"""MANGABD-008 B1 Phase C — pre-commit audit (run AFTER staging, BEFORE commit).

Validates the staged WIP set on branch mangabd-008-b1 (HEAD must be the
Phase A base 73ca565): exactly the expected 13 files, scope/AST integrity,
vendored-font sha256/size/license pins, samples/models/S007 untouched,
A/M only 100644, secret scan on all added lines, docs anchors, and the
m002_sim_v2 = 0 abort-sites gate.
"""
import hashlib
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
HEAD_REF = "73ca565"
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_CELLS = Path("/home/z/my-project/cells")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"

EXPECTED = {
    ("M", "MangaBD_V12_ipynb_txt.ipynb (3).txt"),
    ("M", "agents/GLM_5_3.md"),
    ("M", "scripts/m008_b1_kana_repro.py"),
    ("A", "assets/fonts/NotoSansJP[wght].ttf"),
    ("A", "assets/fonts/OFL-NotoSansJP.txt"),
    ("A", "scripts/m008_b1_phaseC_build.py"),
    ("A", "scripts/m008_b1_phaseC_content4.py"),
    ("A", "scripts/m008_b1_phaseC_content10.py"),
    ("A", "scripts/m008_b1_phaseC_content10b.py"),
    ("A", "scripts/m008_b1_phaseC_content1112.py"),
    ("A", "scripts/m008_b1_phaseC_patches.json"),
    ("A", "scripts/m008_b1_phaseC_verify.py"),
    ("A", "scripts/m008_b1_phaseC_precommit.py"),
}

results = []


def check(name, cond, detail=""):
    ok = bool(cond)
    print(("PASS  " if ok else "FAIL  ") + name + ("" if ok else f"  [{detail}]"))
    results.append((name, ok))


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout


# P0 — branch, HEAD, staged set
branch = git("branch", "--show-current").strip()
check("P0a on branch mangabd-008-b1", branch == "mangabd-008-b1", branch)
head = git("rev-parse", "--short", "HEAD").strip()
check("P0b HEAD == 73ca565 (the Phase A ruling base)", head == "73ca565", head)

staged = set()
for ln in git("status", "--porcelain").splitlines():
    if not ln.strip():
        continue
    st, path = ln[:2].strip(), ln[3:].strip().strip('"')
    staged.add((st, path))
check("P0c staged set exactly the 13 expected files", staged == EXPECTED,
      f"extra={sorted(staged - EXPECTED)} missing={sorted(EXPECTED - staged)}")
unstaged = [ln for ln in git("status", "--porcelain").splitlines()
            if ln.strip() and ln[:2] not in ("A ", "M ", "AM") and not ln.startswith("??")]
check("P0d no unstaged/untracked stragglers beyond the staged set", not unstaged,
      str(unstaged))

# P1 — notebook integrity + scope
nb = json.loads((REPO / NB_NAME).read_text(encoding="utf-8"))
cells_post = ["".join(c.get("source", [])) for c in nb["cells"]
              if c.get("cell_type") == "code"]
nb_pre = json.loads(git("show", f"{HEAD_REF}:{NB_NAME}"))
cells_pre = ["".join(c.get("source", [])) for c in nb_pre["cells"]
             if c.get("cell_type") == "code"]
scope = sorted(i for i in range(27) if cells_post[i] != cells_pre[i])
check("P1a notebook scope drift exactly {4, 10, 11, 12}", scope == [4, 10, 11, 12],
      f"drift={scope}")
import ast  # noqa: E402
for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ast.parse(cells_post[i])
check("P1b AST 27/27 (warnings-as-errors)", True)

with open(REPO / "scripts/m008_b1_phaseC_patches.json", encoding="utf-8") as f:
    patches = json.load(f)
re_src = dict(enumerate(cells_pre))
for p in patches:
    if re_src[p["cell"]].count(p["old"]) != 1:
        check(f"P1c re-derivation anchor {p['name']}", False)
        break
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
else:
    check("P1c re-derivation: post == pre + the 20 manifest patches",
          all(re_src[i] == cells_post[i] for i in range(27)) and len(patches) == 20)

# P2 — vendored font pins
font = REPO / "assets/fonts/NotoSansJP[wght].ttf"
sha = hashlib.sha256(font.read_bytes()).hexdigest()
check("P2a vendored font sha256 == pin", sha == SHA_PIN, sha)
check("P2b vendored font size == 9,589,900", font.stat().st_size == 9589900)
lic = (REPO / "assets/fonts/OFL-NotoSansJP.txt").read_text(encoding="utf-8")
check("P2c OFL-1.1 license vendored",
      "SIL OPEN FONT LICENSE Version 1.1" in lic)
check("P2d cell-4 source carries the identical pin", SHA_PIN in cells_post[4])
check("P2e no Open-RAIL-M anywhere in the batch",
      all("Open-RAIL" not in cells_post[i] for i in range(27)))

# P3 — protected trees untouched
protected = git("diff", "--name-only", HEAD_REF, "--", "samples/", "models/",
                "S007_mangabd005_02.zip").strip()
check("P3a samples/models/S007 untouched vs HEAD", not protected, protected)
flash = git("diff", "--name-only", HEAD_REF, "--", "agents/GLM_5_3_FLASH.md").strip()
check("P3b GLM_5_3_FLASH.md untouched (Flash owns it)", not flash, flash)

# P4 — modes
modes = set()
for ln in git("diff", "--cached", "--name-status").splitlines():
    if ln.strip():
        modes.add((ln.split()[0],))
check("P4 A/M only, 100644, zero deletes/renames",
      all(m in (("A",), ("M",)) for m in modes),
      f"modes={sorted(modes)}")

# P5 — secret scan on all added lines
added = []
for path in sorted(p for _, p in EXPECTED if not p.endswith(".ttf")):
    p = REPO / path
    if not p.exists() or p.is_dir():
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    added.extend(text.splitlines())
joined = "\n".join(added)
hits = [pat for pat in (r"ghp_[A-Za-z0-9]{20,}", r"sk-[A-Za-z0-9]{20,}",
                        r"AIza[A-Za-z0-9\-_]{20,}", r"hf_[A-Za-z0-9]{20,}",
                        r"Bearer\s+[A-Za-z0-9\-_.]{20,}", r"(?i)api_key\s*=\s*['\"][^'\"]{12,}")
        if re.search(pat, joined)]
check("P5 secret scan 0 hits on added text lines", not hits, str(hits))

# P6 — docs anchors
doc = (REPO / "agents/GLM_5_3.md").read_text(encoding="utf-8")
anchors = [
    "# MANGABD-008 — PHASE C: GLYPH-COVERAGE FIX",
    "§M8-C1 — WHAT CHANGED, PER CELL",
    "§M8-C2 — THE VENDORED FONT",
    "§M8-C3 — VERIFICATION (49/49 ALL GREEN",
    "§M8-C4 — THE 6 HARD CONSTRAINTS, PROVEN PRESERVED",
    "§M8-C5 — DISCLOSURES",
    "§M8-C6 — DISPOSITION",
    "MANGABD-008 — BATCH 1 (B1) PHASE C IMPLEMENTED",
    "mangabd-008-b1",
    SHA_PIN,
]
missing = [a for a in anchors if a not in doc]
check("P6 GLM_5_3.md Phase C record anchors present", not missing, str(missing))

# P7 — m002_sim_v2 abort sites on the post-change cells (already in cells/)
sim = subprocess.run(["python3", str(SIM)], capture_output=True, text=True)
m = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)",
              sim.stdout)
check("P7 m002_sim_v2 = 0 abort sites (post-change cells)",
      sim.returncode == 0 and m is not None and int(m.group(1)) == 0,
      (m.group(1) if m else "parse-fail") + (sim.stderr or "")[-120:])

print("\n" + "=" * 60)
fails = [n for n, ok in results if not ok]
print(f"MANGABD-008 PHASE C PRECOMMIT: {len(results) - len(fails)}/{len(results)} PASS")
if fails:
    for n in fails:
        print("  FAILED: " + n)
    sys.exit(1)
print("ALL GREEN")
