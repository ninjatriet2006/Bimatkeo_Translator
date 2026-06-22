import sys, os
from desktop_ui.config_loader import ConfigLoader

loader = ConfigLoader("/home/bimatkeo/Documents/Translator/Bimatkeo_Translator")
loader.oldsession_config = {"current_settings": {"test": 123}, "theme": "Dark"}
loader.save_oldsession_config()
print(f"Saved to {loader.oldsession_path}")
print(f"File exists: {os.path.exists(loader.oldsession_path)}")
