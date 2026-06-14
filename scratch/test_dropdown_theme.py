import os
import sys
import time
from PySide6.QtWidgets import QApplication, QComboBox
from PySide6.QtCore import QTimer, Qt, QPoint

# Add workspace path to sys.path
sys.path.insert(0, os.path.abspath("."))

app = QApplication.instance() or QApplication(sys.argv)

try:
    from desktop_ui.main_window import TranslatorStudioApp
    window = TranslatorStudioApp()
    window.show()
    
    # Let's ensure directories exist
    os.makedirs("scratch/screenshots", exist_ok=True)
    
    # Find the output format combobox (it was changed to dropdown optionmenu)
    # or the theme combobox
    theme_combo = window.theme_combobox
    
    def test_theme(theme_name):
        print(f"Testing theme: {theme_name}")
        # Apply the theme
        window._apply_theme(theme_name)
        theme_combo.setCurrentText(theme_name)
        
        # Process events
        app.processEvents()
        
        # Save screenshot of main window
        window.grab().save(f"scratch/screenshots/main_window_{theme_name.replace(' ', '_')}.png")
        
        # Open the theme combobox popup
        theme_combo.showPopup()
        app.processEvents()
        time.sleep(0.5)  # Let it render
        
        # Grab screenshot of the popup widget if it exists
        if theme_combo.popup_widget:
            popup = theme_combo.popup_widget
            popup.grab().save(f"scratch/screenshots/popup_{theme_name.replace(' ', '_')}.png")
            print(f"Saved popup screenshot for theme: {theme_name}")
            popup.close()
            app.processEvents()
            
    # Test a few themes
    test_theme("Default Qt")
    test_theme("Dracula")
    test_theme("Golden Sands")
    test_theme("Classic Paper")
    
    print("Test completed successfully!")
except Exception as e:
    import traceback
    traceback.print_exc()
    sys.exit(1)
