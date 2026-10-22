#!/usr/bin/env python3
"""MANGABD-006 B1 (Phase C) — vendor OCR engine weights into the repo.

Downloads the sha-pinned engine weights from HuggingFace into the repository
tree (models/kellenok/, models/baberu/) and verifies sha256 against the
committed RF-5 provenance pins where they exist.

Vendored set (M6-B1 decision record, see agents/GLM_5_3.md Phase C):
  - kellenok  = Kellenok/PP-OCRv6_manga v0.2 FP32 det+rec + dict (~23 MB)
                -> EXACTLY the RF-5 sha-pinned, A.1.2-measured build.
  - baberu    = genshiai-daichi/baberu-ocr v1.1 int4 bundle
                (vision_int4.onnx 52.3MB + decoder_prefill_int8 35.1MB +
                 decoder_step_int8 33.9MB + tokenizer files; ~121.3 MB total)
                -> the author-swept smallest build (nCER 0.0901 vs fp16
                   bundle 0.0897 on Manga109 v1.1, +0.0004); chosen because
                   vision_fp16.onnx (172.9 MB) exceeds GitHub's 100 MB hard
                   push limit and git-lfs is not part of the Owner's
                   workflow. Decoder int8 files are the SAME sha-pinned
                   files from the RF-5 run; vision_int4 is a new pin.
Both hub revisions are api-verified pins from the committed runners
(kellenok b3b65cbd..., baberu fdf292a1...).
"""
import hashlib
import json
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO = Path("/home/z/my-project/MangaBD")
OUT_MANIFEST = Path("/home/z/my-project/scripts/m006_b1_weights_manifest.json")

KELLENOK = {
    "repo": "Kellenok/PP-OCRv6_manga",
    "rev": "b3b65cbd29cd0240a6b471e49373eb5a80abac",
    "subdir": "kellenok",
    "files": {
        # sha256 pins from m006_bench/results/kellenok_results.json (RF-5 A8)
        "det/manga_det_v0.2.onnx": "d132078c46e292b226fb5a2ca52a7612ad319262dfdf493e7d8e3be435295978",
        "rec/manga_rec_v0.2.onnx": "de12c84c63e62c80339e882e675983d886670dcb6f0147e1ed041afd6fa81888",
        "ppocrv6_dict.txt": "b5f2bfe2bdd9448429e3e82b51c789775d9b42f2403d082b00662eb77e401c5d",
    },
}

Baberu = {
    "repo": "genshiai-daichi/baberu-ocr",
    "rev": "fdf292a15dae9f5af37dd76bb408679dc4bcdfe4",
    "subdir": "baberu",
    "files": {
        # decoder int8 + tokenizer: sha256 pins from baberu_results.json (RF-5 A8)
        "onnx/decoder_prefill_int8.onnx": "91de16d4e70adaadc0c76ea536f0195b79f54b52e3279aeaac8fc06b46824c60",
        "onnx/decoder_step_int8.onnx": "f6164e9daee6622891d2a52394f143faa7f0ccfdfb90e8d6443193aff36d4c2d",
        "onnx/vision_int4.onnx": None,  # NEW pin (int4 bundle decision) - recorded below
        "tokenizer/vocab.json": "681de4eb83154a397af49e2ddae4705041b12a22e16fe00860b829e889e5f47c",
        "tokenizer/tokenizer_config.json": "c6c8004b1d310bd7c56455387c25cdf4da28594bbd5713aaa3fddfd5eac8f483",
    },
}


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download_group(group, label):
    root = REPO / "models" / group["subdir"]
    manifest = {}
    all_ok = True
    for rel, expected in group["files"].items():
        target = root / rel
        if target.exists() and target.stat().st_size > 1024:
            print(f"  = {label}:{rel} already present ({target.stat().st_size/1e6:.1f} MB)")
        else:
            print(f"  ↓ {label}:{rel} ...")
            hf_hub_download(
                group["repo"], rel, revision=group["rev"], local_dir=str(root)
            )
        got = sha256_of(target)
        if expected is None:
            print(f"    sha256 (NEW PIN): {got}")
            manifest[rel] = {"sha256": got, "size": target.stat().st_size, "pin": "new-int4-bundle"}
        elif got == expected:
            print(f"    sha256 OK ({got[:16]}...)")
            manifest[rel] = {"sha256": got, "size": target.stat().st_size, "pin": "rf5-committed"}
        else:
            print(f"    sha256 MISMATCH! expected {expected}, got {got}")
            all_ok = False
            manifest[rel] = {"sha256": got, "size": target.stat().st_size, "pin": "MISMATCH"}
    return manifest, all_ok


def main():
    print("M6-B1 weight vendoring")
    k_manifest, k_ok = download_group(KELLENOK, "kellenok")
    b_manifest, b_ok = download_group(Baberu, "baberu")

    total_k = sum(v["size"] for v in k_manifest.values())
    total_b = sum(v["size"] for v in b_manifest.values())
    print(f"\nkellenok total: {total_k/1e6:.1f} MB; baberu total: {total_b/1e6:.1f} MB")

    OUT_MANIFEST.write_text(json.dumps({
        "kellenok": {"repo": KELLENOK["repo"], "revision": KELLENOK["rev"], "files": k_manifest},
        "baberu": {"repo": Baberu["repo"], "revision": Baberu["rev"], "files": b_manifest},
    }, indent=1))
    print("manifest ->", OUT_MANIFEST)

    if not (k_ok and b_ok):
        print("SHA VERIFICATION FAILED")
        return 1
    print("ALL SHA CHECKS PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
