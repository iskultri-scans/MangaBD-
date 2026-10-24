#!/usr/bin/env python3
r"""MANGABD-006 B2 — pre-commit audit.

Gates (all must be GREEN before `git commit`):
  P1 scope: staged set == {notebook (M), agents/GLM_5_3.md (M)};
      zero adds, zero deletes
  P2 modes: no executable-bit changes (all staged 100644)
  P3 secret scan on ALL added lines
  P4 AST: staged notebook cells compile 27/27 warnings-as-errors
  P5 base integrity: 21 non-target cells byte-identical to ec4a7f7
      (re-asserted from the staged tree)
  P6 B2 wiring-presence probes on the staged bytes (CONFIG, schema,
      §9b helpers, cell-7 compute + emission, cell-8 sorts + battery,
      cell-22 sites, cell-25 payload + toggle + panel)
  P7 battery integrity: cell-7 test-section markers unchanged vs
      base; cell-8 pre-existing test names all present + 5 new
      M6-B2 tests present; GLM_5_3.md section markers
"""
import json
import re
import subprocess
import sys
import warnings

REPO = "/home/z/my-project/MangaBD"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "ec4a7f7"
TARGET = {1, 3, 7, 8, 22, 25}

PASS = 0
FAIL = 0


def check(name, cond, details=""):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"PASS  {name}")
    else:
        FAIL += 1
        print(f"FAIL  {name}  {details}")


def run(*args):
    return subprocess.run(list(args), capture_output=True, text=True, cwd=REPO)


# P0: stage everything first (audit BEFORE commit, on the staged set)
run("git", "add", "-A")
st = run("git", "diff", "--cached", "--name-status").stdout.strip().splitlines()
print("staged:")
for ln in st:
    print("   ", ln)

added, modified, deleted = set(), set(), set()
for ln in st:
    status, path = ln.split("\t", 1)
    if status.startswith("A"):
        added.add(path)
    elif status.startswith("M"):
        modified.add(path)
    elif status.startswith("D"):
        deleted.add(path)

check("P1a exactly 2 modified tracked files (notebook + GLM_5_3.md)",
      modified == {NB_NAME, "agents/GLM_5_3.md"}, f"modified={sorted(modified)}")
check("P1b zero adds", not added, f"added={sorted(added)}")
check("P1c zero deletions", not deleted, f"deleted={sorted(deleted)}")

# P2: modes
modes = run("git", "diff", "--cached", "--raw").stdout.strip().splitlines()
bad_modes = []
for ln in modes:
    m = re.match(r":(\d{6}) (\d{6}) ", ln)
    if not m:
        bad_modes.append(ln)
        continue
    old_mode, new_mode = m.group(1), m.group(2)
    if new_mode != "100644" or (old_mode != "000000" and old_mode != new_mode):
        bad_modes.append(ln)
check("P2 no file-mode changes (all staged at 100644)", not bad_modes, str(bad_modes[:3]))

# P3: secret scan on added lines
numstat = run("git", "diff", "--cached", "--numstat").stdout.strip().splitlines()
added_text = 0
scanned_text = 0
suspicious = []
PATTERNS = [
    r"ghp_[A-Za-z0-9]{20,}", r"github_pat_[A-Za-z0-9_]{20,}",
    r"sk-[A-Za-z0-9]{20,}", r"hf_[A-Za-z0-9]{20,}", r"AIza[A-Za-z0-9_-]{20,}",
    r"xox[baprs]-[A-Za-z0-9-]{20,}", r"Bearer\s+[A-Za-z0-9._-]{20,}",
    r"(?i)api_key\s*=\s*['\"][A-Za-z0-9]{16,}", r"(?i)password\s*=\s*['\"][^'\"]{6,}",
    r"(?i)secret\s*=\s*['\"][A-Za-z0-9]{12,}",
]
for ln in numstat:
    parts = ln.split("\t")
    if len(parts) != 3:
        continue
    a, d, path = parts
    if a == "-":
        continue
    added_text += int(a)
    diff = run("git", "diff", "--cached", "-U0", "--", path).stdout
    for dline in diff.splitlines():
        if dline.startswith("+") and not dline.startswith("+++"):
            scanned_text += 1
            for pat in PATTERNS:
                if re.search(pat, dline):
                    suspicious.append((path, pat, dline[:100]))
check(f"P3 secret scan: 0 hits on {scanned_text} added lines ({added_text} additions)",
      not suspicious, str(suspicious[:3]))

# P4: AST on the STAGED notebook bytes
nb_staged = run("git", "show", f":{NB_NAME}").stdout
nb = json.loads(nb_staged)
ok_ast = True
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(src, f"staged_cell_{i:02d}.py", "exec")
        except (Warning, SyntaxError) as w:
            ok_ast = False
            print(f"      cell {i}: {w}")
