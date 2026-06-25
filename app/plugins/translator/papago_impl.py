from app.core.factories import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("papago")
class PapagoTranslator(BaseAPITranslator):
    @classmethod
    def get_supported_languages(cls) -> dict:
        return {
            "KOR": ["ENG", "JPN", "CHS", "CHT", "FRA", "DEU", "RUS", "ESP", "ITA", "VIE", "THA", "IND"],
            "JPN": ["ENG", "KOR", "CHS", "CHT"],
            "CHS": ["ENG", "KOR", "JPN"],
            "CHT": ["ENG", "KOR", "JPN"],
            "ENG": ["KOR", "JPN", "CHS", "CHT", "FRA", "DEU", "ESP", "ITA"],
            "FRA": ["ENG", "KOR"],
            "ESP": ["ENG", "KOR"],
            "ITA": ["ENG", "KOR"],
            "DEU": ["ENG", "KOR"]
        }

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        if self.log_callback:
            self.log_callback("WARNING", "Papago translation schema is not yet implemented.")
        return ""
