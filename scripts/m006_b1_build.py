#!/usr/bin/env python3
r"""MANGABD-006 B1 (Phase C) — build driver.

Branch mangabd-006-b1 @ 86d4bdf. Target cells {5, 7, 15, 25} ONLY
(23 non-target cells asserted byte-identical). Implements the PM
directive: OCR engine registry + lazy-load discipline (cell 5),
fallback chain + manual selection + chain self-tests 26-28 (cell 7),
engine_mode pipeline wiring (cell 15), OCR Engine dropdown (cell 25).

Patch mechanism: anchored exact-replace, each old-string unique-asserted;
the full (name, old, new) manifest is written to
scripts/m006_b1_patches.json so the verifier can re-derive
new == old + exactly these patches. JSON writer proven byte-faithful
on the pre-edit file (no re-serialization drift).
"""
import hashlib
import json
import subprocess
import sys
import warnings

sys.path.insert(0, "/home/z/my-project/scripts")
from m006_b1_content5 import CELL5_MM_METHODS, CELL5_ONNX_CLASSES, CELL5_REGISTRY
from m006_b1_content7 import (
    CELL7_ALLPAGES_CALL_NEW, CELL7_ALLPAGES_CALL_OLD, CELL7_ALLPAGES_SIG_NEW,
    CELL7_ALLPAGES_SIG_OLD, CELL7_CHAIN, CELL7_COUNT_FAIL_NEW,
    CELL7_COUNT_FAIL_OLD, CELL7_COUNT_OK_NEW, CELL7_COUNT_OK_OLD,
    CELL7_FAILED_ENGINE_NEW, CELL7_FAILED_ENGINE_OLD, CELL7_FINAL_PRINT_NEW,
    CELL7_FINAL_PRINT_OLD, CELL7_META_NEW, CELL7_META_OLD,
    CELL7_OCR_PAGE_HEAD_NEW, CELL7_OCR_PAGE_HEAD_OLD, CELL7_REGION_CALL_NEW,
    CELL7_REGION_CALL_OLD, CELL7_STATUS_COUNTS_NEW, CELL7_STATUS_COUNTS_OLD,
)
from m006_b1_content7b import CELL7_TESTS_NEW, CELL7_TESTS_OLD

REPO = "/home/z/my-project/MangaBD"
NB = f"{REPO}/MangaBD_V12_ipynb_txt.ipynb (3).txt"
NB_NAME = "MangaBD_V12_ipynb_txt.ipynb (3).txt"
BASE_REF = "86d4bdf"
MANIFEST = "/home/z/my-project/scripts/m006_b1_patches.json"
TARGET_CELLS = {5, 7, 15, 25}

# ── 0. preconditions ────────────────────────────────────────
cur_branch = subprocess.run(["git", "-C", REPO, "branch", "--show-current"],
                            capture_output=True, text=True).stdout.strip()
assert cur_branch == "mangabd-006-b1", f"on branch {cur_branch!r}"

cur_blob = subprocess.run(["git", "-C", REPO, "hash-object", NB],
                          capture_output=True, text=True, check=True).stdout.strip()
base_blob = subprocess.run(["git", "-C", REPO, "rev-parse", f"{BASE_REF}:{NB_NAME}"],
                           capture_output=True, text=True, check=True).stdout.strip()
assert cur_blob == base_blob, f"working blob {cur_blob[:12]} != {BASE_REF}"
print(f"PASS  branch mangabd-006-b1 + notebook blob == {BASE_REF} ({cur_blob[:12]}...)")

status = subprocess.run(["git", "-C", REPO, "status", "--porcelain"],
                        capture_output=True, text=True).stdout.strip().splitlines()
tracked_dirty = [ln for ln in status if ln and not ln.startswith("??")]
untracked = [ln for ln in status if ln.startswith("??")]
assert not tracked_dirty, f"tracked files dirty: {tracked_dirty}"
print(f"PASS  tracked tree clean ({len(untracked)} untracked — vendored models/ expected)")
for ln in untracked:
    print(f"        untracked: {ln[3:]}")

with open(NB, "rb") as f:
    raw = f.read()
nb = json.loads(raw.decode("utf-8"))

