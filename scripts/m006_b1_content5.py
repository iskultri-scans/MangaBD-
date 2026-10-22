#!/usr/bin/env python3
r"""MANGABD-006 B1 — cell 5 patch content (verbatim texts, raw literals).

Every text here is inserted/replaced verbatim into cell 5 of the notebook
by scripts/m006_b1_build.py. Kept in a separate module so the build driver
stays readable and the patch texts remain reviewable byte-for-byte.
"""

# ── patch 5-1: OCR engine registry (insert before "# 4. Qwen VL OCR wrapper") ──
CELL5_REGISTRY = '''print("  ✅ Async + GPU helpers ready")
print()


# ═══════════════════════════════════════════════════════════
# 3b. OCR engine registry — MANGABD-006 B1 (fallback chain + lazy load)
# ═══════════════════════════════════════════════════════════

# Cell-1 "ocr" config-এর উপরে ADDITIVE merge (Phase A §M3.1): আগের সব key
# (qwen_model_id, deterministic, do_sample, num_beams, max_new_tokens,
# min_confidence, confidence_threshold, preprocess...) অপরিবর্তিত থাকে।
# "engine"-এর মানে এখন থেকে MODE: "auto" (fallback_chain ধরে চলবে) বা
# registry-র একটা engine নাম (manual — fail হলে [SKIP:OCR_FAILED])।
# kellenok/baberu weights এই repository-তে VENDORED (models/ দেখো, M6-B1)
# এবং শুধু local path থেকে load হয় — load-time-এ কখনো HF hub ছোঁয় না।
MANGABD_CONFIG["ocr"]["engine"] = "auto"
MANGABD_CONFIG["ocr"]["fallback_chain"] = [
    "qwen",
    "openrouter_vision",
    "kellenok",
    "baberu",
]
MANGABD_CONFIG["ocr"]["engines"] = {
    "qwen": {
        "type": "local",
        "model": "Qwen/Qwen2.5-VL-3B-Instruct",
        "vrmb_gb": 6.7,
        "load_fn": "ensure_qwen",
        "unload_fn": "unload_qwen",
    },
    "openrouter_vision": {
        "type": "cloud",
        "model": "google/gemini-2.0-flash-001",
        "key_env": "OPENROUTER_API_KEY",
        "vrmb_gb": 0,
        # cloud client-ও registry-driven dispatch-এ আসবে — directive-র
        # load_fn/unload_fn convention চারটা engine-এই প্রযোজ্য (zero
        # VRAM: load = lightweight client object, unload-এ কিছুই evict
        # হয় না)
        "load_fn": "ensure_openrouter_vision",
        "unload_fn": "unload_openrouter_vision",
    },
    "kellenok": {
        "type": "local",
        "model": "Kellenok/PP-OCRv6_manga",
        "weights_path": "models/kellenok/",  # vendored (M6-B1)
        "vrmb_gb": 0.4,
        "load_fn": "ensure_kellenok",
        "unload_fn": "unload_kellenok",
    },
    "baberu": {
        "type": "local",
        "model": "genshiai-daichi/baberu-ocr",
        "weights_path": "models/baberu/",  # vendored (M6-B1)
        "vrmb_gb": 0.2,
        "load_fn": "ensure_baberu",
        "unload_fn": "unload_baberu",
    },
}

# MANGABD-004 Phase B-এ ধরা পড়া stale non-collapsing literal
# ["qwen", "ovis", "hybrid"]-এর কোনো consumer ছিল না; এখন registry থেকে
# derive হয় (Phase A §M3.1 — defect closure)।
MANGABD_CONFIG["ocr"]["allowed_engines"] = list(
    MANGABD_CONFIG["ocr"]["engines"].keys()
)

print("─" * 70)
print("  3b. OCR engine registry (MANGABD-006 B1)")
print("─" * 70)

print(f"  Engine mode    : {MANGABD_CONFIG['ocr']['engine']}")
print(
    "  Fallback chain : "
    + " -> ".join(MANGABD_CONFIG["ocr"]["fallback_chain"])
)

for _engine_name, _engine_spec in MANGABD_CONFIG["ocr"]["engines"].items():
    print(
        f"    - {_engine_name:18s} [{_engine_spec.get('type', '?'):5s}] "
        f"{_engine_spec.get('model', '')}"
    )

try:
    import onnxruntime as _ort_probe  # noqa: F401

    print("  ✅ onnxruntime available — kellenok/baberu local engines ready")
except Exception:
    print(
        "  ⚠️ onnxruntime নেই — kellenok/baberu নিজে নিজে disable হবে, "
        "chain পরের engine-এ চলে যাবে। দরকার হলে: !pip install onnxruntime"
    )

print()


# ═══════════════════════════════════════════════════════════
# 4. Qwen VL OCR wrapper
# ═══════════════════════════════════════════════════════════
'''

