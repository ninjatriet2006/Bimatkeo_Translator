"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_context.context_writer
- RESPONSIBILITY: Pure functions for mutating/writing image data in PageContext (RAM/Disk).
- CALLED BY: app.core.ocr, app.core.inpainter, app.core.pipeline
- CALLS TO: app.core.shared_context.dto
- IN = OUT: Modifies context in-place or writes to temporary disk storage.
=============================================================================
"""
import os
import cv2
import numpy as np
import pathlib
from app.core.shared_context.dto import PageContext

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
