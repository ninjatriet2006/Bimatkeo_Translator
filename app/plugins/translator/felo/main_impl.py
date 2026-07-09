"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.felo.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Felo Translator vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: translate.translate_felo
- IN = OUT: Khai báo plugin Felo theo chuẩn BaseAPITranslator.
=============================================================================
"""
from app.core.shared_registry import TranslatorFactory
from app.core.translator.base_api import BaseAPITranslator
from app.plugins.translator.felo.translate import translate_felo

@TranslatorFactory.register("felo")
class FeloTranslator(BaseAPITranslator):
    MODELS = [
        {'key': 'felo', 'check_file': 'app/plugins/translator/felo/main_impl.py', 'default_endpoint': 'https://api.felo.ai/v1', 'endpoint_inference': ['felo.ai']},
    ]

    def __init__(self):
        super().__init__()
        self.max_query_len = 2000

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        return translate_felo(self, system_prompt, user_text)