# ── patch 5-2: ONNX engine wrapper classes (insert before "# 5. ModelManager") ──
CELL5_ONNX_CLASSES = '''print("  ✅ Qwen VL wrapper ready")
print()


# ═══════════════════════════════════════════════════════════
# 4b. ONNX OCR engine wrappers — MANGABD-006 B1 (vendored weights)
# ═══════════════════════════════════════════════════════════
#
# দুইটা CPU-device onnxruntime engine (zero VRAM by construction)।
# Inference classes গুলো MANGABD-006 RF-5-এ committed benchmark runner-দের
# (scripts/m006_phaseA_ext_{kellenok,baberu}.py) প্রমাণিত port — সেখান থেকেই
# নেওয়া, notebook-এ lazy-import discipline যোগ করা হয়েছে: package না থাকলে
# CLASS নয়, ENGINE-টা load-time-এ visible ভাবে disable হয় (chain পরের
# engine-এ যায়; Phase A §M5 row 8 degradation spec)।
#
# Vendored weights (repo models/ দেখো, M6-B1 build):
#   kellenok — det/manga_det_v0.2.onnx + rec/manga_rec_v0.2.onnx +
#              ppocrv6_dict.txt (~23 MB; RF-5 sha256 pins: d132078c...,
#              de12c84c..., b5f2bfe2...; hub rev b3b65cbd...)
#   baberu   — onnx/vision_int4.onnx + onnx/decoder_prefill_int8.onnx +
#              onnx/decoder_step_int8.onnx + tokenizer/* (~122 MB)।
#              fp16 vision (172.9 MB) GitHub-এর 100 MB hard limit ছাড়ায়,
#              তাই author-swept smallest int4 bundle vendored করা হয়েছে —
#              S003 corpus-এ re-measured: EN-bubble CER 0.016 EXACT একই,
#              R2-R6 সব row অভিন্ন (M6-B1 re-measurement record)।
#              Decoder int8 ফাইল দুটো RF-5 pin-ই (91de16d4... / f6164e9d...);
#              vision_int4-এর নতুন pin: 9526bcf9...; hub rev fdf292a1...


class KellenokOnnxOCR:
    """
    Kellenok/PP-OCRv6_manga v0.2 — onnxruntime port of the model repo-র
    published examples/onnx_openvino.py (Apache-2.0)। RF-5 runner-এর
    প্রমাণিত port (A.1.0 disclosure প্রযোজ্য):
      (a) reference-এর normalization float64 promote করে — এখানে explicit
          float32 cast (harness fix, model defect নয়);
      (b) det resize: 960 long-side; long-strip pixel-budget branch শুধু
          তখনই যখন সেটা আসলে DOWNSCALE করে (runner-এর disclosed port
          deviation — ছোট crop 960-এ normalize হয়েছে, R2-R6 arithmetic
          অপরিবর্তিত);
      (c) DB post-processing: thresh 0.15 / box 0.25 / unclip 1.4,
          minAreaRect, min-side 3; rec: h=48 natural width, CTC greedy,
          vertical line-crop auto-rotate 90 CCW।
    """

    DET_FN = "det/manga_det_v0.2.onnx"
    REC_FN = "rec/manga_rec_v0.2.onnx"
    DICT_FN = "ppocrv6_dict.txt"

    MEAN = np.array([0.485, 0.456, 0.406], np.float32)
    STD = np.array([0.229, 0.224, 0.225], np.float32)
    THRESH, BOX_THRESH, UNCLIP = 0.15, 0.25, 1.4

    def __init__(self, root):
        try:
            import cv2  # noqa: F401
            import onnxruntime as ort
            import pyclipper
        except Exception as exc:
            raise RuntimeError(
                "kellenok-র জন্য onnxruntime + pyclipper দরকার। "
                "Install: !pip install onnxruntime pyclipper "
                f"(import failed: {str(exc)[:100]})"
            )

        self._cv2 = cv2
        self._pyclipper = pyclipper

        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        mk = lambda p: ort.InferenceSession(
            str(p), so, providers=["CPUExecutionProvider"]
        )

        start = time.time()
        self.det = mk(root / self.DET_FN)
        self.rec = mk(root / self.REC_FN)
        self.cold_load_s = time.time() - start

        with open(root / self.DICT_FN, encoding="utf-8") as f:
            self.vocab = ["blank"] + [line.strip("\\r\\n") for line in f] + [" "]

        self.det_in = self.det.get_inputs()[0].name
        self.rec_in = self.rec.get_inputs()[0].name

    # ---- detection + DB post-processing ----
    def det_target_size(self, H, W):
        if max(H, W) / min(H, W) > 2 and max(H, W) > 960:
            ratio = min(1.0, (0.75 * 960.0 * 960.0 / (H * W)) ** 0.5)
        else:
            ratio = 960.0 / max(H, W)
        rh = max(int(round(H * ratio / 32) * 32), 32)
        rw = max(int(round(W * ratio / 32) * 32), 32)
        return rh, rw

    def detect_boxes(self, img):
        cv2 = self._cv2
        H, W = img.shape[:2]
        rh, rw = self.det_target_size(H, W)
        inp = cv2.resize(img, (rw, rh)).astype(np.float32) / 255.0
        inp = (inp - self.MEAN) / self.STD
        pred_map = self.det.run(
            None, {self.det_in: inp.transpose((2, 0, 1))[np.newaxis, ...]}
        )[0][0, 0]

        mask = pred_map > self.THRESH
        contours, _ = cv2.findContours(
            (mask * 255).astype(np.uint8), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
        )
        boxes = []
        for cnt in contours:
            pts = cnt.squeeze(1)
            if pts.ndim != 2 or pts.shape[0] < 4:
                continue
            if self._box_score(pred_map, pts) < self.BOX_THRESH:
                continue
            pts = self._unclip(pts, self.UNCLIP)
            if pts is None or len(pts) == 0:
                continue
            rect = cv2.minAreaRect(pts.astype(np.float32))
            _, (bw, bh), _ = rect
            if min(bw, bh) < 3:
                continue
            pts = cv2.boxPoints(rect).astype(np.float32)
            pts[:, 0] = np.clip(np.round(pts[:, 0] / rw * W), 0, W)
            pts[:, 1] = np.clip(np.round(pts[:, 1] / rh * H), 0, H)
            boxes.append(pts)
        return boxes

    def _box_score(self, pred, box):
        cv2 = self._cv2
        h, w = pred.shape[:2]
        b = box.copy().astype(np.int32)
        xmin = int(np.clip(np.floor(b[:, 0].min()), 0, w - 1))
        xmax = int(np.clip(np.ceil(b[:, 0].max()), 0, w - 1))
        ymin = int(np.clip(np.floor(b[:, 1].min()), 0, h - 1))
        ymax = int(np.clip(np.ceil(b[:, 1].max()), 0, h - 1))
        score_mask = np.zeros((ymax - ymin + 1, xmax - xmin + 1), dtype=np.uint8)
        b[:, 0] -= xmin
        b[:, 1] -= ymin
        cv2.fillPoly(score_mask, [b.reshape(-1, 2)], 1)
        return cv2.mean(pred[ymin : ymax + 1, xmin : xmax + 1], score_mask)[0]

    def _unclip(self, box, ratio):
        x, y = box[:, 0], box[:, 1]
        area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
        perimeter = np.linalg.norm(np.roll(box, -1, axis=0) - box, axis=1).sum()
        if area <= 0 or perimeter <= 0:
            return None
        offset = self._pyclipper.PyclipperOffset()
        offset.AddPath(
            box.tolist(),
            self._pyclipper.JT_ROUND,
            self._pyclipper.ET_CLOSEDPOLYGON,
        )
        paths = offset.Execute(area * ratio / perimeter)
        return np.asarray(paths[0], dtype=np.float32) if len(paths) == 1 else None

    # ---- recognition ----
    def read_crop(self, img, vertical_region=False, variant="upright"):
        """
        Full crop text: det boxes -> line order -> per-line rec -> CTC
        greedy -> joined। (vertical_region/variant প্যারামিটার RF-5
        runner-এর সাথে সামঞ্জস্যের জন্য; adapter path সবসময় horizontal
        semantics — y-ascending — ব্যবহার করে।)
        """
        cv2 = self._cv2
        boxes = sorted(
            self.detect_boxes(img), key=lambda b: min(p[1] for p in b)
        )
        H, W = img.shape[:2]
        texts = []
        for box in boxes:
            xs, ys = box[:, 0], box[:, 1]
            x1 = max(0, int(min(xs)))
            y1 = max(0, int(min(ys)))
            x2 = min(W, int(max(xs)))
            y2 = min(H, int(max(ys)))
            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            if crop.shape[0] > crop.shape[1]:
                crop = cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
            ch, cw = crop.shape[:2]
            natural_w = int(round(48.0 * cw / max(1, ch)))
            target_w = max(16, min(2400 if natural_w > 2000 else 640, natural_w))
            c_inp = cv2.resize(crop, (target_w, 48)).astype(np.float32) / 255.0
            c_inp = ((c_inp - 0.5) / 0.5).transpose((2, 0, 1))[np.newaxis, ...]
            logits = self.rec.run(None, {self.rec_in: c_inp})[0][0]
            indices = np.argmax(logits, axis=-1)
            text = "".join(
                self.vocab[idx]
                for i, idx in enumerate(indices)
                if idx != 0 and (i == 0 or idx != indices[i - 1])
            )
            if text:
                texts.append(text)
        return " ".join(texts), boxes

    def read_text(self, image_bgr):
        """
        M6-B1 adapter entry: BGR crop -> full text (horizontal line order)।
        """
        return self.read_crop(image_bgr)[0]


print("  ✅ kellenok ONNX wrapper ready")


# ---------------------------------------------------------------------------
# shipped code: genshiai-daichi/baberu-ocr onnx_infer.py (Apache-2.0),
# verbatim port — RF-5 runner-এ যেমন committed, শুধু vision default
# vendored int4 build + read_text adapter entry যোগ হয়েছে।
# ---------------------------------------------------------------------------
_B_PAST = [f"past_k{i}" for i in range(6)] + [f"past_v{i}" for i in range(6)]

_B_MEAN = np.array([0.485, 0.456, 0.406], np.float32)
_B_STD = np.array([0.229, 0.224, 0.225], np.float32)


def _b_preprocess(image):
    img = image.convert("RGB").resize((224, 224), PILImage.BICUBIC)
    x = (np.asarray(img, np.float32) / 255.0 - _B_MEAN) / _B_STD
    return x.transpose(2, 0, 1)[None]  # [1,3,224,224]


class _BaberuVocab:
    """Char-level vocab. ids 0..3 = <pad>/<bos>/<eos>/<unk>; id>=4 -> charset."""

    def __init__(self, vocab_json):
        import json
        import unicodedata

        charset = json.loads(
            Path(vocab_json).read_text(encoding="utf-8")
        )
        self.id2ch = {0: "", 1: "", 2: "", 3: ""}
        for i, ch in enumerate(charset):
            self.id2ch[i + 4] = ch
        self.bos, self.eos = 1, 2
        self.vocab_size = len(charset) + 4
        self.content_ids = {
            i + 4
            for i, ch in enumerate(charset)
            if len(ch) == 1 and ch not in "ーｰ〜~"
            and unicodedata.category(ch)[0] in "LN"
        }

    def decode(self, ids):
        return "".join(self.id2ch.get(i, "") for i in ids if i >= 4)


class BaberuOnnxOCR:
    """
    baberu-ocr v1.1 ONNX — shipped onnx_infer.py-র as-shipped decode
    (greedy + repetition_penalty 1.2 + run caps 12/16, max_new_tokens 256)।
    vision default = VENDORED int4 build (M6-B1 — উপরের vendoring note)।
    """

    def __init__(self, onnx_dir, tokenizer_dir, vision="vision_int4.onnx"):
        try:
            import onnxruntime as ort
        except Exception as exc:
            raise RuntimeError(
                "baberu-র জন্য onnxruntime দরকার। "
                f"Install: !pip install onnxruntime (import failed: {str(exc)[:100]})"
            )

        d = Path(onnx_dir)
        so = ort.SessionOptions()
        so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        mk = lambda p: ort.InferenceSession(
            str(p), so, providers=["CPUExecutionProvider"]
        )
        self.vis = mk(d / vision)
        self.pre = mk(d / "decoder_prefill_int8.onnx")
        self.stp = mk(d / "decoder_step_int8.onnx")
        self.vocab = _BaberuVocab(Path(tokenizer_dir) / "vocab.json")

    def __call__(self, image, max_new_tokens=256, repetition_penalty=1.2,
                 max_content_run=12, max_symbol_run=16):
        v = self.vocab
        vis = self.vis.run(
            ["vision_embeds"], {"pixel_values": _b_preprocess(image)}
        )[0]
        out = self.pre.run(
            None,
            {"vision_embeds": vis, "input_ids": np.array([[v.bos]], np.int64)},
        )
        logits, present = out[0][0, -1].astype(np.float64), out[1:]
        seq, toks, pos = [v.bos], [], vis.shape[1] + 1
        for _ in range(max_new_tokens):
            if repetition_penalty != 1.0:
                for tid in set(seq):
                    s = logits[tid]
                    logits[tid] = s * repetition_penalty if s < 0 else s / repetition_penalty
            last = toks[-1] if toks else 0
            cap = max_content_run if last in v.content_ids else max_symbol_run if last > 3 else 0
            if cap:
                run = 0
                for t in reversed(toks):
                    if t == last:
                        run += 1
                    else:
                        break
                if run >= cap:
                    logits[last] = -np.inf
            nxt = int(np.argmax(logits))
            if nxt == v.eos:
                break
            toks.append(nxt)
            seq.append(nxt)
            if len(toks) >= max_new_tokens:
                break
            feed = {
                "input_ids": np.array([[nxt]], np.int64),
                "position_ids": np.array([[pos]], np.int64),
            }
            feed.update({nm: t for nm, t in zip(_B_PAST, present)})
            out = self.stp.run(None, feed)
            logits, present = out[0][0, -1].astype(np.float64), out[1:]
            pos += 1
        return v.decode(toks)

    def read_text(self, image_bgr):
        """
        M6-B1 adapter entry: BGR numpy crop -> RGB PIL -> as-shipped decode।
        """
        rgb = np.ascontiguousarray(np.asarray(image_bgr)[:, :, ::-1])
        return self(PILImage.fromarray(rgb))


print("  ✅ baberu ONNX wrapper ready")
print()


# ═══════════════════════════════════════════════════════════
# 5. ModelManager
# ═══════════════════════════════════════════════════════════
'''

