"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.jparacrawl.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký JParaCrawl Translator vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: translate.translate_jparacrawl
- IN = OUT: Khai báo plugin JParaCrawl theo chuẩn BaseOfflineTranslator.
=============================================================================
"""
import os
from typing import List
from app.core.shared_registry import TranslatorFactory
from app.core.translator.base_offline import BaseOfflineTranslator
from app.plugins.translator.jparacrawl.translate import translate_jparacrawl

@TranslatorFactory.register("jparacrawl")
class JParaCrawlTranslator(BaseOfflineTranslator):
    MODELS = [
        {'key': 'jparacrawl', 'check_file': 'models/Offline Translator/JParaCrawl/spm.ja.nopretok.model'},
        {'key': 'jparacrawl_big', 'check_file': 'models/Offline Translator/JParaCrawl/spm.ja.nopretok.model'},
    ]

    def load_weights(self, model_path: str) -> None:
        if not model_path:
            return
        try:
            import fairseq # type: ignore
            model_dir = os.path.dirname(model_path)
            self.model = fairseq.models.transformer.TransformerModel.from_pretrained(
                model_dir,
                checkpoint_file='base.pt',
                bpe='sentencepiece',
                sentencepiece_model=model_path
            )
            self.model.to(self.device)
            self.is_loaded = True
            if self.log_callback:
                self.log_callback("INFO", "JParaCrawl offline translator loaded successfully.")
        except ImportError:
            if self.log_callback:
                self.log_callback("ERROR", "Please install fairseq to use JParaCrawl.")
        except Exception as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Failed to load JParaCrawl: {e}")

    def _perform_translation(self, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
        return translate_jparacrawl(self, texts, src_lang, tgt_lang)
