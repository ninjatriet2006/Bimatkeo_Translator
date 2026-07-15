"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.discovery
- RESPONSIBILITY: Dynamic plugin discovery and importing.
- CALLED BY: app.core.shared_registry.__init__
- CALLS TO: None
- IN = OUT: Scans app/plugins and imports implementations.
=============================================================================
"""
import os
import sys
import importlib

def discover_plugins():
    """Tự động tìm và import tất cả các plugins trong thư mục app/plugins để đăng ký vào Factory."""
    # Move up 4 directories from app/core/shared_registry/discovery.py to project root
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    plugins_dir = os.path.join(project_root, "app", "plugins")
    if not os.path.exists(plugins_dir):
        return
        
    target_dirs = os.environ.get("TARGET_PLUGIN_DIRS")
    if target_dirs:
        target_dirs = [d.strip() for d in target_dirs.split(",")]
        
    for root, dirs, files in os.walk(plugins_dir):
        if target_dirs and root == plugins_dir:
            dirs[:] = [d for d in dirs if d in target_dirs]
            
        for file in files:
            if file.endswith("_impl.py") and not file.startswith("__"):
                rel_path = os.path.relpath(os.path.join(root, file), project_root)
                module_name = rel_path.replace(os.sep, ".")[:-3]
                try:
                    if module_name not in sys.modules:
                        importlib.import_module(module_name)
                except Exception as e:
                    print(f"[SharedRegistry] Failed to auto-discover plugin {module_name}: {e}")
