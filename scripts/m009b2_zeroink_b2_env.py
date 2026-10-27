#!/usr/bin/env python3
"""MANGABD-009 B2 zero-ink repro — verbatim exec environment.

Builds a namespace with verbatim cell-1 (config/logger) + cell-3 (storage) +
cell-10 (render; TIP or BASE variant) + verbatim _estimate_region_angle /
sort_regions_by_reading_order slices from cell-6 (executed BEFORE cell-10 so
the production battery's B2 tests run for real).

Environment-only shims (all disclosed; zero B2-source involvement):
  * cell-0 (bootstrap) is NOT executed — it only pips/torches/raqms the
    Colab env. A faithful CPU MANGABD_ENV dict is pre-seeded instead
    (cell-1 raises without it). Identical bytes in base and tip.
  * a pathlib chroot maps /content/mangabd -> sandbox/<variant> during the
    exec of cells 1/3 (both byte-identical to base main — environment, not
    B2 source). Cells 6/10 slices run unshimmed.
"""
import io
import json
import sys
import pathlib
import pathlib as _pl
from contextlib import redirect_stdout

HERE = pathlib.Path("/home/z/my-project/m009b2_repro")
SANDBOX = HERE / "sandbox"

CHROOT_SRC = "/content/mangabd"


def _load_cells():
    nb = json.loads((HERE / "nb_tip.txt").read_text(encoding="utf-8"))

    def src(c):
        s = c["source"]
        return "".join(s) if isinstance(s, list) else s

    return [src(c) for c in nb["cells"]]


CELLS = _load_cells()


def _load_base_cells():
    nb = json.loads((HERE / "nb_base.txt").read_text(encoding="utf-8"))

    def src(c):
        s = c["source"]
        return "".join(s) if isinstance(s, list) else s

    return [src(c) for c in nb["cells"]]


CELLS_BASE = _load_base_cells()


def _slice_fn(cell_src, start_marker, end_marker):
    i = cell_src.index(start_marker)
    j = cell_src.index(end_marker)
    return cell_src[i:j]


class Chroot:
    """Patch pathlib.Path so /content/mangabd -> dst during with-block.

    Version-proof shim: Path is replaced by a metaclass instance whose
    __call__ constructs a REAL PosixPath at the remapped location and
    whose __instancecheck__/__subclasscheck__ delegate to the real Path.
    No pathlib internals are touched.
    """

    def __init__(self, dst):
        self.dst = str(dst)
        self._real = _pl.Path

    def __enter__(self):
        real = self._real
        dst = self.dst

        def remap(s):
            if s == CHROOT_SRC or s.startswith(CHROOT_SRC + "/"):
                return dst + s[len(CHROOT_SRC):]
            return s

        class _PathMeta(type):
            def __call__(cls, p="", *a, **k):
                if isinstance(p, str):
                    p = remap(p)
                elif isinstance(p, real):
                    p = remap(str(p))
                return real(p, *a, **k)

            def __instancecheck__(cls, inst):
                return isinstance(inst, real)

            def __subclasscheck__(cls, sub):
                return issubclass(sub, real)

            def __getattr__(cls, name):
                # class-level API (Path.cwd/home/...) -> real Path
                return getattr(real, name)

        class PathShim(metaclass=_PathMeta):
            pass

        PathShim.__name__ = "Path"
        self._patched = PathShim
        _pl.Path = PathShim
        return self

    def __exit__(self, *exc):
        _pl.Path = self._real
        return False


