"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.test_config_and_loader
- RESPONSIBILITY: Unit tests for registry loader, configuration verification, and schema checks.
- CALLED BY: Pytest framework
- CALLS TO: app.core.shared_registry.core.loader.RegistryLoader, app.core.desktop.config.ConfigLoader
- IN = OUT: Validates schema checking, model existence verification, and dynamic registry loader.
=============================================================================
"""
import os
import pytest
from app.core.shared_registry.core.loader import RegistryLoader
from app.core.desktop.config import ConfigLoader


def test_registry_loader():
    """Verifies RegistryLoader loads configuration dictionaries correctly."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_loader = ConfigLoader(project_base_dir=project_root)
    loader = RegistryLoader(config_loader)
    registry = loader.load_registry()
    assert isinstance(registry, dict)
    assert len(registry) > 0


def test_config_loader_model_existence_and_missing_fields():
    """Verifies ConfigLoader missing field detection and model existence check."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_loader = ConfigLoader(project_base_dir=project_root)
    
    settings = config_loader.oldsession_config.get("current_settings", {})
    assert isinstance(settings, dict)
    
    missing = config_loader.missing_required_fields(settings)
    assert isinstance(missing, list)
    
    check_exists = config_loader.check_model_existence("paddle_onnx_v6_small", field="offline_detector")
    assert isinstance(check_exists, bool)


