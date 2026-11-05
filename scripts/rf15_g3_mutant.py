#!/usr/bin/env python3
"""RF-15 G3 — mutant arm: battery Test 20 must HARD-RAISE on the old
(84aa238) wrapper bytes.

Mutant construction (from the 3-patch manifest, applied selectively):
  cell 11 mutant = OLD cell 11 (P1 reverted — old wrapper, no fit_w/fit_h)
  cell 12 mutant = OLD cell 12 + P3 ONLY (old wrapper + Test 20 battery)
The harness then runs the SAME full chain (same cells, same shims) with
the mutant cells substituted. Expected:
  - Test 20 prints ❌ (run_test False)
  - render_page swallows per-row TypeErrors ('unexpected keyword
    argument fit_w') -> rendered=0, blank final, zero ink
  - cell 12 exec ends in RuntimeError (the hard-raise contract)
"""
import io, json, sys, traceback
from pathlib import Path

sys.path.insert(0, '/home/z/my-project/scripts')

NB_OLD = '/tmp/nb_old.json'
NB_NEW = '/tmp/nb_new.json'
MANIFEST = '/home/z/my-project/repo/scripts/m009_b2_rf15_patches.json'
OUT = Path('/home/z/my-project/m009b2_repro/rf15_g3_mutant_result.json')
SANDBOX = Path('/home/z/my-project/m009b2_repro/rf15_g3_sandbox')
HARNESS_CELLS = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 15, 23]

def cells_of(path):
    nb = json.load(open(path, encoding='utf-8'))
    return [''.join(c.get('source', [])) for c in nb['cells']]

OLD, NEW = cells_of(NB_OLD), cells_of(NB_NEW)
manifest = json.load(open(MANIFEST, encoding='utf-8'))
P1, P2, P3 = manifest

SANDBOX.mkdir(parents=True, exist_ok=True)

# ── build mutant cells ──────────────────────────────────────────────
mut11 = OLD[11]
assert P1['new'] not in mut11 and P1['old'] in mut11, "old cell 11 shape unexpected"
mut12 = OLD[12]
assert P3['old'] in mut12, "P3 anchor missing in old cell 12"
mut12 = mut12.replace(P3['old'], P3['new'], 1)
# sanity: mutant != new bytes (mutant keeps OLD wrappers)
assert mut11 != NEW[11], "mutant cell 11 accidentally equals fixed cell 11"
assert mut12 != NEW[12], "mutant cell 12 accidentally equals fixed cell 12"
print("mutant built: cell 11 = old wrapper, cell 12 = old wrapper + Test 20")
print(f"  mut11 len={len(mut11)} (new={len(NEW[11])})  mut12 len={len(mut12)} (new={len(NEW[12])})")

# env shims (same as G2)
SANDBOX_BASE = '/home/z/my-project/m009b2_repro/rf15_g3_sandbox/mangabd_base'
SHIMS = {
    1: [('"/content/mangabd"', f'"{SANDBOX_BASE}"')],
    5: [('Path("/root/.cache/huggingface/hub")', f'Path("{SANDBOX}/qwen_hf_cache")')],
}
SRC = {}
for i in HARNESS_CELLS:
    src = {11: mut11, 12: mut12}.get(i, NEW[i])
    for old_s, new_s in SHIMS.get(i, []):
        src = src.replace(old_s, new_s)
    SRC[i] = src
    (SANDBOX / f'cell_{i:02d}.py').write_text(src, encoding='utf-8')

# ── run the chain ───────────────────────────────────────────────────
G = {'__name__': '__main__', '__builtins__': __builtins__}
logs, raised = {}, None
for i in HARNESS_CELLS:
    tag = f"cell[{i}]"
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        exec(compile(SRC[i], f'<mut {tag}>', 'exec'), G)
        logs[tag] = 'OK'
    except Exception:
        logs[tag] = 'RAISED: ' + type(sys.exc_info()[1]).__name__
        raised = (tag, traceback.format_exc(), buf.getvalue())
    finally:
        sys.stdout = old_stdout
    text = buf.getvalue()
    (SANDBOX / f'log_{i:02d}.txt').write_text(text, encoding='utf-8')
    print(f"{tag}: {logs[tag]}" + (f" ({len(text)}B)" if text else ""))
    if raised:
        break

result = {'cell_logs': logs}

# ── expectations ────────────────────────────────────────────────────
log12 = (SANDBOX / 'log_12.txt').read_text(encoding='utf-8') if (SANDBOX / 'log_12.txt').exists() else ''
t20_fail_printed = '❌' in log12 and 'full-chain render integration' in log12
t20_detail = ''
for l in log12.splitlines():
    if 'full-chain render integration' in l:
        t20_detail = l.strip()[:200]

hard_raise = raised is not None and raised[0] == 'cell[12]' and 'RuntimeError' in raised[1]
# WARN lines go through the logging handler into session.log/events.jsonl,
# not into cell stdout — check both the Test-20 detail line (typerr=N) and
# the event artifacts on disk.
import glob
ev_files = glob.glob(str(SANDBOX / 'mangabd_base' / 'sessions' / '*' / 'logs' / '*'))
ev_hit = any('unexpected keyword' in open(f, encoding='utf-8', errors='replace').read()
             for f in ev_files)
kwarg_typerr = ('typerr=' in log12 and 'typerr=0' not in log12) or ev_hit

# probe: was the t20 page left blank / rendered=0? (page deleted in finally,
# so rely on the printed test detail + event lines in stdout)
result['t20_fail_printed'] = t20_fail_printed
result['t20_detail'] = t20_detail
result['hard_raise_cell12'] = hard_raise
result['kwarg_typerr_seen'] = kwarg_typerr
result['raise_tail'] = (raised[1].splitlines()[-1] if raised else None)
result['stdout_tail_cell12'] = log12[-400:]

print("\n══ G3 mutant expectations ══")
checks = {
    'M1 Test 20 printed ❌ (battery fired on mutant)': t20_fail_printed,
    'M2 cell-12 HARD-RAISED RuntimeError': hard_raise,
    'M3 kwarg TypeError seen (owner symptom)': kwarg_typerr,
}
ok = True
for k, v in checks.items():
    print(f"  {'✅' if v else '❌'} {k}")
    ok &= bool(v)
result['checks'] = checks
json.dump(result, open(OUT, 'w'), ensure_ascii=False, indent=1)
print("\nG3 RESULT:", "PASS" if ok else "FAIL", "->", OUT)
sys.exit(0 if ok else 1)
