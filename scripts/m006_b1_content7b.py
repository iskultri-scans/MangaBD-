#!/usr/bin/env python3
r"""MANGABD-006 B1 — cell 7 self-test patch content (Tests 26-28).

Global battery numbering continues from the cell-8 battery (Tests 1-25),
but the chain self-tests physically live HERE in cell 7 — exactly as the
approved M6 batch plan specifies ("25 cell-8 self-tests untouched; new
cell-7 chain self-tests (fake engines, fault injection per §M5 rows)").
This keeps cell 8 byte-identical, so the touched-cell set stays exactly
{5, 7, 15, 25} (23 non-target cells byte-identical to main).
"""

# ── patch 7-11: Tests 26-28 (insert after Test 6, before section 9) ──
CELL7_TESTS_OLD = '''except Exception as exc:
    run_test(
        "translation_df column compatibility",
        False,
        str(exc)[:160],
    )


print()


# ═══════════════════════════════════════════════════════════
# 9. Optional live OCR test
# ═══════════════════════════════════════════════════════════'''

CELL7_TESTS_NEW = '''except Exception as exc:
    run_test(
        "translation_df column compatibility",
        False,
        str(exc)[:160],
    )


# MANGABD-006 B1 — Tests 26-28 (global battery numbering: cell-8 battery-এর
# Tests 1-25-এর পরের নম্বরগুলো, কিন্তু chain self-test-গুলো M6 batch plan
# অনুযায়ী এখানে cell 7-এ বসেছে — cell-8 battery নিজে অপরিবর্তিত থাকে)।
# Fault injection = fake engines (কোনো real model load হয় না; save/restore
# সব finally-এ — RF-2/RF-4-এর inert-test conventions)।


# Test 26: OCR engine registry shape + loader wiring (M6-B1)
try:
    _ocr_reg = MANGABD_CONFIG["ocr"]

    _reg_ok = (
        _ocr_reg.get("engine") == "auto"
        and list(_ocr_reg.get("fallback_chain", []))
        == ["qwen", "openrouter_vision", "kellenok", "baberu"]
        and set(_ocr_reg.get("engines", {}).keys())
        == {"qwen", "openrouter_vision", "kellenok", "baberu"}
        and _ocr_reg["engines"]["qwen"].get("type") == "local"
        and _ocr_reg["engines"]["qwen"].get("load_fn") == "ensure_qwen"
        and _ocr_reg["engines"]["qwen"].get("unload_fn") == "unload_qwen"
        and _ocr_reg["engines"]["openrouter_vision"].get("type") == "cloud"
        and _ocr_reg["engines"]["openrouter_vision"].get("key_env")
        == "OPENROUTER_API_KEY"
        and str(_ocr_reg["engines"]["kellenok"].get("weights_path", ""))
        .startswith("models/kellenok")
        and str(_ocr_reg["engines"]["baberu"].get("weights_path", ""))
        .startswith("models/baberu")
        and _ocr_reg.get("allowed_engines")
        == list(_ocr_reg["engines"].keys())
        and all(
            "load_fn" in spec and hasattr(model_manager, spec["load_fn"])
            for spec in _ocr_reg["engines"].values()
        )
        and all(
            "unload_fn" in spec and hasattr(model_manager, spec["unload_fn"])
            for spec in _ocr_reg["engines"].values()
        )
        and hasattr(model_manager, "ensure_ocr_engine")
        and hasattr(model_manager, "unload_ocr_engine")
    )

    run_test(
        "OCR engine registry (M6-B1)",
        _reg_ok,
        str(
            {
                "engine": _ocr_reg.get("engine"),
                "chain": _ocr_reg.get("fallback_chain"),
                "engines": sorted(_ocr_reg.get("engines", {}).keys()),
            }
        ),
    )
except Exception as exc:
    run_test("OCR engine registry (M6-B1)", False, str(exc)[:160])


# Test 27: fallback chain — auto recovery (reject + error paths) + trace
try:
    _chain_img = np.full((60, 200, 3), 255, dtype=np.uint8)

    _chain_region = {
        "id": 1,
        "region_type": "bubble",
        "x": 0,
        "y": 0,
        "width": 200,
        "height": 60,
        "angle": 0.0,
    }

    _chain_calls = {"order": []}

    def _fake_ensure(_engine_name, force=False):
        return None

    def _fake_run(engine_name, image_bgr, region, page_id=None):
        _chain_calls["order"].append(engine_name)

        if engine_name == "__fake_empty__":
            return {"text": "", "confidence": 0.0, "engine": engine_name}

        if engine_name == "__fake_boom__":
            raise RuntimeError("injected fault")

        return {
            "text": "RECOVERED TEXT",
            "confidence": 0.9,
            "engine": engine_name,
        }

    _saved_chain = MANGABD_CONFIG["ocr"]["fallback_chain"]
    _saved_run = globals().get("run_ocr_engine")
    _saved_ensure = model_manager.ensure_ocr_engine

    try:
        MANGABD_CONFIG["ocr"]["engines"]["__fake_empty__"] = {"type": "cloud"}
        MANGABD_CONFIG["ocr"]["engines"]["__fake_ok__"] = {"type": "cloud"}
        MANGABD_CONFIG["ocr"]["engines"]["__fake_boom__"] = {"type": "cloud"}
        globals()["run_ocr_engine"] = _fake_run
        model_manager.ensure_ocr_engine = _fake_ensure

        # auto: reject path (empty text) -> next engine recovers
        MANGABD_CONFIG["ocr"]["fallback_chain"] = [
            "__fake_empty__",
            "__fake_ok__",
        ]
        _chain_calls["order"] = []
        res_auto = ocr_region_with_fallback(
            _chain_img,
            _chain_region,
            page_id="__chain_test__",
            engine_mode="auto",
        )
        _order_auto = list(_chain_calls["order"])
        _trace_auto = list(res_auto.get("fallback_trace", []))

        # auto: error path (exception) -> next engine recovers
        MANGABD_CONFIG["ocr"]["fallback_chain"] = [
            "__fake_boom__",
            "__fake_ok__",
        ]
        _chain_calls["order"] = []
        res_err = ocr_region_with_fallback(
            _chain_img,
            _chain_region,
            page_id="__chain_test__",
            engine_mode="auto",
        )
        _order_err = list(_chain_calls["order"])
        _trace_err = list(res_err.get("fallback_trace", []))

        # manual: single engine only — reject is terminal
        _chain_calls["order"] = []
        res_manual = ocr_region_with_fallback(
            _chain_img,
            _chain_region,
            page_id="__chain_test__",
            engine_mode="__fake_empty__",
        )
        _order_manual = list(_chain_calls["order"])
        _trace_manual = list(res_manual.get("fallback_trace", []))

        _chain_ok = (
            res_auto.get("text") == "RECOVERED TEXT"
            and res_auto.get("engine") == "__fake_ok__"
            and _order_auto == ["__fake_empty__", "__fake_ok__"]
            and [t.get("outcome") for t in _trace_auto]
            == ["rejected", "ok"]
            and all(
                {"engine", "outcome", "ms"} <= set(t) for t in _trace_auto
            )
            and res_err.get("text") == "RECOVERED TEXT"
            and res_err.get("engine") == "__fake_ok__"
            and _order_err == ["__fake_boom__", "__fake_ok__"]
            and [t.get("outcome") for t in _trace_err] == ["error", "ok"]
            and res_manual.get("text") == "[SKIP:OCR_FAILED]"
            and res_manual.get("engine") == "failed"
            and res_manual.get("status") == "failed"
            and _order_manual == ["__fake_empty__"]
            and [t.get("outcome") for t in _trace_manual] == ["rejected"]
        )

        run_test(
            "OCR fallback chain auto/manual (M6-B1)",
            _chain_ok,
            f"auto={res_auto.get('text')!r} err={res_err.get('text')!r} "
            f"manual={res_manual.get('text')!r}",
        )

    finally:
        MANGABD_CONFIG["ocr"]["fallback_chain"] = _saved_chain
        for _fake_name in ("__fake_empty__", "__fake_ok__", "__fake_boom__"):
            MANGABD_CONFIG["ocr"]["engines"].pop(_fake_name, None)
        if _saved_run is not None:
            globals()["run_ocr_engine"] = _saved_run
        model_manager.ensure_ocr_engine = _saved_ensure

except Exception as exc:
    run_test("OCR fallback chain auto/manual (M6-B1)", False, str(exc)[:160])


# Test 28: chain guards + registry restore + wiring contract (M6-B1)
try:
    import inspect as _inspect

    _guard_details = ""

    # unknown engine -> registry guard raises (কোনো load attempt নয়)
    try:
        model_manager.ensure_ocr_engine("__no_such_engine__")
        _guard_details = "ensure_ocr_engine did not raise"
    except ValueError:
        pass

    # unload_ocr_engine non-resident engine-এ safe no-op
    _unload_noop = model_manager.unload_ocr_engine("kellenok") is False

    # run_ocr_engine dispatch guard
    try:
        run_ocr_engine(
            "__unmapped__", np.zeros((10, 10, 3), dtype=np.uint8), {}
        )
        _guard_details = "run_ocr_engine did not raise"
    except ValueError:
        pass

    # manual mode-এ unknown engine -> visible ValueError (নীরব skip নয়)
    try:
        ocr_region_with_fallback(
            np.zeros((60, 200, 3), dtype=np.uint8),
            {
                "id": 1,
                "region_type": "bubble",
                "x": 0,
                "y": 0,
                "width": 200,
                "height": 60,
                "angle": 0.0,
            },
            page_id="__chain_test__",
            engine_mode="__no_such_engine__",
        )
        _guard_details = "unknown manual mode did not raise"
    except ValueError:
        pass

    # Test 27-এর restore প্রমাণ: chain ও registry অক্ষত
    _restored = (
        MANGABD_CONFIG["ocr"]["fallback_chain"]
        == ["qwen", "openrouter_vision", "kellenok", "baberu"]
        and "__fake_ok__" not in MANGABD_CONFIG["ocr"]["engines"]
    )

    # wiring contract: cell-7 pipeline entrypoints-রা engine_mode নেয়
    _wired = all(
        "engine_mode" in _inspect.signature(fn).parameters
        for fn in (ocr_page, ocr_all_pages, ocr_region_with_fallback)
    )

    run_test(
        "OCR chain guards + wiring (M6-B1)",
        _guard_details == "" and _unload_noop and _restored and _wired,
        _guard_details or "guards/restore/wiring incomplete",
    )
except Exception as exc:
    run_test("OCR chain guards + wiring (M6-B1)", False, str(exc)[:160])


print()


# ═══════════════════════════════════════════════════════════
# 9. Optional live OCR test
# ═══════════════════════════════════════════════════════════'''
