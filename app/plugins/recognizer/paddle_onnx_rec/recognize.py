"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.plugins.recognizer.paddle_onnx_rec.recognize
- RESPONSIBILITY: Thực thi nhận dạng văn bản (OCR) bằng Paddle ONNX Rec.
- CALLED BY: app.plugins.recognizer.paddle_onnx_rec.main_impl
- CALLS TO: None
- IN = OUT: Nhận hình ảnh, trả về text và độ tin cậy.
=============================================================================
"""
import numpy as np
import cv2
import math

def _resize_norm_img(img, max_wh_ratio):
    img_c = 3
    img_h = 48
    img_w = int(img_h * max_wh_ratio)
    img_w = max(round(img_w / 32) * 32, 32)
    
    h, w = img.shape[:2]
    ratio = w / float(h)
    if math.ceil(img_h * ratio) > img_w:
        resized_w = img_w
    else:
        resized_w = math.ceil(img_h * ratio)
        
    resized_img = cv2.resize(img, (resized_w, img_h))
    resized_img = resized_img.astype('float32')
    resized_img = (resized_img / 255.0 - 0.5) / 0.5
    
    padding_im = np.zeros((img_h, img_w, img_c), dtype=np.float32)
    padding_im[:, :resized_w, :] = resized_img
    
    padding_im = padding_im.transpose((2, 0, 1))
    padding_im = np.expand_dims(padding_im, axis=0)
    return padding_im
    
def _ctc_greedy_decoder(preds, character_dict):
    preds_idx = preds.argmax(axis=2)[0]
    preds_prob = preds.max(axis=2)[0]
    
    char_list = []
    conf_list = []
    for i in range(len(preds_idx)):
        idx = preds_idx[i]
        if idx != 0 and not (i > 0 and preds_idx[i - 1] == idx):
            if idx < len(character_dict):
                char_list.append(character_dict[idx])
                conf_list.append(preds_prob[i])
                
    text = ''.join(char_list)
    conf = float(np.mean(conf_list)) if conf_list else 0.0
    return text, conf

def recognize_text_paddle_onnx_rec(session, input_name, character_dict, image_crop: np.ndarray) -> tuple[str, float]:
    if session is None: 
        return "Mock OCR Text (Paddle ONNX Rec not loaded)", 0.0
    
    h, w = image_crop.shape[:2]
    max_wh_ratio = max(w * 1.0 / h, 1.0)
    tensor = _resize_norm_img(image_crop, max_wh_ratio)
    
    outputs = session.run(None, {input_name: tensor})
    preds = outputs[0]
    
    text, conf = _ctc_greedy_decoder(preds, character_dict)
    return text, conf
