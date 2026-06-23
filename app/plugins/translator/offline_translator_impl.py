import os
from typing import List

from app.core.interfaces import BaseTranslator
from app.core.factories import TranslatorFactory
from app.core.translator_utils import GlossaryManager

try:
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM  # type: ignore
    import torch  # type: ignore
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class BaseOfflineTranslator(BaseTranslator):
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if HAS_TRANSFORMERS and torch.cuda.is_available() else "cpu"
        project_base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.glossary_manager = GlossaryManager(project_base_dir)
        self.log_callback = None
        self.is_loaded = False

    def load_weights(self, model_path: str) -> None:
        if not HAS_TRANSFORMERS:
            if self.log_callback:
                self.log_callback("ERROR", "Please install transformers library: pip install transformers sentencepiece")
            return
            
        try:
            if self.log_callback:
                self.log_callback("INFO", f"Loading offline translator from: {model_path} to {self.device}")
                
            self.tokenizer = AutoTokenizer.from_pretrained(model_path)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(self.device)
            self.is_loaded = True
            
            if self.log_callback:
                self.log_callback("INFO", "Offline translator loaded successfully.")
        except Exception as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Failed to load offline model: {e}")

    def translate(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        if not self.is_loaded or not texts:
            return texts
            
        # Optional: offline translation can also benefit from pre-translation glossary replace
        processed_texts = [self.glossary_manager.replace_pre_translation(t) for t in texts]
        
        translated_texts = self._perform_translation(processed_texts, src_lang, tgt_lang)
        
        # Post-translation replace
        final_texts = [self.glossary_manager.replace_post_translation(t) for t in translated_texts]
        return final_texts

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        raise NotImplementedError


@TranslatorFactory.register("m2m100")
class M2M100Translator(BaseOfflineTranslator):
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


@TranslatorFactory.register("nllb")
class NLLBTranslator(BaseOfflineTranslator):
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
