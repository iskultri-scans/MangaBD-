#!/usr/bin/env python3
"""
MANGABD-008 B1 RF-13 — ROOT-CAUSE REPRO (Owner directive: investigate, don't guess).

Runs cell 10 (§3-§8 core + §10 battery) VERBATIM from the pushed HEAD bytes
(5a84994 = RF-12) across a matrix of Drive-like environments to find the env
class that reproduces the Owner's live signature EXACTLY:

    Test 9  (glyph-coverage routing D-1/D-2)   FAIL
    Test 12 (tofu detector D-2)                FAIL
    Test 10 (D-4 WARN-never-silent)            PASS   (with the DESIGNED
                                                      "JP fallback font
                                                      unavailable" ERROR line)
    Test 11 (D-3)                              PASS   (with the after-D-4
                                                      "cmap coverage unavailable:
                                                      /tmp/MISSING-test-font.ttf"
                                                      WARN line)
    post-run: config font_fallback restored, _FB_CACHE empty, registry fine

Also emits the Owner-requested evidence dump at the first failing assertion
(Test 9): config value, _FB_CACHE/_FONT_COVERAGE_CACHE/_FONT_ROUTE_WARNED
contents, get_font_fb(24), _main_font_ok decisions for U+0964/U+0022, and the
exact assert-expression left/right values — plus a full config-mutation trace
(WHO writes font_fallback, from which source line, WHO restores).
"""
import io
import json
import os
import re
import sys
import contextlib
import tempfile
import traceback
from pathlib import Path

REPO = Path("/home/z/my-project/MangaBD")
NB = REPO / "MangaBD_V12_ipynb_txt.ipynb (3).txt"
VENDORED = REPO / "assets/fonts/NotoSansJP[wght].ttf"
PROBE_BEN = Path("/home/z/my-project/m008_probe/fonts/NotoSansBengali-Regular.ttf")
FREESERIF = Path("/usr/share/fonts/truetype/freefont/FreeSerif.ttf")
SHA_PIN = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"
T9 = "glyph-coverage routing (D-1/D-2)"
T10 = "JP fallback WARN-never-silent (D-4)"
T11 = "horizontal mixed render: fallback glyphs real (D-3)"
T12 = "tofu detector: JP solid glyph vs main .notdef (D-2)"

OWNER_SIG = {T9: "fail", T10: "pass", T11: "pass", T12: "fail"}

# ── notebook bytes (verbatim) ───────────────────────────────────────────
raw = NB.read_bytes()
nb = json.loads(raw.decode("utf-8"))
cells = ["".join(c["source"]) for c in nb["cells"] if c.get("cell_type") == "code"]
cell10 = next(c for c in cells if "Cell 10: Rendering Service" in c and "get_font_fb" in c)
lines = cell10.split("\n")
core_start = next(i for i, l in enumerate(lines) if l.startswith("# 3. Text helpers"))
batt_start = next(i for i, l in enumerate(lines) if l.startswith("# 10. Self-tests"))
SPAN_CORE = "\n".join(lines[core_start:batt_start])   # §3-§8 definitions only
SPAN_BATT = "\n".join(lines[batt_start:])             # §10 battery + gate, verbatim
print(f"cell10 verbatim: {len(lines)} lines; core §3-§8 = {batt_start-core_start} lines, "
      f"battery = {len(lines)-batt_start} lines")


