#!/usr/bin/env python3
r"""MANGABD-006 B1 — cell 7 patch content (verbatim texts, raw literals)."""

# ── patch 7-1: engine adapters + fallback chain (insert before "# 6. OCR row builder") ──
CELL7_CHAIN = '''print("  ✅ Single region OCR ready")
print()


# ═══════════════════════════════════════════════════════════
# 5b. MANGABD-006 B1 — engine adapters + ordered fallback chain
# ═══════════════════════════════════════════════════════════

import time

# Chain success rule (Phase A §M3.3): একটা attempt তখনই success যখন তার
# text অাঁকা নয় এবং কোনো reject-marker নেই। Quality label
# (low_confidence / non_english) chain-failure নয় — chain retry করে
# FAILURE-এ, কখনো quality-তে নয় (adjudicated F12 principle)।
# [OCR_FAILED-শূন্য text গ্রহণ করা যাবে না কারণ QwenVLWrapper.recognize
# inference exception ধরে marker text return করে — directive-র literal
# "result.get("text")" check-এর উপরে এই marker-exclusion জরুরি।
_OCR_REJECT_MARKERS = ("[OCR_FAILED", "[EMPTY]", "[SKIP:OCR_FAILED")


def _ocr_chain_result_ok(result):
    """M6-B1: chain-level success predicate (empty / reject-marker = reject)।"""
    if not result:
        return False

    text = str(result.get("text", "") or "").strip()

    if not text:
        return False

    return not any(marker in text for marker in _OCR_REJECT_MARKERS)


def _crop_for_ocr_engine(image_bgr, region, page_id=None):
    """
    M6-B1: non-qwen adapter-দের জন্য crop — ocr_region-এর crop block
    verbatim (rotated branch + context crop + safe fallback)।
    """
    angle = float(region.get("angle", 0.0))

    try:
        if abs(angle) > 5.0 and "crop_region_rotated" in globals():
            return crop_region_rotated(image_bgr, region)

        return crop_bubble_with_context(
            image_bgr,
            region,
            context_ratio=0.15,
        )

    except Exception as exc:
        log_event(
            f"OCR crop failed [{page_id}:{region.get('id', '?')}]: {str(exc)[:100]}",
            level="WARN",
        )
        return np.zeros((10, 10, 3), dtype=np.uint8)


def _is_vertical_ocr_region(region):
    """
    V-3 Layer 1 predicate (REGION geometry — ocr_region-এর মতোই): লম্বা-
    সরু region হলে rotated-only ladder চলবে।
    """
    rw_ = int(region.get("width", 0))
    rh_ = int(region.get("height", 1))
    return rw_ < 90 and rh_ > 2 * max(1, rw_)


def _ocr_result_from_text(engine_name, text, vertical_ocr=None):
    """
    M6-B1: adapter tail — engine text থেকে production result dict
    (cell-5 heuristic confidence + language score + status label —
    per-engine criteria, কখনো cross-engine তুলনা নয়)।
    """
    cleaned = clean_ocr_output(str(text or ""))

    confidence = 0.0
    language_score = {
        "en": 0.0,
        "bn": 0.0,
        "unknown": 1.0,
    }

    if "_language_scores" in globals():
        language_score = _language_scores(cleaned)

    if "_estimate_ocr_confidence" in globals():
        confidence = _estimate_ocr_confidence(cleaned)

    warnings_list = []

    if vertical_ocr is not None:
        warnings_list.append(
            f"vertical OCR: chose {vertical_ocr['chosen_orientation']} "
            f"(candidates: {vertical_ocr['candidate_scores']})"
        )

    is_english = is_english_text(cleaned)

    status = get_ocr_status(cleaned, confidence, is_english)

    if status == "low_confidence":
        warnings_list.append("low OCR confidence")

    if status == "non_english":
        warnings_list.append("OCR output does not look English")

    return {
        "text": cleaned,
        "confidence": confidence,
        "engine": engine_name,
        "language_score": language_score,
        "warnings": warnings_list,
        "is_english": bool(is_english),
        "status": status,
        "vertical_ocr": vertical_ocr,
    }


def _run_vertical_ladder(read_fn, image):
    """
    V-3 Layer 1 (M6-B1 adapter copy): লম্বা-সরু region-এ rotated-only
    candidates — deterministic tie-break, ROTATE_90_CLOCKWISE থেকে strict
    '>' (ocr_region-এর semantics)।
    """
    candidates = []

    for orient_name, cand_img in (
        ("rotate_90_clockwise",
         cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)),
        ("rotate_90_counterclockwise",
         cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)),
    ):
        text = str(read_fn(cand_img) or "")
        score = 0.0

        if "_estimate_ocr_confidence" in globals():
            score += float(_estimate_ocr_confidence(text))

        if "_language_scores" in globals():
            score += float(_language_scores(text).get("en", 0.0))

        candidates.append(
            {
                "orientation": orient_name,
                "score": round(score, 4),
                "text": text,
            }
        )

    chosen = candidates[0]

    for cand in candidates[1:]:
        if cand["score"] > chosen["score"]:
            chosen = cand

    vertical_ocr = {
        "chosen_orientation": chosen["orientation"],
        "candidate_scores": {
            c["orientation"]: c["score"] for c in candidates
        },
    }

    return chosen["text"], vertical_ocr


def _ocr_region_onnx(engine_name, image_bgr, region, page_id=None):
    """
    M6-B1: kellenok / baberu ONNX adapter — raw crop (নিজস্ব internal
    preprocessing), vertical region-এ V-3 rotated-only ladder।
    """
    crop = _crop_for_ocr_engine(image_bgr, region, page_id=page_id)

    if (
        crop is None
        or crop.size == 0
        or crop.shape[0] < 5
        or crop.shape[1] < 5
    ):
        raise RuntimeError(f"crop too small for {engine_name}")

    engine = model_manager.ensure_ocr_engine(engine_name)

    if _is_vertical_ocr_region(region):
        text, vertical_ocr = _run_vertical_ladder(engine.read_text, crop)
    else:
        text = str(engine.read_text(crop) or "")
        vertical_ocr = None

    return _ocr_result_from_text(
        engine_name, text, vertical_ocr=vertical_ocr
    )


def _openrouter_vision_read(pil_img, spec, api_key):
    """
    M6-B1: একটা OpenRouter vision chat-completions call (timeout 30s,
    deterministic decode: temperature 0 — qwen-এর do_sample=False-এর
    API-side প্রতিদ্বন্দ্বী; max_tokens 512 = qwen-এর max_new_tokens)।
    """
    import base64
    import io

    from openai import OpenAI

    buffer = io.BytesIO()
    pil_img.convert("RGB").save(buffer, format="PNG")
    image_b64 = base64.b64encode(buffer.getvalue()).decode("ascii")

    prompt = MANGABD_CONFIG["ocr"].get("default_prompt")

    client = OpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://colab.research.google.com/",
            "X-Title": "MangaBD V12",
        },
    )

    response = client.chat.completions.create(
        model=str(spec.get("model", "google/gemini-2.0-flash-001")),
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image_b64}"
                        },
                    },
                    {"type": "text", "text": prompt},
                ],
            }
        ],
        temperature=0.0,
        max_tokens=512,
        timeout=30.0,
    )

    return str(response.choices[0].message.content or "")


def _ocr_region_openrouter(image_bgr, region, page_id=None):
    """
    M6-B1: openrouter_vision cloud adapter — production OCR prompt + base64
    crop (cell-8 translator-এর একই endpoint/key capture pattern — V-5)।
    Zero VRAM; key না থাকলে visible skip (chain পরের engine-এ যায়)।
    """
    import os

    spec = MANGABD_CONFIG["ocr"]["engines"]["openrouter_vision"]

    api_key = ""

    if "MANGABD_SECRETS" in globals():
        api_key = str(MANGABD_SECRETS.get("openrouter_api_key", "") or "")

    if not api_key:
        api_key = str(
            os.environ.get(
                spec.get("key_env", "OPENROUTER_API_KEY"), ""
            )
            or ""
        )

    if not api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY নেই — openrouter_vision skip হচ্ছে "
            "(Control Studio STEP 0 / Colab secret-এ key দাও)"
        )

    crop = _crop_for_ocr_engine(image_bgr, region, page_id=page_id)

    if (
        crop is None
        or crop.size == 0
        or crop.shape[0] < 5
        or crop.shape[1] < 5
    ):
        raise RuntimeError("crop too small for openrouter_vision")

    model_manager.ensure_ocr_engine("openrouter_vision")

    region_type = str(region.get("region_type", "bubble"))

    preprocessed = preprocess_for_ocr(crop, region_type=region_type)

    def _read_cloud(img_np):
        from PIL import Image as _PILImage

        return _openrouter_vision_read(
            _PILImage.fromarray(img_np.astype(np.uint8)),
            spec,
            api_key,
        )

    if _is_vertical_ocr_region(region):
        text, vertical_ocr = _run_vertical_ladder(_read_cloud, preprocessed)
    else:
        text = str(_read_cloud(preprocessed) or "")
        vertical_ocr = None

    return _ocr_result_from_text(
        "openrouter_vision", text, vertical_ocr=vertical_ocr
    )


def run_ocr_engine(engine_name, image_bgr, region, page_id=None):
    """
    M6-B1: single-engine adapter dispatch।

    qwen               -> existing ocr_region path verbatim (Phase A §M3.3)
    kellenok / baberu  -> ONNX adapters (vendored weights, CPU)
    openrouter_vision  -> cloud vision adapter (zero VRAM)
    """
    if engine_name == "qwen":
        return ocr_region(image_bgr, region, page_id=page_id)

    if engine_name in ("kellenok", "baberu"):
        return _ocr_region_onnx(
            engine_name, image_bgr, region, page_id=page_id
        )

    if engine_name == "openrouter_vision":
        return _ocr_region_openrouter(image_bgr, region, page_id=page_id)

    raise ValueError(f"No OCR adapter for engine {engine_name!r}")


def ocr_region_with_fallback(image_bgr, region, page_id=None, engine_mode=None):
    """
    M6-B1: chain-aware region OCR।

    engine_mode:
      - "auto" : fallback_chain ধরে চেষ্টা — প্রথম success-এ return
      - <name> : শুধু সেই একটা engine (manual) — fail হলে terminal
                 [SKIP:OCR_FAILED] (RF-4 guarantee: কখনো translation
                 হিসেবে apply হয় না)

    প্রতিটা attempt-এর {engine, outcome, ms} fallback_trace-এ জমে
    (additive sidecar field)। সব engine fail করলেই [SKIP:OCR_FAILED] —
    pipeline কখনো single engine-এর মৃত্যুতে আটকায় না (Phase A §M5)।
    """
    ocr_cfg = MANGABD_CONFIG["ocr"]

    if engine_mode is None:
        engine_mode = str(ocr_cfg.get("engine", "auto") or "auto")

    if engine_mode == "auto":
        engines = list(ocr_cfg.get("fallback_chain", ["qwen"]))
    elif engine_mode in ocr_cfg.get("engines", {}):
        engines = [engine_mode]
    else:
        raise ValueError(
            f"Unknown OCR engine mode: {engine_mode!r}. "
            f"Registry: {sorted(ocr_cfg.get('engines', {}).keys())}"
        )

    region_id = region.get("id", "?")

    # Region-property guard (Phase A §M5 row 4): ছোট crop কোনো engine-এর
    # দোষ নয় — আজকের [EMPTY] behavior অপরিবর্তিত, chain চালানো হয় না।
    precheck_crop = _crop_for_ocr_engine(image_bgr, region, page_id=page_id)

    if (
        precheck_crop is None
        or precheck_crop.size == 0
        or precheck_crop.shape[0] < 5
        or precheck_crop.shape[1] < 5
    ):
        return {
            "text": "[EMPTY]",
            "confidence": 0.0,
            "engine": "none",
            "language_score": {
                "en": 0.0,
                "bn": 0.0,
                "unknown": 1.0,
            },
            "warnings": ["crop too small"],
            "is_english": False,
            "status": "empty",
            "vertical_ocr": None,
            "fallback_trace": [],
        }

    fallback_trace = []

    for engine_name in engines:
        attempt_started = time.time()

        try:
            model_manager.ensure_ocr_engine(engine_name)

            result = run_ocr_engine(
                engine_name,
                image_bgr,
                region,
                page_id=page_id,
            )

            if _ocr_chain_result_ok(result):
                fallback_trace.append(
                    {
                        "engine": engine_name,
                        "outcome": "ok",
                        "ms": int((time.time() - attempt_started) * 1000),
                    }
                )

                result["fallback_trace"] = fallback_trace

                if len(fallback_trace) > 1:
                    print(
                        f"      🔁 OCR fallback [{page_id}:{region_id}]: "
                        f"recovered via {engine_name}"
                    )

                return result

            fallback_trace.append(
                {
                    "engine": engine_name,
                    "outcome": "rejected",
                    "ms": int((time.time() - attempt_started) * 1000),
                }
            )

        except Exception as exc:
            fallback_trace.append(
                {
                    "engine": engine_name,
                    "outcome": "error",
                    "ms": int((time.time() - attempt_started) * 1000),
                }
            )

            log_event(
                f"OCR engine {engine_name} failed on {page_id}:{region_id}: "
                f"{str(exc)[:120]}",
                level="WARN",
            )

        if engine_mode != "auto":
            break

    log_event(
        f"OCR chain exhausted [{page_id}:{region_id}] (mode={engine_mode}): "
        + " -> ".join(str(step["engine"]) for step in fallback_trace),
        level="ERROR",
    )

    return {
        "text": "[SKIP:OCR_FAILED]",
        "confidence": 0.0,
        "engine": "failed",
        "language_score": {
            "en": 0.0,
            "bn": 0.0,
            "unknown": 1.0,
        },
        "warnings": [
            "OCR chain exhausted (mode="
            + str(engine_mode)
            + "): "
            + " -> ".join(str(step["engine"]) for step in fallback_trace)
        ],
        "is_english": False,
        "status": "failed",
        "vertical_ocr": None,
        "fallback_trace": fallback_trace,
    }


print("  ✅ OCR fallback chain ready (M6-B1)")
print()


# ═══════════════════════════════════════════════════════════
# 6. OCR row builder
# ═══════════════════════════════════════════════════════════
'''

