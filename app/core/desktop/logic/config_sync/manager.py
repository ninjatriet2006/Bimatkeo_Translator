"""
[INTEGRITY NOTES]
Purpose: Handle UI interactions for downloading configuration from APIs (Config Sync).
Responsibilities:
- Trigger ConfigUpdateWorker for full update or single update.
- Reload UI elements dynamically after fetching.
"""
from PySide6.QtWidgets import QMessageBox
from app.core.desktop.constants import CAT_OFFLINE_MODELS, CAT_API_BASED, CAT_OTHER_ACTIONS
from app.core.desktop.logic.config_sync.workers import ConfigUpdateWorker

class ConfigSyncManager:
    def __init__(self, main_window):
        self.mw = main_window

    def trigger_online_config_update(self, key: str):
        if getattr(self.mw, "_config_update_active", False):
            QMessageBox.information(self.mw, "Đang xử lý", "Một tiến trình cập nhật cấu hình đang chạy, vui lòng đợi.")
            return

        mode = ""
        translator_name = None
        api_key = None

        if key == "target_lang":
            mode = "languages"
            self.mw.log("INFO", "Đang cập nhật danh sách ngôn ngữ đích từ LibreTranslate...")
        elif key in ["offline_translator", "ai_translator"]:
            mode = "single_translator"
            combo = self.mw.setting_widgets.get(key)
            if not combo:
                return
            translator_name = combo.itemData(combo.currentIndex())
            if not translator_name or translator_name in ["none", "original"]:
                QMessageBox.information(self.mw, "Thông tin", f"Bộ dịch '''{translator_name}''' không hỗ trợ cập nhật động.")
                return
                
            self.mw.log("INFO", f"Đang cập nhật khả năng dịch cho bộ dịch: {translator_name}...")
        else:
            return

        self.mw._config_update_active = True
        
        for k in ['target_lang', 'offline_translator', 'ai_translator']:
            w = self.mw.setting_widgets.get(k)
            if w:
                w.setEnabled(False)

        self.mw._config_worker = ConfigUpdateWorker(self.mw.config_loader, mode, translator_name, api_key)
        self.mw._config_worker.finished.connect(self.handle_config_update_finished)
        self.mw._config_worker.start()

    def trigger_all_configs_update(self):
        if getattr(self.mw, "_config_update_active", False):
            QMessageBox.information(self.mw, "Đang xử lý", "Một tiến trình cập nhật cấu hình đang chạy, vui lòng đợi.")
            return

        reply = QMessageBox.question(
            self.mw,
            "Xác nhận Cập nhật Tất cả",
            "Bạn có muốn tải về và đồng bộ hóa toàn bộ danh sách ngôn ngữ & năng lực bộ dịch từ Internet không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.mw.log("INFO", "Bắt đầu cập nhật toàn bộ cấu hình ngôn ngữ và khả năng dịch...")
        self.mw._config_update_active = True

        for k in ['target_lang', 'offline_translator', 'ai_translator']:
            w = self.mw.setting_widgets.get(k)
            if w:
                w.setEnabled(False)

        self.mw._config_worker = ConfigUpdateWorker(self.mw.config_loader, "all")
        self.mw._config_worker.finished.connect(self.handle_config_update_finished)
        self.mw._config_worker.start()

    def handle_config_update_finished(self, success, message):
        self.mw._config_update_active = False
        for k in ['target_lang', 'offline_translator', 'ai_translator']:
            w = self.mw.setting_widgets.get(k)
            if w:
                w.setEnabled(True)
        
        if success:
            self.mw.log("SUCCESS", message)
            self.reload_dynamic_configurations()
            QMessageBox.information(self.mw, "Cập nhật Thành công", message)
        else:
            self.mw.log("ERROR", message)
            QMessageBox.warning(self.mw, "Cập nhật Thất bại", message)
            
        if hasattr(self.mw, '_config_worker'):
            del self.mw._config_worker

    def reload_dynamic_configurations(self):
        import app.core.desktop.main_window as mw
        
        if hasattr(self.mw.config_loader, 'languages') and self.mw.config_loader.languages:
            mw.LANGUAGES.clear()
            mw.LANGUAGES.update(self.mw.config_loader.languages)
            
        offline_info = self.mw.config_loader.full_config_data.get('offline_translator')
        ai_info = self.mw.config_loader.full_config_data.get('ai_translator')
        
        offline_list = offline_info.get('values', []) if offline_info else []
        api_list = ai_info.get('values', []) if ai_info else []
        other_list = ["original", "none"]
        
        mw.TRANSLATOR_GROUPS.clear()
        mw.TRANSLATOR_GROUPS[CAT_OFFLINE_MODELS] = offline_list
        mw.TRANSLATOR_GROUPS[CAT_API_BASED] = api_list
        mw.TRANSLATOR_GROUPS[CAT_OTHER_ACTIONS] = other_list
        
        self.mw.original_offline_translators = list(offline_list)
        self.mw.original_ai_translators = list(api_list)
        
        self.mw._refresh_combobox_values('target_lang')
        self.mw._refresh_combobox_values('offline_translator')
        self.mw._refresh_combobox_values('ai_translator')
