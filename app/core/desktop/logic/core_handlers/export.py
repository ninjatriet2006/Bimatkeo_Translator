"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.export
- RESPONSIBILITY: Proxy export operations for various data types.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.export_manager.ExportManager
- IN = OUT: Instantiates ExportManager lazily and forwards export requests.
=============================================================================
"""

class ExportHandlersMixin:
    @property
    def export_manager(self):
        if not hasattr(self, '_export_manager_obj'):
            from app.core.desktop.logic.export_manager import ExportManager
            self._export_manager_obj = ExportManager(self)
        return self._export_manager_obj

    def _export_detector_image(self):
        return self.export_manager.export_detector_image()

    def _export_ocr_data(self):
        return self.export_manager.export_ocr_data()

    def _export_translator_data(self):
        return self.export_manager.export_translator_data()

    def _export_inpainter_image(self):
        return self.export_manager.export_inpainter_image()

    def _export_render_image(self):
        return self.export_manager.export_render_image()
