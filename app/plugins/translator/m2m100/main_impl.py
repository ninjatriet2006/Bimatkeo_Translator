"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.m2m100.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký M2M100 Translator vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_m2m100_model, translate.translate_m2m100
- IN = OUT: Khai báo plugin M2M100 theo chuẩn BaseOfflineTranslator.
=============================================================================
"""
from typing import List
from app.core.shared_registry import TranslatorFactory
from app.core.translator.base_offline import BaseOfflineTranslator
from app.plugins.translator.m2m100.loader import load_m2m100_model
from app.plugins.translator.m2m100.translate import translate_m2m100

@TranslatorFactory.register("m2m100")
class M2M100Translator(BaseOfflineTranslator):
    MODELS = [
        {'key': 'm2m100', 'check_file': 'models/Offline Translator/M2M100/sentencepiece.model'},
    ]
    
    def load_weights(self, model_path: str) -> None:
        status = load_m2m100_model(self, model_path)
        if status == "USE_SUPER":
            super().load_weights(model_path)

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        return translate_m2m100(self, texts, src_lang, tgt_lang)
