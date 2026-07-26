"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.test_registry
- RESPONSIBILITY: Pytest suite testing plugin discovery and registry factory loaders.
- CALLED BY: Pytest framework
- CALLS TO: app.core.shared_registry.*
- IN = OUT: Unit tests verifying dynamic plugin discovery and factory registries.
=============================================================================
"""
import os
import pytest
from app.core.shared_registry import (
    discover_plugins,
    TranslatorFactory,
    DetectorFactory,
    RecognizerFactory,
    CloudOCRFactory,
    InpainterFactory,
    RendererFactory,
    ColorizerFactory,
    UpscalerFactory,
    DiffusionMainModelFactory,
    DiffusionBaseModelFactory
)
from app.core.translator.base_offline import BaseOfflineTranslator
from app.core.translator.base_api import BaseAPITranslator
from app.core.shared_registry.core.loader import RegistryLoader
from app.core.desktop.config.registry import RegistryMixin


def test_discover_plugins():
    """Tests dynamic plugin discovery without errors."""
    discover_plugins()


def test_translator_factory():
    """Tests TranslatorFactory for offline and API translators."""
    discover_plugins()
    offline_models = TranslatorFactory.get_all_registered_models(BaseOfflineTranslator)
    api_models = TranslatorFactory.get_all_registered_models(BaseAPITranslator)
    
    assert isinstance(offline_models, list)
    assert isinstance(api_models, list)


def test_detector_factory():
    """Tests DetectorFactory registered models."""
    discover_plugins()
    detectors = DetectorFactory.get_all_registered_models()
    assert isinstance(detectors, list)


def test_recognizer_and_cloud_ocr_factory():
    """Tests RecognizerFactory and CloudOCRFactory registered models."""
    discover_plugins()
    ocr_models = RecognizerFactory.get_all_registered_models()
    cloud_ocr_models = CloudOCRFactory.get_all_registered_models()
    assert isinstance(ocr_models, list)
    assert isinstance(cloud_ocr_models, list)


def test_inpainter_and_renderer_factory():
    """Tests InpainterFactory and RendererFactory registered models."""
    discover_plugins()
    inpainters = InpainterFactory.get_all_registered_models()
    renderers = RendererFactory.get_all_registered_models()
    assert isinstance(inpainters, list)
    assert isinstance(renderers, list)


def test_colorizer_upscaler_diffusion_factory():
    """Tests Colorizer, Upscaler, and Diffusion factories."""
    discover_plugins()
    colorizers = ColorizerFactory.get_all_registered_models()
    upscalers = UpscalerFactory.get_all_registered_models()
    diff_main = DiffusionMainModelFactory.get_all_registered_models()
    diff_base = DiffusionBaseModelFactory.get_all_registered_models()
    
    assert isinstance(colorizers, list)
    assert isinstance(upscalers, list)
    assert isinstance(diff_main, list)
    assert isinstance(diff_base, list)


def test_registry_loader():
    """Tests RegistryLoader with RegistryMixin."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mixin = RegistryMixin()
    mixin.project_base_dir = project_root
    loader = RegistryLoader(mixin)
    registry = loader.load_registry()

    assert isinstance(registry, dict)
    assert hasattr(mixin, "full_registry")
    assert "fields" in mixin.full_registry
