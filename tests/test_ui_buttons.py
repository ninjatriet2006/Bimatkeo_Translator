"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.test_ui_buttons
- RESPONSIBILITY: Pytest suite testing top toolbar buttons, standalone widgets, font install dialog, and preview panels.
- CALLED BY: Pytest framework
- CALLS TO: app.core.desktop.main_window, app.core.desktop.components.standalone.*
- IN = OUT: Unit tests verifying UI element creation, button actions, and dialog instantiation without errors.
=============================================================================
"""
import pytest
from PySide6.QtWidgets import QPushButton
from app.core.desktop.main_window import TranslatorStudioApp
from app.core.desktop.components.standalone.translator_widget import TranslatorStandaloneWidget
from app.core.desktop.components.standalone.ocr_widget import OCRStandaloneWidget
from app.core.desktop.components.standalone.inpaint_widget import InpaintStandaloneWidget
from app.core.desktop.components.standalone.diffusion_widget import DiffusionStandaloneWidget
from app.core.desktop.components.standalone.render_widget import RenderStandaloneWidget
from app.core.desktop.components.widgets_helper import SearchableFontInstallDialog


def test_top_toolbar_button_actions(app_instance):
    """Tests clicking auxiliary window buttons and closing standalones."""
    window = app_instance

    # Open auxiliary windows
    window._show_standalone_window(window.queue_window)
    assert window.queue_window.isVisible() is True

    window._show_standalone_window(window.log_window)
    assert window.log_window.isVisible() is True

    window._show_standalone_window(window.history_window)
    assert window.history_window.isVisible() is True

    window._show_standalone_window(window.preview_window)
    assert window.preview_window.isVisible() is True

    # Close standalones call
    window.close_all_standalones()


def test_standalone_widgets_instantiation(qapp):
    """Tests instantiating standalone widgets directly."""
    w_trans = TranslatorStandaloneWidget()
    assert w_trans is not None

    w_ocr = OCRStandaloneWidget()
    assert w_ocr is not None

    w_inpaint = InpaintStandaloneWidget()
    assert w_inpaint is not None

    w_diffusion = DiffusionStandaloneWidget()
    assert w_diffusion is not None

    w_render = RenderStandaloneWidget()
    assert w_render is not None

    w_trans.close()
    w_ocr.close()
    w_inpaint.close()
    w_diffusion.close()
    w_render.close()


def test_font_install_dialog(qapp):
    """Tests SearchableFontInstallDialog creation and filter functionality."""
    fonts = ["Roboto", "Comic Neue", "Bangers", "Noto Sans"]
    dialog = SearchableFontInstallDialog(fonts, default_font="Roboto")
    assert dialog is not None

    # Filter test
    dialog.search_edit.setText("Bangers")
    dialog.filter_fonts("Bangers")
    visible_items = [
        dialog.list_widget.item(i)
        for i in range(dialog.list_widget.count())
        if not dialog.list_widget.item(i).isHidden()
    ]
    assert len(visible_items) == 1
    assert visible_items[0].text() == "Bangers"
    dialog.close()


def test_preview_tester_and_inspector_panel(app_instance):
    """Tests preview tester window and inspector panel initialization."""
    window = app_instance
    assert hasattr(window, "preview_window")
    assert window.preview_window is not None
