"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.diffusion.verify
- RESPONSIBILITY: Integrity check for local Diffusion models vs dynamic Factories.
- CALLED BY: Independent scripts or manager.
- CALLS TO: None
- IN = OUT: Evaluates directories, returns validation results/warnings.
=============================================================================
"""

import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class DiffusionVerifier:
    def __init__(self):
        pass

    def run_verification(self, registry_path: str = "", models_base_path: str = "models"):
        """
        Cross-checks downloaded local Diffusion models against the dynamic model factories.
        Reports Not Installed models (declared but missing on disk) 
        and orphaned models (on disk but not declared).
        """
        print("[DiffusionVerifier] Running integrity check on local Diffusion models...")
        
        from app.core.factories import DiffusionMainModelFactory, DiffusionBaseModelFactory

        # 1. Collect all declared models
        declared_models = []
        all_models = DiffusionMainModelFactory.get_all_registered_models() + DiffusionBaseModelFactory.get_all_registered_models()
        for model in all_models:
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

        # 3. Check for orphaned models in models/Diffusion
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
                    # Check if any valid_path starts with this item_path
                    is_valid = any(vp.startswith(item_path + os.sep) or vp == item_path for vp in valid_paths)
                    if not is_valid:
                        # Orphan directory found
                        print(f"     [Orphaned Folder]: {item_path} (Can be safely deleted)")
                        orphan_count += 1

        check_orphans(os.path.join(models_base_path, "Diffusion", "Main_Models"))
        check_orphans(os.path.join(models_base_path, "Diffusion", "Base_Models"))
        
        if orphan_count == 0:
            print("     [OK] No orphaned models found.")
            
        print("[DiffusionVerifier] Verification complete.\n")


if __name__ == "__main__":
    verifier = DiffusionVerifier()
    verifier.run_verification()
