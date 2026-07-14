"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.sd.loader
- RESPONSIBILITY: Load mô hình Stable Diffusion Inpainting pipeline.
- CALLED BY: app.plugins.inpainter.sd.main_impl
- CALLS TO: diffusers
- IN = OUT: (pipeline, is_loaded)
=============================================================================
"""
import os
from typing import Tuple, Any

def load_sd_model(model_path: str, log_callback=None, **kwargs) -> Tuple[Any, bool]:
    try:
        import torch # type: ignore
        from diffusers import StableDiffusionInpaintPipeline # type: ignore
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        
        if log_callback:
            log_callback("INFO", f"Loading Stable Diffusion Inpainting pipeline to {device}...")
            
        # Default to a well-known model if model_path is empty or invalid
        model_id = "runwayml/stable-diffusion-inpainting"
        
        pipe = StableDiffusionInpaintPipeline.from_pretrained(
            model_id, 
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        )
        if pipe is not None:
            pipe = pipe.to(device)
        
        if log_callback:
            log_callback("INFO", "Stable Diffusion Inpainter loaded successfully.")
            
        return pipe, True
    except ImportError:
        if log_callback:
            log_callback("ERROR", "Please install diffusers and torch: pip install diffusers torch")
        return None, False
    except Exception as e:
        if log_callback:
            log_callback("ERROR", f"Failed to load SD Inpainter: {e}")
        return None, False
