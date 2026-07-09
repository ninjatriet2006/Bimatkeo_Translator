import os
import time
from typing import List, Tuple
from PIL import Image
import numpy as np

from app.core.inpainter.interfaces import BaseInpainter
from app.core.shared_registry import InpainterFactory

@InpainterFactory.register("opencv")
class OpenCVInpainter_Impl(BaseInpainter):
    MODELS = [
        {'key': 'opencv', 'label': 'opencv'},
    ]

    REQUIRES_SD_BASE_MODEL = False

    def __init__(self):
        self.is_loaded = True

    def load_model(self, model_path: str, **kwargs) -> None:
        pass

    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        if not bboxes:
            return image
        
        import cv2
        import numpy as np

        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        for box in bboxes:
            x_min, y_min, x_max, y_max = box
            pad = 5
            x1 = max(0, x_min - pad)
            y1 = max(0, y_min - pad)
            x2 = min(image.shape[1], x_max + pad)
            y2 = min(image.shape[0], y_max + pad)
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
            
        return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)
