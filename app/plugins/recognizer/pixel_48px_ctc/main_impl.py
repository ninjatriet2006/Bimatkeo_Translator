"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.pixel_48px_ctc.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Pixel 48px CTC vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_pixel_48px_ctc_model, recognize.recognize_text_pixel_48px_ctc
- IN = OUT: Triển khai BaseTextRecognizer, đóng gói plugin Pixel 48px CTC.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextRecognizer
from app.core.shared_registry import RecognizerFactory

from app.plugins.recognizer.pixel_48px_ctc.loader import load_pixel_48px_ctc_model
from app.plugins.recognizer.pixel_48px_ctc.recognize import recognize_text_pixel_48px_ctc

@RecognizerFactory.register("48px_ctc")
class Pixel48pxCTCRecognizerImpl(BaseTextRecognizer):
    MODELS = [
        {'key': '48px_ctc', 'check_file': 'models/OCR/48px_ctc/mit48pxctc_ocr.onnx', 'source': 'hf://banned404/mit48pxctc-ocr-onnx'},
    ]

    def __init__(self):
        self.session = None
        self.input_name = None
        self.character_dict = []
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.session, self.input_name, self.character_dict = load_pixel_48px_ctc_model(
            model_path=model_path, log_callback=log_callback, **kwargs
        )

    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        return recognize_text_pixel_48px_ctc(self.session, self.input_name, self.character_dict, image_crop)
