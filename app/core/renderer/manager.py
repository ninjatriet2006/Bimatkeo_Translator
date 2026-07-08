"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.renderer.manager
- RESPONSIBILITY: Khởi tạo RendererFactory và tải font chữ dựa trên cấu hình.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.factories (RendererFactory)
- IN = OUT: Nhận config_dict -> trả về instance của Renderer.
=============================================================================
"""

from app.core.factories import RendererFactory

class RendererManager:
    @staticmethod
    def initialize(config_dict: dict, log_callback=None):
        """
        Khởi tạo và trả về renderer dựa trên config.
        """
        enable_renderer = config_dict.get("pipeline", {}).get("enable_renderer", True)
        
        renderer_name = config_dict.get("render", {}).get("renderer", "pillow_renderer")
        renderer = None
        
        try:
            if enable_renderer and renderer_name != "none":
                renderer = RendererFactory.create(renderer_name, log_callback=log_callback)
                if renderer and "font_path" in config_dict:
                    renderer.load_fonts(config_dict["font_path"], **config_dict.get("render", {}))
        except ValueError:
            if log_callback:
                log_callback("WARNING", f"Renderer '{renderer_name}' not found, falling back to None.")
            renderer = None
            
        return renderer
