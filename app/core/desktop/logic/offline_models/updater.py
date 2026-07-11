"""
[INTEGRITY NOTES]
Purpose: Manage all Model Software UI interactions (Download, check updates, delete).
Responsibilities:
- Provide UI wrapper methods around Model Software Updating.
"""
import os
import shutil
from PySide6.QtWidgets import QMessageBox, QProgressDialog
from PySide6.QtCore import Qt
from app.core.desktop.logic.offline_models.workers import TranslatorSoftwareUpdateWorker

class ModelSoftwareUpdater:
    def __init__(self, main_window):
        self.mw = main_window

    def delete_model_software(self, key: str, model_name: str):
        if not model_name or model_name in ["none", "original"]:
            return
            
        reply = QMessageBox.question(self.mw, "Xác nhận Xóa", f"Bạn có chắc chắn muốn xóa mô hình '{model_name}' không?\nFile tải về sẽ bị gỡ bỏ, bạn sẽ phải tải lại nếu muốn dùng.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        rule = self.mw.config_loader._DEFAULT_CHECKS.get(key, {}).get(model_name, {})
        check_file_path = rule.get("check_file", "")
        
        base_dir = self.mw.project_base_dir
        if check_file_path:
            model_dir = os.path.join(base_dir, os.path.dirname(check_file_path))
            if os.path.exists(model_dir):
                shutil.rmtree(model_dir, ignore_errors=True)
                
        config_dir = os.path.join(base_dir, ".config", "models")
        local_versions_file = os.path.join(config_dir, "local_versions.yaml")
        if os.path.exists(local_versions_file):
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.preserve_quotes = True
            yaml.default_flow_style = False
            with open(local_versions_file, "r", encoding="utf-8") as lf:
                local_versions = yaml.load(lf) or {}
            if key in local_versions and model_name in local_versions[key]:
                del local_versions[key][model_name]
                with open(local_versions_file, "w", encoding="utf-8") as lf:
                    yaml.dump(local_versions, lf)
                    
        QMessageBox.information(self.mw, "Thành công", f"Đã xóa mô hình '{model_name}'.")
        if hasattr(self.mw, '_refresh_combobox_values'):
            self.mw._refresh_combobox_values(key)
        self.mw._update_dynamic_btns(key)

    def trigger_all_models_software_update(self, key: str):
        reply = QMessageBox.question(self.mw, "Cập nhật Hàng loạt", f"Bạn có muốn tự động tải và cập nhật TẤT CẢ mô hình thuộc nhóm '{key}' không?\nQuá trình này có thể tốn nhiều dung lượng và thời gian.", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return
            
        info_title = "In Development"
        info_msg = "Bulk download feature will be implemented in a future update. Please download each model individually for now."
        QMessageBox.information(self.mw, info_title, info_msg)

    def trigger_model_software_update(self, key: str):
        combo = self.mw.setting_widgets.get(key)
        if not combo:
            return
        model_name = combo.itemData(combo.currentIndex())
        if not model_name or model_name in ["none", "original"]:
            QMessageBox.information(self.mw, "Thông tin", f"Bộ dịch '{model_name}' không hỗ trợ cập nhật phần mềm.")
            return
            
        source_url = getattr(self.mw.config_loader, "model_source_map", {}).get(model_name)
        if not source_url:
            if model_name.startswith("tesseract_"):
                lang = model_name.replace("tesseract_", "")
                tess_packages = ["tesseract-ocr"]
                if lang == "mixed" or lang == "all_horizontal":
                    tess_packages.extend(["tesseract-ocr-jpn", "tesseract-ocr-jpn-vert", "tesseract-ocr-chi-sim", "tesseract-ocr-chi-sim-vert", "tesseract-ocr-chi-tra", "tesseract-ocr-chi-tra-vert", "tesseract-ocr-kor", "tesseract-ocr-kor-vert"])
                else:
                    tess_lang = lang.replace("_", "-")
                    tess_packages.append(f"tesseract-ocr-{tess_lang}")
                
                cmd = f"sudo apt-get install {' '.join(tess_packages)}"
                
                msg = QMessageBox(self.mw)
                msg.setWindowTitle("Hướng dẫn cài đặt Tesseract")
                msg.setText(f"Mô hình '{model_name}' yêu cầu phần mềm hệ thống Tesseract OCR.\n\nVui lòng copy câu lệnh sau và dán vào Terminal để cài đặt:")
                msg.setDetailedText(cmd)
                msg.setIcon(QMessageBox.Icon.Information)
                
                copy_btn = msg.addButton("Copy Lệnh", QMessageBox.ButtonRole.ActionRole)
                close_btn = msg.addButton("Đóng", QMessageBox.ButtonRole.RejectRole)
                
                msg.exec()
                
                if msg.clickedButton() == copy_btn:
                    from PySide6.QtGui import QGuiApplication
                    clipboard = QGuiApplication.clipboard()
                    if clipboard:
                        clipboard.setText(cmd)
                        QMessageBox.information(self.mw, "Thành công", "Đã copy câu lệnh vào khay nhớ tạm!")
            else:
                QMessageBox.information(self.mw, "Thông tin", f"Mô hình '{model_name}' không hỗ trợ tính năng tự động tải dữ liệu qua giao diện (có thể là API hoặc phần mềm hệ thống).")
            return

        reply = QMessageBox.question(
            self.mw,
            "Cập nhật Bộ dịch",
            f"Bạn có muốn kiểm tra và tải/cập nhật phiên bản phần mềm hoặc tệp mô hình mới nhất của bộ dịch '{model_name}' không?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.No:
            return

        self.mw.log("INFO", f"Đang kiểm tra cập nhật phần mềm/mô hình cho bộ dịch: {model_name}...")
        
        for k in getattr(self.mw, '_dynamic_btns_map', {}).keys():
            w = self.mw.setting_widgets.get(k)
            if w:
                w.setEnabled(False)

        rule = self.mw.config_loader._DEFAULT_CHECKS.get(key, {}).get(model_name, {})
        check_file_path = rule.get("check_file", "")

        progress_dlg = QProgressDialog(f"Đang kiểm tra cập nhật cho {model_name}...", "Hủy", 0, 100, self.mw)
        progress_dlg.setWindowTitle("Cập nhật Mô hình Dịch")
        progress_dlg.setWindowModality(Qt.WindowModality.WindowModal)
        progress_dlg.setMinimumDuration(0)
        progress_dlg.show()

        self.mw._software_worker = TranslatorSoftwareUpdateWorker(key, model_name, check_file_path)
        progress_dlg.canceled.connect(self.mw._software_worker.terminate)
        
        def on_progress(val, text):
            progress_dlg.setValue(val)
            progress_dlg.setLabelText(text)
            
        def on_finished(success, message):
            progress_dlg.setValue(100)
            progress_dlg.close()
            for k in getattr(self.mw, '_dynamic_btns_map', {}).keys():
                w = self.mw.setting_widgets.get(k)
                if w:
                    w.setEnabled(True)
            if success:
                self.mw.log("SUCCESS", message)
                QMessageBox.information(self.mw, "Cập nhật Hoàn tất", message)
                if hasattr(self.mw, '_refresh_combobox_values'):
                    self.mw._refresh_combobox_values('offline_translator')
                    self.mw._refresh_combobox_values('ai_translator')
                    self.mw._refresh_combobox_values(key)
            else:
                self.mw.log("ERROR", message)
                QMessageBox.warning(self.mw, "Cập nhật Thất bại", message)
            del self.mw._software_worker

        self.mw._software_worker.finished.connect(on_finished, Qt.ConnectionType.QueuedConnection)
        self.mw._software_worker.progress.connect(on_progress, Qt.ConnectionType.QueuedConnection)
        self.mw._software_worker.start()
