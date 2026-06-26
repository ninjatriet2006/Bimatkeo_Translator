import os
import cv2
import numpy as np
from typing import List

from app.core.interfaces import BaseInpainter
from app.core.factories import InpainterFactory
from app.core.downloader import ModelDownloader

try:
    import onnxruntime as ort
except ImportError:
    ort = None

def ceil_modulo(x, mod):
    if x % mod == 0:
        return x
    return (x // mod + 1) * mod

def pad_img_to_modulo(img, mod):
    h, w = img.shape[:2]
    out_h = ceil_modulo(h, mod)
    out_w = ceil_modulo(w, mod)
    if out_h == h and out_w == w:
        return img
    pad_h = out_h - h
    pad_w = out_w - w
    if img.ndim == 3:
        padded = np.pad(img, ((0, pad_h), (0, pad_w), (0, 0)), mode='symmetric')
    else:
        padded = np.pad(img, ((0, pad_h), (0, pad_w)), mode='symmetric')
    return padded

@InpainterFactory.register("lama")
class LamaInpainter_Impl(BaseInpainter):
    DISPLAY_NAME = {
        "lama": "saic-mdal/lama (ONNX)"
    }
    def __init__(self):
        self.model_path = None
        self.is_loaded = False
        self.session = None
        self.input_name_img = None
        self.input_name_mask = None
        self.config = {}

    def load_model(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        self.config = kwargs
        
        # Identify which key it is based on the path
        key = "lama"
            
        if not os.path.exists(self.model_path):
            source_url = ModelDownloader.get_source_url_from_registry("inpainter", key)
            if source_url:
                target_dir = os.path.dirname(self.model_path)
                expected_files = [os.path.basename(self.model_path)]
                print(f"[LaMa] Downloading weights from {source_url}...")
                success = ModelDownloader.download_and_extract(
                    source_url, target_dir, expected_files, extract=True
                )
                if not success:
                    print(f"[LaMa] Failed to download weights for {key}.")
                    return
            else:
                print(f"[LaMa] No source URL found in registry for {key}.")
                return
        
        if ort is None:
            print("[LaMa] onnxruntime is not installed. Inference will fallback to OpenCV.")
            return

        try:
            providers = ['CUDAExecutionProvider', 'CPUExecutionProvider']
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            
            inputs = self.session.get_inputs()
            # LaMa usually takes 'image' and 'mask'
            for inp in inputs:
                if 'image' in inp.name.lower():
                    self.input_name_img = inp.name
                elif 'mask' in inp.name.lower():
                    self.input_name_mask = inp.name
                    
            if not self.input_name_img:
                self.input_name_img = inputs[0].name
            if not self.input_name_mask:
                self.input_name_mask = inputs[1].name

            print(f"[LaMa] ONNX Model loaded successfully: {self.model_path}")
            self.is_loaded = True
        except Exception as e:
            print(f"[LaMa] Failed to load ONNX model: {e}")

    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        if not bboxes:
            return image

        # Create mask from bboxes
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        for box in bboxes:
            x_min, y_min, x_max, y_max = box
            pad = 5
            x1 = max(0, x_min - pad)
            y1 = max(0, y_min - pad)
            x2 = min(image.shape[1], x_max + pad)
            y2 = min(image.shape[0], y_max + pad)
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
            
        if not self.is_loaded or self.session is None:
            print("[LaMa] Executing OpenCV INPAINT_TELEA fallback...")
            return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)

        try:
            inpainting_size = int(self.config.get('inpainting_size', 2048))
            h, w = image.shape[:2]
            
            # Check if model has a fixed expected shape
            is_fixed_shape = False
            fixed_h, fixed_w = None, None
            
            try:
                for inp in self.session.get_inputs():
                    shape = inp.shape
                    print(f"[LaMa] Input '{inp.name}' expected shape: {shape}")
                    if shape and len(shape) == 4:
                        if isinstance(shape[2], (int, float)) and isinstance(shape[3], (int, float)):
                            is_fixed_shape = True
                            fixed_h = int(shape[2])
                            fixed_w = int(shape[3])
                            break
            except Exception as e:
                print(f"[LaMa] Warning: Could not inspect ONNX shapes: {e}")
                    
            if is_fixed_shape and fixed_h and fixed_w:
                print(f"[LaMa] Detected fixed spatial dimensions. Forcing resize to {fixed_w}x{fixed_h}.")
                work_img = cv2.resize(image, (fixed_w, fixed_h), interpolation=cv2.INTER_AREA)
                work_mask = cv2.resize(mask, (fixed_w, fixed_h), interpolation=cv2.INTER_NEAREST)
                ratio = -1.0 # Force resize back later
            else:
                # Downscale if needed
                ratio = 1.0
                if max(h, w) > inpainting_size:
                    ratio = float(inpainting_size) / max(h, w)
                    resize_h = int(h * ratio)
                    resize_w = int(w * ratio)
                    work_img = cv2.resize(image, (resize_w, resize_h), interpolation=cv2.INTER_AREA)
                    work_mask = cv2.resize(mask, (resize_w, resize_h), interpolation=cv2.INTER_NEAREST)
                else:
                    work_img = image.copy()
                    work_mask = mask.copy()

            # Preprocess
            image_padded = pad_img_to_modulo(work_img, 8)
            mask_padded = pad_img_to_modulo(work_mask, 8)

            img_rgb = cv2.cvtColor(image_padded, cv2.COLOR_BGR2RGB)
            img_input = img_rgb.astype(np.float32) / 255.0
            img_input = np.transpose(img_input, (2, 0, 1))
            img_input = np.expand_dims(img_input, axis=0)

            mask_input = mask_padded.astype(np.float32) / 255.0
            mask_input[mask_input > 0] = 1.0
            mask_input = np.expand_dims(mask_input, axis=0)
            mask_input = np.expand_dims(mask_input, axis=0)

            # Inference
            inputs = {
                self.input_name_img: img_input,
                self.input_name_mask: mask_input
            }
            outputs = self.session.run(None, inputs)
            out_tensor = outputs[0]

            # Postprocess
            out_img = out_tensor[0]
            out_img = np.transpose(out_img, (1, 2, 0))
            out_img = np.clip(out_img * 255.0, 0, 255).astype(np.uint8)
            out_img_bgr = cv2.cvtColor(out_img, cv2.COLOR_RGB2BGR)

            # Crop padded part
            work_h, work_w = work_img.shape[:2]
            out_img_bgr = out_img_bgr[:work_h, :work_w]
            
            # Upscale back to original size if it was downscaled
            if ratio < 1.0:
                out_img_bgr = cv2.resize(out_img_bgr, (w, h), interpolation=cv2.INTER_CUBIC)

            # Blend
            mask_bool = (mask > 0)[:, :, np.newaxis]
            result = image * (~mask_bool) + out_img_bgr * mask_bool
            return result.astype(np.uint8)
            
        except Exception as e:
            print(f"[LaMa] ONNX Inference failed: {e}. Executing OpenCV INPAINT_TELEA fallback...")
            return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)
