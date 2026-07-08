"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.recognizer
- RESPONSIBILITY: Gọi mô hình OCR trên từng vùng ảnh đã crop để trích xuất text.
- CALLED BY: app.core.ocr.local_runner
- CALLS TO: BaseTextRecognizer
- IN = OUT: Nhận crop image -> trả về chuỗi text hoặc rỗng.
=============================================================================
"""

import numpy as np
from app.core.interfaces import BaseTextRecognizer

class OCRRecognizer:
    """Xử lý quá trình nhận diện chữ từ ảnh đã crop."""
    
    @staticmethod
    def recognize(crop: np.ndarray, recognizer: BaseTextRecognizer, prob_thresh: float = 0.0) -> str:
        """
        Gọi model Recognizer trên ảnh crop. Trả về text hoặc chuỗi rỗng nếu tự tin thấp/ảnh lỗi.
        """
        if crop.size == 0 or crop.shape[0] < 8 or crop.shape[1] < 8:
            return ""
            
        try:
            text, conf = recognizer.recognize(crop)
            if conf > 0 and conf < prob_thresh:
                return "" # Bỏ qua do điểm tự tin thấp
            return text
        except Exception:
            return ""
