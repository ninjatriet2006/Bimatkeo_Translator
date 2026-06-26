def merge_nearby_boxes_and_texts(bboxes, texts, image_width, image_height):
    clusters = []
    for i, box in enumerate(bboxes):
        text = texts[i]
        matched_cluster_idx = -1
        
        for j, cluster in enumerate(clusters):
            c_box = cluster["box"]
            dx = max(0, max(c_box[0], box[0]) - min(c_box[2], box[2]))
            dy = max(0, max(c_box[1], box[1]) - min(c_box[3], box[3]))
            
            w1, h1 = box[2] - box[0], box[3] - box[1]
            w2, h2 = c_box[2] - c_box[0], c_box[3] - c_box[1]
            min_w = min(w1, w2)
            min_h = min(h1, h2)
            
            max_gap_x = max(20, int(min_w * 0.5))
            max_gap_y = max(20, int(min_h * 0.8))
            
            print(f"box={box}, c_box={c_box}, dx={dx}, dy={dy}, max_x={max_gap_x}, max_y={max_gap_y}")
            
            if dx <= max_gap_x and dy <= max_gap_y:
                matched_cluster_idx = j
                break
                
        if matched_cluster_idx != -1:
            c = clusters[matched_cluster_idx]
            c_box = c["box"]
            c["box"] = [
                min(c_box[0], box[0]),
                min(c_box[1], box[1]),
                max(c_box[2], box[2]),
                max(c_box[3], box[3])
            ]
            c["texts"].append(text)
        else:
            clusters.append({
                "box": list(box),
                "texts": [text]
            })
            
    return [c["box"] for c in clusters], [" ".join(c["texts"]) for c in clusters]

bboxes = [
    [328, 77, 853, 347],
    [131, 626, 484, 777],
    [653, 998, 945, 1222],
    [78, 1551, 471, 1719]
]
texts = ["1", "2", "3", "4"]
print(merge_nearby_boxes_and_texts(bboxes, texts, 1000, 2000))
