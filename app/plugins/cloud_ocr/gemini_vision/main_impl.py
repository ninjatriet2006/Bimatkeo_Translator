"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.cloud_ocr.gemini_vision.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Gemini Vision OCR vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_gemini_vision, recognize.recognize_gemini_vision
- IN = OUT: Khai báo plugin Gemini Vision theo chuẩn BaseCloudOCR.
=============================================================================
"""
import numpy as np

from app.core.ocr.interfaces import BaseCloudOCR
from app.core.shared_registry import CloudOCRFactory
from app.plugins.cloud_ocr.gemini_vision.loader import load_gemini_vision
from app.plugins.cloud_ocr.gemini_vision.recognize import recognize_gemini_vision

@CloudOCRFactory.register("gemini_ocr")
class GeminiVisionImpl(BaseCloudOCR):
    MODELS = [
        {'key': 'gemini_ocr', 'check_file': 'none', 'default_endpoint': 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'},
    ]

    def __init__(self):
        self.api_key = ""
        self.log_callback = None

    def load_model(self, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
        load_gemini_vision(self, api_key, endpoint, model_name, **kwargs)

    def recognize_full_page(self, image: np.ndarray, lang: str = "en") -> list[dict]:
        return recognize_gemini_vision(self, image, lang)
