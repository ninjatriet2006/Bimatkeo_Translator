"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.tesseract.recognize
- RESPONSIBILITY: Thực thi nhận dạng văn bản (OCR) bằng Tesseract.
- CALLED BY: app.plugins.recognizer.tesseract.main_impl
- CALLS TO: None
- IN = OUT: Nhận hình ảnh và mã ngôn ngữ, trả về text và độ tin cậy.
=============================================================================
"""
import numpy as np
import cv2

def recognize_text_tesseract(is_ready: bool, lang_code: str, image_crop: np.ndarray) -> tuple[str, float]:
    if not is_ready:
        return "", 0.0
        
    try:
        import pytesseract
        
        if len(image_crop.shape) == 3:
            gray = cv2.cvtColor(image_crop, cv2.COLOR_BGR2GRAY)
        else:
            gray = image_crop
            
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        white_pixels = np.sum(binary == 255)
        total_pixels = binary.size
        if white_pixels < total_pixels / 2:
            binary = cv2.bitwise_not(binary)

        tess_lang = lang_code
        if lang_code == "mixed":
            tess_lang = "jpn+jpn_vert+chi_sim+chi_sim_vert+chi_tra+chi_tra_vert+kor+kor_vert+eng"
        elif lang_code == "all_horizontal":
            tess_lang = "jpn+chi_sim+chi_tra+kor+eng"
        elif lang_code == "all_vertical":
            tess_lang = "jpn_vert+chi_sim_vert+chi_tra_vert+kor_vert"

        psm = 5 if "_vert" in lang_code or lang_code == "all_vertical" else 6
        
        custom_config = f'-l {tess_lang} --psm {psm} --oem 3'
        
        text = str(pytesseract.image_to_string(binary, config=custom_config))
        
        clean_text = text.strip()
        return clean_text, 1.0 if clean_text else 0.0
        
    except Exception as e:
        return f"[Lỗi Tesseract: {e}]", 0.0
