from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import time

# If your display address is not 0x3C, change it here
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial, rotate=1)



# Create blank image
width = device.width
height = device.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

print("Height: ", height)
print("width: ", width)

# Clear
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some text
text = "Hello Pi!"
font = ImageFont.load_default()
draw.text((0, 0), text, font=font, fill=255)

# Send to display
device.display(image)

time.sleep(10)


# run_roboeyes_desktop.py
import time
from ssd_shim_i2c import LumaSSD1306Shim

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
robo.eyes_width(37,37)
robo.eyes_height(43,43)
robo.eyes_spacing(30)

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
		
    


