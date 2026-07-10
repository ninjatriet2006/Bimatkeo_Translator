"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.pool_dialog.actions.api_actions
- RESPONSIBILITY: Handle adding, moving, and removing API instances in the dialog's list.
- CALLED BY: app.core.desktop.components.pool_dialog.dialog
- CALLS TO: PySide6.QtWidgets.QMessageBox, app.core.api.manager.infer_ai_provider
- IN = OUT: Manipulates QListWidget items and updates dialog.api_profiles.
=============================================================================
"""
from PySide6.QtWidgets import QMessageBox

def move_item(dialog, offset):
    current_row = dialog.api_list.currentRow()
    if current_row < 0: return
    new_row = current_row + offset
    if 0 <= new_row < dialog.api_list.count():
        item = dialog.api_list.takeItem(current_row)
        dialog.api_list.insertItem(new_row, item)
        dialog.api_list.setCurrentRow(new_row)

def remove_from_pool(dialog):
    current_row = dialog.api_list.currentRow()
    if current_row >= 0:
        dialog.api_list.takeItem(current_row)

def add_existing_to_pool(dialog):
    api_name = dialog.existing_api_combo.currentText()
    if api_name:
        dialog.api_list.addItem(api_name)

def add_new_to_pool(dialog):
    name = dialog.new_api_name.text().strip()
    if not name:
        QMessageBox.warning(dialog, "Error", "API Name cannot be empty.")
        return
        
    if name in dialog.api_profiles:
        QMessageBox.warning(dialog, "Error", f"API Profile '{name}' already exists.")
        return
        
    endpoint = dialog.new_api_endpoint.text().strip()
    if dialog.service == "OCR":
        provider = "gemini_ocr" # OCR currently relies mostly on gemini models or custom, default to gemini_ocr
    else:
        from app.core.api.manager import infer_ai_provider
        provider = infer_ai_provider(endpoint)
    
    profile = {
        "type": "Standalone",
        "service": dialog.service,
        "provider": provider,
        "endpoint": endpoint,
        "model": dialog.new_api_model.currentText().strip(),
        "key": dialog.new_api_key.text().strip()
    }
    
    dialog.api_profiles[name] = profile
    dialog.main_window._save_api_profiles(dialog.api_profiles)
    
    # Update existing combo
    dialog.existing_api_combo.addItem(name)
    
    # Add to list
    dialog.api_list.addItem(name)
    
    # Clear fields
    dialog.new_api_name.clear()
    dialog.new_api_endpoint.clear()
    dialog.new_api_model.clear()
    dialog.new_api_model.addItem("Auto")
    dialog.new_api_model.setCurrentText("Auto")
    dialog.new_api_key.clear()
    
    QMessageBox.information(dialog, "Success", f"New API Profile '{name}' created and added to the pool.")
