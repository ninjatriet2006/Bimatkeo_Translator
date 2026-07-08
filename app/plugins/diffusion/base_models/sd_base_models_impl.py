"""
Plugin khai báo metadata cho Diffusion Base Models (sd_1_5, sd_nsfw).
Các base model này chỉ là trọng số, không có class thực thi.
"""
from app.core.factories import DiffusionBaseModelFactory
import os

@DiffusionBaseModelFactory.register("sd_1_5")
class SD_1_5_BaseModel:
    MODELS = [
        {
            "key": "sd_1_5",
            "label": "Stable Diffusion 1.5",
            "check_file": os.path.join("models", "huggingface_cache", "models--runwayml--stable-diffusion-v1-5", "refs", "main"),
            "source": "hf://runwayml/stable-diffusion-v1-5"
        }
    ]

@DiffusionBaseModelFactory.register("sd_nsfw")
class SD_NSFW_BaseModel:
    MODELS = [
        {
            "key": "sd_nsfw",
            "label": "Kernel SD NSFW",
            "check_file": os.path.join("models", "huggingface_cache", "models--Kernel--sd-nsfw", "refs", "main"),
            "source": "hf://Kernel/sd-nsfw"
        }
    ]
