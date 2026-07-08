import os
import numpy as np
from app.core.interfaces import BaseTextRecognizer
from app.core.factories import RecognizerFactory
from app.core.downloader import ModelDownloader

@RecognizerFactory.register("48px")
class Pixel48pxRecognizerImpl(BaseTextRecognizer):
    MODELS = [
        {'key': '48px', 'check_file': 'models/OCR/48px/ocr_ar_48px.ckpt'},
    ]

    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        if not model_path:
            raise ValueError("model_path is required")
        target_dir = os.path.dirname(model_path)
        expected_filename = os.path.basename(model_path)
        if not os.path.exists(model_path):
            url = RecognizerFactory.get_source_url_from_registry("offline_ocr", "48px")
            if url:
                success = ModelDownloader.download_and_extract(
                    url=url, target_dir=target_dir, expected_files=[expected_filename],
                    log_callback=log_callback, extract=False
                )
                if not success:
                    raise RuntimeError(f"Không thể khởi tạo mô hình 48px tại {target_dir}")
            else:
                raise RuntimeError(f"Chưa có nguồn tải cho mô hình 48px. Vui lòng tự nạp mô hình vào {target_dir}")
        
        if log_callback: log_callback("INFO", f"Mô hình 48px OCR đã nạp: {model_path}")
        self.model = os.path.basename(model_path)
        
    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        if self.model is None: return "", 0.0
        return "[48px] Mock OCR text (Curved xPos supported)", 1.0
