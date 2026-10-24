#!/usr/bin/env python3
r"""MANGABD-006 B2 runtime harness — executes the REAL post-build bytes.

The whole-notebook runtime is Flash Phase D + Owner live-retest
territory; this workspace-external harness proves the NEW code runs
correctly before the push:

  1. exec the REAL §9b section (compute_reading_order + helpers)
     extracted from the post-build cell 3 source, with a
     MANGABD_CONFIG stub matching the cell-1 CONFIG shape;
  2. exec the REAL build_ocr_row extracted from post-build cell 7
     (get_page stubbed to the real function's None-on-missing
     contract);
  3. run the REAL new battery block (Tests 26-30) extracted from
     post-build cell 8 with run_test/tests stubs;
  4. also drive the real payload_sort_page_rows / payload_sort_all_rows
     against the archived S001/S003/S005 detections.json geometry.
"""
import ast
import json
import sys

import pandas as pd

POST = "/home/z/my-project/cells_m006_b2_post"
REPO = "/home/z/my-project/MangaBD/samples"

c3_src = open(f"{POST}/cell_03.py", encoding="utf-8").read()
c7_src = open(f"{POST}/cell_07.py", encoding="utf-8").read()
c8_src = open(f"{POST}/cell_08.py", encoding="utf-8").read()


def extract_section(src, start_marker, end_marker):
    a = src.index(start_marker)
    b = src.index(end_marker, a)
    return src[a:b]


def extract_function(src, name):
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return ast.get_source_segment(src, node)
    raise SystemExit(f"function {name} not found")


# ── 1. real §9b section + config stub ───────────────────────
SECTION_9B = extract_section(
    c3_src,
    "# 9b. Reading order",
    "# 10. Initialize manifest",
)

MANGABD_CONFIG = {
    "reading_order": {
        "enabled": True,
        "overlay_note_position": "geometric",
        "payload_sort": "reading_order",
    },
}

ns = {"MANGABD_CONFIG": MANGABD_CONFIG, "pd": pd}
exec(SECTION_9B, ns)  # noqa: S102 — harness purpose
compute_reading_order = ns["compute_reading_order"]
payload_sort_page_rows = ns["payload_sort_page_rows"]
payload_sort_all_rows = ns["payload_sort_all_rows"]
ensure_reading_order_column = ns["ensure_reading_order_column"]
print("PASS  §9b section executes (compute_reading_order + 4 helpers bound)")

# ── 2. real build_ocr_row (cell 7) with get_page None-contract stub ──
BUILD_OCR_ROW = extract_function(c7_src, "build_ocr_row")
ns7 = {"get_page": lambda page_id, required=False: None}
exec(BUILD_OCR_ROW, ns7)  # noqa: S102
build_ocr_row = ns7["build_ocr_row"]
_row = build_ocr_row(
    "__none__",
    {"id": 3, "x": 10, "y": 20, "width": 5, "height": 5, "region_type": "bubble"},
    {"status": "ok", "text": "hello", "confidence": 0.9, "engine": "qwen"},
)
assert _row["reading_order"] == -1, "legacy region must emit -1"
_row2 = build_ocr_row(
    "__none__",
    {"id": 3, "reading_order": 2, "x": 10, "y": 20, "width": 5, "height": 5},
    {"status": "ok", "text": "hello"},
)
assert _row2["reading_order"] == 2, "present reading_order must pass through"
print("PASS  real build_ocr_row emits reading_order (-1 legacy / passthrough)")

# ── 3. real battery block (cell 8 Tests 26-30) ──────────────
BATTERY = extract_section(
    c8_src,
    "# MANGABD-006 B2: reading-order self-tests",
    "# Final status",
)
tests = []


def run_test(name, condition, details=""):
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {name}")
    if details and not condition:
        print(f"         {details}")
    tests.append(bool(condition))


ns8 = {
    "MANGABD_CONFIG": MANGABD_CONFIG,
    "pd": pd,
    "run_test": run_test,
    "compute_reading_order": compute_reading_order,
    "payload_sort_page_rows": payload_sort_page_rows,
    "payload_sort_all_rows": payload_sort_all_rows,
    "ensure_reading_order_column": ensure_reading_order_column,
    "build_ocr_row": build_ocr_row,
}
exec(BATTERY, ns8)  # noqa: S102

assert len(tests) == 5, f"expected 5 new tests, got {len(tests)}"
assert all(tests), "READING-ORDER BATTERY FAILED"
print("PASS  real cell-8 Tests 26-30 all green (5/5)")

# config restored by the block's finally?
assert MANGABD_CONFIG["reading_order"]["enabled"] is True
assert MANGABD_CONFIG["reading_order"]["payload_sort"] == "reading_order"
print("PASS  battery finally-restore verified (config intact)")

# ── 4. archived samples S001/S003/S005 ──────────────────────
VLM_CONFIRMED = [3, 2, 4, 5, 6, 1]
for sample in ["S001_color_webtoon", "S002_batch1", "S003_batch2",
               "S005_manual", "S005_openrouter"]:
    det = json.load(open(f"{REPO}/{sample}/detections.json"))
    order = compute_reading_order(det)
    df = pd.DataFrame([
        {"page_id": "p", "page": "02.jpg", "id": r["id"], "x": r["x"], "y": r["y"],
         "width": r["width"], "height": r["height"], "region_type": r["region_type"],
         "original_text": "t", "translated_text": ""}
        for r in det
    ])
    payload_ids = [int(v) for v in payload_sort_page_rows(df)["id"]]
    all_ids = [int(r["id"]) for _, r in payload_sort_all_rows(df).iterrows()]
    assert order == VLM_CONFIRMED == payload_ids, f"{sample}: {order} / {payload_ids}"
    assert all_ids == VLM_CONFIRMED, f"{sample} all_rows: {all_ids}"
    print(f"PASS  {sample}: compute == payload == VLM-confirmed [3,2,4,5,6,1]")

print("\nRUNTIME HARNESS: ALL GREEN")
