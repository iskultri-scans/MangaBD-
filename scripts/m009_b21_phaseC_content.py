"""MANGABD-009 B2.1 Phase C — patch content: guard except-WARN
allowlist (RB21-2) + never-save-blank quarantine (RB21-3).

Owner ruling on Phase A 67bc594: RB21-1 REJECT (placement-null;
T5 class unfixable), RB21-2 APPROVE, RB21-3 APPROVE (+ Test 22
fail-on-current-bytes contract), RB21-4 REJECT (rung-1 covers
20/20). Implementation scope: items 2+3 only, cell 10 ONLY,
healthy-path bytes byte-identical.

Three anchored patches, all cell 10:
  P1  `_b2_renderable_rows_present` helper (the RF-14 guard's
      renderable-rows predicate, extracted verbatim so guard +
      quarantine share ONE condition) + `_b2_blank_cache_stale`
      rewritten to call it + except split: FileNotFoundError
      (cold-start, expected) silent / other exceptions WARN
      + return False (fail-open value unchanged)
  P2  render_page quarantine branch: rendered==0 AND renderable
      rows present -> save under quarantine/ (NOT final/), WARN,
      do NOT mark stage done; eyeball renders (no renderable
      rows) keep today's final+done exactly
  P3  battery Test 22 — the fail-on-current-bytes contract:
      (a) quarantine arms, (b) recovery re-render inks, (c)
      eyeball legitimacy preserved, (d) guard allowlist quiet/
      loud; fixture cleaned up (Test 19 discipline)
"""

C10_P1_OLD = r'''
def _b2_blank_cache_stale(page_id):
    """MANGABD-009 B2 RF-14: stale BLANK render cache trap-এর শর্ত।

    B2 live-gate-এর pre-translation eyeball render (Phase D gate:
    diagonal page eyeball / axis-aligned byte-unchanged / kill-switch
    rollback) page-এর render stage "done" mark করে যায় rendered=0
    meta নিয়ে — ফাঁকা final.jpg save হয়। পরে Owner অনুবাদ apply
    করে step_4 (run_render_all, force=False resume-aware) ডাকলে
    cache সেই ফাঁকা final-ই ফিরিয়ে দিত — Owner live 2026-10-27:
    "renders ZERO text"। শর্ত দুটো: cached meta-তে
    rendered_regions == 0, আর এই মুহূর্তে পেজে অন্তত এক row আসলেই
    রেন্ডার-যোগ্য (Bengali + non-marker + w,h >= 5)। healthy page
    (rendered > 0) বা এখনও-খালি পেজ False — আগের exact cache
    আচরণ, byte-identical।
    """
    try:
        page = get_page(page_id, required=True)
        if int((page.get("meta") or {}).get("rendered_regions", -1)) != 0:
            return False

        _rf14_df = globals().get("translation_df")
        if _rf14_df is None or len(_rf14_df) == 0:
            _rf14_df = pd.read_csv(TRANSLATION_CSV)
        if (
            _rf14_df is None
            or len(_rf14_df) == 0
            or "page_id" not in _rf14_df.columns
        ):
            return False

        _rf14_rows = _rf14_df[_rf14_df["page_id"] == page_id]
        if len(_rf14_rows) == 0:
            return False

        for _, _rf14_row in _rf14_rows.iterrows():
            _rf14_text = str(
                _rf14_row.get("translated_text", "") or ""
            ).strip()
            if (
                _rf14_text
                and not render_is_special_marker(_rf14_text)
                and render_validate_bengali(_rf14_text)
                and int(_rf14_row.get("width", 0)) >= 5
                and int(_rf14_row.get("height", 0)) >= 5
            ):
                return True
        return False
    except Exception:
        return False
'''


