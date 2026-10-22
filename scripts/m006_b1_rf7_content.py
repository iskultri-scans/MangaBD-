#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-7 — anchored-patch content texts.

Directive (PM relay, Owner live-test 20261019_192): kellenok/baberu failed
in the Owner's Colab with "weights পাওয়া যায়নি" because the session had
only the notebook file, no repo tree. The loader must self-heal:

  1. vendored bytes (repo-relative models/<engine>/ or the documented Drive
     path MODELS_DIR/<engine>) -> sha256-verify against the RF-5 pins and
     use — zero network, M6-B1 behavior byte-for-byte unchanged;
  2. missing -> AUTO-DOWNLOAD from HF hub at the sha-pinned revisions
     (kellenok b3b65cbd...; baberu fdf292a1... int4 bundle), save under
     models/<engine>/, sha256-verify every file, then load (one-time
     ~145 MB; subsequent runs offline);
  3. on failure -> expanded Bengali diagnostic (what was tried + exact
     git-clone one-liner + Drive path alternative).

Scope: cell 5 loader + new self-test 29 in cell 7 (where Tests 26-28 live);
touched cells stay within {5, 7, 15, 25}.
"""

# ── P1: registry comment (cell 5) ────────────────────────────
C5_COMMENT_OLD = """# kellenok/baberu weights এই repository-তে VENDORED (models/ দেখো, M6-B1)
# এবং শুধু local path থেকে load হয় — load-time-এ কখনো HF hub ছোঁয় না।"""

C5_COMMENT_NEW = """# kellenok/baberu weights এই repository-তে VENDORED (models/ দেখো, M6-B1)।
# Vendored/Drive-তে সম্পূর্ণ bundle থাকলে load-time-এ কখনো HF hub ছোঁয় না;
# না থাকলেই শুধু _ensure_engine_weights (RF-7, Owner Colab live-test
# 20261019_192) sha-pinned revision-এ one-time download করে — পরের run
# offline, vendored behavior অপরিবর্তিত।"""

# ── P2: kellenok provenance pins (cell 5) ────────────────────
C5_KELLENOK_OLD = """    "kellenok": {
        "type": "local",
        "model": "Kellenok/PP-OCRv6_manga",
        "weights_path": "models/kellenok/",  # vendored (M6-B1)
        "vrmb_gb": 0.4,"""

C5_KELLENOK_NEW = """    "kellenok": {
        "type": "local",
        "model": "Kellenok/PP-OCRv6_manga",
        "weights_path": "models/kellenok/",  # vendored (M6-B1)
        # RF-7 self-heal provenance pins (RF-5 A8 sha256 + M6-B1 manifest):
        # vendored bundle না থাকলে এই repo-র এই revision থেকেই download
        # হবে, তারপর প্রতিটা ফাইল sha-verify।
        "hf_repo": "Kellenok/PP-OCRv6_manga",
        "hf_revision": "b3b65cbd29cd0240a6b471e49373eb5a80abac",
        "files": {
            "det/manga_det_v0.2.onnx": {
                "sha256": "d132078c46e292b226fb5a2ca52a7612ad319262dfdf493e7d8e3be435295978",
                "size": 1816954,
            },
            "rec/manga_rec_v0.2.onnx": {
                "sha256": "de12c84c63e62c80339e882e675983d886670dcb6f0147e1ed041afd6fa81888",
                "size": 21167540,
            },
            "ppocrv6_dict.txt": {
                "sha256": "b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d",
                "size": 74947,
            },
        },
        "vrmb_gb": 0.4,"""

# ── P3: baberu provenance pins (cell 5) ─────────────────────
C5_BABERU_OLD = """    "baberu": {
        "type": "local",
        "model": "genshiai-daichi/baberu-ocr",
        "weights_path": "models/baberu/",  # vendored (M6-B1)
        "vrmb_gb": 0.2,"""

