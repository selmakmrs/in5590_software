from enum import Enum
import select
import sys
import threading
import queue
import time
import cv2
from collections import deque

from body import BODY
from oled import OLED
from detector import DETECTOR
from led import LED

EMOTIONS = {
    "happy" : 0.95,
    "angry" : 0.6,
    "sad"   : 0.5,
    "suprise" : 0.6,
    "fear" : 0.5

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
        self.oled = OLED()
        self.led = LED()
        
        # State management
        self.state_lock = threading.Lock()
        self.current_state = RobotState.IDLE
        self.requested_state = None
        self._current_emotion = None
        
        # Thread-safe queues for communication
        self.face_queue = queue.Queue(maxsize=1)
        self.emotion_queue = queue.Queue(maxsize=1)
        self.command_queue = queue.Queue()
        
        # Control flags
        self.control_lock = threading.Lock()
        self.running = True
        self.face_detected = False
        self.face_position = None  # (x, y) coordinates
        self.sequence_running = False
        self.sequence_lock = threading.Lock()

        # Emotion confidence system
        self.emotion_lock = threading.Lock()
        self.emotion_history = deque(maxlen=5)
        self.emotion_confidence_threshold = 0.7
        self.min_consitent_frames = 2  # Require 3 consitent detections
        
        # Timing parameters
        # self.emotion_duration = 6.0  # How long to hold emotion
        self.idle_transition_time = 2.0
        self.last_face_time = 0
        self.emotion_start_time = 0
        self.state_cooldown = 0.5
        self.last_state_change = 0

        # LED chekck
        self._run_emotion_led = True
        self._run_idle_led = False

        # Threads
        self.threads = []
        
    def start(self):
        """Start all threads"""

        print("Starting Robot ... ")
        self.detector.start_camera()
        self.body.start()
        self.led.start()
        # self.oled.start()

        threads = [
            threading.Thread(target=self._vision_loop, name="Vision", daemon=True),
            threading.Thread(target=self._oled_loop, name="Oled"),
            threading.Thread(target=self._state_loop, name="State loop", daemon=True),
            threading.Thread(target=self._body_loop, name = "Body",daemon=True),
            threading.Thread(target=self._led_loop, name = "LED",daemon=True),
            threading.Thread(target=self._command_loop, name = "Commands",daemon=True)   

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
            
        try: 
            self.body.close()
            self.detector.cleanup()
            self.led.close()
        except Exception as e:
            print(f"Error shutting down ", e)
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

        time_ok = (time.time() - self.last_state_change) >= self.state_cooldown
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

    def _set_current_emotion(self, emotion):
        with self.emotion_lock:
            self._current_emotion = emotion

    @property
    def current_emotion(self):
        with self.emotion_lock:
            return self._current_emotion

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
                    if self.detector.is_face_centered(face):# and self.detector.is_face_close(face):
                        emotion, confidence = self.detector.detect_emotion(frame, face)
                        # Debug info
                        # print(f"Emotion :  {emotion.upper()}  |  {confidence}")
                        self.detector.draw_emotion_text(frame, face, emotion, confidence)
                        self._proccess_emotion_detection(emotion, confidence)
                    else:
                        self.emotion_history.clear()
                else:
                    self.emotion_history.clear()
            

                # Debug Info
                # cv2.imshow("Frame", frame)

                # key = cv2.waitKey(1)
                # if key == ord('q'):
                #     self.running = False
                #     break
            
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
            [e for e in self.emotion_history if current_time - e[2] < 2.0],
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
                if self.emotion_queue.empty():
                    self._update_queue(self.emotion_queue, consistent_emotion)
                    self.emotion_history.clear()

    def _oled_loop(self):
        print("Starting oled loop ... ")
        while self.running:
            try:
                self.oled.update()

                if self.current_state == RobotState.IDLE:
                    self.oled.idle()
                elif self.current_state == RobotState.TRACKING:
                    self.oled.track()

                elif self.current_state == RobotState.EMOTION:
                    self.oled.run_emotion(self._current_emotion)

            except Exception as e:
                print(f"Failed to update oled", e)

    def _state_loop(self):
        """Main state machine - decides what state to be in"""
        print("Starting state loop ... ")

        while self.running:
            try: 

                self._proccess_commands()

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
                        if time_since_face > 10.0:
                            self._request_state_change(RobotState.IDLE)

                    # Check for emotion detection
                    elif not self.emotion_queue.empty():
                        try:
                            emotion = self.emotion_queue.get_nowait()
                            self._set_current_emotion(emotion)
                            self.emotion_start_time = time.time()
                            self._request_state_change(RobotState.EMOTION)
                        except queue.Empty:
                            pass

                elif current_state == RobotState.EMOTION:
                    
                    # if not self._is_sequence_running():
                    #     self._run_emotion_sequence()

                    if (not self._is_sequence_running() and time.time() - self.emotion_start_time >= 4):
                        self._request_state_change(RobotState.IDLE)

                   
                
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
        last_idle_action = time.time()
        idle_action_interval = 3.0 # Perform idle action evry 3 seconds

        while self.running:
            try: 
                current_state = self._get_state()

                if current_state == RobotState.IDLE:

                    if time.time() - last_idle_action >= idle_action_interval:
                        # Mark sequence as running
                        # self._set_sequence_running(True)
                        # Run idle sequence
                        self.body.idle()
                        last_idle_action = time.time()
                        # Mark sequence as complete
                        # self._set_sequence_running(False)
                    
                elif current_state == RobotState.TRACKING:
                    # Check for face data
                    if not self.face_queue.empty():
                        face = self.face_queue.get()
                        if not self._is_face_centered(face):
                            displacement = self._find_face_displacement(face)
                            # Track face
                            self.body.track_position(displacement)

                    


                elif current_state == RobotState.EMOTION:

                    self._set_sequence_running(True)
                    emotion = self._current_emotion
                    
                    if hasattr(self.body, emotion):
                        move = getattr(self.body, emotion)
                        if callable(move):
                            try:
                                move()
                            except Exception as e:
                                print(f"Error while running {emotion} body: {e}\n")
                        else:
                            print(f"'{emotion}' is not a function.\n")

                    self._set_sequence_running(False)
                    

                else:
                    time.sleep(0.05)


            except Exception as e:
                print("Error in body loop: ", e)
                import traceback
                traceback.print_exc()
                self._set_sequence_running(False)

        print("Ending Body loop ... ")

    def _find_face_displacement(self, face):
        return self.detector.find_face_displacement(face)
    
    def _is_face_centered(self, face):
        return self.detector.is_face_centered(face)
    
    def _command_loop(self):
        """Reads command from terminal"""
        print("Command listener started")
        while self.running:
            try:
                # Check if input is available (Unix/Linux)
                if select.select([sys.stdin], [], [], 0.5)[0]:
                    cmd = sys.stdin.readline().strip().lower()
                    if cmd:
                        self._update_queue(self.command_queue, cmd)
            except Exception as e:
                print("Input error: ", e)
                break


    def _led_loop(self):
        while self.running:
            
            if self.current_state == RobotState.EMOTION:
                if self._run_emotion_led:
                    self.led.run_emotion(self._current_emotion)
                    self._run_emotion_led = False
                    self._run_idle_led = True
            else:
                if self._run_idle_led:
                    self.led.run_emotion("idle")
                    self._run_emotion_led = True
                    self._run_idle_led = False
                    

    #--------------------------------------------#
    #---------------- Emotions ------------------#
    #--------------------------------------------#
    def _run_emotion_sequence(self):
        try:
            if self.current_emotion is not None:
                print(f"Running emotion: {self.current_emotion}")

                self._set_sequence_running(True)
                self.oled.run_emotion(self.current_emotion)
                self.led.run_emotion(self.current_emotion)
                match self.current_emotion:
                    case "happy":
                        self.body.happy()
                    case "sad":
                        self.body.sad()
                    case "angry":
                        self.body.angry()
                    case "suprise":
                        self.body.suprise()
                    case "fear":
                        self.body.fear()

                time.sleep(1)
                self.body.idle()
                self.led.default()
                print(f"Emotion sequence {self.current_emotion} complete")
                self._set_current_emotion(None)
                self._set_sequence_running(False)

        except Exception as e:
            print(f"Error running emotion {self.current_emotion}", e)
            self._set_sequence_running(False)

    # ========== Command Center ==================

    def _proccess_commands(self):
        """Procceses commands"""
        while not self.command_queue.empty():
            try:
                cmd = self.command_queue.get_nowait()
                self._execute_command(cmd)
            except queue.Empty:
                break

    def _execute_command(self, cmd):
        self._set_sequence_running(True)

        cmd = cmd.strip()
        print(f"Command {cmd} accepted")

        if cmd in ["stop", "quit", "exit"]:
            self.running = False
            self.close()

        elif cmd == "status":
            print(f"\n=== Robot Status ===")
            print(f"  State: {self.current_state.value}")
            print(f"  Face Detected: {self.face_detected}")
            print(f"  Sequence Running: {self.sequence_running}")
            print(f"  Current Emotion: {self.current_emotion}")
            print(f"===================\n")

        elif cmd in EMOTIONS:
            print("Triggered Emotion: ", cmd)
            self._set_current_emotion(cmd)
            self.emotion_start_time = time.time()
            self._request_state_change(RobotState.EMOTION)
            

        elif cmd in ["look up", "up"]:
            self.body.look_up()

        elif cmd in ["look down", "down", "neutral", "look neutral"]:
            self.body.look_neutral()

        elif cmd == "home":
            self.body.home_position()


        self._set_sequence_running(False)

