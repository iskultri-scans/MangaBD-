#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-10 — pre-commit audit (run AFTER staging, BEFORE commit).

Validates the staged RF-10 set on branch mangabd-008-b1 (HEAD must descend
from the Phase C WIP commit b848c75 AND carry its exact notebook bytes —
docs-only commits in between are allowed, e.g. the Flash Phase D report
33d5183; NO amend of any previous commit): exactly the expected 6 files,
scope {10} only, the fixtures-only proof (cell-10 §1-§9 byte-identical),
re-derivation from the 4-patch manifest, vendored-font pins untouched,
samples/models/S007 + GLM_5_3_FLASH.md + the Phase C instruments
untouched, A/M only 100644, secret scan, docs anchors, and the
m002_sim_v2 = 0 abort-sites gate.
"""
import ast
import hashlib
import json
import re
import subprocess
import sys
import warnings
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
HEAD_REF = "b848c75"
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_CELLS = Path("/home/z/my-project/cells")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"

EXPECTED = {
    ("M", NB_NAME),
    ("M", "agents/GLM_5_3.md"),
    ("A", "scripts/m008_b1_rf10_build.py"),
    ("A", "scripts/m008_b1_rf10_patches.json"),
    ("A", "scripts/m008_b1_rf10_verify.py"),
    ("A", "scripts/m008_b1_rf10_precommit.py"),
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
nb_blob_head = git("rev-parse", f"HEAD:{NB_NAME}").strip()
nb_blob_base = git("rev-parse", f"{HEAD_REF}:{NB_NAME}").strip()
anc = subprocess.run(
    ["git", "-C", str(REPO), "merge-base", "--is-ancestor",
     HEAD_REF, "HEAD"], capture_output=True).returncode == 0
check("P0b HEAD descends from b848c75 and carries its exact notebook "
      "bytes (NO amend; docs-only commits between allowed — e.g. the "
      "Flash Phase D report 33d5183)",
      anc and nb_blob_head == nb_blob_base,
      f"ancestor={anc} blob={nb_blob_head[:12]}")

staged = set()
for ln in git("status", "--porcelain").splitlines():
    if not ln.strip():
        continue
    st, path = ln[:2].strip(), ln[3:].strip().strip('"')
    staged.add((st, path))
check("P0c staged set exactly the 6 expected files", staged == EXPECTED,
      f"extra={sorted(staged - EXPECTED)} missing={sorted(EXPECTED - staged)}")
unstaged = [ln for ln in git("status", "--porcelain").splitlines()
            if ln.strip() and ln[:2] not in ("A ", "M ", "AM") and not ln.startswith("??")]
check("P0d no unstaged/untracked stragglers beyond the staged set", not unstaged,
      str(unstaged))

# P1 — notebook integrity + scope + fixtures-only proof
nb = json.loads((REPO / NB_NAME).read_text(encoding="utf-8"))
cells_post = ["".join(c.get("source", [])) for c in nb["cells"]
              if c.get("cell_type") == "code"]
nb_pre = json.loads(git("show", f"{HEAD_REF}:{NB_NAME}"))
cells_pre = ["".join(c.get("source", [])) for c in nb_pre["cells"]
             if c.get("cell_type") == "code"]
scope = sorted(i for i in range(27) if cells_post[i] != cells_pre[i])
check("P1a notebook scope drift exactly {10} (26 cells byte-identical to b848c75)",
      scope == [10], f"drift={scope}")

marker = "# 10. Self-tests"
check("P1b fixtures-only: cell-10 §1-§9 byte-identical to b848c75",
      cells_pre[10][:cells_pre[10].index(marker)]
      == cells_post[10][:cells_post[10].index(marker)])

batt = cells_post[10][cells_post[10].index(marker):]
check("P1c fixture pattern: 2x registry pin + 2x explicit /tmp missing path, "
      "zero derived MISSING-NotoSansJP.ttf",
      batt.count('MANGABD_ASSETS["fonts"]["fallback_path"]') == 2
      and batt.count("/tmp/MISSING-test-font.ttf") == 2
      and "MISSING-NotoSansJP.ttf" not in cells_post[10])

for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ast.parse(cells_post[i])
check("P1d AST 27/27 (warnings-as-errors)", True)

with open(REPO / "scripts/m008_b1_rf10_patches.json", encoding="utf-8") as f:
    patches = json.load(f)
re_src = dict(enumerate(cells_pre))
for p in patches:
    if re_src[p["cell"]].count(p["old"]) != 1:
        check(f"P1e re-derivation anchor {p['name']}", False)
        break
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
else:
    check("P1e re-derivation: post == b848c75 + the 4 manifest patches",
          all(re_src[i] == cells_post[i] for i in range(27)) and len(patches) == 4)

# P2 — vendored font pins untouched
font = REPO / "assets/fonts/NotoSansJP[wght].ttf"
sha = hashlib.sha256(font.read_bytes()).hexdigest()
check("P2a vendored font sha256 == pin (untouched)", sha == SHA_PIN, sha)
check("P2b vendored font size == 9,589,900", font.stat().st_size == 9589900)
check("P2c cell-4 source byte-identical to b848c75 (registry key `fallback_path`)",
      cells_post[4] == cells_pre[4])

# P3 — protected trees untouched (vs the CURRENT HEAD: the docs-only
# Flash report 33d5183 between b848c75 and here legitimately changed
# GLM_5_3_FLASH.md — RF-10 itself must not)
protected = git("diff", "--name-only", "HEAD", "--", "samples/", "models/",
                "S007_mangabd005_02.zip").strip()
check("P3a samples/models/S007 untouched vs HEAD", not protected, protected)
flash = git("diff", "--name-only", "HEAD", "--",
            "agents/GLM_5_3_FLASH.md").strip()
check("P3b GLM_5_3_FLASH.md untouched by RF-10 (Flash owns it)",
      not flash, flash)
phasc = git("diff", "--name-only", HEAD_REF, "--",
            "scripts/m008_b1_phaseC_build.py", "scripts/m008_b1_phaseC_verify.py",
            "scripts/m008_b1_phaseC_precommit.py",
            "scripts/m008_b1_phaseC_patches.json").strip()
check("P3c Phase C instruments untouched (the committed Phase C record)",
      not phasc, phasc)

# P4 — modes
modes = set()
for ln in git("diff", "--cached", "--name-status").splitlines():
    if ln.strip():
        modes.add((ln.split()[0],))
check("P4 A/M only, 100644, zero deletes/renames",
      all(m in (("A",), ("M",)) for m in modes),
      f"modes={sorted(modes)}")

# P5 — secret scan on the staged text files
added = []
for path in sorted(p for _, p in EXPECTED if not p.endswith(".ttf")):
    p = REPO / path
    if not p.exists() or p.is_dir():
        continue
    added.extend(p.read_text(encoding="utf-8", errors="ignore").splitlines())
joined = "\n".join(added)
hits = [pat for pat in (r"ghp_[A-Za-z0-9]{20,}", r"sk-[A-Za-z0-9]{20,}",
                        r"AIza[A-Za-z0-9\-_]{20,}", r"hf_[A-Za-z0-9]{20,}",
                        r"Bearer\s+[A-Za-z0-9\-_.]{20,}",
                        r"(?i)api_key\s*=\s*['\"][^'\"]{12,}")
        if re.search(pat, joined)]
check("P5 secret scan 0 hits on staged text lines", not hits, str(hits))

# P6 — docs anchors
doc = (REPO / "agents/GLM_5_3.md").read_text(encoding="utf-8")
anchors = [
    "§M8-C7 — RF-10: CELL-10 TEST FIXTURE PATH FIX",
    "MANGABD-008 — B1 RF-10 DELIVERED",
    "scripts/m008_b1_rf10_verify.py",
    "scripts/m008_b1_rf10_patches.json",
    "/tmp/MISSING-test-font.ttf",
    'MANGABD_ASSETS["fonts"]["fallback_path"]',
    "dcfc184fa09128d5126f0c50d5bb7e3bf20bbcfe",
    SHA_PIN,
]
missing = [a for a in anchors if a not in doc]
check("P6 GLM_5_3.md RF-10 record anchors present", not missing, str(missing))

# P7 — m002_sim_v2 abort sites on the post-change cells (cells/ snapshot
# must be the working notebook's cells — freshness assert, then the sim)
fresh = all(
    (SIM_CELLS / f"cell_{i:02d}.py").read_text(encoding="utf-8") == cells_post[i]
    for i in range(27))
check("P7a workspace cells/ snapshot == the working notebook cells", fresh)
sim = subprocess.run(["python3", str(SIM)], capture_output=True, text=True)
m = re.search(r"ABORT-CLASS findings \(unguarded, unresolvable\): (\d+)",
              sim.stdout)
check("P7b m002_sim_v2 = 0 abort sites (post-change cells)",
      sim.returncode == 0 and m is not None and int(m.group(1)) == 0,
      (m.group(1) if m else "parse-fail") + (sim.stderr or "")[-120:])

print("\n" + "=" * 60)
fails = [n for n, ok in results if not ok]
print(f"MANGABD-008 B1 RF-10 PRECOMMIT: {len(results) - len(fails)}/{len(results)} PASS")
if fails:
    for n in fails:
        print("  FAILED: " + n)
    sys.exit(1)
print("ALL GREEN")
