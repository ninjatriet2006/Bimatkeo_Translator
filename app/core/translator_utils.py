import os
import re
from typing import Dict, List, Optional
import yaml

class GlossaryManager:
    """Quản lý các thuật ngữ (Glossary) để tránh bị dịch sai."""

    def __init__(self, profile_name: str = "None"):
        self.glossary: Dict[str, str] = {}
        self.profile_name = profile_name
        self._load_glossary()

    def _load_glossary(self):
        """Tải danh sách từ vựng từ system_prompt.yaml."""
        if not self.profile_name or self.profile_name == "None":
            return

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        prompt_file = os.path.join(project_root, ".config", "configs", "system_prompt.yaml")
        
        if not os.path.exists(prompt_file):
            return

        try:
            import yaml
            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and "profiles" in data and self.profile_name in data["profiles"]:
                    profile_data = data["profiles"][self.profile_name]
                    post_dict_str = profile_data.get("post_dict", "")
                    
                    for line in post_dict_str.splitlines():
                        line = line.strip()
                        if line and '|' in line and not line.startswith('#'):
                            val, key = line.split('|', 1) # Format: CorrectedText | OCR_Error
                            self.glossary[key.strip()] = val.strip()
        except Exception as e:
            print(f"[GlossaryManager] Lỗi tải từ điển: {e}")

    def replace_pre_translation(self, text: str) -> str:
        """Thực hiện đánh dấu hoặc thay thế nhẹ trước khi ném vào máy dịch (dành cho Offline)."""
        # (Chức năng này mở rộng trong tương lai cho các Model nhạy cảm)
        return text

    def replace_post_translation(self, text: str) -> str:
        """Ép kiểu sửa lại tên riêng sau khi dịch xong."""
        if not self.glossary:
            return text

        # Sửa thẳng các chuỗi lỗi ngớ ngẩn (nếu máy dịch dịch sai Key -> Value)
        # Sẽ ưu tiên độ dài Key giảm dần để tránh thay thế chồng lấp
        sorted_keys = sorted(self.glossary.keys(), key=len, reverse=True)
        for key in sorted_keys:
            val = self.glossary[key]
            # Case-insensitive replace for robustness in comics
            pattern = re.compile(re.escape(key), re.IGNORECASE)
            text = pattern.sub(val, text)
            
        return text


class PromptBuilder:
    """Trình xây dựng ngữ cảnh dịch (System Prompt) cho AI Translator."""

    def __init__(self, profile_name: str = "None"):
        self.base_prompt = ""
        self.profile_name = profile_name
        self._load_system_prompt()

    def _load_system_prompt(self):
        role_desc = (
            "You are a professional manga/comic translator. "
            "Your task is to translate the following text from {src} to {tgt}. "
            "Maintain the tone, emotions, and formatting of the original text. "
            "If the text contains sound effects or onomatopoeia, translate them naturally."
        )
        json_rules = (
            "CRITICAL RULES: \n"
            "- You MUST output ONLY a valid JSON object. Do NOT wrap it in markdown code blocks (e.g. ```json). Do NOT add conversational fillers.\n"
            "- The JSON object MUST strictly follow this schema:\n"
            "{{\n"
            "  \"metadata\": {{\n"
            "    \"status\": \"success\" or \"error\" or \"need_context\",\n"
            "    \"error_reason\": \"Detail reason if status is not success\",\n"
            "    \"detected_source_language\": \"Language name\",\n"
            "    \"target_language\": \"Language name\",\n"
            "    \"line_count_match\": true/false (must match exact input line count)\n"
            "  }},\n"
            "  \"content\": [\n"
            "    {{\n"
            "      \"line_index\": 1,\n"
            "      \"original_text\": \"Original line 1\",\n"
            "      \"translated_text\": \"Translated line 1\",\n"
            "      \"context_notes\": \"Notes on puns, slang, or context (if any)\",\n"
            "      \"confidence_score\": 0.95\n"
            "    }}\n"
            "  ],\n"
            "  \"global_notes\": \"Any general notes\"\n"
            "}}\n"
            "Ensure the `content` array has the EXACT SAME number of items as the input lines."
        )

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        prompt_file = os.path.join(project_root, ".config", "configs", "system_prompt.yaml")
        
        if os.path.exists(prompt_file):
            try:
                import yaml
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and "profiles" in data:
                        profile_data = data["profiles"].get(self.profile_name, {})
                        # Fallback to default if profile not found but roles exist globally (old structure)
                        if not profile_data and self.profile_name == "None":
                            profile_data = data

                        if "role_description" in profile_data:
                            role_desc = profile_data["role_description"].strip()
                        if "json_schema_rules" in profile_data:
                            # Note: f-string formatting requires escaping curly braces.
                            # The yaml string has `{` and `}` for JSON, we need to escape them for `.format()` later.
                            # So we replace `{` with `{{` and `}` with `}}` EXCEPT for `{src}` and `{tgt}` which might be in role_desc.
                            # Since JSON rules shouldn't have {src} or {tgt}, we can just double all braces.
                            raw_rules = profile_data["json_schema_rules"].strip()
                            json_rules = raw_rules.replace("{", "{{").replace("}", "}}")
            except Exception:
                pass
                
        self.base_prompt = f"{role_desc}\n{json_rules}"

    def _get_lang_name(self, code: str) -> str:
        """Helper to convert internal codes to full language names."""
        if code.lower() == 'auto':
            return 'Auto-Detect'
            
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        lang_file = os.path.join(project_root, ".config", "configs", "supporttargetlang.yaml")
        if os.path.exists(lang_file):
            try:
                import yaml
                with open(lang_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Supporttargetlang might not be a valid dict YAML, it's often KEY: Value format.
                for line in content.splitlines():
                    if ':' in line:
                        k, v = line.split(':', 1)
                        if k.strip().upper() == code.upper():
                            return v.strip()
            except Exception:
                pass
        return code

    def build_prompt(self, src_lang: str, tgt_lang: str, glossary: Optional[Dict[str, str]] = None) -> str:
        """Tạo Prompt hoàn chỉnh, có tiêm Glossary nếu có."""
        full_src = self._get_lang_name(src_lang)
        full_tgt = self._get_lang_name(tgt_lang)
        prompt = self.base_prompt.format(src=full_src, tgt=full_tgt)

        if glossary:
            prompt += "\n\n# GLOSSARY (Strictly use these translations for names/terms):\n"
            for k, v in glossary.items():
                prompt += f"- {k} -> {v}\n"

        return prompt
