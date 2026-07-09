"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.paddle_onnx.loader
- RESPONSIBILITY: Tải mô hình Paddle ONNX bằng onnxruntime.
- CALLED BY: app.plugins.detector.paddle_onnx.main_impl
- CALLS TO: None
- IN = OUT: Nhận model_path, trả về session và input_name.
=============================================================================
"""
import os

def load_paddle_onnx_model(model_path: str | None = None, log_callback=None, **kwargs):
    try:
        import onnxruntime as ort
    except ImportError:
        raise RuntimeError("Thư viện 'onnxruntime' hoặc 'onnxruntime-gpu' chưa được cài đặt.")
        
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(f"Không tìm thấy model ONNX tại: {model_path}")
        
    try:
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        if log_callback: 
            log_callback("INFO", f"Đang khởi tạo PaddleONNX với trọng số tại: {model_path}")
        session = ort.InferenceSession(model_path, providers=providers)
        input_name = session.get_inputs()[0].name
        if log_callback: 
            log_callback("INFO", "Mô hình Paddle ONNX đã nạp thành công.")
        return session, input_name
    except Exception as e:
        raise RuntimeError(f"Lỗi khi khởi tạo Paddle ONNX: {e}")
