import sys, os, importlib
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
plugins_dir = os.path.join(project_root, "app", "plugins")
for root, dirs, files in os.walk(plugins_dir):
    for file in files:
        if file.endswith("_impl.py") and not file.startswith("__"):
            rel_path = os.path.relpath(os.path.join(root, file), project_root)
            module_name = rel_path.replace(os.sep, ".")[:-3]
            print("Found module:", module_name)
