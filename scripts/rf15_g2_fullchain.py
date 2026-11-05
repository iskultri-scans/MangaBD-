#!/usr/bin/env python3
"""RF-15 G2 — full-chain harness, INDEPENDENT (not GLM's repro.py).

Runs notebook cells [0..7,10,11,12,15,23] VERBATIM from the dc612d5
bytes (task list "cells 1..7,10,11,12,15,23": notebook cells 1..7 ==
JSON[0..7] since Cell 2 hard-depends on MANGABD_ENV from Cell 1; the
rest are JSON indices per repo convention), in order, in ONE namespace
(fresh interpreter, exec into globals) — exactly the gap RF-15 exposed
(no instrument ever ran render_page AFTER the cells-11/12 wrapper
rebinds in one namespace).

After the verbatim cells run, the harness drives ITS OWN full-chain
page (own geometry/text, distinct from GLM's Test 20):
  init_page -> inpainted artifact -> detections JSON (horizontal /
  tilted-quad / vertical classes) -> mark detect done -> translation
  rows -> render_page(force=True)

Assertions:
  A1 rendered > 0 for the harness page (status=='rendered')
  A2 zero "unexpected keyword argument" events in MANGABD_EVENTS
  A3 every region class inked (per-region ROI diff vs input canvas
     above threshold)
  A4 cell-12's Test 20 (part of verbatim cell 12) printed PASS and did
     not hard-raise
  A5 which wrapper won the global rebind (recorded for G6)
"""
import io, json, sys, traceback
from pathlib import Path

NB = '/tmp/nb_new.json'
OUT = Path('/home/z/my-project/m009b2_repro/rf15_g2_result.json')
SANDBOX = Path('/home/z/my-project/m009b2_repro/rf15_g2_sandbox')

HARNESS_CELLS = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 15, 23]

nb = json.load(open(NB, encoding='utf-8'))
CELLS = [''.join(c.get('source', [])) for c in nb['cells']]

SANDBOX.mkdir(parents=True, exist_ok=True)

# Environment shim (sandbox, NOT a notebook-source change): this container
# cannot create the Colab convention path /content/mangabd (no permission on
# /). Previous RF-14 instruments used the same redirect (their logs show the
# identical 'Drive mount failed' + redirected base). Only cell 1 (JSON[1],
# Config) is redirected; every other cell runs byte-verbatim.
SANDBOX_BASE = '/home/z/my-project/m009b2_repro/rf15_g2_sandbox/mangabd_base'
# cell-5 shim: QWEN_LOCAL_CACHE hardcodes Colab-root convention /root/.cache
# (Colab runs as root; this sandbox user cannot write there). The constant is
# only mkdir'd at setup and used as Qwen-VL download cache_dir — the Qwen
# model is never loaded in this render chain, so the redirect has zero
# behavioral coupling with what G2 measures.
SHIMS = {
    1: [('"/content/mangabd"', f'"{SANDBOX_BASE}"')],
    5: [('Path("/root/.cache/huggingface/hub")',
         f'Path("{SANDBOX}/qwen_hf_cache")')],
}

for i in HARNESS_CELLS:
    src = CELLS[i]
    for old_s, new_s in SHIMS.get(i, []):
        assert old_s in src, f'shim target missing in cell {i}'
        src = src.replace(old_s, new_s)
    (SANDBOX / f'cell_{i:02d}.py').write_text(src, encoding='utf-8')

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

# ── fresh namespace, one global dict ────────────────────────────────
G = {'__name__': '__main__', '__builtins__': __builtins__}
cell_logs = {}
fatal = None

for i in HARNESS_CELLS:
    tag = f"cell[{i}]"
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        exec(compile(SANDBOX.joinpath(f'cell_{i:02d}.py').read_text(encoding='utf-8'),
                     f'<{tag}>', 'exec'), G)
        cell_logs[tag] = 'OK' if i not in SHIMS else 'OK (base-dir shim)'
    except Exception:
        sys.stdout = old
        cell_logs[tag] = 'EXCEPTION'
        fatal = (tag, traceback.format_exc())
        print(f"FATAL in {tag}:\n{fatal[1]}", file=sys.stderr)
        break
    finally:
        if sys.stdout is buf:
            sys.stdout = old
    out = buf.getvalue()
    (SANDBOX / f'log_{i:02d}.txt').write_text(out, encoding='utf-8')
    # battery summary lines worth surfacing
    keep = [l for l in out.splitlines()
            if ('run_test' in l.lower() or '✅' in l or '❌' in l or 'PASS' in l.upper())
            and ('test' in l.lower() or 'battery' in l.lower() or '🧪' in l)]
    print(f"{tag}: ran OK, {len(out)}B stdout"
          + (f" | battery-ish: {keep[-3:]}" if keep else ""))

if fatal:
    json.dump({'fatal': fatal[0], 'trace': fatal[1], 'cell_logs': cell_logs},
              open(OUT, 'w'), ensure_ascii=False, indent=1)
    sys.exit(1)

print("\n══ all harness cells ran verbatim in ONE namespace ══")

# ── A4: Test 20 result from cell-12 stdout ──────────────────────────
log12 = (SANDBOX / 'log_12.txt').read_text(encoding='utf-8')
t20_lines = [l for l in log12.splitlines() if 'RF-15' in l or 'full-chain render integration' in l]
print("cell-12 Test 20 lines:", t20_lines)
t20_pass = any('✅' in l for l in t20_lines) and '❌' not in ''.join(t20_lines)