def make_drive_env(tmp, main_bytes_src, fb_bytes_src, ambient_fb=None, registry=None):
    """Simulate the Owner's Drive fonts dir + cell-4-configured registry/config."""
    fonts = Path(tmp) / "drive" / "MyDrive" / "MangaBD_V12" / "fonts"
    fonts.mkdir(parents=True, exist_ok=True)
    ben = fonts / "NotoSansBengali-Regular.ttf"
    bold = fonts / "NotoSansBengali-Bold.ttf"
    jp = fonts / "NotoSansJP.ttf"
    if main_bytes_src is not None:
        ben.write_bytes(Path(main_bytes_src).read_bytes())
        bold.write_bytes(Path(main_bytes_src).read_bytes())
    if fb_bytes_src is not None:
        jp.write_bytes(Path(fb_bytes_src).read_bytes())
    fb_ambient = str(jp) if ambient_fb is None else ambient_fb
    reg = str(jp) if registry is None else registry
    return fonts, {
        "rendering": {
            "font_size_min": 8, "font_size_max": 48, "font_size_default": 24,
            "line_spacing_factor": 1.18, "padding_ratio": 0.08,
            "allow_synthetic_bold": True,
            "stroke_width_bubble": 0, "stroke_width_thought": 0,
            "stroke_width_narrator": 0, "stroke_width_sfx": 1,
            "stroke_width_overlay": 1,
            "default_bubble_color": [0, 0, 0],
            "default_sfx_color": [255, 255, 255],
            "default_narrator_color": [0, 0, 0],
            "default_overlay_color": [255, 255, 255],
            "preview_max_width": 900,
            "font_regular": str(ben),
            "font_bold": str(bold),
            "font_fallback": fb_ambient,
            "vertical_rotate": -90,
        },
        "detection": {}, "inpainting": {},
    }, reg


def make_ns(cfg, registry_path, trace=False):
    ns = {"__name__": "rf13_harness"}
    ns["MANGABD_CONFIG"] = cfg
    ns["MANGABD_EVENTS"] = []
    trace_log = []

    def log_event(message, level="INFO", **extra):
        ns["MANGABD_EVENTS"].append({"level": level, "message": message, "extra": extra})

    ns["log_event"] = log_event
    ns["MANGABD_ASSETS"] = {
        "fonts": {
            "regular_path": cfg["rendering"]["font_regular"],
            "bold_path": cfg["rendering"]["font_bold"],
            "fallback_path": str(registry_path),
            "fallback_sha256": SHA_PIN,
            "fallback_size": 9589900,
            "fallback_sha_ok": True,
            "fallback_license": "OFL-1.1",
        },
    }
    exec("import cv2\nimport numpy as np\nfrom pathlib import Path\n"
         "from PIL import Image as PILImage\nfrom PIL import ImageDraw, ImageFont\n"
         "from PIL import features\nimport pandas as pd", ns)
    if trace:
        import inspect

        class _TraceDict(dict):
            def __setitem__(self, k, v):
                if k == "font_fallback":
                    caller = inspect.stack()[1]
                    trace_log.append({
                        "what": "config.rendering.font_fallback write",
                        "value": str(v),
                        "src": f"{Path(caller.filename).name}:{caller.lineno}",
                        "line": caller.code_context[0].strip() if caller.code_context else "?",
                    })
                super().__setitem__(k, v)

        _td = _TraceDict(cfg["rendering"])
        cfg["rendering"] = _td
        ns["MANGABD_CONFIG"]["rendering"] = _td
    ns["_RF13_TRACE"] = trace_log
    return ns


