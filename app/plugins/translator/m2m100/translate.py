"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.m2m100.translate
- RESPONSIBILITY: Thực thi dịch thuật offline bằng mô hình M2M100.
- CALLED BY: app.plugins.translator.m2m100.main_impl
- CALLS TO: None
- IN = OUT: Nhận danh sách text, mã ngôn ngữ; trả về danh sách text đã dịch.
=============================================================================
"""
from typing import List

def translate_m2m100(translator_instance, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    if not translator_instance.is_loaded or translator_instance.model is None:
        return []
    
    lang_map = {
        "ENG": "en", "VIE": "vi", "JPN": "ja", "KOR": "ko", "CHI": "zh"
    }
    
    if getattr(translator_instance, "is_ctranslate2", False):
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
            
            source_tokens = [src_token] + translator_instance.sp_model.Encode(text, out_type=str)
            target_prefix = [tgt_token]
            res = translator_instance.model.translate_batch([source_tokens], target_prefix=[target_prefix])
            output_tokens = res[0].hypotheses[0][1:]
            results.append(translator_instance.sp_model.Decode(output_tokens))
        return results
    else:
        if translator_instance.tokenizer is None:
            return []
        src_token = lang_map.get(src_lang, "en")
        tgt_token = lang_map.get(tgt_lang, "vi")
        
        translator_instance.tokenizer.src_lang = src_token
        encoded = translator_instance.tokenizer(texts, return_tensors="pt", padding=True).to(translator_instance.device)
        forced_bos_token_id = translator_instance.tokenizer.get_lang_id(tgt_token)
        
        generated_tokens = translator_instance.model.generate(
            **encoded,
            forced_bos_token_id=forced_bos_token_id,
            max_length=128
        )
        return translator_instance.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
