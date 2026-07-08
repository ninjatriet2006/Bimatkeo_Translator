"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.preprocessor
- RESPONSIBILITY: Chuẩn bị ảnh chất lượng tốt nhất (Invert, Gamma) trước khi đưa vào Detector.
- CALLED BY: app.core.ocr.local_runner
- CALLS TO: None
- IN = OUT: Nhận ảnh gốc (numpy) -> trả về ảnh đã tiền xử lý.
=============================================================================
"""

import cv2
import numpy as np

class OCRPreprocessor:
    """Xử lý ảnh trước khi đưa vào mô hình nhận diện chữ."""
    
    @staticmethod
    def preprocess(image: np.ndarray, ocr_config: dict) -> np.ndarray:
        """
        Áp dụng Invert Colors hoặc Gamma Correction dựa trên cấu hình.
        """
        det_image = image.copy()
        
        # 1. Invert colors if requested
        if ocr_config.get('det_invert'):
            det_image = cv2.bitwise_not(det_image)
        
        # 2. Apply Gamma Correction if requested
        gamma = float(ocr_config.get('det_gamma_correct', 1.0))
        if gamma != 1.0:
            inv_gamma = 1.0 / gamma
            table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in np.arange(0, 256)]).astype("uint8")
            det_image = cv2.LUT(det_image, table)
            
        return det_image
