from luma.core.interface.serial import spi
from luma.oled.device import ssd1306, sh1106
from luma.core.render import canvas
from PIL import ImageFont
import RPi.GPIO as GPIO
from time import sleep

DC = 24
RST = 25

configs = [
    (ssd1306, 64, 48),
    (ssd1306, 128, 32),
    (ssd1306, 68, 48),
    (sh1106, 128, 64)
    ]

for driver, W, H in configs:
    try:
        print(f"Tryning {driver} {H} {W}")
        serial = spi(device=0, port=0, gpio_DC=DC, gpio_RST=RST, bus_speed_hz=8_000_000)
        device = driver(serial, width=W, height=H)
        
        with canvas(device) as draw:
            draw.text((0,0), "Hello", fill=255)
            draw.rectangle((0,0,50,20), outline=255, fill=0)
        sleep(3)
        print("Display Responded!")
        break
    except Exception as e:
        print("Error: ", e)
        sleep(0.5)
        
else:
    print("No display detected")
