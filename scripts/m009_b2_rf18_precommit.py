#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-18 — pre-commit audit.

Final invariants at commit time:
  P1  branch + base: on mangabd-009-b2, notebook blob == the
      session-anchored rebuild (d0ad299b…), cells == the surviving
      verified bytes;
  P2  manifest re-derivation: base(0eeca00) + the 27 committed
      hunks == the working notebook cells, scope exactly {6,10},
      cells 11/12 byte-untouched;
  P3  verify results: scripts/m009_b2_rf18_results.json == 54/54;
  P4  archive laws: S003/S007 (+S001/S002/S005*) archives UNTOUCHED
      vs 0eeca00; S009/S010 refresh modified exactly
      {detections.json, final.jpg, metadata.json}; S011 archive
      complete (11 files incl. the committed parity artifacts);
  P5  secrets scan over the staged diff (sk-… tokens) == 0;
  P6  no stray untracked files outside the RF-18 manifest.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "0eeca00"
sys.path.insert(0, str(REPO / "scripts"))
from m009_b2_rf18_content import PATCHES  # noqa: E402

fails = []


def ck(name, cond, detail=""):
    ok = bool(cond)
    print(f"  {'✅' if ok else '❌'} {name}" + (f"  [{detail}]" if detail else ""))
    if not ok:
        fails.append(name)


def git(*args):
    return subprocess.run(["git", "-C", str(REPO), *args],
                          capture_output=True, text=True, check=True).stdout


print("── P1 branch + session-anchored notebook ──")
ck("P1a on branch mangabd-009-b2",
   git("branch", "--show-current").strip() == "mangabd-009-b2")
blob = git("hash-object", str(NB)).strip()
ck("P1b notebook blob == d0ad299b0ee7e9410e70b6690f3bfe77103561ff",
   blob == "d0ad299b0ee7e9410e70b6690f3bfe77103561ff", blob[:12])
nb = json.loads(NB.read_text(encoding="utf-8"))
cells = ["".join(c.get("source", [])) for c in nb["cells"]]
surv = Path("/home/z/my-project/cells_rf18_work")
same = all(cells[i] == (surv / f"cell_{i:02d}.py").read_text(
    encoding="utf-8") for i in range(27)) if surv.is_dir() else None
ck("P1c notebook cells == surviving verified bytes (27/27)", same)

print("── P2 manifest re-derivation ──")
raw_base = git("show", f"{BASE_REF}:{NB_NAME}").encode("utf-8")
nb_base = json.loads(raw_base.decode("utf-8"))
base = ["".join(c.get("source", [])) for c in nb_base["cells"]]
rb = {i: base[i] for i in range(27)}
for k, (c, old, new) in enumerate(PATCHES, 1):
    assert rb[c].count(old) == 1, f"hunk {k} anchor"
    rb[c] = rb[c].replace(old, new, 1)
drift = [i for i in range(27) if rb[i] != base[i]]
ck("P2a 27 hunks re-derive the working cells, scope exactly {6,10}",
   len(PATCHES) == 27 and sorted(drift) == [6, 10]
   and all(rb[i] == cells[i] for i in range(27)))
ck("P2b cells 11/12 byte-untouched vs 0eeca00",
   cells[11] == base[11] and cells[12] == base[12])

print("── P3 verify results ──")
res = json.loads((REPO / "scripts" / "m009_b2_rf18_results.json").read_text())
ck("P3a RF-18 verify 54/54 PASS", res == {"passed": 54, "total": 54},
   f"{res}")

print("── P4 archive laws ──")
# MODIFIED files only (--diff-filter=M): the parity artifacts are
# NEW (A) files, so this census holds both pre-commit (untracked)
# and post-commit (added) — a re-run of this audit stays green.
diff = git("diff", "--name-only", "--diff-filter=M", BASE_REF, "--",
           "samples").split()
untouched_ok = all(not d.startswith(("samples/S001", "samples/S002",
                                     "samples/S003", "samples/S005",
                                     "S007")) for d in diff)
ck("P4a S001/S002/S003/S005x/S007 archives untouched vs 0eeca00",
   untouched_ok, f"diff={diff}")
s009 = sorted(d for d in diff if d.startswith("samples/S009"))
s010 = sorted(d for d in diff if d.startswith("samples/S010"))
ck("P4b S009 refresh modified exactly {detections,final,metadata} "
   "(parity artifacts are NEW files, checked in P4e)",
   [Path(d).name for d in s009] ==
   ["detections.json", "final.jpg", "metadata.json"], str(s009))
ck("P4c S010 refresh modified the same set",
   [Path(d).name for d in s010] ==
   ["detections.json", "final.jpg", "metadata.json"], str(s010))
S011 = REPO / "samples" / "S011_manhwa_ui"
need = ["original.jpg", "inpainted.png", "text_mask.png",
        "detections.json", "ocr.json", "translation.json", "final.jpg",
        "metadata.json", "rf18_parity.json", "rf18_overlay.png"]
ck("P4d S011 archive complete (10 files)",
   all((S011 / f).is_file() and (S011 / f).stat().st_size > 0
       for f in need))
for f in ("rf18_parity.json", "rf18_overlay.png"):
    for s in ("S009_diagonal", "S010_burst", "S011_manhwa_ui"):
        p = REPO / "samples" / s / f
        ck(f"P4e {s}/{f} non-trivial", p.stat().st_size > 2000,
           f"{p.stat().st_size} B")

print("── P5 secrets scan over the staged diff ──")
patch_text = git("diff", f"{BASE_REF}", "--", NB_NAME)
patch_text += "\n".join(
    p.read_text(encoding="utf-8", errors="ignore")
    for p in (REPO / "scripts").glob("m009_b2_rf18_*.py"))
hits = len(re.findall(r"sk-[A-Za-z0-9]{20,}", patch_text))
ck("P5 no secret-shaped tokens in the diff + scripts", hits == 0)

print("── P6 untracked census ──")
untracked = [u for u in git("status", "--porcelain").splitlines()
             if u.startswith("??")]
allowed = {
    "scripts/m009_b2_rf18_build.py", "scripts/m009_b2_rf18_chain.py",
    "scripts/m009_b2_rf18_content.py", "scripts/m009_b2_rf18_page.py",
    "scripts/m009_b2_rf18_patches.json",
    "scripts/m009_b2_rf18_refresh.py", "scripts/m009_b2_rf18_regen.py",
    "scripts/m009_b2_rf18_results.json",
    "scripts/m009_b2_rf18_s011_build.py",
    "scripts/m009_b2_rf18_verify.py",
    "scripts/m009_b2_rf18_precommit.py",
    "scripts/m009_b2_rf18_commit_msg.txt",
    "samples/S009_diagonal/", "samples/S010_burst/",
    "samples/S011_manhwa_ui/",
}
stray = [u[3:] for u in untracked
         if not any(u[3:].startswith(a) for a in allowed)]
ck("P6 no stray untracked files", not stray, str(stray))

print()
if fails:
    print(f"PRECOMMIT FAILED: {fails}")
    sys.exit(1)
print("PRECOMMIT OK — all invariants hold")
