"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.tesseract.loader
- RESPONSIBILITY: Khởi tạo và kiểm tra trạng thái của Tesseract OCR trên hệ điều hành.
- CALLED BY: app.plugins.recognizer.tesseract.main_impl
- CALLS TO: None
- IN = OUT: Nhận lang_code, trả về boolean báo hiệu trạng thái sẵn sàng.
=============================================================================
"""

def load_tesseract_model(lang_code: str, log_callback=None, **kwargs) -> bool:
    try:
        import pytesseract
        # Kiểm tra xem tesseract có được cài trên hệ điều hành chưa
        pytesseract.get_tesseract_version()
        if log_callback:
            log_callback("INFO", f"Tesseract OCR ({lang_code}) đã sẵn sàng.")
        return True
    except ImportError:
        raise RuntimeError("Vui lòng cài đặt pytesseract: pip install pytesseract")
    except Exception as e:
        raise RuntimeError(
            f"Tesseract chưa được cài đặt trên hệ điều hành. Lỗi: {e}. "
            "Vui lòng chạy: sudo apt-get install tesseract-ocr tesseract-ocr-jpn tesseract-ocr-jpn-vert "
            "tesseract-ocr-kor tesseract-ocr-kor-vert tesseract-ocr-chi-sim tesseract-ocr-chi-sim-vert "
            "tesseract-ocr-chi-tra tesseract-ocr-chi-tra-vert"
        )
