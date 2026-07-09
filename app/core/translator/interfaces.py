"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.translator.interfaces
- RESPONSIBILITY: Base interfaces for Translation components.
- CALLED BY: app.core.translator, app.plugins
- CALLS TO: None
- IN = OUT: Enforces architectural contracts without implementing logic.
=============================================================================
"""
from abc import ABC, abstractmethod
from typing import List, Union, Dict

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
    def translate(self, texts: List[str], src_lang: str, tgt_lang: str, context_texts: List[str] | None = None) -> List[Union[str, dict]]:
        """Dịch danh sách các đoạn text tiếng nguồn sang tiếng đích."""
        pass
