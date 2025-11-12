from oled import OLED
from oled.roboeyes import *

import threading
import queue
import time




# oled = OLED()
# cmd_queue = queue.Queue()
# EMOTIONS = ["happy","sad","angry", "confused"]

# def input_thread():
#     while True:
#         cmd = input("> ").strip().lower()
#         cmd_queue.put(cmd)




# # start the input reader
# threading.Thread(target=input_thread, daemon=True).start()

# # MAIN LOOP
# while True:
#     # 1) update display / sequences
#     oled.update()

#     # 2) check if we got a command
#     try:
#         cmd = cmd_queue.get_nowait()
#     except queue.Empty:
#         cmd = None

#     if cmd and cmd in EMOTIONS:
#         oled.run_emotion(cmd)
        

#     # 3) small sleep so we don’t burn CPU
#     time.sleep(0.02)   # ~50 FPS
		
    

#!/usr/bin/env python3
from time import sleep
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306, sh1106
from PIL import Image, ImageDraw, ImageFont

def test_display(device):
    """Draw a simple test pattern on the screen."""
    img = Image.new("1", (device.width, device.height), 0)
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    draw.rectangle((0, 0, device.width - 1, device.height - 1), outline=1, fill=0)
    draw.text((4, 4), f"{device.__class__.__name__}", font=font, fill=1)
    draw.text((4, 20), f"{device.width}x{device.height}", font=font, fill=1)
    draw.line((0, 0, device.width, device.height), fill=1)
    draw.line((0, device.height, device.width, 0), fill=1)
    device.display(img)
    sleep(2)
    device.clear()

def try_driver(cls, name, serial):
    """Try initializing a driver class and show test image."""
    print(f"Trying {name}...")
    try:
        device = cls(serial, width=128, height=64)
        test_display(device)
        print(f"✅ {name} appears to work!\n")
        return True
    except Exception as e:
        print(f"❌ {name} failed: {e}\n")
        return False

def main():
    serial = i2c(port=1, address=0x3C)   # change address if needed (e.g. 0x3D)
    ok1 = try_driver(ssd1306, "SSD1306", serial)
    ok2 = try_driver(sh1106, "SH1106", serial)
    if not (ok1 or ok2):
        print("No response from either driver. Check wiring and I2C address.")

if __name__ == "__main__":
    main()