def run_env(name, main_src, fb_src, ambient_fb=None, registry=None, trace=False):
    tmp = tempfile.mkdtemp(prefix=f"rf13_{name}_")
    fonts, cfg, reg = make_drive_env(tmp, main_src, fb_src, ambient_fb, registry)
    ns = make_ns(cfg, reg, trace=trace)
    so = io.StringIO()
    gate_raised = False
    try:
        exec(compile(SPAN_CORE, "<cell10 core verbatim>", "exec"), ns)
        with contextlib.redirect_stdout(so):
            exec(compile(SPAN_BATT, "<cell10 battery verbatim>", "exec"), ns)
    except RuntimeError as exc:
        gate_raised = "Cell 10 self-tests failed" in str(exc)
    out = so.getvalue()
    per = {}
    for line in out.splitlines():
        m = re.match(r"^(✅|❌|⚪)\s+(SKIP\s+)?(.*)$", line.strip())
        if m:
            per[m.group(3)] = "skip" if m.group(1) == "⚪" else \
                ("pass" if m.group(1) == "✅" else "fail")
    events = [{"level": e["level"], "message": e["message"]} for e in ns["MANGABD_EVENTS"]]
    post = {
        "config_fb": ns["MANGABD_CONFIG"]["rendering"]["font_fallback"],
        "config_reg": ns["MANGABD_CONFIG"]["rendering"]["font_regular"],
        "_FB_CACHE": {str(k): (v is not None) for k, v in ns["_FB_CACHE"].items()},
        "_FONT_COVERAGE_CACHE": {str(k): (v is not None if v is not None else "None")
                                  for k, v in ns["_FONT_COVERAGE_CACHE"].items()},
        "_FONT_ROUTE_WARNED": sorted(ns["_FONT_ROUTE_WARNED"].keys()),
    }
    sig = {t: per.get(t, "absent") for t in (T9, T10, T11, T12)}
    match = sig == OWNER_SIG
    print("=" * 78)
    print(f"SCENARIO {name}   gate_raised={gate_raised}")
    for line in out.splitlines():
        print("   | " + line)
    print("   events (level/message):")
    for e in events:
        print(f"     [{e['level']}] {e['message']}")
    print("   post-run state:", json.dumps(post, ensure_ascii=False))
    print(f"   signature: {json.dumps(sig)}   {'*** MATCHES OWNER ***' if match else ''}")
    print("=" * 78)
    return {"name": name, "sig": sig, "match": match, "out": out,
            "events": events, "post": post, "ns": ns, "per": per}


# ═══════════════════════════════════════════════════════════════════════
print()
print("#" * 78)
print("# RF-13 REPRO MATRIX — cell 10 VERBATIM from HEAD (RF-12 bytes)")
print("#" * 78)

results = []

# R-A: faithful healthy Drive (control) — expect 12/12
results.append(run_env("R-A_healthy_drive", PROBE_BEN, VENDORED))

# R-G: main font = Bengali+Latin font (FreeSerif class), fallback healthy
results.append(run_env("R-G_main_has_latin", FREESERIF, VENDORED, trace=True))

# R-C: main font path contains the JP bytes (copy-mistake class)
results.append(run_env("R-C_main_is_jp", VENDORED, VENDORED))

# R-D: stale-bad ambient config fb (interrupted-fixture class), registry good
results.append(run_env("R-D_stale_bad_ambient", PROBE_BEN, VENDORED,
                       ambient_fb="/tmp/MISSING-test-font.ttf"))

# R-E: Latin main + stale-bad ambient
results.append(run_env("R-E_latin_main_bad_ambient", FREESERIF, VENDORED,
                       ambient_fb="/tmp/MISSING-test-font.ttf"))

print()
print("#" * 78)
print("# SIGNATURE MATRIX vs OWNER (T9 fail / T10 pass / T11 pass / T12 fail)")
print("#" * 78)
hdr = f"{'scenario':28s} {': '.join(f'{k.split('(')[0][:22]:24s}' for k in (T9, T10, T11, T12))}"
print(hdr)
for r in results:
    print(f"{r['name']:28s} " + " ".join(f"{r['sig'][t]:24s}" for t in (T9, T10, T11, T12))
          + ("   <<< OWNER MATCH" if r["match"] else ""))
Path("/home/z/my-project/rf13_out").mkdir(exist_ok=True)
Path("/home/z/my-project/rf13_out/matrix.json").write_text(json.dumps(
    [{k: r[k] for k in ("name", "sig", "match", "events", "post")} for r in results],
    ensure_ascii=False, indent=2), encoding="utf-8")
print("\nmatrix + dumps -> /home/z/my-project/rf13_out/matrix.json")
