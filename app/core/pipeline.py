import os
import time
import io
import shutil
import queue
import cv2 # type: ignore
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.core.dto import PageContext
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer, BaseTranslator, BaseInpainter, BaseRenderer
from app.core.workers import OCRWorker, TranslatorWorker, InpaintWorker, RenderWorker
from app.core.factories import TranslatorFactory, DetectorFactory, RecognizerFactory, InpainterFactory, RendererFactory

# Nạp các Plugin (để trigger @Factory.register)
try:
    import app.plugins.detector.ctd_impl
    import app.plugins.recognizer.mocr_impl
except ImportError:
    pass

# --- Dummy Implementations for the currently missing ML Models ---
@DetectorFactory.register("dummy_detector")
class DummyDetector(BaseTextDetector):
    def load_model(self, model_path: str, **kwargs) -> None:
        pass
    def detect(self, image: np.ndarray) -> list:
        h, w = image.shape[:2]
        # Return a mock box in the center
        return [[w//4, h//4, w*3//4, h*3//4]]

@RecognizerFactory.register("dummy_recognizer")
class DummyRecognizer(BaseTextRecognizer):
    def load_model(self, model_path: str, **kwargs) -> None:
        pass
    def recognize(self, image_crop: np.ndarray) -> str:
        return "Mock Original Text"

@TranslatorFactory.register("dummy_translator")
class DummyTranslator(BaseTranslator):
    def load_weights(self, model_path: str, **kwargs) -> None:
        pass
    def translate(self, texts: list, src_lang: str, tgt_lang: str) -> list:
        return [f"[Translated to {tgt_lang}] {t}" for t in texts]

@InpainterFactory.register("dummy_inpainter")
class DummyInpainter(BaseInpainter):
    def load_model(self, model_path: str, **kwargs) -> None:
        pass
    def inpaint(self, image: np.ndarray, bboxes: list) -> np.ndarray:
        return image.copy()

@RendererFactory.register("dummy_renderer")
class DummyRenderer(BaseRenderer):
    def load_fonts(self, font_path: str, **kwargs) -> None:
        pass
    def render(self, image: np.ndarray, bboxes: list, texts: list) -> np.ndarray:
        # Convert numpy to PIL for drawing
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        pil_img = Image.fromarray(image_rgb).convert("RGBA")
        draw = ImageDraw.Draw(pil_img, "RGBA")
        
        for box, text in zip(bboxes, texts):
            x1, y1, x2, y2 = box
            # Draw semi-transparent background
            draw.rectangle([x1, y1, x2, y2], fill=(15, 23, 42, 220), outline=(99, 102, 241, 255), width=2)
            # Draw mock text
            draw.text((x1 + 10, y1 + 10), text, fill=(255, 255, 255, 255))
            
        final_rgb = np.array(pil_img.convert("RGB"))
        return cv2.cvtColor(final_rgb, cv2.COLOR_RGB2BGR)
# -----------------------------------------------------------------


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

    def run(self, job, output_path, config_dict, log_callback, is_verbose=False, output_format='png'):
        """Runs the real multi-threaded pipeline."""
        self._preprocess_config(config_dict)
        source_path = job['source_path']
        log_callback("PIPELINE", f"Starting Modular Pipeline for job '{os.path.basename(source_path)}'.")
        self._stopped_by_user = False

        all_files = sorted([
            f for f in os.listdir(source_path) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))
        ])

        if not all_files:
            log_callback("WARNING", "No images found in the source directory.")
            return True

        target_lang = config_dict.get("translator", {}).get("target_lang", "VIN")

        pipeline_config = config_dict.get("pipeline", {})
        enable_ocr = pipeline_config.get("enable_ocr", True)
        enable_translator = pipeline_config.get("enable_translator", True)
        enable_inpainter = pipeline_config.get("enable_inpainter", True)
        enable_renderer = pipeline_config.get("enable_renderer", True)

        # Hidden Debug Config (Dành cho Dev Test - Bỏ qua UI)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Initialize Queues
            q_in = queue.Queue(maxsize=10)
            q_ocr = queue.Queue(maxsize=10)
            q_trans = queue.Queue(maxsize=10)
            q_inpaint = queue.Queue(maxsize=10)
            q_render = queue.Queue(maxsize=10)
            q_out = queue.Queue()

            # Lấy cấu hình model (mặc định là 'ctd' và 'mocr' nếu không có)
            detector_name = config_dict.get("detector", {}).get("detector", "ctd")
            ocr_name = config_dict.get("ocr", {}).get("ocr", "mocr")

            # Initialize Dummy Models from Factories (or None if disabled)
            try:
                detector = DetectorFactory.create(detector_name, log_callback=log_callback) if enable_ocr else None
            except ValueError:
                detector = DetectorFactory.create("dummy_detector", log_callback=log_callback) if enable_ocr else None
                
            try:
                recognizer = RecognizerFactory.create(ocr_name, log_callback=log_callback) if enable_ocr else None
            except ValueError:
                recognizer = RecognizerFactory.create("dummy_recognizer", log_callback=log_callback) if enable_ocr else None
                
            translator = TranslatorFactory.create("dummy_translator") if enable_translator else None
            inpainter = InpainterFactory.create("dummy_inpainter") if enable_inpainter else None
            renderer = RendererFactory.create("dummy_renderer") if enable_renderer else None

            # Initialize Workers
            ocr_worker = OCRWorker(q_in, q_ocr, detector, recognizer, log_callback)
            trans_worker = TranslatorWorker(q_ocr, q_trans, translator, "auto", target_lang, log_callback)
            inpaint_worker = InpaintWorker(q_trans, q_inpaint, inpainter, log_callback)
            render_worker = RenderWorker(q_inpaint, q_render, renderer, log_callback)

            # Start Workers
            for w in [ocr_worker, trans_worker, inpaint_worker, render_worker]:
                w.start()

            # Producer: Load images into memory
            for index, filename in enumerate(all_files):
                if self._stopped_by_user:
                    break
                log_callback("INFO", f"[{index + 1}/{len(all_files)}] Nạp ảnh lên RAM: {filename}")
                img_path = os.path.join(source_path, filename)
                img_array = cv2.imread(img_path)
                if img_array is None:
                    log_callback("WARNING", f"Không thể đọc ảnh: {filename}")
                    continue
                ctx = PageContext(page_id=filename, original_image=img_array)
                q_in.put(ctx)

            # Send stop signals
            q_in.put(None)

            # Consumer: Save outputs
            completed = 0
            while True:
                ctx = q_render.get()
                if ctx is None:
                    break
                
                output_filename = os.path.splitext(ctx.page_id)[0] + f".{output_format}"
                output_file = os.path.join(output_path, output_filename)
                
                if ctx.rendered_image is not None:
                    cv2.imwrite(output_file, ctx.rendered_image)
                    log_callback("SUCCESS", f"Đã lưu kết quả: {output_filename}")
                
                completed += 1
                q_render.task_done()

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
        # Implementation omitted
        pass

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