C5_BABERU_NEW = """    "baberu": {
        "type": "local",
        "model": "genshiai-daichi/baberu-ocr",
        "weights_path": "models/baberu/",  # vendored (M6-B1)
        # RF-7 self-heal provenance pins (RF-5 A8 sha256 + M6-B1 int4
        # bundle manifest — vision_int4 = the vendored int4 build):
        "hf_repo": "genshiai-daichi/baberu-ocr",
        "hf_revision": "fdf292a15dae9f5af37dd76bb408679dc4bcdfe4",
        "files": {
            "onnx/vision_int4.onnx": {
                "sha256": "9526bcf99eb8de805df7ea2f66b385cfcbcb5dff0e99a5dcfb02bdb2d4182bde",
                "size": 52293486,
            },
            "onnx/decoder_prefill_int8.onnx": {
                "sha256": "91de16d4e70adaadc0c76ea536f0195b79f54b52e3279aeaac8fc06b46824c60",
                "size": 35133596,
            },
            "onnx/decoder_step_int8.onnx": {
                "sha256": "f6164e9daee6622891d2a52394f143faa7f0ccfdfb90e8d6443193aff36d4c2d",
                "size": 34715466,
            },
            "tokenizer/vocab.json": {
                "sha256": "681de4eb83154a397af49e2ddae4705041b12a22e16fe00860b829e889e5f47c",
                "size": 130761,
            },
            "tokenizer/tokenizer_config.json": {
                "sha256": "c6c8004b1d310bd7c56455387c25cdf4da28594bbd5713aaa3fddfd5eac8f483",
                "size": 937,
            },
        },
        "vrmb_gb": 0.2,"""

# ── P4: sha256 helper before ModelManager (cell 5) ──────────
C5_SHA_HELPER_OLD = """# ═══════════════════════════════════════════════════════════
# 5. ModelManager
# ═══════════════════════════════════════════════════════════


class ModelManager:"""

C5_SHA_HELPER_NEW = """# ═══════════════════════════════════════════════════════════
# 5. ModelManager
# ═══════════════════════════════════════════════════════════


def _sha256_of_file(path):
    \"\"\"
    RF-7: engine weight ফাইলের sha256 — 1 MB chunk streaming (122 MB
    ফাইলেও memory স্ফীতি নেই)।
    \"\"\"
    import hashlib

    digest = hashlib.sha256()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


class ModelManager:"""

# ── P5: weights self-heal methods (cell 5) ──────────────────
C5_SELFHEAL_OLD = """    # ───────────────────────────────────────────────────────
    # OCR engine registry — MANGABD-006 B1 (lazy load + single resident)
    # ───────────────────────────────────────────────────────

    def _resolve_vendored_engine_dir(self, engine_name):"""

