"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.pixel_32px.loader
- RESPONSIBILITY: Tải mô hình Pixel 32px (Download/Extract/Load).
- CALLED BY: app.plugins.recognizer.pixel_32px.main_impl
- CALLS TO: app.core.downloader.ModelDownloader, app.core.shared_registry.RecognizerFactory
- IN = OUT: Nhận model_path, trả về instance mô hình đã tải.
=============================================================================
"""
import os
from app.core.shared_registry import RecognizerFactory
from app.core.downloader import ModelDownloader

def load_pixel_32px_model(model_path: str | None = None, log_callback=None, **kwargs):
    if not model_path:
        raise ValueError("model_path is required")
    target_dir = os.path.dirname(model_path)
    expected_filename = os.path.basename(model_path)
    
    if not os.path.exists(model_path):
        url = RecognizerFactory.get_source_url_from_registry("offline_ocr", "32px")
        if url:
            success = ModelDownloader.download_and_extract(
                url=url, target_dir=target_dir, expected_files=[expected_filename],
                log_callback=log_callback, extract=True
            )
            if not success:
                raise RuntimeError(f"Không thể khởi tạo mô hình 32px tại {target_dir}")
        else:
            raise RuntimeError(f"Chưa có nguồn tải cho mô hình 32px. Vui lòng tự nạp mô hình vào {target_dir}")
    
    if log_callback: log_callback("INFO", f"Mô hình 32px OCR đã nạp: {model_path}")
    return os.path.basename(model_path)
