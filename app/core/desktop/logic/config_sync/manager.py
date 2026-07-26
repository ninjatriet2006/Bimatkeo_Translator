"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.config_sync.manager
- RESPONSIBILITY: Decoupled manager for online configuration synchronization and updates.
- CALLED BY: app.core.desktop.logic.core_handlers.config_sync, app.core.desktop.main_window
- CALLS TO: app.core.desktop.logic.config_sync.workers.ConfigUpdateWorker
- IN = OUT: Takes config_loader and project_base_dir into __init__, emits PySide6 Signals.
=============================================================================
"""
from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMessageBox
from app.core.desktop.constants import CAT_OFFLINE_MODELS, CAT_API_BASED, CAT_OTHER_ACTIONS
from app.core.desktop.logic.config_sync.workers import ConfigUpdateWorker

class ConfigSyncManager(QObject):
    update_started = Signal(str)
    update_finished = Signal(bool, str)
    log_requested = Signal(str, str)
    configs_reloaded = Signal()

    def __init__(self, config_loader=None, project_base_dir: str = "."):
        super().__init__()
        self.config_loader = config_loader
        self.project_base_dir = project_base_dir

    def trigger_online_config_update(self, key: str, main_window=None):
        mw = main_window
        if mw and getattr(mw, "_config_update_active", False):
            QMessageBox.information(mw, "Đang xử lý", "Một tiến trình cập nhật cấu hình đang chạy, vui lòng đợi.")
            return

        mode = ""
        translator_name = None
        api_key = None

        if key == "target_lang":
            mode = "languages"
            if mw and hasattr(mw, 'log'):
                mw.log("INFO", "Đang cập nhật danh sách ngôn ngữ đích từ LibreTranslate...")
        elif key in ["offline_translator", "ai_translator"]:
            mode = "single_translator"
            if mw and hasattr(mw, 'setting_widgets'):
                combo = mw.setting_widgets.get(key)
                if not combo:
                    return
                translator_name = combo.itemData(combo.currentIndex())
                if not translator_name or translator_name in ["none", "original"]:
                    QMessageBox.information(mw, "Thông tin", f"Bộ dịch '''{translator_name}''' không hỗ trợ cập nhật động.")
                    return
                if hasattr(mw, 'log'):
                    mw.log("INFO", f"Đang cập nhật khả năng dịch cho bộ dịch: {translator_name}...")
        else:
            return

        if mw:
            mw._config_update_active = True
            for k in ['target_lang', 'offline_translator', 'ai_translator']:
                w = mw.setting_widgets.get(k)
                if w:
                    w.setEnabled(False)

        cfg_loader = self.config_loader or getattr(mw, 'config_loader', None)
        worker = ConfigUpdateWorker(cfg_loader, mode, translator_name, api_key)
        if mw:
            mw._config_worker = worker
            worker.finished.connect(lambda s, m: self.handle_config_update_finished(s, m, main_window=mw))
        else:
            worker.finished.connect(self.handle_config_update_finished)
        worker.start()
        self.update_started.emit(key)

    def trigger_all_configs_update(self, main_window=None):
        mw = main_window
        if mw and getattr(mw, "_config_update_active", False):
            QMessageBox.information(mw, "Đang xử lý", "Một tiến trình cập nhật cấu hình đang chạy, vui lòng đợi.")
            return

        if mw:
            reply = QMessageBox.question(
                mw,
                "Xác nhận Cập nhật Tất cả",
                "Bạn có muốn tải về và đồng bộ hóa toàn bộ danh sách ngôn ngữ & năng lực bộ dịch từ Internet không?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

            mw.log("INFO", "Bắt đầu cập nhật toàn bộ cấu hình ngôn ngữ và khả năng dịch...")
            mw._config_update_active = True

            for k in ['target_lang', 'offline_translator', 'ai_translator']:
                w = mw.setting_widgets.get(k)
                if w:
                    w.setEnabled(False)

        cfg_loader = self.config_loader or getattr(mw, 'config_loader', None)
        worker = ConfigUpdateWorker(cfg_loader, "all")
        if mw:
            mw._config_worker = worker
            worker.finished.connect(lambda s, m: self.handle_config_update_finished(s, m, main_window=mw))
        else:
            worker.finished.connect(self.handle_config_update_finished)
        worker.start()
        self.update_started.emit("all")

    def handle_config_update_finished(self, success, message, main_window=None):
        mw = main_window
        if mw:
            mw._config_update_active = False
            for k in ['target_lang', 'offline_translator', 'ai_translator']:
                w = mw.setting_widgets.get(k)
                if w:
                    w.setEnabled(True)

            if success:
                mw.log("SUCCESS", message)
                self.reload_dynamic_configurations(main_window=mw)
                QMessageBox.information(mw, "Cập nhật Thành công", message)
            else:
                mw.log("ERROR", message)
                QMessageBox.warning(mw, "Cập nhật Thất bại", message)

            if hasattr(mw, '_config_worker'):
                del mw._config_worker

        self.update_finished.emit(success, message)

    def reload_dynamic_configurations(self, config_loader=None, main_window=None):
        import app.core.desktop.main_window as mw_module
        mw = main_window
        cfg_loader = config_loader or self.config_loader or getattr(mw, 'config_loader', None)

        if cfg_loader and hasattr(cfg_loader, 'languages') and cfg_loader.languages:
            mw_module.LANGUAGES.clear()
            mw_module.LANGUAGES.update(cfg_loader.languages)

        if cfg_loader and hasattr(cfg_loader, 'translator_groups'):
            offline_list = cfg_loader.translator_groups.get(CAT_OFFLINE_MODELS, [])
            api_list = cfg_loader.translator_groups.get(CAT_API_BASED, [])

            other_list = ["original", "none"]

            mw_module.TRANSLATOR_GROUPS.clear()
            mw_module.TRANSLATOR_GROUPS[CAT_OFFLINE_MODELS] = offline_list
            mw_module.TRANSLATOR_GROUPS[CAT_API_BASED] = api_list
            mw_module.TRANSLATOR_GROUPS[CAT_OTHER_ACTIONS] = other_list

            if mw:
                mw.original_offline_translators = list(offline_list)
                mw.original_ai_translators = list(api_list)

                mw._refresh_combobox_values('target_lang')
                mw._refresh_combobox_values('offline_translator')
                mw._refresh_combobox_values('ai_translator')

        self.configs_reloaded.emit()

