"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.paddle_onnx_rec.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Paddle ONNX Rec vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_paddle_onnx_rec_model, recognize.recognize_text_paddle_onnx_rec
- IN = OUT: Triển khai BaseTextRecognizer, đóng gói plugin Paddle ONNX Rec.
=============================================================================
"""
import numpy as np
from app.core.ocr.interfaces import BaseTextRecognizer
from app.core.shared_registry import RecognizerFactory

from app.plugins.recognizer.paddle_onnx_rec.loader import load_paddle_onnx_rec_model
from app.plugins.recognizer.paddle_onnx_rec.recognize import recognize_text_paddle_onnx_rec

@RecognizerFactory.register("paddle_onnx_rec")
class PaddleONNXRecognizerImpl(BaseTextRecognizer):
    MODELS = [
        {'key': 'paddle_onnx_rec_v6_tiny', 'check_file': 'models/OCR/Paddle_ONNX_Rec/Tiny/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_tiny_rec_onnx@inference.onnx'},
        {'key': 'paddle_onnx_rec_v6_small', 'check_file': 'models/OCR/Paddle_ONNX_Rec/Small/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_small_rec_onnx@inference.onnx'},
        {'key': 'paddle_onnx_rec_v6_medium', 'check_file': 'models/OCR/Paddle_ONNX_Rec/Medium/inference.onnx', 'source': 'hf://PaddlePaddle/PP-OCRv6_medium_rec_onnx@inference.onnx'},
    ]

    def __init__(self):
        self.session = None
        self.input_name = None
        self.character_dict = []
        
    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        self.session, self.input_name, self.character_dict = load_paddle_onnx_rec_model(
            model_path=model_path, log_callback=log_callback, **kwargs
        )

    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        return recognize_text_paddle_onnx_rec(self.session, self.input_name, self.character_dict, image_crop)
