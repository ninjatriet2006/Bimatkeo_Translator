"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.pixel_48px_ctc.loader
- RESPONSIBILITY: Tải mô hình Pixel 48px CTC ONNX và từ điển ký tự.
- CALLED BY: app.plugins.recognizer.pixel_48px_ctc.main_impl
- CALLS TO: None
- IN = OUT: Nhận model_path, trả về session, input_name, và character_dict.
=============================================================================
"""
import os
from app.core.shared_registry import RecognizerFactory
from app.core.downloader import ModelDownloader

def _load_dict(dict_path: str):
    character_dict = []
    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            char = line.strip('\n')
            character_dict.append(char)
    return character_dict

def load_pixel_48px_ctc_model(model_path: str | None = None, log_callback=None, **kwargs):
    try:
        import onnxruntime as ort
    except ImportError:
        raise RuntimeError("Thư viện 'onnxruntime' hoặc 'onnxruntime-gpu' chưa được cài đặt.")
        
    if not model_path:
        raise ValueError("model_path is required")
        
    target_dir = os.path.dirname(model_path)
    expected_filename = os.path.basename(model_path)
    dict_filename = "alphabet-all-v5.txt"
    
    if not os.path.exists(model_path) or not os.path.exists(os.path.join(target_dir, dict_filename)):
        url = RecognizerFactory.get_source_url_from_registry("offline_ocr", "48px_ctc")
        if url:
            if log_callback: log_callback("INFO", f"Đang tiến hành tải tự động 48px CTC ONNX từ {url}...")
            success = ModelDownloader.download_and_extract(
                url=url, target_dir=target_dir, expected_files=[expected_filename, dict_filename],
                log_callback=log_callback, extract=False
            )
            if not success:
                raise RuntimeError(f"Không thể khởi tạo mô hình 48px CTC tại {target_dir}")
        else:
            raise RuntimeError(f"Chưa có nguồn tải cho mô hình 48px CTC. Vui lòng tự nạp mô hình vào {target_dir}")
    
    dict_path = os.path.join(target_dir, dict_filename)
    character_dict = _load_dict(dict_path)
    
    try:
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        if log_callback: log_callback("INFO", f"Đang khởi tạo 48px CTC ONNX Rec với trọng số tại: {model_path}")
        session = ort.InferenceSession(model_path, providers=providers)
        input_name = session.get_inputs()[0].name
        if log_callback: log_callback("INFO", "Mô hình 48px CTC ONNX Rec đã nạp thành công.")
        return session, input_name, character_dict
    except Exception as e:
        raise RuntimeError(f"Lỗi khi khởi tạo 48px CTC ONNX Rec: {e}")
