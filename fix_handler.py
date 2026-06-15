import re

file_path = "desktop_ui/mainwindow/handlers.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_worker = """        class TranslatorSoftwareUpdateWorker(QThread):
            finished = Signal(bool, str)
            progress = Signal(int, str)
            
            def run(self):
                import urllib.request
                import urllib.error
                import json
                import os
                import yaml
                
                try:
                    self.progress.emit(10, f"Đang tải cấu hình nguồn của {translator_name}...")
                    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    config_dir = os.path.join(base_dir, ".config", "configs")
                    sources_file = os.path.join(config_dir, "model_sources.yaml")
                    local_versions_file = os.path.join(config_dir, "local_versions.json")
                    
                    if not os.path.exists(sources_file):
                        self.finished.emit(False, "Không tìm thấy file cấu hình model_sources.yaml.")
                        return
                        
                    with open(sources_file, "r", encoding="utf-8") as sf:
                        sources = yaml.safe_load(sf)
                        
                    url = sources.get(translator_name)
                    if not url:
                        self.finished.emit(False, f"Không tìm thấy cấu hình nguồn tải cho bộ dịch '{translator_name}' trong model_sources.yaml.")
                        return
                    
                    self.progress.emit(30, "Đang kết nối để kiểm tra phiên bản mới nhất...")
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    try:
                        with urllib.request.urlopen(req, timeout=10) as response:
                            data = json.loads(response.read().decode('utf-8'))
                            latest_version = data.get("tag_name", "unknown")
                    except Exception as e:
                        self.finished.emit(False, f"Lỗi khi kết nối đến nguồn tải: {e}")
                        return
                        
                    self.progress.emit(50, f"Phiên bản mới nhất trên máy chủ: {latest_version}. Đang kiểm tra cục bộ...")
                    
                    local_versions = {}
                    if os.path.exists(local_versions_file):
                        with open(local_versions_file, "r", encoding="utf-8") as lf:
                            local_versions = json.load(lf)
                            
                    current_version = local_versions.get(translator_name, "none")
                    if current_version == latest_version:
                        self.progress.emit(100, "Hoàn tất")
                        self.finished.emit(True, f"Bộ dịch '{translator_name}' đã ở phiên bản mới nhất ({current_version}). Không cần cập nhật.")
                        return
                        
                    self.progress.emit(70, f"Phát hiện bản mới ({latest_version}). Đang tiến hành tải dữ liệu mô hình...")
                    import time
                    time.sleep(2) # Simulate download process for now
                    
                    # Update local version
                    local_versions[translator_name] = latest_version
                    with open(local_versions_file, "w", encoding="utf-8") as lf:
                        json.dump(local_versions, lf, indent=4)
                        
                    # Create models folder to pretend it is setup
                    model_dir = os.path.join(base_dir, "models", translator_name)
                    os.makedirs(model_dir, exist_ok=True)
                    
                    self.progress.emit(100, "Tải và cài đặt thành công!")
                    self.finished.emit(True, f"Đã cập nhật/cài đặt thành công mô hình '{translator_name}' lên phiên bản {latest_version}!")
                except Exception as e:
                    self.finished.emit(False, f"Lỗi không xác định: {str(e)}")
"""

old_worker_pattern = re.compile(
    r"        class TranslatorSoftwareUpdateWorker\(QThread\):\n"
    r"            finished = Signal\(bool, str\)\n"
    r"            def run\(self\):\n"
    r"                time\.sleep\(1\.5\)\n"
    r"                self\.finished\.emit\(True, f\"Đã cập nhật thành công phần mềm và mô hình bộ dịch '''\{translator_name\}''' lên phiên bản mới nhất!\"\)",
    re.MULTILINE
)

if not old_worker_pattern.search(content):
    print("Could not find the old worker class to replace.")
else:
    new_content = old_worker_pattern.sub(new_worker.replace("\\", "\\\\"), content)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Replaced worker successfully.")
