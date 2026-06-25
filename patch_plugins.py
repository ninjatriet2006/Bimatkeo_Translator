import os
import re
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
registry_path = ".config/models/model_registry.yaml"

with open(registry_path, "r", encoding="utf-8") as f:
    data = yaml.load(f)

label_map = {}
for field, entries in data.get("fields", {}).items():
    if not isinstance(entries, list): continue
    for entry in entries:
        if "key" in entry and "label" in entry:
            label_map[entry["key"]] = entry["label"]

# Special case for M2M100, NLLB, JParaCrawl, Qwen2 which have _big variants
# They are mapped manually since they are handled by fallback in factories.py

plugins_dir = "app/plugins"
for root, _, files in os.walk(plugins_dir):
    for file in files:
        if file.endswith("_impl.py"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            
            keys_registered = re.findall(r'@\w+Factory\.register\("([^"]+)"\)', content)
            
            new_content = content
            for key in keys_registered:
                label = label_map.get(key)
                if not label:
                    continue
                
                class_pattern = rf'(@\w+Factory\.register\("{key}"\)\s*class\s+\w+\([^)]+\):)'
                
                replacement = rf'\1\n    DISPLAY_NAME = "{label}"'
                new_content = re.sub(class_pattern, replacement, new_content)
                
            if "felo_impl.py" in file and "STATIC_MODELS" not in new_content:
                new_content = re.sub(r'(class FeloTranslator.*?:)', r'\1\n    STATIC_MODELS = ["felo-search"]', new_content)

            if new_content != content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Patched {path}")
