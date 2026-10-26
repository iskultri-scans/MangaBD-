#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-13 — pre-commit audit (run AFTER staging, BEFORE commit).

Validates the staged RF-13 set on branch mangabd-008-b1 (HEAD must be
c072dc5 = the Flash RF-12 DELTA CHECK report, docs-only — its notebook
== RF-12 5a84994's; it landed mid-flight after the RF-13 build started on
the then-tip 5a84994 — docs-only-between re-parent, NO amend):
exactly the expected 10 files, scope {4,10,11,12} only (vs HEAD's notebook
== RF-12 5a84994's), A/M only 100644, secret scan, docs anchors (incl. ALL
prior records), untouched sentinels (vendored font, samples, models, Flash
report, prior instruments), and the m002_sim_v2 = 0 abort-sites gate.
"""
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
HEAD_REF = "c072dc5"          # HEAD: the Flash RF-12 DELTA CHECK report
                             # (docs-only, notebook blob == 5a84994's)
NB_BASE_REF = "5a84994"        # RF-12 (the notebook scope-referenced base)
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_CELLS = Path("/home/z/my-project/cells")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"

EXPECTED = {
    ("M", NB_NAME),
    ("M", "agents/GLM_5_3.md"),
    ("A", "scripts/m008_b1_rf13_build.py"),
    ("A", "scripts/m008_b1_rf13_patches.json"),
    ("A", "scripts/m008_b1_rf13_verify.py"),
    ("A", "scripts/m008_b1_rf13_precommit.py"),
    ("A", "scripts/m008_b1_rf13_repro.py"),
    ("A", "scripts/m008_b1_rf13_dump.py"),
    ("A", "scripts/m008_b1_rf13_evidence.md"),
    ("A", "scripts/m008_rf13_docs.py"),
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
head = git("rev-parse", "HEAD").strip()
check("P0b HEAD == c072dc5 (the Flash RF-12 DELTA CHECK report, docs-only) "
      "— new commit on top, NO amend",
      head.startswith(HEAD_REF), head[:12])

staged = {}
for line in git("diff", "--cached", "--name-status").splitlines():
    st, p = line.split("\t", 1)
    staged[p] = st
check("P0c staged set exactly the 10 expected files",
      {(v, k) for k, v in staged.items()} == EXPECTED,
      f"got {sorted(staged.items())}")

modes = set()
for p in staged:
    m = git("ls-files", "--cached", "-s", p).split()
    modes.add((m[0], staged[p]))
check("P0d A/M only, mode 100644 only",
      all(x in {("100644", "M"), ("100644", "A")} for x in modes), modes)

# P1 — scope + byte proofs on the STAGED notebook (vs RF-12 5a84994's bytes,
# which == HEAD c072dc5's — docs-only report between)
blob = git("rev-parse", f"{NB_BASE_REF}:{NB_NAME}").strip()
nb_head = json.loads(git("show", f"{NB_BASE_REF}:{NB_NAME}"))
nb_staged = json.loads(git("show", f":{NB_NAME}"))
cells_head = ["".join(c["source"]) for c in nb_head["cells"]]
cells_staged = ["".join(c["source"]) for c in nb_staged["cells"]]
scope = sorted(i for i in range(27) if cells_head[i] != cells_staged[i])
check("P1a staged notebook drift vs HEAD exactly {4,10,11,12}", scope == [4, 10, 11, 12],
      f"drift={scope}")
top_h = {k: v for k, v in nb_head.items() if k != "cells"}
top_s = {k: v for k, v in nb_staged.items() if k != "cells"}
check("P1b non-source + top-level fields identical", top_h == top_s
      and all({k: v for k, v in a.items() if k != "source"} ==
              {k: v for k, v in b.items() if k != "source"}
              for a, b in zip(nb_head["cells"], nb_staged["cells"])))

# P2 — sentinels untouched
sha = hashlib.sha256((REPO / "assets/fonts/NotoSansJP[wght].ttf").read_bytes()).hexdigest()
check("P2a vendored font sha untouched", sha == SHA_PIN)
wt = git("status", "--porcelain").splitlines()
untouched_ok = not any(l.strip().startswith(("M", "A", "??", "D"))
                       for l in wt
                       if l.split()[-1].startswith(("samples/", "models/",
                                                     "agents/GLM_5_3_FLASH.md",
                                                     "S007_mangabd005"))
                       and l.split()[-1] not in staged)
check("P2b samples/models/S007/FLASH report untouched", untouched_ok,
      [l for l in wt if 'samples' in l or 'FLASH' in l])
prior = ["m008_b1_rf12_build.py", "m008_b1_rf12_verify.py", "m008_b1_rf12_precommit.py",
         "m008_b1_rf12_patches.json", "m008_b1_rf11_build.py", "m008_b1_rf11_verify.py",
         "m008_b1_rf10_build.py", "m008_b1_phaseC_build.py", "m008_b1_rf10_verify.py",
         "m008_b1_rf11_precommit.py", "m008_b1_rf12_verify.py"]
check("P2c prior RF instruments untouched",
      not any(f"scripts/{p}" in staged for p in prior))

# P3 — docs anchors
docs = (REPO / "agents/GLM_5_3.md").read_text(encoding="utf-8")
for anchor in ["RF-13 DELIVERED", "§M8-C10", "§M8-C9", "§M8-C8",
               "MANGABD-008 — PHASE C", "CURRENT PHASE"]:
    check(f"P3 anchor present: {anchor}", anchor in docs)
check("P3g single CURRENT PHASE section", docs.count("## CURRENT PHASE") == 1)

# P4 — secret scan on staged text
secrets = re.compile(r"(ghp_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|"
                     r"AIza[A-Za-z0-9_-]{30,}|hf_[A-Za-z0-9]{20,}|"
                     r"Bearer [A-Za-z0-9._-]{20,})", re.I)
hits = []
for p in staged:
    fp = REPO / p
    if fp.suffix in {".md", ".py", ".json", ".txt"} and fp.stat().st_size < 3_000_000:
        try:
            m = secrets.findall(fp.read_text(encoding="utf-8", errors="ignore"))
            hits += [f"{p}:{x}" for x in m]
        except Exception:
            pass
check("P4 secret scan 0 hits", not hits, hits[:5])

# P5 — m002_sim_v2 gate
SIM_CELLS.mkdir(exist_ok=True)
for old in SIM_CELLS.glob("cell_*.py"):
    old.unlink()
for i in range(27):
    (SIM_CELLS / f"cell_{i:02d}.py").write_text(cells_staged[i], encoding="utf-8")
sim = subprocess.run(["python3", str(SIM)], capture_output=True, text=True)
m_abort = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)",
                    sim.stdout)
check("P5 m002_sim_v2 = 0 abort sites (staged cells)",
      sim.returncode == 0 and m_abort is not None and int(m_abort.group(1)) == 0,
      (sim.stderr or sim.stdout)[-150:])

print()
fails = [n for n, ok in results if not ok]
print(f"RF-13 PRECOMMIT: {len(results) - len(fails)}/{len(results)} PASS")
if fails:
    print("FAILED:")
    for n in fails:
        print("  - " + n)
    sys.exit(1)
print("ALL GREEN — commit may proceed")
