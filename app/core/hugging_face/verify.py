"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.hugging_face.verify
- RESPONSIBILITY: Integrity check for local Hugging Face versions vs Registry.
- CALLED BY: app.core.hugging_face.manager
- CALLS TO: None
- IN = OUT: Evaluates dictionaries, returns validation results/warnings.
=============================================================================
"""

import os

class HFVerifier:
    def __init__(self):
        pass

    def run_verification(self, registry_path: str, local_versions_path: str):
        """
        Cross-checks downloaded local_versions against the model_registry.
        Reports orphaned local versions (models that were removed from the registry
        but still exist in local_versions).
        """
        print("[HuggingFaceVerifier] Running integrity check on local models...")
        from ruamel.yaml import YAML
        yaml = YAML(typ='safe')
        
        registry = {}
        if os.path.exists(registry_path):
            try:
                with open(registry_path, "r", encoding="utf-8") as rf:
                    registry = yaml.load(rf) or {}
            except Exception as e:
                print(f"  [!] Failed to load registry: {e}")

        local_versions = {}
        if os.path.exists(local_versions_path):
            try:
                with open(local_versions_path, "r", encoding="utf-8") as lf:
                    local_versions = yaml.load(lf) or {}
            except Exception as e:
                print(f"  [!] Failed to load local_versions: {e}")

        if not local_versions:
            return

        # Build a set of all valid model keys from the registry
        valid_model_keys = set()
        fields = registry.get("fields", {})
        for tab, categories in fields.items():
            if isinstance(categories, dict):
                for category, models in categories.items():
                    if isinstance(models, list):
                        for model in models:
                            key = model.get("key")
                            if key:
                                valid_model_keys.add(key)

        # Check local versions against valid keys
        for category, models in local_versions.items():
            if not isinstance(models, dict):
                continue
                
            for model_key in models.keys():
                if model_key not in valid_model_keys:
                    print(f"  [!] Orphaned Model Config Found: '{model_key}' in category '{category}'")
                    print(f"      (This model exists in your local_versions.yaml but was removed from model_registry.yaml)")
