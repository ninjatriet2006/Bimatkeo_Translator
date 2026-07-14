"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.mbart50.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký MBart50 Translator vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: translate.translate_mbart50
- IN = OUT: Khai báo plugin MBart50 theo chuẩn BaseOfflineTranslator.
=============================================================================
"""
from typing import List
from app.core.shared_registry import TranslatorFactory
from app.core.translator.base_offline import BaseOfflineTranslator
from app.plugins.translator.mbart50.translate import translate_mbart50

@TranslatorFactory.register("mbart50")
class MBart50Translator(BaseOfflineTranslator):
    MODELS = [
        {'key': 'mbart50', 'check_file': 'models/Offline Translator/MBart50/pytorch_model.bin', 'source': 'hf://facebook/mbart-large-50-many-to-many-mmt'},
    ]

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        return translate_mbart50(self, texts, src_lang, tgt_lang)
