import os, sys, cv2, numpy as np
sys.path.insert(0, os.path.abspath('.'))
from app.plugins.upscaler.esrgan_impl import ESRGANUpscaler_Impl
upscaler = ESRGANUpscaler_Impl()
upscaler.load_model("models/Upscaler/ESRGAN/esrgan-linux/models/4x-UltraSharp.bin")

# Create a small dummy image
dummy = np.zeros((100, 100, 3), dtype=np.uint8)
cv2.putText(dummy, "Test", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

out = upscaler.upscale(dummy, ratio=2)
print("Output shape:", out.shape)
