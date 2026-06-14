import os
import sys
import base64
import io
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath("."))

app = QApplication.instance() or QApplication(sys.argv)

def get_png_arrow(color_hex):
    img = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    hex_str = color_hex.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    color = (r, g, b, 255)
    
    draw.line([(2, 4), (6, 8)], fill=color, width=2)
    draw.line([(6, 8), (10, 4)], fill=color, width=2)
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"url(data:image/png;base64,{encoded})"

try:
    from desktop_ui.main_window import TranslatorStudioApp
    window = TranslatorStudioApp()
    window.show()
    
    # Let's apply Dracula theme
    window._apply_theme("Dracula")
    app.processEvents()
    
    combo = window.theme_combobox
    colors = window.available_themes["Dracula"]["style"]["colors"]
    bg_main = colors["background_main"]
    txt_main = colors["text_main"]
    border = colors["border"]
    
    arrow_url = get_png_arrow(txt_main)
    print(f"Generated arrow URL: {arrow_url[:50]}...")
    
    # Set the new stylesheet on the main window so it styles all QComboBoxes correctly
    style_sheet = window.styleSheet()
    
    # Replace the QComboBox stylesheet part in the global stylesheet
    # Or just append it since QSS cascading rules will override the previous selectors
    style_sheet += f"""
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
    
    window.setStyleSheet(style_sheet)
    app.processEvents()
    
    # Let's inspect the arrow colors in Dracula now!
    img = combo.grab().toImage()
    w, h = img.width(), img.height()
    
    colors_found = {}
    for x in range(w - 20, w - 5):
        for y in range(5, h - 5):
            c = img.pixelColor(x, y).name()
            colors_found[c] = colors_found.get(c, 0) + 1
            
    print("Distinct colors in arrow area after PNG styling:")
    for c, count in sorted(colors_found.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    {c}: {count}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
