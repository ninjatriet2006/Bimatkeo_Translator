import os
import sys
import cv2

from typing import Any, List
from app.core.interfaces import BaseDiffusionModel
from app.core.factories import DiffusionMainModelFactory

try:
    import torch
    import numpy as np
    from PIL import Image
    from diffusers import DPMSolverMultistepScheduler
    from transformers import CLIPTextModel
except ImportError:
    torch = None
    Image = None

@DiffusionMainModelFactory.register("powerpaint_v2")
class PowerPaintV2_Impl(BaseDiffusionModel):
    MODELS = [
        {'key': 'powerpaint_v2', 'label': 'Sanster/PowerPaint-v2 (BrushNet) (Max 512px)', 'check_file': os.path.join("models", "Diffusion", "Main_Models", "PowerPaint_v2", "PowerPaint_Brushnet", "diffusion_pytorch_model.safetensors")},
    ]

    REQUIRES_SD_BASE_MODEL = True

    def __init__(self):
        self.model_path: str = ""
        self.is_loaded = False
        self.pipe = None
        self.config = {}

    def load_model(self, model_path: str, **kwargs) -> None:
        # model_path points to check_file: .../models/Inpainter/PowerPaint_v2/PowerPaint_Brushnet/diffusion_pytorch_model.safetensors
        # The base dir is 2 levels up
        self.model_path = os.path.dirname(os.path.dirname(model_path))
        self.config = kwargs
        self.load()
        
    def load(self):
        if self.is_loaded:
            return True
            
        if not torch or not Image:
            raise RuntimeError("Missing required dependencies (torch, diffusers, PIL).")
            
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
                    
            powerpaint_code_dir = os.path.join(self.model_path, "powerpaint_v2")
            if self.model_path not in sys.path:
                sys.path.insert(0, self.model_path)
                
            from powerpaint_v2.BrushNet_CA import BrushNetModel  # type: ignore
            from powerpaint_v2.pipeline_PowerPaint_Brushnet_CA import StableDiffusionPowerPaintBrushNetPipeline  # type: ignore
            
            # Khởi tạo Text Encoder tùy chỉnh
            text_encoder_brushnet_path = os.path.join(self.model_path, "text_encoder_brushnet")
            text_encoder_brushnet = CLIPTextModel.from_pretrained(
                text_encoder_brushnet_path,
                torch_dtype=dtype,
            )
            
            # Khởi tạo BrushNet
            brushnet_path = os.path.join(self.model_path, "PowerPaint_Brushnet")
            brushnet = BrushNetModel.from_pretrained(
                brushnet_path,
                torch_dtype=dtype,
            )
            
            # Base model cho diffusers (chủ yếu là runwayml/stable-diffusion-v1-5)
            # Hệ thống sẽ tự tải về ~/.cache/huggingface nếu chưa có
            base_model_key = self.config.get("sd_base_model", "sd_1_5")
            if base_model_key == "sd_nsfw":
                base_model_name = "Kernel/sd-nsfw"
            else:
                base_model_name = "runwayml/stable-diffusion-v1-5"
            
            self.pipe = StableDiffusionPowerPaintBrushNetPipeline.from_pretrained(
                base_model_name,
                brushnet=brushnet,
                text_encoder_brushnet=text_encoder_brushnet,
                torch_dtype=dtype,
                low_cpu_mem_usage=True,
                safety_checker=None,
            )
            
            self.pipe.scheduler = DPMSolverMultistepScheduler.from_config(self.pipe.scheduler.config)
            
            self.pipe = self.pipe.to(device)
            
            self.is_loaded = True
            return True
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"[PowerPaint V2] Error loading model: {e}")
            return False
            
    def task_to_prompt(self, control_type):
        if control_type == "object-removal":
            promptA = "P_ctxt"
            promptB = "P_ctxt"
            negative_promptA = "P_obj"
            negative_promptB = "P_obj"
        elif control_type == "context-aware":
            promptA = "P_ctxt"
            promptB = "P_ctxt"
            negative_promptA = ""
            negative_promptB = ""
        elif control_type == "shape-guided":
            promptA = "P_shape"
            promptB = "P_ctxt"
            negative_promptA = "P_shape"
            negative_promptB = "P_ctxt"
        elif control_type == "image-outpainting":
            promptA = "P_ctxt"
            promptB = "P_ctxt"
            negative_promptA = "P_obj"
            negative_promptB = "P_obj"
        else:
            promptA = "P_obj"
            promptB = "P_obj"
            negative_promptA = "P_obj"
            negative_promptB = "P_obj"
    
        return promptA, promptB, negative_promptA, negative_promptB
            
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
            msg = "[PowerPaint V2] Not loaded. Executing OpenCV INPAINT_TELEA fallback..."
            print(msg)
            if hasattr(self, 'config') and self.config.get('log_callback'):
                self.config['log_callback']("WARNING", msg)
            return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)

        try:
            if Image is None:
                raise RuntimeError("PIL is not installed.")
                
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

            img_rgb = cv2.cvtColor(work_img, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(img_rgb)
            pil_mask = Image.fromarray(work_mask)

            print(f"[PowerPaint V2] Running diffusion inference at {new_w}x{new_h}...")
            output = self._process(
                image=pil_img,
                mask=pil_mask,
                prompt="empty, object removal",
                negative_prompt="text",
                steps=25,
                guidance_scale=7.5
            )

            out_bgr_resized = cv2.cvtColor(np.array(output), cv2.COLOR_RGB2BGR)
            
            if out_bgr_resized.shape[:2] != (h, w):
                out_bgr = cv2.resize(out_bgr_resized, (w, h), interpolation=cv2.INTER_CUBIC)
            else:
                out_bgr = out_bgr_resized

            mask_bool = (mask > 0)[:, :, np.newaxis]
            result = image * (~mask_bool) + out_bgr * mask_bool
            return result.astype(np.uint8)
        except Exception as e:
            msg = f"[PowerPaint V2] Inference failed: {e}. Executing OpenCV INPAINT_TELEA fallback..."
            print(msg)
            if hasattr(self, 'config') and self.config.get('log_callback'):
                self.config['log_callback']("WARNING", msg)
            return cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)

    def _process(self, image: Any, mask: Any, prompt: str = "", **kwargs) -> Any:
        if not self.is_loaded or self.pipe is None:
            if not self.load():
                raise RuntimeError("Failed to load PowerPaint V2 model")
                
        # Padding mask to make sure shape is divisible by 8
        img = np.array(image.convert("RGB"))
        W = int(np.shape(img)[0] - np.shape(img)[0] % 8)
        H = int(np.shape(img)[1] - np.shape(img)[1] % 8)
        
        image = image.resize((H, W))
        mask = mask.resize((H, W))
        
        np_inpimg = np.array(image)
        np_inmask = np.array(mask.convert("L")) / 255.0
        if len(np_inmask.shape) == 2:
            np_inmask = np_inmask[:, :, np.newaxis]
            
        np_inpimg = np_inpimg * (1 - np_inmask)
        image_in = Image.fromarray(np_inpimg.astype(np.uint8)).convert("RGB")  # type: ignore
        
        # Mặc định sử dụng text-guided
        control_type = "text-guided" 
        promptA, promptB, negative_promptA, negative_promptB = self.task_to_prompt(control_type)
        
        ddim_steps = kwargs.get("steps", 30)
        scale = kwargs.get("guidance_scale", 7.5)
        fitting_degree = kwargs.get("fitting_degree", 1.0)
        negative_prompt = kwargs.get("negative_prompt", "")
        
        assert torch is not None
        assert self.pipe is not None
        with torch.inference_mode():  # type: ignore
            result = self.pipe(
                promptA=promptA,
                promptB=promptB,
                promptU=prompt,
                tradoff=fitting_degree,
                tradoff_nag=fitting_degree,
                image=image_in,
                mask=mask.convert("RGB"),
                num_inference_steps=ddim_steps,
                brushnet_conditioning_scale=1.0,
                negative_promptA=negative_promptA,
                negative_promptB=negative_promptB,
                negative_promptU=negative_prompt,
                guidance_scale=scale,
                width=H,
                height=W,
            ).images[0]
            
        # Resize lại về ảnh gốc
        result = result.resize((img.shape[1], img.shape[0]))
        return result
        
    def unload(self):
        if self.pipe:
            del self.pipe
            self.pipe = None
        if torch and torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.is_loaded = False
