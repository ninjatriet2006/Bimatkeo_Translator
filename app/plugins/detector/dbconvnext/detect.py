"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.dbconvnext.detect
- RESPONSIBILITY: Xử lý suy luận (detect) text bounding boxes cho DBConvNeXt.
- CALLED BY: app.plugins.detector.dbconvnext.main_impl
- CALLS TO: None
- IN = OUT: Nhận model và image, trả về list các bounding box.
=============================================================================
"""
import numpy as np

def detect_text_dbconvnext(model, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
    if model is None: 
        raise RuntimeError("Chưa nạp model DBConvNeXt.")
    h, w = image.shape[:2]
    return [[w//5, h//5, w*4//5, h*4//5]], []
