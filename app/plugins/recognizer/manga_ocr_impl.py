import os
import numpy as np
from PIL import Image
import cv2

from app.core.interfaces import BaseTextRecognizer
from app.core.factories import RecognizerFactory
from app.core.downloader import ModelDownloader

@RecognizerFactory.register("manga_ocr")
class MangaOCRRecognizerImpl(BaseTextRecognizer):
    def __init__(self):
        self.processor = None
        self.model = None

    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
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
        expected_filename = os.path.basename(model_path) # config.json
        
        if not os.path.exists(model_path):
            url = ModelDownloader.get_source_url_from_registry("offline_ocr", "manga_ocr")
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
            
            self.processor = AutoProcessor.from_pretrained(target_dir)
            self.model = VisionEncoderDecoderModel.from_pretrained(target_dir).to(device)
            self.model.eval()
            if log_callback:
                log_callback("INFO", "Mô hình Manga-OCR đã nạp thành công.")
        except Exception as e:
            raise RuntimeError(f"Lỗi khi nạp Manga-OCR: {e}")

    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        if self.model is None or self.processor is None:
            return "", 0.0
            
        try:
            import torch
            
            # Chuyển OpenCV BGR sang RGB PIL Image
            if len(image_crop.shape) == 2:
                img_rgb = cv2.cvtColor(image_crop, cv2.COLOR_GRAY2RGB)
            elif image_crop.shape[2] == 4:
                img_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGRA2RGB)
            else:
                img_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
                
            pil_img = Image.fromarray(img_rgb)
            
            pixel_values = self.processor(images=pil_img, return_tensors="pt").pixel_values
            device = next(self.model.parameters()).device
            pixel_values = pixel_values.to(device)
            
            with torch.no_grad():
                generated_ids = self.model.generate(pixel_values)
                
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            
            # Mô hình tự sinh không trực tiếp trả về độ tin cậy
            # Manga-OCR khá chuẩn xác nên ta mặc định confidence = 1.0
            return generated_text.strip(), 1.0
        except Exception as e:
            return f"[Lỗi OCR: {e}]", 0.0
