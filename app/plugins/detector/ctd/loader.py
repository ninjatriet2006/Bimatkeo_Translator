"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.ctd.loader
- RESPONSIBILITY: Tải mô hình CTD (Download/Extract/Load vào RAM/VRAM).
- CALLED BY: app.plugins.detector.ctd.main_impl
- CALLS TO: app.core.downloader.ModelDownloader, app.core.shared_registry.DetectorFactory
- IN = OUT: Nhận model_path, trả về instance mô hình đã tải.
=============================================================================
"""
import os
from app.core.shared_registry import DetectorFactory
from app.core.downloader import ModelDownloader

def load_ctd_model(model_path: str | None = None, log_callback=None, **kwargs):
    if not model_path:
        raise ValueError("model_path is required")
    target_dir = os.path.dirname(model_path)
    expected_filename = os.path.basename(model_path)
    
    if not os.path.exists(model_path):
        url = DetectorFactory.get_source_url_from_registry("offline_detector", "ctd")
        if url:
            success = ModelDownloader.download_and_extract(
                url=url, target_dir=target_dir, expected_files=[expected_filename],
                log_callback=log_callback, extract=False
            )
            if not success:
                raise RuntimeError(f"Không thể khởi tạo CTD tại {target_dir}")
        else:
            raise RuntimeError(f"Chưa có nguồn tải cho CTD. Vui lòng tự nạp mô hình vào {target_dir}")
        
    if log_callback:
        log_callback("INFO", f"Mô hình CTD đã nạp lên VRAM từ {model_path}.")
    else:
        print(f"[LOG:INFO] Mô hình CTD đã nạp lên VRAM từ {model_path}.")
        
    return os.path.basename(model_path)
