from abc import ABC, abstractmethod
import numpy as np
from typing import List

class BaseTextDetector(ABC):
    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """Tải mô hình phát hiện khung chữ."""
        pass

    @abstractmethod
    def detect(self, image: np.ndarray) -> List[List[int]]:
        """Quét tìm và trả về danh sách tọa độ bboxes [x_min, y_min, x_max, y_max]."""
        pass


class BaseTextRecognizer(ABC):
    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """Tải mô hình nhận diện chữ."""
        pass

    @abstractmethod
    def recognize(self, image_crop: np.ndarray) -> str:
        """Nhận ảnh đã cắt gọt chứa 1 dòng chữ và trả về văn bản text."""
        pass


class BaseUpscaler(ABC):
    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """Tải mô hình phóng đại ảnh."""
        pass

    @abstractmethod
    def upscale(self, image: np.ndarray, ratio: int) -> np.ndarray:
        """Nhận ảnh gốc và phóng to theo tỷ lệ để tăng độ nét."""
        pass


class BaseColorizer(ABC):
    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """Tải mô hình tô màu Manga."""
        pass

    @abstractmethod
    def colorize(self, image: np.ndarray) -> np.ndarray:
        """Nhận ảnh truyện trắng đen và trả về ảnh đã được tô màu."""
        pass


class BaseTranslator(ABC):
    @abstractmethod
    def load_weights(self, model_path: str) -> None:
        """Tải trọng số mô hình dịch thuật."""
        pass

    @abstractmethod
    def translate(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        """Dịch danh sách các đoạn text tiếng nguồn sang tiếng đích."""
        pass


class BaseInpainter(ABC):
    @abstractmethod
    def load_model(self, model_path: str) -> None:
        """Tải mô hình inpainting lên bộ nhớ."""
        pass

    @abstractmethod
    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        """Nhận ảnh gốc và tọa độ bboxes chứa văn bản, thực hiện xóa chữ và trả về mảng ảnh nền sạch."""
        pass


class BaseRenderer(ABC):
    @abstractmethod
    def load_fonts(self, font_path: str) -> None:
        """Cấu hình và nạp font chữ."""
        pass

    @abstractmethod
    def render(self, image: np.ndarray, bboxes: List[List[int]], texts: List[str]) -> np.ndarray:
        """Vẽ văn bản tiếng đích (texts) lên ảnh nền đã làm sạch (image) tại đúng vị trí bboxes."""
        pass
