"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.upscaler.esrgan.main_impl
- RESPONSIBILITY: Khởi tạo và đăng ký ESRGAN (và các biến thể Waifu2x, 4xUltraSharp) vào plugin factory.
- CALLED BY: app.core.shared_registry.discovery (Auto-discovered)
- CALLS TO: loader.load_esrgan_model, upscale.upscale_esrgan
- IN = OUT: Khai báo plugin theo chuẩn BaseUpscaler.
=============================================================================
"""
import numpy as np

from app.core.inpainter.interfaces import BaseUpscaler
from app.core.shared_registry import UpscalerFactory
from app.plugins.upscaler.esrgan.loader import load_esrgan_model
from app.plugins.upscaler.esrgan.upscale import upscale_esrgan

@UpscalerFactory.register("esrgan")
@UpscalerFactory.register("waifu2x")
@UpscalerFactory.register("4xultrasharp")
class ESRGANUpscaler_Impl(BaseUpscaler):
    MODELS = [
        {'key': 'esrgan', 'check_file': 'models/Upscaler/ESRGAN/esrgan-{os}/realesrgan-ncnn-vulkan{exe}', 'source': 'https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/realesrgan-ncnn-vulkan-20220424-ubuntu.zip'},
        {'key': 'waifu2x', 'check_file': 'models/Upscaler/Waifu2x/waifu2x-{os}/waifu2x-ncnn-vulkan{exe}', 'source': 'https://github.com/nihui/waifu2x-ncnn-vulkan/releases/download/20220728/waifu2x-ncnn-vulkan-20220728-ubuntu.zip'},
        {'key': '4xultrasharp'},
    ]

    def __init__(self):
        self.model_path = None
        self.is_loaded = False
        self.key = "esrgan"
        self.executable_path = None

    def _get_source_url_from_registry(self, key: str) -> str:
        return UpscalerFactory.get_source_url_from_registry("upscaler", key)

    def load_model(self, model_path: str, **kwargs) -> None:
        load_esrgan_model(self, model_path, **kwargs)

    def upscale(self, image: np.ndarray, ratio: int) -> np.ndarray:
        return upscale_esrgan(self, image, ratio)
