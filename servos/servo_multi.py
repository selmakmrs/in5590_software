from dynamixel_sdk import *
import time

# ====== EDIT THESE ======
DEVICENAME = "/dev/ttyUSB0"      # <- your adapter's COM port on Windows
BAUDRATE   = 1000000     # AX-12A default
ID_RANGE   = range(0,2) # scan IDs 1..20; adjust as needed
# ========================

PROTOCOL_VERSION = 1.0

# Control Table (AX-12A, Protocol 1.0)
ADDR_TORQUE_ENABLE     = 24   # 1 byte
ADDR_GOAL_POSITION     = 30   # 2 bytes
ADDR_PRESENT_POSITION  = 36   # 2 bytes

TORQUE_ENABLE  = 1
TORQUE_DISABLE = 0

def open_bus(dev, baud):
    port = PortHandler(dev)
    pkt  = PacketHandler(PROTOCOL_VERSION)
    if not port.openPort():
        raise RuntimeError("Failed to open port")
    if not port.setBaudRate(baud):
        raise RuntimeError("Failed to set baudrate")
    return port, pkt

def scan_ids(port, pkt, ids):
    found = []
    for i in ids:
        model, comm, err = pkt.ping(port, i)
        if comm == COMM_SUCCESS and err == 0:
            found.append(i)
    return found

def torque_all(port, pkt, ids, enable=True):
    for i in ids:
        pkt.write1ByteTxRx(port, i, ADDR_TORQUE_ENABLE, TORQUE_ENABLE if enable else TORQUE_DISABLE)

def sync_move(port, pkt, ids, positions):
    """positions: dict {id: goal_pos(0..1023)}"""
    # GroupSyncWrite: addr=GOAL_POSITION, length=2 bytes
    group = GroupSyncWrite(port, pkt, ADDR_GOAL_POSITION, 2)
    for i in ids:
        pos = positions.get(i, 512)             # default center if not provided
        param = [DXL_LOBYTE(pos), DXL_HIBYTE(pos)]
        group.addParam(i, bytes(param))
    group.txPacket()
    group.clearParam()

def read_positions(port, pkt, ids):
    vals = {}
    for i in ids:
        pos, comm, err = pkt.read2ByteTxRx(port, i, ADDR_PRESENT_POSITION)
        if comm == COMM_SUCCESS and err == 0:
            vals[i] = pos
    return vals

if __name__ == "__main__":
    port, pkt = open_bus(DEVICENAME, BAUDRATE)

    # 1) find all connected servos
    ids = scan_ids(port, pkt, ID_RANGE)
    if not ids:
        port.closePort()
        raise SystemExit("No servos found in ID range. Check power/IDs.")

    print("Found IDs:", ids)

    # 2) enable torque on all
    torque_all(port, pkt, ids, True)

    # 3) move them simultaneously: left -> right -> center
    #    choose slightly different goals per ID for fun
    goals1 = {i: 350 + (i*10 % 80) for i in ids}
    goals2 = {i: 700 - (i*10 % 80) for i in ids}
    center = {i: 512 for i in ids}

    for goals in (goals1, goals2, center):
        sync_move(port, pkt, ids, goals)
        time.sleep(2.0)
        print("Positions:", read_positions(port, pkt, ids))

    # 4) disable torque and close
    torque_all(port, pkt, ids, False)
    port.closePort()
    print("Done.")
