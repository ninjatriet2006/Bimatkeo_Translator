"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.opencv.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký OpenCV Inpainter vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_opencv_model, inpaint.inpaint_opencv
- IN = OUT: Triển khai BaseInpainter, đóng gói plugin OpenCV.
=============================================================================
"""
from typing import List
import numpy as np
from app.core.inpainter.interfaces import BaseInpainter
from app.core.shared_registry import InpainterFactory

from app.plugins.inpainter.opencv.loader import load_opencv_model
from app.plugins.inpainter.opencv.inpaint import inpaint_opencv

@InpainterFactory.register("opencv")
class OpenCVInpainter_Impl(BaseInpainter):
    MODELS = [
        {'key': 'opencv', 'label': 'opencv'},
    ]

    REQUIRES_SD_BASE_MODEL = False

    def __init__(self):
        self.is_loaded = True

    def load_model(self, model_path: str, **kwargs) -> None:
        load_opencv_model(model_path, **kwargs)

    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        return inpaint_opencv(image, bboxes)
