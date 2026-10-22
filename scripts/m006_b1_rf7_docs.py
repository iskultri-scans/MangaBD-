#!/usr/bin/env python3
r"""MANGABD-006 B1 RF-7 — GLM_5_3.md documentation surgery.

Updates:
  1. CURRENT PHASE header: the M6-B1 entry rewritten to the RF-7 state
     (delivered d569c08 -> Phase D APPROVED 186af82 -> Owner live-test
     20261019_192 -> RF-7 + RF-6 delivered, awaiting Flash delta).
  2. New section PC1-C4 appended before the Phase C (Batch 1) record's
     tail line, which is itself updated.
Every edit is anchor-asserted; the file is written back in full.
"""
from pathlib import Path

DOC = Path("/home/z/my-project/MangaBD/agents/GLM_5_3.md")
text = DOC.read_text(encoding="utf-8")
orig_len = len(text)

# ── 1. CURRENT PHASE entry replacement ──────────────────────
head_marker = "**MANGABD-006 — PHASE C (BATCH 1 / M6-B1: OCR ENGINE REGISTRY"
assert text.count(head_marker) == 1, "CURRENT PHASE anchor not unique"
start = text.index(head_marker)
end = text.index("\n", start)
old_entry = text[start:end]
assert old_entry.rstrip().endswith("[TEST RESULT]"), "entry tail unexpected"

new_entry = (
    "**MANGABD-006 — PHASE C (BATCH 1 / M6-B1) DELIVERED @ `d569c08`; FLASH PHASE D APPROVED @ `186af82`; OWNER LIVE-TEST PASSED THE UX GATE BUT EXPOSED THE WEIGHTS GAP; RF-7 (WEIGHTS SELF-HEAL) + RF-6 (INSTRUMENT FOLD-IN) DELIVERED — AWAITING FLASH RF-7 DELTA CHECK (2026-10-20).** "
    "M6-B1 (registry + fallback chain + lazy-load + manual selection + vendored weights, cells {5, 7, 15, 25}, 23 non-target byte-identical) was delivered on branch `mangabd-006-b1` @ `d569c08` and Flash Phase D verified it **APPROVED** @ `186af82` (E1 scope exact, E2 additive-merge + runtime-proven single-resident, E3 weights sha kellenok 3/3 + baberu 5/5 vs hub @ pinned revs with the int4 substitution ACCEPTABLE, E4 cloud zero-VRAM, E5 34/34 runtime checks incl. byte-exact R3 read + both-direction eviction, E6 13/13 disclosures adjudicated; non-blocking P2 = the Phase C instruments were absent from the pushed tree). "
    "**Owner live-test (Colab session 20261019_192)**: the new dropdown + manual selection + graceful-failure design WORKED (visible trace, no crash, `[SKIP:OCR_FAILED]` on all 6 regions when the engine failed) — but kellenok/baberu failed with \u201cweights \u09aa\u09be\u0993\u09df\u09be \u09af\u09be\u09df\u09a8\u09bf\u201d because the session had ONLY the notebook file, no repo `models/` tree and no Drive copy. "
    "**RF-7 (this commit)**: `_ensure_engine_weights(engine_name)` added to cell 5 — (1) vendored bytes found (repo-relative `models/<engine>/` or the documented Drive path `MODELS_DIR/<engine>`) → sha256-verified against the pins now EMBEDDED in the registry (`hf_repo`/`hf_revision`/`files{sha256,size}` per engine) → used, **zero network, behavior byte-for-byte unchanged**; (2) missing → AUTO-DOWNLOAD from the HF hub at the sha-pinned revisions (kellenok `b3b65cbd\u2026`, baberu `fdf292a1\u2026` int4 bundle), saved under `models/<engine>/`, every file sha256-verified, then loaded — one-time ~145 MB, subsequent runs offline; (3) any failure (network, missing, sha mismatch — vendored OR downloaded) → **expanded Bengali diagnostic**: what was tried + the exact `git clone https://github.com/iskultri-scans/MangaBD-.git` one-liner + the Drive path alternative. Refusal discipline: a sha mismatch NEVER loads silently and never auto-overwrites a corrupt file (user-directed remediation in the diagnostic). "
    "Call-site change: `ensure_kellenok`/`ensure_baberu` now call `_ensure_engine_weights`; `_resolve_vendored_engine_dir` kept byte-identical as the legacy path for pin-less engines. "
    "**New self-test 29** in cell 7 (the Tests 26-28 block): missing weights → downloader invoked with the pinned repo+revision+file set (monkey-patched downloader, **no real network**), wrong bytes → sha refusal; vendored-valid → verified+used with ZERO downloader calls; vendored-corrupt → refusal, zero network. "
    "RF-7 touched cells **{5, 7} only** — 25 non-target cells byte-identical to `d569c08` (cell-8 battery byte-untouched **25/25**, now exec'd 25/25 again), cell-7 battery now **10/10**, m002_sim_v2 **0 abort sites**. "
    "**Verification 64/64 ALL GREEN** (`scripts/m006_b1_rf7_verify.py`): vendored-present runtime through the new path reproduces the committed RF-5 kellenok R3 read BYTE-EXACTLY with identical stdout (no download banner); REAL sha-pinned HF downloads re-executed in-harness (kellenok 3/3 files + baberu tokenizer pair 2/2, every sha == pin — the pinned revisions still resolve); full self-heal flow proven on a hermetic empty dir; refusal + diagnostic paths proven for mismatch / network-down / corrupt-vendored. "
    "**RF-6 folded in** (Phase D P2 discharged): the Phase C + RF-7 instruments are now committed under `scripts/` (12 `m006_b1_*` + 4 `m006_b1_rf7_*` files: build/verify/precommit/extract/download instruments, patch manifests, the weights provenance manifest, and the baberu int4 re-measurement JSON the review had to reproduce independently). Full record + disclosures: \"# MANGABD-006 — PHASE C (BATCH 1)\" §PC1-C4 below. [TEST RESULT]"
)
text = text[:start] + new_entry + text[end:]

