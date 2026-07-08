"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.translator.verify
- RESPONSIBILITY: Integrity check for local Translator models vs dynamic Factories.
- CALLED BY: Independent scripts or manager.
- CALLS TO: None
- IN = OUT: Evaluates directories, returns validation results/warnings.
=============================================================================
"""

import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class TranslatorVerifier:
    def __init__(self):
        pass

    def run_verification(self, registry_path: str = "", models_base_path: str = "models"):
        print("[TranslatorVerifier] Running integrity check on local Translator models...")
        
        from app.core.factories import TranslatorFactory

        # 1. Collect all declared models
        declared_models = []
        for model in TranslatorFactory.get_all_registered_models():
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
            if not os.path.exists(file_path) and file_path.startswith("models"):
                print(f"     [Not Installed]: '{model['key']}' -> Expected file: {file_path}")
                missing_count += 1
        if missing_count == 0:
            print("     [OK] All declared models are present on disk.")

        # 3. Check for orphaned models in models/Translator
        print("  -> Checking for orphaned models (exist on disk but not declared)...")
        valid_paths = [os.path.normpath(m["check_file"]) for m in declared_models if m["check_file"].startswith("models")]
        orphan_count = 0
        
        def check_orphans(base_dir):
            nonlocal orphan_count
            if not os.path.exists(base_dir):
                return
            for item in os.listdir(base_dir):
                item_path = os.path.normpath(os.path.join(base_dir, item))
                if os.path.isdir(item_path):
                    is_valid = any(vp.startswith(item_path + os.sep) or vp == item_path for vp in valid_paths)
                    if not is_valid:
                        print(f"     [Orphaned Folder]: {item_path} (Can be safely deleted)")
                        orphan_count += 1

        check_orphans(os.path.join(models_base_path, "offline_translator"))
        
        if orphan_count == 0:
            print("     [OK] No orphaned models found.")
            
        print("[TranslatorVerifier] Verification complete.\n")

if __name__ == "__main__":
    verifier = TranslatorVerifier()
    verifier.run_verification()
