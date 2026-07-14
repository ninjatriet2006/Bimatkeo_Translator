"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.jparacrawl.translate
- RESPONSIBILITY: Thực thi dịch thuật offline bằng mô hình JParaCrawl.
- CALLED BY: app.plugins.translator.jparacrawl.main_impl
- CALLS TO: None
- IN = OUT: Nhận danh sách text, mã ngôn ngữ; trả về danh sách text đã dịch.
=============================================================================
"""
from typing import List

def translate_jparacrawl(translator_instance, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    if translator_instance.model is None:
        return []
    
    # JParaCrawl typically translates JA -> EN and EN -> JA
    # For fairseq, usually you just call translate()
    try:
        results = []
        for text in texts:
            results.append(translator_instance.model.translate(text))
        return results
    except Exception as e:
        if translator_instance.log_callback:
            translator_instance.log_callback("ERROR", f"JParaCrawl translation failed: {e}")
        return []
