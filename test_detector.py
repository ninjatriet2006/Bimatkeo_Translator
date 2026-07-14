import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.core.shared_registry import DetectorFactory, discover_plugins
discover_plugins()
models = DetectorFactory.get_all_registered_models()
for m in models:
    print(m['key'], m.get('check_file', 'NO_CHECK_FILE'))
