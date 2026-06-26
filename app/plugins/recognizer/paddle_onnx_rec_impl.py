import os
import cv2
import numpy as np
import urllib.request
import logging
import math
from app.core.interfaces import BaseTextRecognizer
from app.core.factories import RecognizerFactory

@RecognizerFactory.register("paddle_onnx_rec")
class PaddleONNXRecognizerImpl(BaseTextRecognizer):
    def __init__(self):
        self.session = None
        self.input_name = None
        self.character_dict = []
        self.dict_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
            ".config", "models", "paddle_en_dict.txt"
        )
        
    def _download_dict_if_needed(self, log_callback=None):
        if not os.path.exists(self.dict_path):
            if log_callback: log_callback("INFO", "Đang tải từ điển ký tự PaddleOCR (en_dict.txt)...")
            url = "https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/en_dict.txt"
            
            # Đọc từ file cấu hình nếu có
            try:
                import yaml
                registry_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                    ".config", "models", "model_registry.yaml"
                )
                with open(registry_path, "r", encoding="utf-8") as f:
                    registry_data = yaml.safe_load(f)
                    configured_url = registry_data.get("global_settings", {}).get("resources", {}).get("paddle_en_dict")
                    if configured_url:
                        url = configured_url
            except Exception as e:
                if log_callback: log_callback("WARNING", f"Không thể đọc cấu hình URL, sử dụng mặc định: {e}")
                
            try:
                os.makedirs(os.path.dirname(self.dict_path), exist_ok=True)
                urllib.request.urlretrieve(url, self.dict_path)
                if log_callback: log_callback("INFO", "Tải từ điển thành công.")
            except Exception as e:
                raise RuntimeError(f"Không thể tải từ điển ký tự từ Github: {e}")
                
    def _load_dict(self):
        self.character_dict = []
        with open(self.dict_path, "r", encoding="utf-8") as f:
            for line in f:
                char = line.strip('\n')
                if char != "":
                    self.character_dict.append(char)
        # PaddleOCR adds ' ' (space) and '<blank>' for CTC
        self.character_dict.append(' ')
        self.character_dict.insert(0, 'blank') # Index 0 is blank in PP-OCRv3/v4/v6

    def load_model(self, model_path: str | None = None, log_callback=None, **kwargs) -> None:
        try:
            import onnxruntime as ort  # type: ignore
        except ImportError:
            raise RuntimeError("Thư viện 'onnxruntime' hoặc 'onnxruntime-gpu' chưa được cài đặt.")
            
        if not model_path or not os.path.exists(model_path):
            raise FileNotFoundError(f"Không tìm thấy model ONNX tại: {model_path}")
            
        self._download_dict_if_needed(log_callback)
        self._load_dict()
        
        try:
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            if log_callback: log_callback("INFO", f"Đang khởi tạo PaddleONNX Rec với trọng số tại: {model_path}")
            self.session = ort.InferenceSession(model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            if log_callback: log_callback("INFO", "Mô hình Paddle ONNX Rec đã nạp thành công.")
        except Exception as e:
            raise RuntimeError(f"Lỗi khi khởi tạo Paddle ONNX Rec: {e}")

    def _resize_norm_img(self, img, max_wh_ratio):
        img_c = 3
        img_h = 48
        img_w = int(img_h * max_wh_ratio)
        img_w = max(round(img_w / 32) * 32, 32) # Ensure multiple of 32 for some architectures
        
        h, w = img.shape[:2]
        ratio = w / float(h)
        if math.ceil(img_h * ratio) > img_w:
            resized_w = img_w
        else:
            resized_w = math.ceil(img_h * ratio)
            
        resized_img = cv2.resize(img, (resized_w, img_h))
        resized_img = resized_img.astype('float32')
        resized_img = (resized_img / 255.0 - 0.5) / 0.5
        
        padding_im = np.zeros((img_h, img_w, img_c), dtype=np.float32)
        padding_im[:, :resized_w, :] = resized_img
        
        padding_im = padding_im.transpose((2, 0, 1))
        padding_im = np.expand_dims(padding_im, axis=0)
        return padding_im
        
    def _ctc_greedy_decoder(self, preds):
        # preds shape: (1, seq_len, num_classes)
        preds_idx = preds.argmax(axis=2)[0]
        preds_prob = preds.max(axis=2)[0]
        
        char_list = []
        conf_list = []
        for i in range(len(preds_idx)):
            idx = preds_idx[i]
            # Ignore blank (0) and duplicates
            if idx != 0 and not (i > 0 and preds_idx[i - 1] == idx):
                if idx < len(self.character_dict):
                    char_list.append(self.character_dict[idx])
                    conf_list.append(preds_prob[i])
                    
        text = ''.join(char_list)
        conf = float(np.mean(conf_list)) if conf_list else 0.0
        return text, conf

    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        if self.session is None: return "Mock OCR Text (Paddle ONNX Rec not loaded)", 0.0
        
        h, w = image_crop.shape[:2]
        max_wh_ratio = max(w * 1.0 / h, 1.0)
        tensor = self._resize_norm_img(image_crop, max_wh_ratio)
        
        outputs = self.session.run(None, {self.input_name: tensor})
        preds = outputs[0]
        
        text, conf = self._ctc_greedy_decoder(preds)
        return text, conf
