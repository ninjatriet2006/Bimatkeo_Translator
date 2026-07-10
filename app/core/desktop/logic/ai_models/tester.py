"""
[INTEGRITY NOTES]
Purpose: Handle testing AI model connections in a background thread.
Responsibilities:
- Retrieve connection credentials.
- Test connection by sending a simple prompt using the selected plugin.
- Emit result signals back to the main thread.
"""
import threading
from PySide6.QtWidgets import QMessageBox

def test_ai_model(main_window, button, combo):
    endpoint = main_window._get_value_from_widget('ai_endpoint', main_window.setting_widgets.get('ai_endpoint'))
    key = main_window._get_value_from_widget('ai_key', main_window.setting_widgets.get('ai_key'))
    
    provider_widget = main_window.setting_widgets.get('ai_translator')
    ai_provider = main_window._get_value_from_widget('ai_translator', provider_widget)
    
    model_name = combo.currentText()
    if not model_name or model_name == "Auto":
        QMessageBox.warning(main_window, "Warning", "Please select a specific model to test (not Auto).")
        return

    if not endpoint and ai_provider != 'gemini':
        main_window.log("WARNING", "No API Endpoint URL provided. Please enter a valid URL.")
        return

    button.setEnabled(False)
    button.setText("...")

    def thread_target():
        from app.core.shared_registry import TranslatorFactory
        try:
            import app.plugins.translator.openai_impl
            import app.plugins.translator.gemini_impl
            import app.plugins.translator.felo_impl
            
            translator = TranslatorFactory.create(ai_provider)
            translator.load_weights({
                "endpoint": endpoint,
                "key": key,
                "model": model_name
            })
            success, msg = translator.test_connection()
            main_window.test_finished_signal.emit(success, msg, button)
        except Exception as e:
            main_window.test_finished_signal.emit(False, str(e), button)

    threading.Thread(target=thread_target, daemon=True).start()

def on_test_finished(main_window, success, message, button):
    button.setEnabled(True)
    button.setText("Test")
    if success:
        QMessageBox.information(main_window, "Test Successful", message)
    else:
        QMessageBox.critical(main_window, "Test Failed", message)
