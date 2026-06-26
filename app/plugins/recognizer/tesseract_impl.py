import numpy as np
import cv2

from app.core.interfaces import BaseTextRecognizer
from app.core.factories import RecognizerFactory

def create_tesseract_class(lang_code: str):
    """Factory method to dynamically generate a Tesseract Recognizer class for a specific language code."""
    class TesseractRecognizerImpl(BaseTextRecognizer):
        def __init__(self):
            self.lang_code = lang_code
            self.is_ready = False

        def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
            try:
                import pytesseract
                # Kiểm tra xem tesseract có được cài trên hệ điều hành chưa
                pytesseract.get_tesseract_version()
                self.is_ready = True
                if log_callback:
                    log_callback("INFO", f"Tesseract OCR ({self.lang_code}) đã sẵn sàng.")
            except ImportError:
                raise RuntimeError("Vui lòng cài đặt pytesseract: pip install pytesseract")
            except Exception as e:
                raise RuntimeError(
                    f"Tesseract chưa được cài đặt trên hệ điều hành. Lỗi: {e}. "
                    "Vui lòng chạy: sudo apt-get install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-jpn-vert "
                    "tesseract-ocr-kor tesseract-ocr-kor-vert tesseract-ocr-chi-sim tesseract-ocr-chi-sim-vert "
                    "tesseract-ocr-chi-tra tesseract-ocr-chi-tra-vert"
                )

        def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
            if not self.is_ready:
                return "", 0.0
                
            try:
                import pytesseract
                
                # Tiền xử lý: Chuyển sang thang độ xám (Grayscale)
                if len(image_crop.shape) == 3:
                    gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image_crop
                    
                # Tiền xử lý: Tăng độ tương phản (Thresholding/Binarization)
                # Dùng Otsu's thresholding để tách chữ khỏi nền
                _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                
                # Đảo ngược màu nếu nền đen chữ trắng (Tesseract thích nền trắng chữ đen hơn)
                white_pixels = np.sum(binary == 255)
                total_pixels = binary.size
                if white_pixels < total_pixels / 2:
                    binary = cv2.bitwise_not(binary)

                # Sử dụng ngôn ngữ được gán cho class này
                tess_lang = self.lang_code
                if self.lang_code == "mixed":
                    tess_lang = "jpn+jpn_vert+chi_sim+chi_sim_vert+chi_tra+chi_tra_vert+kor+kor_vert+eng"
                elif self.lang_code == "all_horizontal":
                    tess_lang = "jpn+chi_sim+chi_tra+kor+eng"
                elif self.lang_code == "all_vertical":
                    tess_lang = "jpn_vert+chi_sim_vert+chi_tra_vert+kor_vert"

                # psm 6: Đọc một khối văn bản đồng nhất (phù hợp cho 1 bong bóng chữ ngang).
                # psm 5: Phù hợp hơn cho chữ dọc.
                # Nếu là ngôn ngữ dọc (có _vert), ta chuyển sang psm 5.
                psm = 5 if "_vert" in self.lang_code or self.lang_code == "all_vertical" else 6
                
                custom_config = f'-l {tess_lang} --psm {psm} --oem 3'
                
                text = str(pytesseract.image_to_string(binary, config=custom_config))
                
                clean_text = text.strip()
                return clean_text, 1.0 if clean_text else 0.0
                
            except Exception as e:
                return f"[Lỗi Tesseract: {e}]", 0.0
                
    return TesseractRecognizerImpl

# Đăng ký động tất cả các biến thể Tesseract vào Factory
langs = [
    "jpn", "jpn_vert", 
    "chi_sim", "chi_sim_vert", 
    "chi_tra", "chi_tra_vert", 
    "kor", "kor_vert", 
    "eng", 
    "mixed",
    "all_horizontal",
    "all_vertical"
]

for lang in langs:
    RecognizerFactory.register(f"tesseract_{lang}")(create_tesseract_class(lang))