# ── patch 7-2: ocr_page signature + mode resolution ──
CELL7_OCR_PAGE_HEAD_OLD = '''def ocr_page(page_id, image_bgr=None, force=False):
    """
    একটা page-এর সব region OCR করে।

    Returns:
        ocr_results list
    """

    page = get_page(page_id, required=True)'''

CELL7_OCR_PAGE_HEAD_NEW = '''def ocr_page(page_id, image_bgr=None, force=False, engine_mode=None):
    """
    একটা page-এর সব region OCR করে।

    M6-B1: engine_mode — None হলে MANGABD_CONFIG["ocr"]["engine"] resolve
    হয় ("auto" বা কোনো registry engine)।

    Returns:
        ocr_results list
    """

    if engine_mode is None:
        engine_mode = str(
            MANGABD_CONFIG["ocr"].get("engine", "auto") or "auto"
        )

    page = get_page(page_id, required=True)'''

# ── patch 7-3: per-region call → chain ──
CELL7_REGION_CALL_OLD = '''            ocr_result = ocr_region(
                image_bgr,
                region,
                page_id=page_id,
            )'''

CELL7_REGION_CALL_NEW = '''            ocr_result = ocr_region_with_fallback(
                image_bgr,
                region,
                page_id=page_id,
                engine_mode=engine_mode,
            )'''

