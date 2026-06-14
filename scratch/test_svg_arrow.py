import os
import sys
import base64
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath("."))

app = QApplication.instance() or QApplication(sys.argv)

def get_svg_arrow(color_hex):
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="{color_hex}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"></polyline></svg>'
    encoded = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"url(data:image/svg+xml;base64,{encoded})"

try:
    from desktop_ui.main_window import TranslatorStudioApp
    window = TranslatorStudioApp()
    window.show()
    
    combo = window.theme_combobox
    
    # Let's override _apply_theme to test our new QComboBox stylesheet
    # We will get colors for Golden Sands
    colors = window.available_themes["Golden Sands"]["style"]["colors"]
    bg_main = colors["background_main"]
    txt_main = colors["text_main"]
    border = colors["border"]
    
    arrow_url = get_svg_arrow(txt_main)
    print(f"Generated arrow URL: {arrow_url[:50]}...")
    
    new_style = f"""
        QComboBox {{
            background-color: {bg_main};
            color: {txt_main};
            border: 1px solid {border};
            border-radius: 3px;
            padding: 4px 24px 4px 8px;
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 20px;
            border: none;
        }}
        QComboBox::down-arrow {{
            image: {arrow_url};
            width: 12px;
            height: 12px;
        }}
    """
    
    combo.setStyleSheet(new_style)
    app.processEvents()
    
    # Let's inspect the arrow colors
    img = combo.grab().toImage()
    w, h = img.width(), img.height()
    
    colors_found = {}
    for x in range(w - 20, w - 5):
        for y in range(5, h - 5):
            c = img.pixelColor(x, y).name()
            colors_found[c] = colors_found.get(c, 0) + 1
            
    print("Distinct colors in arrow area after SVG styling:")
    for c, count in sorted(colors_found.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    {c}: {count}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
