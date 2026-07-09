"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.upscaler.esrgan.upscale
- RESPONSIBILITY: Thực thi subprocess của ncnn-vulkan để upscale ảnh.
- CALLED BY: app.plugins.upscaler.esrgan.main_impl
- CALLS TO: None
- IN = OUT: Nhận ảnh (OpenCV), ratio; trả về ảnh đã upscale.
=============================================================================
"""
import os
import cv2
import numpy as np
import subprocess
import tempfile

def upscale_esrgan(upscaler_instance, image: np.ndarray, ratio: int) -> np.ndarray:
    if not upscaler_instance.is_loaded or ratio < 1:
        return image
    
    print(f"[Upscaler] Upscaling image by {ratio}x using {upscaler_instance.key} (ncnn-vulkan)...")
    
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            in_path = os.path.join(temp_dir, "in.png")
            out_path = os.path.join(temp_dir, "out.png")
            
            # Save input image
            cv2.imwrite(in_path, image)
            
            if not upscaler_instance.executable_path:
                print("[Upscaler] Engine path is missing.")
                h, w = image.shape[:2]
                return cv2.resize(image, (w * ratio, h * ratio), interpolation=cv2.INTER_CUBIC)
            
            # Build command
            cmd: list[str] = [upscaler_instance.executable_path, "-i", in_path, "-o", out_path, "-s", str(ratio)]
            
            # Add model name if 4xultrasharp
            if upscaler_instance.key == "4xultrasharp":
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
