"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.translator.felo.translate
- RESPONSIBILITY: Thực thi gọi API dịch thuật (Felo.ai format).
- CALLED BY: app.plugins.translator.felo.main_impl
- CALLS TO: app.core.translator.base_api.BaseAPITranslator._make_request (gián tiếp)
- IN = OUT: Nhận API config, prompt, text; trả về JSON string kết quả.
=============================================================================
"""
def translate_felo(translator_instance, system_prompt: str, user_text: str) -> str:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {translator_instance.key}"
    }
    
    # Felo API uses a single "query" field for web search augmented chat
    query = f"{system_prompt}\n\nPlease strictly follow the instruction and translate the following lines. YOU MUST RETURN ONLY A VALID JSON OBJECT WITH THE 'content' KEY:\n{user_text}"
    data = {
        "model": translator_instance.model,
        "query": query
    }
    
    url = translator_instance.endpoint
    if not url.endswith("/chat"):
        url = url.rstrip("/") + "/chat"
        
    result = translator_instance._make_request(url, headers, data)
    try:
        return result.get("data", {}).get("answer", str(result)).strip()
    except Exception as e:
        return f'{{"content": "ERROR: Felo API returned unexpected format: {str(e)} - {result}"}}'
