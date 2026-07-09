"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.hardware_utils
- RESPONSIBILITY: Utility functions for hardware detection and resource limits.
- CALLED BY: app.core.config_loader, desktop_ui.config.loader
- CALLS TO: None
- IN = OUT: Returns values used to tune memory usage based on hardware.
=============================================================================
"""
import os

def get_recommended_size() -> int:
    """
    Tính toán và trả về độ phân giải (Size) đề xuất dựa trên phần cứng hiện hành.
    Ưu tiên đo VRAM (Card đồ họa). Nếu không có GPU, đo System RAM.
    """
    vram_gb = 0.0
    try:
        import torch
        if torch.cuda.is_available():
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        # TODO: có thể bổ sung get VRAM cho XPU, MPS nếu cần.
    except Exception:
        pass

    if vram_gb > 0:
        if vram_gb >= 11.5:
            return 3072 # 12GB+ GPUs
        elif vram_gb >= 7.5:
            return 2048 # 8GB GPUs
        elif vram_gb >= 5.5:
            return 1536 # 6GB GPUs
        elif vram_gb >= 3.5:
            return 1024 # 4GB GPUs
        else:
            return 512  # < 4GB GPUs
    
    # Fallback to System RAM
    try:
        import psutil
        ram_gb = psutil.virtual_memory().total / (1024**3)
        if ram_gb > 15.5:
            return 1536
        elif ram_gb > 7.5:
            return 1024
        else:
            return 512
    except Exception:
        return 1024
