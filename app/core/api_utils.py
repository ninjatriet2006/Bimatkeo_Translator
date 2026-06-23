import urllib.request
import urllib.error
import ssl
import json
import os

def is_blacklisted(model_name: str) -> bool:
    name_lower = model_name.lower()
    blacklist_keywords = [
        "embedding", "tts", "whisper", "dall-e", "moderation", 
        "classifier", "aqa", "sib", "babbage", "davinci", "ada"
    ]
    for kw in blacklist_keywords:
        if kw in name_lower:
            return True
    return False

def priority_sort_key(m_name: str):
    m_lower = m_name.lower()
    if any(x in m_lower for x in ["gpt-4o", "o1", "o3", "deepseek-chat", "mixtral", "llama3"]): 
        return (-10, m_lower)
    if any(x in m_lower for x in ["gpt-4", "deepseek", "llama"]): 
        return (-5, m_lower)
    if "gpt-3.5" in m_lower: 
        return (0, m_lower)
    return (5, m_lower)

def infer_ai_provider(endpoint: str) -> str:
    """Infers the AI provider based on the endpoint string."""
    ep_lower = endpoint.lower() if endpoint else ""
    if not ep_lower or "generativelanguage" in ep_lower:
        return 'gemini'
    
    match ep_lower:
        case _ if "api-free.deepl" in ep_lower or "api.deepl" in ep_lower:
            return 'deepl'
        case _ if "fanyi-api.baidu" in ep_lower:
            return 'baidu'
        case _ if "openapi.youdao" in ep_lower:
            return 'youdao'
        case _ if "api.interpreter.caiyunai" in ep_lower:
            return 'caiyun'
        case _ if "openapi.naver" in ep_lower:
            return 'papago'
        case _ if "sakura" in ep_lower:
            return 'sakura'
        case _:
            return 'openai'

def fetch_remote_ai_models(endpoint: str, key: str, ai_provider: str) -> list[str]:
    """Fetches AI models from remote provider (Gemini or OpenAI compatible)."""
    ctx = ssl.create_default_context()
    
    # SECURITY SKILL: Only disable SSL for local models or explicitly allowed environments
    ep_lower = endpoint.lower() if endpoint else ""
    if os.environ.get("ALLOW_INSECURE_SSL") == "1" or "localhost" in ep_lower or "127.0.0.1" in ep_lower or "ollama" in ep_lower or "11434" in ep_lower:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    if ai_provider == 'gemini':
        base_url = endpoint.rstrip('/') if endpoint else "https://generativelanguage.googleapis.com/v1beta"
        url = f"{base_url}/models?key={key}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                gemini_models = []
                for m in res_data.get('models', []):
                    m_name = m.get('name', '').replace('models/', '')
                    if not is_blacklisted(m_name):
                        gemini_models.append((m_name, m.get('inputTokenLimit', 0)))
                
                gemini_models.sort(key=lambda x: (-x[1], x[0]))
                return [x[0] for x in gemini_models]
        except urllib.error.URLError as e:
            raise ValueError(f"Failed to fetch Gemini models: {e}") from e
    else:
        base_url = endpoint.rstrip('/')
        url = f"{base_url}/models"
        
        headers = {
            'User-Agent': 'Mozilla/5.0',
            'Content-Type': 'application/json'
        }
        if key:
            headers['Authorization'] = f"Bearer {key}"
        
        req = urllib.request.Request(url, headers=headers)
        raw_models = []
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if 'data' in res_data and isinstance(res_data['data'], list):
                    raw_models = [item['id'] for item in res_data['data'] if 'id' in item]
                elif 'models' in res_data and isinstance(res_data['models'], list):
                    raw_models = [item['name'] for item in res_data['models'] if 'name' in item]
        except urllib.error.HTTPError as e:
            if '11434' in base_url or 'ollama' in base_url.lower():
                ollama_url = base_url.replace('/v1', '') + '/api/tags'
                req = urllib.request.Request(ollama_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, context=ctx, timeout=10) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    raw_models = [item['name'] for item in res_data.get('models', []) if 'name' in item]
            else:
                raise ValueError(f"HTTPError fetching OpenAI models: {e.code} {e.reason}") from e
        except urllib.error.URLError as e:
            raise ValueError(f"URLError fetching models: {e.reason}") from e

        filtered_models = [m for m in raw_models if not is_blacklisted(m)]
        models = sorted(list(set(filtered_models)), key=priority_sort_key)
        
        if not models:
            raise ValueError("No suitable model IDs found in response.")
        return models
