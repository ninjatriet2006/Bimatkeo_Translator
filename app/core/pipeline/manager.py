"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.manager
- RESPONSIBILITY: Liên kết các Manager, thiết lập Fork-Join Queue, chạy Producer và Consumer.
- CALLED BY: main.py hoặc entrypoint
- CALLS TO: app.core.ocr.initializer, app.core.translator.manager, app.core.inpainter.manager, app.core.renderer.manager
- IN = OUT: Nhận cấu hình hệ thống -> sinh ra các Worker Threads -> chạy song song.
=============================================================================
"""

import os
import queue
import threading

from app.core.pipeline.config_loader import PipelineConfigLoader
from app.core.pipeline.io_manager import PipelineIOManager

from app.core.ocr.initializer import OCRInitializer
from app.core.ocr.ocr import OCRWorker

from app.core.translator.manager import TranslatorManager
from app.core.translator.translate import TranslateWorker
from app.core.translator.edit import EditWorker

from app.core.inpainter.manager import InpainterManager
from app.core.inpainter.inpaint import InpaintWorker
from app.core.inpainter.upscale import UpscalerWorker

from app.core.renderer.manager import RendererManager
from app.core.renderer.render import RenderWorker

class Pipeline:
    """Handles the execution of the backend translation process via Fork-Join Queue Architecture."""

    def __init__(self, app, python_executable, temp_dir):
        self.app = app
        self.python_executable = python_executable
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self.process = None
        self._stopped_by_user = False

    def is_stopped(self):
        return self._stopped_by_user

    def stop(self, log_callback):
        """Stops the pipeline simulation."""
        self._stopped_by_user = True
        if log_callback:
            log_callback("PIPELINE", "Pipeline stopped by user.")
        return True

    def run(self, job, output_path, config_dict, log_callback, is_verbose=False, output_format='png', mtpe_callback=None):
        """Runs the real multi-threaded pipeline."""
        source_path = job['source_path']
        log_callback("PIPELINE", f"Starting Modular Pipeline for job '{os.path.basename(source_path)}'.")
        self._stopped_by_user = False

        if os.path.isfile(source_path):
            source_dir = os.path.dirname(source_path)
            all_files = [os.path.basename(source_path)]
        else:
            source_dir = source_path
            is_single_file = config_dict.get('is_single_file', False)
            all_files = sorted([
                f for f in os.listdir(source_path) 
                if is_single_file or f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.txt'))
            ])

        if not all_files:
            log_callback("WARNING", "No files found in the source directory.")
            return True

        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 1. Load Configurations
        config_bundle = PipelineConfigLoader.load_all_configs(project_root, config_dict, log_callback)
        config_dict = config_bundle["config"]
        skip_languages = config_bundle["skip_languages"]
        filter_texts = config_bundle["filter_texts"]
        api_profiles = config_bundle["api_profiles"]

        target_lang = config_dict.get("translator", {}).get("target_lang", "VIN")

        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Initialize Queues for Fork-Join
            q_in = queue.Queue()
            q_trans = queue.Queue()
            q_edit = queue.Queue()
            q_inpaint = queue.Queue()
            q_upscale = queue.Queue()
            q_render = queue.Queue()
            q_out = queue.Queue()

            # 2. Initialize Models via Domain Managers
            cloud_ocr, detector, recognizer = OCRInitializer.initialize(config_dict, log_callback)
            translator, editor_translator = TranslatorManager.initialize(config_dict, project_root, log_callback)
            inpainter, upscaler, enable_upscaler, upscale_ratio = InpainterManager.initialize(config_dict, log_callback)
            renderer = RendererManager.initialize(config_dict, log_callback)

            # 3. Create Workers
            ocr_worker = OCRWorker(
                in_q=q_in, out_q_trans=q_trans, out_q_inpaint=q_inpaint, out_q_render=q_render,
                detector=detector, recognizer=recognizer, log_callback=log_callback,
                cloud_ocr=cloud_ocr, ocr_config=config_dict.get("ocr", {}), render_config=config_dict.get("render", {})
            )
            
            # Xử lý Translator Chain
            enable_translator = config_dict.get("pipeline", {}).get("enable_translator", True)
            enable_translator_chain = config_dict.get("translator", {}).get("enable_translator_chain", False)
            translator_chain_str = config_dict.get("translator", {}).get("translator_chain", "")
            chained_translators = []
            
            if enable_translator and enable_translator_chain and translator_chain_str:
                steps = [s for s in translator_chain_str.split(';') if s]
                for step in steps:
                    if ':' in step:
                        t_name, t_lang = step.split(':', 1)
                        # Rút gọn logic chain ở đây, gọi lại TranslatorFactory tương tự bản gốc.
                        from app.core.factories import TranslatorFactory
                        step_translator = None
                        if t_name in api_profiles:
                            prof = api_profiles[t_name]
                            provider_name = prof.get('provider', 'openai')
                            try:
                                step_translator = TranslatorFactory.create(provider_name)
                                step_translator.log_callback = log_callback
                                step_translator.load_weights({
                                    "endpoint": prof.get('endpoint'),
                                    "model": prof.get('model'),
                                    "key": prof.get('key'),
                                    "max_retries": prof.get('max_retries', 3),
                                    "system_prompt_profile": config_dict.get("translator", {}).get("system_prompt_profile", "None"),
                                    "project_base_dir": project_root
                                })
                            except Exception as e:
                                log_callback("ERROR", f"Failed to load chain translator '{t_name}': {e}")
                        else:
                            try:
                                step_translator = TranslatorFactory.create(t_name)
                                step_translator.log_callback = log_callback
                                step_translator.load_weights({
                                    "system_prompt_profile": config_dict.get("translator", {}).get("system_prompt_profile", "None"),
                                    "project_base_dir": project_root
                                })
                            except Exception as e:
                                log_callback("ERROR", f"Failed to load chain translator '{t_name}': {e}")
                        
                        if step_translator:
                            chained_translators.append((step_translator, t_lang))
            elif enable_translator and translator:
                chained_translators.append((translator, target_lang))
            
            trans_worker = TranslateWorker(
                in_q=q_trans,
                out_q=q_edit if editor_translator else None,
                translator_or_chain=chained_translators, 
                src_lang=config_dict.get("translator", {}).get("source_lang", "JPN"), 
                tgt_lang=target_lang,
                log_callback=log_callback,
                skip_languages=skip_languages,
                filter_texts=filter_texts,
                no_text_lang_skip=config_dict.get("translator", {}).get("no_text_lang_skip", False),
                max_request_length=int(config_dict.get("translator", {}).get("max_request_length", 2000)),
                context_window=int(config_dict.get("translator", {}).get("context_window", 10)),
                stride_window=int(config_dict.get("translator", {}).get("stride_window", 5))
            )
            
            edit_worker = EditWorker(
                in_q=q_edit,
                editor_translator=editor_translator,
                log_callback=log_callback,
                max_request_length=int(config_dict.get("translator", {}).get("max_request_length", 2000)),
                context_window=int(config_dict.get("translator", {}).get("context_window", 10)),
                stride_window=int(config_dict.get("translator", {}).get("stride_window", 5))
            ) if editor_translator else None
            
            inpaint_worker = InpaintWorker(q_inpaint, inpainter, log_callback, out_q=q_upscale if enable_upscaler else None)
            upscale_worker = UpscalerWorker(q_upscale, upscaler, upscale_ratio, log_callback) if enable_upscaler else None
            render_worker = RenderWorker(q_render, q_out, renderer, log_callback)

            # Start Workers
            workers: list[threading.Thread] = [ocr_worker, trans_worker, inpaint_worker, render_worker]
            if edit_worker:
                workers.append(edit_worker)
            if upscale_worker:
                workers.append(upscale_worker)
            for w in workers:
                w.start()

            # 4. Produce Input
            PipelineIOManager.produce(
                all_files=all_files,
                source_dir=source_dir,
                output_path=output_path,
                config_dict=config_dict,
                log_callback=log_callback,
                q_in=q_in,
                stop_check_callback=self.is_stopped
            )

            # 5. Consume Output
            PipelineIOManager.consume(
                output_path=output_path,
                config_dict=config_dict,
                log_callback=log_callback,
                q_out=q_out
            )

            # Wait for all queues to empty
            join_workers = [ocr_worker, trans_worker, inpaint_worker, render_worker]
            if edit_worker:
                join_workers.append(edit_worker)
            if upscale_worker:
                join_workers.append(upscale_worker)
            for w in join_workers:
                w.join()

            if self._stopped_by_user:
                log_callback("WARNING", "Pipeline run stopped by user.")
                return False

            log_callback("PIPELINE", f"Job '{os.path.basename(source_path)}' completed successfully.")
            return True
            
        except Exception as e:
            log_callback("ERROR", f"Error executing pipeline: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_single_image_test(self, test_image_path, output_path, config_dict, log_callback, is_verbose=False):
        job_dict = {
            'source_path': test_image_path,
            'job_type': config_dict.get('job_type', 'T')
        }
        config_dict['is_single_file'] = True
        return self.run(job_dict, output_path, config_dict, log_callback, is_verbose, output_format='png')
