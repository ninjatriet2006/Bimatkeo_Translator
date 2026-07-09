"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.tesseract.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký các biến thể Tesseract vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_tesseract_model, recognize.recognize_text_tesseract
- IN = OUT: Triển khai BaseTextRecognizer, đóng gói plugin Tesseract đa ngôn ngữ.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextRecognizer
from app.core.shared_registry import RecognizerFactory

from app.plugins.recognizer.tesseract.loader import load_tesseract_model
from app.plugins.recognizer.tesseract.recognize import recognize_text_tesseract

def create_tesseract_class(lang_code: str):
    """Factory method to dynamically generate a Tesseract Recognizer class for a specific language code."""
    class TesseractRecognizerImpl(BaseTextRecognizer):
        def __init__(self):
            self.lang_code = lang_code
            self.is_ready = False

        def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
            self.is_ready = load_tesseract_model(self.lang_code, log_callback=log_callback, **kwargs)

        def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
            return recognize_text_tesseract(self.is_ready, self.lang_code, image_crop)
                
    return TesseractRecognizerImpl

langs = [
    "jpn", "jpn_vert", 
    "chi_sim", "chi_sim_vert", 
    "chi_tra", "chi_tra_vert", 
    "kor", "kor_vert", 
    "eng", 
    "mixed",
    "all_horizontal",
    "all_vertical"
]

for lang in langs:
    RecognizerFactory.register(f"tesseract_{lang}")(create_tesseract_class(lang))
