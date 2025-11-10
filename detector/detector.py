import cv2
import numpy as np
import tensorflow as tf
from tensorflow.lite.python.interpreter import Interpreter
from picamera2 import Picamera2



class DETECTOR:
    """
    Handles camera input and face/emotion detection
    Optimized for Raspberry Pi 3 B+
    """
    
    def __init__(self, resolution=(320, 240), 
                 model_path=r"/home/pi/in5590_software/detector/model/face_model1.tflite",
                 yunet_path=r"/home/pi/in5590_software/detector/model/face_detection_yunet_2023mar.onnx"):
        """
        Initialize camera and detection models
        
        Args:
            resolution: (width, height) tuple
        """
        self.emotion_labels = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']

        # Load model
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

            print("Model loaded successfully!")
            print("Input shape: ", self.input_shape)
            print("Input details: ", self.input_details)
            print("Output details: ", self.output_details)

        except Exception as e:
            print("Error loading model: ", e)
            raise

        # Initialize face detector (Haar Cascade - very lightweight)
        self.face_cascade = cv2.CascadeClassifier(
            '/usr/share/opencv4/haarcascades/haarcascade_frontalface_default.xml'
        )

        self.resolution = resolution

         # === YuNet face detector ===
        self.face_detector = cv2.FaceDetectorYN_create(
            yunet_path,
            "",
            self.resolution,      # (w, h)
            score_threshold=0.7,  # can tune
            nms_threshold=0.3,
            top_k=1               # we only care about the main face
        )



    
    # === Camera Control ===
    def start_camera(self):
        """Initialize and start camera capture"""
        self.picam2 = Picamera2()

        # Configure for video capture
        config = self.picam2.create_preview_configuration(
        main={"size": self.resolution, "format": "RGB888"}
        )
        self.picam2.configure(config)
        
        # Start the camera
        self.picam2.start()
        
        # Get frame dimensions
        self.frame_width = self.resolution[0]
        self.frame_height = self.resolution[1]

        # Open face detector
        self.face_detector.setInputSize(self.resolution)
        
        print("Picamera2 started successfully!")

    
    def stop_camera(self):
        """Release camera resources"""
        if hasattr(self, "picam2"):
            self.picam2.stop()
            self.picam2.close()
        cv2.destroyAllWindows()
    
    def get_frame(self):
        """
        Capture single frame from camera
        
        Returns:
            frame: numpy array (BGR image)
        """
        try:
            frame = self.picam2.capture_array()
            # frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print("Failed to grab frame: ", e)
            return None 

    def get_frame_size(self):
        """
        Get current frame dimensions
        
        Returns:
            (width, height): tuple
        """
        return (self.frame_width, self.frame_height)
    
    # === Face Detection ===
    def detect_face(self, frame):
        """
        Detect face in frame using YuNet.

        Args:
            frame: BGR image

        Returns:
            (x, y, w, h) or None
        """
        if frame is None:
            return None

        h, w = frame.shape[:2]

        # Resize to detector input size if needed
        if (w, h) != self.resolution:
            frame_resized = cv2.resize(frame, self.resolution)
        else:
            frame_resized = frame

        # YuNet expects BGR, which we already have
        retval, faces = self.face_detector.detect(frame_resized)

        if faces is None or len(faces) == 0:
            return None

        # faces shape: (N, 15) -> [x, y, w, h, score, ...]
        # We asked for top_k=1, so faces[0] is the best one.
        x, y, w, h = faces[0][:4].astype(int)

        # If we resized, coords are already in resized space (same as self.resolution),
        # which is also what you use for drawing etc., so no remapping needed.
        return (x, y, w, h)

    
    def is_face_centered(self, face, threshold=0.2):
        """
        Check if face is roughly centered in frame
        
        Args:
            face_data: Face detection result
            threshold: How close to center (0.0-1.0)
            
        Returns:
            bool: True if face is centered
        """
        if face is None:
            return False
        
        x, y, w, h = face

        frame_center_x = self.frame_width // 2
        frame_center_y = self.frame_height // 2

        face_center_x = x + w / 2
        face_center_y = y + h / 2

        x_distance = abs(frame_center_x - face_center_x) / (self.frame_width / 2)
        y_distance = abs(frame_center_y - face_center_y) / (self.frame_height / 2)

        return x_distance <= threshold and y_distance <= threshold

        

    
    def is_face_close(self, face_data, min_size=100):
        """
        Check if face is close enough for emotion detection
        
        Args:
            face_data: Face detection result
            min_size: Minimum face width in pixels
            
        Returns:
            bool: True if face is close enough
        """
        pass
    
    # === Emotion Detection ===
    def detect_emotion(self, frame, face):
        """
        Detect emotion from frame or face region
        
        Args:
            frame: Input image
            face_data: Optional face detection data (for cropping)
            
        Returns:
            (emotion, confidence): tuple
                emotion: str ('happy', 'sad', 'angry', 'surprise', 'neutral', etc.)
                confidence: float (0.0-1.0)
        """
        x, y, w, h = face
        face_frame = frame[y:y+h, x:x+w]

        input_data = self._pre_process_face(face_frame)
        
        # Run inference
        self.interpreter.set_tensor(self.input_details[0]['index'], input_data)
        self.interpreter.invoke()
        
        # Get output
        output_data = self.interpreter.get_tensor(self.output_details[0]['index'])
        predictions = output_data[0]
        
        # Get emotion probabilities
        emotions = {label: float(pred) for label, pred in zip(self.emotion_labels, predictions)}
        dominant_emotion = max(emotions, key=emotions.get)
        emotion_prob = emotions[dominant_emotion]

        return dominant_emotion, emotion_prob

    def _pre_process_face(self, face_frame):
        # Resize to model input_size
        face_frame = cv2.resize(face_frame,(self.input_width, self.input_height), interpolation=cv2.INTER_LINEAR)

        # Convert to grayscale
        if len(face_frame.shape) == 3 and self.input_shape[-1] == 1:
            face_frame = cv2.cvtColor(face_frame, cv2.COLOR_BGR2GRAY)
            face_frame = np.expand_dims(face_frame, axis=-1)

        # Normalize pixel values
        face_frame = face_frame.astype(np.float32) / 255.0

        # Added batch dimention
        face_frame = np.expand_dims(face_frame, axis=0)

        return face_frame


        

    
    
    def get_all_emotions(self, frame, face_data=None):
        """
        Get confidence scores for all emotions
        
        Returns:
            dict: {'happy': 0.8, 'sad': 0.1, 'angry': 0.05, ...}
        """
        pass
    
    # === Utility ===
    def preprocess_face(self, frame, bbox):
        """
        Extract and preprocess face region for emotion detection
        
        Args:
            frame: Full image
            bbox: (x, y, w, h) bounding box
            
        Returns:
            preprocessed_face: Ready for model input
        """
        pass
    
    def draw_debug_info(self, frame, face_data=None, emotion=None):
        """
        Draw bounding boxes, labels for debugging
        
        Args:
            frame: Image to draw on
            face_data: Face detection result
            emotion: (emotion_name, confidence) tuple
            
        Returns:
            frame: Annotated image
        """
        pass
    
    def get_fps(self):
        """
        Get current detection FPS
        
        Returns:
            float: Frames per second
        """
        pass
    
    def cleanup(self):
        """Clean up resources"""
        pass



    # ==== Drawing functions for testing purpes ======
    def draw_face_box(self, frame, face):
        """For testing draw face around the captured face"""
        x, y, w, h = face
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 255,0), 2)

    def draw_emotion_text(self, frame, face, emotion, emotion_prob):
        x, y, w, h = face

        text = f"{emotion}: {emotion_prob:.2f}"
        cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
    


