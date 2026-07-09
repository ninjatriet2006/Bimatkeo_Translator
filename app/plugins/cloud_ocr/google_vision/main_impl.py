"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.cloud_ocr.google_vision.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Google Vision OCR vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_google_vision, recognize.recognize_google_vision
- IN = OUT: Khai báo plugin Google Vision theo chuẩn BaseCloudOCR.
=============================================================================
"""
import numpy as np

from app.core.ocr.interfaces import BaseCloudOCR
from app.core.shared_registry import CloudOCRFactory
from app.plugins.cloud_ocr.google_vision.loader import load_google_vision
from app.plugins.cloud_ocr.google_vision.recognize import recognize_google_vision

@CloudOCRFactory.register("google_ocr")
class GoogleVisionImpl(BaseCloudOCR):
    MODELS = [
        {'key': 'google_ocr', 'check_file': 'none', 'default_endpoint': 'https://vision.googleapis.com/v1/images:annotate'},
    ]

    def __init__(self):
        self.api_key = ""
        self.log_callback = None

    def load_model(self, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
        load_google_vision(self, api_key, endpoint, model_name, **kwargs)

    def recognize_full_page(self, image: np.ndarray, lang: str = "en") -> list[dict]:
        return recognize_google_vision(self, image, lang)
