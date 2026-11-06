#!/usr/bin/env python3
r"""MANGABD-009 B3 Phase C — pre-commit audit (staged-set checks).

Run AFTER `git add` of the exact Phase C file set, BEFORE `git commit`.
"""
import json
import subprocess
import sys
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "8fbde52"
BRANCH = "mangabd-009-b3"

EXPECTED = {
    NB_NAME,
    "agents/GLM_5_3.md",
    "scripts/m009_b3_phaseC_build.py",
    "scripts/m009_b3_phaseC_content.py",
    "scripts/m009_b3_phaseC_commit_msg.txt",
    "scripts/m009_b3_phaseC_harness.py",
    "scripts/m009_b3_phaseC_patches.json",
    "scripts/m009_b3_phaseC_precommit.py",
    "scripts/m009_b3_phaseC_verify.py",
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
print("MANGABD-009 B3 Phase C — PRECOMMIT")
print("=" * 72)

# P0 branch
check("P0a branch mangabd-009-b3",
      git("branch", "--show-current").strip() == BRANCH)

# P1 staged set exactly
staged = [ln for ln in
          git("diff", "--cached", "--name-only",
              "--diff-filter=AM").strip().splitlines() if ln]
check("P1a staged set exactly the 9 Phase C files",
      set(staged) == EXPECTED and len(staged) == len(EXPECTED),
      f"staged={sorted(staged)}")

# P2 notebook integrity
work_blob = git("hash-object", NB_NAME).strip()
staged_blob = git("rev-parse", f":{NB_NAME}").strip()
check("P2a staged notebook blob == work tree (no drift)",
      work_blob == staged_blob, work_blob[:12])

nb = json.loads((REPO / NB_NAME).read_text(encoding="utf-8"))
cells_work = ["".join(c["source"]) for c in nb["cells"]
              if c.get("cell_type") == "code"]
raw_base = git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8")
nb_base = json.loads(raw_base.decode("utf-8"))
cells_base = ["".join(c["source"]) for c in nb_base["cells"]
              if c.get("cell_type") == "code"]
scope = [i for i in range(27) if cells_work[i] != cells_base[i]]
check("P2b scope drift exactly {6,10,11,12}",
      sorted(scope) == [6, 10, 11, 12], f"drift={sorted(scope)}")

with warnings.catch_warnings():
    warnings.simplefilter("error")
    for i in range(27):
        compile(cells_work[i], f"cell_{i:02d}.py", "exec")
check("P2c AST compile 27/27 (warnings-as-errors)", True)

patches = json.loads(
    (REPO / "scripts" / "m009_b3_phaseC_patches.json").read_text(
        encoding="utf-8"))
re_src = list(cells_base)
for p in patches:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"{p['name']} anchor"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
check("P2d manifest re-derivation (work == 8fbde52 + exactly the patches)",
      all(re_src[i] == cells_work[i] for i in range(27)),
      f"{len(patches)} patches")

# B3 wiring probes on the staged notebook
c6w, c10w, c11w, c12w = (cells_work[6], cells_work[10],
                         cells_work[11], cells_work[12])
check("P2e B3 wiring (knob both ends, sampler, conditional key, "
      "override, kwarg chain)",
      c6w.count("color_inherit_enable") == 2
      and "def _b3_undilated_ink_mask(" in c6w
      and "def _b3_sample_ink_color(" in c6w
      and 'regions[-1]["ink_color"] = _b3_c' in c6w
      and c10w.count("b3_page_ink") >= 3
      and "text_color = _b3_row_ink" in c10w
      and "ink_color=_b3_row_ink," in c10w
      and "ink_color=None" in c11w and "ink_color=None" in c12w
      and "ink_color=ink_color)" in c11w
      and "ink_color=ink_color)" in c12w
      and "# Test 23: B3" in c10w)

# P3 untouched surfaces vs HEAD (this commit must not modify them)
untouched = ["agents/DECISION.md", "agents/GLM_5_3_FLASH.md",
             "agents/PROJECT_CONTEXT.md", "agents/TASK.md",
             "S007_mangabd005_02.zip"] + [
    str(p.relative_to(REPO)) for p in sorted(
        (REPO / "samples").rglob("*")) if p.is_file()]
tracked = git("ls-tree", "-r", "--name-only", "HEAD").splitlines()
bad = []
for f in untouched:
    if f in tracked:
        h_idx = git("rev-parse", f":{f}").strip()
        h_head = git("rev-parse", f"HEAD:{f}").strip()
        if h_idx != h_head:
            bad.append(f)
check("P3a DECISION.md + FLASH.md + S007 zip + samples/ byte-identical "
      "to HEAD", not bad, f"changed={bad}" if bad else f"{len(untouched)} files")

# P4 GLM_5_3.md anchors
glm = (REPO / "agents" / "GLM_5_3.md").read_text(encoding="utf-8")
l11 = glm.split("\n")[10]
check("P4a CURRENT PHASE = B3 PHASE C DELIVERED",
      l11.startswith("**MANGABD-009 — B3 PHASE C DELIVERED:")
      and "Flash Phase D" in l11)
check("P4b Phase C H1 unique + M9-B3C.0..5 present",
      glm.count("# MANGABD-009 — PHASE C (B3): INK COLOR INHERITANCE "
                "(GLM-5.3, 2026-11-06)") == 1
      and all(f"## M9-B3C.{k}" in glm for k in range(6)))
check("P4c prior records intact (Phase A B3 + B2.1 chain)",
      glm.count("# MANGABD-009 — PHASE A (B3): INK COLOR INHERITANCE") == 1
      and glm.count("## M9-B3-A.11 Instruments and custody") == 1
      and glm.count("# MANGABD-009 — B2.1 MERGE COMPLETION RECORD "
                    "(GLM-5.3, 2026-11-06)") == 1
      and glm.count("## M9-B21C.5 Next") == 1
      and glm.count("# MANGABD-009 — B2.1 MERGE COMPLETION RECORD") == 2)
staged_glm = git("rev-parse", ":agents/GLM_5_3.md").strip()
work_glm = git("hash-object", "agents/GLM_5_3.md").strip()
check("P4d staged GLM_5_3.md == work tree", staged_glm == work_glm)

# P5 secret scan on the staged diff (added lines only)
diff = git("diff", "--cached", "-U0", "--diff-filter=AM")
added = "\n".join(ln[1:] for ln in diff.splitlines()
                  if ln.startswith("+") and not ln.startswith("+++"))
SECRET_PATTERNS = [
    (r"api_key\s*=\s*['\"][^'\"]{8,}", "api_key assignment"),
    (r"password\s*=\s*['\"][^'\"]{4,}", "password assignment"),
    (r"token\s*=\s*['\"][A-Za-z0-9._-]{8,}", "token assignment"),
    (r"AKIA[0-9A-Z]{16}", "AWS key id"),
    (r"sk-[A-Za-z0-9_-]{16,}", "sk- key"),
    (r"-----BEGIN [A-Z ]*PRIVATE KEY", "private key block"),
]
import re as _re
hits = [lbl for pat, lbl in SECRET_PATTERNS if _re.search(pat, added)]
check("P5a secret-pattern scan on added lines (0 hits)", not hits,
      f"{len(added.splitlines())} added lines, hits={hits}")

# P6 WIP markers
_ZH_FILLER = "\u5f85\u8865\u5145"  # CJK "to be filled in" marker
WIP_PATTERNS = [
    (r"#\s*TODO\b", "TODO comment"),
    (r"#\s*FIXME\b", "FIXME comment"),
    (r"#\s*XXX\b", "XXX comment"),
    (r"#\s*TBD\b", "TBD comment"),
    (_ZH_FILLER, "CJK filler marker"),
    (r"//\s*TODO\b", "TODO comment"),
]
wip = [lbl for pat, lbl in WIP_PATTERNS if _re.search(pat, added)]
check("P6a no WIP markers in the delta", not wip, f"hits={wip}")

n_ok = sum(RESULTS)
print("\n" + "=" * 72)
print(f"B3 Phase C PRECOMMIT: {n_ok}/{len(RESULTS)} PASS")
print("=" * 72)
sys.exit(0 if n_ok == len(RESULTS) else 1)
