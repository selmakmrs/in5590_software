from dynamixel_sdk import *  # pip install dynamixel-sdk
import time

# ====== USER SETTINGS ======
DEVICENAME = "/dev/ttyUSB0"  # change if different
BAUDRATE = 1_000_000           # AX-12A default baud
DXL_ID = 0                   # your servo ID (change if needed)
PROTOCOL_VERSION = 1.0       # AX-12A uses Protocol 1.0
# ============================

# Control Table Addresses
ADDR_TORQUE_ENABLE   = 24
ADDR_GOAL_POSITION   = 30
ADDR_PRESENT_POSITION= 36

# Torque values
TORQUE_ENABLE  = 1
TORQUE_DISABLE = 0

# Position limits (0–1023 ≈ 0–300°)
POS_CENTER = 512
POS_LEFT   = 200
POS_RIGHT  = 800

# Initialize PortHandler and PacketHandler
portHandler = PortHandler(DEVICENAME)
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Open port
if not portHandler.openPort():
    raise RuntimeError("❌ Failed to open the port")

# Set baud rate
if not portHandler.setBaudRate(BAUDRATE):
    raise RuntimeError("❌ Failed to set baudrate")

# Enable torque
dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(
    portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_ENABLE)
if dxl_comm_result != COMM_SUCCESS:
    raise RuntimeError(packetHandler.getTxRxResult(dxl_comm_result))
if dxl_error != 0:
    print("⚠️ Error:", packetHandler.getRxPacketError(dxl_error))
else:
    print("✅ Torque enabled")

# Move to positions
for pos in [POS_LEFT, POS_RIGHT, POS_CENTER]:
    dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(
        portHandler, DXL_ID, ADDR_GOAL_POSITION, pos)
    if dxl_comm_result == COMM_SUCCESS:
        print(f"Moving to position {pos}...")
    else:
        print("Write error:", packetHandler.getTxRxResult(dxl_comm_result))
    time.sleep(2)

# Read final position
dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(
    portHandler, DXL_ID, ADDR_PRESENT_POSITION)
if dxl_comm_result == COMM_SUCCESS:
    print(f"✅ Present Position: {dxl_present_position}")
else:
    print("Read error:", packetHandler.getTxRxResult(dxl_comm_result))

# Disable torque and close port
packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_TORQUE_ENABLE, TORQUE_DISABLE)
portHandler.closePort()
print("🔌 Torque disabled and port closed.")
