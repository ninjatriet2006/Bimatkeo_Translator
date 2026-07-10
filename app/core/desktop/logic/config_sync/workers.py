"""
[INTEGRITY NOTES]
Purpose: Provide QThread worker for downloading latest languages from APIs.
"""
from PySide6.QtCore import QThread, Signal

class ConfigUpdateWorker(QThread):
    finished = Signal(bool, str)
    
    def __init__(self, config_loader, mode, translator_name=None, api_key=None):
        super().__init__()
        self.config_loader = config_loader
        self.mode = mode
        self.translator_name = translator_name
        self.api_key = api_key
        
    def run(self):
        try:
            if self.mode == "all":
                try:
                    langs_data = self.config_loader.fetch_online_languages_libretranslate()
                except Exception:
                    try:
                        langs_data = self.config_loader.fetch_online_languages_lingva()
                    except Exception as e:
                        self.finished.emit(False, f"Lỗi kết nối mạng: Không tải được danh sách ngôn ngữ từ LibreTranslate/Lingva: {e}")
                        return
                
                success = self.config_loader.save_languages_config(langs_data)
                if success:
                    self.finished.emit(True, "Đã cập nhật thành công tất cả cấu hình ngôn ngữ & bộ dịch từ Internet!")
                else:
                    self.finished.emit(False, "Lỗi khi lưu cấu hình ngôn ngữ.")
                    
            elif self.mode == "languages":
                try:
                    langs_data = self.config_loader.fetch_online_languages_libretranslate()
                except Exception:
                    try:
                        langs_data = self.config_loader.fetch_online_languages_lingva()
                    except Exception as e:
                        self.finished.emit(False, f"Lỗi kết nối mạng: Không tải được danh sách ngôn ngữ: {e}")
                        return
                
                success = self.config_loader.save_languages_config(langs_data)
                if success:
                    self.finished.emit(True, "Đã cập nhật thành công danh sách ngôn ngữ đích!")
                else:
                    self.finished.emit(False, "Lỗi khi lưu danh sách ngôn ngữ mới.")
                    
            elif self.mode == "single_translator":
                success, msg = self.config_loader.update_single_translator_capabilities(
                    self.translator_name, self.api_key
                )
                self.finished.emit(success, msg)
        except Exception as e:
            self.finished.emit(False, f"Lỗi trong quá trình cập nhật cấu hình: {e}")
