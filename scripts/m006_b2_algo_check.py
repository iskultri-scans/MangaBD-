#!/usr/bin/env python3
"""MANGABD-006 B2 pre-implementation check — directive algorithm vs archived geometry.

Directive spec (M6-B2 Phase C):
  1. horizontal center = x + width/2
  2. sort centers DESC (right-to-left); band boundary = gap between
     consecutive centers > median(gaps) * 1.5; single-column pages
     (no big gap): all regions in one band
  3. within band: y ASC
  4. final: band-1 (rightmost) top-to-bottom, then band-2, ...
Cross-checked against the Phase A x-interval connected-components
instrument (m006_phaseA_order.py) on S001/S003/S005 archived
detections.json. S003 gate: == VLM-confirmed R3->R2->R4->R5->R6->R1
(Kendall tau +1.000 reference).
"""
import json
import statistics

REPO = "/home/z/my-project/MangaBD/samples"


def kendall_tau(a, b):
    assert sorted(a) == sorted(b)
    n = len(a)
    pos = {v: i for i, v in enumerate(b)}
    seq = [pos[v] for v in a]
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            if seq[i] < seq[j]:
                conc += 1
            elif seq[i] > seq[j]:
                disc += 1
    return (conc - disc) / (conc + disc) if conc + disc else 1.0


def compute_reading_order_directive(regions):
    """Directive algorithm. Returns list of region ids in reading order."""
    if not regions:
        return []
    items = []
    for r in regions:
        x, y, w = int(r["x"]), int(r["y"]), int(r["width"])
        items.append({"id": int(r["id"]), "cx": x + w / 2.0, "y": y})
    if len(items) == 1:
        return [items[0]["id"]]
    # sort by center DESC (right-to-left)
    items.sort(key=lambda t: -t["cx"])
    # gaps between consecutive centers
    gaps = [items[i]["cx"] - items[i + 1]["cx"] for i in range(len(items) - 1)]
    med = statistics.median(gaps) if gaps else 0.0
    # bands: split where gap > median * 1.5
    bands = [[items[0]]]
    for i, g in enumerate(gaps):
        if med > 0 and g > med * 1.5:
            bands.append([items[i + 1]])
        else:
            bands[-1].append(items[i + 1])
    # within band: y ASC (stable, id ASC tie)
    order = []
    for band in bands:
        for r in sorted(band, key=lambda t: (t["y"], t["id"])):
            order.append(r["id"])
    return order


def compute_reading_order_phasea(regions):
    """Phase A instrument algorithm (x-interval connected components)."""
    boxes = []
    for r in regions:
        x, y, w, h = int(r["x"]), int(r["y"]), int(r["width"]), int(r["height"])
        boxes.append({"id": int(r["id"]), "x0": x, "x1": x + w, "y0": y,
                      "region_type": str(r.get("region_type", "bubble"))})
    n = len(boxes)
    parent = list(range(n))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if boxes[i]["x0"] < boxes[j]["x1"] and boxes[j]["x0"] < boxes[i]["x1"]:
                parent[find(i)] = find(j)
    bands = {}
    for i in range(n):
        bands.setdefault(find(i), []).append(boxes[i])
    ordered_bands = sorted(bands.values(),
                           key=lambda b: max(r["x1"] for r in b), reverse=True)
    result = []
    for band in ordered_bands:
        for r in sorted(band, key=lambda r: (r["y0"], -r["x0"])):
            result.append(r["id"])
    return result


VLM_CONFIRMED_S003 = [3, 2, 4, 5, 6, 1]

for sample in ["S001_color_webtoon", "S003_batch2", "S005_openrouter",
               "S002_batch1", "S005_manual"]:
    try:
        det = json.load(open(f"{REPO}/{sample}/detections.json"))
    except FileNotFoundError:
        print(f"  (skip {sample}: no detections.json)")
        continue
    geo = [(d["id"], int(d["x"]), int(d["y"]), int(d["width"]), int(d["height"]),
            d.get("region_type", "?")) for d in det]
    dir_order = compute_reading_order_directive(det)
    pa_order = compute_reading_order_phasea(det)
    det_order = [d["id"] for d in sorted(det, key=lambda r: int(r["id"]))]
    print(f"== {sample} ({len(det)} regions) ==")
    print("   geometry (id, x, y, w, h, type):")
    for g in geo:
        print(f"     R{g[0]}: x={g[1]:4d} y={g[2]:4d} w={g[3]:4d} h={g[4]:4d} cx={g[1]+g[3]/2:7.1f} type={g[5]}")
    print(f"   detection id order : {det_order}")
    print(f"   directive algo     : {dir_order}")
    print(f"   phase-A algo       : {pa_order}")
    agree = "EXACT" if dir_order == pa_order else "*** DIFFER ***"
    print(f"   directive vs phaseA: {agree}")
    if sample == "S003_batch2":
        print(f"   VLM-confirmed      : {VLM_CONFIRMED_S003}")
        print(f"   directive vs VLM   : EXACT={dir_order == VLM_CONFIRMED_S003} tau={kendall_tau(dir_order, VLM_CONFIRMED_S003):+.3f}")
        print(f"   phaseA   vs VLM   : EXACT={pa_order == VLM_CONFIRMED_S003} tau={kendall_tau(pa_order, VLM_CONFIRMED_S003):+.3f}")
        print(f"   id order vs VLM    : EXACT={det_order == VLM_CONFIRMED_S003} tau={kendall_tau(det_order, VLM_CONFIRMED_S003):+.3f}")
    print()
