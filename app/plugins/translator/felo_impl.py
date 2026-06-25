from app.core.factories import TranslatorFactory
from .base_api import BaseAPITranslator

@TranslatorFactory.register("felo")
class FeloTranslator(BaseAPITranslator):
    def _call_api(self, system_prompt: str, user_text: str) -> str:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.key}"
        }
        
        # Felo API uses a single "query" field for web search augmented chat
        query = f"{system_prompt}\n\nPlease strictly follow the instruction and translate the following lines:\n{user_text}"
        data = {
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
