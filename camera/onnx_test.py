import cv2
import numpy as np
import onnxruntime as ort
from collections import deque
import cv2
import numpy as np
from PIL import Image

from picamera2 import Picamera2

picam2 = Picamera2()

config = picam2.create_preview_configuration(main={"size": (640, 480)})
picam2.configure(config)
picam2.start()


IMG_SIZE = 224  # must match training / export
# tfm = classify_transforms(size=IMG_SIZE)


def get_face_detector():
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    return face_cascade


def detect_largest_face(gray, face_cascade):
    faces = face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
    )

    if len(faces) == 0:
        return None
    
    # Choose the largest detected face (area)
    x, y, w, h = max(faces, key=lambda b: b[2] * b[3])
    return x, y, w, h


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





# Load ONNX model
onnx_model_path = r"model\best.onnx"
session = ort.InferenceSession(onnx_model_path)

# Get input/output info
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name
input_shape = session.get_inputs()[0].shape

print(f"Model input name: {input_name}")
print(f"Model input shape: {input_shape}")
print(f"Model output name: {output_name}")

# Determine input size
input_size = (input_shape[2], input_shape[3]) if len(input_shape) == 4 else (224, 224)
print(f"Using input size: {input_size}")

# Define emotion labels (adjust based on your training)
# To get the exact labels from your original model, run:
# from ultralytics import YOLO
# model = YOLO("runs/classify/train3/weights/best.pt")
# print(model.names)
emotion_labels = {
    0: "angry",
    1: "disgust", 
    2: "fear",
    3: "happy",
    4: "neutral",
    5: "sad",
    6: "suprise"
}


face_cascade = get_face_detector()
predictions = deque(maxlen=5)

label_txt = ""
conf_txt = "0.00"

while True:
    frame = picam2.capture_array()
    # if not frame:
    #     break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    bbox = detect_largest_face(gray, face_cascade)

    if bbox is not None:
        x, y, w, h = bbox

        pad = int(0.15 * max(w, h))
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame.shape[1], x + w + pad)
        y2 = min(frame.shape[0], y + h + pad)

        face_crop = gray[y1:y2, x1:x2]

        if face_crop.size > 0:
            try:
                # Preprocess for ONNX (YOLO style)
                input_tensor = preprocess_for_yolo_classification(face_crop)
                
                # Run inference
                outputs = session.run([output_name], {input_name: input_tensor})
                
                # Process outputs - YOLO classification returns logits
                logits = outputs[0][0]  # Remove batch dimension
                
                # Apply softmax
                exp_logits = np.exp(logits - np.max(logits))  # Subtract max for numerical stability
                probs = exp_logits / np.sum(exp_logits)
                
                # Get top prediction
                top1_idx = np.argmax(probs)
                conf = float(probs[top1_idx])
                label = emotion_labels.get(top1_idx, f"class_{top1_idx}")
                
                predictions.append((label, conf))

                # Smooth predictions over the last N frames
                if len(predictions) > 0:
                    labels = [p[0] for p in predictions]
                    best_label = max(set(labels), key=labels.count)
                    avg_conf = np.mean([p[1] for p in predictions if p[0] == best_label])
                    label_txt = best_label
                    conf_txt = f"{avg_conf:.2f}"
                    
            except Exception as e:
                print(f"Inference error: {e}")

        # Draw bbox
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

        # Put text
        cv2.putText(frame, f"{label_txt} {conf_txt}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2, cv2.LINE_AA)

    cv2.imshow("Emotion Recognition (q to quit)", frame)
    key = cv2.waitKey(1) & 0xFF
    if key == ord("q"):
        break

picam2.stop()
cv2.destroyAllWindows()
