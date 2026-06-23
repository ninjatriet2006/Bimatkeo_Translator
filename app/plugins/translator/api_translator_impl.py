import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any

from app.core.interfaces import BaseTranslator
from app.core.factories import TranslatorFactory
from app.core.translator_utils import PromptBuilder, GlossaryManager

class BaseAPITranslator(BaseTranslator):
    """Base class for HTTP API translators."""
    def __init__(self):
        self.endpoint = ""
        self.model = ""
        self.key = ""
        self.prompt_builder = PromptBuilder()
        self.glossary_manager = GlossaryManager()
        self.log_callback = None

    def load_weights(self, model_path: str) -> None:
        """
        Đối với API, 'model_path' được dùng như một JSON string hoặc Dict
        chứa thông tin cấu hình (endpoint, model, key, glossary_path).
        """
        try:
            config = json.loads(model_path) if isinstance(model_path, str) else model_path
            self.endpoint = config.get("endpoint", "")
            self.model = config.get("model", "")
            self.key = config.get("key", "")
            
            glossary_path = config.get("glossary_path", "")
            if glossary_path:
                self.glossary_manager = GlossaryManager(glossary_path)
                
        except Exception as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Failed to parse API config: {e}")

    def _make_request(self, url: str, headers: Dict[str, str], data: Dict[str, Any]) -> dict:
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result
        except urllib.error.URLError as e:
            if self.log_callback:
                self.log_callback("ERROR", f"API Request Error: {e}")
            return {}

    def translate(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        if not texts:
            return texts
            
        system_prompt = self.prompt_builder.build_prompt(src_lang, tgt_lang, self.glossary_manager.glossary)
        combined_text = "\n".join(texts)
        
        import re
        translated_text = self._call_api(system_prompt, combined_text)
        
        if not translated_text:
            return texts
            
        # Strip <think> blocks that reasoning models generate
        translated_text = re.sub(r'<think>.*?</think>', '', translated_text, flags=re.DOTALL).strip()
            
        translated_text = self.glossary_manager.replace_post_translation(translated_text)
        
        # Split back to list
        translated_list = translated_text.split('\n')
        # Handle cases where API merges lines
        if len(translated_list) < len(texts):
            translated_list += [""] * (len(texts) - len(translated_list))
        elif len(translated_list) > len(texts):
            translated_list = translated_list[:len(texts)]
            
        return translated_list

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        raise NotImplementedError


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
            "temperature": 0.3
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

@TranslatorFactory.register("deepl")
class DeepLTranslator(BaseAPITranslator):
    @classmethod
    def get_supported_languages(cls) -> dict:
        return {'__any__': '__all__'}

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        if self.log_callback:
            self.log_callback("WARNING", "DeepL translation schema is not yet implemented.")
        return ""

@TranslatorFactory.register("baidu")
class BaiduTranslator(BaseAPITranslator):
    @classmethod
    def get_supported_languages(cls) -> dict:
        return {'__any__': '__all__'}

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        if self.log_callback:
            self.log_callback("WARNING", "Baidu translation schema is not yet implemented.")
        return ""

@TranslatorFactory.register("youdao")
class YoudaoTranslator(BaseAPITranslator):
    @classmethod
    def get_supported_languages(cls) -> dict:
        return {'__any__': '__all__'}

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        if self.log_callback:
            self.log_callback("WARNING", "Youdao translation schema is not yet implemented.")
        return ""

@TranslatorFactory.register("caiyun")
class CaiyunTranslator(BaseAPITranslator):
    @classmethod
    def get_supported_languages(cls) -> dict:
        return {'__any__': '__all__'}

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        if self.log_callback:
            self.log_callback("WARNING", "Caiyun translation schema is not yet implemented.")
        return ""

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