# ── patch 7-4: engine_counts init ──
CELL7_STATUS_COUNTS_OLD = '''    status_counts = {
        "ok": 0,
        "low_confidence": 0,
        "non_english": 0,
        "failed": 0,
        "empty": 0,
    }'''

CELL7_STATUS_COUNTS_NEW = '''    status_counts = {
        "ok": 0,
        "low_confidence": 0,
        "non_english": 0,
        "failed": 0,
        "empty": 0,
    }

    # M6-B1: per-engine counts (chain summary, Phase A §M5 row 5)
    engine_counts = {}'''

# ── patch 7-5: engine count on success ──
CELL7_COUNT_OK_OLD = '''            status = str(ocr_result.get("status", "ok"))
            status_counts[status] = status_counts.get(status, 0) + 1'''

CELL7_COUNT_OK_NEW = '''            status = str(ocr_result.get("status", "ok"))
            status_counts[status] = status_counts.get(status, 0) + 1

            result_engine = str(ocr_result.get("engine", "?"))
            engine_counts[result_engine] = (
                engine_counts.get(result_engine, 0) + 1
            )'''

# ── patch 7-6: failed_result engine label ──
CELL7_FAILED_ENGINE_OLD = '''            failed_result = {
                "text": f"[OCR_FAILED: {str(exc)[:30]}]",
                "confidence": 0.0,
                "engine": "qwen",'''

