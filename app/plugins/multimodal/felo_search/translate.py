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
    query += f"Please strictly follow the instruction and translate the following lines. YOU MUST RETURN ONLY A VALID JSON OBJECT WITH THE 'content' KEY:\nUser: {user_text}"
    
    headers = {
        "Authorization": f"Bearer {provider.key}",
        "Content-Type": "application/json"
    }
    
    model_name = getattr(provider, 'model', None)
    if not model_name:
        import random
        # 1. Thực hiện HTTP request để lấy danh sách model từ API
        try:
            # Thử suy luận endpoint chứa danh sách model từ endpoint chat
            base_url = endpoint.split('/v2/chat')[0].split('/v1/chat')[0]
            models_endpoint = f"{base_url}/v1/models"
            
            r_models = requests.get(models_endpoint, headers={"Authorization": headers["Authorization"]}, timeout=10)
            if r_models.status_code == 200:
                data_models = r_models.json().get("data", [])
                model_ids = [m.get("id") for m in data_models if "id" in m]
                if model_ids:
                    model_name = random.choice(model_ids)
        except Exception:
            pass
            
        # 2. Nếu API không hỗ trợ endpoint /models (bị lỗi 500/404), lấy ngẫu nhiên từ danh sách khai báo của Provider
        if not model_name:
            if hasattr(provider, 'MODELS') and provider.MODELS:
                static_models = provider.MODELS[0].get('static_models', [])
                if static_models:
                    model_name = random.choice(static_models)
            
            # 3. Fallback an toàn cuối cùng
            if not model_name:
                model_name = 'felo-search'
        
    payload = {
        "model": model_name,
        "query": query
    }
    
    try:
        timeout = getattr(provider, 'timeout', 30)
        response = requests.post(endpoint, headers=headers, json=payload, timeout=timeout)
        
        if response.status_code != 200:
            raise RuntimeError(f"Felo API HTTP Error {response.status_code}: {response.text}")
            
        data = response.json()
        if data.get("code") == "OK" or data.get("status") == "ok" or "answer" in data.get("data", {}):
            answer = data.get("data", {}).get("answer", "")
            
            # Xoá phần append resources vì Translator yêu cầu output trả về chuỗi JSON hợp lệ
                    
            return answer
        else:
            raise RuntimeError(f"Felo API returned error: code={data.get('code')} msg={data.get('message', data.get('msg'))} data={data}")
            
    except Exception as e:
        raise RuntimeError(f"Exception when calling Felo Search API: {str(e)}\n{traceback.format_exc()}")
