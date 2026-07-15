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
import multiprocessing
import queue
import gc
from app.core.shared_context.dto import PageContext
from app.core.shared_context.utils import get_original_image, get_inpainted_image, get_background_image, set_original_image, set_inpainted_image

try:
    import torch # type: ignore
except ImportError:
    torch = None

def release_gpu_memory():
    if torch is not None and torch.cuda.is_available():
        torch.cuda.empty_cache()
    gc.collect()

class UpscalerWorker(multiprocessing.Process):
    def __init__(self, in_q: multiprocessing.Queue, out_q: multiprocessing.Queue, config_dict: dict, log_queue: multiprocessing.Queue):
        super().__init__()
        self.in_q = in_q
        self.out_q = out_q
        self.config_dict = config_dict
        self.log_queue = log_queue
        
        self.ratio = config_dict.get("inpainter", {}).get("upscale_ratio", 2)
        self.daemon = True

    def run(self):
        def _log(level, msg):
            self.log_queue.put((level, msg))
            
        _log("INFO", "Upscale Worker Process Started.")
        
        from app.core.inpainter.initializer import InpainterInitializer
        _, upscaler, _, _ = InpainterInitializer.initialize(self.config_dict, _log)
        self.upscaler = upscaler
        self.log_callback = _log
        
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
                break
                
            if self.log_callback:
                self.log_callback("UPSCALE", f"Upscaling {ctx.page_id} by {self.ratio}x...")

            if self.upscaler and self.ratio > 1:
                try:
                    # Resolve background image (either inpainted or original)
                    bg_image = get_background_image(ctx)
                            
                    if bg_image is not None:
                        upscaled = self.upscaler.upscale(bg_image, self.ratio)
                        set_inpainted_image(ctx, upscaled)
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

            if self.out_q:
                self.out_q.put(ctx)
            release_gpu_memory()
