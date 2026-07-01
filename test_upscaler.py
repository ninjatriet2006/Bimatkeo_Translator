import os, sys
sys.path.insert(0, os.path.abspath('.'))
from app.plugins.upscaler.esrgan_impl import ESRGANUpscaler_Impl
upscaler = ESRGANUpscaler_Impl()
upscaler.load_model("models/Upscaler/ESRGAN/esrgan-linux/models/4x-UltraSharp.bin")
print(upscaler.executable_path)
