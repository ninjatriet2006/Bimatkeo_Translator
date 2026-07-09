"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.renderer.interfaces
- RESPONSIBILITY: Base interfaces for Renderer components.
- CALLED BY: app.core.renderer, app.plugins
- CALLS TO: None
- IN = OUT: Enforces architectural contracts without implementing logic.
=============================================================================
"""
from abc import ABC, abstractmethod
import numpy as np
from typing import List, Union, Dict

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
