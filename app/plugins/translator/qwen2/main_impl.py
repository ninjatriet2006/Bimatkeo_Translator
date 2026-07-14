"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.qwen2.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký Qwen2 Translator (LLM Causal LM) vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: translate.translate_qwen2
- IN = OUT: Khai báo plugin Qwen2 theo chuẩn BaseOfflineTranslator (nhưng override load_weights do dùng CausalLM thay vì Seq2SeqLM).
=============================================================================
"""
import os
from typing import List
from app.core.shared_registry import TranslatorFactory
from app.core.translator.base_offline import BaseOfflineTranslator
from app.plugins.translator.qwen2.translate import translate_qwen2

def check_transformers() -> bool:
    try:
        import transformers  # type: ignore
        import torch  # type: ignore
        return True
    except ImportError:
        return False

@TranslatorFactory.register("qwen2")
class Qwen2Translator(BaseOfflineTranslator):
    MODELS = [
        {'key': 'qwen2', 'check_file': 'models/Offline Translator/Qwen2/model.safetensors', 'source': 'hf://Qwen/Qwen2-7B-Instruct'},
        {'key': 'qwen2_big', 'check_file': 'models/Offline Translator/Qwen2/model.safetensors', 'source': 'hf://Qwen/Qwen2-72B-Instruct'},
    ]

    def load_weights(self, model_path: str) -> None:
        if not model_path:
            return
            
        if not check_transformers():
            if self.log_callback:
                self.log_callback("ERROR", "Please install transformers library.")
            return
            
        try:
            if os.path.isfile(model_path):
                model_path = os.path.dirname(model_path)
                
            if self.log_callback:
                self.log_callback("INFO", f"Loading Qwen2 CausalLM from: {model_path} to {self.device}")
                
            from transformers import AutoTokenizer, AutoModelForCausalLM
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, use_fast=False)
            self.model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto")
            self.is_loaded = True
            
            if self.log_callback:
                self.log_callback("INFO", "Qwen2 Offline LLM loaded successfully.")
        except Exception as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Failed to load Qwen2: {e}")

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        return translate_qwen2(self, texts, src_lang, tgt_lang)
