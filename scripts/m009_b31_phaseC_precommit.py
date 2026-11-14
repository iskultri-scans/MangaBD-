#!/usr/bin/env python3
"""MANGABD-009 B3.1 Phase C — precommit audit (staged-set law)."""
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


# P1 — staged set exactly the Phase C files
staged = git("diff", "--cached", "--name-status").splitlines()
staged_files = sorted(
    (l.split("\t", 1)[0], l.split("\t", 1)[1])
    for l in staged if l.strip())
expect = sorted(
    [("M", NB_NAME), ("M", "agents/GLM_5_3.md")]
    + [("A", f"scripts/m009_b31_phaseC_{n}")
       for n in ("build.py", "content_c10.py", "content_c1112.py",
                 "content_c6.py", "content_t24.py", "harness.py",
                 "patches.json", "precommit.py", "results.json",
                 "verify.py")]
    + [("A", "scripts/m009_b31_s012_build.py"),
       ("A", "scripts/m009_b31_s012_page.py")]
    + [("A", f"samples/S012_manhwa_emphasis/{n}")
       for n in ("b31_parity.json", "detections.json", "final.jpg",
                 "inpainted.png", "metadata.json", "ocr.json",
                 "original.jpg", "text_mask.png", "translation.json")]
)
p1 = staged_files == expect
print(f"P1 staged set exactly the 23 Phase C files: "
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

# P3 — samples/models + the five archives byte-untouched vs HEAD
p3 = (git("diff", "--cached", "--stat", "--", "models/",
          "samples/S003_batch2/", "samples/S009_diagonal/",
          "samples/S010_burst/", "samples/S011_manhwa_ui/").strip()
      == "" and "S007" not in git(
          "diff", "--cached", "--name-only"))
print(f"P3 models + the five committed archives untouched: "
      f"{'PASS' if p3 else 'FAIL'}")

# P4 — notebook: changed cells exactly {6,10,11,12} vs HEAD (cf01aef)
nb_new = json.loads(git("show", f":{NB_NAME}"))
nb_old = json.loads(git("show", f"HEAD:{NB_NAME}"))
changed = sorted(
    i for i in range(27)
    if "".join(nb_new["cells"][i]["source"])
    != "".join(nb_old["cells"][i]["source"]))
p4 = changed == [6, 10, 11, 12]
print(f"P4 notebook cell drift EXACTLY {{6,10,11,12}}: "
      f"{'PASS' if p4 else 'FAIL'} {changed}")

# P5 — the manifest re-derives HEAD->staged byte-exact
patches = json.loads((REPO + "/scripts/m009_b31_phaseC_patches.json")
                     .encode() and open(
    f"{REPO}/scripts/m009_b31_phaseC_patches.json",
    encoding="utf-8").read())
src = {i: "".join(c["source"]) for i, c in
       enumerate(nb_old["cells"])}
ok5 = len(patches) == 20
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
print(f"P5 manifest (20 patches) re-derives HEAD->staged "
      f"byte-exact: {'PASS' if p5 else 'FAIL'}")

# P6 — S012 archive: law-vs-GT 8/8 + the detections carry the keys
s012 = json.load(open(f"{REPO}/samples/S012_manhwa_emphasis/"
                      "b31_parity.json", encoding="utf-8"))
n_ok = sum(1 for e in s012["regions"] if e["pass"])
det = json.load(open(f"{REPO}/samples/S012_manhwa_emphasis/"
                     "detections.json", encoding="utf-8"))
det_rows = det if isinstance(det, list) else det.get("regions", [])
n_keys = sum(1 for d in det_rows if "line_colors" in d)
r1 = next(d for d in det_rows if d.get("id") == 1)
p6 = (n_ok == 8 == len(s012["regions"]) and n_keys == 3
      and r1.get("line_colors") == [None, [200, 30, 30],
                                    None, [30, 30, 180]])
print(f"P6 S012: 8/8 law-vs-GT, 3 line_colors keys in detections "
      f"(R1/R2/R5), R1 == the owner-case ledger: "
      f"{'PASS' if p6 else 'FAIL'} (keys={n_keys})")

# P7 — GLM_5_3.md anchors: new entries unique, prior records intact
doc = open(f"{REPO}/agents/GLM_5_3.md", encoding="utf-8").read()
checks = {
    "header_b31c": doc.count(
        "MANGABD-009 — B3.1 PHASE C DELIVERED") == 1,
    "section_b31c": doc.count(
        "# MANGABD-009 — PHASE C (B3.1):") == 1,
    "c0_ruling": doc.count("## M9-B31C.0 Ruling disposition") == 1,
    "c1_impl": doc.count("## M9-B31C.1 Implementation") == 1,
    "c2_verify": doc.count("## M9-B31C.2 Verification") == 1,
    "c3_disclose": doc.count("## M9-B31C.3 Disclosures") == 1,
    "c4_custody": doc.count("## M9-B31C.4 Instruments") == 1,
    "c5_next": doc.count("## M9-B31C.5 Next") == 1,
    "b3c_intact": doc.count("# MANGABD-009 — PHASE C (B3):") == 1,
    "b3a_intact": doc.count("# MANGABD-009 — PHASE A (B3)") == 1,
    "b21_intact": doc.count(
        "MANGABD-009 — B2.1 CLOSED: SQUASH-MERGED TO MAIN") >= 1,
    "hold_intact": doc.count("B3 merge ON HOLD") >= 2,
    "tau_015": doc.count("τ=0.15") + doc.count("τ = 0.15") >= 2,
    "narrow_80": doc.count("w<80") + doc.count("w < 80") >= 3,
    "guard_2000": doc.count("2000px") >= 2,
    "s012_named": doc.count("S012_manhwa_emphasis") >= 3,
    "v5_confirmed": doc.count("V5 CONFIRMED") >= 1,
}
p7 = all(checks.values())
print(f"P7 GLM anchors: {'PASS' if p7 else 'FAIL'} {checks}")

# P8 — results JSON: 49/49
res = json.load(open(f"{REPO}/scripts/m009_b31_phaseC_results.json",
                     encoding="utf-8"))
p8 = (res["summary"]["pass"] == 49 and res["summary"]["fail"] == 0)
print(f"P8 verify results 49/49 ALL GREEN: "
      f"{'PASS' if p8 else 'FAIL'} ({res['summary']})")

# P9 — secret scan on all added lines (notebook + scripts + docs)
diff = git("diff", "--cached", "-U0")
added = "\n".join(ln[1:] for ln in diff.splitlines()
                  if ln.startswith("+") and not ln.startswith("+++"))
pats = [r"github_pat_[A-Za-z0-9]{20,}", r"ghp_[A-Za-z0-9]{30,}",
        r"sk-[A-Za-z0-9]{20,}", r"AIza[A-Za-z0-9_-]{30,}",
        r"xox[baprs]-[A-Za-z0-9-]{10,}",
        r"-----BEGIN [A-Z ]*PRIVATE KEY"]
hits = [p for p in pats if re.search(p, added)]
p9 = not hits
print(f"P9 secret scan on added lines: "
      f"{'PASS' if p9 else 'FAIL'} {hits}")

# P10 — commit-time state: on the branch, parent == cf01aef,
#       B3 hold intact (cf01aef not on main)
head = git("rev-parse", "--short", "HEAD").strip()
branch = git("branch", "--show-current").strip()
hold = subprocess.run(
    ["git", "-C", REPO, "merge-base", "is-ancestor",
     "cf01aef", "main"], capture_output=True).returncode != 0
p10 = (head == "cf01aef" and branch == "mangabd-009-b3"
       and hold)
print(f"P10 commit-time state (HEAD==cf01aef on mangabd-009-b3, "
      f"B3 hold intact — the commit will parent onto cf01aef): "
      f"{'PASS' if p10 else 'FAIL'} (head={head}, branch={branch}, "
      f"hold={hold})")

ok = all([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10])
print(f"\nB3.1 PHASE C PRECOMMIT: "
      f"{'ALL GREEN (10/10)' if ok else 'FAILED'}")
sys.exit(0 if ok else 1)
