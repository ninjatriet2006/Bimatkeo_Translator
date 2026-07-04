import threading
import queue
import gc
import fnmatch
import re
from app.core.dto import PageContext
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer, BaseTranslator, BaseInpainter, BaseRenderer, BaseCloudOCR, BaseUpscaler
from app.core.vision_utils import sort_comic_text_boxes
from app.core.ocr_corrector import OfflineOCRCorrector

try:
    from langdetect import detect
    import langdetect
except ImportError:
    detect = None

try:
    import torch # type: ignore
except ImportError:
    torch = None

def release_gpu_memory():
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

class OCRWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q_trans: queue.Queue, out_q_inpaint: queue.Queue, out_q_render: queue.Queue, detector: BaseTextDetector | None, recognizer: BaseTextRecognizer | None, log_callback=None, cloud_ocr: BaseCloudOCR | None = None, ocr_config: dict | None = None, render_config: dict | None = None):
        super().__init__()
        self.in_q = in_q
        self.out_q_trans = out_q_trans
        self.out_q_inpaint = out_q_inpaint
        self.out_q_render = out_q_render
        self.detector = detector
        self.recognizer = recognizer
        self.cloud_ocr = cloud_ocr
        self.ocr_config = ocr_config or {}
        self.render_config = render_config or {}
        self.log_callback = log_callback
        self.corrector = OfflineOCRCorrector(log_callback=log_callback)
        self.daemon = True

    def _apply_filters(self, bboxes, texts):
        min_text_length = int(self.ocr_config.get('min_text_length', 0))
        ignore_bubble = int(self.ocr_config.get('ignore_bubble', 0))
        filter_text_str = self.ocr_config.get('filter_text', '')
        filter_texts = [f.strip() for f in filter_text_str.split(',')] if filter_text_str else []

        filtered_bboxes = []
        filtered_texts = []
        for box, text in zip(bboxes, texts):
            w_box = box[2] - box[0]
            h_box = box[3] - box[1]
            if w_box * h_box < ignore_bubble:
                continue
            
            if len(text.strip()) < min_text_length:
                continue
                
            if any(f in text for f in filter_texts):
                continue
                
            filtered_bboxes.append(box)
            filtered_texts.append(text)
            
        return filtered_bboxes, filtered_texts

    def _detect_orientation(self, det_image, recognizer, detector):
        import cv2, numpy as np
        raw_bboxes, _ = detector.detect(det_image)
        if not raw_bboxes: return 0
        boxes = sorted(raw_bboxes, key=lambda b: (b[2]-b[0])*(b[3]-b[1]), reverse=True)[:3]
        angles = [0, 90, 180, 270]
        angle_scores = {a: 0.0 for a in angles}
        
        for angle in angles:
            scores = []
            for box in boxes:
                crop = det_image[box[1]:box[3], box[0]:box[2]]
                if crop.size == 0: continue
                if angle == 90: crop = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)
                elif angle == 180: crop = cv2.rotate(crop, cv2.ROTATE_180)
                elif angle == 270: crop = cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
                text, conf = recognizer.recognize(crop)
                scores.append(conf)
            if scores: angle_scores[angle] = sum(scores) / len(scores)
        return max(angle_scores.items(), key=lambda x: x[1])[0]

    def run(self):
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
                self.out_q_trans.put(None)
                self.out_q_inpaint.put(None)
                self.out_q_render.put(None)
                self.in_q.task_done()
                break
            
            if self.log_callback:
                self.log_callback("OCR", f"Processing {ctx.page_id}...")

            image = ctx.get_original_image()

            if self.cloud_ocr and image is not None:
                h, w = image.shape[:2]
                results = self.cloud_ocr.recognize_full_page(image)
                
                raw_bboxes = [r["box"] for r in results]
                raw_texts = [r["text"] for r in results]
                
                filtered_bboxes, filtered_texts = self._apply_filters(raw_bboxes, raw_texts)
                
                ui_direction = self.render_config.get("direction", "Horizontal: Right-to-Left")
                dir_map = {
                    "Horizontal: Right-to-Left": "rtl_ttb",
                    "Horizontal: Left-to-Right": "ltr_ttb",
                    "Vertical: Right-to-Left": "ttb_rtl",
                    "Vertical: Left-to-Right": "ttb_ltr"
                }
                direction = dir_map.get(ui_direction, "rtl_ttb")
                
                sorted_bboxes = sort_comic_text_boxes(filtered_bboxes, direction=direction, image_width=w, image_height=h)
                
                # Map sorted boxes to text
                box_to_text = {tuple(b): t for b, t in zip(filtered_bboxes, filtered_texts)}
                
                from app.core.vision_utils import merge_nearby_boxes_and_texts
                merged_bboxes, merged_texts = merge_nearby_boxes_and_texts(
                    sorted_bboxes, 
                    [box_to_text[tuple(b)] for b in sorted_bboxes], 
                    w, h
                )
                
                ctx.raw_bboxes = sorted_bboxes
                ctx.bboxes = merged_bboxes
                ctx.original_texts = merged_texts
                ctx.translated_texts = [""] * len(ctx.original_texts)
                
                if self.log_callback:
                    self.log_callback("OCR", f"Cloud OCR đã xử lý và gom lại thành {len(ctx.bboxes)} bong bóng chữ.")

            elif self.detector and image is not None:
                h, w = image.shape[:2]
                
                import cv2
                import numpy as np
                det_image = image.copy()
                
                # 1. Invert colors if requested
                if self.ocr_config.get('det_invert'):
                    det_image = cv2.bitwise_not(det_image)
                
                # 2. Apply Gamma Correction if requested
                gamma = float(self.ocr_config.get('det_gamma_correct', 1.0))
                if gamma != 1.0:
                    inv_gamma = 1.0 / gamma
                    table = np.array([((i / 255.0) ** inv_gamma) * 255
                                      for i in np.arange(0, 256)]).astype("uint8")
                    det_image = cv2.LUT(det_image, table)
                    
                # 3. Auto-Rotate check
                if self.ocr_config.get('det_auto_rotate') and self.recognizer:
                    best_angle = self._detect_orientation(det_image, self.recognizer, self.detector)
                    if best_angle != 0:
                        if self.log_callback:
                            self.log_callback("OCR", f"Auto-Rotate: Phát hiện ảnh bị xoay, tự động xoay lại {best_angle} độ.")
                        if best_angle == 90:
                            image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
                            det_image = cv2.rotate(det_image, cv2.ROTATE_90_CLOCKWISE)
                        elif best_angle == 180:
                            image = cv2.rotate(image, cv2.ROTATE_180)
                            det_image = cv2.rotate(det_image, cv2.ROTATE_180)
                        elif best_angle == 270:
                            image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                            det_image = cv2.rotate(det_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        h, w = image.shape[:2]
                        ctx.set_original_image(image)
                        
                raw_bboxes, raw_polygons = self.detector.detect(det_image)
                
                # Bundle box and polygon to keep them together during sorting
                if not raw_polygons:
                    raw_polygons = [[] for _ in raw_bboxes]
                bundled_boxes = [box + [poly] for box, poly in zip(raw_bboxes, raw_polygons)]
                
                # Sắp xếp lại box theo chuẩn đọc truyện.
                ui_direction = self.render_config.get("direction", "Horizontal: Right-to-Left")
                dir_map = {
                    "Horizontal: Right-to-Left": "rtl_ttb",
                    "Horizontal: Left-to-Right": "ltr_ttb",
                    "Vertical: Right-to-Left": "ttb_rtl",
                    "Vertical: Left-to-Right": "ttb_ltr"
                }
                direction = dir_map.get(ui_direction, "rtl_ttb")
                
                bundled_boxes = sort_comic_text_boxes(bundled_boxes, direction=direction, image_width=w, image_height=h) # type: ignore
                
                bboxes = [b[:4] for b in bundled_boxes]
                polygons = [b[4] for b in bundled_boxes]
                
                texts = []
                prob_thresh = float(self.ocr_config.get('prob', 0.0) or 0.0)
                
                if self.recognizer and bboxes:
                    for i, box in enumerate(bboxes):
                        poly = polygons[i]
                        try:
                            if self.ocr_config.get('det_rotate') and poly:
                                poly_arr = np.array(poly, dtype=np.float32)
                                rect = cv2.minAreaRect(poly_arr)
                                (center, (width, height), angle) = rect
                                if height > width:
                                    width, height = height, width
                                    angle += 90.0
                                
                                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                                box_w, box_h = int(width), int(height)
                                rotated = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))
                                crop = cv2.getRectSubPix(rotated, (box_w, box_h), center)
                            else:
                                crop = image[box[1]:box[3], box[0]:box[2]]
                                
                            if crop.size > 0 and crop.shape[0] >= 8 and crop.shape[1] >= 8:
                                text, conf = self.recognizer.recognize(crop)
                                if conf > 0 and conf < prob_thresh:
                                    text = "" # Bỏ qua do điểm tự tin thấp
                            else:
                                text = ""
                        except Exception as e:
                            if self.log_callback:
                                self.log_callback("ERROR", f"OCR Error on {ctx.page_id}: {e}")
                            text = ""
                        texts.append(text)
                            
                # Stage 2: Vision OCR Correction
                texts = self.corrector.correct(texts, image)
                
                # Stage 2.5: Filtering
                bboxes, texts = self._apply_filters(bboxes, texts)
                
                # Stage 3: Merge nearby boxes and texts
                from app.core.vision_utils import merge_nearby_boxes_and_texts
                if self.ocr_config.get('merge_nearby_boxes', False):
                    merged_bboxes, merged_texts = merge_nearby_boxes_and_texts(bboxes, texts, w, h)
                    # Chạy lại corrector trên văn bản đã gộp để xử lý lỗi dính chữ Hán vào tiếng Anh do merge
                    merged_texts = self.corrector.correct(merged_texts)
                else:
                    merged_bboxes, merged_texts = bboxes, texts
                
                ctx.raw_bboxes = bboxes
                ctx.bboxes = merged_bboxes
                ctx.original_texts = merged_texts
                ctx.translated_texts = [""] * len(merged_texts)
                
                if self.log_callback:
                    self.log_callback("OCR", f"Detector tìm thấy và gom lại thành {len(merged_bboxes)} bong bóng chữ.")
            
            # Fork (Push to 3 queues simultaneously)
            self.out_q_trans.put(ctx)
            self.out_q_inpaint.put(ctx)
            self.out_q_render.put(ctx)
            self.in_q.task_done()
            
            # Optional: release_gpu_memory()


class TranslatorWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, translator_or_chain, src_lang: str, tgt_lang: str, log_callback=None, hitl_callback=None, skip_languages=None, filter_texts=None, no_text_lang_skip=False, max_request_length=-1, editor_translator=None, context_window=10, stride_window=5):
        super().__init__()
        self.in_q = in_q
        
        # Determine if we have a single translator or a chain
        if isinstance(translator_or_chain, list):
            self.chained_translators = translator_or_chain
        else:
            self.chained_translators = [(translator_or_chain, tgt_lang)] if translator_or_chain else []
            
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.log_callback = log_callback
        self.skip_languages = skip_languages or {}
        self.filter_texts = filter_texts or []
        self.no_text_lang_skip = no_text_lang_skip
        self.max_request_length = max_request_length
        
        self.editor_translator = editor_translator
        self.context_window = max(1, context_window)
        self.stride_window = max(1, stride_window)
        self.daemon = True

    def _should_skip_text(self, text, current_tgt_lang):
        if not text or not text.strip():
            return True
            
        # 1. Filter texts check
        for pattern in self.filter_texts:
            pattern = str(pattern).strip()
            if not pattern: continue
            # Regex match
            if pattern.startswith('/') and pattern.endswith('/'):
                regex = pattern[1:-1]
                try:
                    if re.search(regex, text):
                        return True
                except re.error:
                    pass
            # Exact match
            elif pattern.startswith('"') and pattern.endswith('"'):
                if text == pattern[1:-1]:
                    return True
            # Wildcard / Substring match
            else:
                if fnmatch.fnmatch(text, pattern) or pattern in text:
                    return True

        # 2. Language detect check
        if detect and (self.skip_languages or not self.no_text_lang_skip):
            try:
                detected_lang = detect(text).upper()
                
                # Check skip languages
                # Some codes from langdetect need to be mapped if needed, but we'll do direct match
                if self.skip_languages.get(detected_lang, False):
                    return True
                
                # Check translate same language
                if not self.no_text_lang_skip and detected_lang == current_tgt_lang.upper()[:2]:
                    return True
            except Exception:
                pass # langdetect might throw LangDetectException if no features

        return False

    def run(self):
        import queue
        from app.core.dto import PageContext
        
        stage1_buffer = []
        stage2_buffer = []
        
        window_size1 = self.context_window
        stride1 = self.stride_window
        
        window_size2 = window_size1 * 2
        stride2 = stride1 * 2
        
        def process_stage1_window(window: list[PageContext]):
            if not self.chained_translators:
                for ctx in window:
                    if ctx.stage1_candidates is None:
                        ctx.stage1_candidates = []
                return
                
            step_translator, step_tgt_lang = self.chained_translators[0]
            texts_to_translate = []
            page_line_map = []
            
            for ctx in window:
                if ctx.stage1_candidates is None:
                    ctx.stage1_candidates = [[] for _ in range(len(ctx.original_texts or []))]
                    
                if not ctx.original_texts:
                    texts_to_translate.append(f"[Trang {ctx.page_id}: Silent Panel / Không có thoại]")
                    page_line_map.append((ctx, -1))
                else:
                    for i, t in enumerate(ctx.original_texts):
                        if self._should_skip_text(t, step_tgt_lang):
                            if ctx.stage1_candidates is not None:
                                ctx.stage1_candidates[i].append({"text": t, "score": 1.0})
                        else:
                            texts_to_translate.append(t)
                            page_line_map.append((ctx, i))
                        
            if not texts_to_translate:
                return
                
            def _process_recursive(texts, mapping):
                if not texts:
                    return
                    
                total_chars = sum(len(t) for t in texts)
                
                if self.max_request_length > 0 and total_chars > self.max_request_length and len(texts) > 1:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Stage 1 payload ({total_chars} chars) exceeds limit. Splitting into 2 batches...")
                    mid = len(texts) // 2
                    _process_recursive(texts[:mid], mapping[:mid])
                    _process_recursive(texts[mid:], mapping[mid:])
                    return
                    
                try:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Stage 1: Processing batch of {len(texts)} lines ({total_chars} chars).")
                    
                    translated_part = step_translator.translate(texts, self.src_lang, step_tgt_lang, [])
                    
                    for j, (ctx, line_idx) in enumerate(mapping):
                        if j < len(translated_part):
                            res = translated_part[j]
                            text = res if isinstance(res, str) else res.get("text", "")
                            if self.log_callback:
                                self.log_callback("DEBUG", f"OCR: {texts[j]} -> TRANSLATED: {text}")
                            score = 0.5 if isinstance(res, str) else res.get("score", 0.5)
                            if line_idx != -1 and ctx.stage1_candidates is not None:
                                ctx.stage1_candidates[line_idx].append({"text": text, "score": score})
                except Exception as e:
                    if self.log_callback:
                        self.log_callback("ERROR", f"Stage 1 Error: {e}")

            _process_recursive(texts_to_translate, page_line_map)

        def commit_stage1_page(ctx: PageContext):
            if ctx.stage1_candidates is None:
                ctx.translated_texts = list(ctx.original_texts or [])
                return
                
            best_translations = []
            if ctx.stage1_candidates is not None:
                for line_cands in ctx.stage1_candidates:
                    if not line_cands:
                        best_translations.append("")
                    else:
                        best_cands = sorted(line_cands, key=lambda x: x["score"], reverse=True)
                        best_translations.append(best_cands[0]["text"])
            ctx.translated_texts = best_translations

        def process_stage2_window(window: list[PageContext]):
            if not self.editor_translator:
                return
                
            texts_to_translate = []
            page_line_map = []
            
            for ctx in window:
                if ctx.stage2_candidates is None:
                    ctx.stage2_candidates = [[] for _ in range(len(ctx.translated_texts or []))]
                    
                if not ctx.translated_texts:
                    texts_to_translate.append(f"[Trang {ctx.page_id}: Silent Panel / Không có thoại]")
                    page_line_map.append((ctx, -1))
                else:
                    for i, t in enumerate(ctx.translated_texts):
                        texts_to_translate.append(t)
                        page_line_map.append((ctx, i))
                        
            if not texts_to_translate:
                return
                
            def _process_recursive(texts, mapping):
                if not texts:
                    return
                    
                total_chars = sum(len(t) for t in texts)
                
                if self.max_request_length > 0 and total_chars > self.max_request_length and len(texts) > 1:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Stage 2 payload ({total_chars} chars) exceeds limit. Splitting into 2 batches...")
                    mid = len(texts) // 2
                    _process_recursive(texts[:mid], mapping[:mid])
                    _process_recursive(texts[mid:], mapping[mid:])
                    return
                    
                try:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Stage 2 (Double Check): Editing batch of {len(texts)} lines ({total_chars} chars).")
                    
                    translated_part = self.editor_translator.translate(texts, "vi", "vi", [])
                    
                    for j, (ctx, line_idx) in enumerate(mapping):
                        if j < len(translated_part):
                            res = translated_part[j]
                            text = res if isinstance(res, str) else res.get("text", "")
                            score = 0.5 if isinstance(res, str) else res.get("score", 0.5)
                            if line_idx != -1 and ctx.stage2_candidates is not None:
                                ctx.stage2_candidates[line_idx].append({"text": text, "score": score})
                except Exception as e:
                    if self.log_callback:
                        self.log_callback("ERROR", f"Stage 2 Error: {e}")

            _process_recursive(texts_to_translate, page_line_map)

        def commit_stage2_page(ctx: PageContext):
            if ctx.stage2_candidates is not None:
                best_translations = []
                translated_texts = ctx.translated_texts or []
                for i, line_cands in enumerate(ctx.stage2_candidates):
                    if not line_cands:
                        best_translations.append(translated_texts[i] if i < len(translated_texts) else "")
                    else:
                        best_cands = sorted(line_cands, key=lambda x: x["score"], reverse=True)
                        best_translations.append(best_cands[0]["text"])
                ctx.translated_texts = best_translations
            ctx.trans_done.set()
            self.in_q.task_done()

        while True:
            try:
                ctx = self.in_q.get(timeout=0.5)
            except queue.Empty:
                continue
                
            if ctx is None:
                # Flush Stage 1
                while stage1_buffer:
                    process_stage1_window(stage1_buffer)
                    popped = stage1_buffer[:stride1]
                    stage1_buffer = stage1_buffer[stride1:]
                    for p in popped:
                        commit_stage1_page(p)
                        if self.editor_translator:
                            stage2_buffer.append(p)
                        else:
                            p.trans_done.set()
                            self.in_q.task_done()
                            
                # Flush Stage 2
                if self.editor_translator:
                    while stage2_buffer:
                        process_stage2_window(stage2_buffer)
                        popped = stage2_buffer[:stride2]
                        stage2_buffer = stage2_buffer[stride2:]
                        for p in popped:
                            commit_stage2_page(p)
                            
                self.in_q.task_done() # For the None token
                break
                
            stage1_buffer.append(ctx)
            if len(stage1_buffer) >= window_size1:
                process_stage1_window(stage1_buffer)
                popped = stage1_buffer[:stride1]
                stage1_buffer = stage1_buffer[stride1:]
                for p in popped:
                    commit_stage1_page(p)
                    if self.editor_translator:
                        stage2_buffer.append(p)
                        if len(stage2_buffer) >= window_size2:
                            process_stage2_window(stage2_buffer)
                            popped2 = stage2_buffer[:stride2]
                            stage2_buffer = stage2_buffer[stride2:]
                            for p2 in popped2:
                                commit_stage2_page(p2)
                    else:
                        p.trans_done.set()
                        self.in_q.task_done()


class InpaintWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, inpainter: BaseInpainter | None, log_callback=None, out_q: queue.Queue | None = None):
        super().__init__()
        self.in_q = in_q
        self.out_q = out_q
        self.inpainter = inpainter
        self.log_callback = log_callback
        self.daemon = True

    def run(self):
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
                self.in_q.task_done()
                break
            
            if self.log_callback:
                self.log_callback("INPAINT", f"Inpainting {ctx.page_id}...")

            if self.inpainter and (ctx.raw_bboxes or ctx.bboxes):
                image = ctx.get_original_image()
                    
                if image is not None:
                    try:
                        boxes_to_inpaint = ctx.raw_bboxes if ctx.raw_bboxes is not None else ctx.bboxes
                        if boxes_to_inpaint is not None:
                            inpainted = self.inpainter.inpaint(image, boxes_to_inpaint)
                            ctx.set_inpainted_image(inpainted)
                        else:
                            ctx.set_inpainted_image(image.copy())
                    except Exception as e:
                        if self.log_callback:
                            self.log_callback("ERROR", f"Inpaint Error on {ctx.page_id}: {e}")
                        ctx.inpainted_image = image.copy()

            if self.out_q:
                self.out_q.put(ctx)
            else:
                ctx.inpaint_done.set()  # Signal completion of this fork
                
            self.in_q.task_done()
            release_gpu_memory()


class UpscalerWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, upscaler: BaseUpscaler | None, ratio: int, log_callback=None):
        super().__init__()
        self.in_q = in_q
        self.upscaler = upscaler
        self.ratio = ratio
        self.log_callback = log_callback
        self.daemon = True

    def run(self):
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
                self.in_q.task_done()
                break
                
            if self.log_callback:
                self.log_callback("UPSCALE", f"Upscaling {ctx.page_id} by {self.ratio}x...")

            if self.upscaler and self.ratio > 1:
                try:
                    # Resolve background image (either inpainted or original)
                    bg_image = ctx.get_background_image()
                            
                    if bg_image is not None:
                        upscaled = self.upscaler.upscale(bg_image, self.ratio)
                        ctx.set_inpainted_image(upscaled)
                        # Update bounding boxes
                        if ctx.bboxes:
                            ctx.bboxes = [[coord * self.ratio for coord in box] for box in ctx.bboxes]
                        if ctx.raw_bboxes:
                            ctx.raw_bboxes = [[coord * self.ratio for coord in box] for box in ctx.raw_bboxes]
                        # Set upscale ratio for downstream logic if needed
                        ctx.upscale_ratio = getattr(ctx, 'upscale_ratio', 1) * self.ratio
                except Exception as e:
                    if self.log_callback:
                        self.log_callback("ERROR", f"Upscale Error on {ctx.page_id}: {e}")

            ctx.inpaint_done.set()  # Signal completion of the fork for the RenderWorker to join
            self.in_q.task_done()
            release_gpu_memory()


class RenderWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q: queue.Queue, renderer: BaseRenderer | None, log_callback=None):
        super().__init__()
        self.in_q = in_q
        self.out_q = out_q
        self.renderer = renderer
        self.log_callback = log_callback
        self.daemon = True

    def run(self):
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
                self.out_q.put(None)
                self.in_q.task_done()
                break
            
            # JOIN: Wait for both forks to complete
            ctx.trans_done.wait()
            ctx.inpaint_done.wait()
            
            if self.log_callback:
                self.log_callback("RENDER", f"Rendering {ctx.page_id}...")

            if self.renderer:
                bg_image = ctx.get_background_image()
                        
                texts = ctx.translated_texts if ctx.translated_texts else ctx.original_texts
                
                if bg_image is not None and texts and ctx.bboxes:
                    try:
                        rendered = self.renderer.render(bg_image, ctx.bboxes, texts)
                        ctx.rendered_image = rendered
                    except Exception as e:
                        if self.log_callback:
                            self.log_callback("ERROR", f"Render Error on {ctx.page_id}: {e}")
                        ctx.rendered_image = bg_image.copy()
                else:
                    ctx.rendered_image = bg_image.copy() if bg_image is not None else None
            else:
                bg_image = ctx.get_background_image()
                ctx.rendered_image = bg_image.copy() if bg_image is not None else None

            self.out_q.put(ctx)
            self.in_q.task_done()
