"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.colorizer.ddcolor.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký DDColor vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_ddcolor_model, colorize.colorize_ddcolor
- IN = OUT: Khai báo plugin DDColor.
=============================================================================
"""
import os
import numpy as np
from app.core.shared_registry import ColorizerFactory

from app.plugins.colorizer.ddcolor.loader import load_ddcolor_model
from app.plugins.colorizer.ddcolor.colorize import colorize_ddcolor

@ColorizerFactory.register("ddcolor")
class DDColor_Colorizer:
    MODELS = [
        {
            "key": "ddcolor",
            "label": "DDColor",
            "check_file": os.path.join("models", "Colorizer", "ddcolor", "ddcolor_model.onnx"),
            "source": ""
        }
    ]

    def load_model(self, model_path: str, **kwargs):
        load_ddcolor_model(model_path, **kwargs)

    def colorize(self, image: np.ndarray) -> np.ndarray:
        return colorize_ddcolor(image)
