from detector import DETECTOR
import onnxruntime as ort
import numpy as np
import cv2

detector = DETECTOR()
detector.start_camera()

onnx_model_path = r'detector/model/best.onnx'

sess_options = ort.SessionOptions()
sess_options.intra_op_num_threads = 1  # Pi has few cores, avoid overhead
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL

session = ort.InferenceSession(
    onnx_model_path,
    sess_options,
    providers=["CPUExecutionProvider"]
)

# Get input/output info
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name
input_shape = session.get_inputs()[0].shape

emotion_labels = {
    0: "angry",
    1: "disgust", 
    2: "fear",
    3: "happy",
    4: "neutral",
    5: "sad",
    6: "suprise"
}


def preprocess_for_yolo_classification(image, input_size=(224, 224)):
    """
    Reproduce ultralytics.data.augment.classify_transforms() using OpenCV/NumPy.

    Steps:
    - convert gray -> BGR (if needed)
    - BGR -> RGB
    - Resize so the *shortest* edge == size, keep aspect ratio
    - Center-crop to (size, size)
    - Convert to float32, divide by 255
    - HWC -> CHW and add batch dimension
    """
    size = input_size[0]  # assuming square, like 224x224

    # 1) make sure we have 3 channels
    if len(image.shape) == 2 or image.shape[2] == 1:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    # 2) BGR -> RGB
    img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    h, w = img.shape[:2]

    # 3) resize shortest side to `size`, keep aspect ratio
    if h < w:
        new_h = size
        new_w = int(round(w * size / h))
    else:
        new_w = size
        new_h = int(round(h * size / w))

    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # 4) center crop to size x size (like torchvision.CenterCrop)
    y1 = max(0, (new_h - size) // 2)
    x1 = max(0, (new_w - size) // 2)
    img = img[y1:y1 + size, x1:x1 + size]

    # 5) ToTensor(): HWC uint8 [0,255] -> float32 CHW [0,1]
    img = img.astype(np.float32) / 255.0

    # 6) HWC -> CHW and add batch dim
    img = np.transpose(img, (2, 0, 1))   # [C, H, W]
    img = np.expand_dims(img, axis=0)    # [1, C, H, W]

    return img

while True:
    frame = detector.get_frame()

    if frame is None:
        break
    face = detector.detect_face(frame)

    if face is not None:
        x, y, w, h = face
        pad = int(0.15 * max(w, h))
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame.shape[1], x + w + pad)
        y2 = min(frame.shape[0], y + h + pad)
        face_crop = face[y1:y2, x1:x2]

        detector.draw_face_box(frame,face)
        if detector.is_face_centered(face):
            try: 
                input_tensor = preprocess_for_yolo_classification(face_crop)
                outputs = session.run([output_name], {input_name: input_tensor})
                logits = outputs[0][0]
                exp_logits = np.exp(logits - np.max(logits))
                probs = exp_logits / np.sum(exp_logits)
                top1_idx = int(np.argmax(probs))
                conf = float(probs[top1_idx])
                label = emotion_labels.get(top1_idx, f"class_{top1_idx}")
                # predictions.append((label, conf))
                detector.draw_emotion_text(frame,face,label,conf)
            except Exception as e:
                print("Error : ", e)

    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1)
    if key == ord('q'):
        break

detector.stop_camera()