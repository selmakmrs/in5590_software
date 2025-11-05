from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont
import time

# If your display address is not 0x3C, change it here
serial = i2c(port=1, address=0x3C)
device = ssd1306(serial)

# Create blank image
width = device.width
height = device.height
image = Image.new("1", (width, height))
draw = ImageDraw.Draw(image)

# Clear
draw.rectangle((0, 0, width, height), outline=0, fill=0)

# Draw some text
text = "Hello Pi!"
font = ImageFont.load_default()
draw.text((0, 0), text, font=font, fill=255)

# Send to display
device.display(image)

time.sleep(10)
