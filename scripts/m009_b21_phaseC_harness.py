#!/usr/bin/env python3
"""MANGABD-009 B2.1 Phase C — battery harness: run the pipeline cells
VERBATIM from the working-tree notebook and report the cell-10 battery
result incl. the new Test 22.

Env-level stubs (cell source bytes stay VERBATIM) — same disclosed set
as the RF-14 harness (scripts/m009_b2_rf14_repro.py):
  * torch  : inert stub module (no CUDA) — RT-DETR inference is not
             exercised by the battery; cells need import +
             @torch.no_grad().
  * pathlib: /content* and /root* paths remapped to <HARNESS>/content*
             via a Path subclass installed only during cell exec.
  * cell_00 (env doctor / Colab pip bootstrap): NOT exec'd; its runtime
             side effects (MANGABD_ENV report + safe env vars) seeded.
  * fonts : the m008 probe fonts copied into the remapped content dir.
  * cell_23 NOT exec'd (it serves the Owner-session render flow, not
             the battery — disclosed difference vs the RF-14 set).

Cell set: 01, 02, 03, 04, 05, 06, 07, 10. cell_04's zyddnys torch-only
import failures are tolerated under the RF-14 disclosed rule (CTD/LaMa
are inpaint deps, out of the render path; font/raqm/Bengali tests must
be green).

Output markers (parsed by scripts/m009_b21_phaseC_verify.py):
  CELL10_RESULT: SUCCESS|NEEDS FIX
  TEST22: PASS|FAIL   TEST19: PASS|FAIL   TEST21: PASS|FAIL
  BATTERY_EVENTS: tests_passed=N tests_total=N tests_skipped=N
                  tests_diagnosed=N
"""
import contextlib
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import types
from pathlib import PosixPath, PurePosixPath, Path as _RealPath

ROOT = _RealPath("/home/z/my-project")
REPO = ROOT / "MangaBD"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
FONTS = ROOT / "m008_probe" / "fonts"
HARNESS = ROOT / "b21_home"
CELLS_WORK = ROOT / "cells_b21_fix"
CELL_IDS = [1, 2, 3, 4, 5, 6, 7, 10]


def log(msg):
    print(f"[b21-harness] {msg}", flush=True)


def make_torch_stub():
    """Inert torch: import-only + @torch.no_grad() decorator passthrough."""
    stub = types.ModuleType("torch")

    class _NoGradCtx:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    def no_grad(fn=None):
        if fn is not None:
            return fn

        def deco(f):
            return f
        return deco

    stub.no_grad = no_grad
    stub.Tensor = object
    stub.tensor = None
    stub.float16 = "float16"
    stub.float32 = "float32"
    cuda = types.ModuleType("torch.cuda")
    cuda.is_available = lambda: False
    cuda.empty_cache = lambda: None
    cuda.synchronize = lambda: None
    stub.cuda = cuda
    stub.__getattr__ = lambda name: (_ for _ in ()).throw(
        AttributeError(f"torch-stub: {name} unavailable"))
    return stub


def _rewrite_content(a0):
    """Colab-only absolute roots -> <HARNESS>/... (cells stay verbatim)."""
    for prefix in ("/content", "/root"):
        if isinstance(a0, str) and a0.startswith(prefix):
            return str(HARNESS / a0[len(prefix):].lstrip("/"))
        if isinstance(a0, PurePosixPath):
            s = str(a0)
            for prefix in ("/content", "/root"):
                if s.startswith(prefix):
                    return str(HARNESS / s[len(prefix):].lstrip("/"))
    return None


class ShimPath(PosixPath):
    """Real PosixPath subclass; absolute /content* -> <HARNESS>/content*."""

    def __init__(self, *args, **kw):
        if args:
            fixed = _rewrite_content(args[0])
            if fixed is not None:
                args = (fixed,) + tuple(args[1:])
        super().__init__(*args, **kw)


def install_pathlib_shim():
    proxy = types.ModuleType("pathlib_shim")
    import pathlib as real_pathlib
    proxy.__dict__.update(real_pathlib.__dict__)
    proxy.Path = ShimPath
    proxy.PosixPath = ShimPath
    sys.modules["pathlib_shim_saved"] = real_pathlib
    sys.modules["pathlib"] = proxy
    return proxy


def restore_pathlib():
    saved = sys.modules.pop("pathlib_shim_saved", None)
    if saved is not None:
        sys.modules["pathlib"] = saved


def seed_cell00_side_effects(ns):
    from PIL import features as _feat
    ns["MANGABD_ENV"] = {
        "version": "12.0.0",
        "timestamp": "b21-harness",
        "python": sys.version.split()[0],
        "platform": sys.platform,
        "cuda_available": False,
        "gpu_name": None,
        "gpu_memory_gb": None,
        "torch_version": "stub",
        "pip_ok": True,
        "libraqm_ok": bool(_feat.check("raqm")),
        "critical_imports": {"harness": True},
        "errors": [],
        "warnings": [],
    }
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["MANGABD_VERSION"] = "12.0.0"


