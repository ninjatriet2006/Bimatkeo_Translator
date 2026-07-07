import os
import sys
from ruamel.yaml import YAML

def clean_schema(base_dir):
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False
    
    path = os.path.join(base_dir, ".config", "configs", "schema_fallback.yaml")
    if not os.path.exists(path):
        return
        
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.load(f)
        
    remove_models = ["deepl", "youdao", "baidu", "caiyun", "sakura", "papago"]
    
    if "$defs" in data:
        if "Colorizer" in data["$defs"]:
            data["$defs"]["Colorizer"]["enum"] = [m for m in data["$defs"]["Colorizer"].get("enum", []) if m != "mc2"]
            
        if "Translator" in data["$defs"]:
            data["$defs"]["Translator"]["enum"] = [m for m in data["$defs"]["Translator"].get("enum", []) if m not in remove_models]
            
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

if __name__ == "__main__":
    base = "/home/bimatkeo/Documents/Translator/Bimatkeo_Translator"
    clean_schema(base)
    print("Cleaned YAML configs.")
