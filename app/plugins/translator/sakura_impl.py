from app.core.factories import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("sakura")
class SakuraTranslator(BaseAPITranslator):
    @classmethod
    def get_supported_languages(cls) -> dict:
        return {
            "JPN": ["CHS", "CHT"],
            "CHS": ["JPN"],
            "CHT": ["JPN"]
        }

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        if self.log_callback:
            self.log_callback("WARNING", "Sakura translation schema is not yet implemented.")
        return ""
