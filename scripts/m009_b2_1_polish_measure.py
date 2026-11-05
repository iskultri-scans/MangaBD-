#!/usr/bin/env python3
"""MANGABD-009 B2.1 Phase A — orientation-polish measurement instrument.

Docs-only Phase A (NO source changes): quantifies the four B2.1 scope
items on the COMMITTED archives (samples/S009_diagonal, S010_burst,
S011_manhwa_ui + the corpus finals) so the Owner/PM ruling has numbers.

M1 — asymmetric-block parity census (RF-18 residual class)
      * count rows where lines_layout != lines_GT per archive
      * current vjust empirics: rendered band pitch vs GT spacing
        (what the RF-18 vjust stretch actually produced), rendered
        band count, GT band count
      * COUNTERFACTUAL: re-place the rendered per-line ink clusters
        at the GT band centers (3 placement strategies) in the GT
        deskew frame, re-measure the cloud angle — does band-center
        mirroring force rendered-ink parity even at ±1 wrap-count
        miss?  (pure geometry, no font, no re-render)

M2 — render_page blank-save exposure
      * corpus finals scan (all committed samples/*/final.jpg)
      * translation-row renderable classification per B2 archive
      * reachability conditions enumerated from the committed bytes
        (cited to cell/line), incl. the RF-14 Flash G3 live-proven
        fresh-blank-save event class

M3 — ring-margin failure rate (RF-16 rung-2 robustness)
      * verbatim extract of cell-6 `_estimate_region_angle`
        (L999-1155, parametrized ONLY in _B2_RING_MARGIN) run on the
        archived originals per region at margins {4, 6, 10, 16, 24}
      * failure = estimator misses the tilt (returns 0.0) or |est -
        gt_beta| > 2 deg; classified burst vs tilted(ellipse) vs ui
      * rung-1 coverage census (detections.json b2_gt_* presence)

Laws reused verbatim (cited):
  * visible_ink: |final_gray - inpainted_gray| > 24
    (scripts/m009_b2_rf18_verify.py L254-257 — the committed parity
    table's own rendered-ink law)
  * band law: v-histogram + [1,2,3,2,1] smooth + 0.12*peak threshold
    + <2 merge  (cell-06 L1295-1330, `_b2_mask_orientation`)
  * ring-aware isolation + PCA + band/snap/dev law: cell-06
    L999-1155 `_estimate_region_angle`

Run:  python3 scripts/m009_b2_1_polish_measure.py
Reads only committed artifacts; writes
scripts/m009_b2_1_polish_measure_results.json (deterministic).
"""
import cv2
import json
import numpy as np
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SAMP = REPO / "samples"
ARCHIVES = ("S009_diagonal", "S010_burst", "S011_manhwa_ui")
TILTED_CLASSES = ("tilted", "burst", "ui", "ui_dark")
MARGINS = (4, 6, 10, 16, 24)      # 6 = current _B2_RING_MARGIN (cell-06 L996)
GT_TOL = 2.0                       # B2.1 goal: rendered/est within 2 deg of GT


# ───────────────────────── shared measurement laws ─────────────────────────

def visible_ink(final_bgr, inpainted_bgr):
    """Rendered-ink law — verbatim from m009_b2_rf18_verify.py L254-257."""
    f = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2GRAY).astype(np.int16)
    i = cv2.cvtColor(inpainted_bgr, cv2.COLOR_BGR2GRAY).astype(np.int16)
    return np.abs(f - i) > 24


