"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.multimodal.felo_search.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Felo Search Provider.
- CALLED BY: app.core.shared_registry.discovery
- CALLS TO: translate.translate_felo_search
- IN = OUT: Khai báo plugin Felo Search theo chuẩn Multimodal.
=============================================================================
"""
from app.core.shared_registry import TranslatorFactory, MultimodalFactory
from app.core.translator.base_api import BaseAPITranslator
from app.core.api.interfaces import BaseMultimodal

from .translate import translate_felo_search

@MultimodalFactory.register("felo_v2")
@MultimodalFactory.register("felo_search")
@TranslatorFactory.register("felo_v2")
@TranslatorFactory.register("felo_search")
class FeloSearchProvider(BaseMultimodal, BaseAPITranslator):
    MODELS = [
        {'key': 'felo_v2', 'check_file': 'app/plugins/multimodal/felo_search/main_impl.py', 'default_endpoint': 'https://openapi.felo.ai/v2/chat', 'endpoint_inference': []},
        {'key': 'felo_search', 'check_file': 'app/plugins/multimodal/felo_search/main_impl.py', 'default_endpoint': 'https://openapi.felo.ai/v2/chat', 'endpoint_inference': []},
    ]

    def __init__(self):
        super(BaseAPITranslator, self).__init__()

    @classmethod
    def get_supported_services(cls) -> list[str]:
        return ["Translator"]

    @classmethod
    def is_multimodal(cls, model_name: str) -> bool:
        # Felo Search không hỗ trợ nhận diện ảnh (vision) qua API v2/chat
        return False

    def _call_api(self, system_prompt: str, user_text: str, images: list[str] | None = None) -> str:
        return translate_felo_search(self, system_prompt, user_text, images)

    def load_model(self, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
        self.key = api_key
        self.endpoint = endpoint or "https://openapi.felo.ai/v2/chat"
        self.model = model_name or ""
        self.timeout = kwargs.get("timeout", 30)

