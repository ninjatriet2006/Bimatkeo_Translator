import os
import sys
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath("."))

app = QApplication.instance() or QApplication(sys.argv)

try:
    from desktop_ui.main_window import TranslatorStudioApp
    window = TranslatorStudioApp()
    window.show()
    
    combo = window.theme_combobox
    
    def inspect_arrow_colors(theme_name):
        window._apply_theme(theme_name)
        app.processEvents()
        
        img = combo.grab().toImage()
        w, h = img.width(), img.height()
        
        colors = {}
        for x in range(w - 20, w - 5):
            for y in range(5, h - 5):
                c = img.pixelColor(x, y).name()
                colors[c] = colors.get(c, 0) + 1
                
        print(f"Theme: {theme_name}")
        print("  Distinct colors in arrow area (color: count):")
        for c, count in sorted(colors.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"    {c}: {count}")
            
    inspect_arrow_colors("Default Qt")
    inspect_arrow_colors("Dracula")
    inspect_arrow_colors("Golden Sands")
    inspect_arrow_colors("Classic Paper")
    
except Exception as e:
    import traceback
    traceback.print_exc()
