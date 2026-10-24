#!/usr/bin/env python3
r"""MANGABD-007 B2 (Phase C) — cell-5 patch content (S05-1).

S05-1: embedding model warning — ModelManager.ensure_embedding()
(created; did not exist before) + _embedding_load_failed helper +
Test 10 (graceful-degrade battery: simulated ImportError AND OSError,
Bengali diagnostics in logs, cached-failure short-circuit, manager
stays usable). Target cell 5 ONLY; the build driver unique-asserts
every anchor and writes the manifest to m007_b2_patches.json (RF-9:
instruments committed in the Phase C commit).
"""

# 5-1: ensure_embedding + _embedding_load_failed inserted between
# ensure_openrouter_vision (last ensure_* loader) and the unload_* group.
CELL5_ENSURE_EMBEDDING_OLD = r'''        except Exception as exc:
            self.errors["openrouter_vision"] = str(exc)[:300]

            log_event(
                f"OpenRouter vision client init failed: {str(exc)[:160]}",
                level="ERROR",
            )

            raise

    def unload_qwen(self):'''

CELL5_ENSURE_EMBEDDING_NEW = r'''        except Exception as exc:
            self.errors["openrouter_vision"] = str(exc)[:300]

            log_event(
                f"OpenRouter vision client init failed: {str(exc)[:160]}",
                level="ERROR",
            )

            raise

    def ensure_embedding(self, force=False):
        """
        MANGABD-007 B2 S05-1: semantic-search embedding model lazy
        loader (ModelManager.ensure_embedding — নতুন method, আগে
        ছিল না)।

        sentence-transformers এখান থেকে lazy-load হয়। Load fail করলে
        pipeline কখনো crash করে না — বাংলায় স্পষ্ট diagnostic log+print
        হয়, আর None return হয় (feature disabled: semantic search)।
        Caller contract: emb = model_manager.ensure_embedding() —
        None পেলে semantic-search feature empty result দেবে (empty
        list/dict), কখনো raise নয়। আগের failure cached — প্রতি call-এ
        আবার ব্যর্থ import/download চেষ্টা করে সময় নষ্ট করে না;
        force=True দিলে আবার চেষ্টা করে।
        """
        if "embedding" in self.instances and not force:
            return self.instances["embedding"]

        # S05-1: cached-failure short-circuit (আগের failure মনে রাখা —
        # প্রতিটা call নতুন করে fail হওয়া download চালাবে না)।
        if self.errors.get("embedding") and not force:
            return None

        start = time.time()

        try:
            from sentence_transformers import SentenceTransformer

            emb_cfg = self.config.get("semantic_search", {}) or {}
            model_name = str(
                emb_cfg.get(
                    "embedding_model",
                    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                )
            )

            print(f"  📥 Loading embedding model: {model_name}")

            model = SentenceTransformer(
                model_name,
                cache_dir=str(MODELS_DIR / "embedding"),
            )

            instance = {
                "model": model,
                "model_name": model_name,
                "device": DEVICE,
            }

            self.instances["embedding"] = instance
            self.load_times["embedding"] = time.time() - start
            self.errors.pop("embedding", None)

            log_event(
                f"Embedding model loaded in "
                f"{self.load_times['embedding']:.1f}s",
                level="INFO",
            )

            print(
                f"  ✅ Embedding model loaded in "
                f"{self.load_times['embedding']:.1f}s"
            )

            return instance

        except ImportError as exc:
            # S05-1: sentence-transformers ইনস্টল করা নেই — সবচেয়ে
            # সাধারণ failure। Bengali diagnostic + graceful degrade।
            return self._embedding_load_failed(exc)

        except OSError as exc:
            # S05-1: network/disk failure (model download বা cache)।
            return self._embedding_load_failed(exc)

        except Exception as exc:
            # S05-1: unexpected load error — semantic search কখনো
            # pipeline crash করাবে না; একই graceful degrade।
            return self._embedding_load_failed(exc)

    def _embedding_load_failed(self, exc):
        """
        S05-1: embedding load failure handler — বাংলা diagnostic +
        graceful degrade (None return, কখনো raise নয়)।
        """
        reason = f"{type(exc).__name__}: {exc}"[:200]

        self.errors["embedding"] = reason
        self.instances.pop("embedding", None)

        msg = (
            f"⚠️ Embedding model load failed: {reason}। "
            f"Feature disabled: semantic search। "
            f"Fix: !pip install sentence-transformers OR check "
            f"internet connection।"
        )

        print(msg)
        log_event(msg, level="ERROR")

        return None

    def unload_qwen(self):'''

