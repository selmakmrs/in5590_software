#!/usr/bin/env python3
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import time

# --- Initialize both OLEDs ---
oled1 = ssd1306(i2c(port=1, address=0x3C),rotate=1)   # Bus 1 -> pins 3 & 5
oled2 = ssd1306(i2c(port=11, address=0x3C),rotate=3)   # Bus 0 -> pins 27 & 28

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
        if count > 5:
          break
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

robo = RoboEyes(lcd, 128, 128, frame_rate=50, on_show=lcd.on_show)

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



sequences = []


seq = robo.sequences.add( "demo")
seq.step( 2000, lambda robo : robo.open() ) # at 2000 ms from start --> open eyes.
seq.step( 4000, lambda robo : robo.set_mood(HAPPY) ) # Lamba must call function! Cannot assign property! 
seq.step( 4010, lambda robo : robo.laugh() )
seq.step( 6000, lambda robo : robo.set_mood(TIRED) )
seq.step( 7000, lambda robo : robo.set_mood(CURIOUS) )
# seq.step( 9000, lambda robo : robo.set_mood(DEFAULT) )
seq.step( 10000, lambda robo : robo.close() )
seq.step( 11000, lambda robo : print(seq.name,"done !") )  # Also signal the end of sequence at 10 sec

sequences.append(seq)

seq = robo.sequences.add("happy")
seq.step( 2000, lambda robo : robo.open() ) # at 2000 ms from start --> open eyes.
seq.step( 4000, lambda robo : robo.set_mood(HAPPY) ) # Lamba must call function! Cannot assign property! 
seq.step( 4010, lambda robo : robo.laugh() )
seq.step( 9000, lambda robo : robo.laugh() )
# seq.step( 10000, lambda robo : robo.close() )
seq.step( 9000, lambda robo : robo.set_mood(DEFAULT) )
seq.step( 11000, lambda robo : print(seq.name,"done !") )
sequences.append(seq)



