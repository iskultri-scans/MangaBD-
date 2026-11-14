#!/usr/bin/env python3
"""MANGABD-009 RF-19 — precommit audit (staged-set law)."""
import json
import re
import subprocess
import sys

REPO = "/home/z/my-project/MangaBD"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"


def git(*a):
    return subprocess.run(
        ["git", "-C", REPO] + list(a), capture_output=True,
        text=True, check=True).stdout


# P1 — staged set exactly the RF-19 files
staged = git("diff", "--cached", "--name-status").splitlines()
staged_files = sorted(
    (l.split("\t", 1)[0], l.split("\t", 1)[1])
    for l in staged if l.strip())
expect = sorted(
    [("M", NB_NAME), ("M", "agents/GLM_5_3.md")]
    + [("A", f"scripts/m009_rf19_{n}")
       for n in ("build.py", "commit_msg.txt", "content_c10.py",
                 "content_c6.py", "content_t25.py", "design.py",
                 "harness.py", "patches.json", "precommit.py",
                 "results.json", "verify.py")]
)
p1 = staged_files == expect
print(f"P1 staged set exactly the 13 RF-19 files: "
      f"{'PASS' if p1 else 'FAIL'}")
if not p1:
    got = set(staged_files)
    want = set(expect)
    print("  extra:", sorted(got - want))
    print("  missing:", sorted(want - got))
    sys.exit(1)

# P2 — worktree clean apart from the staged set
dirty = [l for l in git("status", "--porcelain").splitlines()
         if l.strip()]
p2 = len(dirty) == len(staged_files)
print(f"P2 worktree touches exactly the staged set: "
      f"{'PASS' if p2 else 'FAIL'} ({len(dirty)} paths)")

# P3 — samples/models + all committed archives byte-untouched vs HEAD
p3 = (git("diff", "--cached", "--stat", "--", "models/", "samples/")
      .strip() == "")
print(f"P3 models + samples (all six archives incl. S012) untouched: "
      f"{'PASS' if p3 else 'FAIL'}")

# P4 — notebook: changed cells exactly {6,10} vs HEAD (36faa98)
nb_new = json.loads(git("show", f":{NB_NAME}"))
nb_old = json.loads(git("show", f"HEAD:{NB_NAME}"))
changed = sorted(
    i for i in range(27)
    if "".join(nb_new["cells"][i]["source"])
    != "".join(nb_old["cells"][i]["source"]))
p4 = changed == [6, 10]
print(f"P4 notebook cell drift EXACTLY {{6,10}}: "
      f"{'PASS' if p4 else 'FAIL'} {changed}")

# P5 — the manifest re-derives HEAD->staged byte-exact
patches = json.loads(
    open(f"{REPO}/scripts/m009_rf19_patches.json",
         encoding="utf-8").read())
src = {i: "".join(c["source"]) for i, c in
       enumerate(nb_old["cells"])}
ok5 = len(patches) == 8
for p in patches:
    if src[p["cell"]].count(p["old"]) != 1:
        ok5 = False
        break
    src[p["cell"]] = src[p["cell"]].replace(p["old"], p["new"])
else:
    ok5 = ok5 and all(
        "".join(nb_new["cells"][i]["source"]) == src[i]
        for i in range(27))
p5 = ok5
print(f"P5 manifest (8 patches) re-derives HEAD->staged "
      f"byte-exact: {'PASS' if p5 else 'FAIL'}")

# P6 — results JSON: 39/39
res = json.load(open(f"{REPO}/scripts/m009_rf19_results.json",
                     encoding="utf-8"))
p6 = (res["summary"]["pass"] == 39 and res["summary"]["fail"] == 0
      and res["summary"]["test25_arms"] == 6)
print(f"P6 verify results 39/39 ALL GREEN + 6 Test-25 arms: "
      f"{'PASS' if p6 else 'FAIL'} ({res['summary']})")

# P7 — GLM_5_3.md anchors: new entries unique, prior records intact
doc = open(f"{REPO}/agents/GLM_5_3.md", encoding="utf-8").read()
checks = {
    "header_rf19": doc.count(
        "MANGABD-009 — RF-19 DELIVERED: FALSE-TILT BAND-CONSISTENCY "
        "GATE") == 1,
    "section_rf19": doc.count(
        "# MANGABD-009 — RF-19: FALSE-TILT BAND-CONSISTENCY GATE + "
        "PRODUCTION TINY-GUARD") == 1,
    "r0": doc.count("## M9-RF19.0 Ruling disposition") == 1,
    "r1": doc.count("## M9-RF19.1 Implementation") == 1,
    "r2": doc.count("## M9-RF19.2 Verification") == 1,
    "r3": doc.count("## M9-RF19.3 Disclosures") == 1,
    "r4": doc.count("## M9-RF19.4 Instruments and custody") == 1,
    "r5": doc.count("## M9-RF19.5 Next") == 1,
    "b31c_intact": doc.count(
        "# MANGABD-009 — PHASE C (B3.1):") == 1,
    "b31_header_intact": doc.count(
        "MANGABD-009 — B3.1 PHASE C DELIVERED") == 1,
    "b3c_intact": doc.count("# MANGABD-009 — PHASE C (B3):") == 1,
    "b21_intact": doc.count(
        "MANGABD-009 — B2.1 CLOSED: SQUASH-MERGED TO MAIN") >= 1,
    "hold_intact": doc.count("B3 merge ON HOLD") >= 3,
    "band_gate_2deg": doc.count("≤ 2°") + doc.count("≤2°") >= 2,
    "guard_2000": doc.count("2000px") >= 3,
    "census_named": doc.count("fire census") >= 4,
    "out_of_scope": doc.count("manual paste") >= 2,
}
p7 = all(checks.values())
print(f"P7 GLM anchors: {'PASS' if p7 else 'FAIL'} {checks}")

# P8 — secret scan on all added lines (notebook + scripts + docs)
diff = git("diff", "--cached", "-U0")
added = "\n".join(ln[1:] for ln in diff.splitlines()
                  if ln.startswith("+") and not ln.startswith("+++"))
pats = [r"github_pat_[A-Za-z0-9]{20,}", r"ghp_[A-Za-z0-9]{30,}",
        r"sk-[A-Za-z0-9]{20,}", r"AIza[A-Za-z0-9_-]{30,}",
        r"xox[baprs]-[A-Za-z0-9-]{10,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY"]
hits = [p for p in pats if re.search(p, added)]
p8 = not hits
print(f"P8 secret scan on added lines: "
      f"{'PASS' if p8 else 'FAIL'} {hits}")

# P9 — commit-time state: on the branch, parent == 36faa98,
#       B3 hold intact (neither 36faa98 nor cf01aef on main)
head = git("rev-parse", "--short", "HEAD").strip()
branch = git("branch", "--show-current").strip()
holds = all(
    subprocess.run(
        ["git", "-C", REPO, "merge-base", "is-ancestor", ref,
         "main"], capture_output=True).returncode != 0
    for ref in ("36faa98", "cf01aef"))
p9 = (head == "36faa98" and branch == "mangabd-009-b3" and holds)
print(f"P9 commit-time state (HEAD==36faa98 on mangabd-009-b3, "
      f"B3 hold intact — the commit will parent onto 36faa98): "
      f"{'PASS' if p9 else 'FAIL'} (head={head}, branch={branch}, "
      f"holds={holds})")

ok = all([p1, p2, p3, p4, p5, p6, p7, p8, p9])
print(f"\nRF-19 PRECOMMIT: {'ALL GREEN (9/9)' if ok else 'FAILED'}")
sys.exit(0 if ok else 1)
