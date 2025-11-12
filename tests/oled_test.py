from oled import OLED
from oled.roboeyes import *

import threading
import queue
import time




oled = OLED()
cmd_queue = queue.Queue()
EMOTIONS = ["happy","sad","angry", "confused"]

def input_thread():
    while True:
        cmd = input("> ").strip().lower()
        cmd_queue.put(cmd)




# start the input reader
threading.Thread(target=input_thread, daemon=True).start()

# MAIN LOOP
while True:
    # 1) update display / sequences
    oled.update()

    # 2) check if we got a command
    try:
        cmd = cmd_queue.get_nowait()
    except queue.Empty:
        cmd = None

    if cmd and cmd in EMOTIONS:
        oled.run_emotion(cmd)
        

    # 3) small sleep so we don’t burn CPU
    time.sleep(0.02)   # ~50 FPS
		
    



