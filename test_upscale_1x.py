import os, sys, cv2, numpy as np
sys.path.insert(0, os.path.abspath('.'))
from app.plugins.upscaler.esrgan_impl import ESRGANUpscaler_Impl
upscaler = ESRGANUpscaler_Impl()
upscaler.load_model("models/Upscaler/ESRGAN/esrgan-linux/models/4x-UltraSharp.bin")

dummy = np.zeros((100, 100, 3), dtype=np.uint8)
cv2.imwrite("temp_in.png", dummy)

import subprocess
cmd = [upscaler.executable_path, "-i", "temp_in.png", "-o", "temp_out.png", "-s", "1", "-n", "4x-UltraSharp"]
print("Running:", " ".join(cmd))
res = subprocess.run(cmd, capture_output=True, text=True)
print("Return code:", res.returncode)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
