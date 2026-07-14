"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.qwen2.translate
- RESPONSIBILITY: Thực thi dịch thuật offline bằng mô hình Qwen2.
- CALLED BY: app.plugins.translator.qwen2.main_impl
- CALLS TO: None
- IN = OUT: Nhận danh sách text, mã ngôn ngữ; trả về danh sách text đã dịch.
=============================================================================
"""
from typing import List

def translate_qwen2(translator_instance, texts: List[str], src_lang: str, tgt_lang: str) -> List[str]:
    if translator_instance.tokenizer is None or translator_instance.model is None:
        return []
    
    lang_map = {
        "ENG": "English", "VIE": "Vietnamese", "JPN": "Japanese", 
        "KOR": "Korean", "CHI": "Chinese"
    }
    src = lang_map.get(src_lang, src_lang)
    tgt = lang_map.get(tgt_lang, tgt_lang)
    
    results = []
    
    for text in texts:
        messages = [
            {"role": "system", "content": f"You are a professional translator. Translate the following text from {src} to {tgt}. Only output the translated text, nothing else."},
            {"role": "user", "content": text}
        ]
        
        try:
            text_prompt = translator_instance.tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=True
            )
            
            model_inputs = translator_instance.tokenizer([text_prompt], return_tensors="pt").to(translator_instance.model.device)
            
            generated_ids = translator_instance.model.generate(
                **model_inputs,
                max_new_tokens=512
            )
            
            # Extract only the newly generated text (ignoring the prompt)
            generated_ids = [
                output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
            ]
            
            response = translator_instance.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
            results.append(response.strip())
        except Exception as e:
            if translator_instance.log_callback:
                translator_instance.log_callback("ERROR", f"Qwen2 generation failed: {e}")
            results.append("")
            
    return results
