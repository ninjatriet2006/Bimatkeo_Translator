from app.core.factories import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("openai")
class OpenAITranslator(BaseAPITranslator):
    def _call_api(self, system_prompt: str, user_text: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}"
        }
        data = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text}
            ],
            "temperature": 0.3,
            "response_format": {"type": "json_object"}
        }
        url = self.endpoint
        if not url.endswith("/chat/completions"):
            url = url.rstrip("/") + "/chat/completions"
            
        result = self._make_request(url, headers, data)
        try:
            return result["choices"][0]["message"]["content"].strip()
        except KeyError:
            return ""

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
