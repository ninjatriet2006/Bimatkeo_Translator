"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base.env
- RESPONSIBILITY: General purpose environment utility functions for base infrastructure.
- CALLED BY: app.core.base.manager, desktop_ui.config.loader
- CALLS TO: None
- IN = OUT: Pure functions for pathing and execution environments.
=============================================================================
"""
import os
import sys

def get_python_executable(project_base_dir: str) -> str:
    """
    Finds and returns the absolute path to the Python executable in the .venv directory.
    Falls back to the system Python executable if .venv is not found.
    """
    venv_path_win = os.path.join(project_base_dir, '.venv', 'Scripts', 'python.exe')
    venv_path_unix = os.path.join(project_base_dir, '.venv', 'bin', 'python')
    
    if os.path.exists(venv_path_win):
        return venv_path_win
    elif os.path.exists(venv_path_unix):
        return venv_path_unix
        
    return sys.executable
