#!/usr/bin/env python3
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import time

# --- Initialize both OLEDs ---
oled1 = ssd1306(i2c(port=1, address=0x3C))   # Bus 1 -> pins 3 & 5
oled2 = ssd1306(i2c(port=11, address=0x3C))   # Bus 0 -> pins 27 & 28

font = ImageFont.load_default()

def draw_text(oled, text):
    img = Image.new("1", (oled.width, oled.height))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, oled.width, oled.height), outline=0, fill=0)
    draw.text((2, 2), text, font=font, fill=255)
    oled.display(img)

# --- Main loop ---
print("Displaying messages on both OLEDs. Press Ctrl+C to exit.")
count = 0
try:
    while True:
        draw_text(oled1, f"OLED #1\nCount: {count}")
        draw_text(oled2, f"OLED #2\nCount: {count}")
        count += 1
        time.sleep(1)
except KeyboardInterrupt:
    print("\nExiting test...")



import time
from i2c_ssd_shim_dual import LumaSSD1306Shim

# ---- MicroPython shims ----
try:
    from micropython import const
except ImportError:
    const = lambda x: x

if not hasattr(time, "ticks_ms"):
    time.ticks_ms  = lambda: int(time.time() * 1000)
    time.ticks_diff = lambda a, b: a - b
    time.ticks_add  = lambda a, b: a + b

try:
    from fbutil import FBUtil
except ImportError:
    class FBUtil:
        def __init__(self, fb): pass



# ---- Run RoboEyes ----
from roboeyes import *

lcd = LumaSSD1306Shim()

def on_show(_):  # called each frame by RoboEyes
    lcd.show()

robo = RoboEyes(lcd, 128, 64, frame_rate=60, on_show=lcd.on_show)

robo.set_auto_blinker(ON, 3, 2)
robo.set_idle_mode(ON, 2, 2)
robo.eyes_width(40,40)
robo.eyes_height(45,45)
robo.eyes_spacing(40)

# print("Running… close the window or Ctrl+C to exit.")
# while True:
#     robo.update()
#     time.sleep(1/60)

import random, time, math






seq = robo.sequences.add( "demo")
seq.step( 2000, lambda robo : robo.open() ) # at 2000 ms from start --> open eyes.
seq.step( 4000, lambda robo : robo.set_mood(HAPPY) ) # Lamba must call function! Cannot assign property! 
seq.step( 4010, lambda robo : robo.laugh() )
seq.step( 6000, lambda robo : robo.set_mood(TIRED) )
seq.step( 7000, lambda robo : robo.set_mood(CURIOUS) )
# seq.step( 9000, lambda robo : robo.set_mood(DEFAULT) )
seq.step( 10000, lambda robo : robo.close() )
seq.step( 11000, lambda robo : print(seq.name,"done !") )  # Also signal the end of sequence at 10 sec

seq = robo.sequences.add("happy")
seq.step( 2000, lambda robo : robo.open() ) # at 2000 ms from start --> open eyes.
seq.step( 4000, lambda robo : robo.set_mood(HAPPY) ) # Lamba must call function! Cannot assign property! 
seq.step( 4010, lambda robo : robo.laugh() )
seq.step( 9000, lambda robo : robo.laugh() )
# seq.step( 10000, lambda robo : robo.close() )
seq.step( 9000, lambda robo : robo.set_mood(DEFAULT) )
seq.step( 11000, lambda robo : print(seq.name,"done !") ) 

# RoboEyes Initial state
robo.position = DEFAULT
robo.close()

# Start the sequence ZERO
# robo.sequences[0].start()
# robo.sequences.get("demo").start()
# robo.sequences.get("happy").start()

seq = robo.sequences.get("happy")

seq.start()

while True:
	# update eyes drawings
	robo.update()  

	# # if robo.sequences.done: # Check all sequences done
	# if robo.sequences.get("demo").done: # Check sequence ZERO done
		
