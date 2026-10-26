#!/usr/bin/env python3
"""
RF-13 — evidence dump at the FIRST failing assertion (Test 9) + full
font_fallback mutation trace, in the reproduced Owner env (R-G: main font
contains basic Latin). Answers the Owner's questions 2 and 3 verbatim.
"""
import io
import json
import contextlib
import re
import tempfile
from pathlib import Path

import importlib.util
spec = importlib.util.spec_from_file_location(
    "rf13_repro", "/home/z/my-project/scripts/m008_b1_rf13_repro.py")
# We only need the helpers; re-exec of the matrix is avoided by env var gate.
mod = importlib.util.module_from_spec(spec)
import os, sys
sys.argv = [sys.argv[0]]
spec.loader.exec_module(mod)   # runs the matrix once more (cheap, ~40s) — fine

print()
print("#" * 78)
print("# EVIDENCE DUMP — R-G env, at the first failing assertion (Test 9)")
print("#" * 78)

# Rebuild the exact R-G environment
tmp = tempfile.mkdtemp(prefix="rf13_dump_")
fonts, cfg, reg = mod.make_drive_env(
    tmp, mod.FREESERIF, mod.VENDORED)          # main=FreeSerif (Bengali+Latin), fb=vendored JP
ns = mod.make_ns(cfg, reg, trace=True)

so = io.StringIO()
exec(compile(mod.SPAN_CORE, "<cell10 core verbatim>", "exec"), ns)

g = ns  # namespace handle
out = {}
print("\n── Dump at Test 9 fixture state (the exact state the assert saw) ──")
# Reproduce Test 9's fixture head EXACTLY as the cell does:
#   _FB_CACHE.clear(); config pin; DIRECT probe; then evaluate each operand.
fb_real = g["MANGABD_CONFIG"]["rendering"].get("font_fallback", "")
try:
    g["_FB_CACHE"].clear()
    g["MANGABD_CONFIG"]["rendering"]["font_fallback"] = str(g["MANGABD_ASSETS"]["fonts"]["fallback_path"])
    probe = None
    probe_exc = None
    try:
        probe = g["ImageFont"].truetype(
            g["MANGABD_CONFIG"]["rendering"]["font_fallback"], 24)
    except Exception as e:
        probe_exc = repr(e)[:200]

    operands = [
        ("_m9_probe is not None", probe is not None),
        ('_main_font_ok("ক") is True', g["_main_font_ok"]("ক") is True),
        ('_main_font_ok("।") is True  # danda U+0964 (D-1)', g["_main_font_ok"]("।") is True),
        ('_main_font_ok("a") is False # ASCII (D-2)', g["_main_font_ok"]("a") is False),
        ('_main_font_ok(\'"\') is False', g["_main_font_ok"]('"') is False),
        ('_main_font_ok("—") is False', g["_main_font_ok"]("—") is False),
        ('_main_font_ok("こ") is False # kana (D-2)', g["_main_font_ok"]("こ") is False),
    ]
    print("   Test 9 ok-chain operands (verbatim expression -> actual value):")
    chain_val = True
    for expr, val in operands:
        chain_val = chain_val and val
        print(f"     {'PASS' if val else 'FAIL*'}  {expr:<46s} -> {val}")
    print(f"   => ok = {chain_val}   (first failing operand ends the chain — 'and' short-circuit)")

    print("\n── The specific decisions the Owner asked for ──")
    for ch, label in [("।", "U+0964 danda"), ('"', 'U+0022 quote'), ("a", "U+0061 a"), ("こ", "U+3053 kana"), ("ক", "U+0995 ka")]:
        print(f"     _main_font_ok({ch!r}) [{label}] = {g['_main_font_ok'](ch)}")

    # cmap ground truth for both fonts (the WHY)
    from fontTools.ttLib import TTFont
    for label, p in [("MAIN (font_regular)", cfg["rendering"]["font_regular"]),
                     ("FALLBACK (registry)", str(reg))]:
        t = TTFont(p); c = t.getBestCmap()
        covers = {repr(ch): (ord(ch) in c) for ch in ["ক", "।", "a", '"', "—", "こ", "H"]}
        print(f"     {label}: {Path(p).name}  cmap_size={len(c)}  covers={covers}")
        t.close()

    print("\n── State at the assert moment ──")
    print(f"     config['rendering']['font_fallback'] (pinned) = {g['MANGABD_CONFIG']['rendering']['font_fallback']}")
    print(f"     config['rendering']['font_regular']            = {g['MANGABD_CONFIG']['rendering']['font_regular']}")
    print(f"     registry fallback_path                        = {g['MANGABD_ASSETS']['fonts']['fallback_path']}")
    print(f"     _FB_CACHE          = {dict(g['_FB_CACHE'])}")
    print(f"     _FONT_COVERAGE_CACHE keys = {list(g['_FONT_COVERAGE_CACHE'].keys())}"
          f" values-present = {[v is not None for v in g['_FONT_COVERAGE_CACHE'].values()]}")
    print(f"     _FONT_ROUTE_WARNED = {sorted(g['_FONT_ROUTE_WARNED'].keys())}")
    print(f"     get_font_fb(24) = {type(g['get_font_fb'](24)).__name__} (None would mean load failure)")
    print(f"     direct probe    = {type(probe).__name__ if probe else None}  exc={probe_exc}")
finally:
    g["MANGABD_CONFIG"]["rendering"]["font_fallback"] = fb_real
    g["_FB_CACHE"].clear()

# ── full battery with trace: WHO writes font_fallback, when, from where ──
print("\n── Full battery run with the font_fallback mutation tracer ──")
ns2 = mod.make_ns(cfg, reg, trace=True)
so2 = io.StringIO()
gate = False
try:
    exec(compile(mod.SPAN_CORE, "<core>", "exec"), ns2)
    with contextlib.redirect_stdout(so2):
        exec(compile(mod.SPAN_BATT, "<battery>", "exec"), ns2)
except RuntimeError:
    gate = True
print(f"   gate_raised={gate}")
print("   ALL font_fallback writes during the battery (chronological):")
for i, entry in enumerate(ns2["_RF13_TRACE"], 1):
    print(f"     {i:2d}. {entry['src']:<28s} -> {entry['value']}")
    print(f"         line: {entry['line']}")
print("\n   raw stdout of the battery (true chronological print order):")
for line in so2.getvalue().splitlines():
    print("     | " + line)
print("\n   log_event stream (what Colab shows via logging/stderr):")
for e in ns2["MANGABD_EVENTS"]:
    print(f"     [{e['level']:5s}] {e['message']}")
print("\n   post-battery state:")
print(f"     config font_fallback = {ns2['MANGABD_CONFIG']['rendering']['font_fallback']}")
print(f"     _FB_CACHE = {dict(ns2['_FB_CACHE'])}")
print(f"     _FONT_COVERAGE_CACHE = {json.dumps({str(k): ('present' if v is not None else 'None') for k, v in ns2['_FONT_COVERAGE_CACHE'].items()}, indent=2)}")
print(f"     _FONT_ROUTE_WARNED = {sorted(ns2['_FONT_ROUTE_WARNED'].keys())}")
