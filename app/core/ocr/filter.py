"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.filter
- RESPONSIBILITY: Lọc bỏ các BBox quá bé, Text quá ngắn hoặc chứa từ cấm.
- CALLED BY: app.core.ocr.cloud_runner, app.core.ocr.local_runner
- CALLS TO: None
- IN = OUT: Nhận danh sách bboxes, texts -> trả về bboxes, texts đã loại bỏ rác.
=============================================================================
"""

from typing import List, Tuple

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
