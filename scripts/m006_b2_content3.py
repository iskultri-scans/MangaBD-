"""MANGABD-006 B2 content — cell 3 new section (reading order).

The algorithm is the Phase A §M4.1 validated form (x-interval
connected-components bands) — NOT the directive's literal center-gap
paraphrase: the center-gap form was measured FIRST and FAILS the
directive's own S003 verification gate (tau +0.467 vs the required
+1.000; instrument scripts/m006_b2_algo_check.py). The validated form
reproduces the VLM-confirmed order EXACTLY. Deviation disclosed in the
Phase C record.
"""

CELL3_SECTION_NEW = '''# ═════════════════════════════════════════════════════════════
# 9b. Reading order (MANGABD-006 B2) — compute + payload order
# ═════════════════════════════════════════════════════════════
# Phase A §M4.1 validated algorithm (EXACT match, Kendall tau +1.000
# vs the VLM-confirmed S003 order): column bands = connected components
# of x-interval overlap; bands right-to-left (max right edge DESC);
# within a band top-to-bottom (y ASC, x DESC tie-break); overlay margin
# notes configurable via CONFIG["reading_order"]["overlay_note_position"]
# (D2 default = geometric). Vertical (V-3) regions keep their
# in-region VLM-decoded line order — this is region-level placement only.


def compute_reading_order(regions, overlay_note_position=None):
    """
    MANGABD-006 B2: region-level manga reading order (Phase A §M4.1).

    Args:
        regions: list of dicts with x, y, width, height
                 (+ id, region_type)
        overlay_note_position: None = CONFIG default;
                 "geometric" | "first" | "last"

    Returns:
        list of region ids in reading order (RTL bands, T2B within)
    """
    if not regions:
        return []

    if overlay_note_position is None:
        overlay_note_position = str(
            MANGABD_CONFIG.get("reading_order", {}).get(
                "overlay_note_position", "geometric"
            )
        )

    boxes = []

    for r in regions:
        x = int(float(r.get("x", 0) or 0))
        y = int(float(r.get("y", 0) or 0))
        w = int(float(r.get("width", 0) or 0))

        boxes.append({
            "id": int(float(r.get("id", 0) or 0)),
            "x0": x,
            "x1": x + w,
            "y0": y,
            "region_type": str(r.get("region_type", "bubble")),
        })

    # 1. column bands = connected components of x-interval overlap
    n = len(boxes)
    parent = list(range(n))

    def _find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for i in range(n):
        for j in range(i + 1, n):
            if (
                boxes[i]["x0"] < boxes[j]["x1"]
                and boxes[j]["x0"] < boxes[i]["x1"]
            ):
                parent[_find(i)] = _find(j)

    bands = {}

    for i in range(n):
        bands.setdefault(_find(i), []).append(boxes[i])

    # 2. bands right-to-left (max right edge DESC)
    ordered_bands = sorted(
        bands.values(),
        key=lambda b: max(r["x1"] for r in b),
        reverse=True,
    )

    # 3. within band: top-to-bottom (y ASC, right-first tie)
    result = []

    for band in ordered_bands:
        for r in sorted(band, key=lambda r: (r["y0"], -r["x0"])):
            result.append(r)

    # 4. overlay margin-note placement (D2 default: geometric)
    if overlay_note_position != "geometric":
        overlays = [r for r in result if r["region_type"] == "overlay"]
        rest = [r for r in result if r["region_type"] != "overlay"]

        if overlay_note_position == "first":
            result = overlays + rest
        else:
            result = rest + overlays

    return [r["id"] for r in result]


def _reading_order_series(page_rows):
    """
    M6-B2 internal: lazily compute reading_order for one page's rows.

    Existing valid values (>= 0) pass through; -1 / missing / legacy
    "" values trigger a recompute from the rows' own geometry.
    Never mutates the input. Returns None when geometry is unusable.
    """
    existing = None

    if "reading_order" in page_rows.columns:
        existing = pd.to_numeric(
            page_rows["reading_order"], errors="coerce"
        )

    if (
        existing is not None
        and len(existing) == len(page_rows)
        and existing.notna().all()
        and bool((existing >= 0).all())
    ):
        return existing.astype(int)

    regions = []

    for _, row in page_rows.iterrows():
        try:
            regions.append({
                "id": int(float(row.get("id", 0) or 0)),
                "x": int(float(row.get("x", 0) or 0)),
                "y": int(float(row.get("y", 0) or 0)),
                "width": int(float(row.get("width", 0) or 0)),
                "height": int(float(row.get("height", 0) or 0)),
                "region_type": str(row.get("region_type", "bubble")),
            })
        except Exception:
            return None

    order_ids = compute_reading_order(regions)
    ro_map = {rid: i for i, rid in enumerate(order_ids)}

    return pd.Series(
        [ro_map.get(r["id"], 0) for r in regions],
        index=page_rows.index,
        dtype=int,
    )


def ensure_reading_order_column(df):
    """
    M6-B2: normalize + lazily fill the reading_order column per page.

    Legacy rows (missing / "" / -1) are computed from their own
    geometry — the backward-compat requirement for archived CSVs.
    Safe no-op on any failure (returns df unchanged).
    """
    try:
        if df is None or len(df) == 0 or "page_id" not in df.columns:
            return df

        if "reading_order" not in df.columns:
            df["reading_order"] = -1
        else:
            df["reading_order"] = (
                pd.to_numeric(df["reading_order"], errors="coerce")
                .fillna(-1)
                .astype(int)
            )

        if not MANGABD_CONFIG.get("reading_order", {}).get(
            "enabled", True
        ):
            return df

        for pid in df["page_id"].unique():
            mask = df["page_id"] == pid

            if bool((df.loc[mask, "reading_order"] < 0).any()):
                ro = _reading_order_series(df[mask])

                if ro is not None:
                    df.loc[ro.index, "reading_order"] = ro

        return df
    except Exception:
        return df


def payload_sort_page_rows(page_rows):
    """
    M6-B2: one page's rows in payload order (ai.Text / copy payload /
    translation records / LLM feed). Default = manga reading order;
    CONFIG["reading_order"]["payload_sort"] == "id" or enabled=False
    falls back to detection order. Legacy rows without the column are
    computed lazily from geometry.
    """
    try:
        ro_cfg = MANGABD_CONFIG.get("reading_order", {})

        if not ro_cfg.get("enabled", True):
            return page_rows.sort_values("id")

        if str(ro_cfg.get("payload_sort", "reading_order")) == "id":
            return page_rows.sort_values("id")

        if len(page_rows) == 0:
            return page_rows

        ro = _reading_order_series(page_rows)

        if ro is None:
            return page_rows.sort_values("id")

        out = page_rows.copy()
        out["reading_order"] = ro

        return out.sort_values(["reading_order", "id"])
    except Exception:
        try:
            return page_rows.sort_values("id")
        except Exception:
            return page_rows


def payload_sort_all_rows(df):
    """
    M6-B2: full-df display order — page, then reading order within
    page (apply-flow coverage reports). enabled=False -> df unchanged
    (legacy iteration order); never raises.
    """
    try:
        ro_cfg = MANGABD_CONFIG.get("reading_order", {})

        if not ro_cfg.get("enabled", True):
            return df

        if str(ro_cfg.get("payload_sort", "reading_order")) == "id":
            return df.sort_values(["page", "id"])

        if df is None or len(df) == 0 or "page" not in df.columns:
            return df

        parts = [
            payload_sort_page_rows(df[df["page"] == pg])
            for pg in df["page"].unique()
        ]

        return pd.concat(parts) if parts else df
    except Exception:
        return df


print("  ✅ Reading order (M6-B2) ready")
print()
'''
