"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.manga_ocr.loader
- RESPONSIBILITY: Tải và nạp mô hình Manga-OCR (sử dụng thư viện transformers).
- CALLED BY: app.plugins.recognizer.manga_ocr.main_impl
- CALLS TO: app.core.downloader.ModelDownloader, app.core.shared_registry.RecognizerFactory
- IN = OUT: Nhận model_path, trả về processor và model instance.
=============================================================================
"""
import os
from app.core.shared_registry import RecognizerFactory
from app.core.downloader import ModelDownloader

def load_manga_ocr_model(model_path: str | None = None, log_callback=None, **kwargs):
    try:
        from transformers import AutoProcessor, VisionEncoderDecoderModel
    except ImportError:
        raise RuntimeError(
            "Cần cài đặt thư viện transformers để dùng Manga-OCR. "
            "Vui lòng chạy: pip install transformers fugashi unidic-lite"
        )

    if not model_path:
        raise ValueError("model_path is required")
        
    target_dir = os.path.dirname(model_path)
    expected_filename = os.path.basename(model_path)
    
    if not os.path.exists(model_path):
        url = RecognizerFactory.get_source_url_from_registry("offline_ocr", "manga_ocr")
        if url:
            if log_callback:
                log_callback("INFO", f"Đang tiến hành tải tự động Manga-OCR từ {url}...")
            success = ModelDownloader.download_and_extract(
                url=url, target_dir=target_dir, expected_files=[expected_filename],
                log_callback=log_callback, extract=False
            )
            if not success:
                raise RuntimeError(f"Không thể khởi tạo mô hình Manga-OCR tại {target_dir}")
        else:
            raise RuntimeError(f"Chưa có nguồn tải cho mô hình Manga-OCR. Vui lòng tự nạp mô hình vào {target_dir}")

    try:
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        if log_callback:
            log_callback("INFO", f"Đang nạp Manga-OCR trên thiết bị: {device}")
        
        processor = AutoProcessor.from_pretrained(target_dir)
        model = VisionEncoderDecoderModel.from_pretrained(target_dir).to(device)
        model.eval()
        if log_callback:
            log_callback("INFO", "Mô hình Manga-OCR đã nạp thành công.")
            
        return processor, model
    except Exception as e:
        raise RuntimeError(f"Lỗi khi nạp Manga-OCR: {e}")
