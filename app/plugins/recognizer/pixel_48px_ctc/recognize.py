"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.pixel_48px_ctc.recognize
- RESPONSIBILITY: Tiền xử lý, chạy inference ONNX và hậu xử lý CTC decoder.
- CALLED BY: app.plugins.recognizer.pixel_48px_ctc.main_impl
- CALLS TO: None
- IN = OUT: Nhận session, hình ảnh, từ điển; trả về text và độ tin cậy.
=============================================================================
"""
import numpy as np
import cv2
import math

def _resize_norm_img(img, img_h=48):
    h, w = img.shape[:2]
    ratio = w / float(h)
    img_w = math.ceil(img_h * ratio)
    
    resized_img = cv2.resize(img, (img_w, img_h))
    resized_img = resized_img.astype('float32')
    resized_img = (resized_img - 127.5) / 127.5
    
    resized_img = resized_img.transpose((2, 0, 1))
    tensor = np.expand_dims(resized_img, axis=0)
    return tensor
    
def _ctc_greedy_decoder(preds, character_dict):
    preds_idx = preds.argmax(axis=2)[0]
    preds_prob = preds.max(axis=2)[0]
    
    char_list = []
    conf_list = []
    for i in range(len(preds_idx)):
        idx = preds_idx[i]
        if idx != 0 and not (i > 0 and preds_idx[i - 1] == idx):
            if idx < len(character_dict):
                char = character_dict[idx]
                if char == "<SP>":
                    char = " "
                char_list.append(char)
                conf_list.append(preds_prob[i])
                
    conf = float(np.mean(conf_list)) if conf_list else 0.0
    return ''.join(char_list), conf

def recognize_text_pixel_48px_ctc(session, input_name, character_dict, image_crop: np.ndarray) -> tuple[str, float]:
    if session is None: 
        return "", 0.0
    
    tensor = _resize_norm_img(image_crop, img_h=48)
    
    outputs = session.run(None, {input_name: tensor})
    char_logits = outputs[0]
    
    text, conf = _ctc_greedy_decoder(char_logits, character_dict)
    return text, conf
