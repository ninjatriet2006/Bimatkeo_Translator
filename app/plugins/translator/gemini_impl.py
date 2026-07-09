from app.core.shared_registry import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("gemini")
class GeminiTranslator(BaseAPITranslator):
    MODELS = [
        {'key': 'gemini', 'check_file': 'app/plugins/translator/gemini_impl.py', 'default_endpoint': 'https://generativelanguage.googleapis.com', 'endpoint_inference': ['generativelanguage']},
    ]

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
        endpoint = self.endpoint.rstrip('/') if self.endpoint else "https://generativelanguage.googleapis.com"
        # e.g., https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=...
        url = f"{endpoint}/v1beta/models/{self.model}:generateContent?key={self.key}"
            
        result = self._make_request(url, headers, data)
        try:
            return result["candidates"][0]["content"]["parts"][0]["text"].strip()
        except KeyError:
            return ""
