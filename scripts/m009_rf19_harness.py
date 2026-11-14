#!/usr/bin/env python3
"""MANGABD-009 RF-19 — battery harness (committed).

Execs the post-build cells (cells_rf19_fix) in one namespace with the
rf15 exec law (incl. the DISCLOSED cell-04 torch-stub tolerance) and
census-checks the battery: cell-10 SUCCESS, the Test-25 arms, the
Test-24 arms, cell-11 7.5c, cell-12 7.7b, the legacy Test-23 family
markers. Called by scripts/m009_rf19_verify.py V2 (subprocess).
"""
import contextlib
import io
import sys
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
sys.path.insert(0, str(REPO / "scripts"))

from m009_b2_rf14_repro import (  # noqa: E402
    install_pathlib_shim, make_torch_stub, restore_pathlib,
)
from m009_b2_rf15_repro import CELL_IDS, seed_cell00_side_effects  # noqa: E402

WORK = Path("/home/z/my-project/cells_rf19_fix")

ns = {"__name__": "__mangabd__"}
logs = {}
seed_cell00_side_effects(ns)
sys.modules["torch"] = make_torch_stub()
install_pathlib_shim()
failed = None
try:
    for cid in CELL_IDS:
        src = (WORK / f"cell_{cid:02d}.py").read_text(encoding="utf-8")
        code = compile(src, f"cell_{cid:02d}.py", "exec")
        buf = io.StringIO()
        print(f"[harness] exec cell_{cid:02d} ({len(src)} bytes)")
        try:
            with contextlib.redirect_stdout(buf):
                exec(code, ns)
        except RuntimeError as exc:
            # DISCLOSED tolerance, cell_04 only (RF-14 rule — the
            # instrument/Phase-C-harness law): inert torch stub cannot
            # feed the zyddnys import chain (CTD/LaMa = inpaint deps,
            # out of the render path under test).
            txt = buf.getvalue()
            fail_lines = [ln for ln in txt.splitlines() if "❌" in ln]
            zyddnys_only = fail_lines and all(
                ("ComicTextDetector" in ln or "LamaLargeInpainter" in ln)
                for ln in fail_lines)
            render_green = all(m in txt for m in (
                "Bengali font render test passed",
                "libraqm available", "Bengali render test"))
            if (cid == 4 and "Cell 4 self-tests failed" in str(exc)
                    and zyddnys_only and render_green):
                print(f"[harness] cell_04 RuntimeError tolerated "
                      f"(torch-stub law, disclosed)")
            else:
                print(f"[harness] cell_{cid:02d} RAISED: {exc}")
                logs[cid] = buf.getvalue()
                failed = (cid, exc)
                break
        logs[cid] = buf.getvalue()
finally:
    restore_pathlib()

if failed:
    cid, exc = failed
    print(f"\n===== cell {cid} output (tail) =====")
    print(logs[cid][-4000:])
    sys.exit(1)

fail = []
for cid in CELL_IDS:
    if cid == 4:
        continue  # disclosed torch-stub import failures (RF-14 law)
    if "❌" in logs.get(cid, ""):
        bad = [ln for ln in logs[cid].splitlines() if "❌" in ln]
        fail.append((cid, bad[:8]))
if fail:
    print("BATTERY SMOKE: FAIL")
    for cid, bad in fail:
        print(f" cell {cid}:")
        for ln in bad:
            print("   ", ln[:160])
    sys.exit(1)

assert "Cell 10 result: SUCCESS" in logs[10]
_cell10_line = next(ln.strip() for ln in logs[10].splitlines()
                    if "Cell 10 result:" in ln)
print(f"CELL10: {_cell10_line}")
t25 = [ln.strip() for ln in logs[10].splitlines()
       if "RF-19" in ln and ("✅" in ln or "❌" in ln)]
print(f"Test 25 arm lines: {len(t25)}")
for ln in t25:
    print("  ", ln[:120])
t24 = [ln.strip() for ln in logs[10].splitlines()
       if "B3.1" in ln and ("✅" in ln or "❌" in ln)]
print(f"Test 24 arm lines: {len(t24)}")
for ln in t24:
    print("  ", ln[:120])
legacy = [ln.strip() for ln in logs[10].splitlines()
          if "✅" in ln and ("B3 " in ln or "B3:" in ln)
          and "B3.1" not in ln]
print(f"LEGACY-B3-MARKERS ({len(legacy)}):")
for ln in legacy:
    print("  ", ln[:120])
print(f"LEGACY-B3-MARKERS-OK {len(legacy) >= 8}")
for cid, marker in ((11, "B3.1 wrapper line_colors threading"),
                    (12, "B3.1 line_colors full-chain integration")):
    hit = [ln for ln in logs[cid].splitlines() if marker in ln]
    assert hit and "✅" in hit[0], f"cell {cid}: {hit}"
    print(f"  cell {cid}: {hit[0].strip()[:120]}")
print("\nBATTERY SMOKE: ALL GREEN")
