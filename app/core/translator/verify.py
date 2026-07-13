"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.translator.verify
- RESPONSIBILITY: Integrity check for local Translator models vs dynamic Factories.
- CALLED BY: Independent scripts or manager.
- CALLS TO: app.core.verify_utils
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
        from app.core.shared_registry import TranslatorFactory
        from app.core.shared_registry.verify import run_models_verification
        run_models_verification(
            verifier_name="TranslatorVerifier",
            factories=[TranslatorFactory],
            orphan_check_dirs=["offline_translator"],
            models_base_path=models_base_path
        )

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format='%(message)s')
    verifier = TranslatorVerifier()
    verifier.run_verification()
