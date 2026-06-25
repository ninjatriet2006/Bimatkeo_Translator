from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True

with open(".config/models/model_registry.yaml", "r", encoding="utf-8") as f:
    data = yaml.load(f)

for field, entries in data.get("fields", {}).items():
    if not isinstance(entries, list): continue
    for entry in entries:
        if "label" in entry:
            del entry["label"]
        if "capabilities" in entry:
            del entry["capabilities"]
        if "static_models" in entry:
            del entry["static_models"]

with open(".config/models/model_registry.yaml", "w", encoding="utf-8") as f:
    yaml.dump(data, f)
print("Registry cleaned.")