# ── patch 5-3: ModelManager registry methods (insert before "# Future OCR placeholder") ──
CELL5_MM_METHODS = '''    # ───────────────────────────────────────────────────────
    # OCR engine registry — MANGABD-006 B1 (lazy load + single resident)
    # ───────────────────────────────────────────────────────

    def _resolve_vendored_engine_dir(self, engine_name):
        """
        Vendored weights directory খোঁজে (registry weights_path)।

        Candidate ক্রম:
          1. CWD-relative path (repo checkout / notebook working dir)
          2. MODELS_DIR/<engine> (notebook-এর models convention)
        """
        spec = self.config["ocr"]["engines"][engine_name]
        rel = str(spec.get("weights_path", f"models/{engine_name}/")).rstrip("/")

        candidates = [
            Path(rel),
            MODELS_DIR / engine_name,
        ]

        for cand in candidates:
            if cand.is_dir():
                return cand

        raise RuntimeError(
            f"{engine_name} weights পাওয়া যায়নি। Vendored location: {rel} "
            f"(এই repo) বা {MODELS_DIR / engine_name}। Repo-র models/{engine_name}/ "
            f"folder-টা working directory/MODELS_DIR-এ আনো।"
        )

    def ensure_kellenok(self, force=False):
        """
        M6-B1: Kellenok/PP-OCRv6_manga v0.2 ONNX (det 1.8MB + rec 21.2MB +
        dict) — CPU-device onnxruntime, zero VRAM by construction।
        """
        if "kellenok" in self.instances and not force:
            return self.instances["kellenok"]

        start = time.time()

        try:
            weights_dir = self._resolve_vendored_engine_dir("kellenok")

            print("  📥 Loading kellenok ONNX (CPU, vendored weights)")

            engine = KellenokOnnxOCR(weights_dir)

            self.instances["kellenok"] = engine
            self.load_times["kellenok"] = time.time() - start

            log_event(
                f"kellenok loaded in {self.load_times['kellenok']:.1f}s",
                level="INFO",
            )

            print(f"  ✅ kellenok loaded in {self.load_times['kellenok']:.1f}s")

            return engine

        except Exception as exc:
            self.errors["kellenok"] = str(exc)[:300]

            log_event(
                f"kellenok load failed: {str(exc)[:160]}",
                level="ERROR",
            )

            raise

    def ensure_baberu(self, force=False):
        """
        M6-B1: genshiai-daichi/baberu-ocr v1.1 ONNX int4 bundle (vendored)
        — CPU-device onnxruntime, zero VRAM by construction।
        """
        if "baberu" in self.instances and not force:
            return self.instances["baberu"]

        start = time.time()

        try:
            weights_dir = self._resolve_vendored_engine_dir("baberu")

            print("  📥 Loading baberu ONNX (CPU, vendored int4 build)")

            engine = BaberuOnnxOCR(weights_dir / "onnx", weights_dir / "tokenizer")

            self.instances["baberu"] = engine
            self.load_times["baberu"] = time.time() - start

            log_event(
                f"baberu loaded in {self.load_times['baberu']:.1f}s",
                level="INFO",
            )

            print(f"  ✅ baberu loaded in {self.load_times['baberu']:.1f}s")

            return engine

        except Exception as exc:
            self.errors["baberu"] = str(exc)[:300]

            log_event(
                f"baberu load failed: {str(exc)[:160]}",
                level="ERROR",
            )

            raise

    def ensure_openrouter_vision(self, force=False):
        """
        M6-B1: cloud vision client — zero VRAM, কোনো model load নেই।
        API key call-time-এ পড়া হয় (cell-8 translator-এর V-5-proven
        capture pattern: MANGABD_SECRETS -> os.environ)।
        """
        if "openrouter_vision" in self.instances and not force:
            return self.instances["openrouter_vision"]

        start = time.time()

        try:
            spec = self.config["ocr"]["engines"]["openrouter_vision"]

            client = {
                "type": "cloud",
                "model": str(spec.get("model", "google/gemini-2.0-flash-001")),
                "key_env": str(spec.get("key_env", "OPENROUTER_API_KEY")),
                "base_url": "https://openrouter.ai/api/v1",
            }

            self.instances["openrouter_vision"] = client
            self.load_times["openrouter_vision"] = time.time() - start

            log_event(
                "OpenRouter vision client ready (cloud, zero VRAM)",
                level="INFO",
            )

            print("  ✅ OpenRouter vision client ready (cloud, zero VRAM)")

            return client

        except Exception as exc:
            self.errors["openrouter_vision"] = str(exc)[:300]

            log_event(
                f"OpenRouter vision client init failed: {str(exc)[:160]}",
                level="ERROR",
            )

            raise

    def unload_qwen(self):
        """M6-B1 registry unload_fn — qwen।"""
        return self.unload("qwen")

    def unload_kellenok(self):
        """M6-B1 registry unload_fn — kellenok।"""
        return self.unload("kellenok")

    def unload_baberu(self):
        """M6-B1 registry unload_fn — baberu।"""
        return self.unload("baberu")

    def unload_openrouter_vision(self):
        """M6-B1 registry unload_fn — openrouter_vision (client object)।"""
        return self.unload("openrouter_vision")

    def ensure_ocr_engine(self, engine_name, force=False):
        """
        M6-B1: registry-driven lazy load — chain-এর প্রতিটা engine এখান দিয়ে
        load হয়।

        Lazy-load discipline (directive rule):
          - local engine cold-load-এর আগে unload_all(exclude=[engine]) —
            একসাথে শুধু একটাই local OCR engine resident থাকে;
          - cloud engine (openrouter_vision) zero-VRAM client — কিছুই evict
            করে না।
        """
        engines = self.config.get("ocr", {}).get("engines", {})

        if engine_name not in engines:
            raise ValueError(
                f"Unknown OCR engine: {engine_name!r}. "
                f"Registry: {sorted(engines.keys())}"
            )

        if engine_name in self.instances and not force:
            return self.instances[engine_name]

        spec = engines[engine_name]

        if spec.get("type") == "local":
            self.unload_all(exclude=[engine_name])

        load_fn = spec.get("load_fn")

        if not load_fn or not hasattr(self, load_fn):
            raise ValueError(
                f"Registry load_fn missing for engine {engine_name!r}"
            )

        return getattr(self, load_fn)(force=force)

    def unload_ocr_engine(self, engine_name):
        """
        M6-B1: registry-driven unload (unload_fn থাকলে সেটাই, নাহলে generic)।
        """
        engines = self.config.get("ocr", {}).get("engines", {})
        spec = engines.get(engine_name, {})
        unload_fn = spec.get("unload_fn")

        if unload_fn and hasattr(self, unload_fn):
            return getattr(self, unload_fn)()

        return self.unload(engine_name)

    # ───────────────────────────────────────────────────────
    # Future OCR placeholder
    # ───────────────────────────────────────────────────────
'''
