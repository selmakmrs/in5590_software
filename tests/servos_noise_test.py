# ax12_scurve_traj_fast.py
# AX-12A test with faster s-curve motion (still smooth)

from dynamixel_sdk import *
import time
import math

# ------------------ USER CONFIG ------------------
DXL_ID = 3
BAUDRATE = 1000000
DEVICENAME = '/dev/ttyUSB0'   # e.g. 'COM3' on Windows

# Control table addresses (AX-12A, Protocol 1.0)
ADDR_TORQUE_ENABLE          = 24
ADDR_GOAL_POSITION          = 30
ADDR_MOVING_SPEED           = 32
ADDR_CW_COMPLIANCE_MARGIN   = 26
ADDR_CCW_COMPLIANCE_MARGIN  = 27
ADDR_CW_COMPLIANCE_SLOPE    = 28
ADDR_CCW_COMPLIANCE_SLOPE   = 29
ADDR_PRESENT_POSITION       = 36

TORQUE_ENABLE  = 1
TORQUE_DISABLE = 0

# Positions (0–1023 ≈ 0–300°)
POS_LEFT  = 350
POS_RIGHT = 700

# ✅ FASTER TRAJECTORY PARAMETERS
MOVE_DURATION = 1.5   # seconds per move (faster than 3.0)
MOVE_STEPS    = 180   # more steps to keep motion smooth

# ------------------ HELPERS ------------------
def scurve_interpolate(p0, p1, s):
    """
    S-curve interpolation between p0 and p1.
    s in [0,1]. Position & velocity start/end at 0.
    """
    s_smooth = 3 * s * s - 2 * s * s * s   # smoothstep (3s² - 2s³)
    return p0 + (p1 - p0) * s_smooth

def read_position():
    pos, comm_result, error = packetHandler.read2ByteTxRx(
        portHandler, DXL_ID, ADDR_PRESENT_POSITION
    )
    if comm_result != COMM_SUCCESS:
        print("Read error:", packetHandler.getTxRxResult(comm_result))
    elif error != 0:
        print("Servo error:", packetHandler.getRxPacketError(error))
    return pos

def scurve_move(start_pos, end_pos, duration, steps):
    dt = duration / steps
    for i in range(steps + 1):
        s = i / float(steps)
        goal = int(scurve_interpolate(start_pos, end_pos, s))
        packetHandler.write2ByteTxRx(
            portHandler, DXL_ID, ADDR_GOAL_POSITION, goal
        )
        time.sleep(dt)

# ------------------ SETUP ------------------
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(1.0)  # Protocol 1.0 for AX-series

if not portHandler.openPort():
    print("❌ Failed to open port")
    raise SystemExit

if not portHandler.setBaudRate(BAUDRATE):
    print("❌ Failed to set baudrate")
    raise SystemExit

print("✅ Port opened and baudrate set")

# Enable torque
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

# ------------------ "FASTER BUT QUIET" SETTINGS ------------------
# Higher max speed, but not full 1023
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MOVING_SPEED, 600)

# Compliance: still a bit soft, but slightly stiffer slopes
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CW_COMPLIANCE_MARGIN, 4)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CCW_COMPLIANCE_MARGIN, 4)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CW_COMPLIANCE_SLOPE, 16)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CCW_COMPLIANCE_SLOPE, 16)

print("\nFast s-curve trajectory enabled.")
print("Moving smoothly between positions. Press Ctrl+C to stop.\n")

# ------------------ MAIN LOOP ------------------
try:
    current_pos = read_position()
    print("→ Homing to left position with s-curve...")
    scurve_move(current_pos, POS_LEFT, MOVE_DURATION, MOVE_STEPS)

    while True:
        print("→ Left → Right (fast)")
        scurve_move(POS_LEFT, POS_RIGHT, MOVE_DURATION, MOVE_STEPS)

        print("← Right → Left (fast)")
        scurve_move(POS_RIGHT, POS_LEFT, MOVE_DURATION, MOVE_STEPS)

except KeyboardInterrupt:
    print("\nStopping motion...")

# Disable torque and clean up
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("✅ Servo relaxed and port closed.")