# A5: which wrapper won
import types
rbt = G.get('render_bengali_text')
winner = 'UNKNOWN'
cell12_src = CELLS[12]
if rbt is not None:
    try:
        code12 = compile(cell12_src, '<c12>', 'exec')
        winner = 'cell-12 wrapper' if 'container-aware' in str(getattr(rbt, '__qualname__', '')) or True else '?'
    except Exception:
        pass
# simpler: check identity of the function object's module-level co_filename
winner = f"co_filename={getattr(rbt, '__co_filename__', getattr(rbt, '__code__', None) and rbt.__code__.co_filename)}"
print("A5 global render_bengali_text:", winner)

# ══ MY OWN full-chain page ══════════════════════════════════════════
import numpy as np

pid = '__rf15_g2_page__'
rng = np.random.default_rng(1515)
canvas = np.full((900, 1100, 3), 247, np.uint8)
canvas[40:860, 40:1060] = 233  # page art stand-in

# three region classes; geometry distinct from Test 20's
#  h : horizontal bubble, angle 0, no tilt
#  t : tilted bubble, angle -14.5 with TRUE quad (quad-extents arm)
#  v : vertical note  w<90, h>2w, angle 0
regions = [
    dict(id=11, x=70,  y=60,  w=260, h=120, angle=0.0,
         quad=[[70, 60], [330, 60], [330, 180], [70, 180]],
         text="সে কি সত্যিই চলে গেছে?", rtype='bubble'),
    dict(id=12, x=430, y=120, w=300, h=200, angle=-14.5,
         quad=[[430, 168], [688, 120], [730, 262], [472, 310]],
         text="কী বলছিলে তুমি একটু বলো?!", rtype='bubble'),
    dict(id=13, x=920, y=210, w=70, h=290, angle=0.0,
         quad=[[920, 210], [990, 210], [990, 500], [920, 500]],
         text="এতগুলো ঘটনা কী করে ঘটলো বলো", rtype='bubble'),
]
dets = [dict(id=r['id'], page_id=pid, x=r['x'], y=r['y'], width=r['w'],
             height=r['h'], quad=r['quad'], angle=r['angle'],
             region_type=r['rtype'], detector_class='text_bubble',
             detector_score=0.93, parent_bubble_id=None) for r in regions]

G['init_page'](pid, width=1100, height=900, image_np=canvas, overwrite=True)
G['save_image_artifact'](pid, 'inpainted', canvas, quality=95)
G['save_json_artifact'](pid, 'detections', dets)
G['mark_stage_done'](pid, 'detect', meta={'region_count': len(dets)})

rows = []
for r in regions:
    row = {c: '' for c in G['TRANSLATION_DF_COLUMNS']}
    row.update({
        'page_id': pid, 'page': pid, 'id': r['id'],
        'region_type': r['rtype'], 'detector_class': 'text_bubble',
        'detector_score': 0.93, 'parent_bubble_id': '',
        'x': r['x'], 'y': r['y'], 'width': r['w'], 'height': r['h'],
        'angle': r['angle'], 'original_text': 'テスト',
        'translated_text': r['text'], 'confidence': 0.93,
        'ocr_engine': 'g2', 'is_english': True,
        'bengali_valid': False, 'status': 'ok', 'reading_order': -1,
    })
    rows.append(row)
G['upsert_translation_rows'](pid, rows)

ev0 = len(G['MANGABD_EVENTS'])
out = G['render_page'](pid, force=True)

new_events = G['MANGABD_EVENTS'][ev0:]
typerr = [e for e in new_events if 'unexpected keyword argument' in str(e.get('message', ''))]
warns = [e for e in new_events if str(e.get('level', '')).upper() in ('WARN', 'WARNING')]

df = G['translation_df']
page_rows = df[df['page_id'] == pid]
rendered = int((page_rows['status'] == 'rendered').sum())

inks = {}
for r, d in zip(regions, dets):
    x, y, w, h = d['x'], d['y'], d['width'], d['height']
    roi = np.abs(out[y:y+h, x:x+w].astype(int) - canvas[y:y+h, x:x+w].astype(int)).sum(axis=2)
    inks[r['id']] = int((roi > 30).sum())

result = {
    'rendered': rendered, 'rows': len(page_rows),
    'typerr_events': len(typerr), 'typerr_sample': typerr[:2],
    'warn_events': len(warns), 'warn_sample': [str(e.get('message', ''))[:120] for e in warns[:3]],
    'inks': inks,
    'out_shape': list(out.shape), 'out_mean': float(out.mean()),
    't20_pass_in_cell12': bool(t20_pass),
    'winner_global_rbt': winner,
}
print("\n══ G2 harness page result ══")
print(json.dumps(result, ensure_ascii=False, indent=1))

checks = {
    'A1 rendered>0': rendered > 0,
    'A2 zero kwarg TypeErrors': len(typerr) == 0,
    'A3a horizontal inked': inks[11] >= 50,
    'A3b tilted-quad inked': inks[12] >= 50,
    'A3c vertical inked': inks[13] >= 50,
    'A4 cell-12 Test 20 PASS in-namespace': bool(t20_pass),
}
print()
ok = True
for k, v in checks.items():
    print(f"  {'✅' if v else '❌'} {k}")
    ok &= bool(v)

result['checks'] = checks
result['cell_logs'] = cell_logs
json.dump(result, open(OUT, 'w'), ensure_ascii=False, indent=1)
print("\nG2 RESULT:", "PASS" if ok else "FAIL", "->", OUT)
sys.exit(0 if ok else 1)
