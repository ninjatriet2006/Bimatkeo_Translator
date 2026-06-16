import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from desktop_ui.config_loader import ConfigLoader

cl = ConfigLoader(BASE_DIR)

current_langs = cl.languages if hasattr(cl, 'languages') else cl._load_backend_languages()
print(f"Current supported target languages: {len(current_langs)}")

print("\nFetching from Lingva...")
try:
    lingva_langs = cl.fetch_online_languages_lingva()
    print(f"Lingva total languages: {len(lingva_langs)}")
    missing_from_lingva = set(lingva_langs.keys()) - set(current_langs.keys())
    print(f"Missing compared to Lingva: {len(missing_from_lingva)}")
    # Update config with Lingva since it usually has more
    cl.save_languages_config(lingva_langs)
    print("Updated supporttargetlang.yaml with Lingva languages.")
except Exception as e:
    print(f"Lingva failed: {e}")

print("\nFetching from LibreTranslate...")
try:
    libre_langs = cl.fetch_online_languages_libretranslate()
    print(f"LibreTranslate total languages: {len(libre_langs)}")
    missing_from_libre = set(libre_langs.keys()) - set(current_langs.keys())
    print(f"Missing compared to LibreTranslate: {len(missing_from_libre)}")
except Exception as e:
    print(f"LibreTranslate failed: {e}")

