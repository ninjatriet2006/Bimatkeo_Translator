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
            "Output ONLY the translated text, without any explanations or conversational fillers."
        )

    def build_prompt(self, src_lang: str, tgt_lang: str, glossary: Dict[str, str] = None) -> str:
        """Tạo Prompt hoàn chỉnh, có tiêm Glossary nếu có."""
        prompt = self.base_prompt.format(src=src_lang, tgt=tgt_lang)

        if glossary:
            prompt += "\n\n# GLOSSARY (Strictly use these translations for names/terms):\n"
            for k, v in glossary.items():
                prompt += f"- {k} -> {v}\n"

        return prompt
