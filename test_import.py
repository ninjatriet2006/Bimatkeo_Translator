import sys, os, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.shared_registry import TranslatorFactory
try:
    importlib.import_module("app.plugins.translator.m2m100.main_impl")
    print("Import successful!")
except Exception as e:
    print("Error:", e)
from app.core.translator.base_offline import BaseOfflineTranslator
models = TranslatorFactory.get_all_registered_models(BaseOfflineTranslator)
print("Registered offline models:", [m['key'] for m in models])
