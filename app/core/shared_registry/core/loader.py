"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.core.loader
- RESPONSIBILITY: Load registry configuration from YAML and resolve OS placeholders.
- CALLED BY: app.core.desktop.config.registry
- CALLS TO: app.core.shared_registry
- IN = OUT: Returns model registry dict and updates registry mixin.
=============================================================================
"""
import os
import sys
from app.core.base.constants import REQUIRED_MODEL_FIELDS, GLOBAL_RESOURCES, MODEL_PRIORITY_KEYWORDS
from app.core.shared_registry import (
    TranslatorFactory, DetectorFactory, RecognizerFactory, InpainterFactory,
    UpscalerFactory, ColorizerFactory, RendererFactory, CloudOCRFactory,
    DiffusionMainModelFactory, DiffusionBaseModelFactory
)
from app.core.translator.base_offline import BaseOfflineTranslator
from app.core.translator.base_api import BaseAPITranslator

_os_suffix = "win" if sys.platform.startswith('win') else ("macos" if sys.platform.startswith('darwin') else "linux")
_exe_ext = ".exe" if _os_suffix == "win" else ""

class RegistryLoader:
    def __init__(self, registry_mixin):
        self.rm = registry_mixin
        
    def registry_path(self):
        return os.path.join(self.rm.project_base_dir, self.rm.REGISTRY_RELATIVE_PATH)

    def resolve_os_placeholders(self, path):
        if not isinstance(path, str):
            return path
        return path.replace("{os}", _os_suffix).replace("{exe}", _exe_ext)

    def load_registry(self):
        self.rm.required_model_fields = REQUIRED_MODEL_FIELDS
        self.rm.global_settings = {
            "resources": GLOBAL_RESOURCES,
            "model_priority_keywords": MODEL_PRIORITY_KEYWORDS
        }
        
        UI_TAB_LAYOUT = {
            "General & Translator": {
                "offline_translator": TranslatorFactory.get_all_registered_models(BaseOfflineTranslator),
                "ai_translator": TranslatorFactory.get_all_registered_models(BaseAPITranslator),
            },
            "Detector & OCR": {
                "offline_detector": DetectorFactory.get_all_registered_models(),
                "offline_ocr": RecognizerFactory.get_all_registered_models(),
                "api_ocr": CloudOCRFactory.get_all_registered_models(),
            },
            "Image & Inpainter": {
                "inpainter": InpainterFactory.get_all_registered_models(),
                "diffusion_main_model": DiffusionMainModelFactory.get_all_registered_models(),
                "diffusion_model": DiffusionBaseModelFactory.get_all_registered_models(),
                "upscaler": UpscalerFactory.get_all_registered_models(),
                "colorizer": ColorizerFactory.get_all_registered_models(),
            },
            "Render & Output": {
                "renderer": RendererFactory.get_all_registered_models(),
            }
        }

        self.rm.full_registry = {
            "fields": UI_TAB_LAYOUT,
            "required_fields": self.rm.required_model_fields,
            "global_settings": self.rm.global_settings
        }
        
        flattened_fields = {}
        for tab_name, categories in UI_TAB_LAYOUT.items():
            for field, models in categories.items():
                flattened_fields[field] = models

        self.rm.all_model_fields = list(flattened_fields.keys())

        self.rm.model_registry = self.validate_fields(flattened_fields)
        self.rm._derive_all()
        return self.rm.model_registry

    def validate_fields(self, fields):
        validated = {}
        for field, entries in fields.items():
            if not isinstance(entries, list):
                print(f"[Registry] Field '{field}' is not a list. Skipping field.")
                continue
            by_key = {}
            for idx, entry in enumerate(entries):
                if not isinstance(entry, dict):
                    print(f"[Registry] {field}[{idx}] is not a mapping. Skipping block.")
                    continue
                key = entry.get("key")
                if not key or not isinstance(key, str):
                    print(f"[Registry] {field}[{idx}] missing valid 'key'. Skipping block.")
                    continue
                if key in by_key:
                    print(f"[Registry] Duplicate key '{key}' in '{field}'. Keeping first, skipping duplicate.")
                    continue
                clean = dict(entry)
                if "check_file" in clean:
                    clean["check_file"] = self.resolve_os_placeholders(clean["check_file"])
                by_key[key] = clean
            validated[field] = by_key
        return validated
