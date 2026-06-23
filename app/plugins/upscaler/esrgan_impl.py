import os
import yaml
import cv2
import numpy as np

from app.core.interfaces import BaseUpscaler
from app.core.factories import UpscalerFactory
from app.core.downloader import ModelDownloader

@UpscalerFactory.register("esrgan")
@UpscalerFactory.register("waifu2x")
class ESRGANUpscaler_Impl(BaseUpscaler):
    def __init__(self):
        self.model_path = None
        self.is_loaded = False
        self.upscale_ratio = 2

    def _get_source_url_from_registry(self, key: str) -> str:
        registry_path = os.path.join(".config", "models", "model_registry.yaml")
        if not os.path.exists(registry_path):
            return ""
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            upscalers = data.get("fields", {}).get("upscaler", [])
            for item in upscalers:
                if item.get("key") == key:
                    return item.get("source", "")
        except Exception as e:
            print(f"[Upscaler] Failed to parse registry: {e}")
        return ""

    def load_model(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        
        key = "esrgan"
        if "waifu2x" in model_path.lower():
            key = "waifu2x"
            
        if not os.path.exists(self.model_path):
            source_url = self._get_source_url_from_registry(key)
            if source_url:
                target_dir = os.path.dirname(self.model_path)
                expected_files = [os.path.basename(self.model_path)]
                print(f"[Upscaler] Downloading weights from {source_url}...")
                success = ModelDownloader.download_and_extract(
                    source_url, target_dir, expected_files, extract=True
                )
                if not success:
                    print(f"[Upscaler] Failed to download weights for {key}.")
                    return
            else:
                print(f"[Upscaler] No source URL found in registry for {key}.")
                return
        
        print(f"[Upscaler] Model confirmed at {self.model_path}. Inference fallback to OpenCV INTER_CUBIC.")
        self.is_loaded = True

    def upscale(self, image: np.ndarray, ratio: int) -> np.ndarray:
        if not self.is_loaded or ratio <= 1:
            return image
        
        print(f"[Upscaler] Upscaling image by {ratio}x using fallback cv2.INTER_CUBIC...")
        h, w = image.shape[:2]
        upscaled = cv2.resize(image, (w * ratio, h * ratio), interpolation=cv2.INTER_CUBIC)
        return upscaled
