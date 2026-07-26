"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.config.ui_verify
- RESPONSIBILITY: Dynamically scan the desktop UI source code to extract hardcoded language IDs.
- CALLED BY: app.core.langs.manager
- CALLS TO: None
- IN = OUT: Returns a dictionary of extracted hardcoded UI keys.
=============================================================================
"""
import os
import re

def extract_hardcoded_ui_keys(project_base_dir: str) -> dict:
    """
    Scans the 'app/core/desktop' directory for any usage of hardcoded UI strings.
    This prevents the LanguageVerifier from falsely flagging them as orphans.
    """
    desktop_dir = os.path.join(project_base_dir, "app", "core", "desktop")
    hardcoded_keys = {
        "ui_strings": set(),
        "messages": set(),
        "tasks": set()
    }
    
    # Regex patterns
    # Matches: .setProperty("lang_id", "KEY")
    pattern_prop = re.compile(r'setProperty\s*\(\s*["\']lang_id["\']\s*,\s*["\']([^"\']+)["\']\s*\)')
    # Matches: get_string("KEY")
    pattern_get = re.compile(r'get_string\s*\(\s*["\']([^"\']+)["\']')
    
    for root, _, files in os.walk(desktop_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # Find all matches
                        matches_prop = pattern_prop.findall(content)
                        matches_get = pattern_get.findall(content)
                        
                        for key in set(matches_prop + matches_get):
                            # Skip dynamic/variable keys if they somehow matched (rare but possible)
                            if not key or '{' in key or '%' in key:
                                continue
                                
                            if key.startswith("msg_"):
                                hardcoded_keys["messages"].add(key)
                            elif key.startswith("task_"):
                                hardcoded_keys["tasks"].add(key)
                            elif key.startswith("ui_"):
                                hardcoded_keys["ui_strings"].add(key)
                            else:
                                hardcoded_keys["ui_strings"].add(key)
                except Exception as e:
                    print(f"[ui_verify] Error reading file {file_path}: {e}")
                    
    return hardcoded_keys

if __name__ == "__main__":
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
    keys = extract_hardcoded_ui_keys(project_root)
    print(f"Extracted UI Strings count: {len(keys.get('ui_strings', []))}")
    print(f"Extracted Messages count: {len(keys.get('messages', []))}")
    print(f"Extracted Tasks count: {len(keys.get('tasks', []))}")
    print("UI Verification Script completed successfully.")
