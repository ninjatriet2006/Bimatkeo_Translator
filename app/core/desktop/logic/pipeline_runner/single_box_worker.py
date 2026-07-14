"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.pipeline_runner.single_box_worker
- RESPONSIBILITY: Execute single-box operations (OCR, Translation, Render) in isolated processes to prevent memory leaks and UI blocking.
- CALLED BY: app.core.desktop.logic.pipeline_runner.preview_tester
- CALLS TO: app.core.pipeline.config_loader, app.core.ocr.initializer, etc.
- IN = OUT: Receives isolated task parameters, returns result via Queue.
=============================================================================
"""
import os
import queue
import multiprocessing
from PIL import Image

def _ocr_process(image_path, bbox, config_dict, result_queue, temp_dir, python_exec):
    try:
        from app.core.pipeline.config_loader import load_all_configs
        from app.core.ocr.initializer import OCRInitializer
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        config_bundle = load_all_configs(project_root, config_dict, None)
        final_config = config_bundle["config"]
        
        # We only need the recognizer
        _, _, recognizer = OCRInitializer.initialize(final_config, None)
        
        if not recognizer:
            result_queue.put({"success": False, "error": "No valid recognizer found for single box OCR."})
            return
            
        img = Image.open(image_path).convert('RGB')
        x, y, w, h = bbox
        crop_img = img.crop((x, y, x + w, y + h))
        
        text = recognizer.recognize(crop_img)
        result_queue.put({"success": True, "text": text})
        
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})

def _translation_process(text, config_dict, result_queue, temp_dir, python_exec):
    try:
        from app.core.pipeline.config_loader import load_all_configs
        from app.core.translator.initializer import TranslatorInitializer
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        config_bundle = load_all_configs(project_root, config_dict, None)
        final_config = config_bundle["config"]
        api_profiles = config_bundle["api_profiles"]
        
        chained_translators, _ = TranslatorInitializer.initialize(final_config, project_root, api_profiles, None)
        
        if not chained_translators:
            result_queue.put({"success": False, "error": "No valid translators found for single box."})
            return
            
        current_text = [text]
        for tr in chained_translators:
            current_text = tr.translate(current_text)
            
        result_queue.put({"success": True, "text": current_text[0] if current_text else ""})
        
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})

def _render_process(image_path, bbox, translated_text, render_config, result_queue, temp_dir, python_exec):
    try:
        from app.core.renderer.initializer import RendererInitializer
        from app.core.shared_context.dto import PageContext, TextBlock
        import cv2
        import numpy as np
        
        renderer = RendererInitializer.initialize({"render": render_config}, None)
        if not renderer:
            result_queue.put({"success": False, "error": "No valid renderer found."})
            return
            
        # Create a dummy context
        ctx = PageContext("test", "test", image_path)
        ctx.rendered_image = cv2.imdecode(np.fromfile(image_path, dtype=np.uint8), cv2.IMREAD_COLOR)
        
        x, y, w, h = bbox
        block = TextBlock(x, y, w, h, "", 0)
        block.translation = translated_text
        block.color = [0, 0, 0] # Default text color
        block.font_size = 30 # Default size
        
        ctx.text_blocks = [block]
        
        renderer.render(ctx)
        
        output_path = os.path.join(temp_dir, "single_box_render_temp.png")
        cv2.imencode('.png', ctx.rendered_image)[1].tofile(output_path)
        
        result_queue.put({"success": True, "output_path": output_path})
        
    except Exception as e:
        result_queue.put({"success": False, "error": str(e)})

class SingleBoxWorker:
    def __init__(self, main_window):
        self.mw = main_window

    def run_ocr(self, image_path, bbox, config_dict, callback):
        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=_ocr_process,
            args=(image_path, bbox, config_dict, result_queue, self.mw.temp_dir, self.mw.config_loader.python_executable)
        )
        p.start()
        
        self._wait_and_callback(p, result_queue, callback)

    def run_translation(self, text, config_dict, callback):
        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=_translation_process,
            args=(text, config_dict, result_queue, self.mw.temp_dir, self.mw.config_loader.python_executable)
        )
        p.start()
        
        self._wait_and_callback(p, result_queue, callback)

    def run_render(self, image_path, bbox, translated_text, render_config, callback):
        result_queue = multiprocessing.Queue()
        p = multiprocessing.Process(
            target=_render_process,
            args=(image_path, bbox, translated_text, render_config, result_queue, self.mw.temp_dir, self.mw.config_loader.python_executable)
        )
        p.start()
        
        self._wait_and_callback(p, result_queue, callback)

    def _wait_and_callback(self, process, result_queue, callback):
        import threading
        
        def waiter():
            process.join()
            try:
                res = result_queue.get_nowait()
                callback(res)
            except queue.Empty:
                callback({"success": False, "error": "Process crashed or returned no result."})
                
        threading.Thread(target=waiter, daemon=True).start()
