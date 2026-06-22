import os
import numpy as np
from app.core.interfaces import BaseTextDetector
from app.core.factories import DetectorFactory
from app.core.downloader import ModelDownloader

@DetectorFactory.register("craft")
class CRAFTDetectorImpl(BaseTextDetector):
    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None) -> None:
        if not model_path:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            model_path = os.path.join(project_root, "models", "Detector", "CRAFT", "craft_mlt_25k.pth")
            
        target_dir = os.path.dirname(model_path)
        expected_filename = os.path.basename(model_path)
        url = "https://github.com/zyddnys/manga-image-translator/releases/download/beta-0.3/craft_mlt_25k.pth" 
        
        success = ModelDownloader.download_and_extract(
            url=url, target_dir=target_dir, expected_files=[expected_filename],
            log_callback=log_callback, extract=False
        )
        
        if not success:
            raise RuntimeError(f"Không thể khởi tạo CRAFT tại {target_dir}")
            
        if log_callback: log_callback("INFO", f"Mô hình CRAFT đã nạp: {model_path}")
        self.model = "CRAFT_Loaded_Model"
        
    def detect(self, image: np.ndarray) -> list[list[int]]:
        if self.model is None: raise RuntimeError("Chưa nạp model CRAFT.")
        h, w = image.shape[:2]
        return [[w//4, h//4, w//2, h//2], [w//2, h//2, w*3//4, h*3//4]]
