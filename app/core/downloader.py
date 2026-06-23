import os
import urllib.request
import zipfile
import hashlib
import shutil

class ModelDownloader:
    """
    Universal Downloader Handler
    Chịu trách nhiệm tải trọng số mô hình từ Internet, giải nén và báo cáo tiến trình về UI.
    """
    
    @staticmethod
    def get_source_url_from_registry(field: str, key: str) -> str:
        import yaml
        registry_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".config", "models", "model_registry.yaml")
        if not os.path.exists(registry_path):
            return ""
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            items = data.get("fields", {}).get(field, [])
            for item in items:
                if item.get("key") == key:
                    return item.get("source", "")
        except Exception as e:
            print(f"[Registry] Failed to parse registry: {e}")
        return ""

    @staticmethod
    def download_and_extract(url: str, target_dir: str, expected_files: list[str], 
                             log_callback=None, extract: bool = False, checksum: str | None = None) -> bool:
        """
        Tải file từ URL và giải nén (nếu là zip).
        
        Args:
            url: Đường dẫn tải về.
            target_dir: Thư mục chứa file sau khi hoàn tất.
            expected_files: Danh sách các file mong đợi sẽ tồn tại (nếu đã có thì skip tải).
            log_callback: Hàm callback(level, msg) để in log tiến trình.
            extract: Có giải nén file zip không.
            checksum: Chuỗi mã băm SHA256 để verify (nếu cần).
        """
        def _log(level, msg):
            if log_callback:
                log_callback(level, msg)
            else:
                print(f"[LOG:{level}] {msg}")

        # Kiểm tra nếu tất cả các file đã tồn tại thì bỏ qua tải
        if all(os.path.exists(os.path.join(target_dir, f)) for f in expected_files):
            _log("INFO", f"Mô hình đã tồn tại đầy đủ tại {target_dir}. Bỏ qua tải.")
            return True
            
        os.makedirs(target_dir, exist_ok=True)
        filename = url.split('/')[-1]
        if "?" in filename:
            filename = filename.split("?")[0]
            
        download_path = os.path.join(target_dir, filename)
        
        # Hàm theo dõi tiến trình
        def _reporthook(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                if percent > 100: percent = 100
                if count % max(1, (total_size // block_size // 10)) == 0:
                    _log("INFO", f"Đang tải {filename}... {percent}%")

        try:
            _log("INFO", f"Bắt đầu tải mô hình từ: {url}")
            urllib.request.urlretrieve(url, download_path, reporthook=_reporthook)
            _log("INFO", f"Tải hoàn tất: {filename}")
            
            # Optional: Kiểm tra Checksum (SHA256)
            if checksum:
                _log("INFO", "Đang xác thực mã băm SHA256...")
                hasher = hashlib.sha256()
                with open(download_path, 'rb') as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hasher.update(chunk)
                if hasher.hexdigest() != checksum:
                    _log("ERROR", "Sai lệch mã băm (Checksum Mismatch). File có thể bị hỏng!")
                    os.remove(download_path)
                    return False
                _log("INFO", "Xác thực mã băm thành công.")
            
            # Giải nén nếu được yêu cầu
            if extract and download_path.endswith('.zip'):
                _log("INFO", "Đang giải nén tệp tin...")
                with zipfile.ZipFile(download_path, 'r') as zip_ref:
                    zip_ref.extractall(target_dir)
                _log("INFO", "Giải nén hoàn tất.")
                # Dọn file zip gốc
                os.remove(download_path)
                
            return True
            
        except Exception as e:
            _log("ERROR", f"Lỗi trong quá trình tải/giải nén: {e}")
            if os.path.exists(download_path):
                os.remove(download_path)
            return False
