"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.cloud_ocr.gemini_vision.loader
- RESPONSIBILITY: Lưu trữ cấu hình (API Key, endpoint) cho Gemini Vision OCR.
- CALLED BY: app.plugins.cloud_ocr.gemini_vision.main_impl
- CALLS TO: None
- IN = OUT: Nhận API key và params, lưu vào instance.
=============================================================================
"""

def load_gemini_vision(ocr_instance, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
    ocr_instance.api_key = api_key
    ocr_instance.endpoint = endpoint
    ocr_instance.model_name = model_name or "gemini-1.5-flash"
    if "log_callback" in kwargs:
        ocr_instance.log_callback = kwargs["log_callback"]
    if ocr_instance.log_callback:
        ocr_instance.log_callback("INFO", "Đã khởi tạo Gemini Vision OCR.")