# 5-2: Test 10 — graceful-degrade battery (importError + OSError
# simulations; deterministic, no real install/network state touched).
CELL5_TEST10_OLD = r'''except Exception as exc:
    run_test("OCR confidence helper", False, str(exc)[:160])

print()'''

CELL5_TEST10_NEW = r'''except Exception as exc:
    run_test("OCR confidence helper", False, str(exc)[:160])


# Test 10: MANGABD-007 B2 S05-1 — embedding load failure → graceful
# degrade (never a crash). Two deterministic simulations, কোনো real
# install/network state ছোঁয়া হয় না: (a) ImportError — sys.modules-এ
# None-injection (standard "package missing" signal), (b) OSError —
# fake module যার SentenceTransformer load-এ raise করে। Contract:
# ensure_embedding() None return করে (কখনো raise নয়), বাংলা
# diagnostic log+console দুই জায়গায় যায়, failure cached (দ্বিতীয়
# call-এ নতুন log line নেই), এবং manager পরে পুরোপুরি usable।
_saved_log10 = globals().get("log_event", None)
try:
    import io as _io10
    import sys as _sys10
    import types as _types10
    from contextlib import redirect_stdout as _rso10

    _emb_logs10 = []

    def _fake_log_event10(msg, level="INFO", **kw):
        _emb_logs10.append((level, str(msg)))

    globals()["log_event"] = _fake_log_event10

    # (a) ImportError simulation — package missing
    _st_had10 = "sentence_transformers" in _sys10.modules
    _st_old10 = _sys10.modules.get("sentence_transformers")
    _sys10.modules["sentence_transformers"] = None

    _mm10 = ModelManager(MANGABD_CONFIG)

    try:
        _buf10 = _io10.StringIO()
        with _rso10(_buf10):
            _res10 = _mm10.ensure_embedding()
        _out10 = _buf10.getvalue()
    finally:
        if _st_had10:
            _sys10.modules["sentence_transformers"] = _st_old10
        else:
            _sys10.modules.pop("sentence_transformers", None)

    _err_msgs10 = [m for lv, m in _emb_logs10 if lv == "ERROR"]
    _ok_import10 = (
        _res10 is None
        and "embedding" not in _mm10.instances
        and bool(_mm10.errors.get("embedding"))
        and any(
            m.startswith("⚠️ Embedding model load failed:")
            and "Feature disabled: semantic search।" in m
            and "Fix: !pip install sentence-transformers OR check "
            "internet connection।" in m
            for m in _err_msgs10
        )
        and "⚠️ Embedding model load failed:" in _out10
        and "Feature disabled: semantic search।" in _out10
    )

    # cached-failure short-circuit: repeat call → None, zero new logs
    _n_logs10 = len(_emb_logs10)
    _res10b = _mm10.ensure_embedding()
    _ok_cached10 = _res10b is None and len(_emb_logs10) == _n_logs10

    # (b) OSError simulation — fake module raising on load
    _fake_st10 = _types10.ModuleType("sentence_transformers")

    def _st_raise10(*args, **kwargs):
        raise OSError("simulated download failure (S05-1 battery)")

    _fake_st10.SentenceTransformer = _st_raise10
    _sys10.modules["sentence_transformers"] = _fake_st10

    try:
        _buf10b = _io10.StringIO()
        with _rso10(_buf10b):
            _res10b2 = ModelManager(MANGABD_CONFIG).ensure_embedding()
        _out10b = _buf10b.getvalue()
    finally:
        if _st_had10:
            _sys10.modules["sentence_transformers"] = _st_old10
        else:
            _sys10.modules.pop("sentence_transformers", None)

    _ok_oserror10 = (
        _res10b2 is None
        and "⚠️ Embedding model load failed:" in _out10b
        and "Feature disabled: semantic search।" in _out10b
    )

    # manager fully usable after both failures (degrade, not crash)
    _status10 = _mm10.status()

    run_test(
        "Embedding graceful degrade (S05-1)",
        _ok_import10
        and _ok_cached10
        and _ok_oserror10
        and isinstance(_status10, dict)
        and "loaded" in _status10
        and "errors" in _status10,
        f"import={_ok_import10} cached={_ok_cached10} "
        f"oserror={_ok_oserror10}",
    )
except Exception as exc:
    run_test("Embedding graceful degrade (S05-1)", False, str(exc)[:160])
finally:
    if _saved_log10 is not None:
        globals()["log_event"] = _saved_log10
    else:
        globals().pop("log_event", None)

print()'''
