from typing import List
from app.core.factories import TranslatorFactory
from .base_offline import BaseOfflineTranslator

@TranslatorFactory.register("m2m100")
class M2M100Translator(BaseOfflineTranslator):
    DISPLAY_NAME = {
        "m2m100": "facebook/m2m100_418M",
        "m2m100_big": "facebook/m2m100_1.2B"
    }
    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        if self.tokenizer is None or self.model is None:
            return []
        
        # Language code mapping logic should be handled here
        # Example mapping: ENG -> en, VIE -> vi, JPN -> ja
        lang_map = {
            "ENG": "en", "VIE": "vi", "JPN": "ja", "KOR": "ko", "CHI": "zh"
        }
        src_token = lang_map.get(src_lang, "en")
        tgt_token = lang_map.get(tgt_lang, "vi")
        
        self.tokenizer.src_lang = src_token
        encoded = self.tokenizer(texts, return_tensors="pt", padding=True).to(self.device)
        
        # M2M100 forces target language using forced_bos_token_id
        forced_bos_token_id = self.tokenizer.get_lang_id(tgt_token)
        
        generated_tokens = self.model.generate(
            **encoded,
            forced_bos_token_id=forced_bos_token_id,
            max_length=128
        )
        
        results = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
        return results
