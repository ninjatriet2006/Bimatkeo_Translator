import os
import yaml
import cv2
import numpy as np
from typing import List

from app.core.interfaces import BaseInpainter
from app.core.factories import InpainterFactory
from app.core.downloader import ModelDownloader

@InpainterFactory.register("lama")
@InpainterFactory.register("manga_inpaint_v3")
class LamaInpainter_Impl(BaseInpainter):
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
            inpainters = data.get("fields", {}).get("inpainter", [])
            for item in inpainters:
                if item.get("key") == key:
                    return item.get("source", "")
        except Exception as e:
            print(f"[LaMa] Failed to parse registry: {e}")
        return ""

    def load_model(self, model_path: str, **kwargs) -> None:
        self.model_path = model_path
        
        # Identify which key it is based on the path or kwargs.
        # But we also registered two keys. Let's extract key from model_path string or hardcode default
        key = "lama"
        if "manga_inpaint_v3" in model_path.lower():
            key = "manga_inpaint_v3"
            
        if not os.path.exists(self.model_path):
            source_url = self._get_source_url_from_registry(key)
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
        
        # Here we WOULD import torch and load the saicinpainting network.
        # Since we are wrapping it for Phase 5 implementation:
        print(f"[LaMa] Weights confirmed at {self.model_path}. Inference fallback to OpenCV until torch network is ported.")
        self.is_loaded = True

    def inpaint(self, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
        if not self.is_loaded:
            return image
        
        # Create mask from bboxes
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        for box in bboxes:
            x_min, y_min, x_max, y_max = box
            # Expand the box slightly to ensure it covers the text anti-aliasing
            pad = 5
            x1 = max(0, x_min - pad)
            y1 = max(0, y_min - pad)
            x2 = min(image.shape[1], x_max + pad)
            y2 = min(image.shape[0], y_max + pad)
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
            
        # Optional: Use Dense CRF or better mask expansion here if needed.
        
        # Fallback to OpenCV INPAINT_TELEA since actual LaMa inference code (ResNet) 
        # requires full model architecture files which are not present yet.
        print("[LaMa] Executing OpenCV INPAINT_TELEA fallback...")
        inpainted = cv2.inpaint(image, mask, 5, cv2.INPAINT_TELEA)
        return inpainted
