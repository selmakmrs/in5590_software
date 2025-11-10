from enum import Enum
import threading
import queue
import time
import cv2
from collections import deque

from body import BODY
from oled import OLED
from detector import DETECTOR

EMOTIONS = {
    "happy" : 0.8,
    "angry" : 0.4,
}

class RobotState(Enum):
    IDLE = "idle"
    TRACKING = "tracking"
    EMOTION = "emotion"
    TRANSITION = "transition"

class Robot:
    def __init__(self):
        self.detector = DETECTOR()
        self.body = BODY()
        # self.oled = OLED()
        
        # State management
        self.current_state = RobotState.IDLE
        self.previous_state = None
        self.current_emotion = None
        
        # Thread-safe queues for communication
        self.face_queue = queue.Queue(maxsize=1)
        self.emotion_queue = queue.Queue(maxsize=1)
        
        # Control flags
        self.running = True
        self.face_detected = False
        self.face_position = None  # (x, y) coordinates

        # Emotion confidence system
        self.emotion_history = deque(maxlen=5)
        self.emotion_confidence_threshold = 0.7
        self.min_consitent_frames = 3  # Require 3 consitent detections
        
        # Timing parameters
        self.emotion_duration = 6.0  # How long to hold emotion
        self.idle_transition_time = 2.0
        self.last_face_time = 0
        self.emotion_start_time = 0


        # Threads
        self.threads = []
        
    def start(self):
        """Start all threads"""

        self.detector.start_camera()
        self.body.start()
        # self.oled.start()

        threads = [
            threading.Thread(target=self._vision_loop, name="Vision"),
            # threading.Thread(target=self._oled_loop, name="Oled"),
            threading.Thread(target=self._state_loop, name="State loop"),
            threading.Thread(target=self._body_loop, name = "Body")
            
        ]

        for thread in threads:
            # thread.daemon = True
            thread.start()
            self.threads.append(thread)
            

        print("Robot started successfully!...")



    #----------------------------------------------#
    #--------- Running Loops Functions ------------#
    #----------------------------------------------#


    def _vision_loop(self):
        """Continuously capture and analyze frames"""
        print("Starting vision loop ...")
        while self.running:
            try:
                if self.current_state != RobotState.EMOTION:
                    # Get frame from camera
                    frame = self.detector.get_frame()
                    
                    # Detect face
                    face = self.detector.detect_face(frame)
                    
                    if face is not None:
                        self.detector.draw_face_box(frame,face)
                        self.face_detected = True
                        self.face_position = face[:2]
                        
                        # Update face position for tracking
                        if self.detector.is_face_centered(face):
                            emotion, confidence = self.detector.detect_emotion(frame, face)

                            self.detector.draw_emotion_text(frame,face,emotion,confidence)
                            
                            if not self.face_queue.full():
                                try:
                                    self.face_queue.get_nowait()
                                except queue.Empty:
                                    pass
                                self.face_queue.put(face)
                        
                        if self.detector.is_face_centered(face):
                            emotion, confidence = self.detector.detect_emotion(frame,face)
                            self._proccess_emotion_detection(emotion,confidence)

                        else:
                            self.emotion_history.clear()

                    else:
                        self.face_detected = False
                        self.emotion_history.clear()

                key = cv2.waitKey(1)
                if key == ord('q'):
                    break

                cv2.imshow("Frame", frame)
            except Exception as e:
                print("Error in vision loop: ", e)
                raise e


        print("Ending vision loop ...")
        

            

    def _proccess_emotion_detection(self, emotion, confidence):
        """Proccess emotion detection with confidance checking"""
        if emotion in EMOTIONS and confidence > EMOTIONS[emotion]:
            # Add to history
            self.emotion_history.append((emotion, confidence, time.time()))

            # Clear old entry (older than 2 seconds)
            current_time = time.time()
            self.emotion_history = deque(
                [e for e in self.emotion_history
                 if current_time - e[2] < 2.0],
                 maxlen=self.min_consitent_frames*2
            )

            # Check for consistent emotion
            if len(self.emotion_history) > self.min_consitent_frames:
                emotions = [e[0] for e in list(self.emotion_history)[-self.min_consitent_frames:]]

                # Check if all recent emotions are the same
                if all(e == emotions[0] for e in emotions):
                    consistent_emotion = emotions[0]
                    avg_confidence = sum(e[1] for e in list(self.emotion_history)[-self.min_consitent_frames:]) / self.min_consitent_frames
                    # print(f"🎭 Consistent emotion detected: {consistent_emotion} (confidence: {avg_confidence:.2f})")

                
                    if not self.emotion_queue.full():
                        try:
                            self.emotion_queue.get_nowait()
                        except queue.Empty:
                            pass
                        self.emotion_queue.put(consistent_emotion)


    def _oled_loop(self):
        print("Starting OLED thread ...")

        while self.running:
            try:
                if self.current_state == RobotState.EMOTION and self.current_emotion in EMOTIONS:
                    print("Starting emotion sequence for: ", self.current_emotion)
                    self.oled.run_emotion(self.current_emotion)
                    self.current_emotion = None
                

                self.oled.update()
                # time.sleep(0.02)
            except Exception as e:
                print("Error in oled: ", e)



    def _state_loop(self):
        """Main state machine - decides what state to be in"""
        print("Starting state loop ... ")
        while self.running:
            # print("Current state: ", self.current_state)
            if self.current_state == RobotState.IDLE:
                # Check if face detected
                if self.face_detected:
                    self._change_state(RobotState.TRACKING)
                # Otherwise stay in idle
                
            elif self.current_state == RobotState.TRACKING:
                # Check if face lost
                if not self.face_detected:
                    self._change_state(RobotState.IDLE)
                
                # Check if emotion detected
                elif not self.emotion_queue.empty():
                    emotion = self.emotion_queue.get()
                    self.current_emotion = emotion
                    self.emotion_start_time = time.time()
                    self._change_state(RobotState.EMOTION)
                    
            elif self.current_state == RobotState.EMOTION:
                # Hold emotion for duration
                elapsed = time.time() - self.emotion_start_time
                
                if elapsed >= self.emotion_duration:
                    # Return to previous state
                    if self.face_detected:
                        self._change_state(RobotState.TRACKING)
                    else:
                        self._change_state(RobotState.IDLE)
            
            time.sleep(0.05)  # Fast decision loop

    def _change_state(self, new_state):
        """Handle state transitions"""
        
        if new_state != self.current_state:
            print(f"State: {self.current_state.value} -> {new_state.value}")
            self.previous_state = self.current_state
            self.current_state = new_state
            
            # Trigger transition animations
            # self.current_state = RobotState.TRANSITION
            # After transition completes, move to new_state

    def _body_loop(self):
        """Control body movements based on state"""
        while self.running:
            
            if self.current_state == RobotState.IDLE:
                # Run idle sequence (look around, small movements)
                self.body.idle_sequence()
                
            elif self.current_state == RobotState.TRACKING:
                # Follow face position
                if not self.face_queue.empty():
                    face_data = self.face_queue.get()
                    # target_position = face_data['position']
                    displacement = self._find_face_displacement(face_data)
                    self.body.track_position(displacement)
                
            elif self.current_state == RobotState.EMOTION:
                print("Emotion State :", self.current_emotion())
    #             # Perform emotion gesture
    #             self.body.emotion_sequence(self.current_emotion)
                
            time.sleep(0.02)  # Smooth motion control


    def _find_face_displacement(self, face):
        x, y, fw, fh = face

        frame_center_x = 320 // 2
        face_center_x = x + fw // 2

        displacement = (face_center_x - frame_center_x) / frame_center_x

        return displacement
    