"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.inpainter.inpaint
- RESPONSIBILITY: Performs text removal (Inpainting) on images.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: Inpainter implementation
- IN = OUT: Receives PageContext from q_inpaint, processes and pushes to q_upscale or sets inpaint_done.
=============================================================================
"""
import threading
import queue
import gc
from app.core.shared.dto import PageContext
from app.core.shared.context_reader import get_original_image, get_inpainted_image, get_background_image
from app.core.shared.context_writer import set_original_image, set_inpainted_image
from app.core.interfaces import BaseInpainter

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
                image = get_original_image(ctx)
                    
                if image is not None:
                    try:
                        boxes_to_inpaint = ctx.raw_bboxes if ctx.raw_bboxes is not None else ctx.bboxes
                        if boxes_to_inpaint is not None:
                            inpainted = self.inpainter.inpaint(image, boxes_to_inpaint)
                            set_inpainted_image(ctx, inpainted)
                        else:
                            set_inpainted_image(ctx, image.copy())
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
