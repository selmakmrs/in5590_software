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
        self.state_lock = threading.Lock()
        self.current_state = RobotState.IDLE
        self.requested_state = None
        self.current_emotion = None
        
        # Thread-safe queues for communication
        self.face_queue = queue.Queue(maxsize=1)
        self.emotion_queue = queue.Queue(maxsize=1)
        
        # Control flags
        self.control_lock = threading.Lock()
        self.running = True
        self.face_detected = False
        self.face_position = None  # (x, y) coordinates
        self.sequence_running = False
        self.sequence_lock = threading.Lock()

        # Emotion confidence system
        self.emotion_history = deque(maxlen=5)
        self.emotion_confidence_threshold = 0.7
        self.min_consitent_frames = 3  # Require 3 consitent detections
        
        # Timing parameters
        self.emotion_duration = 6.0  # How long to hold emotion
        self.idle_transition_time = 2.0
        self.last_face_time = 0
        self.emotion_start_time = 0
        self.state_cooldown = 0.5
        self.last_state_change = 0

        # Threads
        self.threads = []
        
    def start(self):
        """Start all threads"""

        print("Starting Robot ... ")
        self.detector.start_camera()
        self.body.start()
        # self.oled.start()

        threads = [
            threading.Thread(target=self._vision_loop, name="Vision", daemon=True),
            # threading.Thread(target=self._oled_loop, name="Oled"),
            threading.Thread(target=self._state_loop, name="State loop", daemon=True),
            threading.Thread(target=self._body_loop, name = "Body",daemon=True)   
        ]

        for thread in threads:
            thread.start()
            self.threads.append(thread)
            
        print("Robot started successfully!")

    def close(self):
        """Shutdown Robot"""
        print("Shutting down robot ... ")
        self.running = False

        # Wait for threads to finish
        for thread in self.threads:
            thread.join(timeout=2.0)
            
        self.body.close()
        self.detector.cleanup()
        print("Robot Shutdown complete")

    #----------------------------------------------#
    #-------------- State Managment ---------------#
    #----------------------------------------------#

    def _get_state(self):
        """Thread-safe state getter"""
        with self.state_lock:
            return self.current_state
        
    def _request_state_change(self, new_state):
        """Request a state change """
        with self.state_lock:
            if new_state != self.current_state:
                self.requested_state = new_state
                return True
        return False
    
    def _can_change_state(self):
        """Check is state can change"""
        with self.sequence_lock:
            sequence_done = not self.sequence_running

        time_ok = (time.time() - self.last_state_change) <= self.state_cooldown
        return sequence_done and time_ok
    
    def _execute_state_change(self, new_state):
        """Changes the state"""
        with self.state_lock:
            if new_state != self.current_state:
                print(f"State : {self.current_state.value} -> {new_state.value}")
                self.current_state = new_state
                self.requested_state = None
                self.last_state_change = time.time()
                return True
        return False
    
    def _set_sequence_running(self, running):
        """Thread-safe sequence flag setter"""
        with self.sequence_lock:
            self.sequence_running = running

    def _is_sequence_running(self):
        """Thread-safe sequence flag getter"""
        with self.sequence_lock:
            return self.sequence_running

    def _set_face_detection(self, face):
        """Thread-safe face detection flag setter"""
        with self.control_lock:
            self.face_detected = (face is not None)
            if self.face_detected:
                self.last_face_time = time.time()
            
    def _get_face_detected(self):
        """Thread-safe face detected flag getter"""
        with self.control_lock:
            return self.face_detected    

    #----------------------------------------------#
    #--------- Running Loops Functions ------------#
    #----------------------------------------------#


    def _vision_loop(self):
        """Continuously capture and analyze frames"""
        print("Starting vision loop ...")

        while self.running:
            try:
                current_state = self._get_state()

                # Dont process vision during emotion sequence
                if current_state == RobotState.EMOTION:
                    time.sleep(0.1)
                    continue

                # Get frame from camera
                frame = self.detector.get_frame()
                if frame is None:
                    continue

                # Detect face
                face = self.detector.detect_face(frame)

                # Update face detection flage
                self._set_face_detection(face)

                if face is not None:
                    # Draw Debug info
                    self.detector.draw_face_box(frame, face)

                    # Update face queue for for tracking
                    self._update_queue(self.face_queue, face)

                    # Check if face is centered for emorion detection
                    if self.detector.is_face_centered(face):
                        emotion, confidence = self.detector.detect_emotion(frame, face)
                        # Debug info
                        self.detector.draw_emotion_text(frame, face, emotion, confidence)
                        self._proccess_emotion_detection(emotion, confidence)
                    else:
                        self.emotion_history.clear()
                else:
                    self.emotion_history.clear()
            

                # Debug Info
                cv2.imshow("Frame", frame)

                key = cv2.waitKey(1)
                if key == ord('q'):
                    self.running = False
                    break
            
            except Exception as e:
                print(f"Error in vision loop: ", e)
                import traceback
                traceback.print_exc()

        print("Ending vision loop ...")

    def _update_queue(self, q, item):
        """Thread-safe queue update - replace old with new"""
        try:
            q.get_nowait()
        except queue.Empty:
            pass

        try:
            q.put_nowait(item)
        except queue.Full:
            pass

    def _proccess_emotion_detection(self, emotion, confidence):
        """Proccess emotion detection with confidance checking"""
        if emotion not in EMOTIONS or confidence < EMOTIONS[emotion]:
            return
        
        # Add to history
        self.emotion_history.append((emotion, confidence, time.time()))

        # Clear older entries
        current_time = time.time()
        self.emotion_history = deque(
            [e for e in self.emotion_history if current_time - [2] < 2.0],
            maxlen = self.min_consitent_frames * 2
        )

        # Check for consistent emotion
        if len(self.emotion_history) >= self.min_consitent_frames:
            recent_emotions = [e[0] for e in list(self.emotion_history)[-self.min_consitent_frames:]]

            # Check if all recent emotions are the same
            if all(e == recent_emotions[0] for e in recent_emotions):
                consistent_emotion = recent_emotions[0]
                avg_confidence = sum(
                    e[1] for e in list(self.emotion_history)[-self.min_consitent_frames:]
                ) / self.min_consitent_frames

                print(f"Consitent Emotion {consistent_emotion} (conf: {avg_confidence:.2f})")
                self._update_queue(self.emotion_queue, consistent_emotion)

    def _oled_loop(self):
        pass

    def _state_loop(self):
        """Main state machine - decides what state to be in"""
        print("Starting state loop ... ")

        while self.running:
            try: 

                # Get thread-safe state and flag
                current_state = self._get_state()
                face_detected = self._get_face_detected()

                # State decision logic
                if current_state == RobotState.IDLE:
                    if face_detected:
                        self._request_state_change(RobotState.TRACKING)

                elif current_state == RobotState.TRACKING:
                    if not face_detected:
                        # Add grace period before going to idle
                        time_since_face = time.time() - self.last_face_time
                        if time_since_face > 1.0:
                            self._request_state_change(RobotState.IDLE)

                    # Check for emotion detection
                    elif not self.emotion_queue.empty():
                        emotion = self.emotion_queue.get()
                        self.current_emotion = emotion
                        self.emotion_start_time = time.time()
                        self._request_state_change(RobotState.EMOTION)

                elif current_state == RobotState.EMOTION:
                    # Hold Emotion for duration
                    elapsed = time.time() - self.emotion_start_time

                    if elapsed >= self.emotion_duration:
                        # Return to approriate state
                        if face_detected:
                            self._request_state_change(RobotState.TRACKING)
                        else:
                            self._request_state_change(RobotState.IDLE)
                        
                # Execute pending state change if sequence is done
                with self.state_lock:
                    if self.requested_state and self._can_change_state():
                        self._execute_state_change(self.requested_state)
                
                time.sleep(0.5)

            except Exception as e:
                print("Error in state loop: ", e)
                import traceback
                traceback.print_exc()
        
        print("Ending state loop ... ")

    def _body_loop(self):
        """Control body movements based on state"""
        print("Starting body loop ... ")

        while self.running:
            try: 
                current_state = self._get_state()

                if current_state == RobotState.IDLE:
                    # Mark sequence as running
                    self._set_sequence_running(True)

                    # Run idle sequence
                    self.body.idle()

                    # Mark sequence as complete
                    self._set_sequence_running(False)
                
                elif current_state == RobotState.TRACKING:
                    # Check for face data
                    if not self.face_queue.empty():
                        face = self.face_queue.get()
                        displacement = self._find_face_displacement(face)

                        # Track face
                        self.body.track_position(displacement)

                    time.sleep(0.02)


                elif current_state == EMOTIONS:
                    if self.current_emotion:
                        print("Performing Emotion : ", self.current_emotion)


                        self.current_emotion = None

                    time.sleep(0.1)

                else:
                    time.sleep(0.05)


            except Exception as e:
                print("Error in body loop: ", e)
                import traceback
                traceback.print_exc()
                self._set_sequence_running(False)

        print("Ending Body loop ... ")

    def _find_face_displacement(self, face):
        x, y, fw, fh = face

        frame_center_x = 320 // 2
        face_center_x = x + fw // 2

        displacement = (face_center_x - frame_center_x) / frame_center_x

        return displacement
    