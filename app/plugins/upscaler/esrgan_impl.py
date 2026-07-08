import os
import yaml
import cv2
import numpy as np
import subprocess
import tempfile
import sys

from app.core.interfaces import BaseUpscaler
from app.core.factories import UpscalerFactory
from app.core.downloader import ModelDownloader

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
        from app.core.downloader import ModelDownloader
        return UpscalerFactory.get_source_url_from_registry("upscaler", key)

    def _get_executable_path(self, key: str) -> str:
        exe_name = "waifu2x-ncnn-vulkan" if key == "waifu2x" else "realesrgan-ncnn-vulkan"
        if sys.platform == "win32":
            exe_name += ".exe"
            os_name = "windows"
        else:
            os_name = "linux"
        
        base_dir = "models/Upscaler/Waifu2x" if key == "waifu2x" else "models/Upscaler/ESRGAN"
        exe_dir = f"{key}-{os_name}" if key == "waifu2x" else f"esrgan-{os_name}"
        return os.path.abspath(os.path.join(base_dir, exe_dir, exe_name))

    def _download_engine(self, key: str, exe_path: str) -> bool:
        if os.path.exists(exe_path):
            return True
        source_url = self._get_source_url_from_registry(key)
        if not source_url:
            print(f"[Upscaler] No source URL for {key}")
            return False
            
        target_dir = os.path.dirname(exe_path)
        expected_files = [os.path.basename(exe_path)]
        print(f"[Upscaler] Downloading engine from {source_url}...")
        success = ModelDownloader.download_and_extract(
            source_url, target_dir, expected_files, extract=True
        )
        if success and sys.platform != "win32":
            os.chmod(exe_path, 0o755)
        return success

    def load_model(self, model_path: str, **kwargs) -> None:
        self.model_path = os.path.abspath(model_path)
        
        if "4xultrasharp" in model_path.lower() or "4x-ultrasharp" in model_path.lower():
            self.key = "4xultrasharp"
        elif "waifu2x" in model_path.lower():
            self.key = "waifu2x"
        else:
            self.key = "esrgan"
            
        # 1. Download base engine (esrgan for 4xultrasharp, or corresponding engine)
        engine_key = "esrgan" if self.key == "4xultrasharp" else self.key
        self.executable_path = self._get_executable_path(engine_key)
        
        if not self._download_engine(engine_key, self.executable_path):
            print(f"[Upscaler] Failed to download engine for {engine_key}.")
            return
            
        # 2. Download custom model weights if 4xultrasharp
        if self.key == "4xultrasharp":
            if not os.path.exists(self.model_path):
                print(f"[Upscaler] Downloading 4x-UltraSharp weights...")
                repo_id = "Kim2091/UltraSharp"
                target_dir = os.path.dirname(self.model_path)
                os.makedirs(target_dir, exist_ok=True)
                try:
                    from huggingface_hub import hf_hub_download
                    import shutil
                    # Download .bin
                    bin_path = hf_hub_download(repo_id=repo_id, filename="NCNN/4x-UltraSharp-fp16.bin")
                    shutil.copy(bin_path, os.path.join(target_dir, "4x-UltraSharp.bin"))
                    # Download .param
                    param_path = hf_hub_download(repo_id=repo_id, filename="NCNN/4x-UltraSharp-fp16.param")
                    shutil.copy(param_path, os.path.join(target_dir, "4x-UltraSharp.param"))
                    print(f"[Upscaler] Downloaded 4x-UltraSharp to {target_dir}")
                except Exception as e:
                    print(f"[Upscaler] Failed to download 4x-UltraSharp weights: {e}")
                    return
        
        print(f"[Upscaler] Model confirmed: {self.key}. Using engine: {self.executable_path}")
        self.is_loaded = True

    def upscale(self, image: np.ndarray, ratio: int) -> np.ndarray:
        if not self.is_loaded or ratio < 1:
            return image
        
        print(f"[Upscaler] Upscaling image by {ratio}x using {self.key} (ncnn-vulkan)...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                in_path = os.path.join(temp_dir, "in.png")
                out_path = os.path.join(temp_dir, "out.png")
                
                # Save input image
                cv2.imwrite(in_path, image)
                
                if not self.executable_path:
                    print("[Upscaler] Engine path is missing.")
                    h, w = image.shape[:2]
                    return cv2.resize(image, (w * ratio, h * ratio), interpolation=cv2.INTER_CUBIC)
                
                # Build command
                cmd: list[str] = [self.executable_path, "-i", in_path, "-o", out_path, "-s", str(ratio)]
                
                # Add model name if 4xultrasharp
                if self.key == "4xultrasharp":
                    cmd.extend(["-n", "4x-UltraSharp"])
                    
                # Run binary
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Read output image
                if os.path.exists(out_path):
                    upscaled = cv2.imread(out_path)
                    if upscaled is not None:
                        return upscaled
                else:
                    print("[Upscaler] Error: ncnn-vulkan did not produce an output file.")
                    
        except subprocess.CalledProcessError as e:
            print(f"[Upscaler] ncnn-vulkan crashed: {e.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            print(f"[Upscaler] Upscale error: {e}")
            
        print("[Upscaler] Falling back to cv2.INTER_CUBIC due to error.")
        h, w = image.shape[:2]
        return cv2.resize(image, (w * ratio, h * ratio), interpolation=cv2.INTER_CUBIC)