check("P4 staged notebook AST 27/27 warnings-as-errors",
      ok_ast and len(nb["cells"]) == 27)

# P5: 21 non-target cells byte-identical to ec4a7f7 (staged tree)
base_raw = run("git", "show", f"{BASE_REF}:{NB_NAME}").stdout
base_nb = json.loads(base_raw)
drift = [i for i in range(27) if i not in TARGET
         and "".join(nb["cells"][i]["source"]) != "".join(base_nb["cells"][i]["source"])]
check("P5 21 non-target cells byte-identical to ec4a7f7 (staged tree)", not drift,
      f"drift={drift}")

# P6: wiring-presence probes on staged bytes
CELL = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}
probes = [
    ("P6a cell 1 CONFIG reading_order section",
     CELL[1].count('"reading_order": {') == 1
     and '"overlay_note_position": "geometric"' in CELL[1]
     and '"payload_sort": "reading_order"' in CELL[1]),
    ("P6b cell 3 schema tail + §9b",
     '"reading_order",  # MANGABD-006 B2' in CELL[3]
     and CELL[3].count("# 9b. Reading order") == 1
     and "def compute_reading_order" in CELL[3]
     and "def _reading_order_series" in CELL[3]
     and "def ensure_reading_order_column" in CELL[3]
     and "def payload_sort_page_rows" in CELL[3]
     and "def payload_sort_all_rows" in CELL[3]),
    ("P6c cell 3 load + upsert ensure hooks",
     CELL[3].count("ensure_reading_order_column(translation_df)") == 2),
    ("P6d cell 7 build_ocr_row emission + ocr_page compute",
     '"reading_order": int(region.get("reading_order", -1)),  # M6-B2' in CELL[7]
     and "_ro_ids = compute_reading_order(regions)" in CELL[7]
     and 'save_json_artifact(page_id, "detections", regions)' in CELL[7]
     and "📖 Reading order: " in CELL[7]),
    ("P6e cell 8 payload_sort sites (3 sort patches + 3 battery calls)",
     CELL[8].count("payload_sort_page_rows(") == 6),
    ("P6f cell 8 battery tests 26-30",
     all(m in CELL[8] for m in [
         "M6-B2 single-column page", "M6-B2 two-column manga",
         "M6-B2 S003 gate == VLM-confirmed", "M6-B2 overlay_note_position",
         "M6-B2 backward compat"])),
    ("P6g cell 22 payload + display sites",
     "payload_sort_page_rows(" in CELL[22] and "payload_sort_all_rows(" in CELL[22]),
    ("P6h cell 25 payload sort + toggle + panel",
     "payload_sort_page_rows(translation_df[translation_df[\"page\"]==pg])" in CELL[25]
     and "order_sel=widgets.ToggleButtons" in CELL[25]
     and 'MANGABD_CONFIG["reading_order"]["payload_sort"]=order_sel.value' in CELL[25]
     and "scope_sel,order_sel,copy_page_dd" in CELL[25]),
    ("P6i directive sort-by sites all switched (8/1541, 8/1322, 22/301, 25/162)",
     '].sort_values("id")' not in CELL[8]
     and '].sort_values("id")' not in CELL[22]),
]
for name, cond in probes:
    check(name, cond)

# P7: battery integrity
c7_base = "".join(base_nb["cells"][7]["source"])
check("P7a cell-7 self-test section byte-identical to base",
      CELL[7][CELL[7].index("# 8. Self-tests"):] ==
      c7_base[c7_base.index("# 8. Self-tests"):])
c8_pre_names = ["validate_bengali", "clean_translation", "is_special_marker",
                "parse_ai_text (MANGABD-005 B2", "Owner trailing-arrow 6/6 apply (RF-3)",
                "bare [SKIP] marker-skip, never literal (RF-4)", "Live translation test"]
check("P7b cell-8 pre-existing test names all present",
      all(n in CELL[8] for n in c8_pre_names))
check("P7c cell-8 M6-B2 run_test names (5 tests + 1 exception-path)",
      len(re.findall(r'"M6-B2 [^"]+"', CELL[8])) == 6)
glm = run("git", "show", ":agents/GLM_5_3.md").stdout
check("P7d GLM_5_3.md sections (CURRENT PHASE B2 WIP + Batch 2 record + B1 tail intact)",
      "**MANGABD-006 — PHASE C (BATCH 2 / M6-B2) DELIVERED" in glm
      and "# MANGABD-006 — PHASE C (BATCH 2 / M6-B2): READING ORDER" in glm
      and "— End of MANGABD-006 Phase C (Batch 2) record" in glm
      and "has been requested." in glm)

print()
print(f"TOTAL: {PASS} PASS / {FAIL} FAIL")
sys.exit(1 if FAIL else 0)
