"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.pool_dialog.actions.fetch_actions
- RESPONSIBILITY: Fetch models from endpoints in background thread.
- CALLED BY: app.core.desktop.components.pool_dialog.dialog
- CALLS TO: PySide6.QtWidgets.QMessageBox, app.core.api.manager.fetch_remote_ai_models
- IN = OUT: Uses dialog text fields to make API calls, emits signals, updates combo box.
=============================================================================
"""
import threading
from PySide6.QtWidgets import QMessageBox

def fetch_models(dialog):
    endpoint = dialog.new_api_endpoint.text().strip()
    key = dialog.new_api_key.text().strip()
    from app.core.api.manager import infer_ai_provider
    ai_provider = infer_ai_provider(endpoint)
    
    dialog.fetch_models_btn.setEnabled(False)
    dialog.fetch_models_btn.setText("...")

    def thread_target():
        from app.core.api.manager import fetch_remote_ai_models
        try:
            models = fetch_remote_ai_models(endpoint, key, ai_provider)
            dialog.models_fetched_signal.emit(models)
        except Exception as e:
            print(f"[ERROR] Failed to fetch models: {e}")
            dialog.models_fetched_signal.emit([])
        finally:
            dialog.fetch_finished_signal.emit()

    threading.Thread(target=thread_target, daemon=True).start()

def show_fetched_models(dialog, models):
    if not models:
        QMessageBox.warning(dialog, "Warning", "Failed to fetch models or no models found.")
        return
        
    current_text = dialog.new_api_model.currentText()
    dialog.new_api_model.blockSignals(True)
    dialog.new_api_model.clear()
    dialog.new_api_model.addItem("Auto")
    dialog.new_api_model.addItems(models)
    
    if current_text and (current_text in models or current_text == "Auto"):
        dialog.new_api_model.setCurrentText(current_text)
    else:
        dialog.new_api_model.setCurrentText("Auto")
    dialog.new_api_model.blockSignals(False)

def on_fetch_finished(dialog):
    dialog.fetch_models_btn.setEnabled(True)
    dialog.fetch_models_btn.setText("Fetch")
