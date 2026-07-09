"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.implementations
- RESPONSIBILITY: Concrete registry containers for specific system domains.
- CALLED BY: Various
- CALLS TO: None
- IN = OUT: Defines classes like TranslatorFactory, OCRFactory, etc.
=============================================================================
"""
from typing import Dict, Type, Any
from .base import BaseFactory

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

class DiffusionMainModelFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}

class DiffusionBaseModelFactory(BaseFactory):
    _registry: Dict[str, Type[Any]] = {}
