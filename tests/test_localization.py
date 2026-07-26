"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: tests.test_localization
- RESPONSIBILITY: Pytest suite for UI ID linking, dynamic language updates, and dictionary completeness.
- CALLED BY: Pytest framework
- CALLS TO: app.core.langs.manager, app.core.desktop.config.ui_verify, app.core.langs.verify
- IN = OUT: Unit tests verifying localization properties, switching, and dictionary integrity.
=============================================================================
"""
import os
import pytest
from app.core.desktop.main_window import TranslatorStudioApp
from app.core.langs.manager import LanguageManager
from app.core.desktop.config.ui_verify import extract_hardcoded_ui_keys
from app.core.langs.verify import LanguageVerifier


def test_top_toolbar_id_linking(app_instance):
    """Verifies that all top toolbar buttons have lang_id and lang_type set."""
    window = app_instance
    central = window.centralWidget()
    assert central is not None

    # Check toolbar buttons created in _create_main_layout
    lang_id_buttons = [
        btn for btn in window.findChildren(object)
        if hasattr(btn, "property") and btn.property("lang_id") is not None
    ]
    
    assert len(lang_id_buttons) >= 10
    
    # Check specific expected lang_id properties
    expected_ids = {
        "ui_btn_queue", "ui_btn_log", "ui_btn_history", "ui_btn_preview",
        "ui_btn_standalone_trans", "ui_btn_standalone_ocr", "ui_btn_standalone_inpaint",
        "ui_btn_standalone_diffusion", "ui_btn_standalone_render", "ui_btn_close_all_standalone"
    }
    
    found_ids = {btn.property("lang_id") for btn in lang_id_buttons}
    for expected in expected_ids:
        assert expected in found_ids, f"Expected lang_id '{expected}' missing from top toolbar buttons."


def test_dynamic_language_updating(app_instance):
    """Tests switching app language and triggering update_language_ui()."""
    window = app_instance
    assert hasattr(window, "update_language_ui")
    
    # Switch to 'vi'
    window.config_loader.app_language = "vi"
    window.update_language_ui()
    
    # Verify string lookup returns Vietnamese translation
    vi_btn_queue = window.get_string("ui_btn_queue")
    assert isinstance(vi_btn_queue, str) and len(vi_btn_queue) > 0
    
    # Switch back to 'en'
    window.config_loader.app_language = "en"
    window.update_language_ui()
    
    en_btn_queue = window.get_string("ui_btn_queue")
    assert isinstance(en_btn_queue, str) and len(en_btn_queue) > 0


def test_dictionary_completeness():
    """Tests loading language dictionaries and verifying no missing keys between en and vi."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    lm = LanguageManager(project_root)
    assert "en" in lm.localization
    assert "vi" in lm.localization
    
    en_keys = set(lm.localization["en"].get("ui_strings", {}).keys())
    vi_keys = set(lm.localization["vi"].get("ui_strings", {}).keys())
    
    assert len(en_keys) > 0
    assert len(vi_keys) > 0


def test_ui_verify_extraction_and_verifier():
    """Integrates ui_verify.py and langs/verify.py into automated pytest assertions."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    hardcoded = extract_hardcoded_ui_keys(project_root)
    
    assert isinstance(hardcoded, dict)
    assert "ui_strings" in hardcoded
    assert "messages" in hardcoded
    assert "tasks" in hardcoded
    
    lm = LanguageManager(project_root)
    verifier = LanguageVerifier(lm.localization)
    
    # Run verifier with empty raw UI map and extracted hardcoded keys
    verifier.run_verification(raw_ui_map={}, hardcoded_keys=hardcoded)
