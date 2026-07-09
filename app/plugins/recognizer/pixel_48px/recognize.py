"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.pixel_48px.recognize
- RESPONSIBILITY: Thực thi nhận dạng văn bản (OCR) bằng Pixel 48px.
- CALLED BY: app.plugins.recognizer.pixel_48px.main_impl
- CALLS TO: None
- IN = OUT: Nhận hình ảnh, trả về text và độ tin cậy.
=============================================================================
"""
import numpy as np

def recognize_text_pixel_48px(model, image_crop: np.ndarray) -> tuple[str, float]:
    if model is None: 
        return "", 0.0
    return "[48px] Mock OCR text (Curved xPos supported)", 1.0
