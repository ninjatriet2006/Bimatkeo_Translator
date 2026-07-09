"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.manager
- RESPONSIBILITY: Acts as Facade (Delegator) coordinating the text recognition process.
- CALLED BY: app.core.ocr.worker
- CALLS TO: app.core.ocr.cloud_runner, app.core.ocr.local_runner
- IN = OUT: Receives PageContext -> calls corresponding Runner -> completes process.
=============================================================================
"""

from app.core.shared.dto import PageContext
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer, BaseCloudOCR
from app.core.ocr.corrector import OfflineOCRCorrector
from app.core.ocr.cloud_runner import CloudOCRRunner
from app.core.ocr.local_runner import LocalOCRRunner

class OCRProcessor:
    cloud_runner: CloudOCRRunner | None
    local_runner: LocalOCRRunner | None

    def __init__(self, detector: BaseTextDetector | None, recognizer: BaseTextRecognizer | None, cloud_ocr: BaseCloudOCR | None = None, ocr_config: dict | None = None, render_config: dict | None = None, log_callback=None):
        self.ocr_config = ocr_config or {}
        self.render_config = render_config or {}
        self.log_callback = log_callback
        
        self.cloud_ocr = cloud_ocr
        if self.cloud_ocr:
            self.cloud_runner = CloudOCRRunner(self.cloud_ocr, self.ocr_config, self.render_config, self.log_callback)
        else:
            self.cloud_runner = None
            
        self.detector = detector
        self.recognizer = recognizer
        if self.detector:
            self.corrector = OfflineOCRCorrector(log_callback=log_callback)
            self.local_runner = LocalOCRRunner(self.detector, self.recognizer, self.ocr_config, self.render_config, self.corrector, self.log_callback)
        else:
            self.local_runner = None

    def process_page(self, ctx: PageContext):
        """Thực thi luồng OCR cho 1 trang (PageContext) thông qua Runner tương ứng."""
        if self.log_callback:
            self.log_callback("OCR", f"Processing {ctx.page_id}...")

        if self.cloud_runner is not None:
            self.cloud_runner.run(ctx)
        elif self.local_runner is not None:
            self.local_runner.run(ctx)
