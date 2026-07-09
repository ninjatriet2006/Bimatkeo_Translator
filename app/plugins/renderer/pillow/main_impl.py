"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.renderer.pillow.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Pillow Renderer vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_fonts, render.render_pillow
- IN = OUT: Khai báo plugin Pillow theo chuẩn BaseRenderer.
=============================================================================
"""
import numpy as np
from typing import List

from app.core.renderer.interfaces import BaseRenderer
from app.core.shared_registry import RendererFactory
from app.plugins.renderer.pillow.loader import load_fonts
from app.plugins.renderer.pillow.render import render_pillow

@RendererFactory.register("pillow_renderer")
class PillowRenderer_Impl(BaseRenderer):
    MODELS = [
        {'key': 'pillow_renderer'},
    ]

    def __init__(self):
        self.font_path = None
        self.default_font = None
        self.config = {}

    def load_fonts(self, font_path: str, **kwargs) -> None:
        load_fonts(self, font_path, **kwargs)

    def render(self, image: np.ndarray, bboxes: List[List[int]], texts: List[str]) -> np.ndarray:
        return render_pillow(self, image, bboxes, texts)
