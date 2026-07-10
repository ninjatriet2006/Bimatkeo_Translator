"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.ui_visibility
- RESPONSIBILITY: Proxy UI visibility operations.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.ui_visibility.*
- IN = OUT: Forwards logic calls to standalone ui_visibility functions.
=============================================================================
"""

class UIVisibilityHandlersMixin:
    def _get_active_translator_category(self) -> str:
        from app.core.desktop.logic.ui_visibility.translator import get_active_translator_category
        return get_active_translator_category(self)

    def _get_active_translator_name(self) -> str:
        from app.core.desktop.logic.ui_visibility.translator import get_active_translator_name
        return get_active_translator_name(self)

    def _update_translator_visibility(self):
        from app.core.desktop.logic.ui_visibility.translator import update_translator_visibility
        update_translator_visibility(self)

    def _get_active_ocr_category(self) -> str:
        from app.core.desktop.logic.ui_visibility.ocr import get_active_ocr_category
        return get_active_ocr_category(self)

    def _update_ocr_visibility(self):
        from app.core.desktop.logic.ui_visibility.ocr import update_ocr_visibility
        update_ocr_visibility(self)

    def _update_inpainter_visibility(self):
        from app.core.desktop.logic.ui_visibility.inpainter import update_inpainter_visibility
        update_inpainter_visibility(self)

    def _on_ocr_category_changed(self):
        from app.core.desktop.logic.ui_visibility.ocr import on_ocr_category_changed
        on_ocr_category_changed(self)

    def _update_task_translator_visibility(self, context_key: str):
        from app.core.desktop.logic.ui_visibility.translator import update_task_translator_visibility
        update_task_translator_visibility(self, context_key)

    def _on_translator_category_changed(self):
        from app.core.desktop.logic.ui_visibility.translator import on_translator_category_changed
        on_translator_category_changed(self)
