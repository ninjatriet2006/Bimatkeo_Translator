"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base.schema_loader
- RESPONSIBILITY: Loads backend schema from cache or generates new schema via CLI.
- CALLED BY: app.core.base.base_loader
- CALLS TO: app.core.base.io
- IN = OUT: Provides configuration schema dictionary.
=============================================================================
"""
import os
import json
import re
from typing import Any, Optional

from .io import load_yaml_file

def load_backend_schema(cache_path: str, fallback_path: str = "") -> Optional[dict[str, Any]]:
    if cache_path and os.path.exists(cache_path):
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                print("[ConfigLoader] Loading schema from cache...")
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass

    if fallback_path and os.path.exists(fallback_path):
        try:
            return load_yaml_file(fallback_path)
        except Exception:
            pass

    return None

def strip_ansi(text: str) -> str:
    ansi_escape = re.compile(r'\x1B\[[0-9;]*[A-Za-z]')
    return ansi_escape.sub('', text)

def parse_schema_output(stdout: str) -> Optional[dict[str, Any]]:
    """Extracts the JSON portion of the schema output."""
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        cleaned_stdout = strip_ansi(stdout)
        json_start = cleaned_stdout.find('{')
        json_end = cleaned_stdout.rfind('}')
        if json_start == -1 or json_end == -1 or json_end < json_start:
            return None
        try:
            return json.loads(cleaned_stdout[json_start:json_end + 1])
        except json.JSONDecodeError:
            return None