def exec_cells(cell_dir):
    ns = {"__name__": "__mangabd__"}
    logs = {}
    seed_cell00_side_effects(ns)
    install_pathlib_shim()
    try:
        for cid in CELL_IDS:
            src = (cell_dir / f"cell_{cid:02d}.py").read_text(encoding="utf-8")
            code = compile(src, f"cell_{cid:02d}.py", "exec")
            buf = io.StringIO()
            log(f"exec cell_{cid:02d} ({len(src)} bytes) ...")
            try:
                with contextlib.redirect_stdout(buf):
                    exec(code, ns)
            except RuntimeError as exc:
                # DISCLOSED tolerance, cell_04 only (RF-14 rule): the inert
                # torch stub cannot feed the zyddnys import chain (CTD /
                # LaMa = inpaint deps, out of the render path under test).
                txt = buf.getvalue()
                fail_lines = [ln for ln in txt.splitlines() if "❌" in ln]
                zyddnys_only = fail_lines and all(
                    ("ComicTextDetector" in ln or "LamaLargeInpainter" in ln)
                    for ln in fail_lines
                )
                render_green = all(
                    marker in txt for marker in (
                        "Bengali font render test passed",
                        "libraqm available",
                        "Bengali render test",
                    )
                )
                if (cid == 4 and "Cell 4 self-tests failed" in str(exc)
                        and zyddnys_only and render_green):
                    log("cell_04: env-limited zyddnys torch-imports only "
                        "(torch stub; CTD/LaMa = inpaint deps, out of "
                        "scope) — tolerated (DISCLOSED); font tests green")
                else:
                    raise
            logs[cid] = buf.getvalue()
            tail = [ln for ln in logs[cid].splitlines() if ln.strip()]
            log(f"cell_{cid:02d} done ({len(tail)} lines); tail: "
                f"{tail[-1][:100] if tail else '<empty>'}")
    finally:
        restore_pathlib()
    return ns, logs


def battery_report(ns, logs):
    c10 = logs[10]

    def test_line(key):
        for ln in c10.splitlines():
            if key in ln and ("✅" in ln or "❌" in ln):
                return "PASS" if "✅" in ln else "FAIL"
        return "ABSENT"

    result = "SUCCESS" if "Cell 10 result: SUCCESS" in c10 else "NEEDS FIX"
    print(f"CELL10_RESULT: {result}")
    print(f"TEST22: {test_line('B2.1 RB21-2/RB21-3: blank-render quarantine')}")
    print(f"TEST19: {test_line('B2 RF-14: blank-cache trap')}")
    print(f"TEST21: {test_line('B2 RF-18: original-ink orientation parity')}")

    ev = [e for e in ns.get("MANGABD_EVENTS", [])
          if str(e.get("message", "")).startswith("Cell 10 completed")]
    if ev:
        ex = ev[-1].get("extra", {})
        print(f"BATTERY_EVENTS: tests_passed={ex.get('tests_passed')} "
              f"tests_total={ex.get('tests_total')} "
              f"tests_skipped={ex.get('tests_skipped')} "
              f"tests_diagnosed={ex.get('tests_diagnosed')}")
    else:
        print("BATTERY_EVENTS: absent")

    # quarantine WARN + guard WARN evidence from the battery events
    qw = [e for e in ns.get("MANGABD_EVENTS", [])
          if "quarantined" in str(e.get("message", ""))]
    gw = [e for e in ns.get("MANGABD_EVENTS", [])
          if "guard raised" in str(e.get("message", ""))]
    print(f"EVENT_EVIDENCE: quarantine_warns={len(qw)} guard_warns={len(gw)}")


def main():
    if HARNESS.exists():
        shutil.rmtree(HARNESS)
    HARNESS.mkdir(parents=True)
    fonts_dir = HARNESS / "content" / "mangabd" / "fonts"
    fonts_dir.mkdir(parents=True)
    shutil.copy(FONTS / "NotoSansBengali-Regular.ttf",
                fonts_dir / "NotoSansBengali-Regular.ttf")
    shutil.copy(FONTS / "NotoSansBengali-Regular.ttf",
                fonts_dir / "NotoSansBengali-Bold.ttf")
    shutil.copy(FONTS / "NotoSansJP.ttf", fonts_dir / "NotoSansJP.ttf")

    raw = (REPO / NB_NAME).read_bytes()
    nb = json.loads(raw.decode("utf-8"))
    CELLS_WORK.mkdir(parents=True, exist_ok=True)
    for i, c in enumerate(nb["cells"]):
        src = "".join(c.get("source", []))
        (CELLS_WORK / f"cell_{i:02d}.py").write_text(src, encoding="utf-8")
    sha = hashlib.sha256(raw).hexdigest()
    log(f"extracted work cells: {len(nb['cells'])} -> {CELLS_WORK} "
        f"(blob sha {sha[:8]})")

    sys.modules["torch"] = make_torch_stub()
    ns, logs = exec_cells(CELLS_WORK)
    battery_report(ns, logs)
    log("battery-work complete")


if __name__ == "__main__":
    main()
