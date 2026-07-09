"""
Plugin khai báo metadata cho Colorizer Models.
"""
from app.core.shared_registry import ColorizerFactory
import os

@ColorizerFactory.register("mc2")
class MC2_Colorizer:
    MODELS = [
        {
            "key": "mc2",
            "label": "MC2 Colorizer",
            "check_file": os.path.join("models", "Colorizer", "mc2", "mc2_model.onnx"),
            "source": ""
        }
    ]

@ColorizerFactory.register("ddcolor")
class DDColor_Colorizer:
    MODELS = [
        {
            "key": "ddcolor",
            "label": "DDColor",
            "check_file": os.path.join("models", "Colorizer", "ddcolor", "ddcolor_model.onnx"),
            "source": ""
        }
    ]
