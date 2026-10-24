#!/usr/bin/env python3
r"""MANGABD-006 B2 (Phase C) — build driver.

Branch mangabd-006-b2 @ ec4a7f7. Target cells {1, 3, 7, 8, 22, 25} ONLY
(21 non-target cells asserted byte-identical). Implements the Owner
directive: region-level manga reading order — Phase A §M4.1 validated
algorithm (x-interval connected-component bands, RTL, top-to-bottom;
the directive's literal center-gap paraphrase FAILS its own S003 gate
— measured by scripts/m006_b2_algo_check.py, tau +0.467 vs +1.000 —
deviation disclosed in the Phase C record).

Patches:
  cell 1: CONFIG["reading_order"] (enabled/overlay_note_position/payload_sort)
  cell 3: TRANSLATION_DF_COLUMNS + reading_order; §9b algorithm +
          lazy-compat helpers; load-time + upsert-time ensure
  cell 7: build_ocr_row emits reading_order; ocr_page computes and
          assigns per region AFTER detection+OCR + persists
          additively (detections.json + ocr.json + df rows)
  cell 8: export_ai_text / build_translation_records_from_df sorts;
          translate_page LLM feed order; Tests 26-30
  cell 22: fallback copy-paste payload sort; coverage-report display
  cell 25: build_ai_text_content sort; Control Studio order_sel toggle

Patch mechanism: anchored exact-replace, each old-string
unique-asserted; the full (name, old, new) manifest is written to
scripts/m006_b2_patches.json. JSON writer proven byte-faithful on the
pre-edit file (same convention as the B1 build).
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/scripts")
from m006_b2_content3 import CELL3_SECTION_NEW
from m006_b2_content8 import CELL8_TESTS_NEW

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "ec4a7f7"
MANIFEST = "/home/z/my-project/scripts/m006_b2_patches.json"
TARGET_CELLS = {1, 3, 7, 8, 22, 25}

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-006-b2", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-006-b2 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
assert not tracked_dirty, f"tracked files dirty: {tracked_dirty}"
print("PASS  tracked tree clean")

with open(NB, "rb") as f:
    raw = f.read()
nb = json.loads(raw.decode("utf-8"))

rt = json.dumps(nb, indent=2, ensure_ascii=False)
assert rt.encode("utf-8") == raw, "round-trip writer is NOT byte-faithful!"
print("PASS  json writer byte-faithful on pre-edit file")

assert len(nb["cells"]) == 27
SRC0 = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}


def banner_before(src, marker):
    """The '# ═…' banner line immediately preceding `marker` in src."""
    idx = src.index(marker)
    bstart = src.rindex("# ", 0, idx)
    bend = src.index("\n", bstart) + 1
    return src[bstart:bend]


# ── 1. anchored patches ─────────────────────────────────────
SRC = dict(SRC0)
PATCHES = []


def apply(cell, name, old, new):
    src = SRC[cell]
    assert isinstance(old, str) and old, f"{name}: empty old anchor"
    cnt = src.count(old)
    assert cnt == 1, f"{name}: anchor occurs {cnt}x in cell {cell} (must be 1)"
    assert cell in TARGET_CELLS, f"{name}: cell {cell} not in scope {TARGET_CELLS}"
    SRC[cell] = src.replace(old, new)
    PATCHES.append({"cell": cell, "name": name, "old": old, "new": new})
    print(f"PASS  patch applied [cell {cell}] {name}")


# ---- CELL 1 ----
apply(
    1,
    "CONFIG reading_order section (M6-B2)",
    '''        "cache_detection": True,
    },

    # ── OCR ──''',
    '''        "cache_detection": True,
    },

    # ── Reading order (MANGABD-006 B2) ──
    "reading_order": {
        "enabled": True,                       # feature switch (compute + payload order)
        "overlay_note_position": "geometric",  # D2 default: geometric | first | last
        "payload_sort": "reading_order",        # Control Studio toggle (cell 25)
    },

    # ── OCR ──''',
)

# ---- CELL 3 ----
apply(
    3,
    "TRANSLATION_DF_COLUMNS + reading_order (M6-B2)",
    '''    "is_english",
    "bengali_valid",
    "status",
]''',
    '''    "is_english",
    "bengali_valid",
    "status",
    "reading_order",  # MANGABD-006 B2: manga reading order (0..N-1; -1 = legacy)
]''',
)

_c3_marker = "# 10. Initialize manifest + translation_df"
_c3_banner = banner_before(SRC[3], _c3_marker)
_c3_head = 'print("  ✅ translation_df persistence ready")\nprint()\n\n\n'
apply(
    3,
    "§9b reading-order algorithm + helpers (M6-B2)",
    _c3_head + _c3_banner + _c3_marker,
    _c3_head + CELL3_SECTION_NEW + "\n\n" + _c3_banner + _c3_marker,
)

apply(
    3,
    "load_translation_df lazy ensure (M6-B2)",
    '''            translation_df = translation_df[TRANSLATION_DF_COLUMNS]

            log_event(
                f"translation_df loaded: {len(translation_df)} rows",''',
    '''            translation_df = translation_df[TRANSLATION_DF_COLUMNS]

            # MANGABD-006 B2: legacy CSVs (no reading_order column) —
            # computed lazily from row geometry on load (backward-compat)
            ensure_reading_order_column(translation_df)

            log_event(
                f"translation_df loaded: {len(translation_df)} rows",''',
)

apply(
    3,
    "upsert_translation_rows ensure (M6-B2)",
    '''    translation_df = pd.concat(
        [translation_df, new_df],
        ignore_index=True,
    )

    save_translation_df()''',
    '''    translation_df = pd.concat(
        [translation_df, new_df],
        ignore_index=True,
    )

    # MANGABD-006 B2: normalize + lazily fill reading_order before save
    ensure_reading_order_column(translation_df)

    save_translation_df()''',
)

# ---- CELL 7 ----
apply(
    7,
    "build_ocr_row emits reading_order (M6-B2)",
    '''        "id": int(region.get("id", 0)),
        "region_type": str(region.get("region_type", "overlay")),''',
    '''        "id": int(region.get("id", 0)),
        "reading_order": int(region.get("reading_order", -1)),  # M6-B2
        "region_type": str(region.get("region_type", "overlay")),''',
)

apply(
    7,
    "ocr_page computes + assigns reading_order AFTER detection+OCR (M6-B2)",
    '''    # Save OCR artifact
    save_json_artifact(page_id, "ocr", ocr_results)''',
    '''    # MANGABD-006 B2: page-level reading order — computed from the final
    # detections geometry (Phase A §M4.1 validated algorithm: RTL column
    # bands via x-interval connected components; top-to-bottom within
    # band), assigned per region AFTER detection+OCR, persisted
    # additively (detections.json + ocr.json region objects + df rows).
    # V-3 vertical regions keep their in-region line order (M4.3).
    try:
        if MANGABD_CONFIG.get("reading_order", {}).get("enabled", True):
            _ro_ids = compute_reading_order(regions)
            _ro_map = {rid: i for i, rid in enumerate(_ro_ids)}
            for _ro_region in regions:
                _ro_region["reading_order"] = _ro_map.get(
                    int(_ro_region.get("id", -1)), 0
                )
            for _ro_row in rows:
                _ro_row["reading_order"] = _ro_map.get(
                    int(_ro_row.get("id", -1)), 0
                )
            save_json_artifact(page_id, "detections", regions)
            print(
                "    📖 Reading order: "
                + " → ".join(f"R{i}" for i in _ro_ids)
            )
    except Exception as _ro_exc:
        print(f"    ⚠️ Reading order skipped: {str(_ro_exc)[:80]}")

    # Save OCR artifact
    save_json_artifact(page_id, "ocr", ocr_results)''',
)

# ---- CELL 8 ----
apply(
    8,
    "export_ai_text reading-order sort (M6-B2)",
    '''        for page in pages:
            page_rows = translation_df[
                translation_df["page"] == page
            ].sort_values("id")''',
    '''        for page in pages:
            # MANGABD-006 B2: ai.Text export in reading order
            page_rows = payload_sort_page_rows(
                translation_df[translation_df["page"] == page]
            )''',
)

apply(
    8,
    "build_translation_records_from_df reading-order sort (M6-B2)",
    '''    page_rows = translation_df[
        translation_df["page_id"] == page_id
    ].sort_values("id")''',
    '''    # MANGABD-006 B2: records in reading order (translation.json inherits)
    page_rows = payload_sort_page_rows(
        translation_df[translation_df["page_id"] == page_id]
    )''',
)

apply(
    8,
    "translate_page LLM feed in reading order (M6-B2)",
    '''    page_mask = translation_df["page_id"] == page_id
    page_indices = translation_df.index[page_mask].tolist()''',
    '''    # MANGABD-006 B2: regions fed to the translator in reading order
    # (per-region prompts unchanged; feed order + log now match the
    # payload order the Owner copies)
    page_rows = payload_sort_page_rows(
        translation_df[translation_df["page_id"] == page_id]
    )
    page_indices = page_rows.index.tolist()''',
)

_c8_marker = "# Final status"
_c8_banner = banner_before(SRC[8], _c8_marker)
_c8_head = "    print()\n\n\n"
apply(
    8,
    "reading-order self-tests 26-30 (M6-B2)",
    _c8_head + _c8_banner + _c8_marker,
    _c8_head + CELL8_TESTS_NEW + _c8_banner + _c8_marker,
)

# ---- CELL 22 ----
apply(
    22,
    "fallback copy-paste payload reading order (M6-B2)",
    '''            for page in translation_df["page"].unique():
                page_rows = translation_df[
                    translation_df["page"] == page
                ].sort_values("id")''',
    '''            for page in translation_df["page"].unique():
                # MANGABD-006 B2: copy payload in reading order
                page_rows = payload_sort_page_rows(
                    translation_df[translation_df["page"] == page]
                )''',
)

apply(
    22,
    "apply coverage-report display order (M6-B2)",
    '''        _missing = []
        for _, _row in translation_df.iterrows():''',
    '''        _missing = []
        # MANGABD-006 B2: display in reading order (apply itself is
        # page:region_id-keyed — order-independent by construction)
        for _, _row in payload_sort_all_rows(translation_df).iterrows():''',
)

# ---- CELL 25 ----
apply(
    25,
    "build_ai_text_content reading-order sort (M6-B2)",
    '''    for pg in pages:
        prows=translation_df[translation_df["page"]==pg].sort_values("id")''',
    '''    for pg in pages:
        # MANGABD-006 B2: payload in reading order (M4.2 consumer switch)
        prows=payload_sort_page_rows(translation_df[translation_df["page"]==pg])''',
)

apply(
    25,
    "Control Studio order_sel toggle (M6-B2)",
    '''ocr_engine_sel.observe(_apply_ocr_engine_sel,names="value")
_apply_ocr_engine_sel()  # default দিয়ে CONFIG seed''',
    '''ocr_engine_sel.observe(_apply_ocr_engine_sel,names="value")
_apply_ocr_engine_sel()  # default দিয়ে CONFIG seed

# MANGABD-006 B2: payload sort toggle — Reading Order (default) বা
# Detection Order। copy payload / ai.Text export / translation records
# সবই এই CONFIG সেটিং মানে (single source of truth)।
order_sel=widgets.ToggleButtons(
    options=[("📖 READING ORDER","reading_order"),("🔢 DETECTION ORDER","id")],
    value="reading_order",button_style="info",layout=widgets.Layout(width="100%"))
try: order_sel.style.button_width="100%"
except Exception: pass

def _apply_order_sel(*_):
    # M6-B2: selection -> CONFIG (payload_sort)
    try: MANGABD_CONFIG["reading_order"]["payload_sort"]=order_sel.value
    except Exception: pass

order_sel.observe(_apply_order_sel,names="value")
_apply_order_sel()''',
)

apply(
    25,
    "order_sel into the manual copy panel (M6-B2)",
    '''                               btn_copy_ai,scope_sel,copy_page_dd,copy_out,
                               btn_load_src,ta_src,ta_tgt,btn_apply])''',
    '''                               btn_copy_ai,scope_sel,order_sel,copy_page_dd,copy_out,
                               btn_load_src,ta_src,ta_tgt,btn_apply])''',
)

# ── 2. scope + static gates ─────────────────────────────────
non_target = [i for i in range(27) if i not in TARGET_CELLS]
for i in non_target:
    assert SRC[i] == SRC0[i], f"cell {i} drifted!"
print(f"PASS  {len(non_target)} non-target cells byte-identical (scope exact: {sorted(TARGET_CELLS)})")

for i in range(27):
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        try:
            compile(SRC[i], f"cell_{i:02d}.py", "exec")
        except Warning as w:
            raise SystemExit(f"FAIL  cell {i} warning-as-error: {w}")
print("PASS  AST compile 27/27 (warnings-as-errors)")

for i in sorted(TARGET_CELLS):
    print(f"      cell {i:2d}: {SRC0[i].count(chr(10)) + 1} -> {SRC[i].count(chr(10)) + 1} lines")

# ── 3. write notebook (byte-faithful writer) ────────────────
for i in range(27):
    nb["cells"][i]["source"] = SRC[i].splitlines(keepends=True)

out_raw = json.dumps(nb, indent=2, ensure_ascii=False).encode("utf-8")
with open(NB, "wb") as f:
    f.write(out_raw)

with open(NB, "rb") as f:
    check = f.read()
assert check == out_raw, "post-write byte mismatch"

# non-source fields identical (only source arrays changed)
nb_check = json.loads(check.decode("utf-8"))
assert len(nb_check["cells"]) == 27
for i in range(27):
    old_cell, new_cell = json.loads(raw.decode("utf-8"))["cells"][i], nb_check["cells"][i]
    old_keys = {k: v for k, v in old_cell.items() if k != "source"}
    new_keys = {k: v for k, v in new_cell.items() if k != "source"}
    assert old_keys == new_keys, f"cell {i} non-source fields changed"
top_old = {k: v for k, v in json.loads(raw.decode("utf-8")).items() if k != "cells"}
top_new = {k: v for k, v in nb_check.items() if k != "cells"}
assert top_old == top_new, "top-level fields changed"
print("PASS  non-source + top-level fields identical")

# re-derivation proof: new == old + exactly the manifest patches
re_src = dict(SRC0)
for p in PATCHES:
    assert re_src[p["cell"]].count(p["old"]) == 1, f"re-derivation: {p['name']} anchor"
    re_src[p["cell"]] = re_src[p["cell"]].replace(p["old"], p["new"])
for i in range(27):
    assert re_src[i] == SRC[i], f"re-derivation mismatch cell {i}"
print("PASS  re-derivation equality (new == old + exactly these patches)")

with open(MANIFEST, "w", encoding="utf-8") as f:
    json.dump(PATCHES, f, ensure_ascii=False, indent=1)
print(f"\n-> {NB}")
print(f"-> {MANIFEST} ({len(PATCHES)} patches)")
print(f"notebook md5: {hashlib.md5(out_raw).hexdigest()}")
print("BUILD OK")
