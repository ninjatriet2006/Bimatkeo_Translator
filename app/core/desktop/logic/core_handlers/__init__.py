"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.__init__
- RESPONSIBILITY: Aggregate all core handler Mixins into a single HandlersMixin.
- CALLED BY: app.core.desktop.main_window.TranslatorStudioApp
- CALLS TO: All split mixin modules in this directory.
- IN = OUT: Provides a unified facade for PySide6 MainWindow to inherit from.
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

class HandlersMixin(
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
    Unified HandlersMixin built from 13 split domain-specific mixins.
    """
    pass
