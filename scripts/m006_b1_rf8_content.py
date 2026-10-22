#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-8 — anchored patch content (onnxruntime in cell 0 +
download hang robustness).

Base: branch mangabd-006-b1 @ 0b5d11d (RF-7 a0e6bbf + Flash RF-7 delta
CLOSED, report-only — notebook bytes unchanged since a0e6bbf). Touched
cells {0, 5, 7} — the RF-8 directive's explicit scope; the 24 non-target
cells stay byte-identical to 0b5d11d.

Defect 1 (cell 0): onnxruntime missing from the pip-install groups —
baberu's own diagnostic says '!pip install onnxruntime' but cell 0 never
installs it, so a fresh Colab first-run degrades the local OCR engines.
Fix: 'onnxruntime>=1.31.0' in DETECTION_PACKAGES (the RF-5/RF-7
verified version).

Defect 2 (cell 5): owner log shows hf_hub_download reaching 100% then
hanging 10+ min in post-download processing (cache-path copy/lock).
Fix per directive:
  - hf_hub_download(local_dir=..., force_download=False) — HF writes the
    target directly, no shutil.copyfile move step at all.
  - per-file timeout (_ENGINE_DOWNLOAD_TIMEOUT_SECONDS = 300) around the
    call — daemon worker + join(timeout); loud TIMEOUT RuntimeError
    instead of a silent hang.
  - after every file: immediate sha256-verify + visible
    "[N/M] sha256=<8hex> size=<bytes> OK" progress line.
  - ANY sha mismatch/timeout -> the full RF-7 Bengali diagnostic
    (git-clone one-liner + Drive path), never a silent fall-through.

Cell 7: Test 29 extended per directive (download-then-hang simulation ->
timeout fires + diagnostic path taken), plus the two assertion updates
the new fail-fast per-file verify REQUIRES (disclosed in PC1-C5):
  - phase ka: downloader call count 3->1 (wrong bytes stop at file 1)
  - phase kha: [N/M] progress lines asserted via stdout capture.
