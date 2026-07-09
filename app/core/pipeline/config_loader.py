"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.config_loader
- RESPONSIBILITY: Loads pipeline-specific configurations.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: None
- IN = OUT: Parses pipeline yaml to settings dictionary.
=============================================================================
"""
import os
import yaml

class PipelineConfigLoader:
    @staticmethod
    def load_all_configs(project_root: str, base_config: dict, log_callback=None) -> dict:
        """
        Tải các cấu hình bổ sung từ YAML và gộp vào base_config.
        Trả về dictionary chứa: skip_languages, filter_texts, api_profiles, và base_config đã cập nhật.
        """
        # Load Ignored.yaml
        ignored_yaml_path = os.path.join(project_root, ".config", "configs", "Ignored.yaml")
        skip_languages = {}
        filter_texts = []
        if os.path.exists(ignored_yaml_path):
            try:
                with open(ignored_yaml_path, 'r', encoding='utf-8') as f:
                    ignored_data = yaml.safe_load(f) or {}
                skip_languages = ignored_data.get("skip_languages", {})
                filter_texts = ignored_data.get("filter_texts", [])
            except Exception as e:
                if log_callback:
                    log_callback("ERROR", f"Failed to load Ignored.yaml: {e}")

        # Load API profiles for chain
        api_profiles_path = os.path.join(project_root, ".config", "configs", "api_profiles.yaml")
        api_profiles = {}
        if os.path.exists(api_profiles_path):
            try:
                with open(api_profiles_path, 'r', encoding='utf-8') as f:
                    api_profiles = yaml.safe_load(f) or {}
            except Exception:
                pass

        # Pipeline default values
        pipeline_config = base_config.get("pipeline", {})
        enable_ocr = pipeline_config.get("enable_ocr", True)
        enable_translator = pipeline_config.get("enable_translator", True)
        enable_inpainter = pipeline_config.get("enable_inpainter", True)
        enable_renderer = pipeline_config.get("enable_renderer", True)

        # Load Debug overrides
        debug_file = os.path.join(project_root, ".config", "configs", "debug_pipeline.yaml")
        if os.path.exists(debug_file):
            try:
                with open(debug_file, "r", encoding="utf-8") as f:
                    debug_cfg = yaml.safe_load(f) or {}
                
                enable_ocr = debug_cfg.get("enable_ocr", enable_ocr)
                enable_translator = debug_cfg.get("enable_translator", enable_translator)
                enable_inpainter = debug_cfg.get("enable_inpainter", enable_inpainter)
                enable_renderer = debug_cfg.get("enable_renderer", enable_renderer)
                if log_callback:
                    log_callback("PIPELINE", "Loaded hidden overrides from debug_pipeline.yaml")
            except Exception as e:
                if log_callback:
                    log_callback("WARNING", f"Error reading debug_pipeline.yaml: {e}")

        # Override by Job Type
        is_text_only = base_config.get('job_type') == 'TX'
        if is_text_only:
            enable_ocr = False
            enable_inpainter = False
            enable_renderer = False
            
        # Update pipeline dict
        base_config["pipeline"] = {
            "enable_ocr": enable_ocr,
            "enable_translator": enable_translator,
            "enable_inpainter": enable_inpainter,
            "enable_renderer": enable_renderer
        }
        
        return {
            "skip_languages": skip_languages,
            "filter_texts": filter_texts,
            "api_profiles": api_profiles,
            "config": base_config
        }
