"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.rotator
- RESPONSIBILITY: Tìm góc xoay tối ưu bằng cách thử nhận diện text ở các góc.
- CALLED BY: app.core.ocr.local_runner
- CALLS TO: app.core.interfaces.BaseTextRecognizer, app.core.interfaces.BaseTextDetector
- IN = OUT: Nhận Numpy array ảnh -> trả về góc xoay Int và ảnh đã xoay.
=============================================================================
"""

import cv2
import numpy as np
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer

class OCRRotator:
    """Tự động phát hiện góc xoay của trang truyện để sửa lỗi chụp ngược/nghiêng 90 độ."""
    
    @staticmethod
    def detect_orientation(det_image: np.ndarray, recognizer: BaseTextRecognizer, detector: BaseTextDetector) -> int:
        """
        Tìm góc xoay tối ưu (0, 90, 180, 270) bằng cách thử nhận diện text ở các góc.
        """
        raw_bboxes, _ = detector.detect(det_image)
        if not raw_bboxes: 
            return 0
            
        boxes = sorted(raw_bboxes, key=lambda b: (b[2]-b[0])*(b[3]-b[1]), reverse=True)[:3]
        angles = [0, 90, 180, 270]
        angle_scores = {a: 0.0 for a in angles}
        
        for angle in angles:
            scores = []
            for box in boxes:
                crop = det_image[box[1]:box[3], box[0]:box[2]]
                if crop.size == 0: 
                    continue
                    
                if angle == 90: 
                    crop = cv2.rotate(crop, cv2.ROTATE_90_CLOCKWISE)
                elif angle == 180: 
                    crop = cv2.rotate(crop, cv2.ROTATE_180)
                elif angle == 270: 
                    crop = cv2.rotate(crop, cv2.ROTATE_90_COUNTERCLOCKWISE)
                    
                _, conf = recognizer.recognize(crop)
                scores.append(conf)
                
            if scores: 
                angle_scores[angle] = sum(scores) / len(scores)
                
        return max(angle_scores.items(), key=lambda x: x[1])[0]

    @staticmethod
    def apply_rotation(image: np.ndarray, angle: int) -> np.ndarray:
        """
        Xoay ảnh gốc theo góc đã cho.
        """
        if angle == 90:
            return cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(image, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
        return image
