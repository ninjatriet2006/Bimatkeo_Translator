"""
[INTEGRITY NOTES]
Purpose: Handle Model Software downloading and deleting in the background.
Responsibilities:
- Provide QThread class for updating translator software/weights.
"""
import os
import sys
import json
import urllib.request
from PySide6.QtCore import QThread, Signal

class TranslatorSoftwareUpdateWorker(QThread):
    finished = Signal(bool, str)
    progress = Signal(int, str)
    
    def __init__(self, key, model_name, check_file_path):
        super().__init__()
        self.key = key
        self.model_name = model_name
        self.check_file_path = check_file_path
        
    def run(self):
        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        
        try:
            self.progress.emit(10, f"Đang tải cấu hình nguồn của {self.model_name}...")
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
            config_dir = os.path.join(base_dir, ".config", "models")
            local_versions_file = os.path.join(config_dir, "local_versions.yaml")
            
            if self.model_name in ["sd_1_5", "sd_nsfw"]:
                try:
                    if base_dir not in sys.path:
                        sys.path.insert(0, base_dir)
                        
                    from app.core.hugging_face import HuggingFaceManager
                    hf_manager = HuggingFaceManager()
                    
                    repo_id = "runwayml/stable-diffusion-v1-5" if self.model_name == "sd_1_5" else "Kernel/sd-nsfw"
                    hf_manager.download_diffusers(repo_id, progress_callback=self.progress.emit)
                    
                    latest_ver = hf_manager.check_version(repo_id)
                    hf_manager.update_local_version(local_versions_file, self.key, self.model_name, latest_ver)
                        
                    self.finished.emit(True, f"Đã tải xong Base Model: {self.model_name}.")
                    return
                except Exception as e:
                    self.finished.emit(False, f"Lỗi khi tải Base Model: {e}")
                    return
            
            from app.core.downloader import ModelDownloader
            url = ModelDownloader.get_source_url_from_registry(self.key, self.model_name)
            
            if not url:
                self.finished.emit(False, f"Không tìm thấy cấu hình nguồn tải (thuộc tính 'source') cho '{self.model_name}'.")
                return
            
            self.progress.emit(30, "Đang kiểm tra kết nối nguồn tải...")
            
            is_direct_archive = False
            is_direct_file = False
            is_huggingface = False
            
            if url.startswith('hf://'):
                is_huggingface = True
                hf_url_parts = url[5:].split('@', 1)
                repo_id = hf_url_parts[0]
                hf_specific_file = hf_url_parts[1] if len(hf_url_parts) > 1 else None
                
                if base_dir not in sys.path:
                    sys.path.insert(0, base_dir)
                from app.core.hugging_face import HuggingFaceManager
                hf_manager = HuggingFaceManager()
                
                try:
                    self.progress.emit(35, f"Đang kiểm tra phiên bản trên HuggingFace cho {repo_id}...")
                    latest_version = hf_manager.check_version(repo_id)
                except Exception as e:
                    self.finished.emit(False, f"Lỗi kiểm tra phiên bản HF: {e}")
                    return
                zipball_url = ""
            elif url.lower().endswith(('.zip', '.tar.gz', '.tar')):
                is_direct_archive = True
                latest_version = "latest_direct"
                zipball_url = url
            elif url.lower().endswith(('.onnx', '.pth', '.ckpt', '.bin', '.pt')):
                is_direct_file = True
                latest_version = "latest_direct"
                file_url = url
                zipball_url = ""
            else:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                try:
                    with urllib.request.urlopen(req, timeout=10) as response:
                        data = json.loads(response.read().decode('utf-8'))
                        latest_version = data.get("tag_name", "unknown")
                        zipball_url = data.get("zipball_url", "")
                except Exception as e:
                    self.finished.emit(False, f"Lỗi khi kết nối đến nguồn tải (API): {e}")
                    return
                
            self.progress.emit(50, f"Phiên bản mới nhất trên máy chủ: {latest_version}. Đang kiểm tra cục bộ...")
            
            local_versions = {}
            if os.path.exists(local_versions_file):
                with open(local_versions_file, "r", encoding="utf-8") as lf:
                    local_versions = yaml.load(lf) or {}
                    
            current_version = local_versions.get(self.key, {}).get(self.model_name, "none")
            
            needs_update = True
            if current_version == latest_version:
                if self.check_file_path:
                    full_check_path = os.path.join(base_dir, self.check_file_path)
                    if os.path.exists(full_check_path):
                        needs_update = False
                else:
                    needs_update = False
                    
            if not needs_update:
                self.progress.emit(100, "Hoàn tất")
                self.finished.emit(True, f"Bộ dịch '{self.model_name}' đã ở phiên bản mới nhất ({current_version}) và đã được cài đặt. Không cần cập nhật.")
                return
                
            self.progress.emit(70, f"Đang tiến hành lấy danh sách file từ {url}...")
            
            if is_huggingface:
                try:
                    if self.check_file_path:
                        model_dir = os.path.join(base_dir, os.path.dirname(self.check_file_path))
                    else:
                        model_dir = os.path.join(base_dir, "models", "Offline Translator", self.model_name)
                    
                    hf_manager.download(repo_id, model_dir, hf_specific_file, progress_callback=self.progress.emit)
                except Exception as e:
                    self.finished.emit(False, f"Lỗi khi tải từ HuggingFace: {e}")
                    return
                    
            elif is_direct_file:
                try:
                    self.progress.emit(70, f"Đang tiến hành tải file từ {file_url}...")
                    req_file = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_file, timeout=600) as response:
                        total_size = int(response.info().get('Content-Length', -1))
                        
                        if self.check_file_path:
                            model_dir = os.path.join(base_dir, os.path.dirname(self.check_file_path))
                            local_path = os.path.join(base_dir, self.check_file_path)
                        else:
                            model_dir = os.path.join(base_dir, "models", "Unknown", self.model_name)
                            import urllib.parse
                            filename = os.path.basename(urllib.parse.urlparse(file_url).path)
                            if not filename: filename = "model.bin"
                            local_path = os.path.join(model_dir, filename)
                            
                        os.makedirs(model_dir, exist_ok=True)
                        
                        chunk_size = 1024 * 1024
                        downloaded = 0
                        
                        with open(local_path, "wb") as f:
                            while True:
                                chunk = response.read(chunk_size)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded += len(chunk)
                                if total_size > 0:
                                    progress_percent = 70 + int((downloaded / total_size) * 20)
                                    if downloaded % (2 * 1024 * 1024) < chunk_size:
                                        self.progress.emit(progress_percent, f"Đang tải: {downloaded//(1024*1024)}MB / {total_size//(1024*1024)}MB...")
                except Exception as e:
                    self.finished.emit(False, f"Lỗi khi tải trực tiếp: {e}")
                    return
                    
            elif zipball_url:
                try:
                    self.progress.emit(70, f"Đang tiến hành tải dữ liệu từ {zipball_url}...")
                    req_zip = urllib.request.Request(zipball_url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req_zip, timeout=600) as response:
                        import zipfile, tarfile, shutil, tempfile
                        
                        total_size = int(response.info().get('Content-Length', -1))
                        fd, temp_path = tempfile.mkstemp(suffix=".zip")
                        os.close(fd)
                        
                        chunk_size = 1024 * 1024
                        downloaded = 0
                        
                        with open(temp_path, "wb") as f:
                            while True:
                                chunk = response.read(chunk_size)
                                if not chunk:
                                    break
                                f.write(chunk)
                                downloaded += len(chunk)
                                
                                if total_size > 0:
                                    progress_percent = 70 + int((downloaded / total_size) * 20)
                                    if downloaded % (2 * 1024 * 1024) < chunk_size:
                                        self.progress.emit(progress_percent, f"Đang tải: {downloaded//(1024*1024)}MB / {total_size//(1024*1024)}MB...")
                        
                        self.progress.emit(90, "Đang giải nén dữ liệu...")
                        
                        if self.check_file_path:
                            model_dir = os.path.join(base_dir, os.path.dirname(self.check_file_path))
                        else:
                            model_dir = os.path.join(base_dir, "models", "Unknown", self.model_name)
                        os.makedirs(model_dir, exist_ok=True)
                        
                        if zipball_url.lower().endswith('.tar.gz'):
                            with tarfile.open(temp_path, mode="r:gz") as tar_ref:
                                tar_ref.extractall(model_dir)
                        else:
                            with zipfile.ZipFile(temp_path, 'r') as zip_ref:
                                zip_ref.extractall(model_dir)
                                
                        os.remove(temp_path)
                                
                        items = os.listdir(model_dir)
                        if len(items) == 1:
                            single_item_path = os.path.join(model_dir, items[0])
                            if os.path.isdir(single_item_path):
                                for sub_item in os.listdir(single_item_path):
                                    shutil.move(os.path.join(single_item_path, sub_item), os.path.join(model_dir, sub_item))
                                os.rmdir(single_item_path)

                except Exception as e:
                    self.finished.emit(False, f"Lỗi khi tải hoặc giải nén mã nguồn: {e}")
                    return
            else:
                self.finished.emit(False, "Không tìm thấy đường dẫn tải zipball_url.")
                return

            if is_huggingface:
                hf_manager.update_local_version(local_versions_file, self.key, self.model_name, latest_version)
            else:
                local_versions = {}
                if os.path.exists(local_versions_file):
                    with open(local_versions_file, "r", encoding="utf-8") as lf:
                        local_versions = yaml.load(lf) or {}
                if self.key not in local_versions:
                    local_versions[self.key] = {}
                local_versions[self.key][self.model_name] = latest_version
                with open(local_versions_file, "w", encoding="utf-8") as lf:
                    yaml.dump(local_versions, lf)
                
            if self.check_file_path:
                model_dir = os.path.join(base_dir, os.path.dirname(self.check_file_path))
            else:
                model_dir = os.path.join(base_dir, "models", "Unknown", self.model_name)
                
            os.makedirs(model_dir, exist_ok=True)
            
            self.progress.emit(100, "Tải Source Code và cài đặt thành công!")
            self.finished.emit(True, f"Đã tải Source Code và cài đặt thành công mô hình '{self.model_name}' lên phiên bản {latest_version}!")
        except Exception as e:
            self.finished.emit(False, f"Lỗi không xác định: {str(e)}")