"""

# ─────────────────────────────────────────────────────────────
# CELL 0 — pip install list (Defect 1)
# ─────────────────────────────────────────────────────────────

C0_PACKAGES_OLD = r'''DETECTION_PACKAGES = [
    "shapely>=2.0.0",
    "pyclipper>=1.3.0",
    "networkx>=3.0",
    "scikit-image>=0.21.0",
]'''

C0_PACKAGES_NEW = r'''DETECTION_PACKAGES = [
    "shapely>=2.0.0",
    "pyclipper>=1.3.0",
    # RF-8 (owner live-test a0e6bbf): kellenok/baberu ONNX OCR engines-এর
    # runtime — cell 0-তে নেই বলে fresh Colab-এ প্রথম run-এই দুটো engine
    # graceful-fail করত। Version = RF-5/RF-7-এ verified 1.31.0।
    "onnxruntime>=1.31.0",
    "networkx>=3.0",
    "scikit-image>=0.21.0",
]'''

# ─────────────────────────────────────────────────────────────
# CELL 5 — module-level per-file download timeout constant
# ─────────────────────────────────────────────────────────────

C5_TIMEOUT_OLD = r'''    return digest.hexdigest()


class ModelManager:'''

C5_TIMEOUT_NEW = r'''    return digest.hexdigest()


# RF-8 (owner live-test a0e6bbf hang): per-file download timeout —
# hf_hub_download আটকে গেলে এই সেকেন্ড অতিক্রান্ত হলে loud TIMEOUT
# RuntimeError (নীরব 10-মিনিট+ hang নয়)। Self-test 29 ছোট মান patch
# করে এই timeout-টাই যাচাই করে।
_ENGINE_DOWNLOAD_TIMEOUT_SECONDS = 300


class ModelManager:'''

# ─────────────────────────────────────────────────────────────
# CELL 5 — self-heal section header comment
# ─────────────────────────────────────────────────────────────

C5_SECTION_OLD = r'''    # ───────────────────────────────────────────────────────
    # OCR engine weights self-heal — MANGABD-006 B1 RF-7
    # (vendored/Drive sha-verify → sha-pinned HF download)
    # ───────────────────────────────────────────────────────'''

C5_SECTION_NEW = r'''    # ───────────────────────────────────────────────────────
    # OCR engine weights self-heal — MANGABD-006 B1 RF-7
    # (vendored/Drive sha-verify → sha-pinned HF download)
    # RF-8: local_dir direct write + per-file timeout + progress
    # ───────────────────────────────────────────────────────'''

# ─────────────────────────────────────────────────────────────
# CELL 5 — downloader: local_dir direct write + per-file timeout
# ─────────────────────────────────────────────────────────────

C5_DOWNLOADER_OLD = r'''    def _download_engine_file(self, repo_id, revision, filename, dest_path):
        """
        RF-7 downloader — HF hub থেকে একটা ফাইল, sha-pinned revision-এ।
        Production path এটাই ব্যবহার করে; Self-test 29 এটাকে monkey-
        patch করে (no real network)। Return: লেখা ফাইলের Path।
        """
        import shutil

        from huggingface_hub import hf_hub_download

        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        downloaded = Path(
            hf_hub_download(
                repo_id=repo_id,
                revision=revision,
                filename=filename,
            )
        )

        shutil.copyfile(downloaded, dest)

        return dest'''

C5_DOWNLOADER_NEW = r'''    def _download_engine_file(self, repo_id, revision, filename, dest_path):
        """
        RF-7 downloader — HF hub থেকে একটা ফাইল, sha-pinned revision-এ।
        RF-8 (owner live-test a0e6bbf hang): hf_hub_download এখন
        local_dir-এ directly লেখে (cache-path + shutil.copyfile move-step
        নেই — download-পরের copy/block hang দূর), আর প্রতিটা ফাইলে
        per-file timeout (_ENGINE_DOWNLOAD_TIMEOUT_SECONDS) — অতিক্রান্ত
        হলে loud TIMEOUT RuntimeError। Production path এটাই ব্যবহার
        করে; Self-test 29 hf_hub_download monkey-patch করে (no real
        network)। Return: লেখা ফাইলের Path।
        """
        import threading

        from huggingface_hub import hf_hub_download

        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        # local_dir = যে dir-এর নিচে filename বসবে (dest == local_dir/filename)
        local_dir = dest

        for part in str(filename).split("/"):
            if part:
                local_dir = local_dir.parent

        timeout_s = float(
            globals().get("_ENGINE_DOWNLOAD_TIMEOUT_SECONDS", 300)
        )

        result = {}

        def _hf_download_worker():
            try:
                result["path"] = hf_hub_download(
                    repo_id=repo_id,
                    revision=revision,
                    filename=filename,
                    local_dir=str(local_dir),
                    force_download=False,
                )
            except BaseException as exc:
                result["exc"] = exc

        # Daemon worker: download hang করলেও মূল flow এই timeout-এ
        # বেরিয়ে loud diagnostic-এ যায় — নীরব block নয়; worker thread
        # daemon বলে পরে নিজেই শেষ হয়।
        worker = threading.Thread(target=_hf_download_worker, daemon=True)
        worker.start()
        worker.join(timeout_s)

        if worker.is_alive():
            raise RuntimeError(
                f"TIMEOUT: {filename} download {timeout_s:.0f}s-এ শেষ হয়নি — "
                f"নেটওয়ার্ক stall বা HF lock-wait হতে পারে (repo {repo_id} "
                f"@ {revision})। Kernel restart করে আবার চালাও — সম্পূর্ণ "
                f"ফাইল sha-verify হয়ে থাকলে আর download হবে না, বাকিগুলো "
                f"resume হবে।"
            )

        if "exc" in result:
            raise result["exc"]

        if not dest.is_file():
            raise RuntimeError(
                f"{filename} download হয়েছে কিন্তু target-এ ফাইল নেই: "
                f"{dest} — hf_hub_download(local_dir) path mismatch।"
            )

        return dest'''

# ─────────────────────────────────────────────────────────────
# CELL 5 — _ensure_engine_weights docstring tier-2 bullet
# ─────────────────────────────────────────────────────────────

C5_DOCSTRING_OLD = r'''          2. Missing → HF hub থেকে sha-pinned revision-এ auto-download
             (one-time ~145 MB), models/<engine>/-এ save, প্রতিটা ফাইল
             sha256-verify, তারপর load — পরের run থেকে offline।'''

C5_DOCSTRING_NEW = r'''          2. Missing → HF hub থেকে sha-pinned revision-এ auto-download
             (one-time ~145 MB), models/<engine>/-এ directly লেখে (RF-8:
             post-download cache-copy নেই), প্রতিটা ফাইল immediate
             sha256-verify + [N/M] progress লাইন, per-file timeout
             (_ENGINE_DOWNLOAD_TIMEOUT_SECONDS), তারপর load — পরের
             run থেকে offline।'''

# ─────────────────────────────────────────────────────────────
# CELL 5 — download loop: per-file verify + progress + loud wrap
# ─────────────────────────────────────────────────────────────

C5_LOOP_OLD = r'''        try:
            for rel_path in missing:
                self._download_engine_file(
                    str(spec.get("hf_repo", "")),
                    str(spec.get("hf_revision", "")),
                    rel_path,
                    target / rel_path,
                )

            # "sha256-verify every file, then load" — mismatch → refusal
            self._verify_engine_weights(engine_name, target, pins)
        except Exception as exc:
            raise self._engine_weights_diagnostic(
                engine_name,
                tried + "download/verify ব্যর্থ।",
                exc,
            ) from exc'''

C5_LOOP_NEW = r'''        # RF-8: per-file download → immediate sha-verify → visible
        # "[N/M] sha256=<8hex> size=<bytes> OK" progress; mismatch বা
        # timeout হলে পরের ফাইলে যাওয়ার আগেই loud refusal।
        progress = {"done": 0, "last": None}

        try:
            for i, rel_path in enumerate(missing, start=1):
                progress["last"] = rel_path
                file_dest = target / rel_path

                self._download_engine_file(
                    str(spec.get("hf_repo", "")),
                    str(spec.get("hf_revision", "")),
                    rel_path,
                    file_dest,
                )

                got_sha = _sha256_of_file(file_dest)
                want_sha = str(pins[rel_path].get("sha256", ""))

                if got_sha != want_sha:
                    raise RuntimeError(
                        f"{engine_name} downloaded sha mismatch: {rel_path} — "
                        f"pin {want_sha[:12]}..., পাওয়া গেল {got_sha[:12]}... "
                        f"(file: {file_dest})"
                    )

                print(
                    f"    [{i}/{len(missing)}] sha256={got_sha[:8]} "
                    f"size={file_dest.stat().st_size} OK"
                )

                progress["done"] = i

            # "sha256-verify every file, then load" — mismatch → refusal
            self._verify_engine_weights(engine_name, target, pins)
        except Exception as exc:
            raise self._engine_weights_diagnostic(
                engine_name,
                tried
                + (
                    f"download/verify ব্যর্থ — শেষ চেষ্টা: {progress['last']} "
                    f"(সম্পন্ন {progress['done']}/{len(missing)})।"
                ),
                exc,
            ) from exc'''

# ─────────────────────────────────────────────────────────────
# CELL 7 — Tests 26-29 header comment (RF-8 note)
# ─────────────────────────────────────────────────────────────

C7_HEADER_OLD = r'''# Test 29 (RF-7, Owner Colab live-test 20261019_192): weights self-heal —
# monkey-patched candidates+downloader, NO real network।'''

C7_HEADER_NEW = r'''# Test 29 (RF-7, Owner Colab live-test 20261019_192): weights self-heal —
# monkey-patched candidates+downloader, NO real network।
# Test 29 ঙ-ফেজ (RF-8, owner live-test a0e6bbf): download-then-hang —
# hf_hub_download sleep-stub + ছোট patched timeout → TIMEOUT refusal +
# full diagnostic; এখানেও NO real network।'''

# ─────────────────────────────────────────────────────────────
# CELL 7 — Test 29 header comment
# ─────────────────────────────────────────────────────────────

C7_T29_HEADER_OLD = r'''# Test 29: weights self-heal — vendored/Drive sha-verify → sha-pinned HF
# download → refusal discipline (RF-7)। Hermetic: candidates+downloader
# monkey-patched (NO real network), fake pins save/restored in finally।'''

C7_T29_HEADER_NEW = r'''# Test 29: weights self-heal — vendored/Drive sha-verify → sha-pinned HF
# download → refusal discipline (RF-7)। Hermetic: candidates+downloader
# monkey-patched (NO real network), fake pins save/restored in finally।
# RF-8: ঙ-ফেজ — hf_hub_download sleep-stub + timeout=1s (patched global)
# → per-file TIMEOUT fire + full diagnostic assert (no real network)।'''

# ─────────────────────────────────────────────────────────────
# CELL 7 — Test 29 imports (contextlib + io for stdout capture)
# ─────────────────────────────────────────────────────────────

C7_T29_IMPORTS_OLD = r'''    import hashlib as _hashlib29
    import shutil as _shutil29
    import tempfile as _tempfile29
    from pathlib import Path as _Path29'''

C7_T29_IMPORTS_NEW = r'''    import contextlib as _contextlib29
    import hashlib as _hashlib29
    import io as _io29
    import shutil as _shutil29
    import tempfile as _tempfile29
    from pathlib import Path as _Path29'''

# ─────────────────────────────────────────────────────────────
# CELL 7 — Test 29 phase ka: fail-fast assertion update
# ─────────────────────────────────────────────────────────────

C7_T29_PHASE_KA_OLD = r'''            _pin_call_ok29[_eng_name29] = (
                _w29_calls["n"] == len(_exp_files29)
                and all(
                    (_r == _exp_repo29) and (_v == _exp_rev29)
                    for (_r, _v, _f) in _w29_calls["args"]
                )
                and sorted(_f for (_r, _v, _f) in _w29_calls["args"])
                == _exp_files29
            )'''

C7_T29_PHASE_KA_NEW = r'''            # RF-8: per-file immediate verify বলে wrong bytes প্রথম
            # ফাইলেই fail-fast — পরের ফাইলে যাওয়ার আগেই থেমে যায়।
            _pin_call_ok29[_eng_name29] = (
                _w29_calls["n"] == 1
                and all(
                    (_r == _exp_repo29) and (_v == _exp_rev29)
                    for (_r, _v, _f) in _w29_calls["args"]
                )
                and _w29_calls["args"][0][2] in set(_exp_files29)
            )'''

# ─────────────────────────────────────────────────────────────
# CELL 7 — Test 29 phase kha: progress-line capture + assert
# ─────────────────────────────────────────────────────────────

C7_T29_PHASE_KHA_OLD = r'''        _w29_calls["n"] = 0
        _w29_calls["args"] = []

        _dir29 = model_manager._ensure_engine_weights("kellenok")

        _ok_path29 = ('''

C7_T29_PHASE_KHA_NEW = r'''        _w29_calls["n"] = 0
        _w29_calls["args"] = []

        # RF-8: [N/M] progress লাইনগুলোও assert — stdout capture-এ।
        _captured29 = _io29.StringIO()

        with _contextlib29.redirect_stdout(_captured29):
            _dir29 = model_manager._ensure_engine_weights("kellenok")

        _progress_ok29 = (
            "[1/2] sha256=" in _captured29.getvalue()
            and "[2/2] sha256=" in _captured29.getvalue()
            and " OK" in _captured29.getvalue()
        )

        _ok_path29 = ('''

# ─────────────────────────────────────────────────────────────
# CELL 7 — Test 29 tail: RF-8 hang phase (directive) + verdict
# ─────────────────────────────────────────────────────────────

C7_T29_TAIL_OLD = r'''        _t29_ok = (
            all(_pin_call_ok29.values())
            and all(_pin_refusal_ok29.values())
            and _ok_path29
            and _vendored_ok29
            and _corrupt_ok29
        )

        run_test(
            "OCR weights self-heal (RF-7)",
            _t29_ok,
            "; ".join(_pin_detail29)
            + f"; ok={_ok_path29}; vendored={_vendored_ok29}; "
            f"corrupt-refusal={_corrupt_ok29}",
        )'''

C7_T29_TAIL_NEW = r'''        # (ঙ) RF-8 — download-then-hang: hf_hub_download sleep-এ আটকে
        # যায়, per-file timeout fire করে → TIMEOUT + full diagnostic।
        _w29_state["phase"] = "hang"
        _saved_timeout29 = globals().get(
            "_ENGINE_DOWNLOAD_TIMEOUT_SECONDS", 300
        )
        globals()["_ENGINE_DOWNLOAD_TIMEOUT_SECONDS"] = 1

        import huggingface_hub as _hfmod29

        _saved_hf29 = _hfmod29.hf_hub_download
        _saved_dl29 = model_manager._download_engine_file

        def _w29_hang_download(**_kwargs29):
            # Real hf_hub_download-এর জায়গায় sleep — কখনো return নয়।
            import time as _time29

            _time29.sleep(30)

        _hang_refusal29 = None
        _hang_elapsed29 = -1.0

        try:
            # REAL downloader + hanging hf_hub_download + 1s timeout।
            model_manager._download_engine_file = _saved_downloader29
            _hfmod29.hf_hub_download = _w29_hang_download

            import time as _time29h

            _t0_29 = _time29h.monotonic()

            try:
                model_manager._ensure_engine_weights("kellenok")
            except RuntimeError as _r29h:
                _hang_refusal29 = str(_r29h)

            _hang_elapsed29 = _time29h.monotonic() - _t0_29
        finally:
            _hfmod29.hf_hub_download = _saved_hf29
            model_manager._download_engine_file = _saved_dl29
            globals()["_ENGINE_DOWNLOAD_TIMEOUT_SECONDS"] = _saved_timeout29

        _hang_ok29 = (
            _hang_refusal29 is not None
            and "TIMEOUT" in _hang_refusal29
            and "1s" in _hang_refusal29
            and "git clone" in _hang_refusal29
            and "Drive" in _hang_refusal29
            and _hang_elapsed29 < 10
        )

        _t29_ok = (
            all(_pin_call_ok29.values())
            and all(_pin_refusal_ok29.values())
            and _ok_path29
            and _progress_ok29
            and _vendored_ok29
            and _corrupt_ok29
            and _hang_ok29
        )

        run_test(
            "OCR weights self-heal (RF-7)",
            _t29_ok,
            "; ".join(_pin_detail29)
            + f"; ok={_ok_path29}; progress={_progress_ok29}; "
            f"vendored={_vendored_ok29}; corrupt-refusal={_corrupt_ok29}; "
            f"hang-timeout={_hang_ok29}",
        )'''