def band_centers(v_vals, lo, hi):
    """Row-profile band law — cell-06 L1295-1330 (`_b2_mask_orientation`).

    Returns (band_centers, band_weights)."""
    if hi - lo < 4.0:
        return [float(np.mean(v_vals))] if len(v_vals) else [], []
    nb = max(8, int((hi - lo) // 2) + 1)
    hist, _ = np.histogram(v_vals, bins=nb, range=(lo, hi))
    k = np.array([1.0, 2.0, 3.0, 2.0, 1.0])
    sm = np.convolve(hist, k / k.sum(), mode="same")
    peak = float(sm.max())
    if peak <= 0:
        return [], []
    thr = max(0.5, 0.12 * peak)
    bands, s = [], None
    for i, val in enumerate(sm):
        if val >= thr and s is None:
            s = i
        elif val < thr and s is not None:
            bands.append([s, i])
            s = None
    if s is not None:
        bands.append([s, len(sm)])
    merged = []
    for b in bands:
        if merged and b[0] - merged[-1][1] < 2:
            merged[-1] = [merged[-1][0], b[1]]
        else:
            merged.append(b)
    binw = (hi - lo) / nb
    centers, weights = [], []
    for bs, be in merged:
        w = sm[bs:be]
        tot = float(w.sum())
        if tot <= 0:
            centers.append(lo + (bs + be) / 2.0 * binw)
        else:
            idx = np.arange(bs, be)
            centers.append(lo + float((idx * w).sum() / tot + 0.5) * binw)
        weights.append(float(hist[bs:be].sum()))
    return centers, weights


def cloud_angle(xs, ys):
    """minAreaRect long-side tilt, folded to (-90, 90] — cell-06 law."""
    if len(xs) < 10:
        return None
    pts = np.stack([xs.astype(np.float32), ys.astype(np.float32)], axis=1)
    box = cv2.boxPoints(cv2.minAreaRect(pts))
    d01, d03 = box[1] - box[0], box[3] - box[0]
    dlong = d01 if np.linalg.norm(d01) >= np.linalg.norm(d03) else d03
    t = float(np.degrees(np.arctan2(dlong[1], dlong[0])))
    tilt = (t + 180.0) % 180.0
    if tilt > 90.0:
        tilt -= 180.0
    return tilt


def deskew_mask(mask_bool, angle_deg):
    """Rotate a boolean page mask by -angle (PIL rotate(angle) inverse)."""
    m = (mask_bool.astype(np.uint8)) * 255
    h, w = m.shape
    M = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), float(angle_deg), 1.0)
    cos, sin = abs(M[0, 0]), abs(M[0, 1])
    nw = int(h * sin + w * cos) + 1
    nh = int(h * cos + w * sin) + 1
    M[0, 2] += nw / 2.0 - w / 2.0
    M[1, 2] += nh / 2.0 - h / 2.0
    rot = cv2.warpAffine(m, M, (nw, nh), flags=cv2.INTER_NEAREST)
    return rot > 0


# ───────── M3: verbatim extract of cell-06 `_estimate_region_angle` ─────────
# (L999-1155; ONLY delta = _B2_RING_MARGIN is a function argument here.)

