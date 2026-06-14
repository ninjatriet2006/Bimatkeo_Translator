import os
import sys
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QColor

sys.path.insert(0, os.path.abspath("."))

app = QApplication.instance() or QApplication(sys.argv)

try:
    from desktop_ui.main_window import TranslatorStudioApp
    window = TranslatorStudioApp()
    window.show()
    
    combo = window.theme_combobox
    
    def inspect_arrow(theme_name):
        window._apply_theme(theme_name)
        app.processEvents()
        
        # Grab combobox image
        img = combo.grab().toImage()
        w, h = img.width(), img.height()
        
        # We look at the rightmost 30 pixels (the arrow button area)
        arrow_area_width = 30
        bg_color = img.pixelColor(10, h // 2)  # Background color on the left of the combo
        
        different_pixels = 0
        for x in range(w - arrow_area_width, w):
            for y in range(h):
                color = img.pixelColor(x, y)
                # Compare color with bg_color
                if abs(color.red() - bg_color.red()) > 10 or \
                   abs(color.green() - bg_color.green()) > 10 or \
                   abs(color.blue() - bg_color.blue()) > 10:
                    different_pixels += 1
                    
        total_pixels = arrow_area_width * h
        percent = (different_pixels / total_pixels) * 100
        print(f"Theme: {theme_name}")
        print(f"  Background color: {bg_color.name()}")
        print(f"  Different pixels in arrow area: {different_pixels} / {total_pixels} ({percent:.1f}%)")
        
    inspect_arrow("Default Qt")
    inspect_arrow("Dracula")
    inspect_arrow("Golden Sands")
    inspect_arrow("Classic Paper")
    
except Exception as e:
    import traceback
    traceback.print_exc()
