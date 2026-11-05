#!/usr/bin/env python3
"""RF-15 G5 — kill-switch intact probe THROUGH the fixed wrapper chain.

RB2-7 ruled semantics (cell-10 _b2_render_angle, verified in source):
knob OFF ZEROES any stored |angle|>1.0 ("re-detect ছাড়াই আগের exact
render bytes" — the knob-OFF steady state is the angle-0 render, NOT a
B1 rotated render; B1 had no mirror and renders stored angles directly).
So the correct intactness equivalence is:

  W-OFF (stored -15) == B1 rendered with angle 0.0   (K1, ruled semantics)
  W-ON  (stored -15) != angle-0 render               (K2, B2 active)
  typerr==0 in all arms (seam knob-independent)      (K3)

Same tilted-quad fixture, three arms:
  W-ON : work dc612d5, knob default ON  -> estimator lean applies
  W-OFF: work dc612d5, knob False       -> mirror zeroes the stored angle
  B1   : main 5fe8804, row angle forced 0.0 (knob-OFF detection semantics:
         cell-6 would never have stored a non-zero angle)
"""
import hashlib, io, json, sys, traceback
from pathlib import Path

import numpy as np

WORK_NB, B1_NB = '/tmp/nb_new.json', '/tmp/nb_b1.json'
OUT = Path('/home/z/my-project/m009b2_repro/rf15_g5_killswitch_result.json')
ROOT = Path('/home/z/my-project/m009b2_repro/rf15_g5_sandbox')
HARNESS_CELLS = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 15, 23]

def cells_of(path):
    nb = json.load(open(path, encoding='utf-8'))
    return [''.join(c.get('source', [])) for c in nb['cells']]

WORK, B1 = cells_of(WORK_NB), cells_of(B1_NB)

def build_arm(tag, cells_src, kill_switch):
    ns_dir = ROOT / tag
    ns_dir.mkdir(parents=True, exist_ok=True)
    base = ns_dir / 'mangabd_base'
    shims = {
        1: [('"/content/mangabd"', f'"{base}"')],
        5: [('Path("/root/.cache/huggingface/hub")', f'Path("{ns_dir}/qwen_hf_cache")')],
    }
    G = {'__name__': '__main__', '__builtins__': __builtins__}
    for i in HARNESS_CELLS:
        src = cells_src[i]
        for old_s, new_s in shims.get(i, []):
            src = src.replace(old_s, new_s)
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        try:
            exec(compile(src, f'<{tag}:c{i}>', 'exec'), G)
        except Exception:
            sys.stdout = old
            raise RuntimeError(f"{tag}: cell {i} failed\n{traceback.format_exc()}")
        finally:
            if sys.stdout is buf:
                sys.stdout = old
        (ns_dir / f'log_{i:02d}.txt').write_text(buf.getvalue(), encoding='utf-8')
    if kill_switch is False:
        G['MANGABD_CONFIG']['detection']['b2_orientation_enable'] = False
    return G

def run_tilted(G, tag, force_angle=None):
    pid = f'{tag}_tilt'.replace('-', '_')
    canvas = np.full((760, 880, 3), 250, np.uint8)
    quad = [[331, 116], [566, 54], [609, 184], [374, 246]]  # ~-15 deg quad
    dets = [dict(id=1, page_id=pid, x=330, y=54, width=280, height=192,
                 quad=quad, angle=-15.0, region_type='bubble',
                 detector_class='text_bubble', detector_score=0.9,
                 parent_bubble_id=None)]
    G['init_page'](pid, width=880, height=760, image_np=canvas, overwrite=True)
    G['save_image_artifact'](pid, 'inpainted', canvas, quality=95)
    G['save_json_artifact'](pid, 'detections', dets)
    G['mark_stage_done'](pid, 'detect', meta={'region_count': 1})
    row = {c: '' for c in G['TRANSLATION_DF_COLUMNS']}
    row.update({
        'page_id': pid, 'page': pid, 'id': 1, 'region_type': 'bubble',
        'detector_class': 'text_bubble', 'detector_score': 0.9,
        'parent_bubble_id': '', 'x': 330, 'y': 54, 'width': 280, 'height': 192,
        'angle': (force_angle if force_angle is not None else -15.0),
        'original_text': 'テスト',
        'translated_text': 'এই কাত হওয়া বাক্সে কী লেখা আছে বলো তো?',
        'confidence': 0.9, 'ocr_engine': 'g5', 'is_english': True,
        'bengali_valid': False, 'status': 'ok', 'reading_order': -1,
    })
    G['upsert_translation_rows'](pid, [row])
    ev0 = len(G['MANGABD_EVENTS'])
    out = G['render_page'](pid, force=True)
    typerr = sum(1 for e in G['MANGABD_EVENTS'][ev0:]
                 if 'unexpected keyword argument' in str(e.get('message', '')))
    final_path = G['get_artifact_path'](pid, 'final')
    fb = Path(final_path).read_bytes()
    # mirrored global knob state as seen by render
    knob = G['MANGABD_CONFIG']['detection'].get('b2_orientation_enable', 'ABSENT')
    return dict(sha256=hashlib.sha256(fb).hexdigest(), size=len(fb),
                typerr=typerr, knob_at_render=str(knob))

results = {}
for tag, src, ks, fang in [('W-ON', WORK, None, None),
                           ('W-OFF', WORK, False, None),
                           ('B1', B1, None, 0.0)]:
    G = build_arm(tag, src, ks)
    results[tag] = run_tilted(G, tag, force_angle=fang)
    print(f"{tag:6s}: sha={results[tag]['sha256'][:16]} size={results[tag]['size']} "
          f"typerr={results[tag]['typerr']} knob={results[tag]['knob_at_render']}")

checks = {
    'K1 W-OFF == B1@angle0 (RB2-7 zeroing mirror == knob-OFF steady state)':
        results['W-OFF']['sha256'] == results['B1']['sha256'],
    'K2 W-ON != B1@angle0 (B2 lean active when ON)':
        results['W-ON']['sha256'] != results['B1']['sha256'],
    'K3 typerr==0 in all arms (seam fix knob-independent)':
        all(v['typerr'] == 0 for v in results.values()),
}
ok = True
for k, v in checks.items():
    print(f"  {'✅' if v else '❌'} {k}")
    ok &= bool(v)
json.dump({'arms': results, 'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print("\nG5 RESULT:", "PASS" if ok else "FAIL", "->", OUT)
sys.exit(0 if ok else 1)
