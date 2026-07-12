"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.api_profile.mapping
- RESPONSIBILITY: mapping.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.logic.api_profile.mapping.
=============================================================================
"""
def get_profile_mapping(service: str) -> dict:
    mappings = {
        "OCR": {'name': 'ocr_api_name', 'provider': 'api_ocr', 'endpoint': 'ocr_api_endpoint', 'model': 'ocr_api_model', 'key': 'ocr_api_key'},
        "Translator": {'name': 'api_name', 'provider': 'ai_translator', 'endpoint': 'ai_endpoint', 'model': 'ai_model', 'key': 'ai_key', 'max_retries': 'max_retries'},
    }
    return mappings.get(service, mappings["Translator"])
