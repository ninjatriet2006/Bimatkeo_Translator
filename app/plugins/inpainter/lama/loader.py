"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.lama.loader
- RESPONSIBILITY: Tải mô hình LaMa ONNX (Download/Extract/Load vào RAM).
- CALLED BY: app.plugins.inpainter.lama.main_impl
- CALLS TO: app.core.downloader.ModelDownloader, app.core.shared_registry.InpainterFactory
- IN = OUT: Nhận model_path, trả về session, tên inputs, cờ is_loaded.
=============================================================================
"""
import os
from app.core.shared_registry import InpainterFactory
from app.core.downloader import ModelDownloader

try:
    import onnxruntime as ort
except ImportError:
    ort = None

def load_lama_model(model_path: str, log_callback=None, **kwargs):
    key = "lama"
    is_loaded = False
    session = None
    input_name_img = None
    input_name_mask = None
        
    if not os.path.exists(model_path):
        source_url = InpainterFactory.get_source_url_from_registry("inpainter", key)
        if source_url:
            target_dir = os.path.dirname(model_path)
            expected_files = [os.path.basename(model_path)]
            if log_callback: log_callback("INFO", f"[LaMa] Downloading weights from {source_url}...")
            else: print(f"[LaMa] Downloading weights from {source_url}...")
            
            success = ModelDownloader.download_and_extract(
                source_url, target_dir, expected_files, extract=True
            )
            if not success:
                msg = f"[LaMa] Failed to download weights for {key}."
                if log_callback: log_callback("ERROR", msg)
                else: print(msg)
                return session, input_name_img, input_name_mask, is_loaded
        else:
            msg = f"[LaMa] No source URL found in registry for {key}."
            if log_callback: log_callback("ERROR", msg)
            else: print(msg)
            return session, input_name_img, input_name_mask, is_loaded
    
    if ort is None:
        msg = "[LaMa] onnxruntime is not installed. Inference will fallback to OpenCV."
        if log_callback: log_callback("WARNING", msg)
        else: print(msg)
        return session, input_name_img, input_name_mask, is_loaded

    try:
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
        session = ort.InferenceSession(model_path, providers=providers)
        
        inputs = session.get_inputs()
        for inp in inputs:
            if 'image' in inp.name.lower():
                input_name_img = inp.name
            elif 'mask' in inp.name.lower():
                input_name_mask = inp.name
                
        if not input_name_img:
            input_name_img = inputs[0].name
        if not input_name_mask:
            input_name_mask = inputs[1].name

        msg = f"[LaMa] ONNX Model loaded successfully: {model_path}"
        if log_callback: log_callback("INFO", msg)
        else: print(msg)
        
        is_loaded = True
    except Exception as e:
        msg = f"[LaMa] Failed to load ONNX model: {e}"
        if log_callback: log_callback("ERROR", msg)
        else: print(msg)
        
    return session, input_name_img, input_name_mask, is_loaded
