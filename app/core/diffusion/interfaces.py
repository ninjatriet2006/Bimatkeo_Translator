"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.diffusion.interfaces
- RESPONSIBILITY: Base interfaces for Diffusion components.
- CALLED BY: app.core.diffusion, app.plugins
- CALLS TO: None
- IN = OUT: Enforces architectural contracts without implementing logic.
=============================================================================
"""
from abc import ABC, abstractmethod
import numpy as np
from typing import List, Union, Dict

class BaseDiffusionModel(ABC):
    DISPLAY_NAME: Union[str, Dict[str, str]] = ""

    @abstractmethod
    def load_model(self, model_path: str, **kwargs) -> None:
        """Tải mô hình diffusion lên bộ nhớ."""
        pass

    @abstractmethod
    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        """Xóa chữ hoặc tái tạo bối cảnh dựa trên mask và prompt."""
        pass

    # Có thể mở rộng thêm hàm render_text_with_diffusion(self, ...) sau này.
