import sys
import os
import urllib.request
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from desktop_ui.config_loader import ConfigLoader

cl = ConfigLoader(BASE_DIR)

current_langs = cl.languages if hasattr(cl, 'languages') else cl._load_backend_languages()
print(f"Current supported target languages in yaml: {len(current_langs)}")

def get_lingva(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode('utf-8'))

ISO_MAP = {
    "en": "ENG", "vi": "VIN", "ja": "JPN", "ko": "KOR", 
    "zh": "CHS", "es": "ESP", "fr": "FRA", "de": "DEU", 
    "ru": "RUS", "pt": "PTB", "it": "ITA", "pl": "POL", 
    "nl": "NLD", "cs": "CSY", "hu": "HUN", "ro": "ROM", 
    "uk": "UKR", "ar": "ARA", "sr": "SRP", "hr": "HRV", 
    "th": "THA", "id": "IND", "fil": "FIL", "tr": "TRK"
}

instances = ["https://lingva.pussthecat.org/api/v1/languages", "https://translate.plausibility.cloud/api/v1/languages"]

lingva_langs = {}
for url in instances:
    try:
        data = get_lingva(url)
        languages_list = data.get("languages", []) or data.get("targets", [])
        if not languages_list and isinstance(data, list):
            languages_list = data
            
        for item in languages_list:
            code = item.get("code")
            name = item.get("name")
            if code and name:
                app_code = ISO_MAP.get(code.lower(), code.upper())
                lingva_langs[str(name)] = str(app_code)
        print(f"Success with {url}")
        break
    except Exception as e:
        print(f"Failed with {url}: {e}")

if lingva_langs:
    print(f"Lingva total languages: {len(lingva_langs)}")
    missing = set(lingva_langs.keys()) - set(current_langs.keys())
    print(f"Missing compared to Lingva: {len(missing)}")
    cl.save_languages_config(lingva_langs)
    print(f"Updated YAML with Lingva languages. Total now: {len(lingva_langs)}")
