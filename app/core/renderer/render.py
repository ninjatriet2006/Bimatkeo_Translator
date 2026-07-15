"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.renderer.render
- RESPONSIBILITY: Renders translated text onto the image (after inpaint).
- CALLED BY: app.core.pipeline.manager
- CALLS TO: Renderer implementation
- IN = OUT: Waits for trans_done and inpaint_done signals, then renders and pushes to q_out.
=============================================================================
"""
import multiprocessing
import queue
from app.core.shared_context.dto import PageContext
from app.core.shared_context.utils import get_original_image, get_inpainted_image, get_background_image

class RenderWorker(multiprocessing.Process):
    def __init__(self, q_trans_done: multiprocessing.Queue, q_inpaint_done: multiprocessing.Queue, out_q: multiprocessing.Queue, config_dict: dict, log_queue: multiprocessing.Queue):
        super().__init__()
        self.q_trans_done = q_trans_done
        self.q_inpaint_done = q_inpaint_done
        self.out_q = out_q
        self.config_dict = config_dict
        self.log_queue = log_queue
        self.daemon = True

    def run(self):
        def _log(level, msg):
            self.log_queue.put((level, msg))
            
        _log("INFO", "Render Worker Process Started.")
        
        from app.core.renderer.initializer import RendererInitializer
        self.renderer = RendererInitializer.initialize(self.config_dict, _log)
        self.log_callback = _log
        
        trans_buffer = {}
        inpaint_buffer = {}
        trans_finished = False
        inpaint_finished = False
        
        import time
        import queue
        
        while True:
            # Poll Translation
            if not trans_finished:
                try:
                    t_ctx = self.q_trans_done.get(block=False)
                    if t_ctx is None:
                        trans_finished = True
                    else:
                        trans_buffer[t_ctx.page_id] = t_ctx
                except queue.Empty:
                    pass
                    
            # Poll Inpainting
            if not inpaint_finished:
                try:
                    i_ctx = self.q_inpaint_done.get(block=False)
                    if i_ctx is None:
                        inpaint_finished = True
                    else:
                        inpaint_buffer[i_ctx.page_id] = i_ctx
                except queue.Empty:
                    pass
            
            # Find matches
            ready_ids = [pid for pid in trans_buffer if pid in inpaint_buffer]
            
            for pid in ready_ids:
                t_ctx = trans_buffer.pop(pid)
                i_ctx = inpaint_buffer.pop(pid)
                
                # Merge Data
                merged_ctx = i_ctx # Base it off inpaint since it has the final image array
                merged_ctx.translated_texts = t_ctx.translated_texts
                
                if self.log_callback:
                    self.log_callback("RENDER", f"Rendering {merged_ctx.page_id}...")

                if self.renderer:
                    bg_image = get_background_image(merged_ctx)
                            
                    texts = merged_ctx.translated_texts if merged_ctx.translated_texts else merged_ctx.original_texts
                    
                    if bg_image is not None and texts and merged_ctx.bboxes:
                        try:
                            rendered = self.renderer.render(bg_image, merged_ctx.bboxes, texts)
                            merged_ctx.rendered_image = rendered
                        except Exception as e:
                            if self.log_callback:
                                self.log_callback("ERROR", f"Render Error on {merged_ctx.page_id}: {e}")
                            merged_ctx.rendered_image = bg_image.copy()
                    else:
                        merged_ctx.rendered_image = bg_image.copy() if bg_image is not None else None
                else:
                    bg_image = get_background_image(merged_ctx)
                    merged_ctx.rendered_image = bg_image.copy() if bg_image is not None else None

                self.out_q.put(merged_ctx)

            if trans_finished and inpaint_finished and not trans_buffer and not inpaint_buffer:
                self.out_q.put(None)
                break
                
            time.sleep(0.05)
