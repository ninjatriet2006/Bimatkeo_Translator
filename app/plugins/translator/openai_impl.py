from app.core.shared_registry import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("openai")
class OpenAITranslator(BaseAPITranslator):
    MODELS = [
        {'key': 'openai', 'check_file': 'app/plugins/translator/openai_impl.py', 'default_endpoint': 'https://api.openai.com/v1', 'endpoint_inference': []},
        {'key': 'deepseek', 'check_file': 'app/plugins/translator/openai_impl.py', 'default_endpoint': 'https://api.deepseek.com', 'endpoint_inference': []},
        {'key': 'groq', 'check_file': 'app/plugins/translator/openai_impl.py', 'default_endpoint': 'https://api.groq.com/openai/v1', 'endpoint_inference': []},
        {'key': 'custom_openai', 'check_file': 'app/plugins/translator/openai_impl.py', 'endpoint_inference': []},
    ]

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
