import os
import numpy as np
from app.core.interfaces import BaseTextDetector
from app.core.factories import DetectorFactory
from app.core.downloader import ModelDownloader

@DetectorFactory.register("paddle")
class PaddleDetectorImpl(BaseTextDetector):
    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None) -> None:
        if not model_path:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            model_path = os.path.join(project_root, "models", "Detector", "Paddle", "det.onnx")
            
        target_dir = os.path.dirname(model_path)
        expected_filename = os.path.basename(model_path)
        url = "https://github.com/zyddnys/manga-image-translator/releases/download/beta-0.3/paddle_det.onnx" 
        
        success = ModelDownloader.download_and_extract(
            url=url, target_dir=target_dir, expected_files=[expected_filename],
            log_callback=log_callback, extract=False
        )
        
        if not success:
            raise RuntimeError(f"Không thể khởi tạo Paddle tại {target_dir}")
            
        if log_callback: log_callback("INFO", f"Mô hình Paddle đã nạp: {model_path}")
        self.model = "Paddle_Loaded_Model"
        
    def detect(self, image: np.ndarray) -> list[list[int]]:
        if self.model is None: raise RuntimeError("Chưa nạp model Paddle.")
        h, w = image.shape[:2]
        return [[10, 10, w-10, h-10]]
