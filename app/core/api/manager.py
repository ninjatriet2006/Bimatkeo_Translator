"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.api.manager
- RESPONSIBILITY: Centralized management of AI Translator APIs and models.
- CALLED BY: desktop_ui.main_window.job_runner, desktop_ui.main_window.pool_dialog, desktop_ui.main_window.handlers
- CALLS TO: app.core.api.fetcher, app.core.api.models, app.core.api.verify
- IN = OUT: Coordinator module, exposes fetcher and model utility methods.
=============================================================================
"""
import os
from .verify import APIVerifier
from .fetcher import infer_ai_provider, fetch_remote_ai_models
from .models import is_blacklisted, priority_sort_key

class APIManager:
    """
    Facade for all API related operations.
    """
    def __init__(self, project_base_dir: str = None):
        self.project_base_dir = project_base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.verifier = APIVerifier()

    def run_verification(self):
        registry_path = os.path.join(self.project_base_dir, ".config", "models", "model_registry.yaml")
        schema_path = os.path.join(self.project_base_dir, "default_configs", "configs", "schema_fallback.yaml")
        self.verifier.run_verification(registry_path, schema_path)

# Re-exporting module level functions for compatibility
__all__ = ['infer_ai_provider', 'fetch_remote_ai_models', 'is_blacklisted', 'priority_sort_key', 'APIManager']
