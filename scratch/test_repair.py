import sys
import os
sys.path.insert(0, os.path.abspath("."))
from desktop_ui.config_loader import ConfigLoader
loader = ConfigLoader(os.path.abspath("."))
print(loader._DEFAULT_CHECKS['offline_translator']['m2m100'])
with open(".config/models/model_offline_translator.yaml", "r") as f:
    print(f.read())
