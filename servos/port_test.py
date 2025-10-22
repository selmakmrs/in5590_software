from dynamixel_sdk import PortHandler
device = "/dev/ttyUSB0"
port = PortHandler(device)
print(port.openPort())