"""
[INTEGRITY NOTES]
Purpose: Handle UI action for deleting an API profile.
Responsibilities:
- Confirm deletion with the user.
- Remove profile from storage.
- Update UI and refresh combo box.
"""
from PySide6.QtWidgets import QMessageBox, QComboBox
from ..config.mapping import get_profile_mapping
from app.core.api_profile.storage.reader import load_api_profiles
from app.core.api_profile.storage.writer import save_api_profiles

def delete_api_profile_generic(main_window, service: str):
    mapping = get_profile_mapping(service)
    name_widget = main_window.setting_widgets.get(mapping['name'])
    if not name_widget:
        return
    combo = name_widget.findChild(QComboBox)
    if not combo:
        return
    profile_name = combo.currentText().strip()
    if not profile_name or profile_name == "--- Select ---":
        return

    reply = QMessageBox.question(
        main_window,
        "Xác nhận xóa hồ sơ",
        f"Bạn có chắc chắn muốn xóa hồ sơ '{profile_name}' không?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    if reply != QMessageBox.StandardButton.Yes:
        return

    profiles = load_api_profiles(main_window)
    if profile_name in profiles:
        del profiles[profile_name]
        save_api_profiles(main_window, profiles)
        
        if hasattr(main_window, 'app_logger'):
            main_window.app_logger.log("SUCCESS", f"Đã xóa hồ sơ '{profile_name}'.")

        filtered_profiles = [name for name, p in profiles.items() if p.get("type", "Standalone") == "Standalone" and p.get("service", "Translator") == service]

        combo.blockSignals(True)
        combo.clear()
        combo.addItem("--- Select ---")
        combo.addItems(filtered_profiles)
        combo.setCurrentText("--- Select ---")
        combo.blockSignals(False)
        
        from .change_action import on_api_profile_changed_generic
        on_api_profile_changed_generic(main_window, "--- Select ---", service)
    else:
        if hasattr(main_window, 'app_logger'):
            main_window.app_logger.log("WARNING", f"Không tìm thấy hồ sơ '{profile_name}' trong cấu hình.")
