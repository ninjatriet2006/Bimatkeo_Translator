"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.verify
- RESPONSIBILITY: Integrity check for local OCR models vs Model Registry.
- CALLED BY: app.core.ocr.manager (or independent scripts)
- CALLS TO: None
- IN = OUT: Evaluates directories, returns validation results/warnings.
=============================================================================
"""


import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import os
from ruamel.yaml import YAML

class OCRVerifier:
    def __init__(self):
        pass

    def run_verification(self, registry_path: str = "", models_base_path: str = "models"):
        """
        Cross-checks downloaded local OCR models against the dynamic model factories.
        Reports Not Installed models (in registry but not on disk) 
        and orphaned models (on disk but not in registry).
        """
        print("[OCRVerifier] Running integrity check on local OCR models...")
        
        from app.core.factories import DetectorFactory, RecognizerFactory

        # 1. Collect all declared models
        declared_models = []
        all_models = DetectorFactory.get_all_registered_models() + RecognizerFactory.get_all_registered_models()
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
                print(f"     [Missing]: '{model['key']}' -> Expected file: {file_path}")
                missing_count += 1
        if missing_count == 0:
            print("     [OK] All declared models are present on disk.")

        # 3. Check for orphaned models in models/Detector and models/OCR
        print("  -> Checking for orphaned models (exist on disk but not in registry)...")
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
                    is_valid = any(vp.startswith(item_path + os.sep) for vp in valid_paths)
                    if not is_valid:
                        if item_path not in valid_paths:
                            print(f"     [Orphaned Directory]: '{item_path}' is not associated with any registry model.")
                            orphan_count += 1
                else:
                    pass

        check_orphans(os.path.join(models_base_path, "Detector"))
        check_orphans(os.path.join(models_base_path, "OCR"))
        if orphan_count == 0:
            print("     [OK] No orphaned directories found.")
