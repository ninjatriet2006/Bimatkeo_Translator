from app.core.factories import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("deepl")
class DeepLTranslator(BaseAPITranslator):
    @classmethod
    def get_supported_languages(cls) -> dict:
        return {'__any__': '__all__'}

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        if self.log_callback:
            self.log_callback("WARNING", "DeepL translation schema is not yet implemented.")
        return ""