C5_SELFHEAL_NEW = """    # ───────────────────────────────────────────────────────
    # OCR engine weights self-heal — MANGABD-006 B1 RF-7
    # (vendored/Drive sha-verify → sha-pinned HF download)
    # ───────────────────────────────────────────────────────

    def _engine_weights_candidates(self, engine_name):
        \"\"\"
        RF-7: vendored weights-এর documented locations (চেক করার ক্রম):
          1. CWD-relative weights_path (repo checkout / notebook dir)
          2. MODELS_DIR/<engine> — notebook convention; Drive-mounted
             Colab-এ এটাই /content/drive/MyDrive/MangaBD_V12/models/<engine>
        (_resolve_vendored_engine_dir-এর candidate ক্রমের অনুরূপ।)
        \"\"\"
        spec = self.config["ocr"]["engines"][engine_name]
        rel = str(spec.get("weights_path", f"models/{engine_name}/")).rstrip("/")

        return [Path(rel), MODELS_DIR / engine_name]

    def _download_engine_file(self, repo_id, revision, filename, dest_path):
        \"\"\"
        RF-7 downloader — HF hub থেকে একটা ফাইল, sha-pinned revision-এ।
        Production path এটাই ব্যবহার করে; Self-test 29 এটাকে monkey-
        patch করে (no real network)। Return: লেখা ফাইলের Path।
        \"\"\"
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

        return dest

    def _verify_engine_weights(self, engine_name, weights_dir, pins):
        \"\"\"
        RF-7: pinned sha256-এর বিপরীতে প্রতিটা ফাইল verify — vendored
        আর downloaded একই শর্তে (sha mismatch → refusal; corrupt/ভিন্ন
        bytes কখনো নীরবে load হয় না)।
        \"\"\"
        for rel_path, meta in pins.items():
            path = Path(weights_dir) / rel_path

            if not path.is_file():
                raise RuntimeError(
                    f"{engine_name} weight file missing: {path}"
                )

            got_sha = _sha256_of_file(path)
            want_sha = str(meta.get("sha256", ""))

            if got_sha != want_sha:
                raise RuntimeError(
                    f"{engine_name} weight sha mismatch: {rel_path} — "
                    f"pin {want_sha[:12]}..., পাওয়া গেল {got_sha[:12]}... "
                    f"(file: {path})"
                )

    def _engine_weights_diagnostic(self, engine_name, what_tried, root_exc):
        \"\"\"
        RF-7: expanded Bengali diagnostic — কী কী চেষ্টা হলো + এখন ঠিক
        কী করতে হবে (git-clone one-liner + Drive alternative)। Chain-এর
        WARN প্রথম লাইনটা দেখায়; পুরো message log + errors-এ যায়।
        \"\"\"
        return RuntimeError(
            f"{engine_name} weights পাওয়া যায়নি — self-heal fail "
            f"(vendored/Drive নেই, download-ও হয়নি)।\\n"
            f"চেষ্টা করা হয়েছে (RF-7):\\n{what_tried}\\n"
            f"কারণ: {str(root_exc)[:140]}\\n"
            f"এখন করণীয় — যেকোনো একটা:\\n"
            f"  a) পূর্ণ repo clone করো (weights vendored), notebook-টা ওই "
            f"folder থেকে চালাও:\\n"
            f"     git clone https://github.com/iskultri-scans/MangaBD-.git\\n"
            f"  b) Drive alternative: repo-র models/{engine_name}/ ফোল্ডারটা "
            f"Drive-এ {MODELS_DIR / engine_name} পথে copy করে দাও — "
            f"পরের run থেকে download লাগবে না।\\n"
            f"  c) আংশিক/corrupt ফাইল থাকলে ওটা delete করে আবার চালাও — "
            f"sha-pinned download নিজে থেকেই আবার চেষ্টা করবে।"
        )

    def _ensure_engine_weights(self, engine_name):
        \"\"\"
        RF-7 (Owner Colab live-test 20261019_192): weights self-heal —
        notebook-only Colab session-এ vendored repo tree ছাড়াও চলবে।

          1. Vendored bytes আছে (repo-relative models/<engine>/ বা
             documented Drive path MODELS_DIR/<engine>) → RF-5 pins-এ
             sha256-verify, তারপর ব্যবহার — zero network; vendored
             behavior অপরিবর্তিত (M6-B1)।
          2. Missing → HF hub থেকে sha-pinned revision-এ auto-download
             (one-time ~145 MB), models/<engine>/-এ save, প্রতিটা ফাইল
             sha256-verify, তারপর load — পরের run থেকে offline।
          3. Download/verify fail → expanded Bengali diagnostic।
        \"\"\"
        spec = self.config["ocr"]["engines"][engine_name]
        pins = spec.get("files") or {}

        if not pins:
            # Pin-বিহীন engine — RF-7-র আগের vendored-dir contract।
            return self._resolve_vendored_engine_dir(engine_name)

        candidates = self._engine_weights_candidates(engine_name)
        candidates_str = " বা ".join(str(c) for c in candidates)

        # 1. Vendored complete bundle → sha-verify + use (zero network)
        for cand in candidates:
            if cand.is_dir() and all(
                (cand / rel_path).is_file() for rel_path in pins
            ):
                try:
                    self._verify_engine_weights(engine_name, cand, pins)
                except Exception as exc:
                    raise self._engine_weights_diagnostic(
                        engine_name,
                        f"  1. Vendored bundle পাওয়া গেছে ({cand}) কিন্তু "
                        f"sha verify fail — corrupt/ভিন্ন bytes।",
                        exc,
                    ) from exc

                return cand

        # 2. Missing → one-time sha-pinned download under models/<engine>/
        target = None

        for cand in candidates:
            if cand.is_dir():
                target = cand  # অর্ধেক-লেখা copy থাকলে সেখানেই পূরণ হবে

                break

        if target is None:
            target = MODELS_DIR / engine_name

        target = Path(target)
        target.mkdir(parents=True, exist_ok=True)

        missing = [
            rel_path
            for rel_path in pins
            if not (target / rel_path).is_file()
        ]

        if missing:
            total_mb = (
                sum(int(pins[rel_path].get("size", 0)) for rel_path in missing)
                / (1024 * 1024)
            )

            print(
                f"  📥 {engine_name}: vendored weights নেই — HF hub থেকে "
                f"sha-pinned download ({len(missing)}/{len(pins)} ফাইল, "
                f"~{total_mb:.0f} MB, one-time; পরের run offline)"
            )

            log_event(
                f"{engine_name} weights missing — auto-download "
                f"{len(missing)} pinned files (~{total_mb:.0f} MB)",
                level="WARN",
            )

        tried = (
            f"  1. Vendored/Drive খোঁজা হলো: {candidates_str} — সম্পূর্ণ "
            f"bundle নেই।\\n"
            f"  2. HF sha-pinned download ({spec.get('hf_repo', '?')} @ "
            f"{spec.get('hf_revision', '?')}, {len(missing)}/{len(pins)} "
            f"ফাইল): "
        )

        try:
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
            ) from exc

        return target

    # ───────────────────────────────────────────────────────
    # OCR engine registry — MANGABD-006 B1 (lazy load + single resident)
    # ───────────────────────────────────────────────────────

    def _resolve_vendored_engine_dir(self, engine_name):"""

