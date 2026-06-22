import numpy as np
from app.core.interfaces import BaseTextRecognizer
from app.core.factories import RecognizerFactory

@RecognizerFactory.register("mocr")
class MangaOCRImpl(BaseTextRecognizer):
    def __init__(self):
        self.mocr = None
        
    def load_model(self, model_path: str | None = None, log_callback=None) -> None:
        def _log(level, msg):
            if log_callback: log_callback(level, msg)
            else: print(f"[LOG:{level}] {msg}")
            
        try:
            from manga_ocr import MangaOcr # type: ignore
        except ImportError:
            _log("WARNING", "Chưa cài đặt package manga-ocr. Vui lòng chạy: pip install manga-ocr. Đang sử dụng Dummy Mode.")
            return

        _log("INFO", "Đang nạp MangaOCR lên VRAM (Hệ thống sẽ tự động tải weights HuggingFace nếu chưa có)...")
        # Khởi tạo mô hình - Thư viện manga_ocr đã có sẵn cơ chế Auto-Downloader nội bộ.
        self.mocr = MangaOcr()
        _log("INFO", "Nạp MangaOCR hoàn tất. Mô hình đã sẵn sàng.")
        
    def recognize(self, image_crop: np.ndarray) -> str:
        """
        Nhận ảnh crop chứa 1 dòng chữ và trả về văn bản Text.
        """
        if self.mocr is None:
            return "Mock OCR Text (manga-ocr is not installed)"
            
        import cv2
        from PIL import Image
        
        # manga_ocr yêu cầu dữ liệu ảnh dạng PIL Image (RGB)
        rgb_image = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
        pil_image = Image.fromarray(rgb_image)
        
        # Nhận diện
        text = self.mocr(pil_image)
        return text
