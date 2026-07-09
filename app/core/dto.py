"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.dto
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

    @property
    def is_disk_mode(self) -> bool:
        """Kiểm tra xem context có đang hoạt động ở DISK mode không."""
        return self.original_image_path is not None and self.original_image is None

    def get_original_image(self) -> Optional[np.ndarray]:
        """Lấy ảnh gốc từ RAM hoặc đọc từ đĩa nếu đang ở DISK mode."""
        if self.original_image is not None:
            return self.original_image
        if self.original_image_path:
            import cv2
            return cv2.imread(self.original_image_path)
        return None

    def set_original_image(self, image: np.ndarray):
        """Cập nhật ảnh gốc (thường dùng khi Auto-Rotate). Lưu xuống đĩa nếu ở DISK mode."""
        if self.original_image_path and self.original_image is None:
            import cv2, os
            import pathlib
            temp_dir = os.path.join(pathlib.Path(__file__).parent.parent.parent.resolve(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Chỉ ghi đè ra temp nếu file gốc không ở trong temp, để tránh loạn
            temp_path = os.path.join(temp_dir, f"orig_{os.path.basename(self.page_id)}.png")
            cv2.imwrite(temp_path, image)
            self.original_image_path = temp_path
        else:
            self.original_image = image

    def get_inpainted_image(self) -> Optional[np.ndarray]:
        """Lấy ảnh đã xóa chữ từ RAM hoặc đọc từ đĩa nếu đang ở DISK mode."""
        if self.inpainted_image is not None:
            return self.inpainted_image
        if self.inpainted_image_path:
            import cv2
            return cv2.imread(self.inpainted_image_path)
        return None

    def set_inpainted_image(self, image: np.ndarray):
        """Cập nhật ảnh inpaint. Lưu xuống đĩa nếu ở DISK mode."""
        if self.original_image_path and self.original_image is None:
            import cv2, os
            import pathlib
            temp_dir = os.path.join(pathlib.Path(__file__).parent.parent.parent.resolve(), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            temp_path = os.path.join(temp_dir, f"inpaint_{os.path.basename(self.page_id)}.png")
            cv2.imwrite(temp_path, image)
            self.inpainted_image_path = temp_path
            self.inpainted_image = None
        else:
            self.inpainted_image = image

    def get_background_image(self) -> Optional[np.ndarray]:
        """Lấy ảnh nền (ưu tiên ảnh đã xóa chữ, nếu chưa có thì lấy ảnh gốc)."""
        bg = self.get_inpainted_image()
        if bg is not None:
            return bg
        return self.get_original_image()
