from luma.core.interface.serial import spi
from luma.oled.device import ssd1306, sh1106
from luma.core.render import canvas
from PIL import ImageFont, Image, ImageDraw
import RPi.GPIO as GPIO
from time import sleep


W, H = 64, 48
speed = 1_000_000
DC = 23
RST = 24

font = ImageFont.load_default()

spi0 = spi(port=0, device=0, gpio_DC=DC, gpio_RST=RST, bus_speed_hz=speed)
spi1 = spi(port=0, device=1, gpio_DC=DC, gpio_RST=RST, bus_speed_hz=speed)
    
oled0 = ssd1306(spi0, width=W, height=H)
oled1 = ssd1306(spi1, width=W, height=H)

font = ImageFont.load_default()

def draw_help(oled, text):
    img = Image.new("1",(W,H), 0)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, W-1, H-1), outline=1, fill=0)
    d.text((4,16), text, font=font, fill=1)
    oled.display(img)
    
    
def make_demo_frame(text="Split Demo"):
    frame = Image.new("1", (W+W, H), 0)
    
    d = ImageDraw.Draw(frame)
    d.rectangle((0, 0, W*2-1, H-1), outline=1)
    d.line((W, 0, W, H-1), fill = 1)
    d.text((W - 30, H//2-6), text, font=font, fill=1)
    
    d.line((0, 0, W*2-1, H-1), fill=1)
    d.line((0, H-1, W*2-1, 0), fill=1)
    
    return frame


def push_frame(frame, oled0, oled1):
    left_img = frame.crop((0, 0, W, H))
    right_img = frame.crop((W, 0, W*2, H))
    oled0.display(left_img)
    oled1.display(right_img)
    
    
    
    
print("Testing Both Displays")


draw_help(oled0, "Screen 0")
draw_help(oled1, "Screen 1")

sleep(10)
frame = make_demo_frame()
while True:
    push_frame(frame, oled0, oled1)

   


    

