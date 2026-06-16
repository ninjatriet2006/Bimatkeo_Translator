import sys
import os
sys.path.insert(0, os.path.abspath("."))
from desktop_ui.config_loader import ConfigLoader
loader = ConfigLoader(os.path.abspath("."))
print(loader.translator_capabilities.get("TRANSLATOR_GROUPS"))
print(loader.translator_groups)
