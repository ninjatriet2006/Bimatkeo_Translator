"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.manga.loader
- RESPONSIBILITY: Tải mô hình Manga Inpaint. Gọi trực tiếp hàm tải của LaMa do dùng chung kiến trúc ONNX.
- CALLED BY: app.plugins.inpainter.manga.main_impl
- CALLS TO: app.plugins.inpainter.lama.loader.load_lama_model
- IN = OUT: Passthrough tới load_lama_model.
=============================================================================
"""
from app.plugins.inpainter.lama.loader import load_lama_model

def load_manga_model(model_path: str, log_callback=None, **kwargs):
    session, input_name_img, input_name_mask, is_loaded = load_lama_model(
        model_path=model_path, log_callback=log_callback, **kwargs
    )
    if is_loaded:
        msg = f"[Manga] Model loaded successfully: {model_path}"
        if log_callback: log_callback("INFO", msg)
        else: print(msg)
    return session, input_name_img, input_name_mask, is_loaded
