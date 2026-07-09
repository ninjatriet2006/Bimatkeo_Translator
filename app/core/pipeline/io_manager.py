"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.io_manager
- RESPONSIBILITY: Handles I/O operations for pipeline state.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: None
- IN = OUT: Manages reading and writing task data to/from disk.
=============================================================================
"""
import os
import cv2
import json
import queue
from app.core.shared.dto import PageContext
from app.core.shared.context_reader import get_original_image, get_inpainted_image, get_background_image

class PipelineIOManager:
    @staticmethod
    def produce(all_files: list, source_dir: str, output_path: str, config_dict: dict, log_callback, q_in: queue.Queue, stop_check_callback=None):
        """
        Nạp file gốc (ảnh hoặc text) vào hàng đợi q_in. Bỏ qua các file đã hoàn thành nếu resume.
        """
        output_format = config_dict.get("output_format", "png")
        
        for index, filename in enumerate(all_files):
            if stop_check_callback and stop_check_callback():
                break
                
            img_path = os.path.join(source_dir, filename)
            is_text_only = config_dict.get('job_type') == 'TX'
            
            # Tính trước tên file đầu ra để kiểm tra resume
            if is_text_only or filename.lower().endswith('.txt'):
                if config_dict.get('is_single_file', False):
                    output_filename = os.path.splitext(filename)[0] + f"_translated.txt"
                else:
                    output_filename = filename
            else:
                output_filename = os.path.splitext(filename)[0] + f".{output_format}"
            
            output_file = os.path.join(output_path, output_filename)
            if os.path.exists(output_file):
                if log_callback:
                    log_callback("INFO", f"[{index + 1}/{len(all_files)}] Bỏ qua file đã hoàn thành (Resume): {filename}")
                continue

            if is_text_only or filename.lower().endswith('.txt'):
                if log_callback:
                    log_callback("INFO", f"[{index + 1}/{len(all_files)}] Nạp file text: {filename}")
                with open(img_path, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f if line.strip()]
                ctx = PageContext(page_id=filename, original_image=None, original_texts=lines)
                q_in.put(ctx)
            else:
                memory_mode = config_dict.get("memory_mode", "RAM")
                if memory_mode == "DISK":
                    if log_callback:
                        log_callback("INFO", f"[{index + 1}/{len(all_files)}] Nạp ảnh (DISK Mode): {filename}")
                    ctx = PageContext(page_id=filename, original_image=None, original_image_path=img_path)
                    q_in.put(ctx)
                else:
                    if log_callback:
                        log_callback("INFO", f"[{index + 1}/{len(all_files)}] Nạp ảnh lên RAM: {filename}")
                    img_array = cv2.imread(img_path)
                    if img_array is None:
                        if log_callback:
                            log_callback("WARNING", f"Không thể đọc ảnh: {filename}")
                        continue
                    ctx = PageContext(page_id=filename, original_image=img_array, original_image_path=img_path)
                    q_in.put(ctx)
                    
        # Send stop signal
        q_in.put(None)

    @staticmethod
    def consume(output_path: str, config_dict: dict, log_callback, q_out: queue.Queue):
        """
        Lấy kết quả từ q_out và lưu ra file ảnh, txt, hoặc json.
        """
        output_format = config_dict.get("output_format", "png")
        completed = 0
        
        while True:
            ctx = q_out.get()
            if ctx is None:
                break
            
            is_text_only = config_dict.get('job_type') == 'TX'
            if is_text_only or ctx.page_id.lower().endswith('.txt'):
                # Dump JSON Data
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
                if log_callback:
                    log_callback("SUCCESS", f"Đã lưu kết quả text: {output_filename}")
            else:
                output_filename = os.path.splitext(ctx.page_id)[0] + f".{output_format}"
                output_file = os.path.join(output_path, output_filename)
                if ctx.rendered_image is not None:
                    cv2.imwrite(output_file, ctx.rendered_image)
                    if log_callback:
                        log_callback("SUCCESS", f"Đã lưu kết quả: {output_filename}")
                    
                # NEW: Dump intermediate states if running as a single test
                with open(os.path.join(output_path, f"test_data_{os.path.basename(ctx.page_id)}.json"), "w", encoding="utf-8") as f:
                    json.dump({
                        "bboxes": ctx.bboxes,
                        "original_texts": ctx.original_texts,
                        "translated_texts": ctx.translated_texts
                    }, f, ensure_ascii=False, indent=2)
                
                if config_dict.get('is_single_file', False):
                    # Save Inpainted Image
                    inpaint_img = get_inpainted_image(ctx)
                    if inpaint_img is not None:
                        cv2.imwrite(os.path.join(output_path, "test_inpainter.png"), inpaint_img)
                    
                    # Save BBoxes Image (Detector)
                    orig_img = get_original_image(ctx)
                    if orig_img is not None and ctx.bboxes:
                        det_img = orig_img.copy()
                        for box in ctx.bboxes:
                            cv2.rectangle(det_img, (box[0], box[1]), (box[2], box[3]), (0, 255, 0), 2)
                        cv2.imwrite(os.path.join(output_path, "test_detector.png"), det_img)
                        
                    # Save Text Data
                    with open(os.path.join(output_path, "test_data.json"), "w", encoding="utf-8") as f:
                        json.dump({
                            "bboxes": ctx.bboxes,
                            "original_texts": ctx.original_texts,
                            "translated_texts": ctx.translated_texts
                        }, f, ensure_ascii=False, indent=2)
            
            completed += 1
            q_out.task_done()
