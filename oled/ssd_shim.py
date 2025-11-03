# ---- SSD1306-like display backed by luma.emulator ----
from luma.emulator.device import pygame as EmulatorDevice
from PIL import Image, ImageDraw, ImageFont

class LumaSSD1306Shim:
    def __init__(self, width=128, height=64, rotate=0):
        self.width, self.height = width, height
        self.device = EmulatorDevice(width=width, height=height, rotate=rotate)
        self._img = Image.new("1", (width, height), 0)
        self._draw = ImageDraw.Draw(self._img)
        self._font = ImageFont.load_default()

    # MicroPython-ish API used by RoboEyes
    def fill(self, c): self._draw.rectangle((0,0,self.width,self.height), fill=1 if c else 0)
    def pixel(self, x,y,c=1): 
        if 0<=x<self.width and 0<=y<self.height: self._draw.point((x,y), fill=1 if c else 0)
    def hline(self, x,y,w,c=1): self._draw.line((x,y,x+w-1,y), fill=1 if c else 0)
    def vline(self, x,y,h,c=1): self._draw.line((x,y,x,y+h-1), fill=1 if c else 0)
    def line(self, x1,y1,x2,y2,c=1): self._draw.line((x1,y1,x2,y2), fill=1 if c else 0)
    def rect(self, x,y,w,h,c=1): self._draw.rectangle((x,y,x+w-1,y+h-1), outline=1 if c else 0)
    def fill_rect(self, x,y,w,h,c=1): self._draw.rectangle((x,y,x+w-1,y+h-1), fill=1 if c else 0)
    def text(self, s,x,y,c=1): self._draw.text((x,y), s, font=self._font, fill=1 if c else 0)
    def show(self): self.device.display(self._img)
    def clear(self): self.fill(0)
    def on_show(self, _ ): self.show()
    def fill_rrect(self, x, y, w, h, r, c=1):
        """Filled rounded-rectangle: (x,y,w,h,r,color)."""
        color = 1 if c else 0
        r = int(max(0, r))
        # Clamp radius so it fits the box
        r = min(r, w // 2, h // 2)

        if r == 0:
            # fall back to normal filled rect
            self._draw.rectangle((x, y, x + w - 1, y + h - 1), fill=color)
            return

        # Prefer PIL's rounded_rectangle if available
        try:
            self._draw.rounded_rectangle(
                (x, y, x + w - 1, y + h - 1), radius=r, fill=color
            )
            return
        except AttributeError:
            pass  # older Pillow: manual composite below

        # --- Fallback: manual mask for rounded rect fill ---
        from PIL import ImageDraw
        rr = Image.new("1", (w, h), 0)
        d = ImageDraw.Draw(rr)

        # central rectangles
        d.rectangle((r, 0, w - 1 - r, h - 1), fill=1)
        d.rectangle((0, r, w - 1, h - 1 - r), fill=1)
        # corner quarters
        d.pieslice((0, 0, 2 * r - 1, 2 * r - 1), 180, 270, fill=1)                 # TL
        d.pieslice((w - 2 * r, 0, w - 1, 2 * r - 1), 270, 360, fill=1)             # TR
        d.pieslice((0, h - 2 * r, 2 * r - 1, h - 1), 90, 180, fill=1)              # BL
        d.pieslice((w - 2 * r, h - 2 * r, w - 1, h - 1), 0, 90, fill=1)            # BR

        # paste the mask onto the display image
        self._img.paste(1 if color else 0, (x, y), rr)

    def fill_triangle(self, x0, y0, x1, y1, x2, y2, c=1):
        """
        Filled triangle with vertices (x0,y0), (x1,y1), (x2,y2).
        Matches MicroPython-style signature: last arg is color.
        """
        color = 1 if c else 0
        self._draw.polygon([(x0, y0), (x1, y1), (x2, y2)], outline=color, fill=color)

    def fill_circle(self, cx, cy, r, c=1):
        """Filled circle using PIL ellipse."""
        color = 1 if c else 0
        x0, y0, x1, y1 = cx - r, cy - r, cx + r, cy + r
        self._draw.ellipse((x0, y0, x1, y1), outline=color, fill=color)
