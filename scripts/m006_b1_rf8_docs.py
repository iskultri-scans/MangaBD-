#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-8 — GLM_5_3.md documentation surgery.

Updates:
  1. CURRENT PHASE header: the M6-B1 entry rewritten to the RF-8 state
     (RF-7 delta CLOSED 0b5d11d -> Owner live retest (notebook-only
     session) exposed two first-run defects -> RF-8 delivered, awaiting
     Flash RF-8 delta check).
  2. New section PC1-C5 appended before the Phase C (Batch 1) record's
     tail line, which is itself updated.
Every edit is anchor-asserted; the file is written back in full.
"""
from pathlib import Path

DOC = Path("/home/z/my-project/MangaBD/agents/GLM_5_3.md")
text = DOC.read_text(encoding="utf-8")
orig_len = len(text)

# ── 1. CURRENT PHASE entry replacement ──────────────────────
head_marker = "**MANGABD-006 — PHASE C (BATCH 1 / M6-B1) DELIVERED @ `d569c08`;"
assert text.count(head_marker) == 1, "CURRENT PHASE anchor not unique"
start = text.index(head_marker)
end = text.index("\n", start)
old_entry = text[start:end]
assert old_entry.rstrip().endswith("[TEST RESULT]"), "entry tail unexpected"

new_entry = (
    "**MANGABD-006 — PHASE C (BATCH 1 / M6-B1): RF-7 DELTA CLOSED @ `0b5d11d`; OWNER LIVE RETEST (NOTEBOOK-ONLY COLAB) EXPOSED TWO FIRST-RUN DEFECTS; RF-8 (ONNXRUNTIME IN CELL 0 + DOWNLOAD HANG ROBUSTNESS) DELIVERED — AWAITING FLASH RF-8 DELTA CHECK (2026-10-20).** "
    "Chain so far: M6-B1 delivered @ `d569c08` -> Flash Phase D **APPROVED** @ `186af82` -> RF-7 (weights self-heal) + RF-6 (instrument fold-in) @ `a0e6bbf` -> Flash RF-7 delta **CLOSED** @ `0b5d11d` (D1 scope exact {5,7}, D2 vendored byte-unchanged + REAL sha-pinned downloads proven, D3 Test 29 audit + battery 10/10, D4 chain/eviction/guards + sim2 0 aborts, D5 18/18 instruments present incl. the int4 re-measurement artifact; merge gate = Owner live retest on a NOTEBOOK-ONLY Colab session exercising tier-2 auto-download end-to-end). "
    "That live retest (fresh Colab, only the notebook file) surfaced **two real defects**: (1) **onnxruntime missing from cell 0's pip-install list** — baberu's own diagnostic says \"Install: `!pip install onnxruntime`\" but cell 0 never installs it, so a first run degrades both local OCR engines instead of being a no-op; (2) **kellenok download hangs post-completion** — the owner log shows `det/manga_det_v0.2.onnx: 100% 1.82M/1.82M` and then a 10+ minute hang in post-download processing (the RF-7 downloader downloaded into the HF cache then `shutil.copyfile`-moved to the target — root-cause candidates: cache-copy blocking, symlinked cache-path sha re-read, or a lock held by an interrupted attempt). "
    "**RF-8 (this commit, cells {0, 5, 7} — directive-authorized scope; 24 non-target cells byte-identical to `0b5d11d`):** (a) **cell 0** — `\"onnxruntime>=1.31.0\"` added to `DETECTION_PACKAGES` (the RF-5/RF-7-verified version, floor-pinned per directive) so a fresh Colab first-run is a no-op for both ONNX engines; (b) **cell 5** — `_download_engine_file` refactored to `hf_hub_download(local_dir=…, force_download=False, revision=PINNED)` so HF writes the target dir DIRECTLY (the cache-path + copy move-step is gone entirely — the hang class is eliminated structurally), wrapped in a **per-file timeout** (`_ENGINE_DOWNLOAD_TIMEOUT_SECONDS = 300`, daemon worker + `join(timeout)` — a hang becomes a loud `TIMEOUT` RuntimeError instead of silence), and the `_ensure_engine_weights` download loop now **verifies each file's sha immediately and prints `[N/M] sha256=<8hex> size=<bytes> OK` after every file**; ANY sha mismatch or timeout fails loudly with the full RF-7 Bengali diagnostic (git-clone one-liner + Drive path) — never a silent fall-through (a post-download dest-is-file guard closes the last silent path); the vendored-present tier is byte-untouched (tier-1 verify + `_resolve_vendored_engine_dir` + `ensure_kellenok`/`ensure_baberu` + the `tried` string all byte-identical to `0b5d11d`, and the vendored R3 read reproduces the committed RF-5 measurement BYTE-EXACTLY with identical stdout); (c) **cell 7** — Test 29 extended with the directive's **download-then-hang simulation** (phase ঙ: monkey-patched `huggingface_hub.hf_hub_download` sleep-stub + patched `timeout=1s`, NO real network → asserts the timeout fires in <10 s wall AND the full diagnostic path is taken: TIMEOUT marker + the patched value + git-clone + Drive), plus the two assertion updates the new fail-fast per-file verify REQUIRES (phase ক: downloader call count 3→1 — wrong bytes now stop at the first file; phase খ: the `[1/2]`/`[2/2]` progress lines asserted via stdout capture). Cell-7 battery **10/10**, cell-8 battery byte-untouched **25/25**, m002_sim_v2 **0 abort sites**. "
    "**Verification 81/81 ALL GREEN** (`scripts/m006_b1_rf8_verify.py`): V0 8/8 vendored sha; V1 static incl. re-derivation (post == `0b5d11d` + exactly the 12 anchored patches), byte-untouched spans, Test-29 hermeticity + hang-phase restore discipline; V2 fields; V3 runtime harness cells 5→7→8 — batteries 9/9 + 10/10 + 25/25, the hang-phase banner proves tier-2 ran inside the battery, and the post-cell-7 restoration of the timeout constant (300), `hf_hub_download`, the real downloader, and the registry pins are all asserted; V4 vendored-present behavior unchanged (byte-exact R3 + no download banner); V5 REAL-network self-heal — kellenok full 3/3 + **baberu FULL 5/5 incl. the ONNX trio** (~122 MB, discharging the Phase-D D-28 observation) with every sha == pin and visible `[1/3]`..`[3/3]` / `[1/5]`..`[5/5]` progress lines, offline re-run zero-output, the REAL timeout mechanism (hanging stub → TIMEOUT < 10 s → full diagnostic with per-file progress `সম্পন্ন 0/3`), wrong-bytes fail-fast (downloader called exactly ONCE) and corrupt-vendored refusal; V6 sim2 0 abort sites. Full record + disclosures D-29..D-35: \"# MANGABD-006 — PHASE C (BATCH 1)\" §PC1-C5 below. [TEST RESULT]"
)
text = text[:start] + new_entry + text[end:]

# ── 2. PC1-C5 section + tail update ─────────────────────────
tail_marker = ("— End of MANGABD-006 Phase C (Batch 1) record, now including the RF-7 "
               "weights self-heal + RF-6 instrument fold-in. Branch `mangabd-006-b1` @ "
               "the RF-7 commit (parent `186af82`); awaiting the Flash RF-7 delta "
               "check on the pushed bytes.")
assert text.count(tail_marker) == 1, "tail anchor not unique"

pc1c5 = r"""## PC1-C5 RF-8: onnxruntime in cell 0 + download hang robustness (Owner notebook-only live retest fix) (GLM-5.3, 2026-10-20)

