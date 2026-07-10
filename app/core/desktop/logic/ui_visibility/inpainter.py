"""
[INTEGRITY NOTES]
Purpose: Handle UI visibility toggles for Inpainter settings.
Responsibilities:
- Toggle visibility of SD Base Model depending on the selected Inpainter.
"""
def update_inpainter_visibility(main_window):
    from app.core.shared_registry import InpainterFactory, DiffusionMainModelFactory
    from PySide6.QtCore import QTimer
    
    enable_advanced_diffusion = main_window._get_value_from_widget('enable_advanced_diffusion', main_window.setting_widgets.get('enable_advanced_diffusion'))
    
    if 'inpainter' in main_window.setting_rows:
        QTimer.singleShot(50, lambda v=not enable_advanced_diffusion: main_window.setting_rows['inpainter'].setVisible(v))
    if 'diffusion_model' in main_window.setting_rows:
        QTimer.singleShot(50, lambda v=enable_advanced_diffusion: main_window.setting_rows['diffusion_model'].setVisible(v))
        
    show_sd_base = False
    
    if enable_advanced_diffusion:
        diffusion_model = main_window._get_value_from_widget('diffusion_model', main_window.setting_widgets.get('diffusion_model'))
        if diffusion_model:
            impl_class = DiffusionMainModelFactory.get_class(diffusion_model)
            if impl_class:
                if getattr(impl_class, 'REQUIRES_SD_BASE_MODEL', False):
                    show_sd_base = True
            else:
                if 'powerpaint' in str(diffusion_model).lower():
                    show_sd_base = True
    else:
        inpainter = main_window._get_value_from_widget('inpainter', main_window.setting_widgets.get('inpainter'))
        if inpainter:
            impl_class = InpainterFactory.get_class(inpainter)
            if impl_class:
                if getattr(impl_class, 'REQUIRES_SD_BASE_MODEL', False):
                    show_sd_base = True
            else:
                if 'powerpaint' in str(inpainter).lower():
                    show_sd_base = True
    
    if 'sd_base_model' in main_window.setting_rows:
        widget = main_window.setting_rows['sd_base_model']
        QTimer.singleShot(50, lambda v=show_sd_base: widget.setVisible(v))
