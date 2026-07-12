"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.paddle_onnx_rec.loader
- RESPONSIBILITY: Tải mô hình Paddle ONNX Rec và từ điển ký tự.
- CALLED BY: app.plugins.recognizer.paddle_onnx_rec.main_impl
- CALLS TO: None
- IN = OUT: Nhận model_path, trả về session, input_name, và character_dict.
=============================================================================
"""
import os
import urllib.request

def _download_dict_if_needed(dict_path, log_callback=None):
    if not os.path.exists(dict_path):
        if log_callback: log_callback("INFO", "Đang tải từ điển ký tự PaddleOCR (en_dict.txt)...")
        url = "https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/en_dict.txt"
        
        try:
            from app.core.base.constants import GLOBAL_RESOURCES
            configured_url = GLOBAL_RESOURCES.get("paddle_en_dict")
            if configured_url:
                url = configured_url
        except Exception as e:
            if log_callback: log_callback("WARNING", f"Không thể đọc cấu hình URL, sử dụng mặc định: {e}")
            
        try:
            os.makedirs(os.path.dirname(dict_path), exist_ok=True)
            urllib.request.urlretrieve(url, dict_path)
            if log_callback: log_callback("INFO", "Tải từ điển thành công.")
        except Exception as e:
            raise RuntimeError(f"Không thể tải từ điển ký tự từ Github: {e}")

def _load_dict(dict_path):
    character_dict = []
    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            char = line.strip('\n')
            if char != "":
                character_dict.append(char)
    character_dict.append(' ')
    character_dict.insert(0, 'blank')
    return character_dict

def load_paddle_onnx_rec_model(model_path: str | None = None, log_callback=None, **kwargs):
    try:
        import onnxruntime as ort
    except ImportError:
        raise RuntimeError("Thư viện 'onnxruntime' hoặc 'onnxruntime-gpu' chưa được cài đặt.")
        
    if not model_path or not os.path.exists(model_path):
        raise FileNotFoundError(f"Không tìm thấy model ONNX tại: {model_path}")
        
    # Lấy đường dẫn dict_path từ project root
    # loader.py nằm ở app/plugins/recognizer/paddle_onnx_rec/loader.py (cấp 4 từ app)
    # Ta có thể lấy root dễ nhất qua cách tương tự code cũ
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    dict_path = os.path.join(project_root, ".config", "models", "paddle_en_dict.txt")
    
    _download_dict_if_needed(dict_path, log_callback)
    character_dict = _load_dict(dict_path)
    
    try:
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        if log_callback: log_callback("INFO", f"Đang khởi tạo PaddleONNX Rec với trọng số tại: {model_path}")
        session = ort.InferenceSession(model_path, providers=providers)
        input_name = session.get_inputs()[0].name
        if log_callback: log_callback("INFO", "Mô hình Paddle ONNX Rec đã nạp thành công.")
        return session, input_name, character_dict
    except Exception as e:
        raise RuntimeError(f"Lỗi khi khởi tạo Paddle ONNX Rec: {e}")
