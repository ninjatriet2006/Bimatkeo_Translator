"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.openai.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký các dịch giả họ OpenAI (OpenAI, DeepSeek, Groq, Custom).
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: translate.translate_openai
- IN = OUT: Khai báo các plugin theo chuẩn API của OpenAI.
=============================================================================
"""
from app.core.shared_registry import TranslatorFactory
from app.core.translator.base_api import BaseAPITranslator
from app.plugins.translator.openai.translate import translate_openai

@TranslatorFactory.register("openai")
class OpenAITranslator(BaseAPITranslator):
    MODELS = [
        {'key': 'openai', 'check_file': 'app/plugins/translator/openai/main_impl.py', 'default_endpoint': 'https://api.openai.com/v1', 'endpoint_inference': []},
        {'key': 'deepseek', 'check_file': 'app/plugins/translator/openai/main_impl.py', 'default_endpoint': 'https://api.deepseek.com', 'endpoint_inference': []},
        {'key': 'groq', 'check_file': 'app/plugins/translator/openai/main_impl.py', 'default_endpoint': 'https://api.groq.com/openai/v1', 'endpoint_inference': []},
        {'key': 'custom_openai', 'check_file': 'app/plugins/translator/openai/main_impl.py', 'endpoint_inference': []},
    ]

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        return translate_openai(self, system_prompt, user_text)

@TranslatorFactory.register("deepseek")
class DeepSeekTranslator(OpenAITranslator):
    """DeepSeek uses an API completely compatible with OpenAI."""
    pass

@TranslatorFactory.register("groq")
class GroqTranslator(OpenAITranslator):
    """Groq uses an API completely compatible with OpenAI."""
    pass

@TranslatorFactory.register("custom_openai")
class CustomOpenAITranslator(OpenAITranslator):
    """Custom OpenAI-compatible endpoints."""
    pass
