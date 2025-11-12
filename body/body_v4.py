from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import time
import logging
from dynamixel_sdk import *


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Hardware Config
DEVICENAME = "/dev/ttyUSB0"
BAUDRATE = 1_000_000
PROTOCOL_VERSION = 1.0

class ServoID(Enum):
    """Servo identification"""
    HEAD = 0
    BODY = 0
    BASE = 0

class ControlTable:
    """AX-12A Controll Table for addresses"""
    TORQUE_ENABLE = 24
    CW_ANGLE_LIMIT = 6
    CCW_ANGLE_LIMIT = 8
    GOAL_POSITION = 30
    MOVING_SPEED = 32
    TORQUE_LIMIT = 34
    PRESENT_POSITION = 36
    MOVING = 46

class OperationMode(Enum):
    """Servo operating modes"""
    JOINT = "joint"
    WHEEL = "wheel"


# Constraints
HOME_POSITION = 512
MIN_POS = 0
MAX_POS = 1023
MAX_SPEED = 1023


class DynamixelInterface:
    """Low level dynamxiel controll"""

    def __init__(self):
        self.port = PortHandler(DEVICENAME)
        self.packet_handler = PacketHandler(PROTOCOL_VERSION)
        self._is_open = False

    def open(self):
        """Open serial port"""
        if not self.port.openPort():
            raise RuntimeError(f"Failed to open port {self.port.port_name}")
        if not self.port.setBaudRate(BAUDRATE):
            raise RuntimeError(f"Failed to set baudrate to {BAUDRATE}")
        self._is_open = True
        logger.info(f"Port opened: {self.port.port_name}")

    def close(self):
        """Close serial port"""
        if self._is_open:
            self.port.closePort()
            self._is_open = False
            logger.info("Port closed")

    def scan_servos(self, ids):
        """Scan for active servos"""
        found = []
        for servio_id in ids:
            model, comm, err = self.packet_handler.ping(self.port, servio_id)
            if comm == COMM_SUCCESS and err == 0:
                found.append(servio_id)
                logger.info(f"Found servo ID {servio_id}")

        if not found:
            raise RuntimeError("No servos detected!")
        
        return found
    
    def write_byte(self, servo_id, address, value):
        """Write signle byte"""
        _, comm, err = self.packet_handler.write1ByteTxRx(self.port, servo_id, address, value)
        return comm == COMM_SUCCESS and err == 0
    
    def write_word(self, servo_id, address, value):
        """Write two bytes"""
        _, comm, err = self.packet_handler.write2ByteTxRx(self.port, servo_id, address, value)
        return comm == COMM_SUCCESS and err == 0
    
    def read_word(self, servo_id, address):
        """Read two bytes"""
        value, comm, err = self.packet_handler.read2ByteTxRx(self.port, servo_id, address)
        if comm == COMM_SUCCESS and err == 0:
            return value
        return None
    


