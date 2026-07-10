"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.custom_widgets.dynamic_height_list
- RESPONSIBILITY: Provide a list widget that dynamically adjusts its height.
- CALLED BY: UI classes in app.core.desktop
- CALLS TO: PySide6.QtWidgets.QListWidget
- IN = OUT: Instantiates a custom Qt widget.
=============================================================================
"""
from PySide6.QtWidgets import QListWidget
from PySide6.QtCore import Qt, QSize, QEvent

class DynamicHeightListWidget(QListWidget):
    """
    A custom QListWidget that:
    1. Overrides its size hints to always match its content's height.
    2. Disables its own vertical scrollbar, forcing the parent to scroll.
    3. Ignores mouse wheel events to prevent accidental scrolling inside parent.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def minimumSizeHint(self) -> QSize:
        """Override to report the content's height as the minimum possible height."""
        height = self._get_content_height()
        return QSize(super().minimumSizeHint().width(), height)

    def sizeHint(self) -> QSize:
        """Override to report the content's height as the preferred height."""
        height = self._get_content_height()
        return QSize(super().sizeHint().width(), height)

    def wheelEvent(self, event: QEvent):
        """Pass the wheel event to the parent to allow scrolling the main area."""
        event.ignore()

    def _get_content_height(self) -> int:
        """Calculates the total height required to display all items without scrolling."""
        if self.count() == 0:
            return 35  # Return a default small height when empty

        # Sum of the height of each item in the list
        content_height = 0
        for i in range(self.count()):
            content_height += self.sizeHintForRow(i)

        # Add the height of the frame around the content
        content_height += self.frameWidth() * 2

        return content_height
