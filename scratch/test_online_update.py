import sys
import os

# Configure paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from desktop_ui.config_loader import ConfigLoader

cl = ConfigLoader(BASE_DIR)

print("--- Testing fetch_online_languages_libretranslate ---")
try:
    langs = cl.fetch_online_languages_libretranslate()
    print(f"LibreTranslate Success! Loaded {len(langs)} languages.")
    print(f"Sample languages: {list(langs.items())[:5]}")
except Exception as e:
    print(f"LibreTranslate Failed: {e}")

print("\n--- Testing fetch_online_languages_lingva ---")
try:
    langs = cl.fetch_online_languages_lingva()
    print(f"Lingva Success! Loaded {len(langs)} languages.")
    print(f"Sample languages: {list(langs.items())[:5]}")
except Exception as e:
    print(f"Lingva Failed: {e}")

print("\n--- Testing update_single_translator_capabilities (mock) ---")
try:
    success, msg = cl.update_single_translator_capabilities("sakura")
    print(f"Update single sakura status: {success}, msg: {msg}")
except Exception as e:
    print(f"Update single failed: {e}")
