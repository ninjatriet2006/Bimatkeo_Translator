"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.image_utils
- RESPONSIBILITY: Utility functions for OCR (Cropping, Filtering, Geometry, Preprocessing, Rotation).
- CALLED BY: app.core.ocr.local_runner, app.core.ocr.cloud_runner
- CALLS TO: None
- IN = OUT: Helper methods for image and bounding box manipulation.
=============================================================================
"""

import cv2
import numpy as np
from typing import List, Tuple
from collections import defaultdict
from app.core.ocr.interfaces import BaseTextDetector
from app.core.ocr.interfaces import BaseTextRecognizer

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


class OCRFilter:
    """Bộ lọc bỏ các văn bản và bong bóng rác không hợp lệ."""
    
    @staticmethod
    def apply(bboxes: List[List[int]], texts: List[str], ocr_config: dict) -> Tuple[List[List[int]], List[str]]:
        """
        Lọc bỏ các BBox và Text vi phạm:
        - Box quá nhỏ (ignore_bubble).
        - Text quá ngắn (min_text_length).
        - Text nằm trong danh sách từ cấm (filter_text).
        """
        min_text_length = int(ocr_config.get('min_text_length', 0))
        ignore_bubble = int(ocr_config.get('ignore_bubble', 0))
        filter_text_str = ocr_config.get('filter_text', '')
        filter_texts = [f.strip() for f in filter_text_str.split(',')] if filter_text_str else []

        filtered_bboxes = []
        filtered_texts = []
        
        for box, text in zip(bboxes, texts):
            w_box = box[2] - box[0]
            h_box = box[3] - box[1]
            if w_box * h_box < ignore_bubble:
                continue
            
            if len(text.strip()) < min_text_length:
                continue
                
            if any(f in text for f in filter_texts):
                continue
                
            filtered_bboxes.append(box)
            filtered_texts.append(text)
            
        return filtered_bboxes, filtered_texts


def sort_comic_text_boxes(bboxes: List[list], direction: str = "rtl_ttb", image_width: int = 2000, image_height: int = 3000) -> List[list]:
    """
    Sắp xếp các bounding boxes [x1, y1, x2, y2] theo thứ tự luồng đọc truyện.
    """
    if not bboxes:
        return []
        
    boxes_with_centers = []
    for i, box in enumerate(bboxes):
        cx = (box[0] + box[2]) / 2
        cy = (box[1] + box[3]) / 2
        boxes_with_centers.append({"index": i, "box": box, "cx": cx, "cy": cy})
        
    def get_score(item):
        cx = item["cx"]
        cy = item["cy"]
        
        if direction == "rtl_ttb":
            row_group = int(cy / 200)
            return (row_group * 10000) - cx + cy
        elif direction == "ltr_ttb":
            row_group = int(cy / 200)
            return (row_group * 10000) + cx + cy
        elif direction == "ttb_rtl":
            col_group = int((image_width - cx) / 200)
            return (col_group * 10000) + cy
        elif direction == "ttb_ltr":
            col_group = int(cx / 200)
            return (col_group * 10000) + cy
        else:
            return int(cy / 200) * 10000 - cx + cy

    sorted_items = sorted(boxes_with_centers, key=get_score)
    return [item["box"] for item in sorted_items]


def merge_nearby_boxes_and_texts(bboxes: List[List[int]], texts: List[str], image_width: int, image_height: int) -> tuple[List[List[int]], List[str]]:
    """
    Gom các bong bóng chữ ở gần nhau thành 1 bong bóng duy nhất bằng thuật toán Connected Components.
    Giúp tránh tình trạng 1 câu bị ngắt thành nhiều dòng, hoặc các vùng bong bóng bị chồng lấn không được gộp chung.
    """
    if not bboxes or not texts or len(bboxes) != len(texts):
        return bboxes, texts

    n = len(bboxes)
    parent = list(range(n))
    
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]
        
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    for i in range(n):
        for j in range(i + 1, n):
            box1 = bboxes[i]
            box2 = bboxes[j]
            
            dx = max(0, max(box1[0], box2[0]) - min(box1[2], box2[2]))
            dy = max(0, max(box1[1], box2[1]) - min(box1[3], box2[3]))
            
            w1, h1 = box1[2] - box1[0], box1[3] - box1[1]
            w2, h2 = box2[2] - box2[0], box2[3] - box2[1]
            
            min_w = min(w1, w2)
            min_h = min(h1, h2)
            
            max_gap_x = max(40, int(min_w * 1.5))
            max_gap_y = max(40, int(min_h * 2.0))
            
            if dx <= max_gap_x and dy <= max_gap_y:
                union(i, j)

    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
        
    merged_bboxes = []
    merged_texts = []
    
    sorted_groups = sorted(groups.values(), key=lambda indices: indices[0])
    
    for indices in sorted_groups:
        min_x = min(bboxes[i][0] for i in indices)
        min_y = min(bboxes[i][1] for i in indices)
        max_x = max(bboxes[i][2] for i in indices)
        max_y = max(bboxes[i][3] for i in indices)
        
        merged_bboxes.append([min_x, min_y, max_x, max_y])
        
        group_texts = [texts[i] for i in indices if texts[i].strip()]
        merged_texts.append(" ".join(group_texts))
        
    return merged_bboxes, merged_texts


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