C10_P1_NEW = r'''
def _b2_renderable_rows_present(page_id):
    """MANGABD-009 B2.1 (RB21-2/RB21-3): এই মুহূর্তে page-টার জন্য
    অন্তত এক row আসলেই render-যোগ্য কি না — RF-14 guard-এর
    renderable-rows predicate হুবহু তোলা; B2.1-এ guard আর
    render_page-এর quarantine দুই জায়গায় একই শর্ত reuse হয়
    (Phase A ruling: শর্ত reuse-ই eyeball render-দের আগের আচরণ
    রাখে)। render-যোগ্য = অনুবাদ আছে (non-empty + non-marker +
    Bengali-valid) আর w,h >= 5।

    Raises: FileNotFoundError — cold-start (TRANSLATION_CSV এখনও
    নেই); caller-এর except-allowlist সেটাকে expected class ধরে।
    """
    _rf14_df = globals().get("translation_df")
    if _rf14_df is None or len(_rf14_df) == 0:
        _rf14_df = pd.read_csv(TRANSLATION_CSV)
    if (
        _rf14_df is None
        or len(_rf14_df) == 0
        or "page_id" not in _rf14_df.columns
    ):
        return False

    _rf14_rows = _rf14_df[_rf14_df["page_id"] == page_id]
    if len(_rf14_rows) == 0:
        return False

    for _, _rf14_row in _rf14_rows.iterrows():
        _rf14_text = str(
            _rf14_row.get("translated_text", "") or ""
        ).strip()
        if (
            _rf14_text
            and not render_is_special_marker(_rf14_text)
            and render_validate_bengali(_rf14_text)
            and int(_rf14_row.get("width", 0)) >= 5
            and int(_rf14_row.get("height", 0)) >= 5
        ):
            return True
    return False


def _b2_blank_cache_stale(page_id):
    """MANGABD-009 B2 RF-14: stale BLANK render cache trap-এর শর্ত।

    B2 live-gate-এর pre-translation eyeball render (Phase D gate:
    diagonal page eyeball / axis-aligned byte-unchanged / kill-switch
    rollback) page-এর render stage "done" mark করে যায় rendered=0
    meta নিয়ে — ফাঁকা final.jpg save হয়। পরে Owner অনুবাদ apply
    করে step_4 (run_render_all, force=False resume-aware) ডাকলে
    cache সেই ফাঁকা final-ই ফিরিয়ে দিত — Owner live 2026-10-27:
    "renders ZERO text"। শর্ত দুটো: cached meta-তে
    rendered_regions == 0, আর এই মুহূর্তে পেজে অন্তত এক row আসলেই
    রেন্ডার-যোগ্য (Bengali + non-marker + w,h >= 5)। healthy page
    (rendered > 0) বা এখনও-খালি পেজ False — আগের exact cache
    আচরণ, byte-identical।

    B2.1 (RB21-2): শরীরের renderable-rows অংশ
    `_b2_renderable_rows_present` helper-এ উঠেছে (render_page-এর
    quarantine-ও সেটা reuse করে); except-এ এখন type-allowlist —
    cold-start FileNotFoundError নীরব, unexpected class WARN।
    """
    try:
        page = get_page(page_id, required=True)
        if int((page.get("meta") or {}).get("rendered_regions", -1)) != 0:
            return False

        return _b2_renderable_rows_present(page_id)
    except FileNotFoundError:
        # B2.1 RB21-2: cold-start allowlist — TRANSLATION_CSV এখনও
        # নেই (fresh page, pre-apply Run All) — expected class,
        # কোনো WARN নয়; return আগের মতোই False।
        return False
    except Exception as exc:
        # B2.1 RB21-2: শেষ silent route বন্ধ — unexpected exception
        # এখন WARN সহ fail-open False (return value আগের মতোই,
        # তাই Test 19 + guard edge matrix অপরিবর্তিত)।
        log_event(
            f"Blank-cache guard raised [{page_id}]: "
            f"{type(exc).__name__}: {str(exc)[:120]}",
            level="WARN",
            page_id=page_id,
        )
        return False

'''


