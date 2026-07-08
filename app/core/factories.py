from typing import Dict, Type, Any

import importlib
import pkgutil
import os
import sys

def discover_plugins():
    """Tự động tìm và import tất cả các plugins trong thư mục app/plugins để đăng ký vào Factory."""
    plugins_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "plugins")
    if not os.path.exists(plugins_dir):
        return
        
    for root, dirs, files in os.walk(plugins_dir):
        for file in files:
            if file.endswith("_impl.py") and not file.startswith("__"):
                rel_path = os.path.relpath(os.path.join(root, file), os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                module_name = "app." + rel_path.replace(os.sep, ".")[:-3]
                try:
                    if module_name not in sys.modules:
                        importlib.import_module(module_name)
                except Exception as e:
                    print(f"[Factories] Failed to auto-discover plugin {module_name}: {e}")

class BaseFactory:
    _registry: Dict[str, Type[Any]]

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
    def create(cls, name: str, model_path: str = "", **kwargs) -> Any:
        """Tạo và trả về instance của lớp triển khai."""
        impl_class = None
        if hasattr(cls, '_registry'):
            if name in cls._registry:
                impl_class = cls._registry[name]
            else:
                # Fallback check for longest matching prefix (e.g., paddle_onnx_v6_tiny -> paddle_onnx, not paddle)
                longest_match = ""
                for reg_name, reg_class in cls._registry.items():
                    if name.startswith(reg_name) and len(reg_name) > len(longest_match):
                        longest_match = reg_name
                        impl_class = reg_class
                        
        if impl_class is None:
            raise ValueError(f"Mô hình '{name}' chưa được đăng ký vào Factory.")
        
        instance = impl_class()
        
        # Call load_weights or load_model based on the type
        if hasattr(instance, 'load_weights'):
            instance.load_weights(model_path, **kwargs)
        elif hasattr(instance, 'load_model'):
            instance.load_model(model_path, **kwargs)
            
        return instance

    @classmethod
    def get_registered_providers(cls, base_class_filter=None) -> list:
        """Trả về danh sách các provider (schema) đã đăng ký."""
        if not hasattr(cls, '_registry'):
            return []
        if base_class_filter:
            return [name for name, impl in cls._registry.items() if issubclass(impl, base_class_filter)]
        return list(cls._registry.keys())

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
    def get_display_name(cls, name: str) -> str:
        impl_class = cls.get_class(name)
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

class TranslatorFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

    @classmethod
    def get_capabilities(cls, name: str) -> dict:
        """Truy vấn năng lực ngôn ngữ hỗ trợ của một plugin cụ thể."""
        if not hasattr(cls, '_registry') or name not in cls._registry:
            return {'__any__': '__all__'}
        impl_class = cls._registry[name]
        if hasattr(impl_class, 'get_supported_languages'):
            return impl_class.get_supported_languages()
        return {'__any__': '__all__'}

class DetectorFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

class RecognizerFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

class InpainterFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

class RendererFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

class UpscalerFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

class ColorizerFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

class CloudOCRFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

class DiffusionFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

discover_plugins()
