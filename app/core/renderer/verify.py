"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.renderer.verify
- RESPONSIBILITY: Integrity check for local Renderer fonts/models vs dynamic Factories.
- CALLED BY: Independent scripts or manager.
- CALLS TO: None
- IN = OUT: Evaluates directories, returns validation results/warnings.
=============================================================================
"""

import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class RendererVerifier:
    def __init__(self):
        pass

    def run_verification(self, registry_path: str = "", models_base_path: str = "models"):
        print("[RendererVerifier] Running integrity check on local Renderer assets...")
        
        from app.core.factories import RendererFactory

        # 1. Collect all declared models
        declared_models = []
        for model in RendererFactory.get_all_registered_models():
            check_file = model.get("check_file")
            if check_file and check_file != "none":
                declared_models.append({
                    "key": model.get("key"),
                    "check_file": check_file
                })

        # 2. Check for missing models
        print("  -> Checking for missing models (declared in registry but missing on disk)...")
        missing_count = 0
        for model in declared_models:
            file_path = os.path.normpath(model["check_file"])
            if not os.path.exists(file_path):
                print(f"     [Not Installed]: '{model['key']}' -> Expected file: {file_path}")
                missing_count += 1
        if missing_count == 0:
            print("     [OK] All declared models/fonts are present on disk.")

        print("[RendererVerifier] Verification complete.\n")

if __name__ == "__main__":
    verifier = RendererVerifier()
    verifier.run_verification()
