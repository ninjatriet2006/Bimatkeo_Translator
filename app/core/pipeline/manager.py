"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.manager
- RESPONSIBILITY: Links Managers, sets up Fork-Join Queue, runs Producer and Consumer.
- CALLED BY: main.py or entrypoint
- CALLS TO: app.core.ocr.initializer, app.core.translator.manager, app.core.inpainter.manager, app.core.renderer.manager
- IN = OUT: Receives system config -> generates Worker Threads -> runs in parallel.
=============================================================================
"""

import os
from app.core.pipeline.config_loader import load_all_configs
from app.core.ocr.initializer import OCRInitializer
from app.core.translator.initializer import TranslatorInitializer
from app.core.inpainter.initializer import InpainterInitializer
from app.core.renderer.initializer import RendererInitializer

class PipelineManager:
    """Quản lý luồng chính của ứng dụng."""
    
    def __init__(self, app, python_executable, temp_dir):
        from .executor import PipelineExecutor
        self.executor = PipelineExecutor(app, python_executable, temp_dir)

    def is_stopped(self):
        return self.executor.is_stopped()

    def stop(self, log_callback):
        """Stops the pipeline simulation."""
        return self.executor.stop(log_callback)

    def _initialize_models(self, config_dict: dict, project_root: str, api_profiles: dict | None = None, log_callback=None):
        """Khởi tạo toàn bộ các module trong Pipeline. (DEPRECATED for multiprocessing)"""
        pass

    def run(self, job, output_path, config_dict, log_callback, is_verbose=False, output_format='png', mtpe_callback=None):
        """Runs the real multi-threaded pipeline."""
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        config_bundle = load_all_configs(project_root, config_dict, log_callback)
        config_dict = config_bundle["config"]
        api_profiles = config_bundle["api_profiles"]
        config_dict["skip_languages"] = config_bundle["skip_languages"]
        config_dict["filter_texts"] = config_bundle["filter_texts"]
        
        # Add api_profiles to config_dict so executor can use them
        config_dict["api_profiles_resolved"] = api_profiles

        # Pass config_dict to executor instead of models_bundle
        return self.executor.run(job, output_path, config_dict, log_callback, is_verbose, output_format, mtpe_callback)

    def run_single_image_test(self, test_image_path, output_path, config_dict, log_callback, is_verbose=False):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        config_bundle = load_all_configs(project_root, config_dict, log_callback)
        config_dict = config_bundle["config"]
        api_profiles = config_bundle["api_profiles"]
        config_dict["skip_languages"] = config_bundle["skip_languages"]
        config_dict["filter_texts"] = config_bundle["filter_texts"]
        
        config_dict["api_profiles_resolved"] = api_profiles

        return self.executor.run_single_image_test(test_image_path, output_path, config_dict, log_callback, is_verbose)
