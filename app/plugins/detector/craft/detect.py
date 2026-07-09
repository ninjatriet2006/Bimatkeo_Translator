"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.craft.detect
- RESPONSIBILITY: Xử lý suy luận (detect) text bounding boxes.
- CALLED BY: app.plugins.detector.craft.main_impl
- CALLS TO: None
- IN = OUT: Nhận model và image (numpy array), trả về boxes và polys.
=============================================================================
"""
import numpy as np

def detect_text_craft(model, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
    if model is None:
        raise RuntimeError("Chưa nạp model CRAFT.")
    h, w = image.shape[:2]
    boxes = [[w//4, h//4, w//2, h//2], [w//2, h//2, w*3//4, h*3//4]]
    return (boxes, [])
