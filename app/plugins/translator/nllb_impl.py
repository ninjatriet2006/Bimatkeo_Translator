from typing import List
from app.core.shared_registry import TranslatorFactory
from app.core.downloader import ModelDownloader
from app.core.translator.base_offline import BaseOfflineTranslator

@TranslatorFactory.register("nllb")
class NLLBTranslator(BaseOfflineTranslator):
    MODELS = [
        {'key': 'nllb', 'check_file': 'models/Offline Translator/NLLB/pytorch_model.bin', 'source': 'hf://facebook/nllb-200-distilled-600M'},
    ]

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        if self.tokenizer is None or self.model is None:
            return []
            
        # NLLB uses different BCP-47 codes like eng_Latn, vie_Latn, jpn_Jpan
        lang_map = {
            "ENG": "eng_Latn", "VIE": "vie_Latn", "JPN": "jpn_Jpan", 
            "KOR": "kor_Hang", "CHI": "zho_Hans"
        }
        src_token = lang_map.get(src_lang, "eng_Latn")
        tgt_token = lang_map.get(tgt_lang, "vie_Latn")
        
        self.tokenizer.src_lang = src_token
        encoded = self.tokenizer(texts, return_tensors="pt", padding=True).to(self.device)
        
        forced_bos_token_id = self.tokenizer.lang_code_to_id[tgt_token]
        
        generated_tokens = self.model.generate(
            **encoded,
            forced_bos_token_id=forced_bos_token_id,
            max_length=128
        )
        
        results = self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
        return results
