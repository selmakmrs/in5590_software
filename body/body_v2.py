from typing import List, Tuple
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

# MODES
JOINT = "joint"
WHEEL = "wheel"


# ========= UTILITY FUNCTIONS =========
def open_bus(dev, baud):
    port = PortHandler(dev)
    pkt = PacketHandler(PROTOCOL_VERSION)
    if not port.openPort():
        raise RuntimeError("Failed to open port!")
    if not port.setBaudRate(baud):
        raise RuntimeError("Failed to set baudrate!")
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
    Controls robot body movements
    """
    def __init__(self):
        
        self.port, self.pkt = open_bus(DEVICENAME, BAUDRATE)
        self.ids = scan_ids(self.port, self.pkt, SERVOS)


        # Position tracking (CRITICAL for wheel mode)
        self.tracked_positions = {
            HEAD_ID: HOME_POSITIONS[HEAD_ID],
            BODY_ID: HOME_POSITIONS[BODY_ID],
            BASE_ID: HOME_POSITIONS[BASE_ID]
        }

        self.current_mode = None

        print("Body initialized")

    # ============ Start and close ==========

    def start(self):
        """Start the body system"""
        self.enable_motors()
        self.set_joint_mode()
        self.set_torque_limit()
        self.calibrate()
        print("BODY Started")


    def close(self):
        self.home_position()
        time.sleep(1)
        self.disable_motors()
        self.port.closePort()
        print("BODY closed")


    # ========= Initialization =================

    def calibrate(self):
        """Moves al servos to known positions for calibartion"""
        print("Calibrating ...")

        # Ensure all servos in joint mode
        self.set_joint_mode()
        time.sleep(0.1)

        # Move all servos to home position
        self.home_position()
        time.sleep(0.1)

        # Read and store positions
        for dxl_id in self.ids:
            pos = self.get_position(dxl_id)
            self.tracked_positions[dxl_id] = pos
            print(f" ID {dxl_id}: position = {pos}")

        print("Calibration complete ")
        
    def home_position(self):
        """Return all servos to home position"""
        for dxl_id in self.ids:
            self.move_position(dxl_id, HOME_POSITIONS[dxl_id])
        time.sleep(1)

    def enable_motors(self):
        """Enable servo power"""
        for dxl_id in self.ids:
            self.pkt.write1ByteTxRx(self.port, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
        print("Servos enabled")

    def disable_motors(self):
        """Enable servo power"""
        for dxl_id in self.ids:
            self.pkt.write1ByteTxRx(self.port, dxl_id, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
        print("Servos disabled")
        
    def set_joint_mode(self):
         for dxl_id in self.ids:
            self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_CW_ANGLE_LIMIT, 0)
            self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_CCW_ANGLE_LIMIT, 1023)
            self.current_mode = JOINT
            # Update tracked position when entering joint mode
            self.tracked_positions[dxl_id] = self.get_position(dxl_id)

    def set_wheel_mode(self):
        for dxl_id in self.ids:
            self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_CW_ANGLE_LIMIT, 0)
            self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_CCW_ANGLE_LIMIT, 0)
            self.current_mode = WHEEL

    def set_torque_limit(self, limit=1023, dxl_id=None):
        """Sets motor strength (0 = no torque, 1023 = full)"""
        ids = [dxl_id] if dxl_id else self.ids
        for dxl_id in ids:
            self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_TORQUE_LIMIT, max(0, min(1023, limit)))

       

    # ========= Postion And Speed Controll =====================

    def get_position(self, dxl_id):
        """
        Get position - returns tracked position if in wheel mode
        Only reads from servo if in joint mode
        """
        if self.current_mode == WHEEL:
            # In wheel mode, position reading is unreliable
            return self.tracked_positions[dxl_id]
        
        # In joint mode, read actual position
        pos, comm, err = self.pkt.read2ByteTxRx(self.port, dxl_id, ADDR_PRESENT_POSITION)
        if comm == COMM_SUCCESS:
            self.tracked_positions[dxl_id] = pos
            return pos
        
        return self.tracked_positions.get(dxl_id, HOME_POSITIONS[dxl_id])

    def move_position(self, dxl_id, pos, speed = 300):
        """Move to position (simple, joint mode only)"""
        pos = max(0, min(1023, pos))
        speed = max(0,min(1023, speed))
        self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_MOVING_SPEED, speed)
        self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_GOAL_POSITION, pos)
        self.tracked_positions[dxl_id] = pos  # Update tracked position

    def wheel_speed(self, dxl_id, speed):
        """
        Set wheel speed: -1023 to 1023
        Negative = counterclockwise, Positive = clockwise
        """
        direction = 0 if speed >= 0 else 1
        speed = min(1023, abs(speed))
        value = speed | (direction << 10)
        self.pkt.write2ByteTxRx(self.port, dxl_id, ADDR_MOVING_SPEED, value)


    def _scurve_interpolate(self, start, end, s):
        """S-curve interpolation between start and end position"""
        s_smooth = 3 * s * s - 2 * s * s * s
        return int(start + (end - start) * s_smooth)
    

    def move_positions_smooth(self, layer_configs, steps=50, duration = 0.025):
        """Layer configs List with tuple [(dxl_id, start_pos, end_pos, speed)]"""

        for i in range(steps):
            t = i / steps
            for dxl_id, start_pos, end_pos, speed in layer_configs:
                pos = self._scurve_interpolate(start_pos, end_pos, t)
                self.move_position(dxl_id, pos, speed)
            time.sleep(duration)

        

        

    
    



    # === UTILITY ===

    def emergency_stop(self):
        print("🛑 EMERGENCY STOP")
        self.is_emergency_stopped = True
        self.set_wheel_mode()
        for dxl_id in self.ids:
            self.wheel_speed(dxl_id, 0)
        time.sleep(0.1)
        self.set_joint_mode()
        self.is_emergency_stopped = False




    # ============ Base movemnts ==================

    def _look_left_slow(self, hold = 1):
        """Turn head left and light body twist"""
        self.set_joint_mode()

        steps = 5
        duration = 0.01

        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], 200, 50)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], 300, 50)
        self.move_positions_smooth(layer_configs=[head_config, body_config], steps=steps, duration=duration)

        # Hold position
        time.sleep(hold)

        # Return home
        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[HEAD_ID], 50)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[BODY_ID], 50)
        self.move_positions_smooth(layer_configs=[head_config, body_config], steps=steps, duration=duration)

        time.sleep(0.5)


    def _look_right_slow(self, hold=1):
        """Turn head left and light body twist"""
        self.set_joint_mode()

        steps = 5
        duration = 0.01

        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], 800, 50)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], 700, 50)
        self.move_positions_smooth(layer_configs=[head_config, body_config], steps=steps, duration=duration)

        # Hold position
        time.sleep(hold)

        # Return home
        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[HEAD_ID], 50)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[BODY_ID], 50)
        self.move_positions_smooth(layer_configs=[head_config, body_config], steps=steps, duration=duration)

        time.sleep(0.5)

    def _look_left_fast(self, hold = 1):
        """Turn head left and light body twist"""
        self.set_joint_mode()

        steps = 5
        duration = 0.01

        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], 200, 600)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], 300, 600)
        self.move_positions_smooth(layer_configs=[head_config, body_config], steps=steps, duration=duration)

        # Hold position
        time.sleep(hold)

        # Return home
        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[HEAD_ID], 50)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[BODY_ID], 50)
        self.move_positions_smooth(layer_configs=[head_config, body_config], steps=steps, duration=duration)

        time.sleep(0.5)


    def _look_right_fast(self, hold=1):
        """Turn head left and light body twist"""
        self.set_joint_mode()

        steps = 5
        duration = 0.01

        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], 800, 600)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], 700, 600)
        self.move_positions_smooth(layer_configs=[head_config, body_config], steps=steps, duration=duration)

        # Hold position
        time.sleep(hold)

        # Return home
        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[HEAD_ID], 50)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[BODY_ID], 50)
        self.move_positions_smooth(layer_configs=[head_config, body_config], steps=steps, duration=duration)

        time.sleep(0.5)

    def _look_arounf_sweep(self):
        pass

    def _curious_tilit_left(self, hold=1):
        """Turn head left and light body twist"""
        self.set_joint_mode()

        steps = 5
        duration = 0.01

        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], 0, 100)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], 1000, 100)
        base_config = (BASE_ID, self.tracked_positions[HEAD_ID], 0, 100)
        self.move_positions_smooth(layer_configs=[head_config, body_config, base_config], steps=steps, duration=duration)

        # Hold position
        time.sleep(hold)

        # Return home
        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[HEAD_ID], 100)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[BODY_ID], 100)
        base_config = (BASE_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[BASE_ID], 100)
        self.move_positions_smooth(layer_configs=[head_config, body_config, base_config], steps=steps, duration=duration)

        time.sleep(0.5)

    def _curious_tilit_right(self, hold=1):
        """Turn head left and light body twist"""
        self.set_joint_mode()

        steps = 10
        duration = 0.01

        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], 1000, 100)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], 0, 100)
        base_config = (BASE_ID, self.tracked_positions[HEAD_ID], 1000, 100)
        self.move_positions_smooth(layer_configs=[head_config, body_config, base_config], steps=steps, duration=duration)

        # Hold position
        time.sleep(hold)

        # Return home
        head_config = (HEAD_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[HEAD_ID], 100)
        body_config = (BODY_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[BODY_ID], 100)
        base_config = (BASE_ID, self.tracked_positions[HEAD_ID], HOME_POSITIONS[BASE_ID], 100)
        self.move_positions_smooth(layer_configs=[head_config, body_config, base_config], steps=steps, duration=duration)

        time.sleep(0.5)


    def _twitch(self):
        pass

    def _look_up(self):
        pass



    # ============== Wheel Movements =================

    def _run_wheel_movements(self, layer_config, hold=2, go_back=True):
        self.set_wheel_mode()

        for dxl_id, speed, duration in layer_config:
            self.wheel_speed(dxl_id, speed)

        start = time.time()
        
        while True:
            elapsed = time.time() - start
            all_servos_stopped = True
            for dxl_id, speed, duration in layer_config:
                if duration <= elapsed:
                    self.wheel_speed(dxl_id,0)
                else:
                    all_servos_stopped = False

            if all_servos_stopped or elapsed >= 3:
                break
            time.sleep(0.01)

        self._stop_wheels()
        time.sleep(hold)

        if go_back:

            for dxl_id, speed, duration in layer_config:
                self.wheel_speed(dxl_id, -speed)

            start = time.time()
            
            while True:
                elapsed = time.time() - start
                all_servos_stopped = True
                for dxl_id, speed, duration in layer_config:
                    if duration <= elapsed:
                        self.wheel_speed(dxl_id,0)
                    else:
                        all_servos_stopped = False

                if all_servos_stopped or elapsed >= 3:
                    break

            self._stop_wheels()
            time.sleep(hold)


        self.set_joint_mode()

    def _stop_wheels(self):
        for dxl_id in self.ids:
            self.wheel_speed(dxl_id, 0)

    def jump_back(self):
        """Makes Root jumb back
        BASE 180 deg
        BODY -180 deg """
        base_config = (BASE_ID, 1024, 1.5)
        body_config = (BODY_ID, -600, 1.5)
   
        self._run_wheel_movements([base_config, body_config])




    def jump_forward(self):
        pass

    def jump_left(self, hold=3):
        """
        Makes robot jump left
        Config:
          - BASE : -90 deg
          - BODY : 180 deg
          - HEAD : -90 deg
          
        """

        duration = 0.7

        base_config = (BASE_ID, -900, 0.7)
        body_config = (BODY_ID, 1024, 0.9)
        head_config = (HEAD_ID, -900, 0.7)

        self._run_wheel_movements([base_config, body_config, head_config], hold=hold)
        

    def jump_right(self, hold=3):
        """
        Makes robot jump left
        Config:
          - BASE : 90 deg
          - BODY : -180 deg
          - HEAD : 90 deg
          
        """
        base_config = (BASE_ID, 900, 0.7)
        body_config = (BODY_ID, -1024, 0.9)
        head_config = (HEAD_ID, 900, 0.7)

        self._run_wheel_movements([base_config, body_config, head_config])

    def dance(self):
        hold = 0.1
        
        for _ in range(2):
            self.jump_left(hold)
            self.jump_right(hold)

    def sway(self, cycles=4):

        body_config_start = (BODY_ID, 700, 1.5)
        base_config_start = (BASE_ID, -1023, 1.5)

        self._run_wheel_movements([body_config_start, base_config_start], go_back=False)

        time.sleep(1.0)

        duration = 0.01
        steps = 40

        for _ in range(cycles):
            body_config = (BODY_ID, self.tracked_positions[BODY_ID], 0, 100)
            self.move_positions_smooth(layer_configs=[body_config, body_config], steps=steps, duration=duration)
            body_config = (BODY_ID, self.tracked_positions[BODY_ID], 1024, 100)
            self.move_positions_smooth(layer_configs=[body_config, body_config], steps=steps, duration=duration)

        body_config = (BODY_ID, self.tracked_positions[BODY_ID], HOME_POSITIONS[BODY_ID], 400)
        self.move_positions_smooth(layer_configs=[body_config, body_config], steps=steps, duration=duration)

        time.sleep(1)

        body_config_end = (BODY_ID, -700, 1.5)
        base_config_end = (BASE_ID, 1023, 1.5)
        self._run_wheel_movements([body_config_end, base_config_end], go_back=False)


    def look_up(self):
        self.set_wheel_mode()
        base_config = (BASE_ID, -1023, 1.5)
        body_config = (BODY_ID, 700, 1.7)
        head_config = (HEAD_ID, -1023, 1.1)

        for dxl_id, speed, time in [base_config, body_config, head_config]:
            self.wheel_speed(dxl_id, speed)

        time.sleep(1.5)

        self._stop_wheels()
        self.set_joint_mode()

        



    def look_down(self):
        base_config = (BASE_ID, 1023, 1.5)
        body_config = (BODY_ID, -700, 1.5)
        head_config = (HEAD_ID, 1024, 1.5)

        self._run_wheel_movements([base_config, body_config, head_config], go_back=False)
        


        


    # ================================================= #
    # =============== Emotion Sequences =============== #
    # ================================================= #

    def idle(self):
        """IDLE MODE"""
        self.set_joint_mode()


        slow_look_sequences = [
            self._look_left_slow,
            self._look_right_slow,
            self._curious_tilit_left,
            self._curious_tilit_right
        ]

        fast_look_sequence = [
            self._look_left_fast,
            self._look_right_fast,
        ]

        start = time.time()

        slow_seq_prob = 0.1
        fast_seq_prob = 0.03
        home_prob = 0.02


        while True:
            if random.random() < slow_seq_prob:
                sequence = random.choice(slow_look_sequences)
                hold = random.uniform(1,4)
                sequence(hold)

            if random.random() <= home_prob:
                self.home_position()

            if random.random() <= fast_seq_prob:
                sequence = random.choice(fast_seq_prob)
                hold = random.uniform(1,4)
                sequence(hold)


            if 30 < time.time() - start:
                break

            time.sleep(0.5)



    def happy(self):
        pass

    def sad(self):
        pass

    def angry(self):
        pass

    def fear(self):
        pass

    def suprised(self):
        pass

    def courious(self):
        pass









# === EXAMPLE USAGE ===
if __name__ == "__main__":
    body = BODY()

    try:
        body.start()

        time.sleep(1)
        print("Testing Body movemnt in joint mode")
        # body.idle()
        # body._look_left_slow()
        # body._look_right_slow()
        # body._curious_tilit_left()
        # body._curious_tilit_right()
        # body.jump_back()
        # body.jump_left()
        # body.jump_right()
        body.look_up()

        
        print("\n✅ Tests complete!")
        
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        body.emergency_stop()
    finally:
        body.close()