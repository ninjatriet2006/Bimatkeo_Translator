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
            self.endpoint = config.get("endpoint") or ""
            self.model = config.get("model") or ""
            self.key = config.get("key") or ""
            self.max_retries = int(config.get("max_retries", 3))
            
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
        # Add a default User-Agent if not provided to prevent 403 Forbidden from WAFs
        if "User-Agent" not in headers:
            headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            
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
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8', errors='ignore')
            if self.log_callback:
                self.log_callback("ERROR", f"API Request Error: {e}\nResponse: {err_body}")
            return {}
        except urllib.error.URLError as e:
            if self.log_callback:
                self.log_callback("ERROR", f"API Request Error: {e}")
            return {}

    def translate(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        if not texts:
            return texts
            
        system_prompt = self.prompt_builder.build_prompt(src_lang, tgt_lang, self.glossary_manager.glossary)
        
        # Build single chunk of texts without splitting limit
        current_chunk = []
        for i, t in enumerate(texts):
            current_chunk.append(f"Line {i+1}: {t}")
            
        chunks = [current_chunk] if current_chunk else []
            
        all_translated_list = []
        
        import re
        import json
        import time
        
        for chunk in chunks:
            combined_text = "\n".join(chunk)
            
            raw_response = ""
            retry_count = 0
            max_retries = getattr(self, "max_retries", 3)
            
            while retry_count <= max_retries:
                try:
                    raw_response = self._call_api(system_prompt, combined_text)
                except Exception as e:
                    if self.log_callback:
                        self.log_callback("WARNING", f"API Error: {e}")
                    raw_response = None
                
                if raw_response:
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
                        meta = parsed.get("metadata", {})
                        if meta.get("status") in ["success", ""]:
                            break # Success, break out of retry loop
                        else:
                            err = meta.get("error_reason", "Unknown error from AI")
                            if self.log_callback:
                                self.log_callback("WARNING", f"AI Refused translation (attempt {retry_count + 1}/{max_retries + 1}): {err}")
                    except json.JSONDecodeError as e:
                        if self.log_callback:
                            self.log_callback("WARNING", f"Failed to parse JSON (attempt {retry_count + 1}/{max_retries + 1}): {e}")
                else:
                    if self.log_callback:
                        self.log_callback("WARNING", f"Empty API response (attempt {retry_count + 1}/{max_retries + 1})")
                
                retry_count += 1
                if retry_count <= max_retries:
                    time.sleep(2) # Delay before retry
            
            # If all retries failed or final parse failed
            if not raw_response or retry_count > max_retries:
                if self.log_callback:
                    self.log_callback("ERROR", f"Translation failed after {max_retries + 1} attempts.")
                # Append original texts
                for line_str in chunk:
                    original_line = line_str.split(": ", 1)[1] if ": " in line_str else line_str
                    all_translated_list.append(original_line)
                continue
                
            try:
                parsed = json.loads(raw_response)
                
                content = parsed.get("content", [])
                
                # Extract translations for this chunk
                for line_str in chunk:
                    line_idx_str = line_str.split(":", 1)[0].replace("Line ", "").strip()
                    try:
                        line_idx = int(line_idx_str)
                    except ValueError:
                        line_idx = -1
                        
                    matching_item = None
                    for item in content:
                        if item.get("line_index") == line_idx:
                            matching_item = item
                            break
                    
                    if matching_item:
                        all_translated_list.append(matching_item.get("translated_text", ""))
                    else:
                        if self.log_callback:
                            self.log_callback("WARNING", f"AI missed line {line_idx}, using original text.")
                        original_line = line_str.split(": ", 1)[1] if ": " in line_str else line_str
                        all_translated_list.append(original_line)
                        
            except json.JSONDecodeError as e:
                if self.log_callback:
                    self.log_callback("ERROR", f"Failed to parse JSON response for chunk: {e}\nRaw: {raw_response[:200]}...")
                for line_str in chunk:
                    original_line = line_str.split(": ", 1)[1] if ": " in line_str else line_str
                    all_translated_list.append(original_line)
            except Exception as e:
                if self.log_callback:
                    self.log_callback("ERROR", f"Unexpected error during translation chunk: {e}")
                for line_str in chunk:
                    original_line = line_str.split(": ", 1)[1] if ": " in line_str else line_str
                    all_translated_list.append(original_line)
                    
        # Apply glossary replacement post-translation just in case
        translated_list = [self.glossary_manager.replace_post_translation(t) for t in all_translated_list]
        return translated_list

    def _call_api(self, system_prompt: str, user_text: str) -> str:
        raise NotImplementedError


