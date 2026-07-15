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

class InpaintWorker(multiprocessing.Process):
    def __init__(self, in_q: multiprocessing.Queue, config_dict: dict, log_queue: multiprocessing.Queue, out_q: multiprocessing.Queue | None = None):
        super().__init__()
        self.in_q = in_q
        self.out_q = out_q
        self.config_dict = config_dict
        self.log_queue = log_queue
        self.daemon = True

    def run(self):
        def _log(level, msg):
            self.log_queue.put((level, msg))
            
        _log("INFO", "Inpaint Worker Process Started.")
        
        # Initialize models INSIDE the new process
        from app.core.inpainter.initializer import InpainterInitializer
        inpainter, _, _, _ = InpainterInitializer.initialize(self.config_dict, _log)
        self.inpainter = inpainter
        self.log_callback = _log
        
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
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
                
            release_gpu_memory()
