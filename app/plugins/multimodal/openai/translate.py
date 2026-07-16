"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.openai.translate
- RESPONSIBILITY: Thực thi gọi API dịch thuật (OpenAI format).
- CALLED BY: app.plugins.translator.openai.main_impl
- CALLS TO: app.plugins.translator.base_api.BaseAPITranslator._make_request (gián tiếp)
- IN = OUT: Nhận API config, prompt, text; trả về JSON string kết quả.
=============================================================================
"""
from typing import Any

def translate_openai(translator_instance, system_prompt: str, user_text: str, images: list[str] | None = None) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {translator_instance.key}"
    }
    
    user_content: list[dict[str, Any]] = [{"type": "text", "text": user_text}]
    if images:
        for img_b64 in images:
            user_content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{img_b64}"}
            })
            
    data = {
        "model": translator_instance.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content if images else user_text}
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }
    url = translator_instance.endpoint
    if not url.endswith("/chat/completions"):
        url = url.rstrip("/") + "/chat/completions"
        
    result = translator_instance._make_request(url, headers, data)
    try:
        return result["choices"][0]["message"]["content"].strip()
    except KeyError:
        return ""
