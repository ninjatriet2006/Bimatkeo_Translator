"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.translator.utils
- RESPONSIBILITY: Xây dựng System Prompt chuẩn JSON cho Translator.
- CALLED BY: app.core.translator
- CALLS TO: None
- IN = OUT: Đọc file cấu hình system_prompt.yaml và sinh ra string.
=============================================================================
"""
import os
import re
import yaml

class PromptBuilder:
    """Trình xây dựng ngữ cảnh dịch (System Prompt) cho AI Translator."""

    def __init__(self, project_base_dir: str, profile_name: str = "None"):
        self.base_prompt = ""
        self.profile_name = profile_name
        self.project_base_dir = project_base_dir
        self._load_system_prompt()

    def _load_system_prompt(self):
        prompt_file = os.path.join(self.project_base_dir, ".config", "configs", "system_prompt.yaml")
        
        if not os.path.exists(prompt_file):
            raise FileNotFoundError(f"Không tìm thấy file cấu hình system prompt tại: {prompt_file}")

        role_desc = ""
        json_rules = ""
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if data and "profiles" in data:
                    profile_data = data["profiles"].get(self.profile_name, {})
                    # Fallback to default if profile not found but roles exist globally (old structure)
                    if not profile_data and self.profile_name == "None":
                        profile_data = data

                    if "role_description" in profile_data:
                        role_desc = profile_data["role_description"].strip()
                    else:
                        raise ValueError(f"Thiếu 'role_description' trong profile '{self.profile_name}' của file {prompt_file}")
                        
                    if "json_schema_rules" in profile_data:
                        raw_rules = profile_data["json_schema_rules"].strip()
                        json_rules = raw_rules.replace("{", "{{").replace("}", "}}")
                    else:
                        raise ValueError(f"Thiếu 'json_schema_rules' trong profile '{self.profile_name}' của file {prompt_file}")
                        
        except (yaml.YAMLError, OSError) as e:
            raise RuntimeError(f"Lỗi khi đọc file system_prompt.yaml: {e}")
            
        self.base_prompt = f"{role_desc}\n{json_rules}"

    def _get_lang_name(self, code: str) -> str:
        """Helper to convert internal codes to full language names."""
        if code.lower() == 'auto':
            return 'Auto-Detect'
            
        lang_file = os.path.join(self.project_base_dir, ".config", "configs", "supporttargetlang.yaml")
        if os.path.exists(lang_file):
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                for line in content.splitlines():
                    if ':' in line:
                        k, v = line.split(':', 1)
                        if k.strip().upper() == code.upper():
                            return v.strip()
            except OSError:
                pass
        return code

    def build_prompt(self, src_lang: str, tgt_lang: str, glossary: dict[str, str] | None = None) -> str:
        """Tạo Prompt hoàn chỉnh, có tiêm Glossary nếu có."""
        full_src = self._get_lang_name(src_lang)
        full_tgt = self._get_lang_name(tgt_lang)
        prompt = self.base_prompt.format(src=full_src, tgt=full_tgt)

        if glossary:
            prompt += "\n\n# GLOSSARY (Strictly use these translations for names/terms):\n"
            for k, v in glossary.items():
                prompt += f"- {k} -> {v}\n"

        return prompt
