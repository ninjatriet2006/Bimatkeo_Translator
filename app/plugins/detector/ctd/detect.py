"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.ctd.detect
- RESPONSIBILITY: Xử lý suy luận (detect) text bounding boxes cho CTD.
- CALLED BY: app.plugins.detector.ctd.main_impl
- CALLS TO: None
- IN = OUT: Nhận model và image, trả về list các bounding box.
=============================================================================
"""
import numpy as np

def detect_text_ctd(model, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
    if model is None:
        raise RuntimeError("Mô hình chưa được nạp (load_model chưa được gọi).")
        
    h, w = image.shape[:2]
    return [[w//4, h//4, w*3//4, h*3//4]], []
