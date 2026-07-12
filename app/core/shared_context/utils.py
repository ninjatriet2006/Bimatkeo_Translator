"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_context.utils
- RESPONSIBILITY: Pure functions for reading, mutating, and checking PageContext (RAM/Disk).
- CALLED BY: app.core.pipeline, app.core.ocr, app.core.inpainter, app.core.renderer
- CALLS TO: app.core.shared_context.dto
- IN = OUT: Helper methods for interacting with PageContext without deep coupling.
=============================================================================
"""
import os
import cv2
import numpy as np
import pathlib
from typing import Optional
from app.core.shared_context.dto import PageContext

# --- READER METHODS ---

def get_original_image(ctx: PageContext) -> Optional[np.ndarray]:
    """Lấy ảnh gốc từ RAM hoặc đọc từ đĩa nếu đang ở DISK mode."""
    if ctx.original_image is not None:
        return ctx.original_image
    if ctx.original_image_path:
        return cv2.imread(ctx.original_image_path)
    return None

def get_inpainted_image(ctx: PageContext) -> Optional[np.ndarray]:
    """Lấy ảnh đã xóa chữ từ RAM hoặc đọc từ đĩa nếu đang ở DISK mode."""
    if ctx.inpainted_image is not None:
        return ctx.inpainted_image
    if ctx.inpainted_image_path:
        return cv2.imread(ctx.inpainted_image_path)
    return None

def get_background_image(ctx: PageContext) -> Optional[np.ndarray]:
    """Lấy ảnh nền (ưu tiên ảnh đã xóa chữ, nếu chưa có thì lấy ảnh gốc)."""
    bg = get_inpainted_image(ctx)
    if bg is not None:
        return bg
    return get_original_image(ctx)

# --- WRITER METHODS ---

def set_original_image(ctx: PageContext, image: np.ndarray):
    """Cập nhật ảnh gốc (thường dùng khi Auto-Rotate). Lưu xuống đĩa nếu ở DISK mode."""
    if ctx.original_image_path and ctx.original_image is None:
        temp_dir = os.path.join(pathlib.Path(__file__).parent.parent.parent.parent.resolve(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, f"orig_{os.path.basename(ctx.page_id)}.png")
        cv2.imwrite(temp_path, image)
        ctx.original_image_path = temp_path
    else:
        ctx.original_image = image

def set_inpainted_image(ctx: PageContext, image: np.ndarray):
    """Cập nhật ảnh inpaint. Lưu xuống đĩa nếu ở DISK mode."""
    if ctx.original_image_path and ctx.original_image is None:
        temp_dir = os.path.join(pathlib.Path(__file__).parent.parent.parent.parent.resolve(), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, f"inpaint_{os.path.basename(ctx.page_id)}.png")
        cv2.imwrite(temp_path, image)
        ctx.inpainted_image_path = temp_path
        ctx.inpainted_image = None
    else:
        ctx.inpainted_image = image

# --- UTILS METHODS ---

def is_disk_mode(ctx: PageContext) -> bool:
    """Kiểm tra xem context có đang hoạt động ở DISK mode không."""
    return ctx.original_image_path is not None and ctx.original_image is None
