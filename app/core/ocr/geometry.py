"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.geometry
- RESPONSIBILITY: Sorts reading flow (Box Sorting) and merges nearby text bubbles (Box Merging).
- CALLED BY: app.core.ocr.cloud_runner, app.core.ocr.local_runner
- CALLS TO: None
- IN = OUT: Receives bboxes -> sorts / merges -> returns new bboxes.
=============================================================================
"""

import numpy as np
from typing import List

def sort_comic_text_boxes(bboxes: List[list], direction: str = "rtl_ttb", image_width: int = 2000, image_height: int = 3000) -> List[list]:
    """
    Sắp xếp các bounding boxes [x1, y1, x2, y2] theo thứ tự luồng đọc truyện.
    
    Hỗ trợ các hướng (direction):
    - "rtl_ttb": Từ Phải sang Trái, Từ Trên xuống Dưới (Manga Nhật Bản)
    - "ltr_ttb": Từ Trái sang Phải, Từ Trên xuống Dưới (Comic Mỹ/Webtoon)
    - "ttb_rtl": Từ Trên xuống Dưới, Từ Phải sang Trái (Cột chữ truyền thống Nhật)
    - "ttb_ltr": Từ Trên xuống Dưới, Từ Trái sang Phải
    
    Thuật toán: Tính toán tọa độ trung tâm (cx, cy) của từng hộp chữ.
    Sử dụng hàm mục tiêu (score) dựa trên sự ưu tiên của trục chính và trục phụ,
    hoặc dùng thuật toán gom cụm (clustering) theo hàng/cột. Ở đây dùng heuristic trọng số.
    """
    if not bboxes:
        return []
        
    # Tính Center X, Center Y cho mỗi box
    boxes_with_centers = []
    for i, box in enumerate(bboxes):
        cx = (box[0] + box[2]) / 2
        cy = (box[1] + box[3]) / 2
        boxes_with_centers.append({"index": i, "box": box, "cx": cx, "cy": cy})
        
    # Trọng số Y (Hàng) so với X (Cột) để chống nhảy cóc (Ví dụ: Cùng 1 hàng lệch nhau 50px vẫn tính là 1 hàng)
    # Tùy thuộc vào direction, hàm score sẽ khác nhau. Box có score NHỎ NHẤT sẽ được đọc trước.
    
    def get_score(item):
        cx = item["cx"]
        cy = item["cy"]
        
        if direction == "rtl_ttb":
            # Manga: Đọc từ trên xuống (Y tăng), từ phải qua trái (X giảm).
            # Nhóm các bong bóng thoại theo hàng Y (chia cho khoảng 200px để gom nhóm).
            row_group = int(cy / 200)
            return (row_group * 10000) - cx + cy
            
        elif direction == "ltr_ttb":
            # Comic: Trái qua phải (X tăng), trên xuống dưới (Y tăng)
            row_group = int(cy / 200)
            return (row_group * 10000) + cx + cy
            
        elif direction == "ttb_rtl":
            # Cột dọc Nhật: Đọc từ phải qua trái (X giảm) trước, sau đó từ trên xuống (Y tăng)
            col_group = int((image_width - cx) / 200)
            return (col_group * 10000) + cy
            
        elif direction == "ttb_ltr":
            # Cột dọc: Trái qua phải (X tăng), trên xuống (Y tăng)
            col_group = int(cx / 200)
            return (col_group * 10000) + cy
            
        else:
            # Mặc định RTL_TTB
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

    # Tạo đồ thị kết nối giữa các box
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
            
            # Ngưỡng gap động: 150% chiều rộng nhỏ nhất, 200% chiều cao nhỏ nhất (tối thiểu 40px)
            max_gap_x = max(40, int(min_w * 1.5))
            max_gap_y = max(40, int(min_h * 2.0))
            
            if dx <= max_gap_x and dy <= max_gap_y:
                union(i, j)

    # Gom nhóm các box theo root
    from collections import defaultdict
    groups = defaultdict(list)
    for i in range(n):
        groups[find(i)].append(i)
        
    merged_bboxes = []
    merged_texts = []
    
    # Sắp xếp các nhóm dựa trên index của box đầu tiên trong nhóm (để giữ nguyên thứ tự sắp xếp ban đầu)
    sorted_groups = sorted(groups.values(), key=lambda indices: indices[0])
    
    for indices in sorted_groups:
        min_x = min(bboxes[i][0] for i in indices)
        min_y = min(bboxes[i][1] for i in indices)
        max_x = max(bboxes[i][2] for i in indices)
        max_y = max(bboxes[i][3] for i in indices)
        
        merged_bboxes.append([min_x, min_y, max_x, max_y])
        
        # Nối text theo thứ tự ban đầu của các box trong nhóm
        group_texts = [texts[i] for i in indices if texts[i].strip()]
        merged_texts.append(" ".join(group_texts))
        
    return merged_bboxes, merged_texts
