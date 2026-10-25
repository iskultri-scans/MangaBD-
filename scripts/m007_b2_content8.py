#!/usr/bin/env python3
r"""MANGABD-007 B2 (Phase C) — cell-8 patch content (S05-2).

S05-2: paste-back escape normalize — parse_ai_text unescape pipeline
hardening: (1) iterative unescape-to-stability (double-escaped tags
converge), (2) residual-escape validation WARN (never fail),
(3) trailing line-end backslash strip before the tag regex,
(4) Tests 31-32 (double-escaped + mixed-escape fixtures → 100% parse).
Target cell 8 ONLY; the build driver unique-asserts every anchor and
writes the manifest to m007_b2_patches.json (RF-9: instruments
committed in the Phase C commit).
"""

# 8-1: parse_ai_text docstring — step 1 gains the S05-2 semantics note.
CELL8_DOCSTRING_OLD = r'''        1. line-level markdown unescape: "\\[" → "[", "\\]" → "]"'''

CELL8_DOCSTRING_NEW = r'''        1. line-level markdown unescape: "\\[" → "[", "\\]" → "]"
           (MANGABD-007 B2 S05-2: ITERATIVE-to-stable, so
           double-escaped tags \\\\[tag\\\\] converge too; residual
           escaped brackets WARN but never fail; trailing line-end
           backslashes stripped before the tag regex)'''

# 8-2: stats dict — two new visible counters.
CELL8_STATS_OLD = r'''        "trailing_arrow": 0,  # RF-3: Bengali before an empty line-end arrow
        "marker_skipped": 0,  # RF-4: [SKIP]/special-marker translations
    }'''

CELL8_STATS_NEW = r'''        "trailing_arrow": 0,  # RF-3: Bengali before an empty line-end arrow
        "marker_skipped": 0,  # RF-4: [SKIP]/special-marker translations
        "escape_warn": 0,  # M007 B2 S05-2: residual \[ \] after unescape
        "trailing_backslash": 0,  # M007 B2 S05-2: line-end "\" stripped
    }'''

# 8-3: the unescape pipeline itself (B2 step 1) — S05-2 hardening.
CELL8_UNESCAPE_OLD = r'''    # B2 step 1: line-level markdown unescape (before any regex)
    lines = raw.splitlines()

    for i, line in enumerate(lines):
        if "\\[" in line or "\\]" in line:
            lines[i] = line.replace("\\[", "[").replace("\\]", "]")
            stats["unescaped"] += 1'''

CELL8_UNESCAPE_NEW = r'''    # B2 step 1: line-level markdown unescape (before any regex) —
    # MANGABD-007 B2 S05-2 hardening: (1) ITERATIVE unescape-to-stable
    # so double-escaped tags (\\[01.jpg:1\\] → [01.jpg:1]) converge,
    # (2) residual-escape validation WARN (never fail), (3) trailing
    # line-end backslash strip before the tag regex runs.
    lines = raw.splitlines()

    for i, line in enumerate(lines):
        if "\\[" in line or "\\]" in line:
            # S05-2 (1) iterative unescape: keep unescaping until
            # stable. Each pass strictly shortens the line while any
            # \[ / \] pair remains, so this loop provably terminates.
            while "\\[" in line or "\\]" in line:
                new_line = line.replace("\\[", "[").replace("\\]", "]")
                if new_line == line:
                    break  # stable — no pair survives a full pass
                line = new_line
            lines[i] = line
            stats["unescaped"] += 1

            # S05-2 (2) validate: residual escaped bracket after
            # convergence = pathological input → WARN + continue,
            # never fail (the parse below still reports the line if
            # its tag cannot match).
            if "\\[" in line or "\\]" in line:
                stats["escape_warn"] += 1
                log_event(
                    f"parse_ai_text: residual escaped bracket in "
                    f"line {i + 1}: {line[:80]!r} — continuing (S05-2)",
                    level="WARN",
                )
                print(
                    "  ⚠️ residual escaped bracket after unescape "
                    f"(line {i + 1}) — continuing (S05-2)"
                )

        # S05-2 (3) strip trailing backslashes before parsing —
        # clipboard/AI replies sometimes leave a line-end "\" that
        # would otherwise poison the tag match or the translation.
        if line.endswith("\\"):
            line = line.rstrip("\\")
            lines[i] = line
            stats["trailing_backslash"] += 1'''

# 8-4: Tests 31-32 battery — inserted after the M6-B2 reading-order
# battery, before the Final status section.
CELL8_TESTS3132_OLD = r'''    if _ro_saved_cfg is not None:
        try:
            MANGABD_CONFIG["reading_order"] = _ro_saved_cfg
        except Exception:
            pass

print()'''

