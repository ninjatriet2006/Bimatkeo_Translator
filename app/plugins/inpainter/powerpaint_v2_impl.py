import os
import sys

from typing import Any
from app.core.interfaces import BaseInpainter
from app.core.factories import InpainterFactory

try:
    import torch
    import numpy as np
    from PIL import Image
    from diffusers import DPMSolverMultistepScheduler
    from transformers import CLIPTextModel
except ImportError:
    torch = None
    Image = None

@InpainterFactory.register("powerpaint_v2")
class PowerPaintV2_Impl(BaseInpainter):
    DISPLAY_NAME = {
        "powerpaint_v2": "Sanster/PowerPaint-v2 (BrushNet)"
    }
    
    def __init__(self):
        self.model_path: str = ""
        self.is_loaded = False
        self.pipe = None
        self.config = {}

    def setup(self, model_path: str, **kwargs):
        # model_path points to check_file: .../models/Inpainter/PowerPaint_v2/PowerPaint_Brushnet/diffusion_pytorch_model.safetensors
        # The base dir is 2 levels up
        self.model_path = os.path.dirname(os.path.dirname(model_path))
        self.config = kwargs
        
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
            if powerpaint_code_dir not in sys.path:
                sys.path.insert(0, powerpaint_code_dir)
                
            from BrushNet_CA import BrushNetModel  # type: ignore
            from pipeline_PowerPaint_Brushnet_CA import StableDiffusionPowerPaintBrushNetPipeline  # type: ignore
            
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
            
    def process(self, image: Any, mask: Any, prompt: str = "", **kwargs) -> Any:
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
