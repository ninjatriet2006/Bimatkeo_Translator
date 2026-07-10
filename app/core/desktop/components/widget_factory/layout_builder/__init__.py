"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.layout_builder.__init__
- RESPONSIBILITY: Aggregate all UI builder mixins to reconstruct LayoutBuilderFactory.
- CALLED BY: app.core.desktop.components.settings_panel
- CALLS TO: All split builder mixins in this directory.
- IN = OUT: Provides a unified class LayoutBuilderFactory for settings_panel to instantiate.
=============================================================================
"""

from .tabs import TabsBuilderMixin
from .rows import RowsBuilderMixin
from .dynamic_buttons import DynamicButtonsBuilderMixin
from .tooltips import TooltipsBuilderMixin
from .bottom_panel import BottomPanelBuilderMixin
from .extra_widgets import ExtraWidgetsBuilderMixin
from .preview_tester import PreviewTesterBuilderMixin

class LayoutBuilderFactory(
    TabsBuilderMixin,
    RowsBuilderMixin,
    DynamicButtonsBuilderMixin,
    TooltipsBuilderMixin,
    BottomPanelBuilderMixin,
    ExtraWidgetsBuilderMixin,
    PreviewTesterBuilderMixin
):
    """
    Unified LayoutBuilderFactory built from 7 split domain-specific mixins.
    """
    def __init__(self, main_window):
        self.mw = main_window
