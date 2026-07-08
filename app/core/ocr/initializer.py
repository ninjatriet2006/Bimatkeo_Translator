"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.initializer
- RESPONSIBILITY: Khởi tạo các Factory tương ứng dựa trên cấu hình (config).
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.factories (CloudOCRFactory, DetectorFactory, RecognizerFactory)
- IN = OUT: Nhận config_dict -> khởi tạo và trả về instance của CloudOCR, Detector, Recognizer.
=============================================================================
"""

from app.core.factories import CloudOCRFactory, DetectorFactory, RecognizerFactory
from app.core.downloader import ModelDownloader

class OCRInitializer:
    @staticmethod
    def initialize(config_dict: dict, log_callback=None):
        """
        Khởi tạo và trả về (cloud_ocr, detector, recognizer) dựa trên config.
        """
        enable_ocr = config_dict.get("pipeline", {}).get("enable_ocr", True)
        if not enable_ocr:
            return None, None, None

        ocr_category = config_dict.get("ocr_category", "Offline")
        
        cloud_ocr = None
        detector = None
        recognizer = None
        
        if ocr_category == "AI / Online":
            api_ocr_name = config_dict.get("api_ocr", "gemini_ocr")
            api_key = config_dict.get("ocr_api_key", config_dict.get("api_ocr_key", ""))
            endpoint = config_dict.get("ocr_api_endpoint", "")
            model_name = config_dict.get("ocr_api_model", "")
            try:
                cloud_ocr = CloudOCRFactory.create(api_ocr_name)
                cloud_ocr.load_model(api_key, endpoint=endpoint, model_name=model_name, log_callback=log_callback)
            except Exception as e:
                if log_callback:
                    log_callback("ERROR", f"Lỗi khởi tạo Cloud OCR: {e}")
                cloud_ocr = None
        else:
            detector_name = config_dict.get("offline_detector", "dbconvnext")
            ocr_name = config_dict.get("offline_ocr", "paddle_onnx_rec")

            try:
                det_path = ModelDownloader.get_model_path_from_registry("offline_detector", detector_name)
                detector = DetectorFactory.create(detector_name, model_path=det_path, log_callback=log_callback, **config_dict.get("detector", {}))
            except ValueError:
                detector = DetectorFactory.create("dummy_detector", log_callback=log_callback)
                
            try:
                rec_path = ModelDownloader.get_model_path_from_registry("offline_ocr", ocr_name)
                recognizer = RecognizerFactory.create(ocr_name, model_path=rec_path, log_callback=log_callback, **config_dict.get("ocr", {}))
            except ValueError:
                recognizer = RecognizerFactory.create("dummy_recognizer", log_callback=log_callback)

        return cloud_ocr, detector, recognizer
