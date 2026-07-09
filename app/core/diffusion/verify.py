"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.diffusion.verify
- RESPONSIBILITY: Integrity check for local Diffusion models vs dynamic Factories.
- CALLED BY: Independent scripts or manager.
- CALLS TO: app.core.verify_utils
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
        from app.core.shared_registry import DiffusionMainModelFactory, DiffusionBaseModelFactory
        from app.core.verify_utils import run_models_verification
        run_models_verification(
            verifier_name="DiffusionVerifier",
            factories=[DiffusionMainModelFactory, DiffusionBaseModelFactory],
            orphan_check_dirs=[os.path.join("Diffusion", "Main_Models"), os.path.join("Diffusion", "Base_Models")],
            models_base_path=models_base_path
        )

if __name__ == "__main__":
    verifier = DiffusionVerifier()
    verifier.run_verification()
