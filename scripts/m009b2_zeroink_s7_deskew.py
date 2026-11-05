#!/usr/bin/env python3
"""S7: OCR deskew-crop sanity through the verbatim cell-6 crop path.

crop_region_rotated(image, region) consumes region["quad"] — dormant in base
(base never stores angle != 0), ACTIVATED by B2 on live for |angle| > 5.
If the perspective warp mirrors/flips the strip, live OCR fails or empties
-> translation rows become markers/empty -> render SKIPS those regions.
"""
import json
import sys
import pathlib
import numpy as np
import cv2
from PIL import Image as PILImage, ImageDraw, ImageFont

HERE = pathlib.Path("/home/z/my-project/m009b2_repro")
sys.path.insert(0, str(HERE / "scripts"))
from b2_env import build_env, _slice_fn, CELLS  # noqa: E402
from repro_run import JP_FONT  # noqa: E402

ns = build_env("tip", HERE / "s7_env.log")
est = ns["_estimate_region_angle"]

# verbatim cell-6 crop helpers (crop_region + crop_region_rotated)
crop_slice = _slice_fn(
    CELLS[6], "def crop_region(", 'print("  ✅ Crop helpers ready')
exec(compile(crop_slice, "<cell6_crop_slice>", "exec"), ns)
crr = ns["crop_region_rotated"]
print("crop_region_rotated loaded:", crr is not None)

JP = JP_FONT
results = {}

# ---- case A: true diagonal strip (-25deg) ----
page = np.full((900, 1200, 3), 255, np.uint8)
strip = PILImage.new("L", (760, 60), 255)
ImageDraw.Draw(strip).text((10, 8), "বিস্ফোরণ ডাইনামাইট টেস্ট লাইন বাংলা",
                           font=ImageFont.truetype(JP, 34), fill=0)
rot = strip.rotate(-25, expand=True, resample=PILImage.BICUBIC, fillcolor=255)
page[150:150 + rot.size[1], 120:120 + rot.size[0]] = cv2.cvtColor(
    np.asarray(rot.convert("RGB")), cv2.COLOR_RGB2BGR)
g = cv2.cvtColor(page, cv2.COLOR_BGR2GRAY)
ys, xs = np.nonzero(g < 128)
bx = (int(xs.min()) - 2, int(ys.min()) - 2,
      int(xs.max() - xs.min()) + 5, int(ys.max() - ys.min()) + 5)
ang, quad = est(page, *bx)
print(f"A: estimator angle={ang} quad={'Y' if quad else 'N'} bbox={bx}")
region = {"id": 1, "x": bx[0], "y": bx[1], "width": bx[2], "height": bx[3],
          "quad": (quad if quad is not None else
                   [[bx[0], bx[1]], [bx[0] + bx[2], bx[1]],
                    [bx[0] + bx[2], bx[1] + bx[3]], [bx[0], bx[1] + bx[3]]]),
          "angle": float(ang), "region_type": "sfx"}
crop = crr(page, region)
ga = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
results["A_true_-25"] = {
    "est_angle": ang, "crop_shape": list(crop.shape[:2]),
    "ink_px": int((ga < 128).sum()),
    "strip_aspect_ref": round(760 / 60, 2),
    "crop_aspect": round(crop.shape[1] / crop.shape[0], 2),
}
cv2.imwrite(str(HERE / "render_eyeball" / "s7A_deskew_-25.png"), crop)

# readability proxy: re-estimate the angle of the DESKEWED crop —
# a correct deskew yields ~0 lean; mirrored keeps |lean|; 180-flip keeps |lean|
a2, _ = est(crop, 0, 0, crop.shape[1], crop.shape[0])
results["A_true_-25"]["deskewed_relean"] = a2

