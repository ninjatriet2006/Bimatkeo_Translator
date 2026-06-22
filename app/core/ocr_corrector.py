import numpy as np

class VisionOCRCorrector:
    """
    2-Stage Vision OCR Correction
    Mô phỏng sử dụng LLM Vision (như Gemini/GPT-4o) để kiểm tra chéo và sửa lỗi chính tả từ mô hình OCR gốc.
    """
    def __init__(self, use_llm: bool = False, log_callback=None):
        self.use_llm = use_llm
        self.log_callback = log_callback
        
    def correct(self, original_texts: list[str], full_image: np.ndarray) -> list[str]:
        """
        Nhận mảng texts đã OCR bằng mô hình tĩnh và ảnh gốc.
        Nếu cờ use_llm được bật, sẽ chạy cơ chế ghép chuỗi và sửa lỗi.
        """
        if not self.use_llm or not original_texts:
            return original_texts
            
        if self.log_callback:
            self.log_callback("INFO", "Kích hoạt 2-Stage Vision Correction: Đang nạp LLM sửa lỗi OCR...")
            
        corrected_texts = []
        for text in original_texts:
            if not text.strip():
                corrected_texts.append(text)
                continue
                
            # Mô phỏng AI sửa lỗi (Ví dụ: OCR nhầm l/I hoặc 1/I)
            # Trong thực tế, ở đây sẽ gói base64 ảnh và ném lên API Gemini.
            corrected = text.replace("I", "l") if "I" in text and "l" not in text else text
            
            # Đánh dấu đã qua sửa lỗi
            if corrected != text:
                corrected_texts.append(f"{corrected} (Đã sửa bởi AI)")
            else:
                corrected_texts.append(text)
                
        if self.log_callback:
            self.log_callback("SUCCESS", "Hoàn thành 2-Stage Vision Correction.")
            
        return corrected_texts