C10_P2_OLD = r'''
    # Save final artifact
    save_image_artifact(page_id, "final", canvas_pil, quality=95)

    # Save translation_df
    if "save_translation_df" in globals():
        save_translation_df()

'''


C10_P2_NEW = r'''
    # MANGABD-009 B2.1 (RB21-3): never-save-blank quarantine।
    # rendered=0 হলেও page-এ এখন আসলেই render-যোগ্য row থাকলে
    # (অনুবাদ apply হয়েছে কিন্তু সব region render-এ fail) ফাঁকা
    # final.jpg poison-cache হতো — RF-14 trap-এর উৎস। তাই এই render
    # quarantine/ dir-এ যায়, WARN হয়, আর render stage "done" mark
    # হয় না। Phase D pre-translation eyeball render (rendered=0 +
    # renderable row নেই) legitimate — আগের মতোই final + done
    # (Phase A ruling: guard-এর predicate reuse-ই শর্ত)।
    _b21_quarantine = False
    if rendered_count == 0:
        try:
            _b21_quarantine = _b2_renderable_rows_present(page_id)
        except FileNotFoundError:
            _b21_quarantine = False
        except Exception as exc:
            log_event(
                f"Quarantine predicate raised [{page_id}]: "
                f"{type(exc).__name__}: {str(exc)[:120]}",
                level="WARN",
                page_id=page_id,
            )
            _b21_quarantine = False

    if _b21_quarantine:
        _b21_qdir = get_page_dir(page_id) / "quarantine"
        _b21_qdir.mkdir(parents=True, exist_ok=True)
        canvas_pil.save(_b21_qdir / "final.jpg", quality=95)

        if "save_translation_df" in globals():
            save_translation_df()

        log_event(
            f"BLANK render quarantined [{page_id}]: rendered=0 with "
            f"renderable rows — NOT saved as final, render stage NOT "
            f"marked done (B2.1 RB21-3)",
            level="WARN",
            page_id=page_id,
        )
        print(
            f"    ⚠️ BLANK render quarantined (quarantine/, stage not "
            f"done): {page_id} (B2.1 RB21-3)"
        )

        final_bgr = cv2.cvtColor(
            np.array(canvas_pil), cv2.COLOR_RGB2BGR
        )
        return final_bgr

    # Save final artifact
    save_image_artifact(page_id, "final", canvas_pil, quality=95)

    # Save translation_df
    if "save_translation_df" in globals():
        save_translation_df()

'''


C10_P3_OLD = r'''
        "B2 RF-18: original-ink orientation parity (mask GT -> render)",
        False, str(exc)[:160],
    )


# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।
'''