# ---- case B: horizontal 2-line block (estimator false-fire class) ----
pageB_pil = PILImage.new("RGB", (800, 400), (255, 255, 255))
fB = ImageFont.truetype(JP, 30)
d = ImageDraw.Draw(pageB_pil)
d.text((60, 120), "今日の試合、最後の", font=fB, fill=(15, 15, 15))
d.text((60, 165), "ホームラン。", font=fB, fill=(15, 15, 15))
pageB = cv2.cvtColor(np.asarray(pageB_pil), cv2.COLOR_RGB2BGR)
gB = cv2.cvtColor(pageB, cv2.COLOR_BGR2GRAY)
ys, xs = np.nonzero(gB < 128)
bxB = (int(xs.min()) - 2, int(ys.min()) - 2,
       int(xs.max() - xs.min()) + 5, int(ys.max() - ys.min()) + 5)
angB, quadB = est(pageB, *bxB)
print(f"B: estimator angle={angB} quad={'Y' if quadB else 'N'} bbox={bxB}")
regionB = {"id": 1, "x": bxB[0], "y": bxB[1], "width": bxB[2],
           "height": bxB[3],
           "quad": (quadB if quadB is not None else
                    [[bxB[0], bxB[1]], [bxB[0] + bxB[2], bxB[1]],
                     [bxB[0] + bxB[2], bxB[1] + bxB[3]],
                     [bxB[0], bxB[1] + bxB[3]]]),
           "angle": float(angB), "region_type": "bubble"}
cropB = crr(pageB, regionB)
gab = cv2.cvtColor(cropB, cv2.COLOR_BGR2GRAY)
aB2, _ = est(cropB, 0, 0, cropB.shape[1], cropB.shape[0])
results["B_falsefire_2line"] = {
    "est_angle": angB, "crop_shape": list(cropB.shape[:2]),
    "ink_px": int((gab < 128).sum()), "deskewed_relean": aB2,
}
cv2.imwrite(str(HERE / "render_eyeball" / "s7B_deskew_falsefire.png"), cropB)

# ---- case C: what the OCR precheck guard sees for a big-tilt region ----
# |angle|>5 sends crop_region_rotated; make sure warp never returns <5px dims
for beta in (-40, -60, -80):
    stripC = PILImage.new("L", (600, 50), 255)
    ImageDraw.Draw(stripC).text(
        (8, 5), "ডায়াগোনাল টেস্ট লাইন", font=ImageFont.truetype(JP, 28),
        fill=0)
    rotC = stripC.rotate(beta, expand=True, resample=PILImage.BICUBIC,
                         fillcolor=255)
    pageC = np.full((700, 900, 3), 255, np.uint8)
    pageC[100:100 + rotC.size[1], 80:80 + rotC.size[0]] = cv2.cvtColor(
        np.asarray(rotC.convert("RGB")), cv2.COLOR_RGB2BGR)
    gC = cv2.cvtColor(pageC, cv2.COLOR_BGR2GRAY)
    ys, xs = np.nonzero(gC < 128)
    bxC = (int(xs.min()) - 2, int(ys.min()) - 2,
           int(xs.max() - xs.min()) + 5, int(ys.max() - ys.min()) + 5)
    angC, quadC = est(pageC, *bxC)
    regC = {"id": 1, "x": bxC[0], "y": bxC[1], "width": bxC[2],
            "height": bxC[3],
            "quad": (quadC if quadC is not None else
                     [[bxC[0], bxC[1]], [bxC[0] + bxC[2], bxC[1]],
                      [bxC[0] + bxC[2], bxC[1] + bxC[3]],
                      [bxC[0], bxC[1] + bxC[3]]]),
            "angle": float(angC), "region_type": "sfx"}
    cropC = crr(pageC, regC)
    gc = cv2.cvtColor(cropC, cv2.COLOR_BGR2GRAY)
    ar, _ = est(cropC, 0, 0, cropC.shape[1], cropC.shape[0])
    results[f"C_tilt{beta}"] = {
        "est_angle": angC, "crop_shape": list(cropC.shape[:2]),
        "ink_px": int((gc < 128).sum()), "deskewed_relean": ar,
    }
    cv2.imwrite(str(HERE / "render_eyeball" / f"s7C_deskew_{beta}.png"),
                cropC)

print(json.dumps(results, indent=2, ensure_ascii=False))
(HERE / "s7_result.json").write_text(json.dumps(results, indent=2))
