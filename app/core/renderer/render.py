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
import threading
import queue
from app.core.shared_context.dto import PageContext
from app.core.shared_context.context_reader import get_original_image, get_inpainted_image, get_background_image
from app.core.interfaces import BaseRenderer

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
                bg_image = get_background_image(ctx)
                        
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
                bg_image = get_background_image(ctx)
                ctx.rendered_image = bg_image.copy() if bg_image is not None else None

            self.out_q.put(ctx)
            self.in_q.task_done()