class Body:
    """
    High-level robot controlller
    """
    def __init__(self):

        self.interface = DynamixelInterface()

        # State tracking
        self.current_mode = OperationMode.JOINT
        self.tracked_positions = {}
        self._is_looking_up = False

        self.orientation_offsets = {
            ServoID.HEAD.value : 512,
            ServoID.BODY.value : 512,
            ServoID.BASE.value : 512
        }

        self.servos = []

    def start(self):
        """Start Body"""
        try:
            self.interface.open()
            self.servos = self.interface.scan_servos([s.value for s in ServoID])

            self._enable_all_servos()
            self.set_mode(OperationMode.JOINT)
            self._set_torque_limit(MAX_SPEED)
            self._calibare_positions()

            logger.info("Body system started succsessfully")
        except Exception as e:
            logger.error(f"Failed to start body: {e}")
            raise

    def close(self):
        """Shutdown body"""
        try:
            logger.info("Shutting down body...")
            self.move_to_home()
            time.sleep(1.0)
            self._disable_all_servos()
            self.interface.close()
            logger.info("Body closed")
        except Exception as e:
            logger.error(f"Error during shutdown of body:, {e}")

    # =============== Servo Controll ===================

    def set_mode(self, mode):
        """Set mode for all servos"""
        for servo_id in self.servos:
            if mode == OperationMode.JOINT:
                self.interface.write_word(servo_id, ControlTable.CW_ANGLE_LIMIT, MIN_POS)
                self.interface.write_word(servo_id, ControlTable.CWC_ANGLE_LIMIT, MAX_POS)
                self.tracked_positions[servo_id] = self._read_position(servo_id)
            else:
                self.interface.write_word(servo_id, ControlTable.CW_ANGLE_LIMIT, 0)
                self.interface.write_word(servo_id, ControlTable.CCW_ANGLE_LIMIT, 0)

        self.current_mode = mode

    def move_to_position(self, servo_id, position, speed = 200):
        """Move servo to target position"""
        if self.current_mode != OperationMode.JOINT:
            return
        
        position = self._clamp(position, 0, MAX_POS)
        speed = self._clamo(speed, 0, MAX_SPEED)

        self.interface.write_word(servo_id, ControlTable.MOVING_SPEED, speed)
        self.interface.write_word(servo_id, ControlTable.GOAL_POSITION, position)
        self.tracked_positions[servo_id] = position

    def set_wheel_speed(self, servo_id, speed):
        """Set wheel rotation speed for servo"""
        if self.current_mode != OperationMode.WHEEL:
            return
        
        direction = 1 if speed >= 0 else -1
        speed_value = self._clamp(speed, -MAX_SPEED, MAX_SPEED)
        value = speed_value | (direction << 10)

        self.interface.write_byte(servo_id, ControlTable.MOVING_SPEED, value)

    def stop_all_wheels(self):
        """Stop all servos (wheel mode)"""
        for servo_id in self.servos:
            self.set_wheel_speed(servo_id, 0)

    def move_to_home(self):
        """Return all servos to home position"""
        if self.current_mode != OperationMode.JOINT:
            self.set_mode(OperationMode.JOINT)

        for servo_id in self.servos:
            self.move_to_position(servo_id, HOME_POSITION, 200)

    def rotate_geared(self,
                      base_deg = 0,
                      body_deg = 0,
                      head_def = 0,
                      duration = 3.0,
                      max_speed = MAX_SPEED,
                      hold_duration = 1.0,
                      return_to_start = True):
        """Rotate all layers to spesific angles"""
        if self.current_mode != OperationMode.WHEEL:
            self.set_mode(OperationMode.WHEEL)

        
        


    # ========== Helper Fuctions ==============

    def _calibrate_positions(self):
        """Read and store inital servo positions"""
        self.move_to_home()
        time.sleep(1)
        
        for servo_id in self.servos:
            pos = self._read_positions(servo_id)
            self.tracked_positions[servo_id] = pos

    def _read_position(self, servo_id):
        """Read current position of servo"""
        if self.current_mode == OperationMode.WHEEL:
            return self.tracked_positions.get(servo_id, HOME_POSITION)
        
        pos = self.interface.read_word(servo_id, ControlTable.PRESENT_POSITION)
        if pos is None:
            return self.tracked_positions.get(servo_id, HOME_POSITION)
        return pos
    
    def _enable_all_servos(self):
        """Enable torque on all servos"""
        for servio_id in self.servos:
            self.interface.write_byte(servio_id, ControlTable.TORQUE_ENABLE, 1)
        logger.info("All servos enabled")

    def _diable_all_servos(self):
        """Disable torque in all servos"""
        for servo_id in self.servos:
            self.interface.write_byte(servo_id, ControlTable.TORQUE_ENABLE, 0)
        logger.info("All servos disabled")

    def _set_torque_limit(self, limit):
        """Set torque limt for all servos"""
        for servo_id in self.servos:
            self.interface.write_word(servo_id, ControlTable.TORQUE_LIMIT, limit)

    def _clamp(self, value, min_value, max_value):
        """Clamp values between min and max"""
        return max(min_value, min(value, max_value))
        
    
        

                

    

