"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.pool_dialog.actions.pool_actions
- RESPONSIBILITY: Handle CRUD operations for API pools in the dialog.
- CALLED BY: app.core.desktop.components.pool_dialog.dialog
- CALLS TO: PySide6.QtWidgets.QMessageBox, PySide6.QtWidgets.QInputDialog
- IN = OUT: Manipulates the dialog's `pools` dict and saves it via `main_window`.
=============================================================================
"""
from PySide6.QtWidgets import QMessageBox

def _get_str(dialog, key, default):
    if hasattr(dialog, 'main_window') and hasattr(dialog.main_window, 'get_string'):
        val = dialog.main_window.get_string(key)
        if val != key:
            return val
    return default

def refresh_pool_selector(dialog):
    dialog.pool_combo.blockSignals(True)
    dialog.pool_combo.clear()
    dialog.pool_combo.addItem("--- Select ---")
    dialog.pool_combo.addItems(list(dialog.pools.keys()))
    dialog.pool_combo.blockSignals(False)
    if dialog.pool_combo.count() > 1:
        dialog.pool_combo.setCurrentIndex(1)

def on_pool_changed(dialog, pool_name):
    dialog.api_list.clear()
    if pool_name and pool_name != "--- Select ---" and pool_name in dialog.pools:
        for api_name in dialog.pools[pool_name]:
            dialog.api_list.addItem(api_name)

def save_pool(dialog):
    pool_name = dialog.pool_combo.currentText().strip()
    if not pool_name or pool_name == "--- Select ---":
        title = _get_str(dialog, "ui_error", "Error")
        msg = _get_str(dialog, "ui_msg_select_valid_pool", "Please select a valid pool to save.")
        QMessageBox.warning(dialog, title, msg)
        return
        
    apis = []
    for i in range(dialog.api_list.count()):
        apis.append(dialog.api_list.item(i).text())
        
    dialog.pools[pool_name] = apis
    dialog.main_window._save_pool_profiles(dialog.pools, dialog.service)
    
    refresh_pool_selector(dialog)
    dialog.pool_combo.setCurrentText(pool_name)
    title_suc = _get_str(dialog, "ui_success", "Success")
    msg_suc = _get_str(dialog, "ui_msg_pool_saved", "Pool '{pool_name}' saved.").format(pool_name=pool_name)
    QMessageBox.information(dialog, title_suc, msg_suc)

def create_new_pool(dialog):
    import PySide6.QtWidgets as QtWidgets
    title = _get_str(dialog, "ui_title_new_pool", "New Pool")
    msg = _get_str(dialog, "ui_msg_enter_new_pool", "Enter new Pool Name:")
    name, ok = QtWidgets.QInputDialog.getText(dialog, title, msg)
    if ok and name.strip():
        name = name.strip()
        if name in dialog.pools:
            err_title = _get_str(dialog, "ui_error", "Error")
            err_msg = _get_str(dialog, "ui_msg_pool_exists", "Pool '{name}' already exists.").format(name=name)
            QMessageBox.warning(dialog, err_title, err_msg)
            return
        dialog.pools[name] = []
        dialog.main_window._save_pool_profiles(dialog.pools, dialog.service)
        refresh_pool_selector(dialog)
        dialog.pool_combo.setCurrentText(name)

def delete_pool(dialog):
    pool_name = dialog.pool_combo.currentText().strip()
    if pool_name and pool_name != "--- Select ---" and pool_name in dialog.pools:
        title = _get_str(dialog, "ui_title_confirm_delete", "Confirm Delete")
        msg = _get_str(dialog, "ui_msg_confirm_delete_pool", "Are you sure you want to delete pool '{pool_name}'?").format(pool_name=pool_name)
        reply = QMessageBox.question(dialog, title, msg,
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            del dialog.pools[pool_name]
            dialog.main_window._save_pool_profiles(dialog.pools, dialog.service)
            refresh_pool_selector(dialog)
            dialog.api_list.clear()
