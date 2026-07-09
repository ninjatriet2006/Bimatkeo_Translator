"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.pixel_48px.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Pixel 48px vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_pixel_48px_model, recognize.recognize_text_pixel_48px
- IN = OUT: Triển khai BaseTextRecognizer, đóng gói plugin Pixel 48px.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextRecognizer
from app.core.shared_registry import RecognizerFactory

from app.plugins.recognizer.pixel_48px.loader import load_pixel_48px_model
from app.plugins.recognizer.pixel_48px.recognize import recognize_text_pixel_48px

@RecognizerFactory.register("48px")
class Pixel48pxRecognizerImpl(BaseTextRecognizer):
    MODELS = [
        {'key': '48px', 'check_file': 'models/OCR/48px/ocr_ar_48px.ckpt'},
    ]

    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.model = load_pixel_48px_model(model_path=model_path, log_callback=log_callback, **kwargs)
        
    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        return recognize_text_pixel_48px(self.model, image_crop)
