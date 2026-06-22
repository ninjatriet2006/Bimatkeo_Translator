import os
import numpy as np
from app.core.interfaces import BaseTextRecognizer
from app.core.factories import RecognizerFactory
from app.core.downloader import ModelDownloader

@RecognizerFactory.register("32px")
class Pixel32pxRecognizerImpl(BaseTextRecognizer):
    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None) -> None:
        if not model_path:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            model_path = os.path.join(project_root, "models", "OCR", "32px", "alphabet-all-v7.txt")
            
        target_dir = os.path.dirname(model_path)
        expected_filename = os.path.basename(model_path)
        url = "https://github.com/zyddnys/manga-image-translator/releases/download/beta-0.3/32px_ocr.zip" 
        
        success = ModelDownloader.download_and_extract(
            url=url, target_dir=target_dir, expected_files=[expected_filename],
            log_callback=log_callback, extract=False
        )
        
        if log_callback: log_callback("INFO", f"Mô hình 32px OCR đã nạp: {model_path}")
        self.model = "32px_Loaded_Model"
        
    def recognize(self, image_crop: np.ndarray) -> str:
        if self.model is None: return ""
        return "[32px] Nhận diện chữ mẫu"
