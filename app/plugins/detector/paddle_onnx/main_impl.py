"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.detector.paddle_onnx.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Paddle ONNX text detector vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_paddle_onnx_model, detect.detect_text_paddle_onnx
- IN = OUT: Triển khai BaseTextDetector, đóng gói plugin Paddle ONNX.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextDetector
from app.core.shared_registry import DetectorFactory

from app.plugins.detector.paddle_onnx.loader import load_paddle_onnx_model
from app.plugins.detector.paddle_onnx.detect import detect_text_paddle_onnx

@DetectorFactory.register("paddle_onnx")
class PaddleONNXDetectorImpl(BaseTextDetector):
    MODELS = [
        {'key': 'paddle_onnx_v6_tiny', 'check_file': 'models/Detector/Paddle_ONNX/Tiny/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_tiny_det_onnx@inference.onnx'},
        {'key': 'paddle_onnx_v6_small', 'check_file': 'models/Detector/Paddle_ONNX/Small/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_small_det_onnx@inference.onnx'},
        {'key': 'paddle_onnx_v6_medium', 'check_file': 'models/Detector/Paddle_ONNX/Medium/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_medium_det_onnx@inference.onnx'},
    ]

    def __init__(self):
        self.session = None
        self.input_name = None
        self.config = {}
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.config = kwargs
        self.session, self.input_name = load_paddle_onnx_model(
            model_path=model_path, log_callback=log_callback, **kwargs
        )
        
    def detect(self, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
        return detect_text_paddle_onnx(self.session, self.input_name, self.config, image)
