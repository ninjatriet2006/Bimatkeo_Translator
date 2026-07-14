"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.sd.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Stable Diffusion Inpainter vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_sd_model, inpaint.inpaint_sd
- IN = OUT: Triển khai BaseInpainter, đóng gói plugin Stable Diffusion.
=============================================================================
"""
import numpy as np
from typing import List

from app.core.inpainter.interfaces import BaseInpainter
from app.core.shared_registry import InpainterFactory

from app.plugins.inpainter.sd.loader import load_sd_model
from app.plugins.inpainter.sd.inpaint import inpaint_sd

@InpainterFactory.register("sd")
class SDInpainter_Impl(BaseInpainter):
    MODELS = [
        {'key': 'sd'},
    ]

    def __init__(self):
        self.model_path = None
        self.is_loaded = False
        self.pipeline = None
        self.config = {}

    def load_model(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        self.config = kwargs
        self.pipeline, self.is_loaded = load_sd_model(
            model_path=model_path, log_callback=kwargs.get("log_callback"), **kwargs
        )

    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        return inpaint_sd(
            pipeline=self.pipeline, 
            is_loaded=self.is_loaded, 
            image=image, 
            bboxes=bboxes
        )

    def release_model(self) -> None:
        if self.pipeline is not None:
            import torch # type: ignore
            del self.pipeline
            self.pipeline = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        self.is_loaded = False
        if "log_callback" in self.config and self.config["log_callback"]:
            self.config["log_callback"]("INFO", "SD Inpainter model released.")
