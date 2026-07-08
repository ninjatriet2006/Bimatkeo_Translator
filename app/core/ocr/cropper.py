"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.cropper
- RESPONSIBILITY: Cắt vùng ảnh chứa chữ dựa trên BBox hoặc Polygon, xử lý xoay ma trận.
- CALLED BY: app.core.ocr.local_runner
- CALLS TO: None
- IN = OUT: Nhận ảnh gốc, box, poly -> trả về ảnh con đã cắt (crop).
=============================================================================
"""

import cv2
import numpy as np
from typing import List

class OCRCropper:
    """Xử lý việc cắt ảnh dựa trên Bounding Box hoặc Polygon."""
    
    @staticmethod
    def crop(image: np.ndarray, box: List[int], poly: List[List[float]], use_rotation: bool = False) -> np.ndarray:
        """
        Cắt vùng ảnh chứa chữ. Hỗ trợ xoay crop bằng warpAffine nếu use_rotation=True và poly hợp lệ.
        Trả về mảng ảnh crop.
        """
        if use_rotation and poly:
            try:
                poly_arr = np.array(poly, dtype=np.float32)
                rect = cv2.minAreaRect(poly_arr)
                (center, (width, height), angle) = rect
                if height > width:
                    width, height = height, width
                    angle += 90.0
                
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                box_w, box_h = int(width), int(height)
                rotated = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]))
                crop = cv2.getRectSubPix(rotated, (box_w, box_h), center)
                return crop
            except Exception:
                # Fallback to normal crop
                pass
                
        # Normal bounding box crop
        try:
            return image[box[1]:box[3], box[0]:box[2]]
        except Exception:
            return np.array([])
