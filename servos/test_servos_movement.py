#!/usr/bin/env python3
from dynamixel_sdk import *
import time

# ========= CONFIGURATION =========
DEVICENAME = "/dev/ttyUSB0"   # Adjust if needed
BAUDRATE   = 1000000
PROTOCOL_VERSION = 1.0

# IDs
HEAD_ID = 0
BODY_ID = 3
BASE_ID = 1
SERVOS = [HEAD_ID, BODY_ID, BASE_ID]

# --- Control Table addresses (AX-12A) ---
ADDR_TORQUE_ENABLE     = 24
ADDR_CW_ANGLE_LIMIT    = 6
ADDR_CCW_ANGLE_LIMIT   = 8
ADDR_GOAL_POSITION     = 30
ADDR_MOVING_SPEED      = 32
ADDR_TORQUE_LIMIT      = 34
ADDR_PRESENT_POSITION  = 36

TORQUE_ENABLE  = 1
TORQUE_DISABLE = 0

# ========= UTILITY FUNCTIONS =========
def open_bus(dev, baud):
    port = PortHandler(dev)
    pkt  = PacketHandler(PROTOCOL_VERSION)
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
    return found

def torque_all(port, pkt, ids, enable=True):
    for i in ids:
        pkt.write1ByteTxRx(port, i, ADDR_TORQUE_ENABLE,
                           TORQUE_ENABLE if enable else TORQUE_DISABLE)

def set_joint_mode(port, pkt, dxl_id, cw_limit=0, ccw_limit=1023):
    pkt.write2ByteTxRx(port, dxl_id, ADDR_CW_ANGLE_LIMIT, cw_limit)
    pkt.write2ByteTxRx(port, dxl_id, ADDR_CCW_ANGLE_LIMIT, ccw_limit)

def set_wheel_mode(port, pkt, dxl_id):
    pkt.write2ByteTxRx(port, dxl_id, ADDR_CW_ANGLE_LIMIT, 0)
    pkt.write2ByteTxRx(port, dxl_id, ADDR_CCW_ANGLE_LIMIT, 0)

def set_torque_limit(port, pkt, dxl_id, limit=1023):
    pkt.write2ByteTxRx(port, dxl_id, ADDR_TORQUE_LIMIT, max(0, min(1023, limit)))

def move_position(port, pkt, dxl_id, pos):
    pos = max(0, min(1023, pos))
    pkt.write2ByteTxRx(port, dxl_id, ADDR_GOAL_POSITION, pos)

def wheel_speed(port, pkt, dxl_id, speed):
    """
    speed: -1023..1023
    """
    direction = 0
    if speed < 0:
        direction = 1
        speed = -speed
    if speed > 1023:
        speed = 1023
    value = speed | (direction << 10)
    pkt.write2ByteTxRx(port, dxl_id, ADDR_MOVING_SPEED, value)

def read_pos(port, pkt, dxl_id):
    pos, comm, err = pkt.read2ByteTxRx(port, dxl_id, ADDR_PRESENT_POSITION)
    return pos if comm == COMM_SUCCESS and err == 0 else None

# ========= TEST SEQUENCE =========
if __name__ == "__main__":
    port, pkt = open_bus(DEVICENAME, BAUDRATE)

    found = scan_ids(port, pkt, SERVOS)
    if not found:
        port.closePort()
        raise SystemExit("❌ No servos detected.")
    print("✅ Found servos:", found)

    torque_all(port, pkt, found, True)
    print("⚙️ Torque enabled")

    # --- 1️⃣ JOINT MODE TEST ---
    print("\n🔹 Joint mode test: moving each servo sequentially")
    for i in found:
        set_joint_mode(port, pkt, i)
        move_position(port, pkt, i, 300)
        time.sleep(1.0)
        move_position(port, pkt, i, 700)
        time.sleep(1.0)
        move_position(port, pkt, i, 512)
        time.sleep(1.0)
        pos = read_pos(port, pkt, i)
        print(f"Servo {i} position: {pos}")

    # --- 2️⃣ WHEEL MODE TEST ---
    print("\n🔹 Wheel mode test: continuous rotation")
    for i in found:
        set_wheel_mode(port, pkt, i)
        set_torque_limit(port, pkt, i, 800)

    print("Spinning forward...")
    for i in found:
        wheel_speed(port, pkt, i, 300)
    time.sleep(2)

    print("Reversing...")
    for i in found:
        wheel_speed(port, pkt, i, -300)
    time.sleep(2)

    print("Stopping...")
    for i in found:
        wheel_speed(port, pkt, i, 0)
    time.sleep(1)

    # --- 3️⃣ Return to JOINT MODE ---
    print("\n🔹 Resetting to joint mode & center")
    for i in found:
        set_joint_mode(port, pkt, i)
        move_position(port, pkt, i, 512)
    time.sleep(2)

    # --- Cleanup ---
    torque_all(port, pkt, found, False)
    port.closePort()
    print("✅ Test complete and port closed.")