rt = json.dumps(nb, indent=2, ensure_ascii=False)
assert rt.encode("utf-8") == raw, "round-trip writer is NOT byte-faithful!"
print("PASS  json writer byte-faithful on pre-edit file")

assert len(nb["cells"]) == 27
SRC0 = {i: "".join(nb["cells"][i]["source"]) for i in range(27)}

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


# ---- CELL 5 ----
# 5-1 registry: replace the section-3 tail + section-4 header span
apply(
    5,
    "OCR engine registry (M6-B1)",
    '''print("  ✅ Async + GPU helpers ready")
print()


# ═══════════════════════════════════════════════════════════
# 4. Qwen VL OCR wrapper
# ═══════════════════════════════════════════════════════════''',
    CELL5_REGISTRY,
)

# 5-2 ONNX wrapper classes
apply(
    5,
    "ONNX engine wrapper classes (M6-B1)",
    '''print("  ✅ Qwen VL wrapper ready")
print()


# ═══════════════════════════════════════════════════════════
# 5. ModelManager
# ═══════════════════════════════════════════════════════════''',
    CELL5_ONNX_CLASSES,
)

# 5-3 ModelManager registry methods
apply(
    5,
    "ModelManager OCR registry methods (M6-B1)",
    '''    # ───────────────────────────────────────────────────────
    # Future OCR placeholder
    # ───────────────────────────────────────────────────────''',
    CELL5_MM_METHODS,
)

# ---- CELL 7 ----
apply(
    7,
    "engine adapters + fallback chain (M6-B1)",
    '''print("  ✅ Single region OCR ready")
print()


# ═══════════════════════════════════════════════════════════
# 6. OCR row builder
# ═══════════════════════════════════════════════════════════''',
    CELL7_CHAIN,
)

apply(7, "ocr_page signature + mode resolution", CELL7_OCR_PAGE_HEAD_OLD, CELL7_OCR_PAGE_HEAD_NEW)
apply(7, "per-region call -> chain", CELL7_REGION_CALL_OLD, CELL7_REGION_CALL_NEW)
apply(7, "engine_counts init", CELL7_STATUS_COUNTS_OLD, CELL7_STATUS_COUNTS_NEW)
apply(7, "engine count on success", CELL7_COUNT_OK_OLD, CELL7_COUNT_OK_NEW)
apply(7, "failed_result engine label", CELL7_FAILED_ENGINE_OLD, CELL7_FAILED_ENGINE_NEW)
apply(7, "engine count on failure", CELL7_COUNT_FAIL_OLD, CELL7_COUNT_FAIL_NEW)
apply(7, "stage meta engine fields", CELL7_META_OLD, CELL7_META_NEW)
apply(7, "chain summary print", CELL7_FINAL_PRINT_OLD, CELL7_FINAL_PRINT_NEW)
apply(7, "ocr_all_pages signature", CELL7_ALLPAGES_SIG_OLD, CELL7_ALLPAGES_SIG_NEW)
apply(7, "ocr_all_pages pass-through", CELL7_ALLPAGES_CALL_OLD, CELL7_ALLPAGES_CALL_NEW)
apply(7, "chain self-tests 26-28", CELL7_TESTS_OLD, CELL7_TESTS_NEW)

# ---- CELL 15 ----
apply(
    15,
    "run_ocr_all engine_mode signature",
    '''def run_ocr_all(force=False):
    """
    সব detected page-এ OCR চালায়।
    """''',
    '''def run_ocr_all(force=False, engine_mode=None):
    """
    সব detected page-এ OCR চালায়।

    M6-B1: engine_mode (None = MANGABD_CONFIG["ocr"]["engine"] resolve —
    Control Studio-র OCR Engine dropdown সেটাই update করে)।
    """''',
)

apply(
    15,
    "run_ocr_all mode banner",
    '''    print(f"  📖 OCR: {len(target_pages)} pages")
    print()''',
    '''    if engine_mode is None:
        engine_mode = str(
            MANGABD_CONFIG["ocr"].get("engine", "auto") or "auto"
        )

    print(f"  📖 OCR: {len(target_pages)} pages")
    print(f"  ⛓️ OCR engine mode: {engine_mode}")
    print()''',
)

