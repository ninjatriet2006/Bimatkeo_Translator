import threading
import queue
import gc
import fnmatch
import re
from app.core.dto import PageContext
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer, BaseTranslator, BaseInpainter, BaseRenderer, BaseCloudOCR
from app.core.vision_utils import sort_comic_text_boxes
from app.core.ocr_corrector import VisionOCRCorrector

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
        self.corrector = VisionOCRCorrector(use_llm=True, log_callback=log_callback)
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

            if self.cloud_ocr and ctx.original_image is not None:
                h, w = ctx.original_image.shape[:2]
                results = self.cloud_ocr.recognize_full_page(ctx.original_image)
                
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

            elif self.detector and ctx.original_image is not None:
                h, w = ctx.original_image.shape[:2]
                
                import cv2
                import numpy as np
                det_image = ctx.original_image.copy()
                
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
                            ctx.original_image = cv2.rotate(ctx.original_image, cv2.ROTATE_90_CLOCKWISE)
                            det_image = cv2.rotate(det_image, cv2.ROTATE_90_CLOCKWISE)
                        elif best_angle == 180:
                            ctx.original_image = cv2.rotate(ctx.original_image, cv2.ROTATE_180)
                            det_image = cv2.rotate(det_image, cv2.ROTATE_180)
                        elif best_angle == 270:
                            ctx.original_image = cv2.rotate(ctx.original_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                            det_image = cv2.rotate(det_image, cv2.ROTATE_90_COUNTERCLOCKWISE)
                        h, w = ctx.original_image.shape[:2]
                        
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
                                rotated = cv2.warpAffine(ctx.original_image, M, (ctx.original_image.shape[1], ctx.original_image.shape[0]))
                                crop = cv2.getRectSubPix(rotated, (box_w, box_h), center)
                            else:
                                crop = ctx.original_image[box[1]:box[3], box[0]:box[2]]
                                
                            if crop.size > 0:
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
                texts = self.corrector.correct(texts, ctx.original_image)
                
                # Stage 2.5: Filtering
                bboxes, texts = self._apply_filters(bboxes, texts)
                
                # Stage 3: Merge nearby boxes and texts
                from app.core.vision_utils import merge_nearby_boxes_and_texts
                if self.ocr_config.get('merge_nearby_boxes', False):
                    merged_bboxes, merged_texts = merge_nearby_boxes_and_texts(bboxes, texts, w, h)
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
    def __init__(self, in_q: queue.Queue, translator_or_chain, src_lang: str, tgt_lang: str, log_callback=None, hitl_callback=None, skip_languages=None, filter_texts=None, no_text_lang_skip=False, max_request_length=-1):
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
        batch = []
        import queue
        
        def flush_batch():
            if not batch: return
            
            if self.chained_translators:
                # Prepare initial texts
                all_texts = []
                for ctx in batch:
                    if ctx.original_texts:
                        all_texts.extend(ctx.original_texts)
                
                if all_texts:
                    current_texts = list(all_texts)
                    
                    # Run through the chain
                    for i, (step_translator, step_tgt_lang) in enumerate(self.chained_translators):
                        if not step_translator:
                            continue
                            
                        # Build indices of texts that need translation in this step
                        indices_to_translate = []
                        texts_to_translate = []
                        
                        for idx, text in enumerate(current_texts):
                            if not self._should_skip_text(text, step_tgt_lang):
                                indices_to_translate.append(idx)
                                texts_to_translate.append(text)
                                
                        if not texts_to_translate:
                            continue # Nothing to translate in this step
                            
                        if self.log_callback:
                            self.log_callback("TRANSLATE", f"Translating batch of {len(batch)} pages ({len(texts_to_translate)} valid lines) at step {i+1} to {step_tgt_lang}...")
                        
                        try:
                            # Chunking logic based on max_request_length
                            chunks = []
                            if self.max_request_length > 0:
                                current_chunk = []
                                current_indices = []
                                current_len = 0
                                for idx, text in zip(indices_to_translate, texts_to_translate):
                                    text_len = len(text)
                                    if current_len + text_len > self.max_request_length and current_chunk:
                                        chunks.append((current_indices, current_chunk))
                                        current_chunk = []
                                        current_indices = []
                                        current_len = 0
                                    current_chunk.append(text)
                                    current_indices.append(idx)
                                    current_len += text_len
                                if current_chunk:
                                    chunks.append((current_indices, current_chunk))
                            else:
                                chunks = [(indices_to_translate, texts_to_translate)]
                                
                            for chunk_idx, (chunk_indices, chunk_texts) in enumerate(chunks):
                                if len(chunks) > 1 and self.log_callback:
                                    self.log_callback("TRANSLATE", f" -> Processing sub-batch {chunk_idx+1}/{len(chunks)} ({len(chunk_texts)} lines)...")
                                translated_part = step_translator.translate(chunk_texts, self.src_lang, step_tgt_lang)
                                # Reconstruct current_texts
                                for j, idx in enumerate(chunk_indices):
                                    if j < len(translated_part) and translated_part[j]:
                                        current_texts[idx] = translated_part[j]
                        except Exception as e:
                            if self.log_callback:
                                self.log_callback("ERROR", f"Translation Batch Error at step {i+1}: {e}")
                            
                    all_translated = current_texts
                else:
                    all_translated = []
                    
                # Split translated text back to each context
                cursor = 0
                for ctx in batch:
                    if ctx.original_texts:
                        ctx_len = len(ctx.original_texts)
                        ctx.translated_texts = all_translated[cursor:cursor+ctx_len]
                        cursor += ctx_len
                    else:
                        ctx.translated_texts = []
            else:
                # Fallback if no translator is available
                for ctx in batch:
                    ctx.translated_texts = ctx.original_texts if ctx.original_texts else []
                            
            for ctx in batch:
                ctx.trans_done.set()
                self.in_q.task_done()
                
            batch.clear()

        while True:
            try:
                ctx = self.in_q.get(timeout=0.5)
                if ctx is None:
                    flush_batch()
                    self.in_q.task_done()
                    break
                    
                batch.append(ctx)
                if len(batch) >= 15:
                    flush_batch()
            except queue.Empty:
                if batch:
                    flush_batch()


class InpaintWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, inpainter: BaseInpainter | None, log_callback=None):
        super().__init__()
        self.in_q = in_q
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

            if self.inpainter and (ctx.raw_bboxes or ctx.bboxes) and ctx.original_image is not None:
                try:
                    boxes_to_inpaint = ctx.raw_bboxes if ctx.raw_bboxes is not None else ctx.bboxes
                    if boxes_to_inpaint is not None:
                        inpainted = self.inpainter.inpaint(ctx.original_image, boxes_to_inpaint)
                        ctx.inpainted_image = inpainted
                    else:
                        ctx.inpainted_image = ctx.original_image.copy()
                except Exception as e:
                    if self.log_callback:
                        self.log_callback("ERROR", f"Inpaint Error on {ctx.page_id}: {e}")
                    ctx.inpainted_image = ctx.original_image.copy()

            ctx.inpaint_done.set()  # Signal completion of this fork
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
                bg_image = ctx.inpainted_image if ctx.inpainted_image is not None else ctx.original_image
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
                bg_image = ctx.inpainted_image if ctx.inpainted_image is not None else ctx.original_image
                ctx.rendered_image = bg_image.copy() if bg_image is not None else None

            self.out_q.put(ctx)
            self.in_q.task_done()
