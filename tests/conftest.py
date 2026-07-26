"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.conftest
- RESPONSIBILITY: Central Pytest fixtures for PySide6 application testing in headless mode.
- CALLED BY: Pytest framework
- CALLS TO: PySide6.QtWidgets.QApplication, app.core.desktop.main_window.TranslatorStudioApp
- IN = OUT: Provides 'qapp' session fixture with QT_QPA_PLATFORM=offscreen.
=============================================================================
"""
import os
import sys
import pytest

# Ensure QT runs in headless mode to prevent GUI window popping up during tests
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from PySide6.QtWidgets import QApplication
from app.core.desktop.main_window import TranslatorStudioApp


@pytest.fixture(scope="session")
def qapp():
    """Provides a single shared QApplication instance across test session."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def app_instance(qapp):
    """Provides an instantiated TranslatorStudioApp window for unit/UI testing."""
    window = TranslatorStudioApp()
    yield window
    window.close()
