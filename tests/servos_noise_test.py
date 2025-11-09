# quiet_ax12_smooth.py
# Test smooth sinusoidal motion on AX-12A to reduce noise

from dynamixel_sdk import *
import time, math

# ------------------ USER CONFIG ------------------
DXL_ID = 0
BAUDRATE = 1000000
DEVICENAME = '/dev/ttyUSB0'   # Adjust for your system

ADDR_TORQUE_ENABLE = 24
ADDR_GOAL_POSITION = 30
ADDR_MOVING_SPEED = 32
ADDR_CW_COMPLIANCE_MARGIN = 26
ADDR_CCW_COMPLIANCE_MARGIN = 27
ADDR_CW_COMPLIANCE_SLOPE = 28
ADDR_CCW_COMPLIANCE_SLOPE = 29

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# 0–1023 corresponds to ~0–300°
CENTER = 512
AMPLITUDE = 150           # swing range (smaller = quieter)
UPDATE_RATE = 0.05        # seconds between updates (~20 Hz)
PERIOD = 4.0              # seconds per full cycle

# ------------------ SETUP ------------------
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(1.0)

if not portHandler.openPort():
    print("❌ Failed to open port")
    quit()
if not portHandler.setBaudRate(BAUDRATE):
    print("❌ Failed to set baudrate")
    quit()
print("✅ Port open and baudrate set")

# Enable torque
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

# ------------------ QUIET SETTINGS ------------------
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MOVING_SPEED, 150)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CW_COMPLIANCE_MARGIN, 4)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CCW_COMPLIANCE_MARGIN, 4)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CW_COMPLIANCE_SLOPE, 32)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CCW_COMPLIANCE_SLOPE, 32)

print("\nQuiet mode + smooth motion active.")
print("Press Ctrl+C to stop.\n")

# ------------------ SMOOTH MOTION LOOP ------------------
t0 = time.time()
try:
    while True:
        t = time.time() - t0
        angle = CENTER + AMPLITUDE * math.sin(2 * math.pi * t / PERIOD)
        goal = int(angle)
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, goal)
        time.sleep(UPDATE_RATE)
except KeyboardInterrupt:
    print("\nStopping motion...")

# Disable torque when done
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("✅ Servo relaxed and port closed.")
