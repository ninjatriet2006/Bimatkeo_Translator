"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.__init__
- RESPONSIBILITY: Provide HandlersController composite handler class for composition inside TranslatorStudioApp.
- CALLED BY: app.core.desktop.main_window.TranslatorStudioApp
- CALLS TO: All split mixin modules in this directory.
- IN = OUT: Instantiated via composition inside TranslatorStudioApp instead of multiple inheritance.
=============================================================================
"""

from .api_profile import ApiProfileHandlersMixin
from .ui_visibility import UIVisibilityHandlersMixin
from .config_io import ConfigIOHandlersMixin
from .fonts import FontHandlersMixin
from .models_updater import ModelsUpdaterHandlersMixin
from .config_sync import ConfigSyncHandlersMixin
from .dynamic_buttons import DynamicButtonsHandlersMixin
from .settings_sync import SettingsSyncHandlersMixin
from .ui_dropdowns import UIDropdownsHandlersMixin
from .job_queue import JobQueueHandlersMixin
from .export import ExportHandlersMixin
from .themes import ThemeHandlersMixin

class HandlersController(
    ApiProfileHandlersMixin,
    UIVisibilityHandlersMixin,
    ConfigIOHandlersMixin,
    FontHandlersMixin,
    ModelsUpdaterHandlersMixin,
    ConfigSyncHandlersMixin,
    DynamicButtonsHandlersMixin,
    SettingsSyncHandlersMixin,
    UIDropdownsHandlersMixin,
    JobQueueHandlersMixin,
    ExportHandlersMixin,
    ThemeHandlersMixin
):
    """
    Unified HandlersController built from domain-specific handler mixins for explicit composition.
    """
    def __init__(self, app=None):
        self.app = app

    def __getattr__(self, name):
        app = self.__dict__.get('app')
        if app is not None:
            for cls in type(app).__mro__:
                if name in cls.__dict__:
                    return getattr(app, name)
            if name in app.__dict__:
                return app.__dict__[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")



# Backward compatibility facade alias
HandlersMixin = HandlersController

