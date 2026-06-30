import onnxruntime as ort
try:
    session = ort.InferenceSession("models/Inpainter/Lama_ONNX/lama_fp32.onnx")
    for inp in session.get_inputs():
        print(f"Input {inp.name}: shape {inp.shape}")
except Exception as e:
    print(e)
