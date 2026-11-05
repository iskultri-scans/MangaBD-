#!/usr/bin/env python3
"""MANGABD-009 B2 RF-17 — regenerate the patch content module from the
actual notebook-vs-base diff (context 3 lines), so the manifest always
matches reality. Then verify round-trip: base + patches == current.
"""
import difflib
import hashlib
import json
import subprocess
import sys

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "57ac480"
CTX = 3

cur = json.loads(open(NB, encoding="utf-8").read())
cur_cells = ["".join(c.get("source", [])) for c in cur["cells"]]
base_raw = subprocess.run(["git", "-C", REPO, "show", f"{BASE_REF}:{NB_NAME}"],
                          capture_output=True, check=True).stdout
base = json.loads(base_raw.decode("utf-8"))
base_cells = ["".join(c.get("source", [])) for c in base["cells"]]

patches = []
for cell in (6, 10):
    a = base_cells[cell].splitlines(keepends=True)
    b = cur_cells[cell].splitlines(keepends=True)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    ops = [o for o in sm.get_opcodes() if o[0] != "equal"]
    # merge nearby hunks (gap <= 2*CTX) so contexts don't tangle
    merged = []
    for tag, i1, i2, j1, j2 in ops:
        if merged and i1 - merged[-1][2] <= 2 * CTX:
            mt, mi1, mi2, mj1, mj2 = merged[-1]
            merged[-1] = (mt, mi1, max(mi2, i2), mj1, max(mj2, j2))
        else:
            merged.append((tag, i1, i2, j1, j2))
    for k, (tag, i1, i2, j1, j2) in enumerate(merged, 1):
        lo_a = max(0, i1 - CTX)
        hi_a = min(len(a), i2 + CTX)
        lo_b = max(0, j1 - CTX)
        hi_b = min(len(b), j2 + CTX)
        old = "".join(a[lo_a:hi_a])
        new = "".join(b[lo_b:hi_b])
        patches.append({
            "cell": cell,
            "name": f"cell{cell} hunk{k} ({tag} base[{i1}:{i2}])",
            "old": old, "new": new,
        })

print(f"{len(patches)} patches:")
for p in patches:
    print(f"  [{p['cell']}] {p['name']}: old {len(p['old'])}B -> new {len(p['new'])}B")

# round-trip check: base + patches == current?
rebuilt = list(base_cells)
for p in patches:
    src = rebuilt[p["cell"]]
    assert src.count(p["old"]) == 1, f"not unique: {p['name']}"
    rebuilt[p["cell"]] = src.replace(p["old"], p["new"], 1)
ok = all(rebuilt[i] == cur_cells[i] for i in range(len(cur_cells)))
print("round-trip (base + patches == current):", "OK" if ok else "FAIL")
assert ok

# emit the content module
def pystr(s):
    return "    " + repr(s).replace("\\'", "'") if False else None

out = ['#!/usr/bin/env python3',
       '"""MANGABD-009 B2 RF-17 — patch content (REGENERATED from the',
       '57ac480 -> working-tree diff; scripts/m009_b2_rf17_regen.py is the',
       'generator — edit patches via the notebook + regen, never by hand).',
       '',
       'Cells touched: {6, 10} ONLY (RF-17 scope).',
       '"""',
       '']
names = []
for i, p in enumerate(patches, 1):
    const = f"P{i:02d}"
    names.append(const)
    out.append(f"# {'='*66}")
    out.append(f"# {p['name']}")
    out.append(f"{const}_CELL = {p['cell']}")
    out.append(f"{const}_OLD = {p['old']!r}")
    out.append("")
    out.append(f"{const}_NEW = {p['new']!r}")
    out.append("")
out.append("")
out.append("PATCHES = [")
for const in names:
    out.append(f"    ({const}_CELL, {const}_OLD, {const}_NEW),")
out.append("]")
out.append("")

path = f"{REPO}/scripts/m009_b2_rf17_content.py"
open(path, "w", encoding="utf-8").write("\n".join(out))
print(f"content module -> {path}")
print("sha256(new content):", hashlib.sha256(
    open(path, 'rb').read()).hexdigest()[:16])
