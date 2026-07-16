"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.multimodal.gemini.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Gemini Provider (hỗ trợ Text và Vision).
- CALLED BY: app.core.shared_registry.discovery
- CALLS TO: translate.translate_gemini, recognize.recognize_gemini_vision
- IN = OUT: Khai báo plugin Gemini theo chuẩn Multimodal.
=============================================================================
"""
import numpy as np

from app.core.shared_registry import TranslatorFactory, CloudOCRFactory, MultimodalFactory
from app.core.translator.base_api import BaseAPITranslator
from app.core.ocr.interfaces import BaseCloudOCR
from app.core.api.interfaces import BaseMultimodal

from .translate import translate_gemini
from .recognize import recognize_gemini_vision
from .loader import load_gemini_vision

@MultimodalFactory.register("gemini")
@TranslatorFactory.register("gemini")
@CloudOCRFactory.register("gemini")
class GeminiProvider(BaseMultimodal, BaseAPITranslator, BaseCloudOCR):
    MODELS = [
        {'key': 'gemini', 'check_file': 'app/plugins/multimodal/gemini/main_impl.py', 'default_endpoint': 'https://generativelanguage.googleapis.com', 'endpoint_inference': ['generativelanguage']},
    ]

    def __init__(self):
        # Khởi tạo properties cho Translator
        BaseAPITranslator.__init__(self)
        # Khởi tạo properties cho OCR
        self.api_key = ""
        self.log_callback = None

    @classmethod
    def get_supported_services(cls) -> list[str]:
        return ["Translator", "CloudOCR"]

    @classmethod
    def is_multimodal(cls, model_name: str) -> bool:
        name_lower = model_name.lower()
        if "vision" in name_lower or "1.5" in name_lower or "2.0" in name_lower or "pro" in name_lower:
            return True
        return False

    def _call_api(self, system_prompt: str, user_text: str, images: list[str] | None = None) -> str:
        return translate_gemini(self, system_prompt, user_text, images)

    def load_model(self, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
        load_gemini_vision(self, api_key, endpoint, model_name, **kwargs)

    def recognize_full_page(self, image: np.ndarray, lang: str = "en") -> list[dict]:
        return recognize_gemini_vision(self, image, lang)
