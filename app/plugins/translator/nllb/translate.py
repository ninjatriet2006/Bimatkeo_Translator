"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.nllb.translate
- RESPONSIBILITY: Thực thi dịch thuật offline bằng mô hình NLLB.
- CALLED BY: app.plugins.translator.nllb.main_impl
- CALLS TO: None
- IN = OUT: Nhận danh sách text, mã ngôn ngữ; trả về danh sách text đã dịch.
=============================================================================
"""
from typing import List

def translate_nllb(translator_instance, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    if translator_instance.tokenizer is None or translator_instance.model is None:
        return []
        
    lang_map = {
        "ENG": "eng_Latn", "VIE": "vie_Latn", "JPN": "jpn_Jpan", 
        "KOR": "kor_Hang", "CHI": "zho_Hans"
    }
    src_token = lang_map.get(src_lang, "eng_Latn")
    tgt_token = lang_map.get(tgt_lang, "vie_Latn")
    
    translator_instance.tokenizer.src_lang = src_token
    encoded = translator_instance.tokenizer(texts, return_tensors="pt", padding=True).to(translator_instance.device)
    
    forced_bos_token_id = translator_instance.tokenizer.lang_code_to_id[tgt_token]
    
    generated_tokens = translator_instance.model.generate(
        **encoded,
        forced_bos_token_id=forced_bos_token_id,
        max_length=128
    )
    
    results = translator_instance.tokenizer.batch_decode(generated_tokens, skip_special_tokens=True)
    return results
