import base64
import json
import urllib.request
import urllib.error
import numpy as np
import cv2 # type: ignore

from app.core.interfaces import BaseCloudOCR
from app.core.factories import CloudOCRFactory

@CloudOCRFactory.register("google_ocr")
class GoogleVisionImpl(BaseCloudOCR):
    def __init__(self):
        self.api_key = ""
        self.log_callback = None

    def load_model(self, api_key: str, **kwargs) -> None:
        self.api_key = api_key
        if "log_callback" in kwargs:
            self.log_callback = kwargs["log_callback"]
        if self.log_callback:
            self.log_callback("INFO", "Đã khởi tạo Google Vision OCR.")

    def recognize_full_page(self, image: np.ndarray, lang: str = "en") -> list[dict]:
        if not self.api_key:
            if self.log_callback:
                self.log_callback("ERROR", "API Key cho Google Vision không được cung cấp.")
            return []

        # Encode image to JPEG base64
        _, buffer = cv2.imencode('.jpg', image)
        img_b64 = base64.b64encode(buffer).decode('utf-8')

        url = f"https://vision.googleapis.com/v1/images:annotate?key={self.api_key}"

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
            
            if self.log_callback:
                self.log_callback("INFO", f"Google Vision phát hiện {len(valid_results)} khối chữ.")
            return valid_results

        except urllib.error.URLError as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Lỗi kết nối Google Vision API: {e}")
            return []
        except Exception as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Lỗi không xác định khi gọi Google Vision OCR: {e}")
            return []
