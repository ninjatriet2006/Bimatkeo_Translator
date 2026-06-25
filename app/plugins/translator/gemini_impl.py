from app.core.factories import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("gemini")
class GeminiTranslator(BaseAPITranslator):
    def _call_api(self, system_prompt: str, user_text: str) -> str:
        headers = {
            "Content-Type": "application/json"
        }
        data = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [{
                "parts": [{"text": user_text}]
            }],
            "generationConfig": {
                "temperature": 0.3
            }
        }
        # e.g., https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=...
        url = f"{self.endpoint.rstrip('/')}/v1beta/models/{self.model}:generateContent?key={self.key}"
            
        result = self._make_request(url, headers, data)
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except KeyError:
            return ""
