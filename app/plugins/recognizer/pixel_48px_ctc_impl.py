import os
import cv2
import numpy as np
import math
from app.core.interfaces import BaseTextRecognizer
from app.core.factories import RecognizerFactory
from app.core.downloader import ModelDownloader

@RecognizerFactory.register("48px_ctc")
class Pixel48pxCTCRecognizerImpl(BaseTextRecognizer):
    DISPLAY_NAME = "48px CTC (ONNX)"
    def __init__(self):
        self.session = None
        self.input_name = None
        self.character_dict = []
        
    def _load_dict(self, dict_path: str):
        self.character_dict = []
        with open(dict_path, "r", encoding="utf-8") as f:
            for line in f:
                char = line.strip('\n')
                self.character_dict.append(char)
                
    def load_model(self, model_path: str | None = None, log_callback=None) -> None:
        try:
            import onnxruntime as ort  # type: ignore
        except ImportError:
            raise RuntimeError("Thư viện 'onnxruntime' hoặc 'onnxruntime-gpu' chưa được cài đặt.")
            
        if not model_path:
            raise ValueError("model_path is required")
            
        target_dir = os.path.dirname(model_path)
        expected_filename = os.path.basename(model_path)
        dict_filename = "alphabet-all-v5.txt"
        
        if not os.path.exists(model_path) or not os.path.exists(os.path.join(target_dir, dict_filename)):
            url = ModelDownloader.get_source_url_from_registry("offline_ocr", "48px_ctc")
            if url:
                if log_callback: log_callback("INFO", f"Đang tiến hành tải tự động 48px CTC ONNX từ {url}...")
                success = ModelDownloader.download_and_extract(
                    url=url, target_dir=target_dir, expected_files=[expected_filename, dict_filename],
                    log_callback=log_callback, extract=False
                )
                if not success:
                    raise RuntimeError(f"Không thể khởi tạo mô hình 48px CTC tại {target_dir}")
            else:
                raise RuntimeError(f"Chưa có nguồn tải cho mô hình 48px CTC. Vui lòng tự nạp mô hình vào {target_dir}")
        
        dict_path = os.path.join(target_dir, dict_filename)
        self._load_dict(dict_path)
        
        try:
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            if log_callback: log_callback("INFO", f"Đang khởi tạo 48px CTC ONNX Rec với trọng số tại: {model_path}")
            self.session = ort.InferenceSession(model_path, providers=providers)
            self.input_name = self.session.get_inputs()[0].name
            if log_callback: log_callback("INFO", "Mô hình 48px CTC ONNX Rec đã nạp thành công.")
        except Exception as e:
            raise RuntimeError(f"Lỗi khi khởi tạo 48px CTC ONNX Rec: {e}")

    def _resize_norm_img(self, img, img_h=48):
        h, w = img.shape[:2]
        ratio = w / float(h)
        img_w = math.ceil(img_h * ratio)
        
        resized_img = cv2.resize(img, (img_w, img_h))
        resized_img = resized_img.astype('float32')
        resized_img = (resized_img - 127.5) / 127.5
        
        # BGR -> CHW
        resized_img = resized_img.transpose((2, 0, 1))
        # Add batch dimension
        tensor = np.expand_dims(resized_img, axis=0)
        return tensor
        
    def _ctc_greedy_decoder(self, preds):
        # preds shape: (batch=1, time, vocab_size)
        preds_idx = preds.argmax(axis=2)[0]
        
        char_list = []
        for i in range(len(preds_idx)):
            idx = preds_idx[i]
            # 0 is CTC blank token
            if idx != 0 and not (i > 0 and preds_idx[i - 1] == idx):
                if idx < len(self.character_dict):
                    char = self.character_dict[idx]
                    if char == "<SP>":
                        char = " "
                    char_list.append(char)
                    
        return ''.join(char_list)

    def recognize(self, image_crop: np.ndarray) -> str:
        if self.session is None: return "Mock OCR Text (48px CTC ONNX Rec not loaded)"
        
        tensor = self._resize_norm_img(image_crop, img_h=48)
        
        outputs = self.session.run(None, {self.input_name: tensor})
        # outputs[0] is char_logits, outputs[1] is color_values
        char_logits = outputs[0]
        
        text = self._ctc_greedy_decoder(char_logits)
        return text
