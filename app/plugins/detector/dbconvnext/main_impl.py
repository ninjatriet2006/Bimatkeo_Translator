"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.dbconvnext.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký DBConvNeXt text detector vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_dbconvnext_model, detect.detect_text_dbconvnext
- IN = OUT: Triển khai BaseTextDetector, đóng gói plugin DBConvNeXt.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextDetector
from app.core.shared_registry import DetectorFactory

from app.plugins.detector.dbconvnext.loader import load_dbconvnext_model
from app.plugins.detector.dbconvnext.detect import detect_text_dbconvnext

@DetectorFactory.register("dbconvnext")
class DBConvNeXtDetectorImpl(BaseTextDetector):
    MODELS = [
        {'key': 'dbconvnext', 'check_file': 'models/Detector/DBConvNeXt/dbnet_convnext.ckpt'},
    ]

    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.model = load_dbconvnext_model(model_path=model_path, log_callback=log_callback, **kwargs)
        
    def detect(self, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
        return detect_text_dbconvnext(self.model, image)
