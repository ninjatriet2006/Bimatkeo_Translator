import threading
import queue
import gc
from app.core.dto import PageContext
from app.core.interfaces import BaseInpainter, BaseUpscaler

try:
    import torch # type: ignore
except ImportError:
    torch = None

def release_gpu_memory():
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

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
