"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.multimodal.felo_search.translate
- RESPONSIBILITY: Thực hiện gọi API tới Felo /v2/chat (Search-grounded Chat).
- CALLED BY: app.plugins.multimodal.felo_search.main_impl
- CALLS TO: https://openapi.felo.ai/v2/chat
- IN = OUT: Nhận system_prompt, user_text -> ghép thành query -> trả về text.
=============================================================================
"""
import requests
import json
import traceback

def translate_felo_search(provider, system_prompt: str, user_text: str, images: list[str] | None = None) -> str:
    if not provider.key:
        return "ERROR: Missing API Key for Felo Search"
        
    endpoint = provider.endpoint or "https://openapi.felo.ai/v2/chat"
    # Dảm bảo endpoint đúng (phải kết thúc bằng /v2/chat)
    if not endpoint.endswith("/v2/chat"):
        if endpoint.endswith("/v2"):
            endpoint += "/chat"
        elif endpoint.endswith("/"):
            endpoint += "v2/chat"
        else:
            endpoint += "/v2/chat"
            
    # Gộp prompt do API này chỉ nhận 1 trường query
    query = ""
    if system_prompt:
        query += f"System: {system_prompt}\n\n"
    query += f"User: {user_text}"
    
    headers = {
        "Authorization": f"Bearer {provider.key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "query": query
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=provider.timeout)
        response.raise_for_status()
        
        data = response.json()
        if data.get("status") == "ok":
            answer = data.get("data", {}).get("answer", "")
            
            # Tuỳ chọn: Gắn thêm nguồn trích dẫn nếu có
            resources = data.get("data", {}).get("resources", [])
            if resources:
                answer += "\n\n--- Sources ---\n"
                for res in resources:
                    answer += f"- {res.get('title')}: {res.get('link')}\n"
                    
            return answer
        else:
            return f"ERROR: Felo API returned error: {data.get('code')} - {data.get('message')}"
            
    except Exception as e:
        return f"ERROR: Exception when calling Felo Search API: {str(e)}\n{traceback.format_exc()}"
