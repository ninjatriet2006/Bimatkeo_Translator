"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.models_updater
- RESPONSIBILITY: Proxy software updates for AI models.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.models.updater.ModelSoftwareUpdater
- IN = OUT: Instantiates ModelSoftwareUpdater lazily and routes update actions.
=============================================================================
"""

class ModelsUpdaterHandlersMixin:
    @property
    def model_software_updater(self):
        if not hasattr(self, '_model_software_updater_obj'):
            from app.core.desktop.logic.models.updater import ModelSoftwareUpdater
            self._model_software_updater_obj = ModelSoftwareUpdater(self)
        return self._model_software_updater_obj

    def _delete_model_software(self, key: str, model_name: str):
        return self.model_software_updater.delete_model_software(key, model_name)

    def _trigger_all_models_software_update(self, key: str):
        return self.model_software_updater.trigger_all_models_software_update(key)

    def _trigger_model_software_update(self, key: str):
        return self.model_software_updater.trigger_model_software_update(key)
