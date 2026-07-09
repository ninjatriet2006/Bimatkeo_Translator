"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_context.context_reader
- RESPONSIBILITY: Pure functions for reading image data from PageContext (RAM/Disk).
- CALLED BY: app.core.pipeline, app.core.ocr, app.core.inpainter, app.core.renderer
- CALLS TO: app.core.shared_context.dto
- IN = OUT: Returns image arrays from context.
=============================================================================
"""
import cv2
import numpy as np
from typing import Optional
from app.core.shared_context.dto import PageContext

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
