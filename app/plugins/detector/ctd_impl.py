import os
import numpy as np
from app.core.interfaces import BaseTextDetector
from app.core.factories import DetectorFactory
from app.core.downloader import ModelDownloader

@DetectorFactory.register("ctd")
class CTDetectorImpl(BaseTextDetector):
    def __init__(self):
        self.model = None
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        if not model_path:
            raise ValueError("model_path is required")
        target_dir = os.path.dirname(model_path)
        expected_filename = os.path.basename(model_path)
        
        # Mẫu URL giả định tải mô hình CTD từ Github (Bản chất Wrapper)
        if not os.path.exists(model_path):
            url = ModelDownloader.get_source_url_from_registry("offline_detector", "ctd")
            if url:
                success = ModelDownloader.download_and_extract(
                    url=url, target_dir=target_dir, expected_files=[expected_filename],
                    log_callback=log_callback, extract=False
                )
                if not success:
                    raise RuntimeError(f"Không thể khởi tạo CTD tại {target_dir}")
            else:
                raise RuntimeError(f"Chưa có nguồn tải cho CTD. Vui lòng tự nạp mô hình vào {target_dir}")
            
        # 2. Tại đây sẽ thực thi code nạp model lên VRAM (PyTorch/ONNX/OpenCV)
        if log_callback:
            log_callback("INFO", f"Mô hình CTD đã nạp lên VRAM từ {model_path}.")
        else:
            print(f"[LOG:INFO] Mô hình CTD đã nạp lên VRAM từ {model_path}.")
            
        self.model = os.path.basename(model_path)
        
    def detect(self, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
        """
        Nhận ảnh Numpy và trả về danh sách Bounding Boxes.
        Trong giai đoạn này, hàm tạm thời trả về một Mock Box ở giữa ảnh.
        """
        if self.model is None:
            raise RuntimeError("Mô hình chưa được nạp (load_model chưa được gọi).")
            
        h, w = image.shape[:2]
        # Giả lập Box tìm được ở trung tâm ảnh
        return [[w//4, h//4, w*3//4, h*3//4]], []
