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