# ── 2. PC1-C4 section + tail update ─────────────────────────
tail_marker = "— End of MANGABD-006 Phase C (Batch 1) record. Branch `mangabd-006-b1` @ the WIP commit; awaiting Flash Phase D verification on the pushed bytes."
assert text.count(tail_marker) == 1, "tail anchor not unique"

pc1c4 = r"""## PC1-C4 RF-7: weights self-heal (Owner Colab live-test fix) + RF-6 instrument fold-in (GLM-5.3, 2026-10-20)

Directive: PM relay — the Owner live-tested `mangabd-006-b1` in Colab (session **20261019_192**). The new dropdown + manual selection + graceful-failure design **WORKED** (visible trace, no crash, `[SKIP:OCR_FAILED]` on all 6 regions when the engine failed), but kellenok/baberu failed with **"weights পাওয়া যায়নি"** — the Owner's Colab had only the notebook file, not the repo's vendored `models/` folder, and no Drive copy. Fix on `mangabd-006-b1`, cell-5 loader (+ self-test 29 in cell 7); fold in the pending RF-6 artifact-commit (the Phase D P2 recommendation). [FACT]

**Design — three-tier self-heal (directive-literal):**
1. **Vendored present** (repo-relative `models/<engine>/` CWD-relative, or the documented Drive path `MODELS_DIR/<engine>` — on Drive-mounted Colab that is `/content/drive/MyDrive/MangaBD_V12/models/<engine>`): sha256-verify every file against the embedded pins → use. **Zero network; behavior with vendored bytes present is byte-for-byte unchanged** (proven at runtime: identical stdout incl. the M6-B1 load banner, no download banner, and the kellenok R3 read reproduces the committed RF-5 measurement byte-exactly through the new path).
2. **Missing** → auto-download from the HF hub **at the sha-pinned revisions** — kellenok `b3b65cbd…` (3 files, 23.1 MB), baberu `fdf292a1…` int4 bundle (5 files, 122.3 MB; one-time ~145 MB total) — saved under `models/<engine>/`, **every file sha256-verified, then loaded**; subsequent runs find the local bundle and stay offline.
3. **Failure** (any tier: download exception, missing file, sha mismatch on vendored OR downloaded bytes) → **refusal + expanded Bengali diagnostic**: what was tried (candidate paths + the pinned repo@rev attempt with the file count), the root cause, and three remedies — (a) the exact `git clone https://github.com/iskultri-scans/MangaBD-.git` one-liner, (b) the Drive path alternative (copy `models/<engine>/` to `MODELS_DIR/<engine>`), (c) delete a partial/corrupt file and re-run (the download path retries by itself).

**Implementation (cells {5, 7} only):**
- **Cell 5:** (a) registry engine specs gain the provenance pins `hf_repo` / `hf_revision` / `files{relpath → sha256, size}` — the exact committed `scripts/m006_b1_weights_manifest.json` values (RF-5 A8 pins + the M6-B1 int4 pin); (b) module-level `_sha256_of_file` (1 MB chunk streaming — no memory blowup on the 122 MB vision file); (c) `ModelManager` gains `_engine_weights_candidates` (the two documented locations, `_resolve_vendored_engine_dir`'s order), `_download_engine_file` (the downloader: lazy `huggingface_hub.hf_hub_download` at the pinned revision + copy into place — the single monkey-patch surface), `_verify_engine_weights` (per-file pin check → refusal RuntimeError naming the file + expected/got sha prefixes), `_engine_weights_diagnostic` (the expanded Bengali message builder), and **`_ensure_engine_weights`** (the three-tier flow; target-dir rule: the first candidate dir that exists is completed in place — a half-copied Drive bundle heals itself — else a fresh `MODELS_DIR/<engine>`); (d) `ensure_kellenok`/`ensure_baberu` call `_ensure_engine_weights` instead of `_resolve_vendored_engine_dir` — **each function otherwise byte-identical** (verified as an exact one-line delta vs `d569c08`); `_resolve_vendored_engine_dir` kept byte-identical as the legacy path for pin-less engines (no removals).
- **Cell 7:** **Test 29** in the Tests 26-28 block — (ক) REAL pins + missing weights: the monkey-patched downloader is invoked exactly once per pinned file with the pinned repo+revision+filename (kellenok 3 @ `b3b65cbd…`, baberu 5 @ `fdf292a1…`), and deliberately wrong bytes → sha refusal whose message carries "sha mismatch" + the git-clone remedy; (খ) fake pins + missing weights: download → verify → use (files land in the target dir with matching sha); (গ) vendored-valid: verified + used with ZERO downloader calls (zero network); (ঘ) vendored-corrupt: refusal, zero network. All monkey-patching (candidates + downloader + the kellenok spec pins) save/restored in `finally`; hermetic per-phase tmp dirs; NO real network anywhere in the test.

**Verification — 64/64 ALL GREEN (`scripts/m006_b1_rf7_verify.py`):**
- **V0** 8/8 vendored-file sha256 (unchanged bytes).
- **V1 static:** AST 27/27 warnings-as-errors; **25 non-target cells byte-identical to `d569c08`** (RF-7 touches exactly {5, 7}); re-derivation equality (post == `d569c08` + exactly the 9 anchored patches, manifest `scripts/m006_b1_rf7_patches.json`); registry text carries every manifest revision + sha exactly once; `_resolve_vendored_engine_dir` byte-identical; `ensure_kellenok`/`ensure_baberu` differ from `d569c08` by exactly the one call-site line; wiring marker counts; Test-29 presence + hermeticity markers; cell-8 byte-untouched.
- **V2** non-source + top-level notebook fields identical.
- **V3 runtime harness** (cells 5 → 7 → 8, the M6-B1 mocked-globals harness + the same disclosed single-substring `/root` cache redirect): cell 5 battery **9/9**; cell 7 battery **10/10** (6 original + Tests 26-29, zero ❌); cell 8 **25/25**; runtime registry pins == provenance manifest (repo+rev+sha+size); Test 29 leaves the real pins restored.
- **V4 vendored-present behavior:** kellenok manual R3 read through the full new path = **BYTE-EXACT vs the committed RF-5 measurement**; stdout identical to M6-B1 (load banner present, no download banner); baberu int4 manual R3 read via the new path.
- **V5 self-heal behavior:** vendored-present → downloader NEVER called (assert-raise trap); **REAL sha-pinned HF downloads re-executed** — kellenok 3/3 + baberu tokenizer pair 2/2, every sha == pin (the pinned revisions still resolve on the hub today; kellenok downloaded in full, baberu's ONNX trio not re-fetched in-harness — E3 already live-verified that hub tree and the code path is identical per-file); full flow on a hermetic empty dir → download → verify → return dir; sha-mismatch refusal + diagnostic; network-down → expanded diagnostic (cause carried, remedies present); corrupt VENDORED bundle → refusal with no re-download.
- **V6** m002_sim_v2 on the post-build extraction: **ABORT-CLASS findings (unguarded, unresolvable): 0**.

**RF-6 fold-in (Phase D P2 discharged):** the Phase C + RF-7 instruments are now committed under `scripts/`: `m006_b1_download_weights.py`, `m006_b1_extract_cells.py`, `m006_b1_build.py` + `m006_b1_content5/7/7b.py` + `m006_b1_patches.json`, `m006_b1_weights_manifest.json`, `m006_b1_verify.py`, `m006_b1_precommit.py`, `m006_b1_baberu_int4_remeasure.py` + `m006_b1_baberu_int4_results.json` (the int4 re-measurement artifact the review had to reproduce independently), and the RF-7 set `m006_b1_rf7_content.py`/`m006_b1_rf7_build.py`/`m006_b1_rf7_verify.py`/`m006_b1_rf7_patches.json`. NOTE for reviewers: `m006_b1_precommit.py` and `m006_b1_verify.py` contain secret-scanner REGEX LITERALS (`ghp_…`/`sk-…` patterns used BY the scanners) and a fake `"sk-test"` test value — detection patterns, not secrets (the M6-B1 precommit's secret scan of the notebook+doc diff remains 0-hit; re-asserted for RF-7 in `scripts/m006_b1_rf7_precommit.py`). [FACT]

**Interpretation disclosures for the Flash delta check:**
- **D-21 Vendored-present strictness upgrade (disclosed behavior delta):** with vendored bytes present the load is stdout-identical and zero-network (proven), but a cold load now ALSO silently sha-verifies the bundle (kellenok ≈ 23 MB / baberu ≈ 122 MB streaming ≈ 0.1–1 s) and a previously-loading-but-corrupt bundle that would have failed inside onnxruntime with a cryptic error now refuses EARLY with the full diagnostic — strictly better failure mode, disclosed as the one vendored-path change. A COMPLETE valid bundle behaves exactly as `d569c08`.
- **D-22 sha mismatch → refusal, never silent use:** corrupt vendored or downloaded bytes are never loaded and never auto-overwritten (tamper safety); the diagnostic's remedy (c) tells the user to delete the bad file and re-run, which re-enters the download path. Refusal on the DOWNLOADED bytes additionally means a hub/pin drift surfaces loudly rather than loading different weights than were measured.
- **D-23 Download target rule:** first EXISTING candidate dir is completed in place (a partial repo-relative or Drive copy heals itself); else fresh `MODELS_DIR/<engine>` — Drive-persistent when Drive is mounted, session-local otherwise (the same MODELS_DIR convention as QWEN_DRIVE_CACHE). Partial-bundle completion means e.g. 2-of-3 Drive copies download only the missing file.
- **D-24 qwen / openrouter_vision untouched:** `ensure_qwen` keeps its transformers-hub + QWEN_DRIVE_CACHE path (self-healing by design); the cloud client has no weights. `_ensure_engine_weights` is wired only into `ensure_kellenok`/`ensure_baberu`; a pin-less engine spec falls back to the byte-identical legacy `_resolve_vendored_engine_dir` (that path is now unreachable for the two vendored engines but kept as the registry's generic contract).
- **D-25 Incomplete-dir handling:** a candidate dir that exists but lacks files counts as "missing" for those files (download fills them) — the directive's binary (vendored / missing) is implemented at FILE granularity within the two documented locations.
- **D-26 Harness environment note:** the cell-5 full-exec harness ran on torch 2.9.1+cu128 (cpu device) from the sandbox wheel cache — the M6-B1 session's 2.14.1 env is gone; same real-torch full-cell-exec class as V3 of the M6-B1 record, and the torch-bearing spans of cell 5 are byte-identical to `d569c08` (proved by V1), so the prior real-torch record transfers.
- **D-27 Tests 26-29 battery count:** cell 7's battery grows 9/10 → 10/10 with Test 29 (the cell-8 battery stays exactly 25/25 and byte-untouched); Test 29 continues the D-11 placement convention (global numbering from cell 8, block in cell 7).
- **D-28 baberu ONNX trio not re-downloaded in-harness:** the harness re-fetched kellenok in full (3/3, sha == pins) + the baberu tokenizer pair (2/2) to prove the pinned revisions resolve and the shas still hold; the three baberu ONNX files (≈122 MB) were not re-fetched — E3 already live-verified that exact hub tree at the same pinned revision via the HF API, the vendored bytes sha-match the pins (V0), and the downloader code path is identical per-file. Cheap to extend if Flash wants the full re-fetch.
- **Known-opens (non-blocking):** auto-download needs `huggingface_hub` (Colab ships it via transformers; a fresh local env without it surfaces the import error inside the diagnostic — no cell break); `HF_TOKEN` is optional (public repos; the hub warns about rate limits, not a failure); the ~145 MB first-run download shares Colab bandwidth with qwen's hub fetches by design.

"""

text = text.replace(tail_marker,
                    pc1c4
                    + "— End of MANGABD-006 Phase C (Batch 1) record, now including the RF-7 weights self-heal + RF-6 instrument fold-in. Branch `mangabd-006-b1` @ the RF-7 commit (parent `186af82`); awaiting the Flash RF-7 delta check on the pushed bytes.")

DOC.write_text(text, encoding="utf-8")
print(f"GLM_5_3.md: {orig_len} -> {len(text)} bytes (+{len(text)-orig_len})")
print("OK")
