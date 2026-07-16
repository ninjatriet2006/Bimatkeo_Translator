"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.multimodal.openai.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký OpenAI Provider (hỗ trợ Text và Vision).
- CALLED BY: app.core.shared_registry.discovery
- CALLS TO: translate.translate_openai
- IN = OUT: Khai báo plugin OpenAI theo chuẩn Multimodal.
=============================================================================
"""
from app.core.shared_registry import TranslatorFactory, CloudOCRFactory, MultimodalFactory
from app.core.translator.base_api import BaseAPITranslator
from app.core.ocr.interfaces import BaseCloudOCR
from app.core.api.interfaces import BaseMultimodal

from .translate import translate_openai

@MultimodalFactory.register("openai")
@MultimodalFactory.register("felo_search")
@TranslatorFactory.register("openai")
@TranslatorFactory.register("felo_search")
@CloudOCRFactory.register("openai")
@CloudOCRFactory.register("felo_search")
class OpenAIProvider(BaseMultimodal, BaseAPITranslator, BaseCloudOCR):
    MODELS = [
        {'key': 'openai', 'check_file': 'app/plugins/multimodal/openai/main_impl.py', 'default_endpoint': 'https://api.openai.com/v1', 'endpoint_inference': []},
        {'key': 'deepseek', 'check_file': 'app/plugins/multimodal/openai/main_impl.py', 'default_endpoint': 'https://api.deepseek.com', 'endpoint_inference': []},
        {'key': 'groq', 'check_file': 'app/plugins/multimodal/openai/main_impl.py', 'default_endpoint': 'https://api.groq.com/openai/v1', 'endpoint_inference': []},
        {'key': 'custom_openai', 'check_file': 'app/plugins/multimodal/openai/main_impl.py', 'endpoint_inference': []},
        {'key': 'felo', 'check_file': 'app/plugins/multimodal/openai/main_impl.py', 'default_endpoint': 'https://openapi.felo.ai/v1', 'endpoint_inference': [], 'static_models': ['felo-search']},
        {'key': 'felo_search', 'check_file': 'app/plugins/multimodal/openai/main_impl.py', 'default_endpoint': 'https://openapi.felo.ai/v1', 'endpoint_inference': [], 'static_models': ['felo-search']},
    ]

    def __init__(self):
        BaseAPITranslator.__init__(self)

    @classmethod
    def get_supported_services(cls) -> list[str]:
        return ["Translator", "CloudOCR"]

    @classmethod
    def is_multimodal(cls, model_name: str) -> bool:
        name_lower = model_name.lower()
        if "gpt-4o" in name_lower or "vision" in name_lower or "claude-3" in name_lower or "vl" in name_lower or "pixtral" in name_lower:
            return True
        return False

    def _call_api(self, system_prompt: str, user_text: str, images: list[str] | None = None) -> str:
        return translate_openai(self, system_prompt, user_text, images)

    def load_model(self, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
        self.key = api_key
        self.endpoint = endpoint or ""
        self.model = model_name or ""
        self.timeout = kwargs.get("timeout", 10)

    def recognize_full_page(self, image, lang: str = "en") -> list[dict]:
        raise NotImplementedError("OCR using OpenAI is not yet implemented for image crop scanning, but available via API.")

@MultimodalFactory.register("deepseek")
@TranslatorFactory.register("deepseek")
class DeepSeekProvider(OpenAIProvider):
    """DeepSeek uses an API completely compatible with OpenAI."""
    @classmethod
    def get_supported_services(cls) -> list[str]:
        return ["Translator"] # Deepseek currently does not support vision commonly

@MultimodalFactory.register("groq")
@TranslatorFactory.register("groq")
class GroqProvider(OpenAIProvider):
    """Groq uses an API completely compatible with OpenAI."""
    @classmethod
    def get_supported_services(cls) -> list[str]:
        return ["Translator", "CloudOCR"]

@MultimodalFactory.register("custom_openai")
@TranslatorFactory.register("custom_openai")
@CloudOCRFactory.register("custom_openai")
class CustomOpenAIProvider(OpenAIProvider):
    """Custom OpenAI-compatible endpoints."""
    pass

@MultimodalFactory.register("felo")
@TranslatorFactory.register("felo")
class FeloProvider(OpenAIProvider):
    """Felo API wrapper."""
    @classmethod
    def get_supported_services(cls) -> list[str]:
        return ["Translator"] # Felo API doesn't officially support multimodal vision/OCR

