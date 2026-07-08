"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.inpainter.manager
- RESPONSIBILITY: Đọc config và tải model tương ứng.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.factories (InpainterFactory, UpscalerFactory), app.core.downloader
- IN = OUT: Nhận config_dict -> trả về instance của Inpainter và Upscaler.
=============================================================================
"""

from app.core.downloader import ModelDownloader
from app.core.factories import InpainterFactory, DiffusionFactory, UpscalerFactory

class InpainterManager:
    @staticmethod
    def initialize(config_dict: dict, log_callback=None):
        """
        Khởi tạo và trả về (inpainter, upscaler, enable_upscaler, upscale_ratio) dựa trên config.
        """
        enable_inpainter = config_dict.get("pipeline", {}).get("enable_inpainter", True)
        
        inpainter = None
        if enable_inpainter:
            enable_advanced_diffusion = config_dict.get("inpainter", {}).get("enable_advanced_diffusion", False)
            if enable_advanced_diffusion:
                inpainter_name = config_dict.get("inpainter", {}).get("diffusion_model", "powerpaint_v1")
                try:
                    inp_path = ModelDownloader.get_model_path_from_registry("diffusion_model", inpainter_name)
                    if inpainter_name != "none":
                        inpainter = DiffusionFactory.create(inpainter_name, model_path=inp_path, log_callback=log_callback, **config_dict.get("inpainter", {}))
                except ValueError:
                    if log_callback:
                        log_callback("WARNING", f"Diffusion Model '{inpainter_name}' not found, falling back to None.")
            else:
                inpainter_name = config_dict.get("inpainter", {}).get("inpainter", "lama")
                try:
                    inp_path = ModelDownloader.get_model_path_from_registry("inpainter", inpainter_name)
                    if inpainter_name != "none":
                        inpainter = InpainterFactory.create(inpainter_name, model_path=inp_path, log_callback=log_callback, **config_dict.get("inpainter", {}))
                except ValueError:
                    if log_callback:
                        log_callback("WARNING", f"Inpainter '{inpainter_name}' not found, falling back to None.")

        # Upscaler Initialization
        enable_upscaler = config_dict.get("inpainter", {}).get("enable_upscaler", False)
        upscale_ratio = int(config_dict.get("inpainter", {}).get("upscale_ratio", 2))
        upscaler = None
        
        if enable_upscaler:
            upscaler_name = config_dict.get("inpainter", {}).get("upscaler", "esrgan")
            try:
                ups_path = ModelDownloader.get_model_path_from_registry("upscaler", upscaler_name)
                upscaler = UpscalerFactory.create(upscaler_name)
                upscaler.load_model(ups_path)
            except Exception as e:
                if log_callback:
                    log_callback("WARNING", f"Upscaler '{upscaler_name}' could not be loaded: {e}. Falling back to None.")
                upscaler = None

        return inpainter, upscaler, enable_upscaler, upscale_ratio
