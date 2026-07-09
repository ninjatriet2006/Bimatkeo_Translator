"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.inpainter.interfaces
- RESPONSIBILITY: Base interfaces for Inpainting, Upscaling, and Colorizing components.
- CALLED BY: app.core.inpainter, app.plugins
- CALLS TO: None
- IN = OUT: Enforces architectural contracts without implementing logic.
=============================================================================
"""
from abc import ABC, abstractmethod
import numpy as np
from typing import List, Union, Dict

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
