from app.core.shared_registry import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("felo")
class FeloTranslator(BaseAPITranslator):
    MODELS = [
        {'key': 'felo', 'check_file': 'app/plugins/translator/felo_impl.py', 'default_endpoint': 'https://api.felo.ai/v1', 'endpoint_inference': ['felo.ai']},
    ]

    
    def __init__(self):
        super().__init__()
        self.max_query_len = 2000

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}"
        }
        
        # Felo API uses a single "query" field for web search augmented chat
        query = f"{system_prompt}\n\nPlease strictly follow the instruction and translate the following lines. YOU MUST RETURN ONLY A VALID JSON OBJECT WITH THE 'content' KEY:\n{user_text}"
        data = {
            "model": self.model,
            "query": query
        }
        
        url = self.endpoint
        if not url.endswith("/chat"):
            url = url.rstrip("/") + "/chat"
            
        result = self._make_request(url, headers, data)
        try:
            return result["data"]["answer"].strip()
        except KeyError:
            return ""
