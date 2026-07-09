"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.ocr
- RESPONSIBILITY: Brain of OCR processing (Detector, Recognizer), creates PageContext and pushes to queues.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.ocr.manager (OCRProcessor)
- IN = OUT: Receives from q_in, creates PageContext and forks to q_trans, q_inpaint, q_render.
=============================================================================
"""
import threading
import queue
from app.core.dto import PageContext
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer, BaseCloudOCR
from app.core.ocr.manager import OCRProcessor

class OCRWorker(threading.Thread):
    def __init__(self, in_q: queue.Queue, out_q_trans: queue.Queue, out_q_inpaint: queue.Queue, out_q_render: queue.Queue, detector: BaseTextDetector | None, recognizer: BaseTextRecognizer | None, log_callback=None, cloud_ocr: BaseCloudOCR | None = None, ocr_config: dict | None = None, render_config: dict | None = None):
        super().__init__()
        self.in_q = in_q
        self.out_q_trans = out_q_trans
        self.out_q_inpaint = out_q_inpaint
        self.out_q_render = out_q_render
        self.processor = OCRProcessor(
            detector=detector,
            recognizer=recognizer,
            cloud_ocr=cloud_ocr,
            ocr_config=ocr_config,
            render_config=render_config,
            log_callback=log_callback
        )
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
            
            try:
                self.processor.process_page(ctx)
            except Exception as e:
                if self.processor.log_callback:
                    self.processor.log_callback("ERROR", f"Lỗi không xác định trong OCR Processor tại trang {ctx.page_id}: {e}")
            
            # Fork (Push to 3 queues simultaneously)
            self.out_q_trans.put(ctx)
            self.out_q_inpaint.put(ctx)
            self.out_q_render.put(ctx)
            self.in_q.task_done()
