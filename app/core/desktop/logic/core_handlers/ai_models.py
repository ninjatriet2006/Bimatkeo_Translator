"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.ai_models
- RESPONSIBILITY: Proxy AI model fetching and testing operations.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.ai_models.fetcher, app.core.desktop.logic.ai_models.tester
- IN = OUT: Forwards logic calls to AI models managers.
=============================================================================
"""

class AIModelsHandlersMixin:
    def _fetch_ai_models(self, button):
        from app.core.desktop.logic.ai_models.fetcher import fetch_ai_models
        fetch_ai_models(self, button)

    def _show_fetched_models(self, models, button):
        from app.core.desktop.logic.ai_models.fetcher import show_fetched_models
        show_fetched_models(self, models, button)

    def _select_fetched_model(self, model_name, entry_widget):
        from app.core.desktop.logic.ai_models.fetcher import select_fetched_model
        select_fetched_model(self, model_name, entry_widget)

    def _on_models_fetched(self, models, button):
        self._show_fetched_models(models, button)

    def _test_ai_model(self, button, combo):
        from app.core.desktop.logic.ai_models.tester import test_ai_model
        test_ai_model(self, button, combo)

    def _on_test_finished(self, success, message, button):
        from app.core.desktop.logic.ai_models.tester import on_test_finished
        on_test_finished(self, success, message, button)

    def _on_fetch_finished(self, button):
        from app.core.desktop.logic.ai_models.fetcher import on_fetch_finished
        on_fetch_finished(self, button)
