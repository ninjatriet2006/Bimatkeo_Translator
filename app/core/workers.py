import threading
import queue
import gc
from app.core.dto import PageContext
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer, BaseTranslator, BaseInpainter, BaseRenderer

try:
    import torch # type: ignore
except ImportError:
    torch = None

def release_gpu_memory():
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

class OCRWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q: queue.Queue, detector: BaseTextDetector | None, recognizer: BaseTextRecognizer | None, log_callback=None):
        super().__init__()
        self.in_q = in_q
        self.out_q = out_q
        self.detector = detector
        self.recognizer = recognizer
        self.log_callback = log_callback
        self.daemon = True

    def run(self):
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
                self.out_q.put(None)
                self.in_q.task_done()
                break
            
            if self.log_callback:
                self.log_callback("OCR", f"Processing {ctx.page_id}...")

            if self.detector and ctx.original_image is not None:
                bboxes = self.detector.detect(ctx.original_image)
                ctx.bboxes = bboxes
                
                texts = []
                if self.recognizer and bboxes:
                    for box in bboxes:
                        # box format: [x_min, y_min, x_max, y_max]
                        try:
                            crop = ctx.original_image[box[1]:box[3], box[0]:box[2]]
                            if crop.size > 0:
                                text = self.recognizer.recognize(crop)
                                texts.append(text)
                            else:
                                texts.append("")
                        except Exception as e:
                            if self.log_callback:
                                self.log_callback("ERROR", f"OCR Error on {ctx.page_id}: {e}")
                            texts.append("")
                ctx.original_texts = texts
            
            self.out_q.put(ctx)
            self.in_q.task_done()
            
            # Optional: release_gpu_memory()


class TranslatorWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q: queue.Queue, translator: BaseTranslator | None, src_lang: str, tgt_lang: str, log_callback=None):
        super().__init__()
        self.in_q = in_q
        self.out_q = out_q
        self.translator = translator
        self.src_lang = src_lang
        self.tgt_lang = tgt_lang
        self.log_callback = log_callback
        self.daemon = True

    def run(self):
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
                self.out_q.put(None)
                self.in_q.task_done()
                break
            
            if self.log_callback:
                self.log_callback("TRANSLATE", f"Translating {ctx.page_id}...")

            if self.translator and ctx.original_texts:
                try:
                    translated = self.translator.translate(ctx.original_texts, self.src_lang, self.tgt_lang)
                    ctx.translated_texts = translated
                except Exception as e:
                    if self.log_callback:
                        self.log_callback("ERROR", f"Translation Error on {ctx.page_id}: {e}")
                    ctx.translated_texts = [""] * len(ctx.original_texts)

            self.out_q.put(ctx)
            self.in_q.task_done()


class InpaintWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q: queue.Queue, inpainter: BaseInpainter | None, log_callback=None):
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
                self.out_q.put(None)
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

            self.out_q.put(ctx)
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

            self.out_q.put(ctx)
            self.in_q.task_done()
