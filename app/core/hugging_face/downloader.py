"""
========================================================================
[AI_ARCH_NOTE]: HUGGINGFACE DOWNLOADER
- Purpose: Handles the actual downloading of models from HuggingFace via snapshot_download or direct API.
- Structure: Methods for downloading with progress tracking.
- Consumed by: manager.py
- Modified by: Developers
- Critical Rules: Must emit progress signals for the UI.
========================================================================
"""
import os
import urllib.request
import urllib.parse
import json

class HFDownloader:
    def __init__(self):
        pass
        
    def download_diffusers(self, repo_id: str, progress_callback=None):
        """
        Downloads a diffusers model (like stable diffusion) using huggingface_hub snapshot_download.
        """
        from huggingface_hub import snapshot_download
        
        if progress_callback:
            progress_callback(30, f"Đang đồng bộ Base Model từ {repo_id}...")
            
        snapshot_download(
            repo_id=repo_id, 
            allow_patterns=[
                "*.json", 
                "*.txt", 
                "unet/*.safetensors", 
                "vae/*.safetensors", 
                "text_encoder/*.safetensors", 
                "tokenizer/*", 
                "scheduler/*", 
                "feature_extractor/*", 
                "safety_checker/*.safetensors"
            ],
            resume_download=True
        )
        
    def download_model(self, repo_id: str, model_dir: str, hf_specific_file: str = None, progress_callback=None):
        """
        Downloads a model using direct HuggingFace API requests, allowing selective file downloads.
        """
        hf_endpoint = os.environ.get("HF_ENDPOINT", "https://huggingface.co")
        tree_url = f"{hf_endpoint}/api/models/{repo_id}/tree/main?recursive=True"
        req = urllib.request.Request(tree_url, headers={'User-Agent': 'Mozilla/5.0'})
        
        if progress_callback:
            progress_callback(10, f"Đang lấy danh sách file từ repository {repo_id}...")
            
        with urllib.request.urlopen(req, timeout=15) as response:
            files_data = json.loads(response.read().decode('utf-8'))
            
        target_files = []
        safetensors_paths = {item.get("path", "") for item in files_data if item.get("path", "").endswith(".safetensors")}
        
        for item in files_data:
            if item.get("type") == "file":
                path = item.get("path", "")
                if hf_specific_file and path != hf_specific_file:
                    continue
                ext = os.path.splitext(path)[1].lower()
                if ext in [".msgpack", ".h5", ".ot", ".md"] or path.startswith("."):
                    continue
                if ext == ".bin":
                    safetensors_equivalent = path[:-4] + ".safetensors"
                    if safetensors_equivalent in safetensors_paths:
                        continue # skip .bin if .safetensors exists
                target_files.append(item)
                
        total_files = len(target_files)
        if total_files == 0:
            raise RuntimeError(f"Không tìm thấy file hợp lệ nào trong repository {repo_id}")
            
        for idx, item in enumerate(target_files):
            path = item.get("path")
            size = item.get("size", 0)
            file_url = f"{hf_endpoint}/{repo_id}/resolve/main/{urllib.parse.quote(path)}"
            local_path = os.path.join(model_dir, path)
            
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            base_percent = 10 + int((idx / total_files) * 80)
            if progress_callback:
                progress_callback(base_percent, f"Đang tải {path} ({idx+1}/{total_files})...")
                
            req_file = urllib.request.Request(file_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req_file, timeout=60) as resp:
                with open(local_path, "wb") as f:
                    downloaded = 0
                    chunk_size = 1024 * 1024
                    while True:
                        chunk = resp.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if size > 0 and downloaded % (2 * 1024 * 1024) < chunk_size:
                            percent = int((downloaded / size) * 100)
                            if progress_callback:
                                current_p = base_percent + int((percent / 100) * (80 / total_files))
                                progress_callback(current_p, f"Đang tải {path} ({idx+1}/{total_files}) - {percent}%")
