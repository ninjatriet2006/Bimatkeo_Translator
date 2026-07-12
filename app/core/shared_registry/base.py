"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.base
- RESPONSIBILITY: The unified core base class for all factories, providing registration, metadata extraction, and instantiation capabilities.
- CALLED BY: app.core.shared_registry.implementations
- CALLS TO: None
- IN = OUT: Provides a unified BaseFactory pattern for dynamic plugin management.
=============================================================================
"""
import os
from typing import Type, Dict, Any

class BaseFactory:
    """
    Base Factory pattern for dynamic plugin management.
    """
    _registry: Dict[str, Type[Any]]
    _all_factories: list[Type[Any]] = []

    @classmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(BaseFactory, '_all_factories'):
            BaseFactory._all_factories = []
        BaseFactory._all_factories.append(cls)

    # =========================================================================
    # REGISTRY CAPABILITIES
    # =========================================================================
    @classmethod
    def register(cls, name: str):
        """Decorator dùng để đăng ký một triển khai cụ thể."""
        def decorator(subclass):
            if not hasattr(cls, '_registry'):
                cls._registry = {}
            cls._registry[name] = subclass
            return subclass
        return decorator

    @classmethod
    def get_class(cls, name: str) -> Type[Any] | None:
        if not hasattr(cls, '_registry'):
            return None
        if name in cls._registry:
            return cls._registry[name]
        longest_match = ""
        impl_class = None
        for reg_name, reg_class in cls._registry.items():
            if name.startswith(reg_name) and len(reg_name) > len(longest_match):
                longest_match = reg_name
                impl_class = reg_class
        return impl_class

    @classmethod
    def get_registered_providers(cls, base_class_filter=None) -> list:
        """Trả về danh sách các provider (schema) đã đăng ký."""
        if not hasattr(cls, '_registry'):
            return []
        if base_class_filter:
            return [name for name, impl in cls._registry.items() if issubclass(impl, base_class_filter)]
        return list(cls._registry.keys())

    # =========================================================================
    # METADATA CAPABILITIES
    # =========================================================================
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

    # =========================================================================
    # BUILDER CAPABILITIES
    # =========================================================================
    @classmethod
    def create(cls, name: str, model_path: str = "", **kwargs) -> Any:
        """Tạo và trả về instance của lớp triển khai."""
        impl_class = cls.get_class(name) # type: ignore

        if impl_class is None:
            raise ValueError(f"Mô hình '{name}' chưa được đăng ký vào Factory.")

        instance = impl_class()

        # Call load_weights or load_model based on the type
        if hasattr(instance, 'load_weights'):
            instance.load_weights(model_path, **kwargs)
        elif hasattr(instance, 'load_model'):
            instance.load_model(model_path, **kwargs)

        return instance
