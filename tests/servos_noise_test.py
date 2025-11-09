# ax12_scurve_traj.py
# AX-12A test with smooth s-curve acceleration / deceleration

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

ADDR_CW_ANGLE_LIMIT = 6
ADDR_CCW_ANGLE_LIMIT = 8

# Positions (0–1023 ≈ 0–300°)
POS_LEFT  = 350
POS_RIGHT = 700

# Trajectory parameters
MOVE_DURATION = 0.5   # seconds per move (left → right or right → left)
MOVE_STEPS    = 120   # more steps = smoother motion

# ------------------ HELPERS ------------------
def scurve_interpolate(p0, p1, s):
    """
    S-curve interpolation between p0 and p1.
    s in [0,1]. Position, velocity start/end at 0.
    """
    # Smoothstep-like (3s^2 - 2s^3)
    s_smooth = 3 * s * s - 2 * s * s * s
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
packetHandler = PacketHandler(1.0)  # AX series = Protocol 1.0

if not portHandler.openPort():
    print("❌ Failed to open port")
    raise SystemExit

if not portHandler.setBaudRate(BAUDRATE):
    print("❌ Failed to set baudrate")
    raise SystemExit

print("✅ Port opened and baudrate set")

# Enable torque
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_CW_ANGLE_LIMIT, 0)
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_CCW_ANGLE_LIMIT, 1023)

# Quieter base settings
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MOVING_SPEED, 200)  # max speed limit
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CW_COMPLIANCE_MARGIN, 4)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CCW_COMPLIANCE_MARGIN, 4)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CW_COMPLIANCE_SLOPE, 32)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CCW_COMPLIANCE_SLOPE, 32)

print("\nQuiet mode + s-curve trajectory enabled.")
print("Moving smoothly between positions. Press Ctrl+C to stop.\n")

# ------------------ MAIN LOOP ------------------
try:
    current_pos = read_position()
    # First move: gently go to POS_LEFT from wherever we are now
    print("→ Homing to left position with s-curve...")
    scurve_move(current_pos, POS_LEFT, MOVE_DURATION, MOVE_STEPS)

    while True:
        print("→ Left → Right")
        scurve_move(POS_LEFT, POS_RIGHT, MOVE_DURATION, MOVE_STEPS)

        print("← Right → Left")
        scurve_move(POS_RIGHT, POS_LEFT, MOVE_DURATION, MOVE_STEPS)

except KeyboardInterrupt:
    print("\nStopping motion...")

# Disable torque and clean up
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("✅ Servo relaxed and port closed.")