# ── P6/P7: call-site swaps (cell 5) ──────────────────────────
C5_KELLENOK_CALL_OLD = '            weights_dir = self._resolve_vendored_engine_dir("kellenok")'
C5_KELLENOK_CALL_NEW = '            weights_dir = self._ensure_engine_weights("kellenok")'
C5_BABERU_CALL_OLD = '            weights_dir = self._resolve_vendored_engine_dir("baberu")'
C5_BABERU_CALL_NEW = '            weights_dir = self._ensure_engine_weights("baberu")'

# ── P8: Tests 26-29 header comment (cell 7) ─────────────────
C7_HEADER_OLD = """# MANGABD-006 B1 — Tests 26-28 (global battery numbering: cell-8 battery-এর
# Tests 1-25-এর পরের নম্বরগুলো, কিন্তু chain self-test-গুলো M6 batch plan
# অনুযায়ী এখানে cell 7-এ বসেছে — cell-8 battery নিজে অপরিবর্তিত থাকে)।
# Fault injection = fake engines (কোনো real model load হয় না; save/restore
# সব finally-এ — RF-2/RF-4-এর inert-test conventions)।"""

C7_HEADER_NEW = """# MANGABD-006 B1 — Tests 26-29 (global battery numbering: cell-8 battery-এর
# Tests 1-25-এর পরের নম্বরগুলো, কিন্তু chain self-test-গুলো M6 batch plan
# অনুযায়ী এখানে cell 7-এ বসেছে — cell-8 battery নিজে অপরিবর্তিত থাকে)।
# Fault injection = fake engines (কোনো real model load হয় না; save/restore
# সব finally-এ — RF-2/RF-4-এর inert-test conventions)।
# Test 29 (RF-7, Owner Colab live-test 20261019_192): weights self-heal —
# monkey-patched candidates+downloader, NO real network।"""

# ── P9: Test 29 (cell 7) ────────────────────────────────────
C7_T29_OLD = """except Exception as exc:
    run_test("OCR chain guards + wiring (M6-B1)", False, str(exc)[:160])


print()"""