def _mangabd_assets_seed(ns, dst):
    """Cell-4 replacement for the sandbox (environment-only).

    Cell-4 needs torch + a zyddnys clone — live-env provisioning with zero
    B2 relevance. The only cell-10 dependency is MANGABD_ASSETS (battery
    Tests 14/15 vendored-JP probes). Seeded with the REAL vendored font
    bytes (repo assets/fonts, sha/size verified == the cell-4 pins) so the
    battery probes run against true bytes, not a stub.
    """
    real = _pl.Path
    vendored = real("/home/z/my-project/repo/assets/fonts/NotoSansJP[wght].ttf")
    import hashlib
    data = vendored.read_bytes()
    sha = hashlib.sha256(data).hexdigest()
    cfg = ns["MANGABD_CONFIG"]
    ns["MANGABD_ASSETS"] = {
        "zyddnys_repo": "/nonexistent/zyddnys-sandbox",
        "zyddnys_repo_exists": False,
        "patched_files": 0,
        "imports": {
            "ComicTextDetector": False,
            "LamaLargeInpainter": False,
            "Quadrilateral": False,
        },
        "fonts": {
            "regular_path": cfg["rendering"]["font_regular"],
            "bold_path": cfg["rendering"]["font_bold"],
            "regular_ok": real(cfg["rendering"]["font_regular"]).exists(),
            "bold_ok": real(cfg["rendering"]["font_bold"]).exists(),
            "regular_sane": True,
            "raqm_ok": bool(_raqm_ok()),
            "render_ok": True,
            "fallback_path": str(vendored),
            "fallback_sha256": sha,
            "fallback_size": len(data),
            "fallback_sha_ok": sha == ("c2f3b4d463500a2ddcd3849"
                                       "cded1fceeb9fd6d1c32e6cbecd5684"
                                       "53ba50fc68f"),
            "fallback_license": "OFL-1.1",
        },
    }
    cfg.setdefault("external", {})
    cfg["external"]["zyddnys_repo"] = ns["MANGABD_ASSETS"]["zyddnys_repo"]
    cfg["external"]["assets_ready"] = True
    # m008 cell-4 also pins the render fallback path into the config —
    # point it at the SAME sha-pinned bytes copied into the session fonts dir.
    cfg["rendering"].setdefault(
        "font_fallback", str(dst_fonts(ns, dst) / "NotoSansJP.ttf"))


def dst_fonts(ns, dst):
    return _pl.Path(dst) / "fonts"


def _raqm_ok():
    from PIL import features
    return bool(features.check("raqm"))


def build_env(variant, log_path):
    """variant: 'tip' or 'base'. Returns namespace dict."""
    assert variant in ("tip", "base")
    cells = CELLS if variant == "tip" else CELLS_BASE
    dst = SANDBOX / f"session_{variant}"
    dst.mkdir(parents=True, exist_ok=True)
    fonts_dst = dst / "fonts"
    fonts_dst.mkdir(parents=True, exist_ok=True)
    for f in (SANDBOX / "fonts").glob("*.ttf"):
        (fonts_dst / f.name).write_bytes(f.read_bytes())
    ns = {"__name__": f"mangabd_{variant}_env",
          "MANGABD_ENV": {
              "version": "12.0.0",
              "python": sys.version.split()[0],
              "platform": "linux-sandbox",
              "torch_version": "absent",
              "cuda_available": False,
              "gpu_name": "CPU only",
              "gpu_memory_gb": 0,
              "libraqm_ok": _raqm_ok(),
              "pip_ok": True,
              "warnings": [],
              "errors": [],
          }}

    buf = io.StringIO()
    try:
        with redirect_stdout(buf):
            with Chroot(dst):
                exec(compile(cells[1], f"<cell1_{variant}>", "exec"), ns)
            with Chroot(dst):
                exec(compile(cells[2], f"<cell2.1_{variant}>", "exec"), ns)
            with Chroot(dst):
                exec(compile(cells[3], f"<cell3_{variant}>", "exec"), ns)
            _mangabd_assets_seed(ns, dst)
            if variant == "tip":
                est = _slice_fn(
                    cells[6], "def _estimate_region_angle",
                    'print("  ✅ B2 orientation estimator ready')
                exec(compile(est, "<cell6_estimator_slice>", "exec"), ns)
                srt = _slice_fn(
                    cells[6], "def sort_regions_by_reading_order",
                    "\ndef ")
                exec(compile(srt, "<cell6_sort_slice>", "exec"), ns)
            exec(compile(cells[10], f"<cell10_{variant}>", "exec"), ns)
    finally:
        log_path.write_text(buf.getvalue(), encoding="utf-8")
    ns["_session_dir"] = str(dst)
    ns["_cell10_src"] = cells[10]
    return ns


if __name__ == "__main__":
    for v in ("tip", "base"):
        ns = build_env(v, HERE / f"env_exec_{v}.log")
        print(f"[{v}] env built; session={ns['_session_dir']}")
        print(f"[{v}] render_page={ns.get('render_page') is not None} "
              f"estimator={ns.get('_estimate_region_angle') is not None} "
              f"knob={ns['MANGABD_CONFIG']['detection'].get('b2_orientation_enable', 'ABSENT')}")
        log = (HERE / f"env_exec_{v}.log").read_text(encoding="utf-8")
        tail = [l for l in log.splitlines() if "result:" in l or "failed" in l.lower()]
        for t in tail[-4:]:
            print(f"[{v}] {t.strip()[:130]}")
