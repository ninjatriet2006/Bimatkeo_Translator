"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.m2m100.loader
- RESPONSIBILITY: Tải mô hình M2M100 (hỗ trợ CTranslate2 hoặc fallback Transformers).
- CALLED BY: app.plugins.translator.m2m100.main_impl
- CALLS TO: None
- IN = OUT: Cấu hình `model` và `tokenizer`/`sp_model` cho instance M2M100.
=============================================================================
"""
import os

def load_m2m100_model(translator_instance, model_path: str):
    if not model_path: return
    if os.path.isfile(model_path):
        model_path = os.path.dirname(model_path)
        
    if os.path.isfile(os.path.join(model_path, "model.bin")):
        import ctranslate2
        import sentencepiece as spm
        
        translator_instance.sp_model = spm.SentencePieceProcessor()
        translator_instance.sp_model.Load(os.path.join(model_path, "sentencepiece.model"))
        
        try:
            translator_instance.model = ctranslate2.Translator(model_path, device="cuda" if translator_instance.device == "cuda" else "cpu")
            if translator_instance.device == "cuda":
                # Perform a dummy translation to catch missing CUDA libraries (e.g. libcublas.so.12)
                translator_instance.model.translate_batch([["__en__", " a"]], target_prefix=[["__vi__"]])
        except RuntimeError as e:
            if translator_instance.log_callback:
                translator_instance.log_callback("WARNING", f"CUDA failed for CTranslate2 ({e}), falling back to CPU.")
            translator_instance.model = ctranslate2.Translator(model_path, device="cpu")
        
        translator_instance.is_ctranslate2 = True
        translator_instance.is_loaded = True
        if translator_instance.log_callback:
            translator_instance.log_callback("INFO", f"Loaded M2M100 using CTranslate2 from {model_path}.")
    else:
        translator_instance.is_ctranslate2 = False
        # Gọi load_weights của BaseOfflineTranslator (qua super() từ main_impl)
        return "USE_SUPER"
