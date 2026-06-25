import base64
import json
import urllib.request
import urllib.error
import numpy as np
import cv2 # type: ignore
from typing import List, Dict

from app.core.interfaces import BaseCloudOCR
from app.core.factories import CloudOCRFactory

@CloudOCRFactory.register("gemini_ocr")
class GeminiVisionImpl(BaseCloudOCR):
    DISPLAY_NAME = "Gemini Vision OCR"
    def __init__(self):
        self.api_key = ""
        self.log_callback = None

    def load_model(self, api_key: str, endpoint: str | None = None, model_name: str | None = None, **kwargs) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.model_name = model_name or "gemini-1.5-flash"
        if "log_callback" in kwargs:
            self.log_callback = kwargs["log_callback"]
        if self.log_callback:
            self.log_callback("INFO", "Đã khởi tạo Gemini Vision OCR.")

    def recognize_full_page(self, image: np.ndarray, lang: str = "en") -> list[dict]:
        if not self.api_key:
            if self.log_callback:
                self.log_callback("ERROR", "API Key cho Gemini Vision không được cung cấp.")
            return []

        # Encode image to JPEG base64
        _, buffer = cv2.imencode('.jpg', image)
        img_b64 = base64.b64encode(buffer).decode('utf-8')

        if not self.endpoint:
            import os
            try:
                import yaml
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
                reg_path = os.path.join(project_root, ".config", "models", "model_registry.yaml")
                with open(reg_path, "r", encoding="utf-8") as f:
                    reg = yaml.safe_load(f)
                for item in reg.get("fields", {}).get("api_ocr", []):
                    if item.get("key") == "gemini_ocr":
                        self.endpoint = item.get("default_endpoint")
                        break
            except Exception:
                pass

        if self.endpoint:
            base_url = self.endpoint.format(model=self.model_name) if "{model}" in self.endpoint else self.endpoint
            url = f"{base_url}?key={self.api_key}" if "?" not in base_url else f"{base_url}&key={self.api_key}"
        else:
            raise ValueError("Endpoint is missing and could not be loaded from registry.")

        system_prompt = (
            "You are an OCR assistant. Detect all text in the provided image. "
            "Return ONLY a JSON array of objects. Each object must have the following structure: "
            "{\"box\": [x_min, y_min, x_max, y_max], \"text\": \"the detected string\", \"score\": 1.0}. "
            "Do not include any other text or markdown formatting. The coordinates must be absolute pixel values based on the image size."
        )

        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [{
                "parts": [
                    {"text": "Detect text in this image and return JSON."},
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": img_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "response_mime_type": "application/json"
            }
        }

        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as response:
                result = json.loads(response.read().decode('utf-8'))
                
            text_response = result["candidates"][0]["content"]["parts"][0]["text"].strip()
            
            # Clean markdown if accidentally included
            if text_response.startswith('```json'):
                text_response = text_response[7:]
            if text_response.startswith('```'):
                text_response = text_response[3:]
            if text_response.endswith('```'):
                text_response = text_response[:-3]
                
            parsed = json.loads(text_response)
            
            # Ensure the output format is correct
            valid_results = []
            if isinstance(parsed, list):
                for item in parsed:
                    if "box" in item and "text" in item:
                        # Some LLMs might return string coordinates or strings for scores
                        box = [int(v) for v in item["box"]]
                        text = str(item["text"])
                        score = float(item.get("score", 1.0))
                        valid_results.append({"box": box, "text": text, "score": score})
            
            if self.log_callback:
                self.log_callback("INFO", f"Gemini Vision phát hiện {len(valid_results)} khối chữ.")
            return valid_results

        except urllib.error.URLError as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Lỗi kết nối Gemini API: {e}")
            return []
        except json.JSONDecodeError as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Không thể parse JSON từ Gemini: {e}")
            return []
        except Exception as e:
            if self.log_callback:
                self.log_callback("ERROR", f"Lỗi không xác định khi gọi Gemini OCR: {e}")
            return []
