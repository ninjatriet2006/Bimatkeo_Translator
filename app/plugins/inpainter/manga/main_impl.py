"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.manga.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Manga Inpainter vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_manga_model, inpaint.inpaint_manga
- IN = OUT: Triển khai BaseInpainter, đóng gói plugin Manga.
=============================================================================
"""
import numpy as np
from typing import List

from app.core.inpainter.interfaces import BaseInpainter
from app.core.shared_registry import InpainterFactory

from app.plugins.inpainter.manga.loader import load_manga_model
from app.plugins.inpainter.manga.inpaint import inpaint_manga

@InpainterFactory.register("manga")
class MangaInpainter_Impl(BaseInpainter):
    MODELS = [
        {'key': 'manga', 'label': 'mayocream/lama-manga (ONNX)', 'check_file': 'models/Inpainter/Manga_ONNX/erika.onnx'},
        {'key': 'manga_inpaint_v3', 'label': 'dremaz/manga-inpaint-v3 (MPE)', 'check_file': 'models/Inpainter/Manga_Inpaint_V3/inpainting_lama_mpe.ckpt', 'source': 'hf://dremaz/manga-inpaint-v3@inpainting_lama_mpe.ckpt'},
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
        self.session, self.input_name_img, self.input_name_mask, self.is_loaded = load_manga_model(
            model_path=model_path, log_callback=kwargs.get("log_callback"), **kwargs
        )

    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        return inpaint_manga(
            session=self.session, 
            is_loaded=self.is_loaded, 
            input_name_img=self.input_name_img, 
            input_name_mask=self.input_name_mask, 
            config=self.config, 
            image=image, 
            bboxes=bboxes
        )