CELL8_TESTS3132_NEW = r'''    if _ro_saved_cfg is not None:
        try:
            MANGABD_CONFIG["reading_order"] = _ro_saved_cfg
        except Exception:
            pass


# ── MANGABD-007 B2: S05-2 paste-back escape-hardening battery ──────
# MANGABD-005 B2-র RF-2 single-pass unescape তিনটা edge shape-এ আটকে
# যেত: (a) double-escaped tags — কোড-aware paste path থেকে
# escape-of-escape (content "\\[01.jpg:1\\]"), (b) mixed paste — কিছু
# line escaped, কিছু raw, (c) translation-এর পরে line-end backslash।
# S05-2 fix: iterative unescape-to-stable + residual-escape WARN
# (never fail) + trailing-backslash strip। Tests 31-32: 100% parse
# success প্রমাণ। Tests 16-21-এর sandbox pattern (deterministic
# empty-session translation_df)।
_saved_df_s05 = globals().get("translation_df", _B2_UNSET)
translation_df = pd.DataFrame()
try:
    # Test 31: double-escaped fixture → 100% parse success
    # (source literal "\\\\[01.jpg:1\\\\]" = content "\\[01.jpg:1\\]"
    #  — দুই স্তরের escape; single pass-এ এক স্তর টিকে থাকত)
    try:
        sample_31 = (
            "\\\\[01.jpg:1\\\\] Hello → হ্যালো\n"
            "\\\\[01.jpg:2\\\\] World → বিশ্ব"
        )

        parsed31 = parse_ai_text(sample_31)
        _sent31 = parsed31.get(("_unparsed", 0), {})
        _st31 = _sent31.get("stats", {})

        ok31 = (
            len(parsed31) == 3  # 2 entries + report sentinel
            and parsed31[("01.jpg", 1)]["original_text"] == "Hello"
            and parsed31[("01.jpg", 1)]["translated_text"] == "হ্যালো"
            and parsed31[("01.jpg", 2)]["original_text"] == "World"
            and parsed31[("01.jpg", 2)]["translated_text"] == "বিশ্ব"
            and _st31.get("unescaped") == 2
            and _st31.get("escape_warn", 0) == 0
            and _st31.get("trailing_backslash", 0) == 0
            and not _sent31.get("unparsed_lines")
        )

        run_test(
            "double-escaped fixture 100% parse (S05-2)",
            ok31,
            str(parsed31)[:200],
        )
    except Exception as exc:
        run_test("double-escaped fixture 100% parse (S05-2)", False, str(exc)[:160])

    # Test 32: mixed-escape fixture → 100% parse success
    # (escaped line + raw line + trailing-backslash line + escaped
    #  arrowless Bengali-only line — directive-র edge গুলো একসাথে)
    try:
        sample_32 = (
            "\\[01.jpg:1\\] Hello → হ্যালো\n"
            "[01.jpg:2] World → বিশ্ব\n"
            "[01.jpg:3] Text → টেক্সট\\\n"
            "\\[01.jpg:4\\] শুধুই বাংলা"
        )

        parsed32 = parse_ai_text(sample_32)
        _sent32 = parsed32.get(("_unparsed", 0), {})
        _st32 = _sent32.get("stats", {})

        ok32 = (
            len(parsed32) == 5  # 4 entries + report sentinel
            and parsed32[("01.jpg", 1)]["original_text"] == "Hello"
            and parsed32[("01.jpg", 1)]["translated_text"] == "হ্যালো"
            and parsed32[("01.jpg", 2)]["translated_text"] == "বিশ্ব"
            and parsed32[("01.jpg", 3)]["translated_text"] == "টেক্সট"
            and parsed32[("01.jpg", 4)]["translated_text"] == "শুধুই বাংলা"
            and parsed32[("01.jpg", 4)]["original_text"] == ""
            and _st32.get("unescaped") == 2
            and _st32.get("arrowless") == 1
            and _st32.get("trailing_backslash") == 1
            and _st32.get("escape_warn", 0) == 0
            and not _sent32.get("unparsed_lines")
        )

        run_test(
            "mixed-escape fixture 100% parse (S05-2)",
            ok32,
            str(parsed32)[:200],
        )
    except Exception as exc:
        run_test("mixed-escape fixture 100% parse (S05-2)", False, str(exc)[:160])
finally:
    if _saved_df_s05 is _B2_UNSET:
        globals().pop("translation_df", None)
    else:
        translation_df = _saved_df_s05

print()'''
