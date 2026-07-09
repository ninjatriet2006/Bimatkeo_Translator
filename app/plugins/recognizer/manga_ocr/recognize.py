"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.manga_ocr.recognize
- RESPONSIBILITY: Thực thi nhận dạng văn bản (OCR) bằng mô hình Manga-OCR.
- CALLED BY: app.plugins.recognizer.manga_ocr.main_impl
- CALLS TO: None
- IN = OUT: Nhận hình ảnh, trả về text và độ tin cậy.
=============================================================================
"""
import numpy as np
import cv2
from PIL import Image

def recognize_text_manga_ocr(processor, model, image_crop: np.ndarray) -> tuple[str, float]:
    if model is None or processor is None:
        return "", 0.0
        
    try:
        import torch
        
        if len(image_crop.shape) == 2:
            img_rgb = cv2.cvtColor(image_crop, cv2.COLOR_GRAY2RGB)
        elif image_crop.shape[2] == 4:
            img_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGRA2RGB)
        else:
            img_rgb = cv2.cvtColor(image_crop, cv2.COLOR_BGR2RGB)
            
        pil_img = Image.fromarray(img_rgb)
        
        pixel_values = processor(images=pil_img, text="", return_tensors="pt").pixel_values
        device = next(model.parameters()).device
        pixel_values = pixel_values.to(device)
        
        with torch.no_grad():
            generated_ids = model.generate(pixel_values)
            
        generated_text = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
        
        return generated_text.strip(), 1.0
    except Exception as e:
        return f"[Lỗi OCR: {e}]", 0.0
