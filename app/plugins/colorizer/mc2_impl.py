import os
import yaml
import cv2
import numpy as np

from app.core.interfaces import BaseColorizer
from app.core.factories import ColorizerFactory
from app.core.downloader import ModelDownloader

@ColorizerFactory.register("mc2")
class MangaColorization_Impl(BaseColorizer):
    DISPLAY_NAME = "qdraw/MangaColorizationV2"
    def __init__(self):
        self.model_path = None
        self.is_loaded = False

    def _get_source_url_from_registry(self, key: str) -> str:
        registry_path = os.path.join(".config", "models", "model_registry.yaml")
        if not os.path.exists(registry_path):
            return ""
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            colorizers = data.get("fields", {}).get("colorizer", [])
            for item in colorizers:
                if item.get("key") == key:
                    return item.get("source", "")
        except Exception as e:
            print(f"[Colorizer] Failed to parse registry: {e}")
        return ""

    def load_model(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        key = "mc2"
            
        if not os.path.exists(self.model_path):
            source_url = self._get_source_url_from_registry(key)
            if source_url:
                target_dir = os.path.dirname(self.model_path)
                expected_files = [os.path.basename(self.model_path)]
                print(f"[Colorizer] Downloading weights from {source_url}...")
                success = ModelDownloader.download_and_extract(
                    source_url, target_dir, expected_files, extract=True
                )
                if not success:
                    print(f"[Colorizer] Failed to download weights for {key}.")
                    return
            else:
                print(f"[Colorizer] No source URL found in registry for {key}.")
                return
        
        print(f"[Colorizer] Model confirmed at {self.model_path}. Inference fallback to original image.")
        self.is_loaded = True

    def colorize(self, image: np.ndarray) -> np.ndarray:
        if not self.is_loaded:
            return image
            
        print("[Colorizer] Executing Colorizer (fallback: pass-through)...")
        # To truly colorize manga, you need full GAN inference
        # Returning original image for now to keep pipeline unbroken
        return image
