#!/usr/bin/env python3
r"""MANGABD-007 B1 (Phase C) — build driver: the 1-line cell-1 lama_size cleanup.

Surgical byte-level edit of the notebook raw JSON:

  OLD (escaped raw form):  \"lama_size\": 1024,
  NEW (escaped raw form):  \"lama_size\": 2048,

Location: cell 1 (index 1), source line 302 — the MANGABD_CONFIG "inpainting"
dict literal. This closes tracked follow-up #1 of MANGABD-005 B1 Phase D
(DECISION.md §E.1: "cell-1:295 lama_size cleanup", cited at the M005-era
line numbering; the literal has since drifted to line 302 after the M6-B1
OCR-registry CONFIG section additions — disclosed in the Phase C record).

Surgery properties (all asserted):
  * the OLD byte string occurs EXACTLY ONCE in the raw file
    (cell-9's migration `== 1024:` and ladder tuple `(2048, 1536, 1024)`
    are different byte forms and do not match);
  * the NEW byte string occurs ZERO times pre-edit;
  * replacement is SAME-LENGTH (file size byte-identical);
  * exactly 3 byte positions differ ('1'->'2', '2'->'4', '4'->'8'; the '0'
    is shared) — zero reformatting, zero collateral bytes;
  * post-write: JSON valid, 27 cells, cell-1 source line 302 reads 2048,
    every other cell byte-identical to the pre-edit state.
"""
import ast
import hashlib
import json
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
OLD = b'\\"lama_size\\": 1024,'
NEW = b'\\"lama_size\\": 2048,'
CELL1_LINE = 302  # 1-indexed source line of the literal inside cell 1


def fail(msg):
    print(f"FAIL  {msg}")
    sys.exit(1)


def cell_source(nb, i):
    return "".join(nb["cells"][i]["source"])


# ── pre-state assertions ─────────────────────────────────────
raw = NB.read_bytes()
pre_md5 = hashlib.md5(raw).hexdigest()
n_old = raw.count(OLD)
n_new = raw.count(NEW)
if n_old != 1:
    fail(f"pre-edit: OLD byte string count == {n_old}, expected exactly 1")
if n_new != 0:
    fail(f"pre-edit: NEW byte string count == {n_new}, expected 0")
print(f"pre-edit md5: {pre_md5}")
print(f"pre-edit: OLD x{n_old}, NEW x{n_new}  (uniqueness proven)")

nb_pre = json.loads(raw)
if len(nb_pre["cells"]) != 27:
    fail(f"pre-edit: {len(nb_pre['cells'])} cells, expected 27")
pre_line = cell_source(nb_pre, 1).split("\n")[CELL1_LINE - 1]
if pre_line != '        "lama_size": 1024,':
    fail(f"pre-edit: cell-1 line {CELL1_LINE} == {pre_line!r}, unexpected")

# ── the surgery ──────────────────────────────────────────────
raw2 = raw.replace(OLD, NEW, 1)
if raw2.count(NEW) != 1 or raw2.count(OLD) != 0:
    fail("post-replace occurrence counts wrong")
if len(raw2) != len(raw):
    fail(f"length changed: {len(raw)} -> {len(raw2)}")
diffs = [i for i in range(len(raw)) if raw[i] != raw2[i]]
if len(diffs) != 3:
    fail(f"expected exactly 3 differing byte positions, got {len(diffs)}: {diffs}")
delta = [(d, bytes([raw[d]]), bytes([raw2[d]])) for d in diffs]
print(f"differing byte positions ({len(diffs)}): "
      + ", ".join(f"@{d} {o.decode()}->{n.decode()}" for d, o, n in delta))
span = raw2.index(NEW) + NEW.index(b"2048")  # start of the replaced 4-char digit run
if not (raw[span:span + 4] == b"1024" and raw2[span:span + 4] == b"2048"):
    fail(f"replaced span @{span} is not 1024->2048")
if not all(span <= d < span + 4 for d in diffs):
    fail(f"differing positions outside the replaced span [{span},{span+4}): {diffs}")
NB.write_bytes(raw2)
post_md5 = hashlib.md5(raw2).hexdigest()
print(f"post-edit md5: {post_md5}  (size identical: {len(raw2)} bytes)")

# ── post-write verification ──────────────────────────────────
nb_post = json.loads(NB.read_bytes())
if len(nb_post["cells"]) != 27:
    fail("post-write: cell count != 27")
post_line = cell_source(nb_post, 1).split("\n")[CELL1_LINE - 1]
if post_line != '        "lama_size": 2048,':
    fail(f"post-write: cell-1 line {CELL1_LINE} == {post_line!r}")
for i in range(27):
    if i == 1:
        continue
    if json.dumps(nb_pre["cells"][i]) != json.dumps(nb_post["cells"][i]):
        fail(f"post-write: cell {i} changed (must be byte-identical)")
src1_pre = cell_source(nb_pre, 1).split("\n")
src1_post = cell_source(nb_post, 1).split("\n")
if len(src1_pre) != len(src1_post):
    fail("cell-1 source line count changed")
changed = [k for k in range(len(src1_pre)) if src1_pre[k] != src1_post[k]]
if changed != [CELL1_LINE - 1]:
    fail(f"cell-1 changed source lines == {changed}, expected [{CELL1_LINE - 1}]")
ast.parse(cell_source(nb_post, 1))  # cell 1 still compiles
ast.parse(cell_source(nb_post, 9))  # cell 9 still compiles (untouched)
print(f"post-write: cell-1 line {CELL1_LINE} now reads {post_line.strip()!r}; "
      f"only changed source line in cell 1; other 26 cells byte-identical")

print()
print("BUILD OK — 1-line surgical edit applied, zero collateral bytes")
