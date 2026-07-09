"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.interfaces
- RESPONSIBILITY: Base interfaces for OCR-related components (Detector, Recognizer, CloudOCR).
- CALLED BY: app.core.ocr, app.plugins
- CALLS TO: None
- IN = OUT: Enforces architectural contracts without implementing logic.
=============================================================================
"""
from abc import ABC, abstractmethod
import numpy as np
from typing import Union, Dict

class BaseTextDetector(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""

    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        """Tải mô hình phát hiện khung chữ."""
        pass

    @abstractmethod
    def detect(self, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
        """Quét tìm và trả về (danh sách bboxes [x_min, y_min, x_max, y_max], danh sách polygons)."""
        pass

class BaseTextRecognizer(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""

    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        """Tải mô hình nhận diện chữ."""
        pass

    @abstractmethod
    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        """
        Takes an image crop containing text and returns the recognized text and a confidence score (0.0 to 1.0).
        """
        pass

class BaseCloudOCR(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""

    @abstractmethod
    def load_model(self, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
        """
        Thiết lập kết nối với Cloud API.
        """
        pass

    @abstractmethod
    def recognize_full_page(self, image: np.ndarray, lang: str = "en") -> list[dict]:
        """
        Nhận diện văn bản và tọa độ từ ảnh toàn trang sử dụng Cloud API.
        Trả về danh sách các dict, ví dụ:
        [
            {"box": [x1, y1, x2, y2], "text": "Hello World", "score": 0.99},
            ...
        ]
        """
        pass
