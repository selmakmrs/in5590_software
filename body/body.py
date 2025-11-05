from dynamixel_sdk import *
import time
import math
import random

# ========= CONFIGURATION =========
DEVICENAME = "/dev/ttyUSB0"
BAUDRATE = 1000000
PROTOCOL_VERSION = 1.0

# IDs
HEAD_ID = 0
BODY_ID = 3
BASE_ID = 1
SERVOS = [HEAD_ID, BODY_ID, BASE_ID]

# --- Control Table addresses (AX-12A) ---
ADDR_TORQUE_ENABLE = 24
ADDR_CW_ANGLE_LIMIT = 6
ADDR_CCW_ANGLE_LIMIT = 8
ADDR_GOAL_POSITION = 30
ADDR_MOVING_SPEED = 32
ADDR_TORQUE_LIMIT = 34
ADDR_PRESENT_POSITION = 36
ADDR_MOVING = 46

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# HOME POSITIONS (center positions for each servo)
HOME_POSITIONS = {
    HEAD_ID: 512,
    BODY_ID: 512,
    BASE_ID: 512
}

# MOVEMENT THRESHOLDS
BIG_MOVE_THRESHOLD = 200  # Use wheel mode only for movements larger than this
WHEEL_MODE_SLOWDOWN = 30  # Start slowing down when this close to target

# WHEEL MODE USAGE:
# For your robot with small gears:
# - Option 1: NEVER use wheel mode for positioning (safest)
# - Option 2: Only use wheel mode for FULL SPINS where position doesn't matter
# - Option 3: Add limit switches or encoders for absolute positioning

# ========= UTILITY FUNCTIONS =========
def open_bus(dev, baud):
    port = PortHandler(dev)
    pkt = PacketHandler(PROTOCOL_VERSION)
    if not port.openPort():
        raise RuntimeError("❌ Failed to open port")
    if not port.setBaudRate(baud):
        raise RuntimeError("❌ Failed to set baudrate")
    print("✅ Port opened at", baud, "bps")
    return port, pkt

def scan_ids(port, pkt, ids):
    found = []
    for i in ids:
        model, comm, err = pkt.ping(port, i)
        if comm == COMM_SUCCESS and err == 0:
            found.append(i)
            print(f"  - Found ID {i}, model {model}")

    if not found:
        port.closePort()
        raise SystemExit("No servos detected!")
    
    print("Found servos:", found)
    return found


