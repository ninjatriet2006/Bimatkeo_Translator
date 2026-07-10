"""
[INTEGRITY NOTES]
Purpose: Handle fetching AI models from remote APIs in a background thread.
Responsibilities:
- Retrieve endpoint and key configuration.
- Launch a daemon thread to fetch models.
- Emit signals back to the main thread upon completion.
- Handle UI updates related to fetched models.
"""
import threading
from PySide6.QtWidgets import QMessageBox, QComboBox

def fetch_ai_models(main_window, button):
    endpoint = main_window._get_value_from_widget('ai_endpoint', main_window.setting_widgets.get('ai_endpoint'))
    key = main_window._get_value_from_widget('ai_key', main_window.setting_widgets.get('ai_key'))
    
    provider_widget = main_window.setting_widgets.get('ai_translator')
    ai_provider = main_window._get_value_from_widget('ai_translator', provider_widget)

    if not endpoint and ai_provider != 'gemini':
        main_window.log("WARNING", "No API Endpoint URL provided. Please enter a valid URL.")
        return

    button.setEnabled(False)
    button.setText("...")

    def thread_target():
        from app.core.api.manager import fetch_remote_ai_models
        try:
            models = fetch_remote_ai_models(endpoint, key, ai_provider)
            main_window.models_fetched_signal.emit(models, button)
        except Exception as e:
            err_msg = str(e)
            print(f"[ERROR] Failed to fetch models: {err_msg}")
            main_window.log("ERROR", f"Failed to fetch models: {err_msg}")
        finally:
            main_window.fetch_finished_signal.emit(button)

    threading.Thread(target=thread_target, daemon=True).start()

def show_fetched_models(main_window, models, button):
    if not models:
        QMessageBox.warning(main_window, "Warning", "Failed to fetch models or no models found.")
        return
        
    model_widget = main_window.setting_widgets.get('ai_model')
    if model_widget:
        combo = model_widget.findChild(QComboBox)
        if combo:
            current_text = combo.currentText()
            combo.blockSignals(True)
            combo.clear()
            combo.addItem("Auto")
            combo.addItems(models)
            
            if current_text and (current_text in models or current_text == "Auto"):
                combo.setCurrentText(current_text)
            else:
                combo.setCurrentText("Auto")
                main_window.current_settings['ai_model'] = "Auto"
                
            combo.blockSignals(False)
            main_window._on_setting_changed('ai_model')
            combo.showPopup()

def select_fetched_model(main_window, model_name, entry_widget):
    entry_widget.setText(model_name)
    main_window._on_setting_changed('ai_model')

def on_fetch_finished(main_window, button):
    button.setEnabled(True)
    button.setText("Fetch")
