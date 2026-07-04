import os
import time
import io
import shutil
import queue
import cv2 # type: ignore
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.core.dto import PageContext
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer, BaseTranslator, BaseInpainter, BaseRenderer, BaseCloudOCR, BaseUpscaler
from app.core.workers import OCRWorker, TranslatorWorker, InpaintWorker, RenderWorker, UpscalerWorker
from app.core.factories import TranslatorFactory, DetectorFactory, RecognizerFactory, InpainterFactory, RendererFactory, CloudOCRFactory, UpscalerFactory

# Nạp các Plugin (để trigger @Factory.register)
try:
    import app.plugins.detector.ctd_impl
    import app.plugins.detector.dbconvnext_impl
    import app.plugins.detector.craft_impl

    import app.plugins.detector.paddle_onnx_impl
    import app.plugins.recognizer.pixel_32px_impl
    import app.plugins.recognizer.pixel_48px_impl
    import app.plugins.recognizer.pixel_48px_ctc_impl
    import app.plugins.recognizer.paddle_onnx_rec_impl
    import app.plugins.recognizer.tesseract_impl
    import app.plugins.recognizer.manga_ocr_impl
    import app.plugins.cloud_ocr.gemini_vision_impl
    import app.plugins.cloud_ocr.google_vision_impl
    import app.plugins.translator
    
    import app.plugins.inpainter.lama_impl
    import app.plugins.inpainter.manga_inpaint_impl
    import app.plugins.inpainter.powerpaint_impl
    import app.plugins.inpainter.powerpaint_v2_impl
    import app.plugins.inpainter.opencv_impl
    import app.plugins.upscaler.esrgan_impl
    import app.plugins.renderer.pillow_impl
except ImportError as e:
    print(f"Warning: Failed to import some plugins - {e}")

