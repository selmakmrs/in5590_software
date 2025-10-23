"""
Real-time Emotion Detection using TensorFlow Lite
Optimized for Raspberry Pi with TFLite interpreter
Requires: pip install opencv-python numpy tflite-runtime (or tensorflow)
"""

import cv2
import numpy as np
import time
import tensorflow as tf
from tensorflow.lite.python import Interpreter
   

class EmotionDetectorTFLite:
    def __init__(self, model_path='model/face_model.tflite'):
        """Initialize TFLite emotion detector"""
        self.emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
        
        # Load TFLite model
        try:
            self.interpreter = Interpreter(model_path=model_path)
            self.interpreter.allocate_tensors()
            
            # Get input and output details
            self.input_details = self.interpreter.get_input_details()
            self.output_details = self.interpreter.get_output_details()
            
            # Get input shape
            self.input_shape = self.input_details[0]['shape']
            self.input_height = self.input_shape[1]
            self.input_width = self.input_shape[2]
            
            print(f"Model loaded successfully!")
            print(f"Input shape: {self.input_shape}")
            print(f"Expected input size: {self.input_width}x{self.input_height}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            print("\nTo get a pre-trained emotion detection model:")
            print("1. Download from: https://github.com/oarriaga/face_classification")
            print("2. Or convert your own Keras model to TFLite")
            print("3. Place 'emotion_model.tflite' in the same directory")
            raise
        
        # Initialize face detector (Haar Cascade - very lightweight)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
    
    def preprocess_face(self, face_img):
        """Preprocess face image for model input"""
        # Resize to model input size
        face_img = cv2.resize(face_img, (self.input_width, self.input_height))
        
        # Convert to grayscale if needed
        if len(face_img.shape) == 3 and self.input_shape[-1] == 1:
            face_img = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
            face_img = np.expand_dims(face_img, axis=-1)
        
        # Normalize pixel values
        face_img = face_img.astype(np.float32) / 255.0
        
        # Add batch dimension
        face_img = np.expand_dims(face_img, axis=0)
        
        return face_img
    
    def predict_emotion(self, face_img):
        """Predict emotion from face image"""
        # Preprocess
        input_data = self.preprocess_face(face_img)
        
        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        
        # Get output
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        predictions = output_data[0]
        
        # Get emotion probabilities
        emotions = {label: float(pred) for label, pred in zip(self.emotion_labels, predictions)}
        dominant_emotion = max(emotions, key=emotions.get)
        
        return dominant_emotion, emotions


def detect_emotion_realtime(model_path='model/face_model.tflite'):
    """Run real-time emotion detection using Picamera2 frames."""
    detector = EmotionDetectorTFLite(model_path)

    # --- Picamera2 init (fast on Pi 3 B+) ---
    picam2 = Picamera2()
    config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    picam2.start()
    print("\nStarting emotion detection (Picamera2 + TFLite). Press 'q' to quit.")

    fps_start_time = time.time()
    fps_frame_count = 0
    fps = 0

    try:
        while True:
            # Picamera2 returns RGB; convert to BGR for OpenCV drawing and consistency
            frame_rgb = picam2.capture_array()
            frame = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)

            # Face detection uses grayscale
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = detector.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

            for (x, y, w, h) in faces:
                face_roi = frame[y:y+h, x:x+w]

                try:
                    dominant_emotion, emotions = detector.predict_emotion(face_roi)
                    confidence = emotions[dominant_emotion]

                    # Draws on BGR frame
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{dominant_emotion}: {confidence:.2f}",
                                (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

                    top3 = sorted(emotions.items(), key=lambda kv: kv[1], reverse=True)[:3]
                    y_off = y + h + 25
                    for lab, p in top3:
                        cv2.putText(frame, f"{lab}: {p:.2f}", (x, y_off),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                        y_off += 20
                except Exception as e:
                    print(f"Error processing face: {e}")

            # FPS
            fps_frame_count += 1
            if time.time() - fps_start_time > 1:
                fps = fps_frame_count
                fps_frame_count = 0
                fps_start_time = time.time()

            cv2.putText(frame, f"FPS: {fps} | Faces: {len(faces)}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            cv2.imshow('Emotion Detection (Picamera2)', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        picam2.stop()
        cv2.destroyAllWindows()

def _pick_face(faces):
    sortes_faces = sorted(faces, key=lambda x: x[2]*x[3])
    return sortes_faces[0]


if __name__ == "__main__":
    import sys
    
    # Run real-time detection
    model_path = sys.argv[1] if len(sys.argv) > 1 else 'models/face_model1.tflite'
    detect_emotion_realtime(model_path)