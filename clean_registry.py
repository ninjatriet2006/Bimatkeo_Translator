import os
import sys
from ruamel.yaml import YAML

def clean_registry(base_dir):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    
    path = os.path.join(base_dir, ".config", "models", "model_registry.yaml")
    if not os.path.exists(path):
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f)
        
    remove_models = ["deepl", "youdao", "baidu", "caiyun", "sakura", "papago"]
    
    if "fields" in data:
        if "ai_translator" in data["fields"]:
            ai_translator = data["fields"]["ai_translator"]
            data["fields"]["ai_translator"] = [item for item in ai_translator if item.get("key") not in remove_models]
            
        if "colorizer" in data["fields"]:
            colorizer = data["fields"]["colorizer"]
            data["fields"]["colorizer"] = [item for item in colorizer if item.get("key") != "mc2"]
            
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

if __name__ == "__main__":
    base = "/home/bimatkeo/Documents/Translator/Bimatkeo_Translator"
    clean_registry(base)
    print("Cleaned model registry.")
