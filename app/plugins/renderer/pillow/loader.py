"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.renderer.pillow.loader
- RESPONSIBILITY: Load font file cho Pillow Renderer.
- CALLED BY: app.plugins.renderer.pillow.main_impl
- CALLS TO: None
- IN = OUT: Nhận font_path và cấu hình, lưu vào instance.
=============================================================================
"""
import os
from PIL import ImageFont

def load_fonts(renderer_instance, font_path: str, **kwargs) -> None:
    renderer_instance.font_path = font_path
    renderer_instance.config = kwargs
    # If font path doesn't exist or is empty, fallback to default PIL font
    if not renderer_instance.font_path or not os.path.exists(renderer_instance.font_path):
        print(f"[Renderer] Font path invalid: {renderer_instance.font_path}. Using default system font.")
        renderer_instance.default_font = ImageFont.load_default()
    else:
        print(f"[Renderer] Loaded font from {renderer_instance.font_path}")
