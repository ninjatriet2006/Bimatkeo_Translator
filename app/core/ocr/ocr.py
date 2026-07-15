"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.ocr
- RESPONSIBILITY: Brain of OCR processing (Detector, Recognizer), creates PageContext and pushes to queues.
- CALLED BY: app.core.pipeline.executor
- CALLS TO: app.core.ocr.processor (OCRProcessor)
- IN = OUT: Receives from q_in, creates PageContext and forks to q_trans, q_inpaint, q_render.
=============================================================================
"""
import multiprocessing
import queue

from app.core.shared_context.dto import PageContext
from app.core.ocr.processor import OCRProcessor

class OCRWorker(multiprocessing.Process):
    def __init__(self, in_q: multiprocessing.Queue, out_q_trans: multiprocessing.Queue, 
                 out_q_inpaint: multiprocessing.Queue, config_dict: dict, log_queue: multiprocessing.Queue):
        super().__init__()
        self.in_q = in_q
        self.out_q_trans = out_q_trans
        self.out_q_inpaint = out_q_inpaint
        self.config_dict = config_dict
        self.log_queue = log_queue
        self.daemon = True

    def run(self):
        def _log(level, msg):
            self.log_queue.put((level, msg))
            
        _log("INFO", "OCR Worker Process Started.")
        
        # Initialize models INSIDE the new process
        from app.core.ocr.initializer import OCRInitializer
        cloud_ocr, detector, recognizer = OCRInitializer.initialize(self.config_dict, _log)
        
        self.processor = OCRProcessor(
            detector=detector,
            recognizer=recognizer,
            cloud_ocr=cloud_ocr,
            ocr_config=self.config_dict.get("ocr", {}),
            render_config=self.config_dict.get("render", {}),
            log_callback=_log
        )
        
        while True:
            ctx: PageContext = self.in_q.get()
            if ctx is None:
                self.out_q_trans.put(None)
                self.out_q_inpaint.put(None)
                break
            
            try:
                self.processor.process_page(ctx)
            except Exception as e:
                _log("ERROR", f"Lỗi không xác định trong OCR Processor tại trang {ctx.page_id}: {e}")
            
            # Fork (Push to 2 queues simultaneously)
            self.out_q_trans.put(ctx)
            self.out_q_inpaint.put(ctx)
