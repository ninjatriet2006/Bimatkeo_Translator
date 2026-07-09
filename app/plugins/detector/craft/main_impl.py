"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.craft.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký CRAFT text detector vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_craft_model, detect.detect_text_craft
- IN = OUT: Triển khai BaseTextDetector, đóng gói plugin CRAFT.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextDetector
from app.core.shared_registry import DetectorFactory

from app.plugins.detector.craft.loader import load_craft_model
from app.plugins.detector.craft.detect import detect_text_craft

@DetectorFactory.register("craft")
class CRAFTDetectorImpl(BaseTextDetector):
    MODELS = [
        {'key': 'craft', 'check_file': 'models/Detector/CRAFT/craft_mlt_25k.pth'},
    ]

    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.model = load_craft_model(model_path=model_path, log_callback=log_callback, **kwargs)
        
    def detect(self, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
        return detect_text_craft(self.model, image)
