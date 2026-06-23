from dataclasses import dataclass, field
import threading
import numpy as np
from typing import List, Optional, Any

@dataclass
class PageContext:
    page_id: str                 # Định danh trang (Ví dụ: Chap_1.1_001)
    original_image: Optional[np.ndarray] = None   # Mảng ảnh gốc dạng NumPy lưu trên RAM
    bboxes: Optional[List[List[int]]] = None          # Tọa độ khung chữ (từ Worker OCR)
    original_texts: Optional[List[str]] = None  # Văn bản gốc nhận diện được (từ Worker OCR)
    translated_texts: Optional[List[str]] = None# Văn bản đã dịch (từ Worker Translator)
    text_styles: Optional[List[Any]] = None     # Định dạng chữ (Màu sắc, kích cỡ, font từ OCR phân tích)
    inpainted_image: Optional[np.ndarray] = None # Mảng ảnh đã xóa nền bong bóng thoại
    rendered_image: Optional[np.ndarray] = None  # Ảnh phẳng cuối cùng đã vẽ chữ (để xuất PNG/JPG)
    
    # Fork-Join Synchronization Flags
    trans_done: threading.Event = field(default_factory=threading.Event)
    inpaint_done: threading.Event = field(default_factory=threading.Event)
