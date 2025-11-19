from led import LED


import threading
import queue
import time




led = LED()
led.start()
cmd_queue = queue.Queue()
EMOTIONS = ["happy","sad","angry", "suprise", "fear"]
COLORS = led.color_codes.keys()

def input_thread():
    while True:
        cmd = input("> ").strip().lower()
        cmd_queue.put(cmd)




# start the input reader
threading.Thread(target=input_thread, daemon=True).start()

# MAIN LOOP
while True:
    # 1) update display / sequences

    # 2) check if we got a command
    try:
        cmd = cmd_queue.get_nowait()
    except queue.Empty:
        cmd = None

    if cmd and cmd in EMOTIONS or cmd == "idle":
        led.show_emotion(cmd)

    elif cmd and cmd in COLORS:
        led.change_color(cmd)
        

    # 3) small sleep so we don’t burn CPU
    time.sleep(0.02)   # ~50 FPS
		
    



