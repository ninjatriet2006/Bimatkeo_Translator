import sys, os, yaml
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.shared_registry import TranslatorFactory, discover_plugins
from app.core.translator.base_offline import BaseOfflineTranslator

discover_plugins()

yaml_path = ".config/models/model_registry.yaml"
with open(yaml_path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f)
    UI_TAB_LAYOUT = data.get("fields", {})

dynamic_models = TranslatorFactory.get_all_registered_models(BaseOfflineTranslator)
tab_name = "General & Translator"
field = "offline_translator"

existing = {m.get("key"): m for m in UI_TAB_LAYOUT[tab_name][field] if isinstance(m, dict) and "key" in m}
for model in dynamic_models:
    key = model.get("key")
    if key and key in existing:
        existing[key].update(model)
    else:
        UI_TAB_LAYOUT[tab_name][field].append(model)

print("Offline translators after merge:", [m.get("key") for m in UI_TAB_LAYOUT[tab_name][field]])
