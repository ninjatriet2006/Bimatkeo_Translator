import os
import cv2
import numpy as np
from typing import List, Any

from app.core.interfaces import BaseDiffusionModel
from app.core.factories import DiffusionFactory

try:
    import torch
    from diffusers import AutoPipelineForInpainting # type: ignore
    from PIL import Image
except ImportError:
    torch = None
    AutoPipelineForInpainting = None
    Image = None

@DiffusionFactory.register("powerpaint_v1")
class PowerPaintV1_Impl(BaseDiffusionModel):
    MODELS = [
        {'key': 'powerpaint_v1', 'label': 'powerpaint_v1'},
    ]

    REQUIRES_SD_BASE_MODEL = True
    
    def __init__(self):
        self.model_path = None
        self.is_loaded = False
        self.pipe = None
        self.config = {}

    def load_model(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        self.config = kwargs
        
        # Check if the folder contains model_index.json
        model_dir = os.path.dirname(self.model_path) if os.path.isfile(self.model_path) else self.model_path
        if not os.path.exists(os.path.join(model_dir, "model_index.json")):
            print(f"[PowerPaint] Model not found at {model_dir}. Please download it from the Settings UI.")
            return
        
        if torch is None or AutoPipelineForInpainting is None:
            print("[PowerPaint] 'diffusers' or 'torch' is not installed. Please check requirements.txt.")
            return

        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            precision_str = self.config.get("inpainting_precision", "fp16")
            if device == "cpu":
                dtype = torch.float32
            else:
                if precision_str == "fp32":
                    dtype = torch.float32
                elif precision_str == "bf16":
                    dtype = torch.bfloat16
                else:
                    dtype = torch.float16
            
            print(f"[PowerPaint] Loading diffusers pipeline from {model_dir} to {device}...")
            assert AutoPipelineForInpainting is not None
            pipeline: Any = AutoPipelineForInpainting.from_pretrained(
                model_dir,
                torch_dtype=dtype,
                variant="fp16" if device == "cuda" else None,
                local_files_only=True
            )
            self.pipe = pipeline.to(device)  # type: ignore
            
            self.pipe.set_progress_bar_config(disable=True)
            
            print(f"[PowerPaint] Model loaded successfully.")
            self.is_loaded = True
        except Exception as e:
            print(f"[PowerPaint] Failed to load diffusers model: {e}")

    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        if not bboxes:
            return image

        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        for box in bboxes:
            x_min, y_min, x_max, y_max = box
            pad = 5
            x1 = max(0, x_min - pad)
            y1 = max(0, y_min - pad)
            x2 = min(image.shape[1], x_max + pad)
            y2 = min(image.shape[0], y_max + pad)
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
            
        if not self.is_loaded or self.pipe is None:
            print("[PowerPaint] Not loaded. Executing OpenCV INPAINT_TELEA fallback...")
            return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)

        try:
            if Image is None:
                raise RuntimeError("PIL is not installed. Please install it via requirements.txt.")
                
            # Resize logic for 512px limit
            h, w = image.shape[:2]
            max_dim = 512
            resize_ratio = 1.0
            work_img = image
            work_mask = mask
            
            if max(h, w) > max_dim:
                resize_ratio = float(max_dim) / max(h, w)
                new_w = int(w * resize_ratio)
                new_h = int(h * resize_ratio)
                # Multiples of 8
                new_w = max(8, (new_w // 8) * 8)
                new_h = max(8, (new_h // 8) * 8)
                work_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
                work_mask = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
            else:
                new_w = max(8, (w // 8) * 8)
                new_h = max(8, (h // 8) * 8)
                if new_w != w or new_h != h:
                    work_img = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    work_mask = cv2.resize(mask, (new_w, new_h), interpolation=cv2.INTER_NEAREST)
                else:
                    new_w, new_h = w, h

            # Convert CV2 BGR to PIL RGB
            img_rgb = cv2.cvtColor(work_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            pil_mask = Image.fromarray(work_mask)

            # Standard erasing prompt for PowerPaint is "empty, object removal" 
            prompt = "empty, object removal"
            negative_prompt = "text"

            print(f"[PowerPaint] Running diffusion inference at {new_w}x{new_h}...")
            output = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                image=pil_img,
                mask_image=pil_mask,
                num_inference_steps=25,
                guidance_scale=7.5
            ).images[0]

            out_bgr_resized = cv2.cvtColor(np.array(output), cv2.COLOR_RGB2BGR)
            
            if out_bgr_resized.shape[:2] != (h, w):
                out_bgr = cv2.resize(out_bgr_resized, (w, h), interpolation=cv2.INTER_CUBIC)
            else:
                out_bgr = out_bgr_resized

            # Blend back using mask to keep non-masked regions perfectly original
            mask_bool = (mask > 0)[:, :, np.newaxis]
            result = image * (~mask_bool) + out_bgr * mask_bool
            return result.astype(np.uint8)
            
        except Exception as e:
            msg = f"[PowerPaint] Inference failed: {e}. Executing OpenCV INPAINT_TELEA fallback..."
            print(msg)
            if self.config.get('log_callback'):
                self.config['log_callback']("WARNING", msg)
            return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)
