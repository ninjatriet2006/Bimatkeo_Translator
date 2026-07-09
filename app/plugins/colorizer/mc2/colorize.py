"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.colorizer.mc2.colorize
- RESPONSIBILITY: Thực thi colorization (mock).
- CALLED BY: app.plugins.colorizer.mc2.main_impl
- CALLS TO: None
- IN = OUT: Nhận hình ảnh, trả về ảnh đã lên màu.
=============================================================================
"""
import numpy as np

def colorize_mc2(image: np.ndarray) -> np.ndarray:
    return image
