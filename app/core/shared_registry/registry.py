"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.registry
- RESPONSIBILITY: Provide @register decorator and store class references.
- CALLED BY: app.core.shared_registry.base
- CALLS TO: None
- IN = OUT: Maps string IDs to class implementations.
=============================================================================
"""
from typing import Dict, Type, Any

class RegistryMixin:
    _registry: Dict[str, Type[Any]]
    _all_factories: list[Type[Any]] = []

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
