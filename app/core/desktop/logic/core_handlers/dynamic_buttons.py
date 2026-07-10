"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.dynamic_buttons
- RESPONSIBILITY: Proxy routing for dynamic UI buttons.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.dynamic_buttons.router.DynamicButtonRouter
- IN = OUT: Instantiates DynamicButtonRouter lazily and routes button clicks.
=============================================================================
"""

class DynamicButtonsHandlersMixin:
    @property
    def dynamic_button_router(self):
        if not hasattr(self, '_dynamic_button_router_obj'):
            from app.core.desktop.logic.dynamic_buttons.router import DynamicButtonRouter
            self._dynamic_button_router_obj = DynamicButtonRouter(
                self, 
                self.font_ui_manager, 
                self.model_software_updater, 
                self.config_sync_manager
            )
        return self._dynamic_button_router_obj

    def _update_dynamic_btns(self, key: str):
        return self.dynamic_button_router.update_dynamic_btns(key)

    def _on_dynamic_btn_clicked(self, key: str, action: str):
        return self.dynamic_button_router.on_dynamic_btn_clicked(key, action)
