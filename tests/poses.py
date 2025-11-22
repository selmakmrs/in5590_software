from led import LED
from oled import OLED
from oled.roboeyes import *


import threading
import queue
import time


oled = OLED()

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

try: 
    # MAIN LOOP
    while True:
        # oled.update()
        # 1) update display / sequences

        # 2) check if we got a command
        try:
            cmd = cmd_queue.get_nowait()
        except queue.Empty:
            cmd = None

        if cmd and cmd in EMOTIONS or cmd == "idle":
            match cmd:
                case "happy":
                    led.change_color("yellow")
                    oled.roboeyes.set_mood(HAPPY)
                    oled.roboeyes.set_auto_blinker(OFF)
                    oled.roboeyes.set_idle_mode(OFF)
                    oled.roboeyes.set_position(DEFAULT)
                    time.sleep(1)
                    oled.update()

                case "sad":
                    led.change_color("sad")
                    oled.roboeyes.set_mood(TIRED)
                    oled.roboeyes.set_auto_blinker(OFF)
                    oled.roboeyes.set_position(DEFAULT)

                case "angry":
                    led.change_color("red")
                    oled.roboeyes.set_mood(ANGRY)
                    oled.roboeyes.set_auto_blinker(OFF)
                    oled.roboeyes.set_position(DEFAULT)


        elif cmd and cmd in COLORS:
            led.change_color(cmd)
            

        # 3) small sleep so we don’t burn CPU
        time.sleep(0.02)   # ~50 FPS

except KeyboardInterrupt:
    led.close()
            