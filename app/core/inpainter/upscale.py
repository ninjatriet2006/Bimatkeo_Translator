"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.inpainter.upscale
- RESPONSIBILITY: Performs background upscaling after inpainting is complete.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: Upscaler implementation
- IN = OUT: Receives PageContext from q_upscale, processes and calls inpaint_done.set().
=============================================================================
"""
import threading
import queue
import gc
from app.core.dto import PageContext
from app.core.interfaces import BaseUpscaler

try:
    import torch # type: ignore
except ImportError:
    torch = None

def release_gpu_memory():
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

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
