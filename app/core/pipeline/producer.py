"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.producer
- RESPONSIBILITY: Loads input files into the pipeline queue (q_in).
- CALLED BY: app.core.pipeline.executor
- CALLS TO: app.core.shared_context.dto, app.core.shared_context.utils
- IN = OUT: Converts files on disk to PageContext objects in memory.
=============================================================================
"""
import os
import cv2
import multiprocessing
from app.core.shared_context.dto import PageContext
from app.core.shared_context.utils import set_original_image

def produce(all_files: list, source_dir: str, output_path: str, config_dict: dict, log_callback, q_in: multiprocessing.Queue, stop_check_callback=None):
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
                log_callback("INFO", f"[{index + 1}/{len(all_files)}] msg_pipeline_skip_resume|filename={filename}")
            continue

        if is_text_only or filename.lower().endswith('.txt'):
            if log_callback:
                log_callback("INFO", f"[{index + 1}/{len(all_files)}] msg_pipeline_produce_text|filename={filename}")
            with open(img_path, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f if line.strip()]
            ctx = PageContext(page_id=filename, original_texts=lines)
            q_in.put(ctx)
        else:
            memory_mode = config_dict.get("memory_mode", "RAM")
            if memory_mode == "DISK":
                if log_callback:
                    log_callback("INFO", f"[{index + 1}/{len(all_files)}] msg_pipeline_produce_image_disk|filename={filename}")
                ctx = PageContext(page_id=filename, original_image_path=img_path)
                q_in.put(ctx)
            else:
                if log_callback:
                    log_callback("INFO", f"[{index + 1}/{len(all_files)}] msg_pipeline_produce_image|filename={filename}")
                img_array = cv2.imread(img_path)
                if img_array is None:
                    if log_callback:
                        log_callback("WARNING", f"msg_pipeline_produce_error|filename={filename}")
                    continue
                ctx = PageContext(page_id=filename)
                set_original_image(ctx, img_array)
                # ensure original_image_path is also preserved for debug
                ctx.original_image_path = img_path
                q_in.put(ctx)
                
    # Send stop signal
    q_in.put(None)
