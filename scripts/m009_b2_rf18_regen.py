#!/usr/bin/env python3
r"""MANGABD-009 B2 RF-18 — patch-content REGENERATOR.

Generates scripts/m009_b2_rf18_content.py from the anchored diff
between the base notebook cells (branch @ 0eeca00, RF-17 tip) and the
RF-18 working cells (cells_rf18_work — the bytes every pre-restart
verification ran against, and the byte-source this session rebuilt
the notebook from).

Laws (RF-17 regen discipline, m009_b2_rf17_regen.py):
  * one cluster per contiguous change (opcodes merged when separated
    by <= 2 unchanged lines); context extended — but never past a
    neighbouring cluster — until the OLD anchor is UNIQUE in its
    base cell; if uniqueness needs more room, clusters merge;
  * re-derivation proof: base + PATCHES == work, cell by cell, byte
    for byte;
  * scope guard: changed cells exactly {6, 10}.

Edit patches via the notebook + regen, never by hand.
"""
import difflib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "0eeca00"
WORK = Path("/home/z/my-project/cells_rf18_work")
OUT = REPO / "scripts" / "m009_b2_rf18_content.py"
MERGE_GAP = 2          # unchanged lines that still merge two clusters
MIN_CONTEXT = 2        # context lines kept on each side of a cluster


def cells_at(ref):
    raw = subprocess.run(
        ["git", "-C", str(REPO), "show", f"{ref}:{NB_NAME}"],
        capture_output=True, check=True).stdout
    nb = json.loads(raw.decode("utf-8"))
    return ["".join(c.get("source", [])) for c in nb["cells"]]


def span_text(lines, s, e):
    """Exact source text of lines[s:e] (join + trailing newline when
    the span does not run to the array end; split('\n') semantics).
    An EMPTY span is the empty string (pure insertion/deletion)."""
    if e <= s:
        return ""
    if e >= len(lines):
        return "\n".join(lines[s:e])
    return "\n".join(lines[s:e]) + "\n"


def clusters_for(a, b):
    """Non-overlapping (i0, i1, j0, j1) change clusters, gaps <=
    MERGE_GAP merged, anchors unique, contexts within bounds."""
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    raw = [op for op in sm.get_opcodes() if op[0] != "equal"]
    merged = []
    for tag, i0, i1, j0, j1 in raw:
        if merged and i0 - merged[-1][1] <= MERGE_GAP:
            pi0, pi1, pj0, pj1 = merged[-1]
            merged[-1] = (pi0, max(pi1, i1), pj0, max(pj1, j1))
        else:
            merged.append((i0, i1, j0, j1))

    full = "\n".join(a)
    out = []
    for k, (i0, i1, j0, j1) in enumerate(merged):
        lo = merged[k - 1][1] if k else 0
        hi = merged[k + 1][0] if k + 1 < len(merged) else len(a)
        s, e = i0, i1
        # grow context until the anchor is unique (or bounds reached)
        while True:
            anchor = span_text(a, s, e)
            if full.count(anchor) == 1:
                break
            grew = False
            if s > lo and (i0 - s) < (e - i1):
                s -= 1
                grew = True
            elif e < hi:
                e += 1
                grew = True
            elif s > lo:
                s -= 1
                grew = True
            if not grew:
                break
        anchor = span_text(a, s, e)
        assert full.count(anchor) == 1, (
            f"anchor not unique even at bounds [{s}:{e}]")
        js = j0 - (i0 - s)
        je = j1 + (e - i1)
        assert 0 <= js and je <= len(b), "work-span bounds"
        out.append((s, e, js, je))
    return out


base = cells_at(BASE_REF)
work = [p.read_text(encoding="utf-8")
        for p in sorted(WORK.glob("cell_*.py"))]
assert len(base) == len(work) == 27

changed = [i for i in range(27) if base[i] != work[i]]
assert sorted(changed) == [6, 10], f"scope breach: {changed}"
print(f"changed cells: {changed}")

patches = []
for c in changed:
    a = base[c].split("\n")
    b = work[c].split("\n")
    for s, e, js, je in clusters_for(a, b):
        old = span_text(a, s, e)
        new = span_text(b, js, je)
        assert base[c].count(old) == 1
        patches.append((c, old, new))

# re-derivation proof
rebuilt = {c: base[c] for c in range(27)}
for c, old, new in patches:
    assert rebuilt[c].count(old) == 1
    rebuilt[c] = rebuilt[c].replace(old, new, 1)
for c in changed:
    assert rebuilt[c] == work[c], f"re-derivation mismatch cell {c}"