Directive: PM relay — the Owner live-tested `mangabd-006-b1` @ `a0e6bbf` on a **fresh, notebook-only Colab session** (the Phase-D merge-gate item: exercise tier-2 auto-download end-to-end). Two real defects surfaced. [FACT]

**Defect 1 — onnxruntime missing from cell 0.** baberu's engine diagnostic correctly says "Install: `!pip install onnxruntime`" but cell 0's pip-install groups never included it, so on a fresh Colab the loader refuses gracefully but the first-run UX is a preventable engine-degradation. Fix: `"onnxruntime>=1.31.0"` added to `DETECTION_PACKAGES` in cell 0 (alongside pyclipper; the version GLM/Flash verified in RF-5/RF-7 = 1.31.0, floor-pinned per directive). Cell 0 was previously out of scope per the M6-B1 disclosure D-7 — this directive explicitly authorizes the cell-0 touch, superseding D-7. [FACT]

**Defect 2 — kellenok download hangs post-completion.** Owner log: `det/manga_det_v0.2.onnx: 100% 1.82M/1.82M [00:00<00:0` … then hung 10+ minutes: `hf_hub_download` completed but the subsequent processing (RF-7's cache-path → `shutil.copyfile` → target move, then sha-verify) blocked. Root-cause candidates from the directive: (a) the post-download copy blocking on a partially-locked cache dir; (b) sha re-read on a symlinked/hardlinked cache path with odd Colab access semantics; (c) a lock held by an interrupted previous attempt. **Fix (directive-literal, eliminates the class structurally):**
- `_download_engine_file` now calls `hf_hub_download(local_dir=<target>, force_download=False, revision=PINNED)` — HF stages inside `local_dir/.cache/huggingface/` and completes with a same-filesystem move into place; **there is no cache-path copy step at all anymore** (candidate (a) and (b) removed by construction; (c) is contained by the timeout below).
- **Per-file timeout** (`_ENGINE_DOWNLOAD_TIMEOUT_SECONDS = 300`): the call runs in a daemon worker thread + `join(timeout)`; on expiry a loud `RuntimeError` ("TIMEOUT: <file> download 300s-এ শেষ হয়নি … Kernel restart করে আবার চালাও — সম্পূর্ণ ফাইল sha-verify হয়ে থাকলে আর download হবে না, বাকিগুলো resume হবে।") propagates into the full RF-7 diagnostic — a hang can no longer be silent. Python threads are unkillable, so the timed-out worker lingers until it finishes or the kernel restarts (daemon ⇒ it never blocks interpreter exit); disclosed as D-31.
- **Per-file immediate sha-verify + visible progress**: after every downloaded file the loop verifies its sha against the pin and prints `[N/M] sha256=<8hex> size=<bytes> OK`; a mismatch raises at that file (fail-fast — the next file is never attempted) and the wrapped diagnostic's what-tried line now reports the stuck file + the completed count ("…শেষ চেষ্টা: <rel> (সম্পন্ন N/M)।").
- **Never-silent discipline**: ANY sha mismatch or timeout → the full RF-7 Bengali diagnostic (git-clone one-liner + Drive alternative); plus a post-download `dest.is_file()` guard that turns any local_dir/path-mismatch surprise into a loud error.
- The belt-and-braces full-bundle `_verify_engine_weights` after the loop is retained (pre-existing tampered files in a partial target are still caught there).

**Vendored-present behavior byte-unchanged (RF-7 guarantee inherited):** tier-1 (vendored complete → sha-verify → use, zero network) is untouched — `_resolve_vendored_engine_dir`, `ensure_kellenok`, `ensure_baberu`, the registry pins, and the `tried` string are byte-identical to `0b5d11d` (asserted as spans in V1), and the vendored R3 read reproduces the committed RF-5 measurement byte-exactly with identical stdout (V4).

**Test 29 extension (cell 7) — hermetic, no real network anywhere:**
- **Phase ঙ (new, the directive's hang simulation):** real `_download_engine_file` + monkey-patched `huggingface_hub.hf_hub_download` = `time.sleep(30)` stub + patched global `timeout = 1 s` → asserts the refusal carries the TIMEOUT marker + the patched value ("1s") + git-clone + Drive, and wall-clock < 10 s (the timeout genuinely fired rather than the sleep completing). hf_hub_download + the downloader + the timeout global are all restored in a `finally` (the daemon stub-thread dies silently ≤30 s later).
- **Phase ক (assertion update REQUIRED by fail-fast):** wrong-bytes downloads now stop at the FIRST file, so the downloader call count assertion changes 3→1 (kellenok + baberu both: exactly one call, at a pinned file, with pinned repo+rev).
- **Phase খ (progress assertion):** the fake-pin download flow runs under `contextlib.redirect_stdout` and asserts the `[1/2] sha256=…` / `[2/2] sha256=…` progress lines + ` OK`.
- Phases গ/ঘ (vendored-valid zero-network, vendored-corrupt refusal) unchanged.

**Verification — 81/81 ALL GREEN (`scripts/m006_b1_rf8_verify.py`):**
- **V0** 8/8 vendored-file sha256 (unchanged bytes).
- **V1 static:** AST 27/27; **24 non-target cells byte-identical to `0b5d11d`** (RF-8 touches exactly {0, 5, 7}); re-derivation equality (post == `0b5d11d` + exactly the 12 anchored patches, manifest `scripts/m006_b1_rf8_patches.json`); cell-0 pin present once in DETECTION_PACKAGES and absent everywhere else; timeout constant + downloader mechanics (local_dir/force_download/revision kwargs, daemon+join+is_alive, dest guard, patched-global read); per-file fail-fast verify + progress format; byte-untouched spans (`_resolve_vendored_engine_dir`, `ensure_kellenok`/`ensure_baberu`, `tried`, registry pins); Test-29 extension markers + hermeticity + restore discipline.
- **V2** non-source + top-level notebook fields identical.
- **V3 runtime harness** (cells 5 → 7 → 8, the RF-7 mocked-globals harness + the same disclosed single-substring `/root` cache redirect; torch 2.14.1+cpu — D-26 class): cell 5 battery **9/9**; cell 7 battery **10/10** (zero ❌; the hang-phase's 0-MB fake-pin download banner proves tier-2 ran inside the battery); cell 8 **25/25**; post-cell-7 restorations asserted (timeout constant 300, `hf_hub_download` original, real bound downloader, registry pins == manifest).
- **V4 vendored-present behavior:** kellenok manual R3 read **BYTE-EXACT vs the committed RF-5 measurement**, stdout identical to M6-B1/RF-7 (load banner, no download banner, no progress lines); baberu int4 manual R3 read.
- **V5 REAL-network self-heal behavior:** vendored-present downloader tripwire (0 calls); REAL `local_dir` downloads — kellenok **3/3** and **baberu FULL 5/5 (incl. the ONNX trio, ~122 MB — Phase-D observation D-28 discharged)**, every sha == pin, progress lines `[1/3]`..`[3/3]` and `[1/5]`..`[5/5]` with sha8+size+OK captured from the flow; offline re-run of the completed bundle returns the same dir with ZERO download output; the REAL timeout mechanism proven twice (direct call → TIMEOUT < 10 s; full `_ensure_engine_weights` → the complete Bengali diagnostic with git-clone + Drive + "সম্পন্ন 0/3"); wrong-bytes download → fail-fast refusal with the downloader called exactly ONCE; corrupt vendored → refusal, downloader never called.
- **V6** m002_sim_v2 on the post-build extraction: **ABORT-CLASS findings (unguarded, unresolvable): 0**.

**Interpretation disclosures for the Flash delta check:**
- **D-29 Cell-0 scope expansion:** cell 0 enters the touched set per this directive (D-7's "onnxruntime NOT in cell 0 (out of scope)" disclosure is superseded — the defect it documented is now fixed); the pin is the floor form `>=1.31.0` per the directive's literal text; placement in `DETECTION_PACKAGES` (the group carrying pyclipper, the OCR-det dependency group).
- **D-30 Fail-fast per-file verify (production-semantics delta, required by the directive's per-file progress + never-silent rules):** previously ALL missing files downloaded then verified together (a bad download still fetched the rest; Test 29 phase ক saw 3 downloader calls); now verification is immediate per file so a bad first file stops the loop (1 call). Refusal class, diagnostic content, and refusal triggers are unchanged — only the point in time the refusal fires moves earlier. Test 29 phase ক's call-count assertion updated 3→1 as a direct consequence (disclosed as a test-semantics change, not a coverage reduction: the pinned repo+rev+file assertion is retained).
- **D-31 Timeout mechanism:** daemon worker thread + `join(timeout)`; on expiry the main flow raises immediately but the worker is unkillable and may linger in the background (holds no shared state; dies at kernel restart; the diagnostic advises the restart). The timeout value is read at call time from the module global `_ENGINE_DOWNLOAD_TIMEOUT_SECONDS` (default 300) so the self-test can patch it to 1 s — the value is a floor, not a max: fast networks never see it; it exists to convert a silent 10-minute-plus hang into a loud failure.
- **D-32 local_dir staging side-effect:** HF writes its transfer metadata under `<target>/.cache/huggingface/` inside the models dir; tier-1 completeness checks and `_verify_engine_weights` look only at the pinned relpaths, so the staging dir is invisible to the contract (disclosed; harmless on Colab/Drive).
- **D-33 Progress-line semantics:** M = files missing in THIS run (a partial bundle shows the remaining count; the banner keeps the missing/pins ratio); N counts completed downloads; the printed sha is the actual on-disk sha (== the pin, else refusal fires first) and the size is the byte count.
- **D-34 baberu ONNX trio re-fetched in-harness (D-28 discharged):** the RF-8 verify re-downloaded the FULL baberu int4 bundle (5/5, ~122 MB, every sha == pin) through the NEW local_dir path — the RF-7 gap (only the tokenizer pair was re-fetched) is closed; kellenok full 3/3 re-verified through the new path as well.
- **D-35 Harness environment:** torch 2.14.1+cpu (the RF-7 session's 2.9.1+cu128 env was recycled with the sandbox; same real-torch full-cell-exec class, D-26 lineage), onnxruntime 1.31.0 (the pin), huggingface_hub 2.2.0, transformers 5.20.2; the torch-bearing spans of cell 5 are byte-identical to `0b5d11d` (V1), so the prior real-torch records transfer.
- **Known-opens (non-blocking, carried):** the Phase-D cross-candidate mixed-state redundant-download nit (a candidate dir with SOME valid files while another candidate holds the complete bundle → tier-2 tops up instead of switching) — out of RF-8 scope, unchanged; HF rate-limit warning on unauthenticated downloads (harmless, `HF_TOKEN` optional); the ~145 MB first-run download shares Colab bandwidth with qwen's hub fetches by design.

"""

text = text.replace(
    tail_marker,
    pc1c5
    + "— End of MANGABD-006 Phase C (Batch 1) record, now including RF-7 (weights self-heal + RF-6 fold-in) and RF-8 (onnxruntime in cell 0 + download hang robustness). Branch `mangabd-006-b1` @ the RF-8 commit (parent `0b5d11d`); awaiting the Flash RF-8 delta check on the pushed bytes.")

DOC.write_text(text, encoding="utf-8")
print(f"GLM_5_3.md: {orig_len} -> {len(text)} bytes (+{len(text)-orig_len})")
print("OK")
