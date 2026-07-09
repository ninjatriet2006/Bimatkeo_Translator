"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_context.dto
- RESPONSIBILITY: Define Data Transfer Objects (DTO) shared across the application.
- CALLED BY: Various
- CALLS TO: None
- IN = OUT: Stores structured data to prevent deep coupling.
=============================================================================
"""
from dataclasses import dataclass, field
import threading
import numpy as np
from typing import List, Optional, Any

@dataclass
class PageContext:
    page_id: str                 # Định danh trang (Ví dụ: Chap_1.1_001)
    original_image: Optional[np.ndarray] = None   # Mảng ảnh gốc dạng NumPy lưu trên RAM
    original_image_path: Optional[str] = None     # Đường dẫn ảnh gốc trên đĩa (dành cho DISK mode)
    raw_bboxes: Optional[List[List[int]]] = None  # Tọa độ khung chữ CHƯA GỘP (dùng cho inpaint)
    bboxes: Optional[List[List[int]]] = None          # Tọa độ khung chữ ĐÃ GỘP (dùng cho render)
    original_texts: Optional[List[str]] = None  # Văn bản gốc nhận diện được (từ Worker OCR)
    translated_texts: Optional[List[str]] = None# Văn bản đã dịch (từ Worker Translator)
    text_styles: Optional[List[Any]] = None     # Định dạng chữ (Màu sắc, kích cỡ, font từ OCR phân tích)
    inpainted_image: Optional[np.ndarray] = None # Mảng ảnh đã xóa nền bong bóng thoại
    inpainted_image_path: Optional[str] = None   # Đường dẫn ảnh đã xóa nền trên đĩa (dành cho DISK mode)
    rendered_image: Optional[np.ndarray] = None  # Ảnh phẳng cuối cùng đã vẽ chữ (để xuất PNG/JPG)
    upscale_ratio: int = 1                       # Tỷ lệ upscale của ảnh nền
    
    # Multipass Translation Candidates
    stage1_candidates: Optional[List[List[dict]]] = None
    stage2_candidates: Optional[List[List[dict]]] = None
    
    # Fork-Join Synchronization Flags
    trans_done: threading.Event = field(default_factory=threading.Event)
    inpaint_done: threading.Event = field(default_factory=threading.Event)
    
    # Human-in-the-loop Synchronization Flag
    hitl_lock: threading.Event = field(default_factory=threading.Event)