C10_P3_NEW = r'''
        "B2 RF-18: original-ink orientation parity (mask GT -> render)",
        False, str(exc)[:160],
    )


# Test 22: B2.1 RB21-2/RB21-3 — never-save-blank quarantine + guard
# except-WARN allowlist। fail-on-current-bytes contract: pre-B2.1
# bytes-এ (blank final + stage-done + silent except) এই test FAIL
# করত। (a) renderable row থাকা অবস্থায় সব region fail → final নয়,
# quarantine/, stage NOT done, WARN; (b) পুনরায় সফল render → healthy
# final + done + visible ink (poison-cache নেই); (c) eyeball render
# (অনুবাদ নেই) → আগের মতোই final + done; (d) guard allowlist:
# cold-start FileNotFoundError নীরব False, unexpected exception WARN
# + False।
try:
    _t22_pid = "__b21_t22__"
    _t22_canvas = np.full((400, 600, 3), 255, np.uint8)
    init_page(_t22_pid, width=600, height=400,
              image_np=_t22_canvas, overwrite=True)
    save_image_artifact(_t22_pid, "inpainted", _t22_canvas, quality=95)
    save_json_artifact(_t22_pid, "detections", [
        {"id": 1, "page_id": _t22_pid, "x": 60, "y": 80,
         "width": 200, "height": 90,
         "quad": [[60, 80], [260, 80], [260, 170], [60, 170]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
    ])
    mark_stage_done(_t22_pid, "detect", meta={"region_count": 1})

    _t22_row = {c: "" for c in TRANSLATION_DF_COLUMNS}
    _t22_row.update({
        "page_id": _t22_pid, "page": _t22_pid, "id": 1,
        "region_type": "bubble",
        "detector_class": "text_bubble",
        "detector_score": 0.9, "parent_bubble_id": "",
        "x": 60, "y": 80, "width": 200, "height": 90,
        "angle": 0.0, "original_text": "テスト",
        "translated_text": "এই কী হয়েছে বলো তো?!", "confidence": 0.9,
        "ocr_engine": "t22", "is_english": True,
        "bengali_valid": True, "status": "ok",
        "reading_order": -1,
    })
    upsert_translation_rows(_t22_pid, [_t22_row])

    # (a) QUARANTINE: render engine-কে fail করালাম — rendered=0
    # কিন্তু renderable row আছে
    _t22_real_rbt = render_bengali_text

    def _t22_boom(*_a, **_k):
        raise RuntimeError("t22 forced render failure")

    render_bengali_text = _t22_boom
    _t22_ev0 = len(MANGABD_EVENTS)
    try:
        render_page(_t22_pid, force=True)
    finally:
        render_bengali_text = _t22_real_rbt

    _t22_final_a = load_image_artifact(_t22_pid, "final")
    _t22_qdir = get_page_dir(_t22_pid) / "quarantine"
    _t22_done_a = is_stage_done(_t22_pid, "render")
    _t22_warn_a = [
        e for e in MANGABD_EVENTS[_t22_ev0:]
        if e.get("level") == "WARN"
        and "quarantined" in str(e.get("message", ""))
    ]
    _t22_ok_a = (
        _t22_final_a is None
        and (_t22_qdir / "final.jpg").exists()
        and not _t22_done_a
        and len(_t22_warn_a) >= 1
    )

    # (b) recovery: stage done না থাকায় force=False-ই নতুন render —
    # healthy final + done + visible ink (poison-cache নেই)
    _t22_out = render_page(_t22_pid, force=False)
    _t22_roi = np.abs(
        _t22_out[80:170, 60:260].astype(int)
        - _t22_canvas[80:170, 60:260].astype(int)
    ).sum(axis=2)
    _t22_ink = int((_t22_roi > 30).sum())
    _t22_ok_b = (
        load_image_artifact(_t22_pid, "final") is not None
        and is_stage_done(_t22_pid, "render")
        and _t22_ink >= 50
    )

    # (c) EYEBALL: rows আছে কিন্তু অনুবাদ খালি → legitimate final +
    # done (Phase D pre-translation eyeball contract অপরিবর্তিত)
    _t22_pid2 = "__b21_t22_eye__"
    init_page(_t22_pid2, width=600, height=400,
              image_np=_t22_canvas, overwrite=True)
    save_image_artifact(_t22_pid2, "inpainted", _t22_canvas, quality=95)
    save_json_artifact(_t22_pid2, "detections", [
        {"id": 1, "page_id": _t22_pid2, "x": 60, "y": 80,
         "width": 200, "height": 90,
         "quad": [[60, 80], [260, 80], [260, 170], [60, 170]],
         "angle": 0.0, "region_type": "bubble",
         "detector_class": "text_bubble", "detector_score": 0.9,
         "parent_bubble_id": None},
    ])
    mark_stage_done(_t22_pid2, "detect", meta={"region_count": 1})
    _t22_row2 = dict(_t22_row)
    _t22_row2.update({
        "page_id": _t22_pid2, "page": _t22_pid2,
        "translated_text": "", "bengali_valid": False,
    })
    upsert_translation_rows(_t22_pid2, [_t22_row2])

    render_page(_t22_pid2, force=False)
    _t22_ok_c = (
        load_image_artifact(_t22_pid2, "final") is not None
        and is_stage_done(_t22_pid2, "render")
        and not (get_page_dir(_t22_pid2) / "quarantine").exists()
    )

    # (d) GUARD ALLOWLIST (RB21-2): cold-start FileNotFoundError
    # নীরব False; unexpected exception WARN + False
    _t22_pid3 = "__b21_t22_guard__"
    init_page(_t22_pid3, width=600, height=400,
              image_np=_t22_canvas, overwrite=True)
    mark_stage_done(_t22_pid3, "render",
                    meta={"rendered_regions": 0})

    _t22_no_csv = Path("/tmp/__b21_t22_no_such_csv__.csv")
    assert not _t22_no_csv.exists()  # intentional cold-start path
    _t22_saved_csv = TRANSLATION_CSV
    _t22_saved_df = globals().get("translation_df")
    try:
        translation_df = pd.DataFrame()
        globals()["TRANSLATION_CSV"] = _t22_no_csv
        _t22_ev1 = len(MANGABD_EVENTS)
        _t22_g1 = _b2_blank_cache_stale(_t22_pid3)
        _t22_quiet = not [
            e for e in MANGABD_EVENTS[_t22_ev1:]
            if e.get("level") == "WARN"
        ]

        mark_stage_done(_t22_pid3, "render",
                        meta={"rendered_regions": "t22-not-a-number"})
        _t22_ev2 = len(MANGABD_EVENTS)
        _t22_g2 = _b2_blank_cache_stale(_t22_pid3)
        _t22_loud = [
            e for e in MANGABD_EVENTS[_t22_ev2:]
            if e.get("level") == "WARN"
            and "guard raised" in str(e.get("message", ""))
        ]
    finally:
        globals()["TRANSLATION_CSV"] = _t22_saved_csv
        translation_df = _t22_saved_df
    _t22_ok_d = (
        _t22_g1 is False and _t22_quiet
        and _t22_g2 is False and len(_t22_loud) >= 1
    )

    run_test(
        "B2.1 RB21-2/RB21-3: blank-render quarantine + guard "
        "except-WARN allowlist",
        _t22_ok_a and _t22_ok_b and _t22_ok_c and _t22_ok_d,
        f"final_a={'saved' if _t22_final_a is not None else 'none'} "
        f"q={'Y' if (_t22_qdir / 'final.jpg').exists() else 'N'} "
        f"done_a={'Y' if _t22_done_a else 'N'} "
        f"warn_a={len(_t22_warn_a)} ink_b={_t22_ink} "
        f"eyeball={'Y' if _t22_ok_c else 'N'} "
        f"guard={_t22_g1}/{_t22_g2} quiet={_t22_quiet} "
        f"loud={len(_t22_loud)}",
    )
except Exception as exc:
    run_test(
        "B2.1 RB21-2/RB21-3: blank-render quarantine + guard "
        "except-WARN allowlist",
        False, str(exc)[:160],
    )
finally:
    try:
        _t22_df2 = globals().get("translation_df")
        if _t22_df2 is not None and len(_t22_df2):
            _t22_keep = _t22_df2[
                ~_t22_df2["page_id"].isin(
                    ["__b21_t22__", "__b21_t22_eye__"]
                )
            ]
            globals()["translation_df"] = _t22_keep
            save_translation_df(_t22_keep)
        reset_page("__b21_t22__", delete_artifacts=True)
        reset_page("__b21_t22_eye__", delete_artifacts=True)
        reset_page("__b21_t22_guard__", delete_artifacts=True)
    except Exception:
        pass


# RF-13 fixture hygiene: D-4/D-3 fixture residue battery-র শেষে পরিষ্কার।
'''
