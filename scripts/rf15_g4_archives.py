#!/usr/bin/env python3
"""RF-15 G4 — archive byte-identity: S003/S007 full-chain renders through
the RF-15-fixed wrapper chain (dc612d5) must be byte-IDENTICAL to B1 main
(5fe8804), both with kill-switch default-ON and as control with knob OFF.

Arms (fresh namespace each):
  W-ON  : work dc612d5, knob default (ON)
  W-OFF : work dc612d5, MANGABD_CONFIG['detection']['b2_orientation_enable']=False
  B1    : main 5fe8804 bytes (no B2 engine, old wrappers, no fit_w kwargs)

Fixtures (real pipeline artifacts, identical inputs both arms):
  S003 = repo samples/S003_batch2, S007 = repo S007 zip (unpacked)
  image = archived inpainted.png; detections = archived detections.json
  translations = archived translation.json merged into a full row template

Per arm per archive: init_page -> inpainted artifact -> detections ->
detect done -> translation rows -> render_page(force=True) -> hash the
'final' artifact FILE BYTES + per-region ink + rendered count.

Claims tested:
  G4a W-ON final bytes == B1 final bytes  (S003 and S007)
  G4b W-OFF final bytes == B1 final bytes (kill-switch control)
"""
import hashlib, io, json, sys, traceback
from pathlib import Path

import numpy as np
from PIL import Image

WORK_NB = '/tmp/nb_new.json'   # dc612d5
B1_NB = '/tmp/nb_b1.json'      # 5fe8804 (B1 main; Phase A docs-only after f218b35)
OUT = Path('/home/z/my-project/m009b2_repro/rf15_g4_result.json')
ROOT = Path('/home/z/my-project/m009b2_repro/rf15_g4_sandbox')
HARNESS_CELLS = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 15, 23]

ARCHIVES = {
    'S003': Path('/home/z/my-project/repo/samples/S003_batch2'),
    'S007': Path('/tmp/s007'),
}

def cells_of(path):
    nb = json.load(open(path, encoding='utf-8'))
    return [''.join(c.get('source', [])) for c in nb['cells']]

WORK, B1 = cells_of(WORK_NB), cells_of(B1_NB)

def build_arm(tag, cells_src, kill_switch, arm_dir):
    """Fresh namespace; exec verbatim cells; return globals dict."""
    ns_dir = arm_dir / tag
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

ROW_TEMPLATE_FIELDS = dict(
    page_id='', page='', id=0, region_type='bubble',
    detector_class='text_bubble', detector_score=0.9, parent_bubble_id='',
    x=0, y=0, width=0, height=0, angle=0.0,
    original_text='', translated_text='', confidence=0.9,
    ocr_engine='archive', is_english=True, bengali_valid=True,
    status='translated', reading_order=-1,
)

def run_archive(G, tag, arch_name, arch_dir, ns_dir):
    pid = f'{tag}_{arch_name}'.replace('-', '_')
    inp = np.array(Image.open(arch_dir / 'inpainted.png').convert('RGB'))
    h, w = inp.shape[:2]
    dets = json.load(open(arch_dir / 'detections.json'))
    trans = {r['id']: r for r in json.load(open(arch_dir / 'translation.json'))}

    G['init_page'](pid, width=w, height=h, image_np=inp, overwrite=True)
    G['save_image_artifact'](pid, 'inpainted', inp, quality=95)
    G['save_json_artifact'](pid, 'detections', dets)
    G['mark_stage_done'](pid, 'detect', meta={'region_count': len(dets)})

    rows = []
    for d in dets:
        row = dict(ROW_TEMPLATE_FIELDS)
        row.update({
            'page_id': pid, 'page': pid, 'id': int(d['id']),
            'region_type': d.get('region_type', 'bubble'),
            'x': int(d['x']), 'y': int(d['y']),
            'width': int(d['width']), 'height': int(d['height']),
            'angle': float(d.get('angle') or 0.0),
        })
        t = trans.get(d['id'], {})
        row['original_text'] = t.get('original_text', '')
        row['translated_text'] = t.get('translated_text', 'বাংলা পরীক্ষা')
        row['bengali_valid'] = bool(t.get('bengali_valid', True))
        row['status'] = t.get('status', 'translated')
        rows.append(row)
    G['upsert_translation_rows'](pid, rows)

    ev0 = len(G['MANGABD_EVENTS'])
    out = G['render_page'](pid, force=True)
    events = G['MANGABD_EVENTS'][ev0:]

    final_path = G['get_artifact_path'](pid, 'final')
    final_bytes = Path(final_path).read_bytes()
    sha = hashlib.sha256(final_bytes).hexdigest()

    inks = {}
    for d in dets:
        x, y, ww, hh = int(d['x']), int(d['y']), int(d['width']), int(d['height'])
        roi = np.abs(out[y:y+hh, x:x+ww].astype(int) - inp[y:y+hh, x:x+ww].astype(int)).sum(axis=2)
        inks[int(d['id'])] = int((roi > 30).sum())

    df = G['translation_df']
    pr = df[df['page_id'] == pid]
    rendered = int((pr['status'] == 'rendered').sum())
    typerr = sum(1 for e in events if 'unexpected keyword argument' in str(e.get('message', '')))

    (ns_dir / f'final_{arch_name}.jpg').write_bytes(final_bytes)
    return dict(pid=pid, sha256=sha, size=len(final_bytes), rendered=rendered,
                rows=len(pr), typerr=typerr, inks=inks, out_mean=round(float(out.mean()), 4))

results = {}
arm_defs = [
    ('W-ON', WORK, None),
    ('W-OFF', WORK, False),
    ('B1', B1, None),
]
for tag, src, ks in arm_defs:
    results[tag] = {}
    for arch in ('S003', 'S007'):
        ns_dir = ROOT / tag
        G = build_arm(tag, src, ks, ROOT)
        r = run_archive(G, tag, arch, ARCHIVES[arch], ns_dir)
        results[tag][arch] = r
        print(f"{tag:6s} {arch}: sha={r['sha256'][:16]} size={r['size']} "
              f"rendered={r['rendered']}/{r['rows']} typerr={r['typerr']} inks={list(r['inks'].values())}")

print()
checks = {}
for arch in ('S003', 'S007'):
    checks[f'G4a {arch}: W-ON == B1 (byte-identical final)'] = \
        results['W-ON'][arch]['sha256'] == results['B1'][arch]['sha256']
    checks[f'G4b {arch}: W-OFF == B1 (kill-switch control)'] = \
        results['W-OFF'][arch]['sha256'] == results['B1'][arch]['sha256']
    checks[f'G4c {arch}: rendered==6, rows==6, typerr==0 in W-ON'] = (
        results['W-ON'][arch]['rendered'] == 6 and results['W-ON'][arch]['rows'] == 6
        and results['W-ON'][arch]['typerr'] == 0)
    checks[f'G4d {arch}: all 6 regions inked in W-ON'] = \
        all(v > 0 for v in results['W-ON'][arch]['inks'].values())

ok = True
for k, v in checks.items():
    print(f"  {'✅' if v else '❌'} {k}")
    ok &= bool(v)

json.dump({'arms': results, 'checks': checks}, open(OUT, 'w'), ensure_ascii=False, indent=1)
print("\nG4 RESULT:", "PASS" if ok else "FAIL", "->", OUT)
sys.exit(0 if ok else 1)
