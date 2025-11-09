# quiet_ax12_test.py
# Test script to reduce AX-12A servo noise

from dynamixel_sdk import *  # Uses Dynamixel SDK library
import time

# ------------------ USER CONFIG ------------------
DXL_ID = 0                 # Your servo ID
BAUDRATE = 1000000         # Typical default for AX-12A
DEVICENAME = '/dev/ttyUSB0'  # Adjust for your system (e.g. COM3 on Windows)

ADDR_TORQUE_ENABLE = 24
ADDR_GOAL_POSITION = 30
ADDR_MOVING_SPEED = 32
ADDR_CW_COMPLIANCE_MARGIN = 26
ADDR_CCW_COMPLIANCE_MARGIN = 27
ADDR_CW_COMPLIANCE_SLOPE = 28
ADDR_CCW_COMPLIANCE_SLOPE = 29
ADDR_PRESENT_POSITION = 36

TORQUE_ENABLE = 1
TORQUE_DISABLE = 0

# Positions (0–1023 → 0–300 degrees)
POS_LEFT = 300
POS_RIGHT = 700

# ------------------ SETUP ------------------
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(1.0)  # AX-series uses protocol 1.0

if portHandler.openPort():
    print("Port opened successfully!")
else:
    print("Failed to open port.")
    quit()

if portHandler.setBaudRate(BAUDRATE):
    print("Baudrate set.")
else:
    print("Failed to set baudrate.")
    quit()

# Enable torque
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)

# ------------------ QUIET SETTINGS ------------------
# Lower speed
packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_MOVING_SPEED, 150)

# Soften compliance parameters
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CW_COMPLIANCE_MARGIN, 4)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CCW_COMPLIANCE_MARGIN, 4)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CW_COMPLIANCE_SLOPE, 32)
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_CCW_COMPLIANCE_SLOPE, 32)

print("\nQuiet mode parameters set.")
print("Moving slowly back and forth... (Press Ctrl+C to stop)\n")

# ------------------ MOTION LOOP ------------------
try:
    while True:
        print("→ Moving right")
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, POS_RIGHT)
        time.sleep(2.5)

        print("← Moving left")
        packetHandler.write2ByteTxRx(portHandler, DXL_ID, ADDR_GOAL_POSITION, POS_LEFT)
        time.sleep(2.5)

except KeyboardInterrupt:
    print("\nStopping test...")

# Disable torque
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("Port closed.")