# --- Dummy Implementations for the currently missing ML Models ---
@DetectorFactory.register("dummy_detector")
class DummyDetector(BaseTextDetector):
    def load_model(self, model_path: str, **kwargs) -> None:
        pass
    def detect(self, image: np.ndarray) -> tuple[list[list[int]], list[list[list[int]]]]:
        h, w = image.shape[:2]
        # Return a mock box in the center and empty polygon
        return [[w//4, h//4, w*3//4, h*3//4]], [[[]]]

@RecognizerFactory.register("dummy_recognizer")
class DummyRecognizer(BaseTextRecognizer):
    def load_model(self, model_path: str, **kwargs) -> None:
        pass
    def recognize(self, image_crop: np.ndarray) -> tuple[str, float]:
        return "Mock Original Text", 1.0

@TranslatorFactory.register("dummy_translator")
class DummyTranslator(BaseTranslator):
    def load_weights(self, model_path: str, **kwargs) -> None:
        pass
    def translate(self, texts: list, src_lang: str, tgt_lang: str, context_texts: list | None = None) -> list:
        return [f"[Translated to {tgt_lang}] {t}" for t in texts]




class Pipeline:
    """Handles the execution of the backend translation process via Fork-Join Queue Architecture."""

    def __init__(self, app, python_executable, temp_dir):
        self.app = app
        self.python_executable = python_executable
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self.process = None
        self._stopped_by_user = False

    def _preprocess_config(self, config_dict):
        # Implementation omitted for brevity but functionally the same as before
        pass

    def run(self, job, output_path, config_dict, log_callback, is_verbose=False, output_format='png', mtpe_callback=None):
        """Runs the real multi-threaded pipeline."""
        self._preprocess_config(config_dict)
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

        target_lang = config_dict.get("translator", {}).get("target_lang", "VIN")

        pipeline_config = config_dict.get("pipeline", {})
        enable_ocr = pipeline_config.get("enable_ocr", True)
        enable_translator = pipeline_config.get("enable_translator", True)
        enable_inpainter = pipeline_config.get("enable_inpainter", True)
        enable_renderer = pipeline_config.get("enable_renderer", True)
        enable_hitl = config_dict.get("enable_hitl", False)

        # Hidden Debug Config (Dành cho Dev Test - Bỏ qua UI)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # Load Ignored.yaml
        ignored_yaml_path = os.path.join(project_root, ".config", "configs", "Ignored.yaml")
        skip_languages = {}
        filter_texts = []
        if os.path.exists(ignored_yaml_path):
            try:
                import yaml
                with open(ignored_yaml_path, 'r', encoding='utf-8') as f:
                    ignored_data = yaml.safe_load(f) or {}
                skip_languages = ignored_data.get("skip_languages", {})
                filter_texts = ignored_data.get("filter_texts", [])
            except Exception as e:
                log_callback("ERROR", f"Failed to load Ignored.yaml: {e}")
        
        # Load API profiles for chain
        api_profiles_path = os.path.join(project_root, ".config", "configs", "api_profiles.yaml")
        api_profiles = {}
        if os.path.exists(api_profiles_path):
            try:
                import yaml
                with open(api_profiles_path, 'r', encoding='utf-8') as f:
                    api_profiles = yaml.safe_load(f) or {}
            except Exception:
                pass
        debug_file = os.path.join(project_root, ".config", "configs", "debug_pipeline.yaml")
        if os.path.exists(debug_file):
            try:
                import yaml
                with open(debug_file, "r", encoding="utf-8") as f:
                    debug_cfg = yaml.safe_load(f) or {}
                enable_ocr = debug_cfg.get("enable_ocr", enable_ocr)
                enable_translator = debug_cfg.get("enable_translator", enable_translator)
                enable_inpainter = debug_cfg.get("enable_inpainter", enable_inpainter)
                enable_renderer = debug_cfg.get("enable_renderer", enable_renderer)
                log_callback("PIPELINE", "Loaded hidden overrides from debug_pipeline.yaml")
            except Exception as e:
                log_callback("WARNING", f"Error reading debug_pipeline.yaml: {e}")

        is_text_only = config_dict.get('job_type') == 'TX'
        if is_text_only:
            enable_ocr = False
            enable_inpainter = False
            enable_renderer = False

        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Initialize Queues for Fork-Join
            q_in = queue.Queue()
            q_trans = queue.Queue()
            q_inpaint = queue.Queue()
            q_upscale = queue.Queue()
            q_render = queue.Queue()
            q_out = queue.Queue()

            # Lấy cấu hình OCR/Detector mới
            ocr_category = config_dict.get("ocr_category", "Offline")
            
            detector = None
            recognizer = None
            cloud_ocr = None
            
            if enable_ocr:
                if ocr_category == "AI / Online":
                    api_ocr_name = config_dict.get("api_ocr", "gemini_ocr")
                    api_key = config_dict.get("ocr_api_key", config_dict.get("api_ocr_key", ""))
                    endpoint = config_dict.get("ocr_api_endpoint", "")
                    model_name = config_dict.get("ocr_api_model", "")
                    try:
                        cloud_ocr = CloudOCRFactory.create(api_ocr_name)
                        cloud_ocr.load_model(api_key, endpoint=endpoint, model_name=model_name, log_callback=log_callback)
                    except Exception as e:
                        log_callback("ERROR", f"Lỗi khởi tạo Cloud OCR: {e}")
                        cloud_ocr = None
                else:
                    detector_name = config_dict.get("offline_detector", "dbconvnext")
                    ocr_name = config_dict.get("offline_ocr", "paddle_onnx_rec")

                    from app.core.downloader import ModelDownloader

                    # Initialize Local Models
                    try:
                        det_path = ModelDownloader.get_model_path_from_registry("offline_detector", detector_name)
                        detector = DetectorFactory.create(detector_name, model_path=det_path, log_callback=log_callback, **config_dict.get("detector", {}))
                    except ValueError:
                        detector = DetectorFactory.create("dummy_detector", log_callback=log_callback)
                        
                    try:
                        rec_path = ModelDownloader.get_model_path_from_registry("offline_ocr", ocr_name)
                        recognizer = RecognizerFactory.create(ocr_name, model_path=rec_path, log_callback=log_callback, **config_dict.get("ocr", {}))
                    except ValueError:
                        recognizer = RecognizerFactory.create("dummy_recognizer", log_callback=log_callback)
                
            translator_dict = config_dict.get("translator", {})
            translator = None
            if enable_translator:
                try:
                    if 'pool_apis' in translator_dict and translator_dict['pool_apis']:
                        # Dùng API đầu tiên trong Pool (có thể nâng cấp thành PoolTranslator xoay vòng sau)
                        api_info = translator_dict['pool_apis'][0]
                        provider_name = api_info.get('translator', 'openai')
                        translator = TranslatorFactory.create(provider_name)
                        translator.log_callback = log_callback
                        translator.load_weights({
                            "endpoint": api_info.get('endpoint'),
                            "model": api_info.get('model'),
                            "key": api_info.get('api_key', api_info.get('key', '')),
                            "max_retries": translator_dict.get('max_retries', 3),
                            "glossary_path": translator_dict.get('glossary_path', ''),
                            "system_prompt_profile": translator_dict.get('system_prompt_profile', 'None'),
                            "project_base_dir": project_root
                        })
                    else:
                        provider_name = translator_dict.get('translator', 'openai')
                        translator = TranslatorFactory.create(provider_name)
                        translator.log_callback = log_callback
                        category = translator_dict.get('translator_category', 'Offline')
                        
                        if category == 'Offline' or provider_name in ['nllb', 'm2m100']:
                            from app.core.downloader import ModelDownloader
                            try:
                                trans_path = ModelDownloader.get_model_path_from_registry("offline_translator", provider_name)
                                translator.load_weights(trans_path)
                            except ValueError:
                                log_callback("ERROR", f"Offline translator '{provider_name}' not found.")
                                translator = None
                        else:
                            translator.load_weights({
                                "endpoint": translator_dict.get('ai_endpoint'),
                                "model": translator_dict.get('ai_model'),
                                "key": translator_dict.get('ai_api_key', translator_dict.get('ai_key', '')),
                                "max_retries": translator_dict.get('max_retries', 3),
                                "glossary_path": translator_dict.get('glossary_path', ''),
                                "system_prompt_profile": translator_dict.get('system_prompt_profile', 'None'),
                                "project_base_dir": project_root
                            })
                except Exception as e:
                    log_callback("ERROR", f"Failed to load translator: {e}")
                    translator = None
                    
            editor_translator = None
            if enable_translator and str(config_dict.get("enable_double_check", "Yes")).lower() in ["yes", "true", "1"]:
                try:
                    if 'pool_apis' in translator_dict and translator_dict['pool_apis']:
                        api_info = translator_dict['pool_apis'][0]
                        provider_name = api_info.get('translator', 'openai')
                        editor_translator = TranslatorFactory.create(provider_name)
                        editor_translator.log_callback = log_callback
                        editor_translator.load_weights({
                            "endpoint": api_info.get('endpoint'),
                            "model": api_info.get('model'),
                            "key": api_info.get('api_key', api_info.get('key', '')),
                            "max_retries": translator_dict.get('max_retries', 3),
                            "glossary_path": translator_dict.get('glossary_path', ''),
                            "system_prompt_profile": "editor",
                            "project_base_dir": project_root
                        })
                    else:
                        provider_name = translator_dict.get('translator', 'openai')
                        editor_translator = TranslatorFactory.create(provider_name)
                        editor_translator.log_callback = log_callback
                        category = translator_dict.get('translator_category', 'Offline')
                        
                        if category == 'Offline' or provider_name in ['nllb', 'm2m100']:
                            from app.core.downloader import ModelDownloader
                            try:
                                trans_path = ModelDownloader.get_model_path_from_registry("offline_translator", provider_name)
                                editor_translator.load_weights(trans_path)
                            except ValueError:
                                log_callback("ERROR", f"Offline editor translator '{provider_name}' not found.")
                                editor_translator = None
                        else:
                            editor_translator.load_weights({
                                "endpoint": translator_dict.get('ai_endpoint'),
                                "model": translator_dict.get('ai_model'),
                                "key": translator_dict.get('ai_api_key', translator_dict.get('ai_key', '')),
                                "max_retries": translator_dict.get('max_retries', 3),
                                "glossary_path": translator_dict.get('glossary_path', ''),
                                "system_prompt_profile": "editor",
                                "project_base_dir": project_root
                            })
                except Exception as e:
                    log_callback("ERROR", f"Failed to load editor translator: {e}")
                    editor_translator = None
            enable_advanced_diffusion = config_dict.get("inpainter", {}).get("enable_advanced_diffusion", False)
            if enable_advanced_diffusion:
                inpainter_name = config_dict.get("inpainter", {}).get("diffusion_model", "powerpaint_v1")
                try:
                    from app.core.downloader import ModelDownloader
                    from app.core.factories import DiffusionFactory
                    inp_path = ModelDownloader.get_model_path_from_registry("diffusion_model", inpainter_name)
                    inpainter = DiffusionFactory.create(inpainter_name, model_path=inp_path, log_callback=log_callback, **config_dict.get("inpainter", {})) if enable_inpainter and inpainter_name != "none" else None
                except ValueError:
                    log_callback("WARNING", f"Diffusion Model '{inpainter_name}' not found, falling back to None.")
                    inpainter = None
            else:
                inpainter_name = config_dict.get("inpainter", {}).get("inpainter", "lama")
                try:
                    from app.core.downloader import ModelDownloader
                    inp_path = ModelDownloader.get_model_path_from_registry("inpainter", inpainter_name)
                    inpainter = InpainterFactory.create(inpainter_name, model_path=inp_path, log_callback=log_callback, **config_dict.get("inpainter", {})) if enable_inpainter and inpainter_name != "none" else None
                except ValueError:
                    log_callback("WARNING", f"Inpainter '{inpainter_name}' not found, falling back to None.")
                    inpainter = None

            renderer_name = config_dict.get("render", {}).get("renderer", "pillow_renderer")
            try:
                renderer = RendererFactory.create(renderer_name, log_callback=log_callback) if enable_renderer and renderer_name != "none" else None
                if renderer and "font_path" in config_dict:
                    renderer.load_fonts(config_dict["font_path"], **config_dict.get("render", {}))
            except ValueError:
                log_callback("WARNING", f"Renderer '{renderer_name}' not found, falling back to None.")
                renderer = None
                
            enable_upscaler = config_dict.get("inpainter", {}).get("enable_upscaler", False)
            upscaler = None
            upscale_ratio = int(config_dict.get("inpainter", {}).get("upscale_ratio", 2))
            if enable_upscaler:
                upscaler_name = config_dict.get("inpainter", {}).get("upscaler", "esrgan")
                try:
                    from app.core.downloader import ModelDownloader
                    ups_path = ModelDownloader.get_model_path_from_registry("upscaler", upscaler_name)
                    upscaler = UpscalerFactory.create(upscaler_name)
                    upscaler.load_model(ups_path)
                except Exception as e:
                    log_callback("WARNING", f"Upscaler '{upscaler_name}' could not be loaded: {e}. Falling back to None.")
                    upscaler = None

            # Initialize Workers for Fork-Join Pipeline
            ocr_worker = OCRWorker(q_in, q_trans, q_inpaint, q_render, detector, recognizer, log_callback, cloud_ocr=cloud_ocr, ocr_config=config_dict.get("ocr", {}), render_config=config_dict.get("render", {}))
            
            # --- Translator Chain / Translator setup ---
            enable_translator_chain = config_dict.get("translator", {}).get("enable_translator_chain", False)
            translator_chain_str = config_dict.get("translator", {}).get("translator_chain", "")
            
            chained_translators = []
            if enable_translator and enable_translator_chain and translator_chain_str:
                steps = [s for s in translator_chain_str.split(';') if s]
                for step in steps:
                    if ':' in step:
                        t_name, t_lang = step.split(':', 1)
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
            
            no_text_lang_skip = config_dict.get("translator", {}).get("no_text_lang_skip", False)
            max_request_length = int(config_dict.get("translator", {}).get("max_request_length", 2000))

            trans_worker = TranslatorWorker(
                q_trans, 
                chained_translators, 
                config_dict.get("translator", {}).get("source_lang", "JPN"), 
                target_lang, # Fallback overall target_lang
                log_callback,
                skip_languages=skip_languages,
                filter_texts=filter_texts,
                no_text_lang_skip=no_text_lang_skip,
                max_request_length=max_request_length,
                editor_translator=editor_translator,
                context_window=int(config_dict.get("translator", {}).get("context_window", 10)),
                stride_window=int(config_dict.get("translator", {}).get("stride_window", 5))
            )
            inpaint_worker = InpaintWorker(q_inpaint, inpainter, log_callback, out_q=q_upscale if enable_upscaler else None)
            upscale_worker = UpscalerWorker(q_upscale, upscaler, upscale_ratio, log_callback) if enable_upscaler else None
            render_worker = RenderWorker(q_render, q_out, renderer, log_callback)

            # Start Workers
            import threading
            workers: list[threading.Thread] = [ocr_worker, trans_worker, inpaint_worker, render_worker]
            if upscale_worker:
                workers.append(upscale_worker)
            for w in workers:
                w.start()

            # Producer: Load files into memory (with Resume feature)
            for index, filename in enumerate(all_files):
                if self._stopped_by_user:
                    break
                img_path = os.path.join(source_dir, filename)
                is_text_only = config_dict.get('job_type') == 'TX'
                
                # Tính trước tên file đầu ra để kiểm tra resume
                if is_text_only or filename.lower().endswith('.txt'):

                    import json
                    with open(os.path.join(output_path, f"test_data_{os.path.basename(ctx.page_id)}.json"), "w", encoding="utf-8") as f:
                        json.dump({
                            "bboxes": ctx.bboxes,
                            "original_texts": ctx.original_texts,
                            "translated_texts": ctx.translated_texts
                        }, f, ensure_ascii=False, indent=2)
                    
                    if config_dict.get('is_single_file', False):

                        output_filename = os.path.splitext(filename)[0] + f"_translated.txt"
                    else:
                        output_filename = filename
                else:
                    output_filename = os.path.splitext(filename)[0] + f".{output_format}"
                
                output_file = os.path.join(output_path, output_filename)
                if os.path.exists(output_file):
                    log_callback("INFO", f"[{index + 1}/{len(all_files)}] Bỏ qua file đã hoàn thành (Resume): {filename}")
                    continue

                if is_text_only or filename.lower().endswith('.txt'):
                    log_callback("INFO", f"[{index + 1}/{len(all_files)}] Nạp file text: {filename}")
                    with open(img_path, 'r', encoding='utf-8') as f:
                        lines = [line.strip() for line in f if line.strip()]
                    ctx = PageContext(page_id=filename, original_image=None, original_texts=lines)
                    q_in.put(ctx)
                else:
                    memory_mode = config_dict.get("memory_mode", "RAM")
                    if memory_mode == "DISK":
                        log_callback("INFO", f"[{index + 1}/{len(all_files)}] Nạp ảnh (DISK Mode): {filename}")
                        ctx = PageContext(page_id=filename, original_image=None, original_image_path=img_path)
                        q_in.put(ctx)
                    else:
                        log_callback("INFO", f"[{index + 1}/{len(all_files)}] Nạp ảnh lên RAM: {filename}")
                        img_array = cv2.imread(img_path)
                        if img_array is None:
                            log_callback("WARNING", f"Không thể đọc ảnh: {filename}")
                            continue
                        ctx = PageContext(page_id=filename, original_image=img_array, original_image_path=img_path)
                        q_in.put(ctx)

            # Send stop signals
            q_in.put(None)

            # Consumer: Save outputs
            completed = 0
            while True:
                ctx = q_out.get()
                if ctx is None:
                    break
                
                is_text_only = config_dict.get('job_type') == 'TX'
                if is_text_only or ctx.page_id.lower().endswith('.txt'):
                    # Save translated text

                    import json
                    with open(os.path.join(output_path, f"test_data_{os.path.basename(ctx.page_id)}.json"), "w", encoding="utf-8") as f:
                        json.dump({
                            "bboxes": ctx.bboxes,
                            "original_texts": ctx.original_texts,
                            "translated_texts": ctx.translated_texts
                        }, f, ensure_ascii=False, indent=2)
                    
                    if config_dict.get('is_single_file', False):

                        output_filename = os.path.splitext(ctx.page_id)[0] + f"_translated.txt"
                    else:
                        output_filename = ctx.page_id
                    output_file = os.path.join(output_path, output_filename)
                    with open(output_file, 'w', encoding='utf-8') as f:
                        if ctx.translated_texts:
                            f.write("\n".join(ctx.translated_texts))
                        else:
                            f.write("\n".join(ctx.original_texts or []))
                    log_callback("SUCCESS", f"Đã lưu kết quả text: {output_filename}")
                else:
                    output_filename = os.path.splitext(ctx.page_id)[0] + f".{output_format}"
                    output_file = os.path.join(output_path, output_filename)
                    if ctx.rendered_image is not None:
                        cv2.imwrite(output_file, ctx.rendered_image)
                        log_callback("SUCCESS", f"Đã lưu kết quả: {output_filename}")
                        
                    # ---------------------------------------------------------
                    # NEW: Dump intermediate states if running as a single test
                    # ---------------------------------------------------------

                    import json
                    with open(os.path.join(output_path, f"test_data_{os.path.basename(ctx.page_id)}.json"), "w", encoding="utf-8") as f:
                        json.dump({
                            "bboxes": ctx.bboxes,
                            "original_texts": ctx.original_texts,
                            "translated_texts": ctx.translated_texts
                        }, f, ensure_ascii=False, indent=2)
                    
                    if config_dict.get('is_single_file', False):

                        import json
                        
                        # Save Inpainted Image
                        inpaint_img = ctx.get_inpainted_image()
                        if inpaint_img is not None:
                            cv2.imwrite(os.path.join(output_path, "test_inpainter.png"), inpaint_img)
                        
                        # Save BBoxes Image (Detector)
                        orig_img = ctx.get_original_image()
                        if orig_img is not None and ctx.bboxes:
                            det_img = orig_img.copy()
                            for box in ctx.bboxes:
                                cv2.rectangle(det_img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
                            cv2.imwrite(os.path.join(output_path, "test_detector.png"), det_img)
                        
                        # Save Text Data (OCR and Translator)
                        with open(os.path.join(output_path, "test_data.json"), "w", encoding="utf-8") as f:
                            json.dump({
                                "bboxes": ctx.bboxes,
                                "original_texts": ctx.original_texts,
                                "translated_texts": ctx.translated_texts
                            }, f, ensure_ascii=False, indent=2)
                
                completed += 1
                q_out.task_done()

            # Wait for all queues to empty
            for w in [ocr_worker, trans_worker, inpaint_worker, render_worker]:
                w.join()

            if self._stopped_by_user:
                log_callback("WARNING", "Pipeline run stopped by user.")
                return False

            log_callback("PIPELINE", f"Job '{os.path.basename(source_path)}' completed successfully.")
            return True
        except Exception as e:
            log_callback("ERROR", f"Error executing pipeline: {e}")
            return False

    def run_single_image_test(self, test_image_path, output_path, config_dict, log_callback, is_verbose=False):
        job_dict = {
            'source_path': test_image_path,
            'job_type': config_dict.get('job_type', 'T')
        }
        config_dict['is_single_file'] = True
        return self.run(job_dict, output_path, config_dict, log_callback, is_verbose, output_format='png')

    def stop(self, log_callback):
        """Stops the pipeline simulation."""
        self._stopped_by_user = True
        log_callback("PIPELINE", "Pipeline stopped by user.")
        return True


if __name__ == "__main__":
    import argparse
    import json
    import sys
    
    parser = argparse.ArgumentParser(description="Bimatkeo Translator Backend CLI")
    parser.add_argument("--task-config", type=str, required=True, help="Path to JSON file containing task configuration")
    parser.add_argument("--test-image", type=str, help="Path to image for visual test comparison")
    args = parser.parse_args()
    
    try:
        with open(args.task_config, 'r', encoding='utf-8') as f:
            task_data = json.load(f)
    except Exception as e:
        print(f"[LOG:ERROR] Failed to load task config: {e}", flush=True)
        sys.exit(1)
        
    job = task_data.get("job")
    output_path = task_data.get("output_path")
    config = task_data.get("config")
    
    def log_callback(prefix, message):
        print(f"[LOG:{prefix}] {message}", flush=True)
        
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    temp_dir = os.path.join(project_root, "temp")
    pipeline = Pipeline(None, sys.executable, temp_dir)
    
    output_format = task_data.get("output_format", "png")
    success = pipeline.run(job, output_path, config, log_callback, is_verbose=False, output_format=output_format)
        
    if success:
        print("[FINISHED:SUCCESS]", flush=True)
        sys.exit(0)
    else:
        print("[FINISHED:FAILED]", flush=True)
        sys.exit(1)
