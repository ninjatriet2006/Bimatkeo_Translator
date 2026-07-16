"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.gemini.translate
- RESPONSIBILITY: Thực thi gọi API dịch thuật (Google Gemini format).
- CALLED BY: app.plugins.translator.gemini.main_impl
- CALLS TO: app.core.translator.base_api.BaseAPITranslator._make_request (gián tiếp)
- IN = OUT: Nhận API config, prompt, text; trả về JSON string kết quả.
=============================================================================
"""
def translate_gemini(translator_instance, system_prompt: str, user_text: str, images: list[str] | None = None) -> str:
    headers = {
        "Content-Type": "application/json"
    }
    
    parts = [{"text": user_text}]
    if images:
        for img_b64 in images:
            parts.append({
                "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": img_b64
                }
            })
            
    data = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [{
            "parts": parts
        }],
        "generationConfig": {
            "temperature": 0.3
        }
    }
    endpoint = translator_instance.endpoint.rstrip('/') if translator_instance.endpoint else "https://generativelanguage.googleapis.com"
    url = f"{endpoint}/v1beta/models/{translator_instance.model}:generateContent?key={translator_instance.key}"
        
    result = translator_instance._make_request(url, headers, data)
    try:
        return result["candidates"][0]["content"]["parts"][0]["text"].strip()
    except KeyError:
        return ""
