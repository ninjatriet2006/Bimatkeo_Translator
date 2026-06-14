import os
import sys
from PySide6.QtWidgets import QApplication, QComboBox
from PySide6.QtCore import QPoint

sys.path.insert(0, os.path.abspath("."))

app = QApplication.instance() or QApplication(sys.argv)

try:
    from desktop_ui.main_window import TranslatorStudioApp
    window = TranslatorStudioApp()
    window.show()
    
    # We want to inspect the theme combobox
    combo = window.theme_combobox
    
    def inspect_combo(theme_name):
        window._apply_theme(theme_name)
        app.processEvents()
        
        # Get geometry relative to main window
        geom = combo.geometry()
        pos = combo.mapToParent(QPoint(0, 0))
        
        # Grab combobox screenshot
        combo_img = combo.grab()
        
        # Get some pixels from the combobox
        # center of the combobox
        w, h = combo_img.width(), combo_img.height()
        bg_pixel = combo_img.toImage().pixelColor(w // 4, h // 2)
        arrow_pixel = combo_img.toImage().pixelColor(w - 10, h // 2)
        
        print(f"Theme: {theme_name}")
        print(f"  Combobox size: {w}x{h}")
        print(f"  Theme Main BG: {window.theme_colors.get('background_main')}")
        print(f"  Theme Frame BG: {window.theme_colors.get('background_frame')}")
        print(f"  Theme Border: {window.theme_colors.get('border')}")
        print(f"  Combobox BG Pixel: {bg_pixel.name()}")
        print(f"  Combobox Arrow area Pixel: {arrow_pixel.name()}")
        
    inspect_combo("Default Qt")
    inspect_combo("Dracula")
    inspect_combo("Golden Sands")
    inspect_combo("Classic Paper")
    
except Exception as e:
    import traceback
    traceback.print_exc()
