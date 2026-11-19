#!/usr/bin/env python3
"""MANGABD-009 RF-20 — precommit audit (staged-set law)."""
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


# P1 — staged set exactly the RF-20 files
staged = git("diff", "--cached", "--name-status").splitlines()
staged_files = sorted(
    (l.split("\t", 1)[0], l.split("\t", 1)[1])
    for l in staged if l.strip())
expect = sorted(
    [("M", NB_NAME)]
    + [("A", f"scripts/m009_rf20_{n}")
       for n in ("build.py", "content_c10.py", "content_t26.py",
                 "harness.py", "patches.json", "results.json",
                 "s013_build.py", "s013_page.py", "verify.py",
                 "commit_msg.txt", "docs.py", "precommit.py")]
    + [("M", "scripts/m009_b2_rf18_chain.py")]
    + [("M", "agents/GLM_5_3.md")]
    + [("A", f"samples/S013_dark_webtoon/{n}")
       for n in ("detect_mask.png", "detections.json", "final.jpg",
                 "inpainted.png", "metadata.json", "ocr.json",
                 "original.jpg", "rf20_parity.json",
                 "text_mask.png", "translation.json")]
)
p1 = staged_files == expect
print(f"P1 staged set exactly the {len(expect)} RF-20 files: "
      f"{'PASS' if p1 else 'FAIL'}")
if not p1:
    got = set(staged_files)
    want = set(expect)
    print("  extra:", sorted(got - want))
    print("  missing:", sorted(want - got))
    sys.exit(1)

# P2 — worktree clean apart from the staged set (untracked
#      __pycache__ tolerated — regenerable bytecode, never staged)
dirty = [l for l in git("status", "--porcelain").splitlines()
         if l.strip() and not l.startswith("??")]
p2 = len(dirty) == len(staged_files)
print(f"P2 worktree touches exactly the staged set: "
      f"{'PASS' if p2 else 'FAIL'} ({len(dirty)} paths)")
if not p2:
    for l in dirty:
        print("   ", l)
    sys.exit(1)

# P3 — committed archives (the six pre-RF-20) + models byte-untouched
six = ["samples/S001_color_webtoon/", "samples/S002_batch1/",
       "samples/S003_batch2/", "samples/S005_manual/",
       "samples/S005_openrouter/", "samples/S009_diagonal/",
       "samples/S010_burst/", "samples/S011_manhwa_ui/",
       "samples/S012_manhwa_emphasis/", "models/"]
diffstat = git("diff", "--cached", "--stat", "--", *six).strip()
p3 = diffstat == ""
print(f"P3 prior archives (S001-S012) + models untouched: "
      f"{'PASS' if p3 else 'FAIL'}")
if not p3:
    print("  ", diffstat)

# P4 — notebook: changed cells exactly {10} vs HEAD (7d0a58e)
nb_new = json.loads(git("show", f":{NB_NAME}"))
nb_old = json.loads(git("show", f"HEAD:{NB_NAME}"))
changed = sorted(
    i for i in range(27)
    if "".join(nb_new["cells"][i]["source"])
    != "".join(nb_old["cells"][i]["source"]))
p4 = changed == [10]
print(f"P4 notebook cell drift EXACTLY {{10}}: "
      f"{'PASS' if p4 else 'FAIL'} {changed}")

# P5 — the manifest re-derives HEAD->staged byte-exact (application order)
patches = json.loads(
    open(f"{REPO}/scripts/m009_rf20_patches.json",
         encoding="utf-8").read())
src = {i: "".join(c["source"]) for i, c in
       enumerate(nb_old["cells"])}
ok5 = len(patches) == 9
for p in patches:                     # sequential application order
    if src[p["cell"]].count(p["old"]) != 1:
        ok5 = False
        print(f"  anchor not unique pre-apply: {p['name']}")
        break
    src[p["cell"]] = src[p["cell"]].replace(p["old"], p["new"])
else:
    ok5 = ok5 and all(
        "".join(nb_new["cells"][i]["source"]) == src[i]
        for i in range(27))
p5 = ok5
print(f"P5 manifest (9 patches, ordered) re-derives HEAD->staged "
      f"byte-exact: {'PASS' if p5 else 'FAIL'}")

# P6 — results JSON: 37/37
res = json.load(open(f"{REPO}/scripts/m009_rf20_results.json",
                     encoding="utf-8"))
p6 = (res["summary"]["pass"] == 37 and res["summary"]["fail"] == 0
      and res["summary"]["test26_arms"] == 7)
print(f"P6 verify results 37/37 ALL GREEN + 7 Test-26 markers: "
      f"{'PASS' if p6 else 'FAIL'} ({res['summary']['pass']}/"
      f"{res['summary']['pass'] + res['summary']['fail']})")

# P7 — GLM_5_3.md anchors: new entries unique, prior records intact
doc = open(f"{REPO}/agents/GLM_5_3.md", encoding="utf-8").read()
checks = {
    "header_rf20": doc.count(
        "MANGABD-009 — RF-20 DELIVERED: WHOLE+FRAGMENT CONTAINMENT "
        "DEDUP") == 1,
    "section_rf20": doc.count(
        "# MANGABD-009 — RF-20: WHOLE+FRAGMENT CONTAINMENT DEDUP + "
        "DARK-WEBTOON GHOST WIPE") == 1,
    "r0": doc.count("## M9-RF20.0 Ruling disposition") == 1,
    "r1": doc.count("## M9-RF20.1 Implementation") == 1,
    "r2": doc.count("## M9-RF20.2 Verification") == 1,
    "r3": doc.count("## M9-RF20.3 Disclosures") == 1,
    "r4": doc.count("## M9-RF20.4 Instruments and custody") == 1,
    "r5": doc.count("## M9-RF20.5 Next") == 1,
    "rf19_intact": doc.count(
        "# MANGABD-009 — RF-19: FALSE-TILT BAND-CONSISTENCY GATE + "
        "PRODUCTION TINY-GUARD") == 1,
    "b3m_intact": doc.count(
        "MANGABD-009 — B3+B3.1+RF-19 MERGE COMPLETION RECORD") >= 1,
    "cp_intact": doc.count("## CURRENT PHASE") == 1,
    "s013_named": doc.count("S013_dark_webtoon") >= 3,
    "pairs_named": doc.count("(4,5)(7,8)(16,17)(20,21)") >= 1
                    or doc.count("(4,5),(7,8),(16,17),(20,21)")
                    >= 1,
    "containment_law": doc.count("centroid") >= 3,
    "zero_suppression": doc.count("ZERO suppression") >= 1,
}
p7 = all(checks.values())
print(f"P7 GLM anchors: {'PASS' if p7 else 'FAIL'} "
      f"{[k for k, v in checks.items() if not v]}")

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

# P9 — commit-time state: on the branch, parent == 7d0a58e (merged
#      main tip — RF-20 is a fresh fast round on main, no hold)
head = git("rev-parse", "--short", "HEAD").strip()
branch = git("branch", "--show-current").strip()
p9 = (head == "7d0a58e" and branch == "mangabd-009-rf20")
print(f"P9 commit-time state (HEAD==7d0a58e on mangabd-009-rf20): "
      f"{'PASS' if p9 else 'FAIL'} (head={head}, branch={branch})")

ok = all([p1, p2, p3, p4, p5, p6, p7, p8, p9])
print(f"\nRF-20 PRECOMMIT: {'ALL GREEN (9/9)' if ok else 'FAILED'}")
sys.exit(0 if ok else 1)
