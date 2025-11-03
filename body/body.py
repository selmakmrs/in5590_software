class BODY:
    """
    Controls robot body movements (servos, motors)
    Handles head tracking and emotion gestures
    """
    
    def __init__(self, servo_pins=None):
        """
        Initialize servo controllers and motors
        
        Args:
            servo_pins: dict like {'head_pan': 17, 'head_tilt': 18, 'arm_left': 22, ...}
        """
        pass
    
    # === Initialization & Calibration ===
    def calibrate(self):
        """
        Move all servos to known positions for calibration
        Should be called on startup
        """
        pass
    
    def home_position(self):
        """
        Return to neutral/home position
        """
        pass
    
    def enable_motors(self):
        """Enable servo power"""
        pass
    
    def disable_motors(self):
        """Disable servo power (to prevent overheating)"""
        pass
    
    # === Position Control ===
    def set_head_position(self, pan_angle, tilt_angle):
        """
        Set head position (absolute)
        
        Args:
            pan_angle: Horizontal angle (-90 to 90 degrees)
            tilt_angle: Vertical angle (-45 to 45 degrees)
        """
        pass
    
    def move_head_smooth(self, target_pan, target_tilt, speed=0.1):
        """
        Smoothly interpolate head to target position
        
        Args:
            target_pan: Target horizontal angle
            target_tilt: Target vertical angle
            speed: Movement speed (0.0-1.0)
        """
        pass
    
    def get_current_position(self):
        """
        Get current head position
        
        Returns:
            (pan_angle, tilt_angle): Current angles
        """
        pass
    
    # === Tracking ===
    def track_position(self, face_position, frame_size=(320, 240)):
        """
        Point head toward face position in frame
        
        Args:
            face_position: (x, y) in pixel coordinates
            frame_size: (width, height) of camera frame
        """
        pass
    
    def calculate_servo_angles(self, pixel_x, pixel_y, frame_size):
        """
        Convert pixel position to servo angles
        
        Args:
            pixel_x, pixel_y: Position in frame
            frame_size: (width, height)
            
        Returns:
            (pan_angle, tilt_angle): Servo angles
        """
        pass
    
    # === State Sequences (Generators) ===
    def idle_sequence(self):
        """
        Execute one step of idle animation
        Call repeatedly in loop for continuous animation
        
        Returns:
            str: Current action name (for debugging)
        """
        pass
    
    def _idle_generator(self):
        """
        Generator that yields idle movements
        
        Yields:
            Movement commands (look around, small nods, etc.)
        """
        # Example:
        # while True:
        #     yield self._look_left_slow()
        #     yield self._pause(2.0)
        #     yield self._look_right_slow()
        #     yield self._pause(2.0)
        #     yield self._look_center()
        #     yield self._head_tilt_curious()
        pass
    
    def emotion_sequence(self, emotion):
        """
        Execute one step of emotion gesture
        
        Args:
            emotion: str ('happy', 'sad', 'angry', etc.)
            
        Returns:
            bool: True if sequence still running, False if complete
        """
        pass
    
    def _emotion_generator(self, emotion):
        """
        Generator for emotion-specific movements
        
        Args:
            emotion: Emotion name
            
        Yields:
            Movement commands
        """
        # Example for 'happy':
        # - Nod head up and down
        # - Wave arms
        # - Bounce motion
        pass
    
    # === Emotion Gestures ===
    def gesture_happy(self):
        """Perform happy gesture (nod, bounce, etc.)"""
        pass
    
    def gesture_sad(self):
        """Perform sad gesture (head down, slow movements)"""
        pass
    
    def gesture_angry(self):
        """Perform angry gesture (shake head, tense movements)"""
        pass
    
    def gesture_surprised(self):
        """Perform surprised gesture (head back, quick movement)"""
        pass
    
    def gesture_fear(self):
        """Perform fear gesture (head down, retreat motion)"""
        pass
    
    def gesture_neutral(self):
        """Perform neutral gesture (center, still)"""
        pass
    
    # === Primitive Movements ===
    def look_left(self, angle=45):
        """Turn head left"""
        pass
    
    def look_right(self, angle=45):
        """Turn head right"""
        pass
    
    def look_up(self, angle=30):
        """Tilt head up"""
        pass
    
    def look_down(self, angle=30):
        """Tilt head down"""
        pass
    
    def look_center(self):
        """Return head to center"""
        pass
    
    def nod(self, times=3, speed=0.5):
        """Nod head up and down"""
        pass
    
    def shake_head(self, times=3, speed=0.5):
        """Shake head left and right"""
        pass
    
    def tilt_curious(self):
        """Tilt head to side (curious look)"""
        pass
    
    # === Additional Body Parts (if applicable) ===
    def set_arm_position(self, left_angle, right_angle):
        """Control arm servos"""
        pass
    
    def wave(self, arm='right'):
        """Wave arm"""
        pass
    
    def arms_up(self):
        """Raise both arms (excited)"""
        pass
    
    def arms_down(self):
        """Lower both arms (sad)"""
        pass
    
    # === Utility ===
    def is_moving(self):
        """
        Check if any servos are currently moving
        
        Returns:
            bool: True if in motion
        """
        pass
    
    def wait_for_movement(self):
        """Block until all movements complete"""
        pass
    
    def emergency_stop(self):
        """Immediately stop all movements"""
        pass
    
    def get_servo_angle(self, servo_name):
        """Get current angle of specific servo"""
        pass
    
    def set_servo_speed(self, speed):
        """Set global movement speed multiplier"""
        pass
    
    def cleanup(self):
        """Clean up GPIO and servo resources"""
        pass