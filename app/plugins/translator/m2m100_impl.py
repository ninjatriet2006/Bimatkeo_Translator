from typing import List
import os
from app.core.shared_registry import TranslatorFactory
from .base_offline import BaseOfflineTranslator

@TranslatorFactory.register("m2m100")
class M2M100Translator(BaseOfflineTranslator):
    MODELS = [
        {'key': 'm2m100', 'check_file': 'models/Offline Translator/M2M100/sentencepiece.model'},
    ]

    
    def load_weights(self, model_path: str) -> None:
        if not model_path: return
        if os.path.isfile(model_path):
            model_path = os.path.dirname(model_path)
            
        if os.path.isfile(os.path.join(model_path, "model.bin")):
            import ctranslate2
            import sentencepiece as spm
            
            self.sp_model = spm.SentencePieceProcessor()
            self.sp_model.Load(os.path.join(model_path, "sentencepiece.model"))
            
            try:
                self.model = ctranslate2.Translator(model_path, device="cuda" if self.device == "cuda" else "cpu")
                if self.device == "cuda":
                    # Perform a dummy translation to catch missing CUDA libraries (e.g. libcublas.so.12)
                    self.model.translate_batch([["__en__", " a"]], target_prefix=[["__vi__"]])
            except RuntimeError as e:
                if self.log_callback:
                    self.log_callback("WARNING", f"CUDA failed for CTranslate2 ({e}), falling back to CPU.")
                self.model = ctranslate2.Translator(model_path, device="cpu")
            
            self.is_ctranslate2 = True
            self.is_loaded = True
            if self.log_callback:
                self.log_callback("INFO", f"Loaded M2M100 using CTranslate2 from {model_path}.")
        else:
            self.is_ctranslate2 = False
            super().load_weights(model_path)

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        if not self.is_loaded or self.model is None:
            return []
        
        lang_map = {
            "ENG": "en", "VIE": "vi", "JPN": "ja", "KOR": "ko", "CHI": "zh"
        }
        
        if getattr(self, "is_ctranslate2", False):
            results = []
            
            # Check if auto language detection is requested
            is_auto = (src_lang.lower() == "auto")
            
            for text in texts:
                # Detect language dynamically if auto
                current_src_lang = src_lang
                if is_auto:
                    try:
                        import re
                        from langdetect import detect
                        detected = detect(text)
                        
                        if detected == 'ko' and not bool(re.search(r'[\uac00-\ud7af]', text)):
                            # langdetect falsely classified as Korean (no Hangul present)
                            if bool(re.search(r'[\u4e00-\u9fff]', text)):
                                current_src_lang = 'CHI'
                            elif bool(re.search(r'[\u3040-\u30ff]', text)):
                                current_src_lang = 'JPN'
                            else:
                                current_src_lang = 'ENG'
                        elif detected.startswith('zh'):
                            current_src_lang = 'CHI'
                        elif detected == 'ja':
                            current_src_lang = 'JPN'
                        elif detected == 'ko':
                            current_src_lang = 'KOR'
                        else:
                            current_src_lang = 'ENG'
                    except:
                        current_src_lang = 'ENG' # fallback
                        
                src_token = f"__{lang_map.get(current_src_lang, 'en')}__"
                tgt_token = f"__{lang_map.get(tgt_lang, 'vi')}__"
                
                source_tokens = [src_token] + self.sp_model.Encode(text, out_type=str)
                target_prefix = [tgt_token]
                res = self.model.translate_batch([source_tokens], target_prefix=[target_prefix])
                output_tokens = res[0].hypotheses[0][1:]
                results.append(self.sp_model.Decode(output_tokens))
            return results
        else:
            if self.tokenizer is None:
                return []
            src_token = lang_map.get(src_lang, "en")
            tgt_token = lang_map.get(tgt_lang, "vi")
            
            self.tokenizer.src_lang = src_token
            encoded = self.tokenizer(texts, return_tensors="pt", padding=True).to(self.device)
            forced_bos_token_id = self.tokenizer.get_lang_id(tgt_token)
            
            generated_tokens = self.model.generate(
                **encoded,
                forced_bos_token_id=forced_bos_token_id,
                max_length=128
            )
            return self.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
