"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.multimodal.anthropic.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Anthropic Provider (hỗ trợ Text và Vision).
- CALLED BY: app.core.shared_registry.discovery
- CALLS TO: translate.translate_anthropic
- IN = OUT: Khai báo plugin Anthropic theo chuẩn Multimodal.
=============================================================================
"""
from app.core.shared_registry import TranslatorFactory, MultimodalFactory
from app.core.translator.base_api import BaseAPITranslator
from app.core.api.interfaces import BaseMultimodal

from .translate import translate_anthropic

@MultimodalFactory.register("anthropic")
@MultimodalFactory.register("custom_anthropic")
@TranslatorFactory.register("anthropic")
@TranslatorFactory.register("custom_anthropic")
class AnthropicProvider(BaseMultimodal, BaseAPITranslator):
    MODELS = [
        {'key': 'anthropic', 'check_file': 'app/plugins/multimodal/anthropic/main_impl.py', 'default_endpoint': 'https://api.anthropic.com', 'endpoint_inference': []},
        {'key': 'custom_anthropic', 'check_file': 'app/plugins/multimodal/anthropic/main_impl.py', 'endpoint_inference': []},
    ]

    def __init__(self):
        super(BaseAPITranslator, self).__init__()

    @classmethod
    def get_supported_services(cls) -> list[str]:
        return ["Translator"]

    @classmethod
    def is_multimodal(cls, model_name: str) -> bool:
        name_lower = model_name.lower()
        if "claude-3" in name_lower or "sonnet" in name_lower or "opus" in name_lower or "haiku" in name_lower:
            return True
        return False

    def _call_api(self, system_prompt: str, user_text: str, images: list[str] | None = None) -> str:
        return translate_anthropic(self, system_prompt, user_text, images)

    def load_model(self, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
        self.key = api_key
        self.endpoint = endpoint or ""
        self.model = model_name or "claude-3-5-sonnet-20241022"
        self.timeout = kwargs.get("timeout", 10)
