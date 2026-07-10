import random
from app.core.shared_registry import TranslatorFactory, DetectorFactory, RecognizerFactory, InpainterFactory, UpscalerFactory, ColorizerFactory, RendererFactory, CloudOCRFactory, DiffusionMainModelFactory, DiffusionBaseModelFactory

FACTORY_MAP = {
    "offline_translator": TranslatorFactory,
    "ai_translator": TranslatorFactory,
    "offline_detector": DetectorFactory,
    "offline_ocr": RecognizerFactory,
    "api_ocr": CloudOCRFactory,
    "inpainter": InpainterFactory,
    "upscaler": UpscalerFactory,
    "colorizer": ColorizerFactory,
    "renderer": RendererFactory,
    "diffusion_main_model": DiffusionMainModelFactory,
    "diffusion_model": DiffusionBaseModelFactory,
}

class RegistryUtils:
    def __init__(self, registry_mixin):
        self.rm = registry_mixin

    def format_display_label(self, key, field=None):
        if not isinstance(key, str):
            return str(key)
        
        if key == "none":
            return "--- Not Used ---"
        if key == "original":
            return "--- Original ---"
            
        if field and field in FACTORY_MAP:
            factory = FACTORY_MAP[field]
            display = factory.get_display_name(key)
            if display != key:
                return display
                
        if not field:
            for factory in FACTORY_MAP.values():
                display = factory.get_display_name(key)
                if display != key:
                    return display
                    
        labels = getattr(self.rm, "model_labels", {})
        if field and field in labels and key in labels[field]:
            return labels[field][key]
        for field_labels in labels.values():
            if key in field_labels:
                return field_labels[key]
                
        return key

    def list_field_keys(self, field):
        return list(getattr(self.rm, "model_registry", {}).get(field, {}).keys())

    def resolve_available_model(self, field, current_value):
        registry = getattr(self.rm, "model_registry", {})
        by_key = registry.get(field, {})

        if current_value and current_value in by_key:
            return current_value

        def is_setup(key):
            try:
                return self.rm.check_model_existence(key, field=field)
            except Exception:
                return False

        ready = [k for k in by_key.keys() if is_setup(k)]
        if ready:
            return random.choice(ready)
        if by_key:
            return random.choice(list(by_key.keys()))
        return ""

    SETTINGS_FIELD_MAP = {
        "offline_translator": "offline_translator",
        "ai_translator": "ai_translator",
        "offline_detector": "offline_detector",
        "offline_ocr": "offline_ocr",
        "api_ocr": "api_ocr",
        "inpainter": "inpainter",
        "upscaler": "upscaler",
        "colorizer": "colorizer",
    }

    def sweep_settings(self, settings):
        if not isinstance(settings, dict):
            return []

        changes = []

        for key, field in self.SETTINGS_FIELD_MAP.items():
            if key not in settings:
                continue
            old = settings.get(key)
            if old in (None, "", "none", "original"):
                continue
            new = self.resolve_available_model(field, old)
            if new != old:
                settings[key] = new
                changes.append((key, old, new))

        category = settings.get("translator_category", "Offline")
        is_ai = category not in ("Offline", None, "")
        category_key = "ai_translator" if is_ai else "offline_translator"
        field = category_key

        if "translator" in settings:
            old = settings.get("translator")
            if old not in (None, "", "none", "original"):
                if category_key in settings and settings[category_key] not in (None, "", "none", "original"):
                    new = settings[category_key]
                else:
                    new = self.resolve_available_model(field, old)
                if new != old:
                    settings["translator"] = new
                    changes.append(("translator", old, new))

        return changes

    def missing_required_fields(self, settings):
        if not isinstance(settings, dict):
            return []
        missing = []
        for field in getattr(self.rm, 'required_model_fields', []):
            value = settings.get(field)
            if value in (None, "", "none"):
                missing.append(field)
                continue
            try:
                if not self.rm.check_model_existence(value, field=field):
                    missing.append(field)
            except Exception:
                missing.append(field)
        return missing
