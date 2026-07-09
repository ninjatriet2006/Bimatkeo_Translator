"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.utils
- RESPONSIBILITY: General purpose utility functions for core components.
- CALLED BY: Various
- CALLS TO: None
- IN = OUT: Pure functions, primarily for pathing and simple transforms.
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
