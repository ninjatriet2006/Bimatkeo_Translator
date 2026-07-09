"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.upscaler.esrgan.loader
- RESPONSIBILITY: Tải models/engines (ncnn-vulkan) cho ESRGAN, Waifu2x, 4xUltraSharp.
- CALLED BY: app.plugins.upscaler.esrgan.main_impl
- CALLS TO: app.core.downloader.ModelDownloader
- IN = OUT: Cấu hình key, tải binary, tải weights (nếu cần), gán executable_path.
=============================================================================
"""
import os
import sys

def _get_executable_path(key: str) -> str:
    exe_name = "waifu2x-ncnn-vulkan" if key == "waifu2x" else "realesrgan-ncnn-vulkan"
    if sys.platform == "win32":
        exe_name += ".exe"
        os_name = "windows"
    else:
        os_name = "linux"
    
    base_dir = "models/Upscaler/Waifu2x" if key == "waifu2x" else "models/Upscaler/ESRGAN"
    exe_dir = f"{key}-{os_name}" if key == "waifu2x" else f"esrgan-{os_name}"
    return os.path.abspath(os.path.join(base_dir, exe_dir, exe_name))

def _download_engine(key: str, exe_path: str, source_url: str) -> bool:
    if os.path.exists(exe_path):
        return True
    if not source_url:
        print(f"[Upscaler] No source URL for {key}")
        return False
        
    target_dir = os.path.dirname(exe_path)
    expected_files = [os.path.basename(exe_path)]
    print(f"[Upscaler] Downloading engine from {source_url}...")
    
    from app.core.downloader import ModelDownloader
    success = ModelDownloader.download_and_extract(
        source_url, target_dir, expected_files, extract=True
    )
    if success and sys.platform != "win32":
        os.chmod(exe_path, 0o755)
    return success

def load_esrgan_model(upscaler_instance, model_path: str, **kwargs):
    upscaler_instance.model_path = os.path.abspath(model_path)
    
    if "4xultrasharp" in model_path.lower() or "4x-ultrasharp" in model_path.lower():
        upscaler_instance.key = "4xultrasharp"
    elif "waifu2x" in model_path.lower():
        upscaler_instance.key = "waifu2x"
    else:
        upscaler_instance.key = "esrgan"
        
    # 1. Download base engine (esrgan for 4xultrasharp, or corresponding engine)
    engine_key = "esrgan" if upscaler_instance.key == "4xultrasharp" else upscaler_instance.key
    upscaler_instance.executable_path = _get_executable_path(engine_key)
    
    source_url = upscaler_instance._get_source_url_from_registry(engine_key)
    if not _download_engine(engine_key, upscaler_instance.executable_path, source_url):
        print(f"[Upscaler] Failed to download engine for {engine_key}.")
        return
        
    # 2. Download custom model weights if 4xultrasharp
    if upscaler_instance.key == "4xultrasharp":
        if not os.path.exists(upscaler_instance.model_path):
            print(f"[Upscaler] Downloading 4x-UltraSharp weights...")
            repo_id = "Kim2091/UltraSharp"
            target_dir = os.path.dirname(upscaler_instance.model_path)
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
    
    print(f"[Upscaler] Model confirmed: {upscaler_instance.key}. Using engine: {upscaler_instance.executable_path}")
    upscaler_instance.is_loaded = True
