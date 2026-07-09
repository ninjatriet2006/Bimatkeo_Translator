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
def translate_openai(translator_instance, system_prompt: str, user_text: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {translator_instance.key}"
    }
    data = {
        "model": translator_instance.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_text}
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
