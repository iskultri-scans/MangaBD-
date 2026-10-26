# MANGABD-008 B1 RF-13 — Evidence dump + root-cause statement

Owner directive (zai-web IM): "ROOT-CAUSE INVESTIGATION (NO more fixture
guesses)… Reproduce Owner's EXACT env… dump and report… Find WHO mutates
config/coverage cache to /tmp/MISSING-test-font.ttf BEFORE Test 9, and WHO
fails to restore it… Fix the ROOT CAUSE in the production path + fixture
save/restore… Decouple the gate… Deliver ONE commit with evidence dump +
root-cause statement + fix."

Instruments: `scripts/m008_b1_rf13_repro.py` (5-env verbatim matrix),
`scripts/m008_b1_rf13_dump.py` (assert-moment dump + mutation trace),
`scripts/m008_b1_rf13_build.py` + `m008_b1_rf13_patches.json` (10 anchored
patches), `scripts/m008_b1_rf13_verify.py` (35/35), `m008_b1_rf13_precommit.py`.
Cell 10 was executed VERBATIM (§3–§8 core + §10 battery, byte-exact from the
pushed RF-12 `5a84994`) in a simulated Owner Drive env.

## 1. Signature matrix (the ONLY env class that reproduces the Owner's live output)

| env class | T9 | T10 | T11 | T12 | = Owner? |
|---|---|---|---|---|---|
| R-A healthy Drive (Latin-less NotoSansBengali main + vendored JP fb) | pass | pass | pass | pass | no (12/12) |
| **R-G main font CONTAINS BASIC LATIN (Bengali+Latin font at font_regular)** | **fail** | **pass** | **pass** | **fail** | **YES — exact match** |
| R-C main = JP bytes at font_regular | fail | pass | fail | pass | no |
| R-D stale-bad ambient font_fallback (/tmp/MISSING-class) | pass | fail | fail | pass | no |
| R-E Latin main + stale-bad ambient | fail | fail | fail | fail | no |

The Owner's signature (T9+T12 fail, T10+T11 pass, post-run config correct,
`_FB_CACHE` empty) is reproduced by ONE class only: **the main font at
`MANGABD_CONFIG["rendering"]["font_regular"]` covers basic Latin** — i.e. the
Drive fonts-dir Bengali-regular file is NOT the Latin-less NotoSansBengali the
D-2 fixtures assume. The fallback side (which the Owner's diagnostic cells
validated) is innocent in every scenario.

## 2. Dump at the first failing assertion (Test 9, R-G env)

- `MANGABD_CONFIG["rendering"]["font_fallback"]` (pinned) = the real vendored-byte JP path — correct.
- `_FB_CACHE` = {} — empty at the assert moment.
- `_FONT_COVERAGE_CACHE` = {main-path: present, fb-path: present} — both cmaps read fine; no None entries.
- `_FONT_ROUTE_WARNED` = [] — no suppressed warnings.
- `get_font_fb(24)` = FreeTypeFont (loads). DIRECT probe = FreeTypeFont. No load failure anywhere.
- `_main_font_ok` decisions: "ক" U+0995 → **True** ✓ (D-1 fine), "।" U+0964 → **True** ✓ (danda in MAIN, D-1 fine), "こ" U+3053 → **False** ✓ (kana routes to fallback), **"a" U+0061 → True ✗ (fixture expects False)**, '"' U+0022 → True ✗, "—" U+2014 → True ✗.
- ok-chain verdicts: `_m9_probe is not None` PASS; `_main_font_ok("ক") is True` PASS; `_main_font_ok("।") is True` PASS; `_main_font_ok("a") is False` **FAIL (actual True)** — the `and` chain dies here ('"', "—" never evaluated; "こ" PASSes on its own).
- cmap ground truth: MAIN cmap 10,306 codepoints, covers {ক ✓ ঔ ✓ a ✓ " ✓ — ✓ H ✓ こ ✗}; FALLBACK (vendored JP) 16,732 codepoints, covers {ক ✗ ঔ ✗ a ✓ " ✓ — ✓ H ✓ こ ✓}.

**Rendering is tofu-free in this env** — every sample glyph exists in ≥1 font;
ASCII/dash/quote simply render from the MAIN font instead of the fallback.

## 3. WHO mutates config to /tmp/MISSING-test-font.ttf? — NOBODY before Test 9

Full `font_fallback` write trace across the whole battery (8 writes, chronological):
1. Test 9 pin ← registry (real JP path); 2. Test 9 finally-restore (real path);
3. Test 10 D-4 fixture pin → /tmp/MISSING-test-font.ttf; 4. Test 10 finally-restore;
5. Test 11 D-3 fixture pin → /tmp/MISSING-test-font.ttf; 6. Test 11 finally-restore;
7. Test 12 pin ← registry; 8. Test 12 finally-restore.

The FIRST /tmp/MISSING write is Test 10's D-4 fixture — **AFTER Test 9 has
already failed**. RF-12's "Test 10 pollutes cache before Test 9" theory is
chronologically impossible (Owner-stated) and trace-proven false; the finallys
restore everything (config + `_FB_CACHE`) — **fixture save/restore is sound;
nothing needs repair there.** The Owner-observed messages are both DESIGNED
fixture behavior, not leaks:

