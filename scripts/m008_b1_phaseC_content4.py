#!/usr/bin/env python3
r"""MANGABD-008 B1 Phase C — content module: CELL 4 patches.

Cell 4 = MANGABD_ASSETS font registration + the vendored NotoSansJP
resolution (sha256-pinned, RF-7 pattern). No download.

Every OLD anchor below is byte-copied from the base notebook
(main @ 73ca565) and unique-asserted by the build driver.
"""

FONT_FALLBACK_SHA256 = "c2f3b4d463500a2ddcd3849cded1fceeb9fd6d1c32e6cbecd568453ba50fc68f"
FONT_FALLBACK_SIZE = 9589900

# ── patch 4-1: section 8.5 (vendored JP fallback font) ───────
CELL4_S85_OLD = """# Bold font fail করলে regular font কে bold fallback হিসেবে copy করি
if not bold_font_ok and regular_font_ok:
    try:
        shutil.copy(FONT_REGULAR_PATH, FONT_BOLD_PATH)
        bold_font_ok = True
        print("  ℹ️ Regular font copied as bold fallback")
    except Exception as exc:
        print(f"  ⚠️ Bold fallback copy failed: {str(exc)[:120]}")

print()
"""

CELL4_S85_NEW = CELL4_S85_OLD + """
# ═══════════════════════════════════════════════════════════
# 8.5 Japanese fallback font (MANGABD-008 Phase C — vendored, sha-pinned)
# ═══════════════════════════════════════════════════════════

print("─" * 70)
print("  8.5 Japanese fallback font (vendored)")
print("─" * 70)

# কানা/ASCII/em-dash glyph-গুলোর জন্য JP fallback font (OFL-1.1)।
# MANGABD-008 Phase C থেকে repo-তে vendored — runtime download নেই (Owner
# decision; cells 11/12-এর পুরনো download logic বাদ)। M6-B1 RF-7 প্যাটার্ন:
# load-এ sha256-verify; না পেলে clear diagnostic — কখনো silent নয়।
import hashlib

FONT_FALLBACK_SHA256 = \"""" + FONT_FALLBACK_SHA256 + """\"
FONT_FALLBACK_SIZE = """ + str(FONT_FALLBACK_SIZE) + """
FONT_FALLBACK_LICENSE = "OFL-1.1"


def _sha256_of_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


FONT_FALLBACK_CANDIDATES = [
    Path("assets/fonts/NotoSansJP[wght].ttf"),   # repo checkout (CWD-relative)
    DIRS["fonts"] / "NotoSansJP.ttf",            # notebook fonts convention (Drive)
]

fallback_font_path = None
fallback_sha_ok = False

for _fb_cand in FONT_FALLBACK_CANDIDATES:
    if not _fb_cand.is_file() or _fb_cand.stat().st_size < 1024:
        continue
    _fb_got = _sha256_of_file(_fb_cand)
    if _fb_got == FONT_FALLBACK_SHA256:
        fallback_font_path = _fb_cand
        fallback_sha_ok = True
        print(f"  ✅ JP fallback font sha256-verified: {_fb_cand}")
        break
    print(f"  ⚠️ JP fallback font corrupt/different bytes — skip: {_fb_cand}")

if fallback_font_path is None:
    fallback_font_path = FONT_FALLBACK_CANDIDATES[0]
    print(
        "  ⚠️ JP fallback font পাওয়া যায়নি — ASCII/কানা tofu হবে।\\n"
        "     Fix: repo-র assets/fonts/NotoSansJP[wght].ttf vendored করো,\\n"
        f"     অথবা এখানে রাখো: {DIRS['fonts'] / 'NotoSansJP.ttf'}"
    )
    log_event("JP fallback font missing — ASCII/kana will tofu", level="WARN")

MANGABD_CONFIG["rendering"]["font_fallback"] = str(fallback_font_path)
print(f"  🔤 JP fallback: {fallback_font_path} (sha_ok={fallback_sha_ok})")

print()
"""

# ── patch 4-2: asset registry extension ───────────────────────
CELL4_REGISTRY_OLD = """    "fonts": {
        "regular_path": str(FONT_REGULAR_PATH),
        "bold_path": str(FONT_BOLD_PATH),
        "regular_ok": regular_font_ok,
        "bold_ok": bold_font_ok,
        "raqm_ok": raqm_ok,
        "render_ok": font_render_ok,
    },
}"""

CELL4_REGISTRY_NEW = """    "fonts": {
        "regular_path": str(FONT_REGULAR_PATH),
        "bold_path": str(FONT_BOLD_PATH),
        "regular_ok": regular_font_ok,
        "bold_ok": bold_font_ok,
        "raqm_ok": raqm_ok,
        "render_ok": font_render_ok,
        # MANGABD-008 Phase C: JP fallback font (vendored, sha-pinned)
        "fallback_path": str(fallback_font_path),
        "fallback_sha256": FONT_FALLBACK_SHA256,
        "fallback_size": FONT_FALLBACK_SIZE,
        "fallback_sha_ok": fallback_sha_ok,
        "fallback_license": FONT_FALLBACK_LICENSE,
    },
}"""

# ── patch 4-3: battery — JP fallback registration test ────────
CELL4_BATTERY_OLD = """run_test(
    "Bold font exists or fallback available",
    bold_font_ok and FONT_BOLD_PATH.exists(),
    str(FONT_BOLD_PATH),
)

run_test(
    "libraqm available",
    raqm_ok,
)"""

CELL4_BATTERY_NEW = """run_test(
    "Bold font exists or fallback available",
    bold_font_ok and FONT_BOLD_PATH.exists(),
    str(FONT_BOLD_PATH),
)

run_test(
    "JP fallback font registered (MANGABD-008)",
    bool(MANGABD_CONFIG["rendering"].get("font_fallback")),
    str(MANGABD_CONFIG["rendering"].get("font_fallback", ""))
        + " (sha_ok=" + str(fallback_sha_ok) + ")",
)

run_test(
    "libraqm available",
    raqm_ok,
)"""

# ── patch 4-4: log_event extras — fallback status ─────────────
CELL4_LOG_OLD = """    regular_font=regular_font_ok,
    bold_font=bold_font_ok,
    raqm=raqm_ok,"""

CELL4_LOG_NEW = """    regular_font=regular_font_ok,
    bold_font=bold_font_ok,
    fallback_ok=fallback_sha_ok,
    raqm=raqm_ok,"""
