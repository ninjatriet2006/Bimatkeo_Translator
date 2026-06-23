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
        try:
            from paddleocr import PaddleOCR  # type: ignore
        except ImportError:
            raise RuntimeError("Thư viện 'paddleocr' hoặc 'paddlepaddle' chưa được cài đặt. Vui lòng cài đặt qua pip.")
            
        try:
            # Kiểm tra xem người dùng có tải model offline qua giao diện UI hay không
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
            offline_model_path = os.path.join(project_root, "models", "Detector", "Paddle")
            
            det_model_dir = None
            if os.path.exists(offline_model_path):
                for root, _, files in os.walk(offline_model_path):
                    if any(f.endswith('.pdmodel') for f in files):
                        det_model_dir = root
                        break
            
            if det_model_dir:
                if log_callback: log_callback("INFO", f"Đang khởi tạo PaddleOCR với trọng số Offline tại: {det_model_dir}")
                self.model = PaddleOCR(use_angle_cls=False, lang='en', det=True, rec=False, det_model_dir=det_model_dir, show_log=False)
            else:
                if log_callback: log_callback("INFO", "Đang khởi tạo mô hình PaddleOCR chính thức (tự động tải Online nếu thiếu)...")
                # Tự động tải weights theo mặc định của paddleocr (vào ~/.paddleocr/)
                self.model = PaddleOCR(use_angle_cls=False, lang='en', det=True, rec=False, show_log=False)
                
            if log_callback: log_callback("INFO", "Mô hình PaddleOCR đã nạp thành công.")
        except Exception as e:
            raise RuntimeError(f"Lỗi khi khởi tạo PaddleOCR: {e}")
        
    def detect(self, image: np.ndarray) -> list[list[int]]:
        if self.model is None: raise RuntimeError("Chưa nạp model Paddle.")
        
        # result: list of polygons for the image.
        # Format: result[0] is a list of polygons: [ [[x1, y1], [x2, y2], [x3, y3], [x4, y4]], ... ]
        result = self.model.ocr(image, rec=False)
        
        bboxes = []
        if result and len(result) > 0 and result[0] is not None:
            # Tùy phiên bản PaddleOCR, đôi khi trả về mảng trực tiếp nếu rec=False
            polygons = result[0] if isinstance(result[0], list) and (len(result[0]) > 0 and isinstance(result[0][0], list)) else result
            
            for polygon in polygons:
                if not polygon or len(polygon) < 4: continue
                # Nếu polygon là mảng numpy hoặc list chứa 4 tọa độ
                try:
                    xs = [pt[0] for pt in polygon]
                    ys = [pt[1] for pt in polygon]
                    bboxes.append([int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))])
                except (IndexError, TypeError):
                    continue
                    
        return bboxes
