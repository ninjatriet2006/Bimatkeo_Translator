import os
import re
from typing import Dict, List, Optional
import yaml

class GlossaryManager:
    """Quản lý các thuật ngữ (Glossary) để tránh bị dịch sai."""

    def __init__(self, glossary_path: str = ""):
        self.glossary: Dict[str, str] = {}
        self.glossary_path = glossary_path
        self._load_glossary()

    def _load_glossary(self):
        """Tải danh sách từ vựng từ file."""
        if not self.glossary_path or not os.path.exists(self.glossary_path):
            return

        try:
            with open(self.glossary_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Hỗ trợ cả file txt (Key=Value) và yaml
            if self.glossary_path.endswith(('.yaml', '.yml')):
                data = yaml.safe_load(content)
                if isinstance(data, dict):
                    self.glossary = {str(k): str(v) for k, v in data.items()}
            else:
                for line in content.splitlines():
                    line = line.strip()
                    if line and '=' in line and not line.startswith('#'):
                        key, val = line.split('=', 1)
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

    def __init__(self):
        self.base_prompt = (
            "You are a professional manga/comic translator. "
            "Your task is to translate the following text from {src} to {tgt}. "
            "Maintain the tone, emotions, and formatting of the original text. "
            "If the text contains sound effects or onomatopoeia, translate them naturally. "
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
