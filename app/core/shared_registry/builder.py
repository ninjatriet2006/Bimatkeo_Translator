"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.builder
- RESPONSIBILITY: Instantiate plugins and invoke their load methods.
- CALLED BY: app.core.shared_registry.base
- CALLS TO: None
- IN = OUT: Returns an initialized instance of a plugin.
=============================================================================
"""
from typing import Any

class BuilderMixin:
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
