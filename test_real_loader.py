import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.shared_registry.core.loader import RegistryLoader
import pprint

loader = RegistryLoader()
registry = loader.load_registry()
print("Loaded dynamic tabs:")
print(list(registry.keys()))
print("Loaded offline translators:")
print([m['key'] for m in registry.get('offline_translator', {}).values() if isinstance(m, dict) and 'key' in m])
