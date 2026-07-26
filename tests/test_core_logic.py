"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.test_core_logic
- RESPONSIBILITY: Pytest suite testing decoupled managers, ConfigManager, and controller composition.
- CALLED BY: Pytest framework
- CALLS TO: app.core.desktop.logic.*, app.core.base.manager, app.core.desktop.config
- IN = OUT: Unit tests verifying manager isolation, config loader, and controller composition.
=============================================================================
"""
import os
import pytest
from app.core.desktop.logic.api_profile.manager import ApiProfileManager
from app.core.desktop.logic.config_sync.manager import ConfigSyncManager
from app.core.desktop.logic.job_queue_manager import JobQueueUIManager
from app.core.desktop.logic.theme_manager import ThemeManager
from app.core.base.manager import ConfigManager
from app.core.desktop.config import ConfigLoader
from app.core.desktop.main_window import TranslatorStudioApp


def test_api_profile_manager_decoupling():
    """Verifies ApiProfileManager instantiates with primitive project_base_dir without main_window dependency."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manager = ApiProfileManager(project_base_dir=project_root)
    assert manager is not None
    assert manager.project_base_dir == project_root
    
    path = manager.get_api_profiles_file_path()
    assert isinstance(path, str)
    assert len(path) > 0


def test_config_sync_manager_decoupling():
    """Verifies ConfigSyncManager instantiates without main_window dependency."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manager = ConfigSyncManager(project_base_dir=project_root)
    assert manager is not None
    assert manager.project_base_dir == project_root


def test_job_queue_ui_manager_decoupling():
    """Verifies JobQueueUIManager instantiates without main_window dependency."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manager = JobQueueUIManager(project_base_dir=project_root)
    assert manager is not None
    assert manager.project_base_dir == project_root


def test_theme_manager_decoupling():
    """Verifies ThemeManager instantiates without main_window dependency."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manager = ThemeManager(project_base_dir=project_root)
    assert manager is not None
    assert manager.project_base_dir == project_root


def test_config_manager_and_loader():
    """Verifies ConfigManager and ConfigLoader functionality."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    cm = ConfigManager(project_root)
    assert cm.backend_schema is not None

    cl = ConfigLoader(project_root)
    assert cl is not None
    assert isinstance(cl.oldsession_config, dict)


def test_controller_composition(app_instance):
    """Verifies explicit controller composition on TranslatorStudioApp."""
    window = app_instance
    assert hasattr(window, "handlers_controller")
    assert window.handlers_controller is not None
