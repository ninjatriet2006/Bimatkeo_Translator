"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.opencv.loader
- RESPONSIBILITY: Tải mô hình OpenCV Inpainter (thực chất là hàm nội bộ không cần tải).
- CALLED BY: app.plugins.inpainter.opencv.main_impl
- CALLS TO: None
- IN = OUT: Hàm mock, trả về True.
=============================================================================
"""
def load_opencv_model(model_path: str, **kwargs) -> bool:
    return True
