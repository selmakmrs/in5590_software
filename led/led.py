import board
import neopixel
import time
import random


class LED:
    def __init__(
        self,
        pixel_pin=board.D18,
        num_pixels=22,
        brightness=0.9,
        pixel_order=neopixel.GRB,
    ):
        # Hardware config
        self.pixel_pin = pixel_pin
        self.num_pixels = num_pixels
        self.pixel_order = pixel_order
        self.brightness = brightness

        # NeoPixel object (created in start())
        self.pixels = None

        # Basic color codes (RGB)
        self.color_codes = {
            "off": (0, 0, 0),

            # Emotions
            "idle": (255, 180, 80),      # warm white / soft amber
            "happy": (255, 255, 0),      # yellow
            "sad": (0, 0, 255),          # blue
            "angry": (255, 0, 0),        # red
            "suprise": (255, 255, 255), # bright white
            "fear": (128, 0, 128),       # purple

            # Generic colors if you want to use them
            "red": (255, 0, 0),
            "blue": (0, 0, 255),
            "green": (0, 255, 0),
            "white": (255, 255, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
        }

    def start(self):
        """Initialize the LED strip."""
        if self.pixels is None:
            self.pixels = neopixel.NeoPixel(
                self.pixel_pin,
                self.num_pixels,
                brightness=self.brightness,
                auto_write=False,
                pixel_order=self.pixel_order,
            )
        # Turn everything off on start
        self.change_color("off")

    def close(self):
        """Turn LEDs off and release the strip."""
        if self.pixels is not None:
            self.change_color("off")
            try:
                # On some platforms NeoPixel has deinit()
                self.pixels.deinit()
            except AttributeError:
                pass
            self.pixels = None

    def default(self):
        """Default / idle state for the robot."""
        # Simple: static idle color
        self.change_color("idle")

        # If you later want a breathing effect for idle, you can call:
        # self.breathing("idle", cycles=1, period=3.0)

    def _resolve_color(self, color):
        """Accept either a color name or an (R,G,B) tuple."""
        if isinstance(color, str):
            key = color.lower()
            if key not in self.color_codes:
                raise ValueError(f"Unknown color name: {color}")
            return self.color_codes[key]
        elif isinstance(color, (tuple, list)) and len(color) == 3:
            return tuple(color)
        else:
            raise TypeError("Color must be a name (str) or (R,G,B) tuple")

    def change_color(self, color):
        """Set all pixels to the given color and show it."""
        if self.pixels is None:
            raise RuntimeError("LED strip not started. Call start() first.")

        rgb = self._resolve_color(color)
        self.pixels.fill(rgb)
        self.pixels.show()

    def blinking_sequence(
        self,
        sequence=("red", "off"),
        time_on=0.3,
        time_off=0.3,
        loops=3,
    ):
        """
        Blink through a sequence of colors.

        sequence: iterable of color names or (R,G,B) tuples
        time_on: seconds for non-'off' colors
        time_off: seconds for 'off'
        loops: how many times to repeat the full sequence
        """
        if self.pixels is None:
            raise RuntimeError("LED strip not started. Call start() first.")

        for _ in range(loops):
            for color in sequence:
                if isinstance(color, str) and color.lower() == "off":
                    self.change_color("off")
                    time.sleep(time_off)
                else:
                    self.change_color(color)
                    time.sleep(time_on)

    def breathing(
        self,
        color="idle",
        cycles=1,
        period=2.0,
        min_brightness=0.1,
        max_brightness=1.0,
        step=0.05,
    ):
        """
        Simple breathing effect by changing global brightness.
        period: time (seconds) for one full breath (in + out)
        """
        if self.pixels is None:
            raise RuntimeError("LED strip not started. Call start() first.")

        base_color = self._resolve_color(color)
        self.pixels.fill(base_color)

        original_brightness = self.pixels.brightness
        self.pixels.show()

        # Time per step (half-cycle)
        steps = int((max_brightness - min_brightness) / step)
        if steps <= 0:
            steps = 1
        step_time = (period / 2.0) / steps

        for _ in range(cycles):
            # Fade in
            b = min_brightness
            while b <= max_brightness:
                self.pixels.brightness = b
                self.pixels.show()
                time.sleep(step_time)
                b += step

            # Fade out
            b = max_brightness
            while b >= min_brightness:
                self.pixels.brightness = b
                self.pixels.show()
                time.sleep(step_time)
                b -= step

        # Restore original brightness
        self.pixels.brightness = original_brightness
        self.pixels.show()

    # --- High-level emotion helper ---

    def show_emotion(self, emotion):
        """
        High-level helper: call this from your robot state machine.
        Each emotion uses a slightly different pattern.
        """
        emotion = emotion.lower()

        if emotion == "idle":
            # Slow breathing warm white
            # self.breathing("idle", cycles=1, period=3.0)
            self.change_color("idle")

        elif emotion == "happy":
            # Bright yellow + a few quick soft blinks
            # self.blinking_sequence(
            #     sequence=("happy", "off"),
            #     time_on=0.2,
            #     time_off=0.1,
            #     loops=3,
            # )
            self.change_color("happy")

        elif emotion == "sad":
            # Static blue or very slow breathing
            # self.breathing("sad", cycles=1, period=4.0)
            self.change_color("sad")
            

        elif emotion == "angry":
            # Strong red, fast repeating flashes
            self.change_color("red")
            time.sleep(3)
            self.blinking_sequence(
                sequence=("angry", "off"),
                time_on=0.5,
                time_off=0.5,
                loops=6,
            )
            self.change_color("angry")

        elif emotion == "suprise":
            # One strong white flash, then idle color
            print(self.color_codes.keys()[0])
            color = random.choice(self.color_codes.keys())
            self.change_color(color)
            # self.blinking_sequence(
            #     sequence=("suprise", "off"),
            #     time_on=0.15,
            #     time_off=0.15,
            #     loops=1,
            # )
            # self.change_color("idle")

        elif emotion == "fear":
            # Purple, a bit flickery
            self.change_color("fear")
            # for _ in range(10):
            #     self.change_color("fear")
            #     time.sleep(0.05)
            #     self.change_color("off")
            #     time.sleep(0.03)
            # self.change_color("fear")

        else:
            # Unknown emotion → fallback to idle
            self.default()
