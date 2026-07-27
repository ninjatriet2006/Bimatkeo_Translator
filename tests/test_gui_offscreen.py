"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.test_gui_offscreen
- RESPONSIBILITY: Offscreen integration test for TranslatorStudioApp GUI.
- CALLED BY: Pytest framework
- CALLS TO: app.core.desktop.main_window.TranslatorStudioApp
- IN = OUT: Instantiates main window in QT offscreen mode to verify layout construction without popping up windows.
=============================================================================
"""
import os
import sys
import pytest

os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication(sys.argv)
    yield app


def test_main_window_instantiation(qapp):
    """Verifies that TranslatorStudioApp can be instantiated without errors."""
    from app.core.desktop.main_window import TranslatorStudioApp
    window = TranslatorStudioApp()
    assert window is not None
    assert "Bimatkeo Translator" in window.windowTitle()
    assert len(window.findChildren(QObject)) > 0

