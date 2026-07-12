"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base.constants
- RESPONSIBILITY: Contains system-wide constants, previously defined in YAML.
- CALLED BY: app.plugins.recognizer.paddle_onnx_rec_impl, desktop_ui.config.registry
- CALLS TO: None
=============================================================================
"""

GLOBAL_RESOURCES = {
    "google_font_metadata": "https://cdn.jsdelivr.net/npm/google-font-metadata/data/google-fonts-v2.json",
    "google_font_css": "https://fonts.googleapis.com/css?family=",
    "paddle_en_dict": "https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/main/ppocr/utils/en_dict.txt"
}

MODEL_PRIORITY_KEYWORDS = {
    "high": ["gpt-4o", "o1", "o3", "deepseek-chat", "mixtral", "llama3"],
    "medium": ["gpt-4", "deepseek", "llama"],
    "low": ["gpt-3.5"],
    "fallback_weight": 5
}

REQUIRED_MODEL_FIELDS = [
    "offline_detector",
    "offline_ocr",
    "inpainter"
]
