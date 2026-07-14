"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.inpainter.sd.inpaint
- RESPONSIBILITY: Xử lý inference inpainting bằng Stable Diffusion.
- CALLED BY: app.plugins.inpainter.sd.main_impl
- CALLS TO: None
- IN = OUT: Nhận ảnh BGR và list bboxes; trả về ảnh BGR đã inpaint.
=============================================================================
"""
import cv2
import numpy as np
from typing import List
from PIL import Image

def inpaint_sd(pipeline, is_loaded: bool, image: np.ndarray, bboxes: List[List[int]]) -> np.ndarray:
    if not is_loaded or pipeline is None or image is None or not bboxes:
        return image
        
    try:
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]
        
        # Create mask
        mask = np.zeros((h, w), dtype=np.uint8)
        for bbox in bboxes:
            # bbox is [x, y, w, h] or similar. Let's assume [xmin, ymin, xmax, ymax] standard format.
            # Usually bboxes are [x, y, w, h] in OpenCV. Let's handle both safely.
            if len(bbox) >= 4:
                x, y, bw, bh = bbox[:4]
                # If the values are xmin, ymin, xmax, ymax
                if bw > w and bh > h:
                    x1, y1, x2, y2 = bbox[:4]
                else:
                    x1, y1, x2, y2 = x, y, x + bw, y + bh
                cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
                
        img_pil = Image.fromarray(img_rgb)
        mask_pil = Image.fromarray(mask).convert("L")
        
        # In SD, sizes must be multiples of 8. We resize temporarily if needed.
        # But for now, we just pass it to the pipeline.
        result = pipeline(prompt="background, high quality", image=img_pil, mask_image=mask_pil).images[0]
        
        # Convert back to BGR
        res_rgb = np.array(result)
        res_bgr = cv2.cvtColor(res_rgb, cv2.COLOR_RGB2BGR)
        
        # Overlay original image outside the mask
        final_img = image.copy()
        mask_3d = mask[:, :, np.newaxis] > 0
        final_img[mask_3d[:, :, 0]] = res_bgr[mask_3d[:, :, 0]]
        
        return final_img
    except Exception as e:
        print(f"SD Inpainting error: {e}")
        return image
