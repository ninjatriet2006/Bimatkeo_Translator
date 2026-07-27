"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.test_plugin_registry
- RESPONSIBILITY: Unit tests for plugin discovery and shared registry factories.
- CALLED BY: Pytest framework
- CALLS TO: app.core.shared_registry (TranslatorFactory, CloudOCRFactory, DetectorFactory, RendererFactory, MultimodalFactory)
- IN = OUT: Verifies that plugins are automatically discovered and registered into factories.
=============================================================================
"""
import pytest
from app.core.shared_registry import (
    TranslatorFactory,
    CloudOCRFactory,
    DetectorFactory,
    RendererFactory,
    discover_plugins
)
from app.core.translator.base_api import BaseAPITranslator
from app.core.translator.base_offline import BaseOfflineTranslator


@pytest.fixture(scope="module", autouse=True)
def setup_plugins():
    """Ensure plugins are discovered before running tests."""
    discover_plugins()


def test_translator_factory_registration():
    """Verify API and offline translator model registration."""
    api_models = TranslatorFactory.get_all_registered_models(BaseAPITranslator)
    offline_models = TranslatorFactory.get_all_registered_models(BaseOfflineTranslator)
    
    assert isinstance(api_models, list)
    assert isinstance(offline_models, list)
    assert len(api_models) + len(offline_models) > 0


def test_cloud_ocr_factory_registration():
    """Verify Cloud OCR models are registered."""
    ocr_models = CloudOCRFactory.get_all_registered_models()
    assert isinstance(ocr_models, list)
    assert len(ocr_models) > 0


def test_detector_factory_registration():
    """Verify Detector models are registered."""
    detectors = DetectorFactory.get_all_registered_models()
    assert isinstance(detectors, list)
    assert len(detectors) > 0


def test_renderer_factory_registration():
    """Verify Renderer models are registered."""
    renderers = RendererFactory.get_all_registered_models()
    assert isinstance(renderers, list)
    assert len(renderers) > 0
