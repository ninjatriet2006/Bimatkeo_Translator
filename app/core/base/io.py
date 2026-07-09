"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base.io
- RESPONSIBILITY: Responsible for reading and writing YAML files.
- CALLED BY: app.core.base.base_loader, app.core.base.schema_loader
- CALLS TO: ruamel.yaml
- IN = OUT: Handles I/O with YAML files.
=============================================================================
"""
import os
from typing import Any

def save_yaml_file(path: str, data: Any) -> None:
    from ruamel.yaml import YAML
    from ruamel.yaml.error import YAMLError
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.default_flow_style = False  # type: ignore
    try:
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
    except (YAMLError, OSError) as e:
        print(f"[ConfigLoader] Error saving {os.path.basename(path)}: {e}")

def load_yaml_file(path: str) -> dict[str, Any]:
    """Loads a YAML file and returns its content as a dictionary."""
    if os.path.exists(path):
        from ruamel.yaml import YAML
        from ruamel.yaml.error import YAMLError
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False  # type: ignore
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.load(f) or {}
        except (YAMLError, OSError) as e:
            print(f"[ConfigLoader] Error loading YAML file {os.path.basename(path)}: {e}")
    return {}
