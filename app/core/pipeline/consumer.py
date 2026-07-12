"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.consumer
- RESPONSIBILITY: Saves processed results from the pipeline queue (q_out) to disk.
- CALLED BY: app.core.pipeline.executor
- CALLS TO: app.core.shared_context.dto, app.core.shared_context.utils
- IN = OUT: Writes translated texts, JSON data, and final images.
=============================================================================
"""
import os
import cv2
import json
import queue
from app.core.shared_context.dto import PageContext
from app.core.shared_context.utils import get_original_image, get_inpainted_image

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
                log_callback("SUCCESS", f"msg_pipeline_consume_text|filename={output_filename}")
        else:
            output_filename = os.path.splitext(ctx.page_id)[0] + f".{output_format}"
            output_file = os.path.join(output_path, output_filename)
            if ctx.rendered_image is not None:
                cv2.imwrite(output_file, ctx.rendered_image)
                if log_callback:
                    log_callback("SUCCESS", f"msg_pipeline_consume_image|filename={output_filename}")
                
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