def estimate_region_angle(image_bgr, x, y, w, h, ring_margin):
    """cell-06 `_estimate_region_angle` verbatim (margin parametrized)."""
    if w < 90 and h > 2 * max(1, w):            # V-3 predicate (L1000-1001)
        return 0.0, None
    H, W = image_bgr.shape[:2]
    x1, y1 = max(0, x - 2), max(0, y - 2)
    x2, y2 = min(W, x + w + 2), min(H, y + h + 2)
    if x2 - x1 < 8 or y2 - y1 < 8:
        return 0.0, None
    crop = image_bgr[y1:y2, x1:x2]

    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    ink = (gray < 100).astype(np.uint8) * 255
    if int(ink.sum() // 255) < 30:
        _otsu, _ = cv2.threshold(
            gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        ink = (gray < max(int(_otsu), 40)).astype(np.uint8) * 255
    _nl, _lab, _st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    if _nl > 1:
        _keep = np.zeros_like(ink)
        for _ci in range(1, _nl):
            if _st[_ci, cv2.CC_STAT_AREA] >= 6:
                _keep[_lab == _ci] = 255
        if int(_keep.sum() // 255) >= 30:
            ink = _keep

    # RF-16 ring-aware isolation (L1049-1068) — margin parametrized
    _light = (ink == 0)
    _ff = np.pad(_light, 1, constant_values=True).astype(np.uint8)
    _ffmask = np.zeros((_ff.shape[0] + 2, _ff.shape[1] + 2), np.uint8)
    cv2.floodFill(_ff, _ffmask, (0, 0), 2)
    _outside = (_ff == 2)[1:-1, 1:-1]
    _kern = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE, (2 * ring_margin + 1, 2 * ring_margin + 1))
    _enclosed = (ink > 0) & (cv2.dilate(
        _outside.astype(np.uint8), _kern) == 0)
    enclosed_px = int(_enclosed.sum())
    total_ink_px = int((ink > 0).sum())
    if enclosed_px >= 100:
        ink = _enclosed.astype(np.uint8) * 255

    ys, xs = np.nonzero(ink)
    if len(xs) < 100:
        return 0.0, None
    if len(xs) > 60000:
        _sel = np.random.default_rng(42).choice(len(xs), 60000, replace=False)
        xs, ys = xs[_sel], ys[_sel]
    pts = np.stack(
        [xs.astype(np.float64), ys.astype(np.float64)], axis=1)

    centered = pts - pts.mean(axis=0)
    cov = centered.T @ centered / len(pts)
    ev, evec = np.linalg.eigh(cov)
    if ev[1] <= 0:
        return 0.0, None
    aniso = float(ev[0] / ev[1])
    theta_cw = float(np.degrees(np.arctan2(evec[1, 1], evec[0, 1])))

    tilt = (theta_cw + 180.0) % 180.0
    if tilt > 90.0:
        tilt -= 180.0
    a = abs(tilt)
    if a < 5.0 or a >= 85.0:
        return 0.0, None
    if aniso > 0.70:
        return 0.0, None

    _p32 = np.stack(
        [xs.astype(np.float32), ys.astype(np.float32)], axis=1)
    _box = cv2.boxPoints(cv2.minAreaRect(_p32))
    _d01 = _box[1] - _box[0]
    _d03 = _box[3] - _box[0]
    _d = _d01 if np.linalg.norm(_d01) >= np.linalg.norm(_d03) else _d03
    t_mar = (float(np.degrees(np.arctan2(_d[1], _d[0]))) + 180.0) % 180.0
    if t_mar > 90.0:
        t_mar -= 180.0
    _dist = abs(t_mar - tilt) % 180.0
    _dist = min(_dist, 180.0 - _dist)
    if _dist > 10.0:
        return 0.0, None

    dev = tilt - 90.0 * round(tilt / 90.0)
    if abs(dev) < 5.0:
        return 0.0, None
    pil_angle = round(-dev, 2)
    return pil_angle, dict(enclosed_px=enclosed_px,
                           total_ink_px=total_ink_px, aniso=round(aniso, 3))


# ───────────────────────────────── M1 ─────────────────────────────────

def m1_asymmetric(sample_dir, det_rows, parity_rows):
    """Asymmetric-block census + vjust empirics + counterfactual placement."""
    final = cv2.imread(str(sample_dir / "final.jpg"), cv2.IMREAD_COLOR)
    inp = cv2.imread(str(sample_dir / "inpainted.png"), cv2.IMREAD_COLOR)
    tmask = cv2.imread(str(sample_dir / "text_mask.png"), cv2.IMREAD_GRAYSCALE)
    vink = visible_ink(final, inp)
    det_by_id = {int(r["id"]): r for r in det_rows}
    par_by_id = {int(r["id"]): r for r in parity_rows}
    out = []

    for rid, r in sorted(det_by_id.items()):
        p = par_by_id.get(rid)
        if p is None or p.get("class") not in TILTED_CLASSES:
            continue
        if p.get("b2_gt_lines") is None and r.get("b2_gt_lines") is None:
            continue
        x, y, w, h = (int(r[k]) for k in ("x", "y", "width", "height"))
        stored = float(r.get("angle", 0.0))
        gt_lines = int(p.get("lines_gt") or r.get("b2_gt_lines") or 0)
        lay_lines = p.get("lines_layout")
        if lay_lines is None:
            continue

        # GT frame = undo the renderer's PIL rotate(stored).
        # PIL rotate(a) is visual-CCW by a == OpenCV getRotationMatrix2D(-a)
        # (y-down frame), so the inverse (deskew) is OpenCV angle +stored.
        # stored == GT within 0.5 deg on every archived row (parity A1
        # max dev 0.35 deg).  Sign validated in-run: deskewed rendered
        # cloud angle == parity rendered_ink_deg - stored (parDev).
        pad = 8
        x1, y1 = max(0, x - pad), max(0, y - pad)
        x2, y2 = min(tmask.shape[1], x + w + pad), min(tmask.shape[0], y + h + pad)

        gmask_d = deskew_mask(tmask[y1:y2, x1:x2] > 0, -stored)
        rink_d = deskew_mask(vink[y1:y2, x1:x2], -stored)

        gys, gxs = np.nonzero(gmask_d)
        rys, rxs = np.nonzero(rink_d)

        # GT bands (dilated mask: band structure intact at ~40px spacing
        # vs 12px dilation swelling — disclosed)
        if len(gys) > 30:
            gc, gw = band_centers(gys.astype(np.float64),
                                  float(gys.min()), float(gys.max()))
        else:
            gc, gw = [], []
        # rendered bands
        if len(rys) > 30:
            rc, rw = band_centers(rys.astype(np.float64),
                                  float(rys.min()), float(rys.max()))
        else:
            rc, rw = [], []

        # current deviation: cloud angle of rendered ink in GT frame
        cur_dev = cloud_angle(rxs, rys) if len(rxs) > 30 else None
        # control: GT cloud angle in the same frame (method validation —
        # the GT text was drawn at gt_beta and stored == gt within 0.5
        # deg, so the deskewed GT cloud must measure ~0)
        gt_cloud_dev = cloud_angle(gxs, gys) if len(gxs) > 30 else None

        # vjust empirics: rendered band pitch vs GT spacing
        gt_sp = float(r.get("b2_gt_spacing") or 0.0)
        pitch = float(np.median(np.diff(rc))) if len(rc) >= 2 else None

        # ── counterfactual: re-place rendered line clusters at GT centers
        cf = {}
        if len(rc) >= 1 and len(gc) >= 1 and len(rxs) > 30:
            # split rendered ink into per-band clusters (band membership
            # by v-coordinate), each cluster kept rigid (u coords fixed)
            lo, hi = float(rys.min()), float(rys.max())
            edges = [-1] + [int((rc[i] + rc[i + 1]) / 2.0)
                            for i in range(len(rc) - 1)] + [10 ** 9]
            clusters = []       # (u array, v array)
            for i in range(len(rc)):
                sel = (rys >= edges[i] + (1 if i else 0)) & (rys <= edges[i + 1])
                if sel.sum() >= 5:
                    clusters.append((rxs[sel], rys[sel]))

            def place(targets):
                if len(clusters) != len(targets):
                    return None
                px, py = [], []
                for (cu, cv_), tc in zip(clusters, targets):
                    shift = tc - float(np.mean(cv_))
                    px.append(cu)
                    py.append(cv_ + shift)
                return (np.concatenate(px), np.concatenate(py))

            n, m = len(clusters), len(gc)
            strategies = {}
            # S1 block-height parity: spread over GT band extremes
            if n >= 2:
                strategies["S1_endpoints"] = [
                    gc[0] + (gc[-1] - gc[0]) * i / (n - 1)
                    for i in range(n)]
            elif n == 1 and m >= 1:
                strategies["S1_endpoints"] = [(gc[0] + gc[-1]) / 2.0]
            # S2 proportional quantile map onto GT bands
            if n >= 2 and m >= n:
                strategies["S2_proportional"] = [
                    gc[int(round(i * (m - 1) / (n - 1)))]
                    for i in range(n)]
            elif n == 1 and m >= 1:
                strategies["S2_proportional"] = [gc[(m - 1) // 2]]
            # S3 weight-matched: n largest GT bands, kept in v-order
            if m >= n >= 1:
                order = sorted(int(o) for o in
                               np.argsort(gw)[::-1][:n])
                strategies["S3_weightmatched"] = [gc[o] for o in order]
            # S4 spacing parity: pitch == GT spacing, centered on the
            # GT ink centroid (the "smarter line-spacing justification"
            # candidate: no band mirroring, just forced pitch)
            if n >= 2 and len(gys) > 0:
                gmid = float(np.mean(gys))
                strategies["S4_spacing"] = [
                    gmid + (i - (n - 1) / 2.0) * gt_sp
                    for i in range(n)] if gt_sp > 0 else None
                if strategies["S4_spacing"] is None:
                    del strategies["S4_spacing"]
            for name, targets in strategies.items():
                placed = place(targets)
                if placed is not None:
                    cf[name] = cloud_angle(placed[0], placed[1])

            # ── B_balance: horizontal extent-balancing counterfactual.
            # Scale each cluster's u-extent about its u-center to a
            # target max/min ratio (1.0 = equal line lengths, 1.5 =
            # soft balance); v placement UNCHANGED (current).  Tests
            # whether wrap-balancing — not spacing — is the lever that
            # moves the re-measured cloud angle.
            if n >= 2:
                exts = [float(cu.max() - cu.min() + 1)
                        for cu, _ in clusters]
                for ratio, key in ((1.0, "B10_equal_extents"),
                                   (1.5, "B15_ratio_1p5")):
                    tgt = max(exts) / ratio
                    px, py = [], []
                    for cu, cvv in clusters:
                        ext = float(cu.max() - cu.min() + 1)
                        if ext < tgt and ext > 0:
                            c = float(cu.mean())
                            cu = c + (cu - c) * (tgt / ext)
                        px.append(cu)
                        py.append(cvv)
                    cf[key] = cloud_angle(np.concatenate(px),
                                          np.concatenate(py))

        out.append({
            "id": rid, "tag": p.get("tag"), "class": p.get("class"),
            "stored": stored, "gt_beta": p.get("gt_beta_deg"),
            "lines_gt": gt_lines, "lines_layout": lay_lines,
            "lines_post": p.get("lines_post_remeasured"),
            "asymmetric": bool(lay_lines != gt_lines),
            "cur_reink_dev": (None if cur_dev is None
                              else round(cur_dev, 2)),
            "gt_cloud_dev": (None if gt_cloud_dev is None
                             else round(gt_cloud_dev, 2)),
            "par_reink_dev": (None if p.get("rendered_ink_deg") is None
                              else round(p["rendered_ink_deg"] - stored, 2)),
            "gt_bands": len(gc), "rend_bands": len(rc),
            "gt_spacing": gt_sp,
            "rend_pitch": (None if pitch is None else round(pitch, 2)),
            "vjust_stretch": (None if pitch is None or not gt_sp
                              else round(pitch / gt_sp, 2)),
            "counterfactual_dev": {k: (None if v is None else round(v, 2))
                                   for k, v in cf.items()},
            "extent_ratio": p.get("extent_ratio"),
        })
    return out


# ───────────────────────────────── M2 ─────────────────────────────────

def m2_blank_save():
    """Corpus finals scan + row classification + reachability census."""
    scans = []
    for fdir in sorted(SAMP.iterdir()):
        fj = fdir / "final.jpg"
        if not fj.exists():
            continue
        g = cv2.imread(str(fj), cv2.IMREAD_GRAYSCALE)
        ink_px = int((g < 200).sum())
        scans.append({
            "sample": fdir.name,
            "ink_px": ink_px,
            "blank": ink_px == 0,
            "near_blank_frac": round(float((g >= 200).mean()), 4),
        })
    rows_cls = {}
    for s in ARCHIVES:
        t = json.load(open(SAMP / s / "translation.json"))
        rows = t if isinstance(t, list) else []
        cls = {"rows": len(rows), "with_text": 0, "marker": 0,
               "bengali_valid": 0, "renderable_guess": 0}
        for r in rows:
            txt = str(r.get("translated_text", "") or "").strip()
            if txt:
                cls["with_text"] += 1
                if txt.startswith("[") and txt.endswith("]"):
                    cls["marker"] += 1
                elif r.get("bengali_valid"):
                    cls["bengali_valid"] += 1
                    if int(r.get("width", 0) or 0) >= 5 if "width" in r else True:
                        cls["renderable_guess"] += 1
        rows_cls[s] = cls
    return {
        "corpus_finals": scans,
        "blank_rate": f"{sum(1 for s in scans if s['blank'])}/{len(scans)}",
        "translation_rows": rows_cls,
        "reachability": {
            "save_line": "cell-10 L1996: save_image_artifact(page_id,'final',...) UNCONDITIONAL",
            "mark_done_line": "cell-10 L2036: mark_stage_done(page_id,'render',meta) UNCONDITIONAL",
            "rendered0_conditions": [
                "translation_df empty for the page (cell-10 L1746-47 prints warning, still saves)",
                "all rows special-marker / non-Bengali -> skipped_count only",
                "every row raises in the render loop (cell-10 L1989-92 WARN swallow)",
            ],
            "guard_covers": "RESUME half only (_b2_blank_cache_stale cell-10 L1614/L1696)",
            "live_proven_event": "RF-14 Flash G3 fd8d625 arm: blank saved+marked, per-region ink 0/0/0/0/0/0, meta rendered=0 (committed report 84aa238)",
        },
    }


# ───────────────────────────────── M3 ─────────────────────────────────

def m3_ring_margin():
    """Rung-2 estimator sweep over margins, per region class."""
    out = {}
    for s in ARCHIVES:
        orig = cv2.imread(str(SAMP / s / "original.jpg"), cv2.IMREAD_COLOR)
        det = json.load(open(SAMP / s / "detections.json"))
        par = {int(r["id"]): r for r in
               json.load(open(SAMP / s / "rf18_parity.json"))["rows"]}
        rows = []
        rung1 = 0
        tilted = 0
        for r in det:
            p = par.get(int(r["id"]))
            if p is None or p.get("class") not in TILTED_CLASSES:
                continue
            tilted += 1
            if r.get("b2_gt_lines") is not None:
                rung1 += 1
            x, y, w, h = (int(r[k]) for k in ("x", "y", "width", "height"))
            gt = float(p["gt_beta_deg"])
            sweep = {}
            for m in MARGINS:
                est, info = estimate_region_angle(orig, x, y, w, h, m)
                miss = abs(est) < 0.01           # estimator returned 0.0
                dev = None if miss else round(est - gt, 2)
                sweep[m] = {
                    "est": est,
                    "miss": bool(miss),
                    "fail": bool(miss or abs(est - gt) > GT_TOL),
                    "dev": dev,
                    "enclosed_px": (info or {}).get("enclosed_px"),
                    "total_ink_px": (info or {}).get("total_ink_px"),
                }
            rows.append({
                "id": r["id"], "tag": p.get("tag"), "class": p.get("class"),
                "gt": gt, "stored": float(r.get("angle", 0.0)),
                "rung1": r.get("b2_gt_lines") is not None,
                "sweep": sweep,
            })
        out[s] = {"rows": rows, "rung1_coverage": f"{rung1}/{tilted}"}
    return out


# ───────────────────────────────── main ─────────────────────────────────

def main():
    report = {"m1": {}, "m2": None, "m3": None}
    print("═══ M1 — asymmetric-block census + vjust + counterfactual ═══")
    for s in ARCHIVES:
        det = json.load(open(SAMP / s / "detections.json"))
        par = json.load(open(SAMP / s / "rf18_parity.json"))["rows"]
        rows = m1_asymmetric(SAMP / s, det, par)
        report["m1"][s] = rows
        asym = [r for r in rows if r["asymmetric"]]
        print(f"\n{s}: {len(rows)} tilted rows, {len(asym)} ASYMMETRIC "
              f"(lines_layout != lines_GT)")
        print(f"  {'tag':>4s} {'gt':>5s} {'stored':>7s} {'lGT':>3s} {'lay':>3s}"
              f" {'curDev':>6s} {'gtCtl':>6s} {'parDev':>6s} {'pitch':>6s} {'str':>5s}"
              f" {'extR':>5s} {'B10':>6s} {'B15':>6s}  vplacement-insensitivity")
        for r in rows:
            cf = r["counterfactual_dev"]
            vstrats = [v for k, v in cf.items()
                       if k.startswith(("S1", "S2", "S3", "S4"))
                       and v is not None]
            vsens = (f"{max(vstrats) - min(vstrats):.3f}"
                     if len(vstrats) >= 2 else "-")
            print(f"  {str(r['tag']):>4s} {r['gt_beta']:>5} {r['stored']:>7}"
                  f" {r['lines_gt']:>3d} {r['lines_layout']:>3d}"
                  f" {str(r['cur_reink_dev']):>6s} {str(r['gt_cloud_dev']):>6s}"
                  f" {str(r['par_reink_dev']):>6s}"
                  f" {str(r['rend_pitch']):>6s} {str(r['vjust_stretch']):>5s}"
                  f" {str(r['extent_ratio']):>5s}"
                  f" {str(cf.get('B10_equal_extents')):>6s}"
                  f" {str(cf.get('B15_ratio_1p5')):>6s}  {vsens}")

    print("\n═══ M2 — blank-save exposure ═══")
    report["m2"] = m2_blank_save()
    m2 = report["m2"]
    print(f"corpus finals blank rate: {m2['blank_rate']}")
    for s, c in m2["translation_rows"].items():
        print(f"  {s}: rows={c['rows']} with_text={c['with_text']} "
              f"bengali_valid={c['bengali_valid']}")
    print("  reachability: fresh blank-save STILL possible "
          "(save L1996 + mark L2036 unconditional) — RF-14 guard covers "
          "the resume half only")

    print("\n═══ M3 — ring-margin sweep (rung-2, margin parametrized) ═══")
    report["m3"] = m3_ring_margin()
    for s, blk in report["m3"].items():
        print(f"\n{s}: rung-1 coverage {blk['rung1_coverage']}")
        print(f"  {'tag':>4s} {'cls':>7s} {'gt':>6s}" +
              "".join(f"  m{m:<2d}" for m in MARGINS))
        for r in blk["rows"]:
            cells = ""
            for m in MARGINS:
                sw = r["sweep"][m]
                cells += f"  {'MISS' if sw['miss'] else str(sw['dev']):>5s}"
            print(f"  {str(r['tag']):>4s} {r['class']:>7s} {r['gt']:>6}"
                  + cells)

    dest = Path(__file__).resolve().parent / "m009_b2_1_polish_measure_results.json"
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print(f"\nreport → {dest.name}")

    # headline summary
    print("\n═══ HEADLINES ═══")
    for s in ARCHIVES:
        rows = report["m1"][s]
        asym = [r for r in rows if r["asymmetric"]]
        over2 = [r for r in rows
                 if r["cur_reink_dev"] is not None
                 and abs(r["cur_reink_dev"]) > GT_TOL]
        b10 = [abs(r["counterfactual_dev"].get("B10_equal_extents"))
               for r in rows
               if r["counterfactual_dev"].get("B10_equal_extents") is not None]
        b15 = [abs(r["counterfactual_dev"].get("B15_ratio_1p5"))
               for r in rows
               if r["counterfactual_dev"].get("B15_ratio_1p5") is not None]
        print(f"  {s}: asym={len(asym)}/{len(rows)}, |curDev|>2deg: {len(over2)};"
              f" balance-cf max|dev| B10={max(b10) if b10 else None}"
              f" B15={max(b15) if b15 else None}")
    for s, blk in report["m3"].items():
        for m in MARGINS:
            fails = sum(1 for r in blk["rows"] if r["sweep"][m]["fail"])
            print(f"  {s} margin={m:2d}: rung-2 fails {fails}/{len(blk['rows'])}")


if __name__ == "__main__":
    main()
