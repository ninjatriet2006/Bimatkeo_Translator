import onnxruntime as ort
import numpy as np

model_path = "models/Inpainter/MangaInpaintV3/model.onnx"
try:
    session = ort.InferenceSession(model_path, providers=['CPUExecutionProvider'])
    inputs = session.get_inputs()
    outputs = session.get_outputs()
    print("Inputs:")
    for i in inputs:
        print(f" - {i.name}: {i.shape} ({i.type})")
    print("Outputs:")
    for o in outputs:
        print(f" - {o.name}: {o.shape} ({o.type})")
except Exception as e:
    print(e)