- "ERROR JP fallback font unavailable" = Test 10's D-4 WARN-never-silent proof
  (`warned` must be True for the test to pass). It is emitted through
  `log_event` → `logging` → **stderr**, while the ✅/❌ verdict lines are
  stdout — Colab's interleaved output area can displace stderr lines, which
  explains the Owner seeing it "right after choose_text_color". In true stdout
  order it belongs to Test 10. Exactly ONE such ERROR event exists per battery.
- "cmap coverage unavailable: /tmp/MISSING-test-font.ttf — range routing" =
  Test 11's D-3 canvas_b, whose fixture pins the missing path on purpose
  (fbcov unreadable → range-routing fallback). Fires after D-4. Benign.

## 4. ROOT CAUSE (one sentence)

Tests 9/12 (and the cells-11/12 §7.5 D-2 check) hardcode the DEFAULT font
set's charset SHAPE — "main must lack ASCII" (`_main_font_ok("a") is False`)
and "main must render H as a hollow .notdef" — while the Owner's Drive
`font_regular` file is a Bengali font that CONTAINS basic Latin; the correct
routing it produces (ASCII → main) fails the shape assertion, and the final
gate hard-blocks a pipeline whose actual rendering is tofu-free. The
production-path gap: cell 4 §8 only downloads a missing font_regular —
any other/wrong file at that path passes silently with zero diagnostics
in cells 1–9.

## 5. THE FIX (10 anchored patches, scope {4,10,11,12})

- **cell 4 §8.6 (production path):** main-font sanity check — PIL load +
  fontTools cmap; ক/। required (a non-Bengali file at font_regular → loud
  named ❌ + WARN event + delete/re-download fix route); Latin coverage →
  loud "basic Latin আছে" note (shape differs, tofu-free); registry gains
  `regular_sane`. Never raises (§8.5 contract).
- **cell 10 Test 9:** HARD = render integrity — probe loads (RF-12 kept) +
  tofu-scan: every sample glyph (ক । a " — こ) in ≥1 cmap, tofu chars NAMED
  on fail. DIAG (new `run_test_diag`, counted in `tests_diagnosed`, NOT in
  the ledger) = D-2 shape (ASCII/kana present in main).
- **cell 10 Test 12:** HARD = fb solid pixel-probe on BOTH "H" AND "こ"
  (fontTools-independent garbage guard; probe throw → RF-12's loud FAIL
  kept). Main-side .notdef calibration → 3-outcome DIAG (hollow ✓ silent /
  blank / solid-substitute / covers-all), never a hard fail — a font
  property, not render integrity.
- **cell 10 gate decoupling:** ledger = hard failures only; `all_tests_passed`
  mechanics unchanged; final status prints the 🔶 diag count; `log_event`
  gains `tests_diagnosed`. A diagnostic can no longer hard-block a
  tofu-free pipeline.
- **cell 10 fixture hygiene:** post-battery pop of the fixture-scoped
  `_FONT_COVERAGE_CACHE["/tmp/MISSING…"]` entry + `_FONT_ROUTE_WARNED["fb_load"]`
  (the only residues the trace found; finallys already restore config/cache).
- **cells 11/12 §7.5 D-2 (byte-identical mirrors):** re-scoped to
  tofu-semantics (kana/ASCII in ≥1 font) + "basic Latin" INFO note — the
  same root-cause class in the production vertical path.

## 6. Measured disclosures (honest, no-false-pass kept)

- **No-false-pass proofs (gate still raises):** main=JP bytes → T9 hard-fail
  naming U+0995/U+0964 (ক/। in NEITHER font — real tofu risk); garbage at
  vendored → probe throws → T9+T12 loud FAIL with the exception named
  (Flash's garbage-false-pass finding stays covered, now double-guarded by
  the こ pixel-probe); stale-bad ambient → T10+T11 loud FAIL (regression
  class preserved); vendored missing → RF-11 skip class preserved; _FB_CACHE
  pre-pollution → RF-12 immunity preserved (12/12).
- **Known separate limitation (measured, print-only, out of scope per the
  bounded-round rule):** with a BLANK/SOLID-notdef main (the FreeSerif-class
  repro), cells-11/12 §7.5 D-5 reports drawn=37 vs ref=44 — the vertical
  fit measures こ on MAIN-font metrics (documented at the renderer: "fit
  calibrates on main-font metrics only"), so a non-box-notdef main
  over-sizes the fit and the kana glyph clips in the narrow vertical
  column. §7.5 prints; it does not gate. If the Owner's font is in this
  subclass, D-5 will report it — that becomes the next bounded RF with the
  vertical-fit semantics mapped.
- The sandbox cannot observe the Owner's Colab stderr interleaving directly;
  the ERROR-line position claim is derived from the battery's trace (the
  message can only originate from Test 10's fixture call, which its own
  assertion requires to fire) plus log_event's logging→stderr channel.