class BODY:
    """
    Controls robot body movements (servos, motors)
    Handles head tracking and emotion gestures
    """
    def __init__(self):
    
        self.port, self.pkt = open_bus(DEVICENAME, BAUDRATE)
        self.ids = scan_ids(self.port, self.pkt, SERVOS)
        
        # Movement state
        self.speed_multiplier = 1.0
        self.is_emergency_stopped = False
        
        # Position tracking (CRITICAL for wheel mode)
        self.tracked_positions = {
            HEAD_ID: HOME_POSITIONS[HEAD_ID],
            BODY_ID: HOME_POSITIONS[BODY_ID],
            BASE_ID: HOME_POSITIONS[BASE_ID]
        }
        
        # Mode tracking
        self.current_modes = {
            HEAD_ID: "joint",
            BODY_ID: "joint", 
            BASE_ID: "joint"
        }
        
        # Idle state
        self.idle_counter = 0
        
        print("🤖 BODY initialized")

    # === Start & Close ===
    def start(self):
        """Start the body system"""
        self.enable_motors()
        self.set_joint_mode()
        self.set_torque_limit(512)  # 50% torque to start
        self.calibrate()
        print("▶️  BODY started")

    def close(self):
        """Shutdown the body system safely"""
        self.home_position()
        time.sleep(1)
        self.disable_motors()
        self.port.closePort()
        print("⏹️  BODY closed")

    # === Initialization & Calibration ===
    def calibrate(self):
        """Move all servos to known positions for calibration"""
        print("🔧 Calibrating...")
        
        # Ensure all servos are in joint mode
        for servo_id in self.ids:
            self.set_joint_mode(servo_id)
            time.sleep(0.1)
        
        # Move to home and update tracked positions
        self.home_position()
        time.sleep(0.5)
        
        # Read actual positions to sync tracking
        for servo_id in self.ids:
            actual_pos = self.get_position_safe(servo_id)
            self.tracked_positions[servo_id] = actual_pos
            print(f"  ID {servo_id}: position = {actual_pos}")
        
        print("✅ Calibration complete")

    def recalibrate_after_spin(self, layer_id):
        """
        Recalibrate a single servo after it's been in wheel mode
        Attempts to return to home position
        """
        print(f"🔄 Recalibrating ID {layer_id}...")
        self.set_joint_mode(layer_id)
        time.sleep(0.1)
        self.move_position(layer_id, HOME_POSITIONS[layer_id])
        time.sleep(1.0)
        actual = self.get_position_safe(layer_id)
        print(f"  ID {layer_id} home position: {actual}")

    def home_position(self):
        """Return to neutral/home position"""
        for servo_id in self.ids:
            self.move_position(servo_id, HOME_POSITIONS[servo_id])
        time.sleep(0.3)

    def enable_motors(self):
        """Enable servo power"""
        for i in self.ids:
            self.pkt.write1ByteTxRx(self.port, i, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

    def disable_motors(self):
        """Disable servo power (to prevent overheating)"""
        for i in self.ids:
            self.pkt.write1ByteTxRx(self.port, i, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)

    def set_joint_mode(self, dxl_id=None):
        """Set servos to joint mode (angle servo)"""
        ids = [dxl_id] if dxl_id else self.ids
        for i in ids:
            self.pkt.write2ByteTxRx(self.port, i, ADDR_CW_ANGLE_LIMIT, 0)
            self.pkt.write2ByteTxRx(self.port, i, ADDR_CCW_ANGLE_LIMIT, 1023)
            self.current_modes[i] = "joint"
            # Update tracked position when entering joint mode
            self.tracked_positions[i] = self.get_position_safe(i)

    def set_wheel_mode(self, dxl_id=None):
        """Set servos to wheel mode (infinite rotation, no target angle)"""
        ids = [dxl_id] if dxl_id else self.ids
        for i in ids:
            # Save current position BEFORE entering wheel mode
            if self.current_modes[i] == "joint":
                self.tracked_positions[i] = self.get_position_safe(i)
            
            self.pkt.write2ByteTxRx(self.port, i, ADDR_CW_ANGLE_LIMIT, 0)
            self.pkt.write2ByteTxRx(self.port, i, ADDR_CCW_ANGLE_LIMIT, 0)
            self.current_modes[i] = "wheel"

    def set_torque_limit(self, limit=1023, dxl_id=None):
        """Sets motor strength (0 = no torque, 1023 = full)"""
        ids = [dxl_id] if dxl_id else self.ids
        for i in ids:
            self.pkt.write2ByteTxRx(self.port, i, ADDR_TORQUE_LIMIT, max(0, min(1023, limit)))

    # === Position/Speed Control ===
    def get_position_safe(self, dxl_id):
        """
        Get position - returns tracked position if in wheel mode
        Only reads from servo if in joint mode
        """
        if self.current_modes[dxl_id] == "wheel":
            # In wheel mode, position reading is unreliable
            return self.tracked_positions[dxl_id]
        
        # In joint mode, read actual position
        pos, comm, err = self.pkt.read2ByteTxRx(self.port, dxl_id, ADDR_PRESENT_POSITION)
        if comm == COMM_SUCCESS:
            self.tracked_positions[dxl_id] = pos
            return pos
        return self.tracked_positions.get(dxl_id, HOME_POSITIONS[dxl_id])

    def get_position(self, dxl_id):
        """Get current position of servo (legacy compatibility)"""
        return self.get_position_safe(dxl_id)

    def move_position(self, dxl_id, pos):
        """Move to position (simple, joint mode only)"""
        pos = max(0, min(1023, pos))
        self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_GOAL_POSITION, pos)
        self.tracked_positions[dxl_id] = pos  # Update tracked position

    def move_position_smart(self, dxl_id, target_pos, use_wheel_mode=True):
        """
        Smart movement: automatically switches to wheel mode for big movements
        WARNING: Using wheel mode loses absolute position - use for full rotations only!
        """
        if self.is_emergency_stopped:
            return
            
        current_pos = self.get_position_safe(dxl_id)
        distance = abs(target_pos - current_pos)
        
        # Small movement: just use joint mode
        if distance < BIG_MOVE_THRESHOLD or not use_wheel_mode:
            self.set_joint_mode(dxl_id)
            self.move_position(dxl_id, target_pos)
            return
        
        # Big movement: AVOID wheel mode for precise positioning
        # Instead, just move slower in joint mode
        print(f"🔄 Big move on ID {dxl_id}: {current_pos} → {target_pos} (joint mode)")
        self.set_joint_mode(dxl_id)
        self.move_position(dxl_id, target_pos)
        
        # Wait for movement to complete
        time.sleep(0.5)

    def wheel_speed(self, dxl_id, speed):
        """
        Set wheel speed: -1023 to 1023
        Negative = counterclockwise, Positive = clockwise
        """
        direction = 0 if speed >= 0 else 1
        speed = min(1023, abs(speed))
        value = speed | (direction << 10)
        self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_MOVING_SPEED, value)

    # === PRIMITIVE MOVEMENTS ===

    def rotate_layer(self, layer_id, degrees, speed="normal", use_smart=True):
        """
        Rotate a layer by degrees from current position
        speed: 'slow', 'normal', 'fast'
        """
        current = self.get_position(layer_id)
        steps_per_degree = 1023 / 300.0  # AX-12A is ~300 degrees range
        target = int(current + (degrees * steps_per_degree))
        target = max(0, min(1023, target))
        
        if use_smart:
            self.move_position_smart(layer_id, target)
        else:
            self.move_position(layer_id, target)

    def wiggle(self, layer_id, amplitude=20, cycles=2, speed=3.0):
        """Small oscillation back and forth"""
        center = self.get_position(layer_id)
        duration = cycles / speed
        start = time.time()
        
        while time.time() - start < duration:
            if self.is_emergency_stopped:
                return
            t = time.time() - start
            offset = amplitude * math.sin(2 * math.pi * speed * t)
            self.move_position(layer_id, int(center + offset))
            time.sleep(0.02)
        
        # Return to center
        self.move_position(layer_id, center)

    def bounce(self, layer_id, height=30, times=3):
        """Bounce up and down"""
        center = self.get_position(layer_id)
        for _ in range(times):
            if self.is_emergency_stopped:
                return
            self.move_position(layer_id, center + height)
            time.sleep(0.2)
            self.move_position(layer_id, center)
            time.sleep(0.2)

    def spin(self, layer_id, rotations=1, speed=300):
        """
        Continuous spin (requires wheel mode)
        WARNING: This LOSES absolute position! Must recalibrate after.
        """
        print(f"⚠️  Spinning ID {layer_id} - position tracking will be lost!")
        self.set_wheel_mode(layer_id)
        duration = rotations * 2.0  # ~2 seconds per rotation at medium speed
        self.wheel_speed(layer_id, speed)
        time.sleep(duration)
        self.wheel_speed(layer_id, 0)
        time.sleep(0.2)
        
        # CRITICAL: After spinning, we don't know where we are!
        # Options:
        # 1. Return to home position (safest)
        # 2. Assume we're near where we started
        # 3. Use external encoder
        
        self.set_joint_mode(layer_id)
        print(f"⚠️  ID {layer_id} lost position - returning home")
        self.move_position(layer_id, HOME_POSITIONS[layer_id])
        time.sleep(0.5)

    def hold(self, duration):
        """Pause for duration seconds"""
        time.sleep(duration)

    # === HEAD MOVEMENTS ===

    def look_left(self, angle=45):
        """Turn head left"""
        self.rotate_layer(HEAD_ID, -angle, use_smart=False)

    def look_right(self, angle=45):
        """Turn head right"""
        self.rotate_layer(HEAD_ID, angle, use_smart=False)

    def look_center(self):
        """Return head to center"""
        self.move_position(HEAD_ID, HOME_POSITIONS[HEAD_ID])

    def shake_head(self, times=3, speed=0.3):
        """Shake head left and right"""
        center = self.get_position(HEAD_ID)
        for _ in range(times):
            if self.is_emergency_stopped:
                return
            self.move_position(HEAD_ID, center - 50)
            time.sleep(speed)
            self.move_position(HEAD_ID, center + 50)
            time.sleep(speed)
        self.move_position(HEAD_ID, center)

    def nod_head(self, times=2, speed=0.3):
        """Nod head (if you have tilt - simulated with body for now)"""
        for _ in range(times):
            if self.is_emergency_stopped:
                return
            self.rotate_layer(BODY_ID, 10, use_smart=False)
            time.sleep(speed)
            self.rotate_layer(BODY_ID, -10, use_smart=False)
            time.sleep(speed)

    def tilt_curious(self):
        """Tilt head to side (curious look)"""
        self.rotate_layer(HEAD_ID, 25, use_smart=False)
        time.sleep(0.5)

    # === IDLE SEQUENCE (Generator) ===

    def idle_sequence(self):
        """
        Generator that yields idle micro-movements
        Call next() on this in your main loop
        """
        actions = [
            ("look_random", 40),
            ("wait", 2.0),
            ("small_wiggle", None),
            ("wait", 3.0),
            ("look_center", None),
            ("wait", 1.5),
        ]
        
        while True:
            for action, param in actions:
                if action == "look_random":
                    angle = random.randint(-param, param)
                    self.rotate_layer(HEAD_ID, angle, use_smart=False)
                elif action == "small_wiggle":
                    layer = random.choice([BODY_ID, BASE_ID])
                    self.wiggle(layer, amplitude=15, cycles=1, speed=2)
                elif action == "look_center":
                    self.look_center()
                elif action == "wait":
                    time.sleep(param)
                
                yield action

    # === EMOTION GESTURES ===

    def gesture_happy(self):
        """Happy: bounce, wiggle, spin!"""
        print("😊 HAPPY gesture")
        self.bounce(BODY_ID, height=40, times=2)
        self.wiggle(HEAD_ID, amplitude=30, cycles=3, speed=4)
        self.spin(BASE_ID, rotations=0.5, speed=400)
        self.home_position()

    def gesture_sad(self):
        """Sad: slow, droopy movements"""
        print("😢 SAD gesture")
        self.rotate_layer(HEAD_ID, -20, use_smart=False)
        time.sleep(0.8)
        self.rotate_layer(BODY_ID, -15, use_smart=False)
        time.sleep(1.5)
        self.home_position()

    def gesture_angry(self):
        """Angry: shake, tense movements"""
        print("😠 ANGRY gesture")
        self.shake_head(times=5, speed=0.15)
        self.wiggle(BASE_ID, amplitude=25, cycles=2, speed=5)
        self.home_position()

    def gesture_surprised(self):
        """Surprised: quick back movement"""
        print("😲 SURPRISED gesture")
        self.rotate_layer(BODY_ID, 30, use_smart=False)
        time.sleep(0.1)
        self.rotate_layer(HEAD_ID, 20, use_smart=False)
        time.sleep(0.5)
        self.rotate_layer(BODY_ID, -30, use_smart=False)
        time.sleep(0.8)
        self.home_position()

    def gesture_fear(self):
        """Fear: retreat, small movements"""
        print("😨 FEAR gesture")
        self.rotate_layer(HEAD_ID, -15, use_smart=False)
        self.rotate_layer(BODY_ID, -20, use_smart=False)
        time.sleep(0.5)
        self.wiggle(HEAD_ID, amplitude=10, cycles=4, speed=6)
        time.sleep(1.0)
        self.home_position()

    def gesture_neutral(self):
        """Neutral: return to center"""
        print("😐 NEUTRAL gesture")
        self.home_position()

    # === UTILITY ===

    def is_moving(self, dxl_id=None):
        """Check if servo(s) are currently moving"""
        ids = [dxl_id] if dxl_id else self.ids
        for i in ids:
            moving, comm, err = self.pkt.read1ByteTxRx(self.port, i, ADDR_MOVING)
            if comm == COMM_SUCCESS and moving:
                return True
        return False

    def wait_for_movement(self, timeout=5.0):
        """Block until all movements complete"""
        start = time.time()
        while self.is_moving() and (time.time() - start) < timeout:
            time.sleep(0.05)

    def emergency_stop(self):
        """Immediately stop all movements"""
        print("🛑 EMERGENCY STOP")
        self.is_emergency_stopped = True
        for i in self.ids:
            self.set_wheel_mode(i)
            self.wheel_speed(i, 0)
        time.sleep(0.1)
        for i in self.ids:
            self.set_joint_mode(i)
        self.is_emergency_stopped = False

    def set_servo_speed(self, speed):
        """Set global movement speed multiplier (0.1 to 2.0)"""
        self.speed_multiplier = max(0.1, min(2.0, speed))
        print(f"⚡ Speed set to {self.speed_multiplier}x")

    def cleanup(self):
        """Clean up resources"""
        self.close()


# === EXAMPLE USAGE ===
if __name__ == "__main__":
    body = BODY()

    try:
        body.start()
        
        # Test movements
        print("\n🧪 Testing basic movements...")
        body.look_left(30)
        time.sleep(1)
        body.look_right(30)
        time.sleep(1)
        body.look_center()
        
        print("\n😊 Testing HAPPY gesture...")
        body.gesture_happy()
        time.sleep(2)
        
        print("\n🔁 Testing idle sequence (5 iterations)...")
        idle_gen = body.idle_sequence()
        for _ in range(5):
            action = next(idle_gen)
            print(f"  Idle action: {action}")
        
        print("\n✅ Tests complete!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    finally:
        body.cleanup()