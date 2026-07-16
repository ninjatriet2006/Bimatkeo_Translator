"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.api.interfaces
- RESPONSIBILITY: Base interfaces for unified API providers (e.g. Multimodal).
- CALLED BY: app.plugins.multimodal, app.core.api.manager
- CALLS TO: None
- IN = OUT: Defines the contract for an AI Provider that handles multiple modalities.
=============================================================================
"""
from abc import ABC, abstractmethod

class BaseMultimodal(ABC):
    @classmethod
    def get_supported_services(cls) -> list[str]:
        """
        Trả về danh sách các dịch vụ mà Provider này hỗ trợ.
        Ví dụ: ["Translator", "CloudOCR"]
        """
        return []

    @classmethod
    def is_multimodal(cls, model_name: str) -> bool:
        """
        Kiểm tra xem một model cụ thể có hỗ trợ xử lý hình ảnh (Vision) không.
        Mặc định trả về False.
        """
        return False
