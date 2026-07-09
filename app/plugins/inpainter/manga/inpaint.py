"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.manga.inpaint
- RESPONSIBILITY: Thực thi inpainting ảnh. Dùng lại module xử lý của LaMa do dùng chung kiến trúc.
- CALLED BY: app.plugins.inpainter.manga.main_impl
- CALLS TO: app.plugins.inpainter.lama.inpaint.inpaint_lama
- IN = OUT: Passthrough tới inpaint_lama.
=============================================================================
"""
import numpy as np
from typing import List
from app.plugins.inpainter.lama.inpaint import inpaint_lama

def inpaint_manga(session, is_loaded, input_name_img, input_name_mask, config, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
    return inpaint_lama(
        session=session,
        is_loaded=is_loaded,
        input_name_img=input_name_img,
        input_name_mask=input_name_mask,
        config=config,
        image=image,
        bboxes=bboxes
    )
