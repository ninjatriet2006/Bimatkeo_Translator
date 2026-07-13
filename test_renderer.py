import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.shared_registry import RendererFactory, discover_plugins
discover_plugins()
print("Registered renderers:", [m['key'] for m in RendererFactory.get_all_registered_models()])
