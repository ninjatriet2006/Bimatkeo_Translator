import os
import time
import io
import shutil
from PIL import Image, ImageDraw, ImageFont

class Pipeline:
    """Handles the execution of the backend translation process (Mock/Pure UI Phase)."""

    def __init__(self, app, python_executable, temp_dir):
        self.app = app
        self.python_executable = python_executable
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self.process = None
        self._stopped_by_user = False

    def _extract_env_overrides(self, config_dict):
        # Decoupled from manga_translator.translators.keys
        return {}

    def _generate_mock_image(self, input_image_path, output_image_path, target_lang):
        """Vẽ đè thông báo dịch thử nghiệm bằng Pillow lên ảnh đầu ra để giả lập kết quả."""
        try:
            with open(input_image_path, 'rb') as f:
                image_bytes = f.read()
            
            img = Image.open(io.BytesIO(image_bytes))
            draw = ImageDraw.Draw(img, "RGBA")
            width, height = img.size

            # Thiết lập kích thước box vẽ
            card_w, card_h = min(width - 40, 500), min(height - 40, 300)
            x1 = (width - card_w) // 2
            y1 = (height - card_h) // 2
            x2, y2 = x1 + card_w, y1 + card_h

            # Vẽ panel tối kính mờ (Glassmorphism Mock)
            draw.rectangle([x1, y1, x2, y2], fill=(15, 23, 42, 220), outline=(255, 255, 255, 40), width=2)
            draw.rectangle([x1 + 5, y1 + 5, x2 - 5, y1 + 10], fill=(99, 102, 241, 255)) # Màu nhấn Indigo

            # Chữ tiêu đề
            text_title = "Bimatkeo Translator v2"
            text_status = "MOCK ASYNC RUN SUCCESSFUL!"
            text_details = (
                f"Target Lang: {target_lang}\n"
                f"Processing Thread: QThread (Async)\n"
                f"OCR Engine: Modular Mock\n"
                f"Status: UI Responsive (0% lag)"
            )

            draw.text((x1 + 20, y1 + 30), text_title, fill=(255, 255, 255, 255))
            draw.text((x1 + 20, y1 + 60), text_status, fill=(16, 185, 129, 255)) # Emerald
            draw.text((x1 + 20, y1 + 100), text_details, fill=(209, 213, 219, 255))

            img.save(output_image_path)
            return True
        except Exception as e:
            print(f"Error drawing mock: {e}")
            try:
                shutil.copy(input_image_path, output_image_path)
                return True
            except:
                return False

    def run(self, job, output_path, config_dict, log_callback, is_verbose=False, output_format='png'):
        """Runs the mock pipeline for a batch of files asynchronously."""
        source_path = job['source_path']
        log_callback("PIPELINE", f"Starting mock pipeline for job '{os.path.basename(source_path)}'.")
        self._stopped_by_user = False

        # Thu thập các file ảnh đầu vào
        all_files = sorted([
            f for f in os.listdir(source_path) 
            if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))
        ])

        if not all_files:
            log_callback("WARNING", "No images found in the source directory.")
            return True

        target_lang = config_dict.get("translator", {}).get("target_lang", "VIN")

        try:
            os.makedirs(output_path, exist_ok=True)
            
            for index, filename in enumerate(all_files):
                if self._stopped_by_user:
                    log_callback("WARNING", "Pipeline run stopped by user.")
                    return False
                
                log_callback("INFO", f"[{index + 1}/{len(all_files)}] Processing image: {filename}")
                
                # Giả lập các bước xử lý bất đồng bộ
                steps = [
                    ("DETECT", "Detecting text boxes..."),
                    ("OCR", "Performing OCR text recognition..."),
                    ("TRANSLATE", f"Translating text to {target_lang}..."),
                    ("INPAINT", "Inpainting background textures..."),
                    ("RENDER", "Rendering typography layer...")
                ]
                
                for prefix, msg in steps:
                    if self._stopped_by_user:
                        return False
                    log_callback(prefix, msg)
                    time.sleep(0.4) # Độ trễ giả lập nhẹ nhàng

                # Tạo ảnh mock ở output path
                input_file = os.path.join(source_path, filename)
                output_filename = os.path.splitext(filename)[0] + f".{output_format}"
                output_file = os.path.join(output_path, output_filename)
                
                self._generate_mock_image(input_file, output_file, target_lang)
                log_callback("SUCCESS", f"Saved translated output: {output_filename}")
                time.sleep(0.2)

            log_callback("PIPELINE", f"Job '{os.path.basename(source_path)}' completed successfully.")
            return True
        except Exception as e:
            log_callback("ERROR", f"Error executing pipeline: {e}")
            return False

    def run_single_image_test(self, test_image_path, output_path, config_dict, log_callback, is_verbose=False):
        """Runs the mock pipeline for a single test image inside a background thread."""
        log_callback("PIPELINE", f"Starting visual test mock for: {os.path.basename(test_image_path)}")
        self._stopped_by_user = False

        target_lang = config_dict.get("translator", {}).get("target_lang", "VIN")

        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Giả lập tiến trình
            steps = [
                ("DETECT", "Finding speech bubbles..."),
                ("OCR", "Recognizing characters..."),
                ("TRANSLATE", f"Translating text to {target_lang}..."),
                ("INPAINT", "Cleaning text regions..."),
                ("RENDER", "Rendering typeset text...")
            ]
            
            for prefix, msg in steps:
                if self._stopped_by_user:
                    log_callback("WARNING", "Visual test interrupted.")
                    return False
                log_callback(prefix, msg)
                time.sleep(0.3)

            # Tạo file kết quả
            filename = os.path.basename(test_image_path)
            output_file = os.path.join(output_path, filename)
            
            self._generate_mock_image(test_image_path, output_file, target_lang)
            log_callback("SUCCESS", f"Test rendering finalized at {output_file}")
            return True
        except Exception as e:
            log_callback("ERROR", f"Visual test simulation failed: {e}")
            return False

    def stop(self, log_callback):
        """Stops the mock pipeline simulation."""
        self._stopped_by_user = True
        log_callback("PIPELINE", "Mock pipeline stopped by user.")
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
    
    if args.test_image:
        success = pipeline.run_single_image_test(args.test_image, output_path, config, log_callback)
    else:
        output_format = task_data.get("output_format", "png")
        success = pipeline.run(job, output_path, config, log_callback, is_verbose=False, output_format=output_format)
        
    if success:
        print("[FINISHED:SUCCESS]", flush=True)
        sys.exit(0)
    else:
        print("[FINISHED:FAILED]", flush=True)
        sys.exit(1)
