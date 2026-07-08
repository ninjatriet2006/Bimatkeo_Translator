"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.api.verify
- RESPONSIBILITY: Verify API configuration integrity.
- CALLED BY: app.core.api.manager
- CALLS TO: None
- IN = OUT: Evaluates dictionaries, returns validation results/warnings.
=============================================================================
"""

import os
from ruamel.yaml import YAML

class APIVerifier:
    def __init__(self):
        pass

    def run_verification(self, registry_path: str, schema_path: str):
        """
        Runs basic validation on the model registry and schema configurations.
        """
        print("[APIVerifier] Running integrity check on API module configs...")
        yaml = YAML(typ='safe')
        
        # Verify Model Registry (REMOVED - migrated to dynamic factories)

        # Verify Schema Fallback
        if not os.path.exists(schema_path):
            print(f"  [!] Missing schema fallback at {schema_path}")
        else:
            try:
                with open(schema_path, "r", encoding="utf-8") as f:
                    data = yaml.load(f)
                    if not data or "properties" not in data:
                        print("  [!] schema_fallback.yaml is missing 'properties' root key.")
            except Exception as e:
                print(f"  [!] Failed to parse schema_fallback.yaml: {e}")
