"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.lama.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký LaMa Inpainter vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_lama_model, inpaint.inpaint_lama
- IN = OUT: Triển khai BaseInpainter, đóng gói plugin LaMa.
=============================================================================
"""
import numpy as np
from typing import List

from app.core.inpainter.interfaces import BaseInpainter
from app.core.shared_registry import InpainterFactory

from app.plugins.inpainter.lama.loader import load_lama_model
from app.plugins.inpainter.lama.inpaint import inpaint_lama

@InpainterFactory.register("lama")
class LamaInpainter_Impl(BaseInpainter):
    MODELS = [
        {'key': 'lama', 'check_file': 'models/Inpainter/Lama_ONNX/lama_fp32.onnx', 'source': 'hf://Carve/LaMa-ONNX@lama_fp32.onnx'},
    ]

    def __init__(self):
        self.model_path = None
        self.is_loaded = False
        self.session = None
        self.input_name_img = None
        self.input_name_mask = None
        self.config = {}

    def load_model(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        self.config = kwargs
        self.session, self.input_name_img, self.input_name_mask, self.is_loaded = load_lama_model(
            model_path=model_path, log_callback=kwargs.get("log_callback"), **kwargs
        )

    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        return inpaint_lama(
            session=self.session, 
            is_loaded=self.is_loaded, 
            input_name_img=self.input_name_img, 
            input_name_mask=self.input_name_mask, 
            config=self.config, 
            image=image, 
            bboxes=bboxes
        )
