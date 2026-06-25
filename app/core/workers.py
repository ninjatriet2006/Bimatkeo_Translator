import threading
import queue
import gc
from app.core.dto import PageContext
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer, BaseTranslator, BaseInpainter, BaseRenderer, BaseCloudOCR
from app.core.vision_utils import sort_comic_text_boxes
from app.core.ocr_corrector import VisionOCRCorrector

try:
    import torch # type: ignore
except ImportError:
    torch = None

def release_gpu_memory():
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

class OCRWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q_trans: queue.Queue, out_q_inpaint: queue.Queue, out_q_render: queue.Queue, detector: BaseTextDetector | None, recognizer: BaseTextRecognizer | None, log_callback=None, cloud_ocr: BaseCloudOCR | None = None):
        super().__init__()
        self.in_q = in_q
        self.out_q_trans = out_q_trans
        self.out_q_inpaint = out_q_inpaint
        self.out_q_render = out_q_render
        self.detector = detector
        self.recognizer = recognizer
        self.cloud_ocr = cloud_ocr
        self.log_callback = log_callback
        self.corrector = VisionOCRCorrector(use_llm=True, log_callback=log_callback)
        self.daemon = True

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
                sorted_bboxes = sort_comic_text_boxes(raw_bboxes, direction="rtl_ttb", image_width=w, image_height=h)
                
                # Map sorted boxes to text
                box_to_text = {tuple(r["box"]): r["text"] for r in results}
                
                ctx.bboxes = sorted_bboxes
                ctx.original_texts = [box_to_text[tuple(b)] for b in sorted_bboxes]
                ctx.translated_texts = [""] * len(ctx.original_texts)
                
                if self.log_callback:
                    self.log_callback("OCR", f"Cloud OCR đã xử lý {len(ctx.bboxes)} bong bóng chữ.")

            elif self.detector and ctx.original_image is not None:
                h, w = ctx.original_image.shape[:2]
                raw_bboxes = self.detector.detect(ctx.original_image)
                # Sắp xếp lại box theo chuẩn đọc truyện. 
                # (TODO: Đọc direction từ config_dict, tạm thời gán cứng rtl_ttb)
                bboxes = sort_comic_text_boxes(raw_bboxes, direction="rtl_ttb", image_width=w, image_height=h)
                ctx.bboxes = bboxes
                
                texts = []
                if self.recognizer and bboxes:
                    for box in bboxes:
                        # box format: [x_min, y_min, x_max, y_max]
                        try:
                            crop = ctx.original_image[box[1]:box[3], box[0]:box[2]]
                            if crop.size > 0:
                                text = self.recognizer.recognize(crop)
                            else:
                                text = ""
                        except Exception as e:
                            if self.log_callback:
                                self.log_callback("ERROR", f"OCR Error on {ctx.page_id}: {e}")
                            text = ""
                        texts.append(text)
                            
                # Stage 2: Vision OCR Correction
                texts = self.corrector.correct(texts, ctx.original_image)
                ctx.original_texts = texts
                ctx.translated_texts = [""] * len(texts)
                
                if self.log_callback:
                    self.log_callback("OCR", f"Detector tìm thấy {len(bboxes)} bong bóng chữ.")
            
            # Fork (Push to 3 queues simultaneously)
            self.out_q_trans.put(ctx)
            self.out_q_inpaint.put(ctx)
            self.out_q_render.put(ctx)
            self.in_q.task_done()
            
            # Optional: release_gpu_memory()


class TranslatorWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, translator: BaseTranslator | None, src_lang: str, tgt_lang: str, log_callback=None, hitl_callback=None):
        super().__init__()
        self.in_q = in_q
        self.translator = translator
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.log_callback = log_callback
        self.daemon = True

    def run(self):
        batch = []
        import queue
        
        def flush_batch():
            if not batch: return
            
            if self.translator:
                all_texts = []
                for ctx in batch:
                    if ctx.original_texts:
                        all_texts.extend(ctx.original_texts)
                
                if all_texts:
                    if self.log_callback:
                        self.log_callback("TRANSLATE", f"Translating batch of {len(batch)} pages ({len(all_texts)} lines)...")
                    try:
                        all_translated = self.translator.translate(all_texts, self.src_lang, self.tgt_lang)
                    except Exception as e:
                        if self.log_callback:
                            self.log_callback("ERROR", f"Translation Batch Error: {e}")
                        all_translated = [""] * len(all_texts)
                        
                    # Split translated text back to each context
                    cursor = 0
                    for ctx in batch:
                        if ctx.original_texts:
                            ctx_len = len(ctx.original_texts)
                            ctx.translated_texts = all_translated[cursor:cursor+ctx_len]
                            cursor += ctx_len
                        else:
                            ctx.translated_texts = []
                            
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

            if self.inpainter and ctx.bboxes and ctx.original_image is not None:
                try:
                    inpainted = self.inpainter.inpaint(ctx.original_image, ctx.bboxes)
                    ctx.inpainted_image = inpainted
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