C7_T29_NEW = """except Exception as exc:
    run_test("OCR chain guards + wiring (M6-B1)", False, str(exc)[:160])


# Test 29: weights self-heal — vendored/Drive sha-verify → sha-pinned HF
# download → refusal discipline (RF-7)। Hermetic: candidates+downloader
# monkey-patched (NO real network), fake pins save/restored in finally।
try:
    import hashlib as _hashlib29
    import shutil as _shutil29
    import tempfile as _tempfile29
    from pathlib import Path as _Path29

    _w29_root = _Path29(_tempfile29.mkdtemp(prefix="mangabd_rf7_t29_"))

    _w29_state = {"phase": "pin"}
    _w29_calls = {"n": 0, "args": []}
    _w29_payloads = {}

    def _w29_candidates(engine_name):
        # Hermetic tmp dir — real repo models/ বা MODELS_DIR এই test-এ
        # অংশ নেয় না; ফেজ-প্রতি আলাদা dir, ফলে cross-phase pollution নেই।
        _cand = _w29_root / f"{engine_name}_{_w29_state['phase']}"
        _cand.mkdir(parents=True, exist_ok=True)
        return [_cand]

    def _w29_downloader(repo_id, revision, filename, dest_path):
        _w29_calls["n"] += 1
        _w29_calls["args"].append((repo_id, revision, filename))
        _dest = _Path29(dest_path)
        _dest.parent.mkdir(parents=True, exist_ok=True)
        _dest.write_bytes(_w29_payloads.get(filename, b"rf7-wrong-bytes"))

    def _w29_sha(payload):
        return _hashlib29.sha256(payload).hexdigest()

    _eng29 = MANGABD_CONFIG["ocr"]["engines"]
    _saved_candidates29 = model_manager._engine_weights_candidates
    _saved_downloader29 = model_manager._download_engine_file
    _saved_kellenok_pins29 = {
        "files": _eng29["kellenok"].get("files"),
        "hf_repo": _eng29["kellenok"].get("hf_repo"),
        "hf_revision": _eng29["kellenok"].get("hf_revision"),
    }

    try:
        model_manager._engine_weights_candidates = _w29_candidates
        model_manager._download_engine_file = _w29_downloader

        # (ক) REAL pins + missing weights → downloader ঠিক pinned
        # repo+revision+filename-এ ডাকা হয়; ভুল bytes → sha refusal।
        _w29_state["phase"] = "pin"
        _pin_expect29 = {
            "kellenok": (
                "Kellenok/PP-OCRv6_manga",
                "b3b65cbd29cd0240a6b471e49373eb5a80abac",
                sorted(_eng29["kellenok"]["files"]),
            ),
            "baberu": (
                "genshiai-daichi/baberu-ocr",
                "fdf292a15dae9f5af37dd76bb408679dc4bcdfe4",
                sorted(_eng29["baberu"]["files"]),
            ),
        }

        _pin_call_ok29 = {}
        _pin_refusal_ok29 = {}
        _pin_detail29 = []

        for _eng_name29, (_exp_repo29, _exp_rev29, _exp_files29) in _pin_expect29.items():
            _w29_calls["n"] = 0
            _w29_calls["args"] = []
            _refusal29 = None

            try:
                model_manager._ensure_engine_weights(_eng_name29)
            except RuntimeError as _r29:
                _refusal29 = str(_r29)

            _pin_call_ok29[_eng_name29] = (
                _w29_calls["n"] == len(_exp_files29)
                and all(
                    (_r == _exp_repo29) and (_v == _exp_rev29)
                    for (_r, _v, _f) in _w29_calls["args"]
                )
                and sorted(_f for (_r, _v, _f) in _w29_calls["args"])
                == _exp_files29
            )
            _pin_refusal_ok29[_eng_name29] = (
                _refusal29 is not None
                and "sha mismatch" in _refusal29
                and "git clone" in _refusal29
            )
            _pin_detail29.append(
                f"{_eng_name29}:calls={_w29_calls['n']},"
                f"refusal={'sha+clone' if _pin_refusal_ok29[_eng_name29] else 'BAD'}"
            )

        # (খ) Fake pins + missing weights → download → verify → use।
        _w29_state["phase"] = "ok"
        _fake_files29 = {
            "det/manga_det_v0.2.onnx": b"rf7-test-det-bytes",
            "ppocrv6_dict.txt": b"rf7-test-dict-bytes",
        }
        _fake_pins29 = {
            _rel29: {"sha256": _w29_sha(_pl29), "size": len(_pl29)}
            for _rel29, _pl29 in _fake_files29.items()
        }
        _eng29["kellenok"]["files"] = _fake_pins29
        _eng29["kellenok"]["hf_repo"] = "TEST/OWNER-REPO"
        _eng29["kellenok"]["hf_revision"] = "deadbeef0000"
        _w29_payloads.update(_fake_files29)

        _w29_calls["n"] = 0
        _w29_calls["args"] = []

        _dir29 = model_manager._ensure_engine_weights("kellenok")

        _ok_path29 = (
            _Path29(_dir29) == _w29_root / "kellenok_ok"
            and _w29_calls["n"] == 2
            and all(
                (_r == "TEST/OWNER-REPO") and (_v == "deadbeef0000")
                for (_r, _v, _f) in _w29_calls["args"]
            )
            and _w29_sha(
                (_Path29(_dir29) / "det/manga_det_v0.2.onnx").read_bytes()
            )
            == _fake_pins29["det/manga_det_v0.2.onnx"]["sha256"]
        )

        # (গ) Vendored bytes present → sha-verify + use — zero network।
        _w29_state["phase"] = "vendored"
        _cand29v = _w29_root / "kellenok_vendored"
        (_cand29v / "det").mkdir(parents=True, exist_ok=True)
        (_cand29v / "det/manga_det_v0.2.onnx").write_bytes(
            _fake_files29["det/manga_det_v0.2.onnx"]
        )
        (_cand29v / "ppocrv6_dict.txt").write_bytes(
            _fake_files29["ppocrv6_dict.txt"]
        )

        _w29_calls["n"] = 0
        _w29_calls["args"] = []

        _dir29v = model_manager._ensure_engine_weights("kellenok")

        _vendored_ok29 = (
            _Path29(_dir29v) == _cand29v
            and _w29_calls["n"] == 0
        )

        # (ঘ) Vendored bytes corrupt → sha refusal, downloader ডাকা হয় না।
        _w29_state["phase"] = "corrupt"
        _cand29c = _w29_root / "kellenok_corrupt"
        (_cand29c / "det").mkdir(parents=True, exist_ok=True)
        (_cand29c / "det/manga_det_v0.2.onnx").write_bytes(b"tampered-bytes")
        (_cand29c / "ppocrv6_dict.txt").write_bytes(
            _fake_files29["ppocrv6_dict.txt"]
        )

        _w29_calls["n"] = 0
        _refusal29c = None

        try:
            model_manager._ensure_engine_weights("kellenok")
        except RuntimeError as _r29c:
            _refusal29c = str(_r29c)

        _corrupt_ok29 = (
            _refusal29c is not None
            and "sha mismatch" in _refusal29c
            and "git clone" in _refusal29c
            and _w29_calls["n"] == 0
        )

        _t29_ok = (
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
        )

    finally:
        model_manager._engine_weights_candidates = _saved_candidates29
        model_manager._download_engine_file = _saved_downloader29
        _eng29["kellenok"]["files"] = _saved_kellenok_pins29["files"]
        _eng29["kellenok"]["hf_repo"] = _saved_kellenok_pins29["hf_repo"]
        _eng29["kellenok"]["hf_revision"] = _saved_kellenok_pins29["hf_revision"]
        _shutil29.rmtree(_w29_root, ignore_errors=True)

except Exception as exc:
    run_test("OCR weights self-heal (RF-7)", False, str(exc)[:160])


print()"""
