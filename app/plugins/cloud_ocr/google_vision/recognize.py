"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.cloud_ocr.google_vision.recognize
- RESPONSIBILITY: Thực thi nhận diện chữ (Cloud OCR) qua Google Vision API.
- CALLED BY: app.plugins.cloud_ocr.google_vision.main_impl
- CALLS TO: urllib.request
- IN = OUT: Nhận ảnh (OpenCV), API key; trả về danh sách các dict chứa box, text, score.
=============================================================================
"""
import base64
import json
import urllib.request
import urllib.error
import numpy as np
import cv2 # type: ignore

def recognize_google_vision(ocr_instance, image: np.ndarray, lang: str = "en") -> list[dict]:
    if not ocr_instance.api_key:
        if ocr_instance.log_callback:
            ocr_instance.log_callback("ERROR", "API Key cho Google Vision không được cung cấp.")
        return []

    # Encode image to JPEG base64
    _, buffer = cv2.imencode('.jpg', image)
    img_b64 = base64.b64encode(buffer).decode('utf-8')

    if not ocr_instance.endpoint and hasattr(ocr_instance, 'MODELS') and ocr_instance.MODELS:
        ocr_instance.endpoint = ocr_instance.MODELS[0].get("default_endpoint")

    if ocr_instance.endpoint:
        url = f"{ocr_instance.endpoint}?key={ocr_instance.api_key}" if "?" not in ocr_instance.endpoint else f"{ocr_instance.endpoint}&key={ocr_instance.api_key}"
    else:
        raise ValueError("Endpoint is missing and could not be loaded from registry.")

    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "requests": [
            {
                "image": {
                    "content": img_b64
                },
                "features": [
                    {
                        "type": "DOCUMENT_TEXT_DETECTION"
                    }
                ]
            }
        ]
    }

    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))
            
        responses = result.get("responses", [])
        if not responses or not responses[0]:
            return []
            
        valid_results = []
        pages = responses[0].get("fullTextAnnotation", {}).get("pages", [])
        for page in pages:
            for block in page.get("blocks", []):
                vertices = block.get("boundingBox", {}).get("vertices", [])
                if not vertices: 
                    continue
                    
                xs = [v.get("x", 0) for v in vertices]
                ys = [v.get("y", 0) for v in vertices]
                box = [min(xs), min(ys), max(xs), max(ys)]
                
                text_parts = []
                for paragraph in block.get("paragraphs", []):
                    for word in paragraph.get("words", []):
                        word_text = "".join([sym.get("text", "") for sym in word.get("symbols", [])])
                        text_parts.append(word_text)
                
                # Ghép các từ thành câu
                text = " ".join(text_parts).strip()
                if text:
                    valid_results.append({"box": box, "text": text, "score": 1.0})
        
        if ocr_instance.log_callback:
            ocr_instance.log_callback("INFO", f"Google Vision phát hiện {len(valid_results)} khối chữ.")
        return valid_results

    except urllib.error.URLError as e:
        if ocr_instance.log_callback:
            ocr_instance.log_callback("ERROR", f"Lỗi kết nối Google Vision API: {e}")
        return []
    except Exception as e:
        if ocr_instance.log_callback:
            ocr_instance.log_callback("ERROR", f"Lỗi không xác định khi gọi Google Vision OCR: {e}")
        return []
