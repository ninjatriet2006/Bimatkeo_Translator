"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.gemini.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Gemini Translator vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: translate.translate_gemini
- IN = OUT: Khai báo plugin Gemini theo chuẩn BaseAPITranslator.
=============================================================================
"""
from app.core.shared_registry import TranslatorFactory
from app.core.translator.base_api import BaseAPITranslator
from app.plugins.translator.gemini.translate import translate_gemini

@TranslatorFactory.register("gemini")
class GeminiTranslator(BaseAPITranslator):
    MODELS = [
        {'key': 'gemini', 'check_file': 'app/plugins/translator/gemini/main_impl.py', 'default_endpoint': 'https://generativelanguage.googleapis.com', 'endpoint_inference': ['generativelanguage']},
    ]

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        return translate_gemini(self, system_prompt, user_text)
