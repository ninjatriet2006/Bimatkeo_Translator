from typing import Dict, Type, Any

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
        if not hasattr(cls, '_registry') or name not in cls._registry:
            raise ValueError(f"Mô hình '{name}' chưa được đăng ký vào Factory.")
        
        impl_class = cls._registry[name]
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