CELL7_FAILED_ENGINE_NEW = '''            failed_result = {
                "text": f"[OCR_FAILED: {str(exc)[:30]}]",
                "confidence": 0.0,
                # M6-B1: chain semantics — belt-and-braces path-টা কোনো
                # নির্দিষ্ট engine-এর নাম দাবি করে না, terminal state
                # রিপোর্ট করে
                "engine": "failed",'''

# ── patch 7-7: engine count on failure ──
CELL7_COUNT_FAIL_OLD = '''            status_counts["failed"] += 1'''

CELL7_COUNT_FAIL_NEW = '''            status_counts["failed"] += 1
            engine_counts["failed"] = engine_counts.get("failed", 0) + 1'''

# ── patch 7-8: stage meta ──
CELL7_META_OLD = '''            "ocr_region_count": len(rows),
            "ocr_engine": MANGABD_CONFIG["ocr"].get("engine", "qwen"),
            "ocr_status_counts": status_counts,'''

CELL7_META_NEW = '''            "ocr_region_count": len(rows),
            "ocr_engine": MANGABD_CONFIG["ocr"].get("engine", "auto"),
            "ocr_status_counts": status_counts,
            "ocr_engine_mode": engine_mode,      # M6-B1
            "ocr_engine_counts": engine_counts,  # M6-B1'''

