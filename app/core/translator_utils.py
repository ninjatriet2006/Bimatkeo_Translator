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
        role_desc = (
            "You are a professional manga/comic translator. "
            "Your task is to translate the following text from {src} to {tgt}. "
            "Maintain the tone, emotions, and formatting of the original text. "
            "If the text contains sound effects or onomatopoeia, translate them naturally.\n"
            "IMPORTANT: The input lines may be split across multiple speech bubbles but form a single continuous conversation or sentence. Mentally combine them to understand the full context before translating, then distribute the translated sentence back across the corresponding lines naturally so they make sense when read together."
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
            "      \"confidence_score\": 0.85\n"
            "    }}\n"
            "  ],\n"
            "  \"global_notes\": \"Any general notes\"\n"
            "}}\n"
            "Ensure the `content` array has the EXACT SAME number of items as the input lines.\n"
            "\"confidence_score\" should be a float from 0.0 to 1.0 representing your certainty."
        )

        prompt_file = os.path.join(self.project_base_dir, ".config", "configs", "system_prompt.yaml")
        
        if os.path.exists(prompt_file):
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
                        if "json_schema_rules" in profile_data:
                            raw_rules = profile_data["json_schema_rules"].strip()
                            json_rules = raw_rules.replace("{", "{{").replace("}", "}}")
            except (FileNotFoundError, yaml.YAMLError, OSError):
                pass
                
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
