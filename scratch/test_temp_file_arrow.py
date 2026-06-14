import os
import sys
from PIL import Image, ImageDraw
from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath("."))

app = QApplication.instance() or QApplication(sys.argv)

def get_temp_png_arrow(color_hex, theme_name):
    # Create temp dir if not exists
    os.makedirs("temp", exist_ok=True)
    img_path = os.path.abspath(f"temp/arrow_{theme_name.replace(' ', '_')}.png")
    
    img = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    hex_str = color_hex.lstrip('#')
    r = int(hex_str[0:2], 16)
    g = int(hex_str[2:4], 16)
    b = int(hex_str[4:6], 16)
    color = (r, g, b, 255)
    
    # Draw a simple V arrow: down-pointing chevron
    # Let's draw it precisely:
    draw.line([(2, 4), (6, 8)], fill=color, width=2)
    draw.line([(6, 8), (10, 4)], fill=color, width=2)
    
    img.save(img_path, format="PNG")
    return img_path

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
    
    arrow_path = get_temp_png_arrow(txt_main, "Dracula")
    print(f"Generated arrow PNG at: {arrow_path}")
    
    # In QSS, backslashes must be forward slashes
    arrow_qss_path = arrow_path.replace("\\", "/")
    
    # Style the combobox
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
            image: url({arrow_qss_path});
            width: 12px;
            height: 12px;
        }}
    """
    
    combo.setStyleSheet(new_style)
    app.processEvents()
    
    # Inspect the arrow colors
    img = combo.grab().toImage()
    w, h = img.width(), img.height()
    
    colors_found = {}
    for x in range(w - 20, w - 5):
        for y in range(5, h - 5):
            c = img.pixelColor(x, y).name()
            colors_found[c] = colors_found.get(c, 0) + 1
            
    print("Distinct colors in arrow area after local file PNG styling:")
    for c, count in sorted(colors_found.items(), key=lambda x: x[1], reverse=True)[:5]:
        print(f"    {c}: {count}")
        
except Exception as e:
    import traceback
    traceback.print_exc()
