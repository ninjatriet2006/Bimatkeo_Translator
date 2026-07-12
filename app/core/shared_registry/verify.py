"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_registry.verify
- RESPONSIBILITY: Provides common integrity check logic for models against the registry (missing, orphaned).
- CALLED BY: app.core.diffusion.verify, app.core.inpainter.verify, app.core.ocr.verify, app.core.translator.verify, app.core.renderer.verify
- CALLS TO: None
- IN = OUT: run_models_verification receives Factories -> logs results to system logger.
=============================================================================
"""

import os
from typing import List, Any
import logging

logger = logging.getLogger(__name__)

def run_models_verification(verifier_name: str, factories: List[Any], orphan_check_dirs: List[str] | None = None, models_base_path: str = "models"):
    """
    Cross-checks downloaded local models against the dynamic model factories.
    Reports Not Installed models (in registry but not on disk) 
    and orphaned models (on disk but not in registry).
    """
    logger.info(f"[{verifier_name}] Running integrity check on local models...")

    # 1. Collect all declared models
    declared_models = []
    all_models = []
    for factory in factories:
        all_models.extend(factory.get_all_registered_models())
        
    for model in all_models:
        check_file = model.get("check_file")
        if check_file and check_file != "none":
            declared_models.append({
                "key": model.get("key"),
                "check_file": check_file
            })

    # 2. Check for missing models
    logger.info("  -> Checking for missing models (declared in registry but missing on disk)...")
    missing_count = 0
    for model in declared_models:
        file_path = os.path.normpath(model["check_file"])
        if not os.path.exists(file_path) and file_path.startswith("models"):
            logger.warning(f"     [Missing]: '{model['key']}' -> Expected file: {file_path}")
            missing_count += 1
    if missing_count == 0:
        logger.info("     [OK] All declared models are present on disk.")

    # 3. Check for orphaned models
    if orphan_check_dirs:
        logger.info("  -> Checking for orphaned models (exist on disk but not in registry)...")
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
                            logger.warning(f"     [Orphaned Directory]: '{item_path}' is not associated with any registry model.")
                            orphan_count += 1

        for check_dir in orphan_check_dirs:
            check_orphans(os.path.join(models_base_path, check_dir))
            
        if orphan_count == 0:
            logger.info("     [OK] No orphaned directories found.")
