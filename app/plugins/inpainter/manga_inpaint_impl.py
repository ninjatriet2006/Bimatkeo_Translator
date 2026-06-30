import os
from typing import Dict, Union

from app.core.factories import InpainterFactory
from app.plugins.inpainter.lama_impl import LamaInpainter_Impl

@InpainterFactory.register("manga")
class MangaInpainter_Impl(LamaInpainter_Impl):
    DISPLAY_NAME: Union[str, Dict[str, str]] = {
        "manga": "mayocream/lama-manga (ONNX)"
    }
    
    def __init__(self):
        super().__init__()
        # Manga inpaint is heavily based on LaMa and shares the same ONNX input/output logic.
        # It operates by inheriting load_model and inpaint from LamaInpainter_Impl.
        
    def load_model(self, model_path: str, **kwargs) -> None:
        """Tải mô hình Manga Inpaint lên bộ nhớ. Sử dụng chung pipeline ONNX với LaMa."""
        # Optional: any specific preprocessing or logging overrides can be done here.
        super().load_model(model_path, **kwargs)
        if self.session is not None:
            print(f"[Manga] Model loaded successfully: {model_path}")