# 1. GREETING SEQUENCE - Friendly welcome
seq = robo.sequences.add("greeting")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_mood(HAPPY))
seq.step(1500, lambda robo: robo.blink())
seq.step(2500, lambda robo: robo.set_position(N))
seq.step(3500, lambda robo: robo.set_position(DEFAULT))
seq.step(4000, lambda robo: robo.set_mood(DEFAULT))
seq.step(5000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 2. CURIOUS SCAN - Looking around curiously
seq = robo.sequences.add("curious_scan")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_mood(CURIOUS))
seq.step(1500, lambda robo: robo.set_position(W))
seq.step(3000, lambda robo: robo.set_position(E))
seq.step(4500, lambda robo: robo.set_position(N))
seq.step(6000, lambda robo: robo.set_position(DEFAULT))
seq.step(6500, lambda robo: robo.blink())
seq.step(7500, lambda robo: robo.set_mood(DEFAULT))
seq.step(8000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 3. CONFUSED - Expressing confusion
seq = robo.sequences.add("confused")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.confuse())
seq.step(2000, lambda robo: robo.set_position(NW))
seq.step(3000, lambda robo: robo.confuse())
seq.step(4000, lambda robo: robo.set_position(NE))
seq.step(5000, lambda robo: robo.confuse())
seq.step(6000, lambda robo: robo.set_position(DEFAULT))
seq.step(7000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 4. ANGRY OUTBURST - Getting angry
seq = robo.sequences.add("angry_outburst")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_mood(ANGRY))
seq.step(1500, lambda robo: robo.set_position(E))
seq.step(2000, lambda robo: robo.set_position(W))
seq.step(2500, lambda robo: robo.set_position(E))
seq.step(3000, lambda robo: robo.set_position(DEFAULT))
seq.step(4000, lambda robo: robo.close())
seq.step(5000, lambda robo: robo.open())
seq.step(6000, lambda robo: robo.set_mood(TIRED))
seq.step(8000, lambda robo: robo.set_mood(DEFAULT))
seq.step(9000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 5. SLEEPY - Getting tired and falling asleep
seq = robo.sequences.add("sleepy")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_mood(TIRED))
seq.step(2000, lambda robo: robo.blink())
seq.step(3500, lambda robo: robo.blink())
seq.step(4500, lambda robo: robo.blink())
seq.step(5500, lambda robo: robo.close())
seq.step(7000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 6. SURPRISE - Surprised reaction
seq = robo.sequences.add("surprise")
seq.step(500, lambda robo: robo.close())
seq.step(1000, lambda robo: robo.open())
seq.step(1100, lambda robo: robo.eyes_width(leftEye=40, rightEye=40))
seq.step(1200, lambda robo: robo.eyes_height(leftEye=40, rightEye=40))
seq.step(2000, lambda robo: robo.blink())
seq.step(3000, lambda robo: robo.eyes_width(leftEye=18, rightEye=18))
seq.step(3100, lambda robo: robo.eyes_height(leftEye=18, rightEye=18))
seq.step(4000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 7. SCARY MODE - Frightening look
seq = robo.sequences.add("scary")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_mood(SCARY))
seq.step(1500, lambda robo: robo.eyes_width(leftEye=30, rightEye=30))
seq.step(5000, lambda robo: robo.set_mood(DEFAULT))
seq.step(5500, lambda robo: robo.eyes_width(leftEye=18, rightEye=18))
seq.step(6000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 8. FROZEN SCARED - Frozen in fear
seq = robo.sequences.add("frozen")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_mood(FROZEN))
seq.step(1500, lambda robo: robo.eyes_width(leftEye=25, rightEye=25))
seq.step(4000, lambda robo: robo.set_mood(DEFAULT))
seq.step(4500, lambda robo: robo.eyes_width(leftEye=18, rightEye=18))
seq.step(5000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)

# 9. HAPPY LAUGH - Joyful laughing
seq = robo.sequences.add("happy_laugh")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_mood(HAPPY))
seq.step(1500, lambda robo: robo.laugh())
seq.step(3000, lambda robo: robo.laugh())
seq.step(4500, lambda robo: robo.laugh())
seq.step(6000, lambda robo: robo.set_mood(DEFAULT))
seq.step(7000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 10. WINK LEFT - Playful left wink
seq = robo.sequences.add("wink_left")
seq.step(500, lambda robo: robo.open())
seq.step(1500, lambda robo: robo.wink(left=True))
seq.step(3000, lambda robo: robo.set_mood(HAPPY))
seq.step(4000, lambda robo: robo.set_mood(DEFAULT))
seq.step(5000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 11. WINK RIGHT - Playful right wink
seq = robo.sequences.add("wink_right")
seq.step(500, lambda robo: robo.open())
seq.step(1500, lambda robo: robo.wink(right=True))
seq.step(3000, lambda robo: robo.set_mood(HAPPY))
seq.step(4000, lambda robo: robo.set_mood(DEFAULT))
seq.step(5000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)

# 12. LOOK AROUND - Systematic scanning
seq = robo.sequences.add("look_around")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_position(NW))
seq.step(2000, lambda robo: robo.set_position(N))
seq.step(3000, lambda robo: robo.set_position(NE))
seq.step(4000, lambda robo: robo.set_position(E))
seq.step(5000, lambda robo: robo.set_position(SE))
seq.step(6000, lambda robo: robo.set_position(S))
seq.step(7000, lambda robo: robo.set_position(SW))
seq.step(8000, lambda robo: robo.set_position(W))
seq.step(9000, lambda robo: robo.set_position(DEFAULT))
seq.step(9500, lambda robo: robo.blink())
seq.step(10000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 13. THINKING - Contemplative expression
seq = robo.sequences.add("thinking")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_position(NW))
seq.step(2000, lambda robo: robo.set_mood(CURIOUS))
seq.step(4000, lambda robo: robo.blink())
seq.step(6000, lambda robo: robo.set_position(DEFAULT))
seq.step(7000, lambda robo: robo.set_mood(DEFAULT))
seq.step(8000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 14. CYCLOPS SCAN - One-eyed scanning
seq = robo.sequences.add("cyclops_scan")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_cyclops(True))
seq.step(1500, lambda robo: robo.set_position(W))
seq.step(3000, lambda robo: robo.set_position(E))
seq.step(4500, lambda robo: robo.set_position(DEFAULT))
seq.step(5000, lambda robo: robo.blink())
seq.step(6000, lambda robo: robo.set_cyclops(False))
seq.step(7000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)


# 15. EMOTIONAL ROLLERCOASTER - Rapid mood changes
seq = robo.sequences.add("emotional_rollercoaster")
seq.step(500, lambda robo: robo.open())
seq.step(1000, lambda robo: robo.set_mood(HAPPY))
seq.step(1500, lambda robo: robo.laugh())
seq.step(3000, lambda robo: robo.set_mood(CURIOUS))
seq.step(4000, lambda robo: robo.confuse())
seq.step(5500, lambda robo: robo.set_mood(ANGRY))
seq.step(7000, lambda robo: robo.set_mood(TIRED))
seq.step(8500, lambda robo: robo.set_mood(DEFAULT))
seq.step(9000, lambda robo: robo.blink())
seq.step(10000, lambda robo: print(seq.name, "done!"))
sequences.append(seq)




# RoboEyes Initial state
robo.position = DEFAULT
robo.close()

# Start the sequence ZERO
# robo.sequences[0].start()
# robo.sequences.get("demo").start()
# robo.sequences.get("happy").start()

# seq = robo.sequences.get("happy")

seq.start()
i = 0
seq = sequences[i]
seq.start()

while True:
    robo.update()
    if seq.done and i < len(sequences)-1:
        i += 1
        seq = sequences[i]
        print("Starting: ", seq.name)
        seq.start()
