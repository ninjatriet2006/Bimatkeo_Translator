import os
import yaml

class RepairMixin:
    def _get_yaml_filename(self, field: str) -> str:
        field_lower = field.lower()
        if field_lower in ["alignment", "direction", "inpainting_precision", "renderer"]:
            return os.path.join("configs", f"config_{field_lower}.yaml")
        return os.path.join("models", f"model_{field_lower}.yaml")

    def _initialize_and_repair_config(self):
        """
        Ensures that .config/ exists and contains validated, repaired YAML files
        for languages (supporttargetlang.yaml) and all backend enum models (model_ocr.yaml, etc.).
        """
        config_dir = os.path.join(self.project_base_dir, ".config")
        os.makedirs(os.path.join(config_dir, "configs"), exist_ok=True)
        os.makedirs(os.path.join(config_dir, "models"), exist_ok=True)

        # 1. Repair supporttargetlang.yaml
        lang_yaml_path = os.path.join(config_dir, "configs", "supporttargetlang.yaml")
        old_lang_path = os.path.join(config_dir, "configs", "lang.yaml")
        
        if hasattr(self, 'languages') and self.languages:
            default_langs = {str(v): str(k) for k, v in self.languages.items()}
        else:
            default_langs = {
                "auto": "Auto-Detect", "ENG": "English", "TRK": "Turkish", "JPN": "Japanese",
                "KOR": "Korean", "CHS": "Simplified Chinese", "CHT": "Traditional Chinese",
                "ESP": "Spanish", "FRA": "French", "DEU": "German", "RUS": "Russian",
                "PTB": "Portuguese (Brazilian)", "ITA": "Italian", "POL": "Polish",
                "NLD": "Dutch", "CSY": "Czech", "HUN": "Hungarian", "ROM": "Romanian",
                "UKR": "Ukrainian", "VIN": "Vietnamese", "ARA": "Arabic", "SRP": "Serbian",
                "HRV": "Croatian", "THA": "Thai", "IND": "Indonesian", "FIL": "Filipino (Tagalog)"
            }

        loaded_langs = {}
        read_path = lang_yaml_path if os.path.exists(lang_yaml_path) else old_lang_path
        if os.path.exists(read_path):
            try:
                with open(read_path, 'r', encoding='utf-8') as f:
                    content = yaml.safe_load(f)
                if isinstance(content, dict):
                    for k, v in content.items():
                        if k and v and isinstance(k, (str, int, float)) and isinstance(v, (str, int, float)):
                            loaded_langs[str(k)] = str(v)
            except Exception as e:
                print(f"[ConfigLoader] Error reading lang config: {e}")

        repaired_langs = default_langs.copy()
        repaired_langs.update(loaded_langs)

        try:
            with open(lang_yaml_path, 'w', encoding='utf-8') as f:
                yaml.dump(repaired_langs, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            if os.path.exists(old_lang_path) and lang_yaml_path != old_lang_path:
                os.remove(old_lang_path)
        except Exception as e:
            print(f"[ConfigLoader] Error writing supporttargetlang.yaml: {e}")

        # 2. Repair dynamic enum model files
        enum_fields = {}
        all_properties = {}

        root_props = self.backend_schema.get("properties", {})
        all_properties.update(root_props)
        for prop in root_props.values():
            ref_path = prop.get("allOf", [{}])[0].get('$ref')
            if ref_path:
                config_def = self._get_definition_from_ref(ref_path)
                if config_def and "properties" in config_def:
                    all_properties.update(config_def["properties"])

        for key, prop_def in all_properties.items():
            if isinstance(prop_def, dict):
                ref_path = prop_def.get("allOf", [{}])[0].get('$ref')
                if ref_path:
                    enum_def = self._get_definition_from_ref(ref_path)
                    if enum_def and "enum" in enum_def:
                        enum_fields[key] = enum_def["enum"]

        if 'translator' in enum_fields:
            del enum_fields['translator']

        translator_groups = self.translator_capabilities.get("TRANSLATOR_GROUPS", {})
        enum_fields['offline_translator'] = translator_groups.get("--- OFFLINE MODELS (No API Key) ---", [])
        enum_fields['ai_translator'] = translator_groups.get("--- API-BASED (Requires Setup) ---", [])

        old_translator_yaml = os.path.join(config_dir, "model_translator.yaml")
        if os.path.exists(old_translator_yaml):
            try:
                os.remove(old_translator_yaml)
            except Exception:
                pass

        for field, schema_choices in enum_fields.items():
            filename = self._get_yaml_filename(field)
            model_yaml_path = os.path.join(config_dir, filename)
            
            root_filename = os.path.basename(filename)
            possible_old_names = [root_filename, f"model_{field.lower()}.yaml", f"config_{field.lower()}.yaml"]
            for old_name in possible_old_names:
                old_path = os.path.join(config_dir, old_name)
                if os.path.exists(old_path) and old_path != model_yaml_path:
                    try:
                        if os.path.exists(model_yaml_path):
                            os.remove(model_yaml_path)
                        os.rename(old_path, model_yaml_path)
                        print(f"[ConfigLoader] Migrated {old_name} to {filename}")
                        break
                    except Exception as e:
                        print(f"[ConfigLoader] Error migrating {old_name} to {filename}: {e}")
            
            loaded_models = []
            if os.path.exists(model_yaml_path):
                try:
                    with open(model_yaml_path, 'r', encoding='utf-8') as f:
                        content = yaml.safe_load(f)
                    if isinstance(content, dict) and "models" in content:
                        models_list = content["models"]
                    elif isinstance(content, list):
                        models_list = content
                    else:
                        models_list = []
                    
                    for item in models_list:
                        if isinstance(item, str):
                            loaded_models.append(item)
                        elif isinstance(item, dict) and "name" in item:
                            loaded_models.append(item)
                except Exception as e:
                    print(f"[ConfigLoader] Error reading {filename}: {e}")

            existing_by_name = {}
            for item in loaded_models:
                if isinstance(item, str):
                    existing_by_name[item] = {"name": item}
                elif isinstance(item, dict) and "name" in item:
                    existing_by_name[item["name"]] = item

            repaired_models = []
            for item in schema_choices:
                name = str(item)
                field_key = field.lower()
                has_default = (field_key in self._DEFAULT_CHECKS and name in self._DEFAULT_CHECKS[field_key])
                
                if name in existing_by_name and not has_default:
                    repaired_models.append(existing_by_name[name])
                else:
                    model_entry = {"name": name}
                    if has_default:
                        model_entry.update(self._DEFAULT_CHECKS[field_key][name])
                    repaired_models.append(model_entry)
            
            for name, item in existing_by_name.items():
                if name not in schema_choices:
                    repaired_models.append(item)

            try:
                with open(model_yaml_path, 'w', encoding='utf-8') as f:
                    yaml.dump({"models": repaired_models}, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            except Exception as e:
                print(f"[ConfigLoader] Error writing {filename}: {e}")
