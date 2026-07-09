"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.cloud_runner
- RESPONSIBILITY: Calls Cloud API, filters, sorts, merges text bubbles.
- CALLED BY: app.core.ocr.processor
- CALLS TO: app.core.ocr.interfaces.BaseCloudOCR, app.core.ocr.filter, app.core.ocr.geometry
- IN = OUT: Receives PageContext -> processes Cloud OCR -> writes results to PageContext.
=============================================================================
"""

from app.core.shared_context.dto import PageContext
from app.core.shared_context.context_reader import get_original_image, get_inpainted_image, get_background_image
from app.core.ocr.interfaces import BaseCloudOCR
from app.core.ocr.filter import OCRFilter
from app.core.ocr.geometry import sort_comic_text_boxes, merge_nearby_boxes_and_texts

class CloudOCRRunner:
    def __init__(self, cloud_ocr: BaseCloudOCR, ocr_config: dict, render_config: dict, log_callback=None):
        self.cloud_ocr = cloud_ocr
        self.ocr_config = ocr_config
        self.render_config = render_config
        self.log_callback = log_callback

    def run(self, ctx: PageContext):
        image = get_original_image(ctx)
        if image is None:
            return

        h, w = image.shape[:2]
        
        results = self.cloud_ocr.recognize_full_page(image)
        raw_bboxes = [r["box"] for r in results]
        raw_texts = [r["text"] for r in results]
        
        filtered_bboxes, filtered_texts = OCRFilter.apply(raw_bboxes, raw_texts, self.ocr_config)
        
        ui_direction = self.render_config.get("direction", "Horizontal: Right-to-Left")
        dir_map = {
            "Horizontal: Right-to-Left": "rtl_ttb",
            "Horizontal: Left-to-Right": "ltr_ttb",
            "Vertical: Right-to-Left": "ttb_rtl",
            "Vertical: Left-to-Right": "ttb_ltr"
        }
        direction = dir_map.get(ui_direction, "rtl_ttb")
        
        sorted_bboxes = sort_comic_text_boxes(filtered_bboxes, direction=direction, image_width=w, image_height=h)
        
        box_to_text = {tuple(b): t for b, t in zip(filtered_bboxes, filtered_texts)}
        merged_bboxes, merged_texts = merge_nearby_boxes_and_texts(
            sorted_bboxes, 
            [box_to_text[tuple(b)] for b in sorted_bboxes], 
            w, h
        )
        
        ctx.raw_bboxes = sorted_bboxes
        ctx.bboxes = merged_bboxes
        ctx.original_texts = merged_texts
        ctx.translated_texts = [""] * len(ctx.original_texts)
        
        if self.log_callback:
            self.log_callback("OCR", f"Cloud OCR đã xử lý và gom lại thành {len(ctx.bboxes)} bong bóng chữ.")
