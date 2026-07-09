"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.ocr.local_runner
- RESPONSIBILITY: Coordinates Local OCR tools to extract text.
- CALLED BY: app.core.ocr.processor
- CALLS TO: app.core.ocr.preprocessor, app.core.ocr.detector, app.core.ocr.rotator, app.core.ocr.cropper, app.core.ocr.recognizer, app.core.ocr.corrector, app.core.ocr.filter, app.core.ocr.geometry
- IN = OUT: Receives PageContext -> processes -> writes results to PageContext.
=============================================================================
"""

from app.core.shared.dto import PageContext
from app.core.shared.context_reader import get_original_image, get_inpainted_image, get_background_image
from app.core.shared.context_writer import set_original_image, set_inpainted_image
from app.core.interfaces import BaseTextDetector, BaseTextRecognizer

from app.core.ocr.preprocessor import OCRPreprocessor
from app.core.ocr.rotator import OCRRotator
from app.core.ocr.cropper import OCRCropper
from app.core.ocr.recognizer import OCRRecognizer
from app.core.ocr.filter import OCRFilter
from app.core.ocr.geometry import sort_comic_text_boxes, merge_nearby_boxes_and_texts
from app.core.ocr.corrector import OfflineOCRCorrector

class LocalOCRRunner:
    def __init__(self, detector: BaseTextDetector, recognizer: BaseTextRecognizer | None, ocr_config: dict, render_config: dict, corrector: OfflineOCRCorrector, log_callback=None):
        self.detector = detector
        self.recognizer = recognizer
        self.ocr_config = ocr_config
        self.render_config = render_config
        self.corrector = corrector
        self.log_callback = log_callback

    def run(self, ctx: PageContext):
        image = get_original_image(ctx)
        if image is None:
            return

        h, w = image.shape[:2]
        det_image = image.copy()
        
        # 1. Preprocess
        det_image = OCRPreprocessor.preprocess(image, self.ocr_config)
        
        # 2. Auto Rotate
        if self.ocr_config.get('det_auto_rotate') and self.recognizer:
            best_angle = OCRRotator.detect_orientation(det_image, self.recognizer, self.detector)
            if best_angle != 0:
                if self.log_callback:
                    self.log_callback("OCR", f"Auto-Rotate: Phát hiện ảnh bị xoay, tự động xoay lại {best_angle} độ.")
                image = OCRRotator.apply_rotation(image, best_angle)
                det_image = OCRRotator.apply_rotation(det_image, best_angle)
                h, w = image.shape[:2]
                set_original_image(ctx, image)
                
        # 3. Detection
        raw_bboxes, raw_polygons = self.detector.detect(det_image)
        
        if not raw_polygons:
            raw_polygons = [[] for _ in raw_bboxes]
        bundled_boxes = [box + [poly] for box, poly in zip(raw_bboxes, raw_polygons)]
        
        ui_direction = self.render_config.get("direction", "Horizontal: Right-to-Left")
        dir_map = {
            "Horizontal: Right-to-Left": "rtl_ttb",
            "Horizontal: Left-to-Right": "ltr_ttb",
            "Vertical: Right-to-Left": "ttb_rtl",
            "Vertical: Left-to-Right": "ttb_ltr"
        }
        direction = dir_map.get(ui_direction, "rtl_ttb")
        bundled_boxes = sort_comic_text_boxes(bundled_boxes, direction=direction, image_width=w, image_height=h) # type: ignore
        
        bboxes = [b[:4] for b in bundled_boxes]
        polygons = [b[4] for b in bundled_boxes]
        texts = []
        
        prob_thresh = float(self.ocr_config.get('prob', 0.0) or 0.0)
        use_rotation = bool(self.ocr_config.get('det_rotate', False))
        
        # 4. Cropping & Recognition
        if self.recognizer and bboxes:
            for i, box in enumerate(bboxes):
                poly = polygons[i]
                crop = OCRCropper.crop(image, box, poly, use_rotation=use_rotation)
                text = OCRRecognizer.recognize(crop, self.recognizer, prob_thresh)
                texts.append(text)
                    
        # 5. Correction
        texts = self.corrector.correct(texts, image)
        
        # 6. Filtering
        bboxes, texts = OCRFilter.apply(bboxes, texts, self.ocr_config)
        
        # 7. Merge Nearby
        if self.ocr_config.get('merge_nearby_boxes', False):
            merged_bboxes, merged_texts = merge_nearby_boxes_and_texts(bboxes, texts, w, h)
            merged_texts = self.corrector.correct(merged_texts)
        else:
            merged_bboxes, merged_texts = bboxes, texts
        
        ctx.raw_bboxes = bboxes
        ctx.bboxes = merged_bboxes
        ctx.original_texts = merged_texts
        ctx.translated_texts = [""] * len(merged_texts)
        
        if self.log_callback:
            self.log_callback("OCR", f"Detector tìm thấy và gom lại thành {len(merged_bboxes)} bong bóng chữ.")
