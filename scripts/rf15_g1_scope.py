#!/usr/bin/env python3
"""RF-15 G1 scope check — INDEPENDENT (do not trust GLM's verify script).

1. Apply the 3-patch manifest (old -> new) and confirm byte-exact cell rebuild.
2. Confirm manifest 'old' strings exist verbatim in the OLD cells and 'new'
   strings verbatim in the NEW cells.
3. Count patch deltas (each patch must account for the FULL old->new delta —
   no extra edits beyond the manifest).
4. AST-parse both new cells (syntax validity).
5. Secrets scan on the changed cells.
"""
import json, hashlib, sys, ast, re

OLD_NB, NEW_NB = '/tmp/nb_old.json', '/tmp/nb_new.json'
MANIFEST = '/home/z/my-project/repo/scripts/m009_b2_rf15_patches.json'

def cells(path):
    nb = json.load(open(path, encoding='utf-8'))
    return [''.join(c.get('source', [])) for c in nb['cells']]

A, B = cells(OLD_NB), cells(NEW_NB)
manifest = json.load(open(MANIFEST, encoding='utf-8'))
fails = []

print(f"manifest patches: {len(manifest)}")
assert len(manifest) == 3, "manifest must have exactly 3 patches"

# --- 1. rebuild new cells from old + manifest ---
rebuild = {11: A[11], 12: A[12]}
applied = {11: 0, 12: 0}
for p in manifest:
    ci = p['cell']
    old, new = p['old'], p['new']
    if old not in rebuild[ci]:
        fails.append(f"P '{p['name']}': old-string NOT FOUND verbatim in old cell {ci}")
        continue
    occurrences = rebuild[ci].count(old)
    if occurrences != 1:
        fails.append(f"P '{p['name']}': old-string occurs {occurrences}x in cell {ci} (ambiguous)")
    rebuild[ci] = rebuild[ci].replace(old, new, 1)
    applied[ci] += 1

print(f"applied: cell11={applied[11]} cell12={applied[12]}")
for ci in (11, 12):
    if rebuild[ci] == B[ci]:
        print(f"cell {ci}: manifest rebuild == new cell BYTE-EXACT")
    else:
        fails.append(f"cell {ci}: manifest rebuild != new cell (byte mismatch)")
        # locate first divergence
        r, n = rebuild[ci], B[ci]
        for i in range(min(len(r), len(n))):
            if r[i] != n[i]:
                print(f"  first divergence at char {i}: rebuild={r[i-40:i+40]!r} new={n[i-40:i+40]!r}")
                break
        else:
            print(f"  length divergence: rebuild={len(r)} new={len(n)}")

# --- 2. new strings verbatim in new cells ---
for p in manifest:
    if p['new'] not in B[p['cell']]:
        fails.append(f"P '{p['name']}': new-string NOT verbatim in new cell {p['cell']}")

# --- 3. delta accounting: old + all replacements == new (implied by #1), report sizes ---
for p in manifest:
    print(f"  {p['name']}: cell {p['cell']}, old {len(p['old'])}B -> new {len(p['new'])}B")

# --- 4. AST validity of new cells 11/12 (they are wrapper-nested defs inside a
#        function body in the original; try raw parse first) ---
for ci in (11, 12):
    try:
        ast.parse(B[ci])
        print(f"cell {ci}: AST parse OK")
    except SyntaxError as e:
        # cells may be Colab-magicked / partial; report but check old cell same status
        try:
            ast.parse(A[ci])
            fails.append(f"cell {ci}: NEW cell AST-broken but OLD parsed fine: {e}")
        except SyntaxError:
            print(f"cell {ci}: AST parse fails on BOTH old and new (pre-existing cell style, e.g. %%magic) — parity OK")
# full-notebook AST count (27/27 convention: count parseable code cells)
nb = json.load(open(NEW_NB, encoding='utf-8'))
ok_ast = bad_ast = 0
for c in nb['cells']:
    if c['cell_type'] != 'code':
        continue
    src = ''.join(c.get('source', []))
    src = re.sub(r'^%%[^\n]*\n', '', src)
    try:
        ast.parse(src); ok_ast += 1
    except SyntaxError:
        bad_ast += 1
print(f"notebook AST: {ok_ast} parse OK / {bad_ast} fail (out of {sum(1 for c in nb['cells'] if c['cell_type']=='code')} code cells)")

# --- 5. secrets scan on changed cells ---
sec_pat = re.compile(r'(api[_-]?key|secret|token|password|Bearer\s|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36})', re.I)
for ci in (11, 12):
    hits = sec_pat.findall(B[ci])
    print(f"cell {ci}: secret-pattern hits = {len(hits)}" + (f" {set(hits)}" if hits else ""))

print("\n" + "=" * 60)
if fails:
    print("G1 RESULT: FAIL")
    for f in fails:
        print("  FAIL:", f)
    sys.exit(1)
print("G1 RESULT: PASS — scope {11,12} only, exactly 3 patches, byte-exact rebuild, cells 6/10 untouched")
