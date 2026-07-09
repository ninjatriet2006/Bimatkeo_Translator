"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.shared_context.context_utils
- RESPONSIBILITY: Provide general utility functions acting on PageContext DTO.
- CALLED BY: Various
- CALLS TO: app.core.shared_context.dto
- IN = OUT: Returns boolean state.
=============================================================================
"""
from app.core.shared_context.dto import PageContext

def is_disk_mode(ctx: PageContext) -> bool:
    """Kiểm tra xem context có đang hoạt động ở DISK mode không."""
    return ctx.original_image_path is not None and ctx.original_image is None
