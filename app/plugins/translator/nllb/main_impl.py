"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.nllb.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký NLLB Translator vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: translate.translate_nllb
- IN = OUT: Khai báo plugin NLLB theo chuẩn BaseOfflineTranslator.
=============================================================================
"""
from typing import List
from app.core.shared_registry import TranslatorFactory
from app.core.translator.base_offline import BaseOfflineTranslator
from app.plugins.translator.nllb.translate import translate_nllb

@TranslatorFactory.register("nllb")
class NLLBTranslator(BaseOfflineTranslator):
    MODELS = [
        {'key': 'nllb', 'check_file': 'models/Offline Translator/NLLB/pytorch_model.bin', 'source': 'hf://facebook/nllb-200-distilled-600M'},
        {'key': 'nllb_big', 'check_file': 'models/Offline Translator/NLLB/pytorch_model.bin', 'source': 'hf://facebook/nllb-200-distilled-1.3B'},
    ]

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        return translate_nllb(self, texts, src_lang, tgt_lang)
