"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.metadata
- RESPONSIBILITY: Extract metadata from registered models.
- CALLED BY: app.core.shared_registry.base
- CALLS TO: None
- IN = OUT: Reads MODELS attribute and returns info.
=============================================================================
"""
import os

class MetadataMixin:
    @classmethod
    def get_source_url_from_registry(cls, field: str, key: str) -> str:
        for factory in cls._all_factories: # type: ignore
            for item in factory.get_all_registered_models():
                if item.get("key") == key:
                    return item.get("source", "")
        return ""

    @classmethod
    def get_model_path_from_registry(cls, field: str, key: str) -> str:
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        for factory in cls._all_factories: # type: ignore
            for item in factory.get_all_registered_models():
                if item.get("key") == key:
                    path = item.get("check_file", "")
                    if path:
                        return os.path.join(project_root, path)
        return ""

    @classmethod
    def get_display_name(cls, name: str) -> str:
        impl_class = cls.get_class(name) # type: ignore
        if impl_class and hasattr(impl_class, 'MODELS'):
            for model in getattr(impl_class, 'MODELS'):
                if model.get('key') == name and 'label' in model:
                    return model['label']
        return name

    @classmethod
    def get_all_registered_models(cls, base_class_filter=None) -> list[dict]:
        """Trả về danh sách dictionary chứa siêu dữ liệu (metadata) của tất cả các models được khai báo trong plugin."""
        models_dict = {}
        if hasattr(cls, '_registry'):
            for impl_class in cls._registry.values():
                if base_class_filter and not issubclass(impl_class, base_class_filter):
                    continue
                if hasattr(impl_class, 'MODELS'):
                    for model in getattr(impl_class, 'MODELS'):
                        key = model.get('key')
                        if key and key not in models_dict:
                            models_dict[key] = model
        return list(models_dict.values())
