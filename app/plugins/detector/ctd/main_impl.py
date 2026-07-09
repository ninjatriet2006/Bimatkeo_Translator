"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.ctd.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký CTD text detector vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_ctd_model, detect.detect_text_ctd
- IN = OUT: Triển khai BaseTextDetector, đóng gói plugin CTD.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextDetector
from app.core.shared_registry import DetectorFactory

from app.plugins.detector.ctd.loader import load_ctd_model
from app.plugins.detector.ctd.detect import detect_text_ctd

@DetectorFactory.register("ctd")
class CTDetectorImpl(BaseTextDetector):
    MODELS = [
        {'key': 'ctd', 'label': 'ctd'},
    ]

    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.model = load_ctd_model(model_path=model_path, log_callback=log_callback, **kwargs)
        
    def detect(self, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
        return detect_text_ctd(self.model, image)
