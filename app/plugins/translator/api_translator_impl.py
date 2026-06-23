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
        self.prompt_builder = PromptBuilder("")
        self.glossary_manager = GlossaryManager("")
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
            
            project_base_dir = config.get("project_base_dir")
            if not project_base_dir:
                project_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            system_prompt_profile = config.get("system_prompt_profile", "None")
            if system_prompt_profile and system_prompt_profile != "None":
                self.prompt_builder = PromptBuilder(project_base_dir, system_prompt_profile)
                self.glossary_manager = GlossaryManager(project_base_dir, system_prompt_profile)
            else:
                # Fallback to older glossary_path if present
                glossary_path = config.get("glossary_path", "")
                if glossary_path:
                    # In this old fallback, glossary_path was sometimes a full path or a profile name
                    self.glossary_manager = GlossaryManager(project_base_dir, glossary_path)
                
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
        
        # Prepare the input nicely for the LLM so it can map line_index correctly
        numbered_texts = [f"Line {i+1}: {t}" for i, t in enumerate(texts)]
        combined_text = "\n".join(numbered_texts)
        
        import re
        import json
        raw_response = self._call_api(system_prompt, combined_text)
        
        if not raw_response:
            return texts
            
        # Strip <think> blocks that reasoning models generate
        raw_response = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
        
        # Clean up Markdown code blocks if any
        if raw_response.startswith('```json'):
            raw_response = raw_response[7:]
        elif raw_response.startswith('```'):
            raw_response = raw_response[3:]
        if raw_response.endswith('```'):
            raw_response = raw_response[:-3]
        raw_response = raw_response.strip()

        try:
            parsed = json.loads(raw_response)
            
            # Check metadata
            meta = parsed.get("metadata", {})
            if meta.get("status") not in ["success", ""]:
                err = meta.get("error_reason", "Unknown error from AI")
                if self.log_callback:
                    self.log_callback("ERROR", f"AI Refused to translate: {err}")
                return texts
                
            content = parsed.get("content", [])
            translated_list = []
            
            # Extract translations maintaining the exact order
            for i, original_line in enumerate(texts):
                # Try to find the matching item in the content array
                matching_item = None
                for item in content:
                    if item.get("line_index") == i + 1:
                        matching_item = item
                        break
                
                if matching_item:
                    translated_list.append(matching_item.get("translated_text", ""))
                else:
                    # If AI missed a line, use the original
                    if self.log_callback:
                        self.log_callback("WARNING", f"AI missed line {i+1}, using original text.")
                    translated_list.append(original_line)
                    
            # Apply glossary replacement post-translation just in case
            translated_list = [self.glossary_manager.replace_post_translation(t) for t in translated_list]
            return translated_list
            
        except json.JSONDecodeError as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Failed to parse JSON response: {e}\nRaw Response: {raw_response[:200]}...")
            return texts
        except Exception as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Translation processing error: {e}")
            return texts

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
