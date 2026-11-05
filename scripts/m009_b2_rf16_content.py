#!/usr/bin/env python3
"""MANGABD-009 B2 RF-16 — patch content: text-ink-only PCA (cell 6).

Three anchored patches, scope {6} ONLY (cells 10/11/12 and every other
cell byte-untouched — RF-14 fix, RF-15 fix, B2 render engine, wrappers
all ride unchanged):

  P1  section constant: _B2_RING_MARGIN = 6 (ring-stroke exclusion
      margin for the outside-dilation)
  P2  estimator docstring: documents the RF-16 law (text-ink-only PCA,
      fallback = previous full-ink behavior)
  P3  the isolation block itself, inserted between the despeckle step
      and the pixel harvest:
        - light flood-fill from the crop border (padded trick) -> the
          border-reachable "outside" light region
        - dilate(outside, _B2_RING_MARGIN) -> covers the bubble ring
          stroke + its AA fringe + background/art ink near the box edge
        - enclosed ink = ink AND NOT dilated-outside  -> the text ink
          inside the bubble (ring-aware mask erosion, RF-16 directive)
        - fallback: if the enclosed ink is < 100 px (no ring, SFX,
          broken ring, plain text strip) keep the previous full-ink
          mask -> downstream PCA/gates/quad run on EXACTLY the old
          pixel set (corpus byte-identity + cell-10 battery fixtures
          unchanged)
"""
C6_P1_OLD = """MANGABD_CONFIG["detection"].setdefault("b2_orientation_enable", True)


def _estimate_region_angle(image_bgr, x, y, w, h):
"""

C6_P1_NEW = """MANGABD_CONFIG["detection"].setdefault("b2_orientation_enable", True)

# RF-16: ring-margin (px) — bubble-এর ring-stroke + তার AA fringe বাদ
# দিতে border-reachable "outside" light-mask এত px dilate করা হয়
# (আসল manga ring stroke ~3-8px, S009-class fixture 4px)।
_B2_RING_MARGIN = 6


def _estimate_region_angle(image_bgr, x, y, w, h):
"""

C6_P2_OLD = '''    """MANGABD-009 B2 (RB2-1..RB2-4): pixel-PCA orientation inheritance।

    Region crop-এর dark-ink pixel-গুলোর PCA principal axis থেকে θcw
'''

C6_P2_NEW = '''    """MANGABD-009 B2 (RB2-1..RB2-4): pixel-PCA orientation inheritance।

    RF-16: PCA এখন TEXT INK-এর উপরেই চলে — আগে পুরো dark-ink cloud
    (near-upright bubble ring + background art) ঢুকে যেত, তাই সত্যি
    tilted text-ও মাপা পড়ত ±2-6° (ring-এর দিকে টেনে) → 5° snap →
    0.00 (dc612d5 LIVE REJECT: 7 tilted-এর 6টাই সরল রেন্ডার)। এখন
    border-reachable light flood + ring-margin dilate করে শুধু
    bubble-এর ভেতরের enclosed text-ink-ই PCA দেখে; ring না পেলে
    fallback = আগের full-ink mask (হুবহু পুরনো আচরণ)।

    Region crop-এর dark-ink pixel-গুলোর PCA principal axis থেকে θcw
'''

C6_P3_OLD = """        if int(_keep.sum() // 255) >= 30:
            ink = _keep

    ys, xs = np.nonzero(ink)
"""

C6_P3_NEW = """        if int(_keep.sum() // 255) >= 30:
            ink = _keep

    # RF-16: TEXT-INK-ONLY PCA — মাপার আগেই enclosed ink আলাদা করা।
    # crop-এর border থেকে light-pixel flood-fill (_outside) বাইরের
    # সব light-এ ছড়ায়; bubble ring-stroke + background art-এর কালি
    # সব _outside-এর ঠিক পাশে-পাশে। _outside-কে _B2_RING_MARGIN px
    # dilate করে বাদ দিলে থাকে শুধু bubble-এর ভেতরের text ink
    # (ring-aware mask erosion — RF-16 directive #1)। Enclosed ink
    # 100px-এর কম উঠলে (ring নেই / SFX / ভাঙা ring / plain text
    # strip) আগের full-ink mask-ই থাকে — সেই ক্ষেত্রে নিচের সব
    # PCA/gate/quad ঠিক আগের bytes-এর মতোই চলে (corpus 0/36 +
    # cell-10 battery fixture-গুলো অটুট)।
    _light = (ink == 0)
    _ff = np.pad(_light, 1, constant_values=True).astype(np.uint8)
    _ffmask = np.zeros((_ff.shape[0] + 2, _ff.shape[1] + 2), np.uint8)
    cv2.floodFill(_ff, _ffmask, (0, 0), 2)
    _outside = (_ff == 2)[1:-1, 1:-1]
    _kern = cv2.getStructuringElement(
        cv2.MORPH_ELLIPSE,
        (2 * _B2_RING_MARGIN + 1, 2 * _B2_RING_MARGIN + 1))
    _enclosed = (ink > 0) & (cv2.dilate(
        _outside.astype(np.uint8), _kern) == 0)
    if int(_enclosed.sum()) >= 100:
        ink = _enclosed.astype(np.uint8) * 255

    ys, xs = np.nonzero(ink)
"""
