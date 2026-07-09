"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.__init__
- RESPONSIBILITY: Facade exporting all specific factories and triggering discovery.
- CALLED BY: Various
- CALLS TO: app.core.shared_registry.discovery
- IN = OUT: Entrypoint for the shared_registry package.
=============================================================================
"""
from .base import BaseFactory
from .implementations import (
    TranslatorFactory,
    DetectorFactory,
    RecognizerFactory,
    InpainterFactory,
    RendererFactory,
    UpscalerFactory,
    ColorizerFactory,
    CloudOCRFactory,
    DiffusionMainModelFactory,
    DiffusionBaseModelFactory
)
from .discovery import discover_plugins

__all__ = [
    "BaseFactory",
    "TranslatorFactory",
    "DetectorFactory",
    "RecognizerFactory",
    "InpainterFactory",
    "RendererFactory",
    "UpscalerFactory",
    "ColorizerFactory",
    "CloudOCRFactory",
    "DiffusionMainModelFactory",
    "DiffusionBaseModelFactory"
]

# Tự động scan và nạp các plugin vào registry ngay khi package được load
discover_plugins()