# ── patch 7-9: chain summary print ──
CELL7_FINAL_PRINT_OLD = '''    print(
        f"    ✅ OCR done: "
        f"ok={status_counts.get('ok', 0)}, "
        f"low={status_counts.get('low_confidence', 0)}, "
        f"non_en={status_counts.get('non_english', 0)}, "
        f"failed={status_counts.get('failed', 0)}, "
        f"empty={status_counts.get('empty', 0)}"
    )

    return ocr_results'''

CELL7_FINAL_PRINT_NEW = '''    print(
        f"    ✅ OCR done: "
        f"ok={status_counts.get('ok', 0)}, "
        f"low={status_counts.get('low_confidence', 0)}, "
        f"non_en={status_counts.get('non_english', 0)}, "
        f"failed={status_counts.get('failed', 0)}, "
        f"empty={status_counts.get('empty', 0)}"
    )

    # M6-B1: engine-chain summary line (Phase A §M5 row 5)
    print(
        f"    ⛓️ OCR engine mode: {engine_mode} | engines: {engine_counts}"
    )

    return ocr_results'''

# ── patch 7-10: ocr_all_pages pass-through ──
CELL7_ALLPAGES_SIG_OLD = '''def ocr_all_pages(force=False):'''
CELL7_ALLPAGES_SIG_NEW = '''def ocr_all_pages(force=False, engine_mode=None):'''

CELL7_ALLPAGES_CALL_OLD = '''            page_results = ocr_page(page_id, force=force)'''
CELL7_ALLPAGES_CALL_NEW = '''            page_results = ocr_page(
                page_id, force=force, engine_mode=engine_mode
            )'''
