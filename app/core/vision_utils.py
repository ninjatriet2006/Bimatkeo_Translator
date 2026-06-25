import numpy as np
from typing import List

def sort_comic_text_boxes(bboxes: List[List[int]], direction: str = "rtl_ttb", image_width: int = 2000, image_height: int = 3000) -> List[List[int]]:
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
    Gom các bong bóng chữ ở gần nhau thành 1 bong bóng duy nhất.
    Giúp tránh tình trạng 1 câu bị ngắt thành nhiều dòng dịch (word-by-word) làm mất ngữ cảnh.
    """
    if not bboxes or not texts or len(bboxes) != len(texts):
        return bboxes, texts

    clusters = []
    for i, box in enumerate(bboxes):
        text = texts[i]
        matched_cluster_idx = -1
        
        # Tìm xem box hiện tại có nên gộp với cluster nào không
        for j, cluster in enumerate(clusters):
            c_box = cluster["box"]
            
            # Tính khoảng cách giữa box hiện tại và cluster box
            dx = max(0, max(c_box[0], box[0]) - min(c_box[2], box[2]))
            dy = max(0, max(c_box[1], box[1]) - min(c_box[3], box[3]))
            
            # Tính kích thước để làm hệ tham chiếu
            w1, h1 = box[2] - box[0], box[3] - box[1]
            w2, h2 = c_box[2] - c_box[0], c_box[3] - c_box[1]
            
            # Lấy kích thước nhỏ hơn để tránh 1 box khổng lồ nuốt chửng mọi thứ
            min_w = min(w1, w2)
            min_h = min(h1, h2)
            
            # Ngưỡng gap động: 50% chiều rộng nhỏ nhất, 80% chiều cao nhỏ nhất (tối thiểu 20px)
            max_gap_x = max(20, int(min_w * 0.5))
            max_gap_y = max(20, int(min_h * 0.8))
            
            if dx <= max_gap_x and dy <= max_gap_y:
                matched_cluster_idx = j
                break
                
        if matched_cluster_idx != -1:
            c = clusters[matched_cluster_idx]
            c_box = c["box"]
            c["box"] = [
                min(c_box[0], box[0]),
                min(c_box[1], box[1]),
                max(c_box[2], box[2]),
                max(c_box[3], box[3])
            ]
            c["texts"].append(text)
        else:
            clusters.append({
                "box": list(box),
                "texts": [text]
            })
            
    merged_bboxes = []
    merged_texts = []
    for c in clusters:
        merged_bboxes.append(c["box"])
        # Nối các câu lại, nếu không có dấu kết câu ở trước thì nối bằng dấu cách
        merged_text = " ".join([t for t in c["texts"] if t.strip()])
        merged_texts.append(merged_text)
        
    return merged_bboxes, merged_texts
