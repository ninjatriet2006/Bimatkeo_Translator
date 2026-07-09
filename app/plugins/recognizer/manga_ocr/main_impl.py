"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.manga_ocr.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Manga-OCR vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_manga_ocr_model, recognize.recognize_text_manga_ocr
- IN = OUT: Triển khai BaseTextRecognizer, đóng gói plugin Manga-OCR.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextRecognizer
from app.core.shared_registry import RecognizerFactory

from app.plugins.recognizer.manga_ocr.loader import load_manga_ocr_model
from app.plugins.recognizer.manga_ocr.recognize import recognize_text_manga_ocr

@RecognizerFactory.register("manga_ocr")
class MangaOCRRecognizerImpl(BaseTextRecognizer):
    MODELS = [
        {'key': 'manga_ocr', 'label': 'manga_ocr'},
    ]

    def __init__(self):
        self.processor = None
        self.model = None

    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.processor, self.model = load_manga_ocr_model(
            model_path=model_path, log_callback=log_callback, **kwargs
        )

    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        return recognize_text_manga_ocr(self.processor, self.model, image_crop)
