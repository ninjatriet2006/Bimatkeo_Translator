"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.verify
- RESPONSIBILITY: Integrity check for local OCR models vs Model Registry.
- CALLED BY: app.core.ocr.manager (or independent scripts)
- CALLS TO: app.core.verify_utils
- IN = OUT: Evaluates directories, returns validation results/warnings.
=============================================================================
"""

import sys, os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class OCRVerifier:
    def __init__(self):
        pass

    def run_verification(self, registry_path: str = "", models_base_path: str = "models"):
        from app.core.factories import DetectorFactory, RecognizerFactory
        from app.core.verify_utils import run_models_verification
        run_models_verification(
            verifier_name="OCRVerifier",
            factories=[DetectorFactory, RecognizerFactory],
            orphan_check_dirs=["Detector", "OCR"],
            models_base_path=models_base_path
        )

if __name__ == "__main__":
    verifier = OCRVerifier()
    verifier.run_verification()
