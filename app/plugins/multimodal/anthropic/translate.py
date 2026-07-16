"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.multimodal.anthropic.translate
- RESPONSIBILITY: Thực hiện gọi API tới các endpoint chuẩn Anthropic (Claude).
- CALLED BY: app.plugins.multimodal.anthropic.main_impl
- CALLS TO: Anthropic SDK
- IN = OUT: Xử lý prompt, base64 images -> Anthropic Messages -> string result.
=============================================================================
"""
import traceback
from anthropic import Anthropic, APIError

def translate_anthropic(provider, system_prompt: str, user_text: str, images: list[str] | None = None) -> str:
    if not provider.key:
        return "ERROR: Missing API Key for Anthropic"
        
    try:
        # Khởi tạo client. Nếu provider có custom endpoint, ta truyền vào base_url.
        client_kwargs = {
            "api_key": provider.key,
        }
        if provider.endpoint:
            client_kwargs["base_url"] = provider.endpoint
            
        client = Anthropic(**client_kwargs)
        
        # Xây dựng nội dung cho message
        content_blocks: list[dict] = []
        
        # Thêm text
        if user_text:
            content_blocks.append({
                "type": "text",
                "text": user_text
            })
            
        # Thêm ảnh (nếu có)
        if images:
            for b64_img in images:
                # Đảm bảo bỏ đi phần header "data:image/png;base64," nếu có
                clean_b64 = b64_img
                if "," in b64_img:
                    clean_b64 = b64_img.split(",", 1)[1]
                    
                content_blocks.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg", # Default fallback, Anthropic SDK is flexible or we might need strict detection
                        "data": clean_b64
                    }
                })
                
        # Gọi API
        model_name = provider.model if provider.model else "claude-3-5-sonnet-20241022"
        
        import typing
        messages_payload: typing.Any = [{"role": "user", "content": content_blocks}]
        
        if system_prompt:
            response = client.messages.create(
                model=model_name,
                max_tokens=4096,
                messages=messages_payload,
                system=system_prompt
            )
        else:
            response = client.messages.create(
                model=model_name,
                max_tokens=4096,
                messages=messages_payload
            )
        
        # Lấy nội dung text từ response
        if response.content:
            for block in response.content:
                if getattr(block, "type", "") == "text":
                    return getattr(block, "text", "")
            return getattr(response.content[0], "text", "")
        return ""
        
    except APIError as e:
        return f"ERROR: Anthropic API Error: {str(e)}"
    except Exception as e:
        return f"ERROR: Exception when calling Anthropic: {str(e)}\n{traceback.format_exc()}"
