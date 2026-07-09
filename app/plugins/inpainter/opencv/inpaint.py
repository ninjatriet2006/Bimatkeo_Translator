"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.opencv.inpaint
- RESPONSIBILITY: Thực thi inpainting ảnh bằng OpenCV Telea algorithm.
- CALLED BY: app.plugins.inpainter.opencv.main_impl
- CALLS TO: None
- IN = OUT: Nhận hình ảnh và danh sách bboxes, trả về ảnh đã inpaint.
=============================================================================
"""
import numpy as np
from typing import List
import cv2

def inpaint_opencv(image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
    if not bboxes:
        return image

    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    for box in bboxes:
        x_min, y_min, x_max, y_max = box
        pad = 5
        x1 = max(0, x_min - pad)
        y1 = max(0, y_min - pad)
        x2 = min(image.shape[1], x_max + pad)
        y2 = min(image.shape[0], y_max + pad)
        cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
        
    return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)
