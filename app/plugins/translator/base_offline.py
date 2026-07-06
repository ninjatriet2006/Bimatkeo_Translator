import os
from typing import List, Union

from app.core.interfaces import BaseTranslator
from app.core.factories import TranslatorFactory

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
        self.log_callback = None
        self.is_loaded = False

    def load_weights(self, model_path: str) -> None:
        if not model_path:
            return
            
        if not HAS_TRANSFORMERS:
            if self.log_callback:
                self.log_callback("ERROR", "Please install transformers library: pip install transformers sentencepiece")
            return
            
        try:
            if os.path.isfile(model_path):
                model_path = os.path.dirname(model_path)
                
            if self.log_callback:
                self.log_callback("INFO", f"Loading offline translator from: {model_path} to {self.device}")
                
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
            self.model = AutoModelForSeq2SeqLM.from_pretrained(model_path).to(self.device)
            self.is_loaded = True
            
            if self.log_callback:
                self.log_callback("INFO", "Offline translator loaded successfully.")
        except Exception as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Failed to load offline model: {e}")

    def translate(self, texts: List[str], src_lang: str, tgt_lang: str, context_texts: List[str] | None = None) -> List[Union[str, dict]]:
        if not self.is_loaded or not texts:
            return texts
            
        # No pre-translation glossary replace
        processed_texts = texts
        
        translated_texts = self._perform_translation(processed_texts, src_lang, tgt_lang)
        
        # No post-translation replace
        final_texts = translated_texts
        return final_texts

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        raise NotImplementedError

