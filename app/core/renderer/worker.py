import threading
import queue
from app.core.dto import PageContext
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
                bg_image = ctx.get_background_image()
                        
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
                bg_image = ctx.get_background_image()
                ctx.rendered_image = bg_image.copy() if bg_image is not None else None

            self.out_q.put(ctx)
            self.in_q.task_done()
