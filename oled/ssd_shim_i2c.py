# ---- SSD1306/SH1106 SPI display backed by luma.oled ----
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306, sh1106
from PIL import Image, ImageDraw, ImageFont

class LumaSSD1306Shim:
    """
    Drop-in replacement for your previous shim, but writes to a real SPI OLED.
    Matches the MicroPython-ish API RoboEyes expects (fill, fill_rrect, etc.).
    """
    def __init__(self, width=64, height=48, rotate=0,
                 ce=0, driver="ssd1306", dc=24, rst=25, speed=1_000_000):
        self.width, self.height = width, height
        self._img = Image.new("1", (width, height), 0)
        self._draw = ImageDraw.Draw(self._img)
        self._font = ImageFont.load_default()

        serial = i2c(port=1, address=0x3C)
        device = ssd1306(serial)

    # --- MicroPython-ish API used by RoboEyes ---
    def fill(self, c):  # clear/fill
        self._draw.rectangle((0, 0, self.width-1, self.height-1), fill=1 if c else 0)

    def pixel(self, x, y, c=1):
        if 0 <= x < self.width and 0 <= y < self.height:
            self._draw.point((x, y), fill=1 if c else 0)

    def hline(self, x, y, w, c=1):
        self._draw.line((x, y, x+w-1, y), fill=1 if c else 0)

    def vline(self, x, y, h, c=1):
        self._draw.line((x, y, x, y+h-1), fill=1 if c else 0)

    def line(self, x1, y1, x2, y2, c=1):
        self._draw.line((x1, y1, x2, y2), fill=1 if c else 0)

    def rect(self, x, y, w, h, c=1):
        self._draw.rectangle((x, y, x+w-1, y+h-1), outline=1 if c else 0)

    def fill_rect(self, x, y, w, h, c=1):
        self._draw.rectangle((x, y, x+w-1, y+h-1), fill=1 if c else 0)

    def text(self, s, x, y, c=1):
        self._draw.text((x, y), s, font=self._font, fill=1 if c else 0)

    def show(self):
        self.device.display(self._img)

    def clear(self):
        self.fill(0)

    # RoboEyes will call this per frame
    def on_show(self, _):
        self.show()

    # Filled rounded-rectangle
    def fill_rrect(self, x, y, w, h, r, c=1):
        color = 1 if c else 0
        r = int(max(0, min(r, w // 2, h // 2)))
        try:
            self._draw.rounded_rectangle((x, y, x + w - 1, y + h - 1), radius=r, fill=color)
        except AttributeError:
            # Fallback if Pillow is older
            rr = Image.new("1", (w, h), 0)
            d = ImageDraw.Draw(rr)
            d.rectangle((r, 0, w - 1 - r, h - 1), fill=1)
            d.rectangle((0, r, w - 1, h - 1 - r), fill=1)
            d.pieslice((0, 0, 2*r-1, 2*r-1), 180, 270, fill=1)
            d.pieslice((w-2*r, 0, w-1, 2*r-1), 270, 360, fill=1)
            d.pieslice((0, h-2*r, 2*r-1, h-1), 90, 180, fill=1)
            d.pieslice((w-2*r, h-2*r, w-1, h-1), 0, 90, fill=1)
            self._img.paste(color, (x, y), rr)

    def fill_triangle(self, x0, y0, x1, y1, x2, y2, c=1):
        self._draw.polygon([(x0, y0), (x1, y1), (x2, y2)], outline=1 if c else 0, fill=1 if c else 0)

    def fill_circle(self, cx, cy, r, c=1):
        color = 1 if c else 0
        self._draw.ellipse((cx-r, cy-r, cx+r, cy+r), outline=color, fill=color)
