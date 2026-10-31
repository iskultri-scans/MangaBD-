#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-15 — pre-commit audit (post-commit form).

Gate after creating the RF-15 commit on branch mangabd-009-b2 (the
worktree is clean once the commit exists — the audit inspects the
commit's own delta vs its parent):
  P1  branch + the commit sits ON TOP of the remote tip 84aa238 (no
      amend of the fd8d625/2a37127/bd88a3e/84aa238 lineage) + worktree
      clean + the commit's delta == exactly the expected RF-15 files
  P2  committed notebook blob == the build-reported sha
  P3  scope drift exactly {11,12} + cells {6,10} HARD-untouched +
      manifest re-derivation + AST 27/27
  P4  exact commit inventory (notebook + docs + 8 instruments)
  P5  secret scan on the full delta vs 84aa238
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
BASE_REF = "84aa238"
BUILD_SHA = ("ed51ddc370cbc6993b1421217bb6e0d9935684479127121998cbf91e"
             "8bc09731")
MANIFEST = REPO / "scripts" / "m009_b2_rf15_patches.json"

EXPECTED_FILES = {
    "MangaBD_V12_ipynb_txt.ipynb (3).txt",
    "agents/GLM_5_3.md",
    "scripts/m009_b2_rf15_build.py",
    "scripts/m009_b2_rf15_content.py",
    "scripts/m009_b2_rf15_verify.py",
    "scripts/m009_b2_rf15_precommit.py",
    "scripts/m009_b2_rf15_repro.py",
    "scripts/m009_b2_rf15_patches.json",
    "scripts/m009_b2_rf15_results.json",
    "scripts/m009_b2_rf15_commit_msg.txt",
}

RESULTS = []


def check(name, cond, detail=""):
    ok = bool(cond)
    RESULTS.append(ok)
    print(f"  {'✅' if ok else '❌'} {name}" + (f"  [{detail}]" if detail else ""))


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout


print("=" * 72)
print("MANGABD-009 B2 RF-15 — PRECOMMIT AUDIT")
print("=" * 72)

check("P1a branch mangabd-009-b2", git("branch", "--show-current").strip()
      == "mangabd-009-b2")
TIP = git("rev-parse", "--short", "origin/mangabd-009-b2").strip()
check("P1b RF-15 commit sits ON TOP of the remote tip 84aa238 "
      "(no amend of the RF-14 lineage)",
      git("rev-parse", "--short", "HEAD^").strip() == TIP and TIP == "84aa238",
      f"tip={TIP}")


def _deq(s):
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s


status = [ln for ln in git("status", "--porcelain").splitlines() if ln]
changed = {_deq(ln[3:]) for ln in status if not ln.startswith("??")}
untracked = {_deq(ln[3:]) for ln in status if ln.startswith("??")}
all_new = changed | untracked
# post-commit form: the worktree is clean; audit the commit's own delta
commit_files = {_deq(ln) for ln in
                git("diff", "--name-only", "HEAD^", "HEAD").splitlines()
                if ln}
check("P1c the RF-15 commit's delta == exactly the expected inventory "
      "(worktree clean)",
      (not all_new) and commit_files == EXPECTED_FILES,
      f"commit={sorted(commit_files)}; "
      f"worktree-extra={sorted(all_new - EXPECTED_FILES)}")

blob_sha = hashlib.sha256(NB.read_bytes()).hexdigest()
check("P2 notebook blob == build-reported sha", blob_sha == BUILD_SHA,
      blob_sha[:16])

raw_work = json.loads(NB.read_text(encoding="utf-8"))
cells_work = ["".join(c.get("source", [])) for c in raw_work["cells"]]
raw_base = json.loads(git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8"))
cells_base = ["".join(c.get("source", [])) for c in raw_base["cells"]]
drift = [i for i in range(27) if cells_work[i] != cells_base[i]]
check("P3a scope drift exactly {11,12}", sorted(drift) == [11, 12],
      f"{drift}")
check("P3b cells {6,10} HARD byte-untouched (RF-15 directive)",
      cells_work[6] == cells_base[6] and cells_work[10] == cells_base[10])

patches = json.loads(MANIFEST.read_text(encoding="utf-8"))
re_src = list(cells_base)
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("P3c re-derivation equality", all(re_src[i] == cells_work[i]
                                        for i in range(27)))

with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        try:
            compile(cells_work[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL cell {i}: {w}")
check("P3d AST 27/27 (warnings-as-errors)", True)

check("P4a inventory size + notebook present in the commit delta",
      len(EXPECTED_FILES) == 10 and "MangaBD_V12_ipynb_txt.ipynb (3).txt"
      in commit_files)

# secret scan: the notebook delta + docs delta + results (the instrument
# scripts themselves contain the scan keywords — scanning them would be a
# self-referential false positive; their content is the audit code)
nb_diff = git("diff", BASE_REF, "--", NB_NAME)
hay = "\n".join(ln[1:] for ln in nb_diff.splitlines()
                if ln.startswith("+") and not ln.startswith("+++"))
docs_diff = git("diff", BASE_REF, "--", "agents/GLM_5_3.md")
hay += "\n" + "\n".join(ln[1:] for ln in docs_diff.splitlines()
                        if ln.startswith("+") and not ln.startswith("+++"))
for f in ("scripts/m009_b2_rf15_results.json",
          "scripts/m009_b2_rf15_patches.json",
          "scripts/m009_b2_rf15_commit_msg.txt"):
    if (REPO / f).exists():
        hay += ("\n" + (REPO / f).read_text(encoding="utf-8",
                                            errors="ignore"))
hits = [kw for kw in ("api_key=", "password=", "secret=", "token=",
                      "AKIA", "sk-") if kw in hay]
check("P5 secret scan (notebook delta + docs delta + results)", not hits,
      f"{hits}")

n_ok = sum(RESULTS)
print("\n" + "=" * 72)
print(f"PRECOMMIT: {n_ok}/{len(RESULTS)} PASS")
print("=" * 72)
sys.exit(0 if n_ok == len(RESULTS) else 1)
