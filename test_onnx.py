import onnx
try:
    model = onnx.load("models/Inpainter/Lama_ONNX/lama_fp32.onnx")
    for ipt in model.graph.input:
        shape = []
        for dim in ipt.type.tensor_type.shape.dim:
            if dim.HasField("dim_value"):
                shape.append(str(dim.dim_value))
            elif dim.HasField("dim_param"):
                shape.append(dim.dim_param)
            else:
                shape.append("?")
        print(f"Input {ipt.name}: shape {shape}")
except Exception as e:
    print(e)
