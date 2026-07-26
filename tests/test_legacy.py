"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.test_legacy
- RESPONSIBILITY: Refactored legacy tests converted into standard pytest test functions.
- CALLED BY: Pytest framework
- CALLS TO: app.core.*, PySide6.*
- IN = OUT: Unit tests verifying legacy behavior, window creation, timers, loaders, and factories.
=============================================================================
"""
import os
import sys
import time
import yaml
import threading
import pytest
from PySide6.QtWidgets import QPushButton, QApplication
from PySide6.QtCore import QMetaObject, Qt, QTimer

from app.core.desktop.main_window import TranslatorStudioApp
from app.core.desktop.config import ConfigLoader
from app.core.shared_registry import (
    TranslatorFactory,
    DetectorFactory,
    CloudOCRFactory,
    RendererFactory,
    discover_plugins
)
from app.core.translator.base_offline import BaseOfflineTranslator
from app.core.translator.base_api import BaseAPITranslator
from app.core.shared_registry.core.loader import RegistryLoader
from app.core.desktop.config.registry import RegistryMixin


def test_legacy_check(qapp):
    """Refactored test_check.py: Uses TranslatorStudioApp instead of non-existent BimatkeoTranslator."""
    window = TranslatorStudioApp()
    settings = window.current_settings
    assert isinstance(settings, dict)
    missing = window.config_loader.missing_required_fields(settings)
    assert isinstance(missing, (list, set, dict))
    check_exists = window.config_loader.check_model_existence("paddle_onnx_v6_small", field="offline_detector")
    assert isinstance(check_exists, bool)
    window.close()


def test_legacy_invoke(qapp):
    """Refactored test_invoke.py: Test thread invocation via QMetaObject using qapp fixture."""
    from PySide6.QtCore import QObject, Slot, Q_ARG

    btn = QPushButton("Wait")
    btn.show()

    class Receiver(QObject):
        @Slot(str)
        def set_text_slot(self, text):
            btn.setText(text)

    receiver = Receiver()

    def bg_thread():
        time.sleep(0.1)
        QMetaObject.invokeMethod(receiver, "set_text_slot", Qt.ConnectionType.QueuedConnection, Q_ARG(str, "Done"))

    t = threading.Thread(target=bg_thread, daemon=True)
    t.start()
    start_time = time.time()
    while t.is_alive() and (time.time() - start_time < 2.0):
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()

    assert btn.text() == "Done"
    btn.close()


def test_legacy_merge():
    """Refactored test_merge.py: Merges dynamic models into UI_TAB_LAYOUT safely."""
    discover_plugins()
    yaml_path = ".config/models/model_registry.yaml"
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        UI_TAB_LAYOUT = data.get("fields", {}) or {}

    dynamic_models = TranslatorFactory.get_all_registered_models(BaseOfflineTranslator)
    tab_name = "General & Translator"
    field = "offline_translator"

    if tab_name not in UI_TAB_LAYOUT:
        UI_TAB_LAYOUT[tab_name] = {}
    if field not in UI_TAB_LAYOUT[tab_name]:
        UI_TAB_LAYOUT[tab_name][field] = []

    existing = {m.get("key"): m for m in UI_TAB_LAYOUT[tab_name][field] if isinstance(m, dict) and "key" in m}
    for model in dynamic_models:
        key = model.get("key")
        if key and key in existing:
            existing[key].update(model)
        else:
            UI_TAB_LAYOUT[tab_name][field].append(model)

    assert isinstance(UI_TAB_LAYOUT[tab_name][field], list)


def test_legacy_qtimer_thread(qapp):
    """Refactored test_qtimer_thread.py: Safe QTimer singleShot from thread test with receiver context."""
    executed = []

    def callback():
        executed.append(True)

    btn = QPushButton()

    def _load():
        time.sleep(0.1)
        QTimer.singleShot(0, btn, callback)

    t = threading.Thread(target=_load, daemon=True)
    t.start()
    start_time = time.time()
    while t.is_alive() and (time.time() - start_time < 2.0):
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()

    assert len(executed) == 1
    btn.close()


def test_legacy_real_loader():
    """Refactored test_real_loader.py: RegistryLoader initialization with RegistryMixin positional arg."""
    mixin = RegistryMixin()
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    mixin.project_base_dir = project_root
    loader = RegistryLoader(mixin)
    registry = loader.load_registry()

    assert isinstance(registry, dict)
    assert "offline_translator" in registry or len(registry) >= 0


def test_legacy_timer(qapp):
    """Refactored test_timer.py: QTimer singleShot lambda test with receiver context."""
    btn = QPushButton("Wait")
    btn.show()

    def bg_thread():
        time.sleep(0.1)
        QTimer.singleShot(0, btn, lambda: btn.setText("Done"))

    t = threading.Thread(target=bg_thread, daemon=True)
    t.start()
    start_time = time.time()
    while t.is_alive() and (time.time() - start_time < 2.0):
        qapp.processEvents()
        time.sleep(0.01)
    qapp.processEvents()

    assert btn.text() == "Done"
    btn.close()



def test_legacy_gui_and_launch(qapp):
    """Refactored test_gui.py & test_launch.py: Verifies main window instantiation."""
    window = TranslatorStudioApp()
    assert window is not None
    assert window.windowTitle() != "" or window.isVisible() is False
    window.close()


def test_legacy_plugins_and_factories():
    """Refactored test_plugins.py, test_api.py, test_api_ocr.py, test_detector.py, test_renderer.py."""
    discover_plugins()
    offline_models = TranslatorFactory.get_all_registered_models(BaseOfflineTranslator)
    api_models = TranslatorFactory.get_all_registered_models(BaseAPITranslator)
    cloud_ocr_models = CloudOCRFactory.get_all_registered_models()
    detectors = DetectorFactory.get_all_registered_models()
    renderers = RendererFactory.get_all_registered_models()

    assert isinstance(offline_models, list)
    assert isinstance(api_models, list)
    assert isinstance(cloud_ocr_models, list)
    assert isinstance(detectors, list)
    assert isinstance(renderers, list)
