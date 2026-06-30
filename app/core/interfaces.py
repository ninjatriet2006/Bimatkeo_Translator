from abc import ABC, abstractmethod
import numpy as np
from typing import List, Union, Dict

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


class BaseUpscaler(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""

    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        """Tải mô hình phóng đại ảnh."""
        pass

    @abstractmethod
    def upscale(self, image: np.ndarray, ratio: int) -> np.ndarray:
        """Nhận ảnh gốc và phóng to theo tỷ lệ để tăng độ nét."""
        pass


class BaseColorizer(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""

    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        """Tải mô hình tô màu Manga."""
        pass

    @abstractmethod
    def colorize(self, image: np.ndarray) -> np.ndarray:
        """Nhận ảnh truyện trắng đen và trả về ảnh đã được tô màu."""
        pass


class BaseTranslator(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""
    STATIC_MODELS: List[str] = []
    MAX_CHARS: int = -1

    @classmethod
    def get_supported_languages(cls) -> dict:
        """Trả về dictionary chứa năng lực ngôn ngữ. VD: {'__any__': '__all__'} hoặc {'__any__': ['ENG', 'VIN']}"""
        return {'__any__': '__all__'}

    @abstractmethod
    def load_weights(self, model_path: str) -> None:
        """Tải trọng số mô hình dịch thuật."""
        pass

    @abstractmethod
    def translate(self, texts: List[str], src_lang: str, tgt_lang: str, context_texts: List[str] = None) -> List[Union[str, dict]]:
        """Dịch danh sách các đoạn text tiếng nguồn sang tiếng đích."""
        pass


class BaseInpainter(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""

    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        """Tải mô hình inpainting lên bộ nhớ."""
        pass

    @abstractmethod
    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        """Nhận ảnh gốc và tọa độ bboxes chứa văn bản, thực hiện xóa chữ và trả về mảng ảnh nền sạch."""
        pass


class BaseRenderer(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""

    @abstractmethod
    def load_fonts(self, font_path: str, **kwargs) -> None:
        """Cấu hình và nạp font chữ."""
        pass

    @abstractmethod
    def render(self, image: np.ndarray, bboxes: List[List[int]], texts: List[str]) -> np.ndarray:
        """Vẽ văn bản tiếng đích (texts) lên ảnh nền đã làm sạch (image) tại đúng vị trí bboxes."""
        pass
