import os
import re

constants_import = "from desktop_ui.constants import *\n"

replacements = [
    (r'"--- OFFLINE MODELS \(No API Key\) ---"', 'CAT_OFFLINE_MODELS'),
    (r'"--- API-BASED \(Requires Setup\) ---"', 'CAT_API_BASED'),
    (r'"--- OTHER ACTIONS ---"', 'CAT_OTHER_ACTIONS'),
    (r'"📥 Cập nhật danh sách hỗ trợ dịch..."', 'UPDATE_SUPPORTED_LANGS'),
    (r'"📥 Update translation support list..."', 'UPDATE_SUPPORTED_LANGS_EN'),
    (r'"📥 Cập nhật TẤT CẢ mô hình dịch..."', 'UPDATE_ALL_MODELS'),
    (r'"📥 Update ALL translation models..."', 'UPDATE_ALL_MODELS_EN'),
    (r'"📥 Cập nhật phần mềm/mô hình dịch..."', 'UPDATE_SOFTWARE'),
    (r'"📥 Cập nhật danh sách ngôn ngữ..."', 'UPDATE_LANGS_LIST'),
    (r'"🔍 Install New Font..."', 'INSTALL_NEW_FONT'),
    (r'"📥 Update All Fonts..."', 'UPDATE_ALL_FONTS'),
    (r'"https://cdn.jsdelivr.net/npm/google-font-metadata/"', 'FONT_METADATA_URL'),
    (r'"https://fonts.googleapis.com/css\?family="', 'FONT_CSS_URL'),
    (r"'--- OFFLINE MODELS \(No API Key\) ---'", 'CAT_OFFLINE_MODELS'),
    (r"'--- API-BASED \(Requires Setup\) ---'", 'CAT_API_BASED'),
    (r"'--- OTHER ACTIONS ---'", 'CAT_OTHER_ACTIONS'),
    (r"'📥 Cập nhật danh sách hỗ trợ dịch...'", 'UPDATE_SUPPORTED_LANGS'),
    (r"'📥 Update translation support list...'", 'UPDATE_SUPPORTED_LANGS_EN'),
    (r"'📥 Cập nhật TẤT CẢ mô hình dịch...'", 'UPDATE_ALL_MODELS'),
    (r"'📥 Update ALL translation models...'", 'UPDATE_ALL_MODELS_EN'),
    (r"'📥 Cập nhật phần mềm/mô hình dịch...'", 'UPDATE_SOFTWARE'),
    (r"'📥 Cập nhật danh sách ngôn ngữ...'", 'UPDATE_LANGS_LIST'),
    (r"'🔍 Install New Font...'", 'INSTALL_NEW_FONT'),
    (r"'📥 Update All Fonts...'", 'UPDATE_ALL_FONTS'),
    (r"'https://cdn.jsdelivr.net/npm/google-font-metadata/'", 'FONT_METADATA_URL'),
    (r"'https://fonts.googleapis.com/css\?family='", 'FONT_CSS_URL'),
]

files_to_update = [
    "desktop_ui/mainwindow/handlers.py",
    "desktop_ui/mainwindow/widget_builders.py",
    "desktop_ui/config/capabilities.py",
    "desktop_ui/config/registry.py",
    "desktop_ui/config/repair.py",
    "desktop_ui/main_window.py"
]

for filepath in files_to_update:
    if not os.path.exists(filepath):
        print(f"Skipping {filepath}, not found.")
        continue
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content
    
    # Apply replacements
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
        
    if content != original_content:
        # Add import statement after the first set of imports if not already there
        if "from desktop_ui.constants import *" not in content:
            # find first import
            import_idx = content.find("import ")
            if import_idx != -1:
                # Find the end of the imports block (a blank line)
                end_imports = content.find("\n\n", import_idx)
                if end_imports != -1:
                    content = content[:end_imports] + "\n" + constants_import + content[end_imports:]
                else:
                    content = constants_import + content
            else:
                content = constants_import + content
                
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {filepath}")
    else:
        print(f"No changes for {filepath}")

print("Done refactoring constants.")
