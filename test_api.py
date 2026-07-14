import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.shared_registry import TranslatorFactory, discover_plugins
from app.core.translator.base_api import BaseAPITranslator
discover_plugins()
models = TranslatorFactory.get_all_registered_models(BaseAPITranslator)
for m in models:
    print(m['key'])
