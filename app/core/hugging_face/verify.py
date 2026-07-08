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


import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import os

class HFVerifier:
    def __init__(self):
        pass

    def run_verification(self, registry_path: str = "", local_versions_path: str = ".config/models/local_versions.yaml"):
        """
        Cross-checks downloaded local_versions against the dynamic model factories.
        Reports orphaned local versions (models that were removed from the registry
        but still exist in local_versions).
        """
        print("[HuggingFaceVerifier] Running integrity check on local models...")
        from ruamel.yaml import YAML
        yaml = YAML(typ='safe')

        local_versions = {}
        if os.path.exists(local_versions_path):
            try:
                with open(local_versions_path, "r", encoding="utf-8") as lf:
                    local_versions = yaml.load(lf) or {}
            except Exception as e:
                print(f"  [!] Failed to load local_versions: {e}")

        if not local_versions:
            return

        # Build a set of all valid model keys from the factories
        valid_model_keys = set()
        from app.core.factories import (
            TranslatorFactory, DetectorFactory, RecognizerFactory, InpainterFactory,
            UpscalerFactory, ColorizerFactory, RendererFactory, CloudOCRFactory, DiffusionFactory
        )
        
        all_models = (
            TranslatorFactory.get_all_registered_models() +
            DetectorFactory.get_all_registered_models() +
            RecognizerFactory.get_all_registered_models() +
            InpainterFactory.get_all_registered_models() +
            UpscalerFactory.get_all_registered_models() +
            ColorizerFactory.get_all_registered_models() +
            RendererFactory.get_all_registered_models() +
            CloudOCRFactory.get_all_registered_models() +
            DiffusionFactory.get_all_registered_models()
        )
        
        for model in all_models:
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