apply(
    15,
    "run_ocr_all -> ocr_page pass-through",
    '''                ocr_page(page_id, force=force)''',
    '''                ocr_page(page_id, force=force, engine_mode=engine_mode)''',
)

apply(
    15,
    "run_detection_ocr_all engine_mode",
    '''def run_detection_ocr_all(force=False):
    """
    Detection + OCR একসাথে চালায়।
    """

    print("=" * 70)
    print("  Pipeline: Detection + OCR")
    print("=" * 70)
    print()

    run_detection_all(force=force)
    run_ocr_all(force=force)''',
    '''def run_detection_ocr_all(force=False, engine_mode=None):
    """
    Detection + OCR একসাথে চালায়।

    M6-B1: engine_mode OCR pipeline-এ নামিয়ে দেয়।
    """

    print("=" * 70)
    print("  Pipeline: Detection + OCR")
    print("=" * 70)
    print()

    run_detection_all(force=force)
    run_ocr_all(force=force, engine_mode=engine_mode)''',
)

# ---- CELL 25 ----
apply(
    25,
    "OCR Engine dropdown + observer (M6-B1)",
    '''scope_sel=widgets.ToggleButtons(  # MANGABD-004 B2: per-page scoping (A3.4-2)
    options=[("📄 THIS PAGE","page"),("📚 ALL PAGES","all")],
    value="page",button_style="info",layout=widgets.Layout(width="100%"))
try: scope_sel.style.button_width="100%"
except Exception: pass''',
    '''scope_sel=widgets.ToggleButtons(  # MANGABD-004 B2: per-page scoping (A3.4-2)
    options=[("📄 THIS PAGE","page"),("📚 ALL PAGES","all")],
    value="page",button_style="info",layout=widgets.Layout(width="100%"))
try: scope_sel.style.button_width="100%"
except Exception: pass

# MANGABD-006 B1: OCR engine selection — Auto (fallback chain) বা যেকোনো
# একটা registry engine (manual: fail হলে [SKIP:OCR_FAILED], fallback নেই)।
ocr_engine_sel=widgets.Dropdown(
    options=[
        ("Auto (fallback chain)","auto"),
        ("qwen","qwen"),
        ("openrouter_vision","openrouter_vision"),
        ("kellenok","kellenok"),
        ("baberu","baberu")
    ],
    value="auto",description="OCR Engine:",
    layout=widgets.Layout(width="100%"),style={"description_width":"95px"})

def _apply_ocr_engine_sel(*_):
    # M6-B1: selection -> CONFIG (single source of truth; pipeline
    # call-time-এ এটাই resolve হয়)
    try: MANGABD_CONFIG["ocr"]["engine"]=ocr_engine_sel.value
    except Exception: pass

ocr_engine_sel.observe(_apply_ocr_engine_sel,names="value")
_apply_ocr_engine_sel()  # default দিয়ে CONFIG seed''',
)

apply(
    25,
    "on_ocr passes engine_mode (M6-B1)",
    '''def on_ocr(_):
    console.clear_output(); say("Detect + OCR চলছে…","🔍")
    fn=_safe("run_detection_ocr_all","V12 Cell 11 চালাও")
    if fn:
        with console:
            try: fn()
            except Exception as e: print(f"❌ {e}")''',
    '''def on_ocr(_):
    console.clear_output(); say("Detect + OCR চলছে…","🔍")
    fn=_safe("run_detection_ocr_all","V12 Cell 11 চালাও")
    if fn:
        with console:
            # M6-B1: নির্বাচিত OCR engine pipeline-এ পাঠানো হয়
            try: fn(engine_mode=ocr_engine_sel.value)
            except Exception as e: print(f"❌ {e}")''',
)

apply(
    25,
    "STEP 1-2 section gains the dropdown (M6-B1)",
    '''    section("STEP 1–2 • INPUT + OCR",[btn_upload,btn_ocr]),''',
    '''    section("STEP 1–2 • INPUT + OCR",[btn_upload,ocr_engine_sel,btn_ocr]),  # M6-B1''',
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
