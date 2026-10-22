#!/usr/bin/env python3
"""MANGABD-006 Phase A — extract current main notebook cells to cells_m006/.

Byte-faithful extraction (join of source list per cell) from the repo notebook
on main @ 86d4bdf (mangabd-006-b1 baseline). Mirrors the m005 extraction conventions.
"""
import json, os, hashlib, sys

REPO = "/home/z/my-project/MangaBD"
NB = os.path.join(REPO, "MangaBD_V12_ipynb_txt.ipynb (3).txt")
OUT = "/home/z/my-project/cells_m006_b1"

os.makedirs(OUT, exist_ok=True)
raw = open(NB, "rb").read()
print("notebook md5:", hashlib.md5(raw).hexdigest(), "bytes:", len(raw))
nb = json.loads(raw.decode("utf-8"))
cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]
print("code cells:", len(cells))
for i, c in enumerate(cells):
    src = "".join(c.get("source", []))
    path = os.path.join(OUT, f"cell_{i:02d}.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(src)
    print(f"cell_{i:02d}.py lines={src.count(chr(10))+1} md5={hashlib.md5(src.encode()).hexdigest()[:16]}")
print("OK ->", OUT)