for c in range(27):
    if c not in changed:
        assert rebuilt[c] == base[c]
print(f"clusters: {len(patches)}; re-derivation PROVEN "
      f"(base + patches == cells_rf18_work, 27/27)")

names6 = [
    "_B2_RING_MARGIN 16 -> 6 revert (RF-18: 9b estimator is the "
    "fallback rung only; S009 stored angles byte-stable 6..18)",
    "9c section: _b2_page_ink_mask + _b2_mask_orientation "
    "(original-ink orientation GT — minAreaRect + row-profile)",
    "detect_page: b2_ink_mask build (kill-switch gated, WARN on fail)",
    "detect_page: RF-18 ladder — mask-GT first (measured 0.0 FINAL), "
    "9b estimator fallback, 0 deg",
    "detect_page: b2_gt_lines/spacing/cx/cy on tilted mask-GT rows",
]
names10 = [
    "choose_text_color: +mask kwarg (signature)",
    "choose_text_color: mask-restricted brightness (D2 white-on-white)",
    "_b2_gt_tilted_layout: GT-mirrored wrap/size/line-height/vjust",
    "render_bengali_text: fit_result normalize + b2gt mode guard "
    "(rotated-only, RF-15 disjoint-condition law)",
    "render_bengali_text: b2gt consumption (_b2_gt_lh + cx/cy)",
    "render_bengali_text: else -> elif _b2_gt_lh is None (branch split)",
    "render_bengali_text: line_height = GT spacing mirror",
    "render call: gt_cx/gt_cy/gt_block_h threading",
    "_render_rotated_text: gt_cx/gt_cy/gt_block_h kwargs (signature)",
    "_render_rotated_text: canvas height growth for GT block (D1 law)",
    "_render_rotated_text: paste center = original ink centroid (GT)",
    "_b2_interior_fit DELETED (RF-17 helper superseded by mask GT)",
    "render_page: b2_page_gt dict",
    "render_page: b2_gt_* load from detections artifact",
    "render_page: b2_page_gt reset arm",
    "render_page: b2gt fit_result + quad fillPoly color mask "
    "(replaces the RF-17 interior-fit block)",
    "render_page: choose_text_color(mask=...) + RF-17 interior-color "
    "override removed",
    "render_page: RF-17 interior padding/centroid-shift block removed",
    "render call: x/y back to bbox (RF-17 _b2_dx/_b2_dy removed)",
    "render call: fit_result=b2gt_fr (RF-17 padding kwarg removed)",
    "battery Test 21 rewritten: mask-GT -> render parity trap",
    "Test 21 label line",
]

lines_out = [
    "#!/usr/bin/env python3",
    '"""MANGABD-009 B2 RF-18 — patch content (REGENERATED from the',
    "0eeca00 -> cells_rf18_work diff; scripts/m009_b2_rf18_regen.py is",
    "the generator — edit patches via the notebook + regen, never by",
    "hand).",
    "",
    "Cells touched: {6, 10} ONLY (RF-18 scope).",
    '"""',
    "",
]
percell = {6: 0, 10: 0}
for k, (c, old, new) in enumerate(patches, 1):
    percell[c] += 1
    nm = (names6 if c == 6 else names10)[percell[c] - 1]
    lines_out.append("# " + "=" * 66)
    lines_out.append(f"# cell{c} hunk{percell[c]} (replace) — {nm}")
    lines_out.append(f"P{k:02d}_CELL = {c}")
    lines_out.append(f"P{k:02d}_OLD = {old!r}")
    lines_out.append("")
    lines_out.append(f"P{k:02d}_NEW = {new!r}")
    lines_out.append("")
lines_out.append("PATCHES = [")
for k in range(1, len(patches) + 1):
    lines_out.append(f"    (P{k:02d}_CELL, P{k:02d}_OLD, P{k:02d}_NEW),")
lines_out.append("]")
OUT.write_text("\n".join(lines_out) + "\n", encoding="utf-8")
print(f"wrote {OUT} ({len(patches)} patches: "
      f"cell6 x{percell[6]}, cell10 x{percell[10]})")

# import check of the generated module
sys.path.insert(0, str(REPO / "scripts"))
import m009_b2_rf18_content as mc  # noqa: E402
assert len(mc.PATCHES) == len(patches)
rb = {c: base[c] for c in range(27)}
for c, old, new in mc.PATCHES:
    assert rb[c].count(old) == 1
    rb[c] = rb[c].replace(old, new, 1)
for c in changed:
    assert rb[c] == work[c]
print("generated module import + re-derivation PROVEN")
