"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.api.config
- RESPONSIBILITY: Load model configurations and registry.
- CALLED BY: app.core.api.models, app.core.api.fetcher
- CALLS TO: ruamel.yaml
- IN = OUT: Reads YAML files and exports _MODEL_BLACKLIST, _AI_TRANSLATOR_REGISTRY.
=============================================================================
"""
import os
from ruamel.yaml import YAML

def _get_registry_data():
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    registry_path = os.path.join(project_root, ".config", "models", "model_registry.yaml")
    schema_path = os.path.join(project_root, "default_configs", "configs", "schema_fallback.yaml")
    
    global_blacklist = []
    ai_translators = []
    
    try:
        y = YAML(typ='safe')
        
        # Load custom endpoints via factories
        from app.core.factories import TranslatorFactory
        from app.plugins.translator.base_api import BaseAPITranslator
        ai_translators = TranslatorFactory.get_all_registered_models(BaseAPITranslator)
            
        # Load SSOT model blacklist
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_data = y.load(f) or {}
            global_blacklist = schema_data.get("properties", {}).get("global_settings", {}).get("properties", {}).get("model_blacklist", {}).get("default", [])
            
    except Exception as e:
        print(f"[api.config] Warning: Failed to load registry/schema: {e}")
        
    return global_blacklist, ai_translators

_MODEL_BLACKLIST, _AI_TRANSLATOR_REGISTRY = _get_registry_data()
