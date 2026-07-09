"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared.context_utils
- RESPONSIBILITY: Lightweight utility functions for evaluating PageContext state.
- CALLED BY: Various
- CALLS TO: app.core.shared.dto
- IN = OUT: Returns boolean state.
=============================================================================
"""
from app.core.shared.dto import PageContext

def is_disk_mode(ctx: PageContext) -> bool:
    """Kiểm tra xem context có đang hoạt động ở DISK mode không."""
    return ctx.original_image_path is not None and ctx.original_image is None
