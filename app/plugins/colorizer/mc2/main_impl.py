"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.colorizer.mc2.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký MC2 Colorizer vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_mc2_model, colorize.colorize_mc2
- IN = OUT: Khai báo plugin MC2 Colorizer.
=============================================================================
"""
import os
import numpy as np
from app.core.shared_registry import ColorizerFactory

from app.plugins.colorizer.mc2.loader import load_mc2_model
from app.plugins.colorizer.mc2.colorize import colorize_mc2

@ColorizerFactory.register("mc2")
class MC2_Colorizer:
    MODELS = [
        {
            "key": "mc2",
            "label": "MC2 Colorizer",
            "check_file": os.path.join("models", "Colorizer", "mc2", "mc2_model.onnx"),
            "source": ""
        }
    ]

    def load_model(self, model_path: str, **kwargs):
        load_mc2_model(model_path, **kwargs)

    def colorize(self, image: np.ndarray) -> np.ndarray:
        return colorize_mc2(image)
