#!/usr/bin/env python3
r"""MANGABD-008 B1 RF-11 — pre-commit audit (run AFTER staging, BEFORE commit).

Validates the staged RF-11 set on branch mangabd-008-b1 (HEAD must be the
Flash RF-10 delta report b627686 which descends from 9b232f0 AND carries
its exact notebook bytes — NO amend of any previous commit): exactly the
expected 6 files, scope {4, 10} only, the fixtures-only proof (cell-10
§1-§9 byte-identical) AND the loader-only proof (cell-4 delta confined to
§8.5), re-derivation from the 6-patch manifest, vendored-font pins
untouched, samples/models/S007 + GLM_5_3_FLASH.md + the Phase C and
RF-10 instruments untouched, A/M only 100644, secret scan, docs anchors,
and the m002_sim_v2 = 0 abort-sites gate.
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
HEAD_REF = "9b232f0"
SIM = Path("/home/z/my-project/scripts/fresh_run_sim2.py")
SIM_CELLS = Path("/home/z/my-project/cells")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"

EXPECTED = {
    ("M", NB_NAME),
    ("M", "agents/GLM_5_3.md"),
    ("A", "scripts/m008_b1_rf11_build.py"),
    ("A", "scripts/m008_b1_rf11_patches.json"),
    ("A", "scripts/m008_b1_rf11_verify.py"),
    ("A", "scripts/m008_b1_rf11_precommit.py"),
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
nb_blob_head = git("rev-parse", f"HEAD:{NB_NAME}").strip()
nb_blob_base = git("rev-parse", f"{HEAD_REF}:{NB_NAME}").strip()
anc = subprocess.run(
    ["git", "-C", str(REPO), "merge-base", "--is-ancestor",
     HEAD_REF, "HEAD"], capture_output=True).returncode == 0
check("P0b HEAD == the Flash RF-10 delta report b627686 which descends "
      "from 9b232f0 and carries its exact notebook bytes (NO amend; "
      "docs-only commits between allowed)",
      head.startswith("b627686") and anc and nb_blob_head == nb_blob_base,
      f"head={head[:12]} ancestor={anc} blob={nb_blob_head[:12]}")

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

# P1 — notebook integrity + scope + fixtures-only + loader-only proofs
nb = json.loads((REPO / NB_NAME).read_text(encoding="utf-8"))
cells_post = ["".join(c.get("source", [])) for c in nb["cells"]
              if c.get("cell_type") == "code"]
nb_pre = json.loads(git("show", f"{HEAD_REF}:{NB_NAME}"))
cells_pre = ["".join(c.get("source", [])) for c in nb_pre["cells"]
             if c.get("cell_type") == "code"]
scope = sorted(i for i in range(27) if cells_post[i] != cells_pre[i])
check("P1a notebook scope drift exactly {4, 10} (25 cells byte-identical "
      "to 9b232f0)", scope == [4, 10], f"drift={scope}")

marker = "# 10. Self-tests"
check("P1b fixtures-only: cell-10 §1-§9 byte-identical to 9b232f0",
      cells_pre[10][:cells_pre[10].index(marker)]
      == cells_post[10][:cells_post[10].index(marker)])

s85 = "# 8.5 Japanese fallback font"
cfg_line = 'MANGABD_CONFIG["rendering"]["font_fallback"] = str(fallback_font_path)'
b_pre = cells_pre[4][:cells_pre[4].rindex("\n# ═", 0, cells_pre[4].index(s85)) + 1]
n_pre = cells_post[4][:cells_post[4].rindex("\n# ═", 0, cells_post[4].index(s85)) + 1]
b_post = cells_pre[4][cells_pre[4].index(cfg_line):]
n_post = cells_post[4][cells_post[4].index(cfg_line):]
check("P1c loader-only: cell-4 delta confined to §8.5 (pre-§8.5 + "
      "post-§8.5 byte-identical to 9b232f0)", b_pre == n_pre and b_post == n_post)

batt = cells_post[10][cells_post[10].index(marker):]
b4 = cells_post[4]
check("P1d fixture pattern: run_test_skip + 2 skip branches (Tests 9/12) + "
      "shared fixture + RF-10 asserts gone + Tests 10/11 explicit missing "
      "path kept + tests_total arithmetic",
      batt.count("def run_test_skip") == 1
      and batt.count("if not _vendored_jp_present:") == 3
      and batt.count("assert Path(real_jp_path).exists()") == 0
      and batt.count("/tmp/MISSING-test-font.ttf") == 2
      and batt.count("assert not Path(missing_path).exists()") == 2
      and "tests_total=len(tests) + tests_skipped" in batt
      and "tests_skipped=tests_skipped" in batt)
check("P1e loader pattern: helper trio + ensure called BEFORE the scan + "
      "both sha-pinned URLs + registry/MANGABD_ASSETS block byte-identical",
      b4.count("def _ensure_vendored_font") == 1
      and b4.count("def _find_repo_vendored_font") == 1
      and b4.count("def _download_vendored_font") == 1
      and b4.index("_ensure_vendored_font()\n\nfallback_font_path = None")
          < b4.index("for _fb_cand in")
      and b4.count("https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf") == 1
      and b4.count("https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/notosansjp/NotoSansJP%5Bwght%5D.ttf") == 1
      and b4[b4.index("MANGABD_ASSETS = {"):]
          == cells_pre[4][cells_pre[4].index("MANGABD_ASSETS = {"):])

for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        ast.parse(cells_post[i])
check("P1f AST 27/27 (warnings-as-errors)", True)

with open(REPO / "scripts/m008_b1_rf11_patches.json", encoding="utf-8") as f:
    patches = json.load(f)
re_src = dict(enumerate(cells_pre))
for p in patches:
    if re_src[p["cell"]].count(p["old"]) != 1:
        check(f"P1g re-derivation anchor {p['name']}", False)
        break
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
else:
    check("P1g re-derivation: post == 9b232f0 + the 6 manifest patches",
          all(re_src[i] == cells_post[i] for i in range(27)) and len(patches) == 6)

# P2 — vendored font pins untouched
font = REPO / "assets/fonts/NotoSansJP[wght].ttf"
sha = hashlib.sha256(font.read_bytes()).hexdigest()
check("P2a vendored font sha256 == pin (untouched)", sha == SHA_PIN, sha)
check("P2b vendored font size == 9,589,900", font.stat().st_size == 9589900)
license_ = REPO / "assets/fonts/OFL-NotoSansJP.txt"
check("P2c OFL license file untouched vs 9b232f0",
      git("diff", "--name-only", HEAD_REF, "--",
          "assets/fonts/OFL-NotoSansJP.txt").strip() == "")

# P3 — protected trees untouched (vs the CURRENT HEAD b627686: the Flash
# delta report between 9b232f0 and here legitimately changed
# GLM_5_3_FLASH.md — RF-11 itself must not)
protected = git("diff", "--name-only", "HEAD", "--", "samples/", "models/",
                "S007_mangabd005_02.zip").strip()
check("P3a samples/models/S007 untouched vs HEAD", not protected, protected)
flash = git("diff", "--name-only", "HEAD", "--",
            "agents/GLM_5_3_FLASH.md").strip()
check("P3b GLM_5_3_FLASH.md untouched by RF-11 (Flash owns it)",
      not flash, flash)
instr = git("diff", "--name-only", HEAD_REF, "--",
            "scripts/m008_b1_phaseC_build.py", "scripts/m008_b1_phaseC_verify.py",
            "scripts/m008_b1_phaseC_precommit.py",
            "scripts/m008_b1_phaseC_patches.json",
            "scripts/m008_b1_rf10_build.py", "scripts/m008_b1_rf10_verify.py",
            "scripts/m008_b1_rf10_precommit.py",
            "scripts/m008_b1_rf10_patches.json",
            "scripts/m008_rf10_forensic.py").strip()
check("P3c Phase C + RF-10 instruments untouched (the committed records)",
      not instr, instr)

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
    "§M8-C8 — RF-11: VENDORED-FONT GRACEFUL SKIP + AUTO-DOWNLOAD SELF-HEAL",
    "MANGABD-008 — B1 RF-11 DELIVERED",
    "scripts/m008_b1_rf11_verify.py",
    "scripts/m008_b1_rf11_patches.json",
    "_ensure_vendored_font",
    "run_test_skip",
    "FONT_FALLBACK_URLS",
    "10 passed + 2 skipped = 12",
    "b627686",
    "9b232f0",
    SHA_PIN,
    "§M8-C7 — RF-10: CELL-10 TEST FIXTURE PATH FIX",
]
missing = [a for a in anchors if a not in doc]
check("P6 GLM_5_3.md RF-11 record anchors present (prior records intact)",
      not missing, str(missing))

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
print(f"MANGABD-008 B1 RF-11 PRECOMMIT: {len(results) - len(fails)}/{len(results)} PASS")
if fails:
    for n in fails:
        print("  FAILED: " + n)
    sys.exit(1)
print("ALL GREEN")
