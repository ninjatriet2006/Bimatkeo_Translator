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
        from app.core.shared_registry import TranslatorFactory
        from app.core.translator.base_api import BaseAPITranslator
        ai_translators = TranslatorFactory.get_all_registered_models(BaseAPITranslator)
            
    except Exception as e:
        print(f"[api.config] Warning: Failed to load registry: {e}")
        
    return global_blacklist, ai_translators

_MODEL_BLACKLIST, _AI_TRANSLATOR_REGISTRY = _get_registry_data()
