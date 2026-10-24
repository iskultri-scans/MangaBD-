"""MANGABD-006 B2 content — cell 8 battery addition (Tests 26-30).

Self-contained reading-order tests per the M6-B2 directive:
single-column page / two-column manga / vertical T/L note (S003 gate,
embedded archived geometry) / overlay_note_position variants /
backward compat (legacy df without the reading_order column, id
toggle, disabled fallback, build_ocr_row -1 emission).
"""

CELL8_TESTS_NEW = '''# MANGABD-006 B2: reading-order self-tests (Phase A §M4.1 algorithm;
# the archived S003 geometry embedded verbatim from
# samples/S003_batch2/detections.json so the battery is self-contained)
_ro_saved_cfg = None
try:
    _ro_saved_cfg = dict(MANGABD_CONFIG.get("reading_order", {}))
    MANGABD_CONFIG["reading_order"] = {
        "enabled": True,
        "overlay_note_position": "geometric",
        "payload_sort": "reading_order",
    }

    # Test 26: single-column page — all regions one band, y-order
    _ro_single = [
        {"id": 1, "x": 110, "y": 360, "width": 190, "height": 60, "region_type": "bubble"},
        {"id": 2, "x": 120, "y": 200, "width": 180, "height": 60, "region_type": "bubble"},
        {"id": 3, "x": 100, "y": 40,  "width": 200, "height": 60, "region_type": "bubble"},
    ]
    run_test(
        "M6-B2 single-column page (one band, y-order)",
        compute_reading_order(_ro_single) == [3, 2, 1],
        str(compute_reading_order(_ro_single)),
    )

    # Test 27: two-column manga — rightmost band first, y within
    _ro_2col = [
        {"id": 1, "x": 20,  "y": 100, "width": 80,  "height": 60, "region_type": "bubble"},
        {"id": 2, "x": 30,  "y": 300, "width": 70,  "height": 60, "region_type": "bubble"},
        {"id": 3, "x": 400, "y": 90,  "width": 120, "height": 60, "region_type": "bubble"},
        {"id": 4, "x": 410, "y": 320, "width": 110, "height": 60, "region_type": "bubble"},
    ]
    run_test(
        "M6-B2 two-column manga (RTL bands, y-order within)",
        compute_reading_order(_ro_2col) == [3, 4, 1, 2],
        str(compute_reading_order(_ro_2col)),
    )

    # Test 28: archived S003 geometry — the VLM-confirmed gate
    # (R1 = the vertical T/L margin note: own leftmost band -> last)
    _ro_s003 = [
        {"id": 1, "x": 10,  "y": 81,  "width": 61,  "height": 298, "region_type": "overlay"},
        {"id": 2, "x": 218, "y": 110, "width": 87,  "height": 156, "region_type": "bubble"},
        {"id": 3, "x": 403, "y": 340, "width": 204, "height": 216, "region_type": "bubble"},
        {"id": 4, "x": 76,  "y": 361, "width": 103, "height": 109, "region_type": "bubble"},
        {"id": 5, "x": 197, "y": 672, "width": 128, "height": 140, "region_type": "bubble"},
        {"id": 6, "x": 101, "y": 880, "width": 131, "height": 204, "region_type": "bubble"},
    ]
    _ro_gate = compute_reading_order(_ro_s003)
    run_test(
        "M6-B2 S003 gate == VLM-confirmed R3->R2->R4->R5->R6->R1 (tau +1.000)",
        _ro_gate == [3, 2, 4, 5, 6, 1],
        str(_ro_gate),
    )

    # Test 29: overlay_note_position variants (D2 default = geometric)
    run_test(
        "M6-B2 overlay_note_position geometric/first/last (D2)",
        (
            compute_reading_order(_ro_s003, overlay_note_position="geometric") == [3, 2, 4, 5, 6, 1]
            and compute_reading_order(_ro_s003, overlay_note_position="first") == [1, 3, 2, 4, 5, 6]
            and compute_reading_order(_ro_s003, overlay_note_position="last") == [3, 2, 4, 5, 6, 1]
        ),
    )

    # Test 30: backward compat — legacy df WITHOUT the reading_order
    # column computes lazily from geometry; the id toggle and the
    # disabled switch fall back to detection order; build_ocr_row
    # emits -1 for a legacy region lacking the field
    _ro_legacy = pd.DataFrame([
        {"page_id": "__ro_test__", "page": "ro_test.jpg", "id": r["id"],
         "region_type": r["region_type"], "x": r["x"], "y": r["y"],
         "width": r["width"], "height": r["height"],
         "original_text": "txt" + str(r["id"]), "translated_text": ""}
        for r in _ro_s003
    ])
    _ro_page_rows = _ro_legacy[_ro_legacy["page"] == "ro_test.jpg"]
    _ro_sorted_ids = [
        int(v) for v in payload_sort_page_rows(_ro_page_rows)["id"]
    ]
    _ro_ensured = ensure_reading_order_column(_ro_legacy.copy())
    _ro_ensured_by_id = [
        int(v) for v in _ro_ensured.sort_values(["id"])["reading_order"]
    ]
    _ro_row_legacy = build_ocr_row(
        "__ro_test__",
        {"id": 9, "x": 0, "y": 0, "width": 10, "height": 10},
        {"status": "ok", "text": "legacy"},
    )
    MANGABD_CONFIG["reading_order"]["payload_sort"] = "id"
    _ro_id_order = [
        int(v) for v in payload_sort_page_rows(_ro_page_rows)["id"]
    ]
    MANGABD_CONFIG["reading_order"]["payload_sort"] = "reading_order"
    MANGABD_CONFIG["reading_order"]["enabled"] = False
    _ro_disabled = [
        int(v) for v in payload_sort_page_rows(_ro_page_rows)["id"]
    ]
    run_test(
        "M6-B2 backward compat (lazy compute; id toggle; disabled; -1 row)",
        (
            _ro_sorted_ids == [3, 2, 4, 5, 6, 1]
            and _ro_ensured_by_id == [5, 1, 0, 2, 3, 4]
            and int(_ro_row_legacy.get("reading_order", -2)) == -1
            and _ro_id_order == [1, 2, 3, 4, 5, 6]
            and _ro_disabled == [1, 2, 3, 4, 5, 6]
        ),
        "sorted=" + str(_ro_sorted_ids) + " ensured=" + str(_ro_ensured_by_id)
        + " id=" + str(_ro_id_order) + " off=" + str(_ro_disabled),
    )
except Exception as _ro_exc:
    run_test("M6-B2 reading-order battery", False, str(_ro_exc)[:160])
finally:
    if _ro_saved_cfg is not None:
        try:
            MANGABD_CONFIG["reading_order"] = _ro_saved_cfg
        except Exception:
            pass

print()


'''
