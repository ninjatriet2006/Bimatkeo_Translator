import sys
import os

# Configure paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from desktop_ui.config_loader import ConfigLoader

# Initialize ConfigLoader
cl = ConfigLoader(BASE_DIR)

# Dynamically loaded constants
LANGUAGES = cl.languages
TRANSLATOR_CAPABILITIES = cl.translator_capabilities

print(f"Dynamic LANGUAGES loaded count: {len(LANGUAGES)}")
print(f"Dynamic TRANSLATOR_CAPABILITIES loaded count: {len(TRANSLATOR_CAPABILITIES)}")

# Test helper supports_target function
def supports_target(translator_name, target_code):
    if translator_name in ["none", "original"]:
        return True
    capabilities = TRANSLATOR_CAPABILITIES.get(translator_name, {'__any__': '__all__'})
    if capabilities.get('__any__') == '__all__':
        return True
    for source_lang, target_langs in capabilities.items():
        if target_code in target_langs:
            return True
    return False

# Check translator capabilities for Vietnamese (VIN) vs English (ENG)
for lang_name, target_code in [("English", "ENG"), ("Vietnamese", "VIN"), ("Japanese", "JPN")]:
    print(f"\n--- Translators supporting Target Lang: {lang_name} ({target_code}) ---")
    
    # Offline
    offline_models = cl.translator_groups["--- OFFLINE MODELS (No API Key) ---"]
    supported_offline = [t for t in offline_models if supports_target(t, target_code)]
    print(f"Offline Supported: {supported_offline}")
    
    # AI
    ai_models = cl.translator_groups["--- API-BASED (Requires Setup) ---"]
    supported_ai = [t for t in ai_models if supports_target(t, target_code)]
    print(f"AI/Online Supported: {supported_ai}")

print("\nValidation Succeeded!")
