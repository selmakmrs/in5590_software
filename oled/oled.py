from oled.ssd_shim import LumaSSD1306Shim
from oled.roboeyes import *

class OLED:
    """
    Controls OLED display for robot eyes/expressions
    Typically 128x64 or 128x32 OLED via I2C
    """
    
    def __init__(self, width=128, height=64, i2c_address=0x3C):
        """
        Initialize OLED display
        
        Args:
            width: Display width in pixels
            height: Display height in pixels
            i2c_address: I2C address of OLED
        """
        self.lcd = LumaSSD1306Shim(width=width, height=height)
        self.roboeyes = RoboEyes(self.lcd, width, height, on_show=self.lcd.on_show)

        self.setup()


    # === Setup ====
    def setup(self):
        # Eye Configuartion
        self.roboeyes.set_auto_blinker(ON,3,2)
        self.roboeyes.set_idle_mode(ON,2,2)
        
        self.roboeyes.eyes_width(40,40)
        self.roboeyes.eyes_height(30,30)
        self.roboeyes.eyes_radius(6,6)
        self.roboeyes.eyes_spacing(30)


        # Setup Eye sequences
        self._create_sequences()
    
    # === Display Control ===
    def clear(self):
        """Clear display"""
        pass
    
    def update(self):
        """Update display with current buffer"""
        self.roboeyes.update()

    def run_emotion(self, emotion):
        """Start the emotion sequence"""
        seq = self.roboeyes.sequences.get(emotion)
        if seq:
            seq.reset()
            seq.start()


    # === Create Sequences 
    def _create_sequences(self):

        # Happy Sequence
        seq = self.roboeyes.sequences.add("happy")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_mood(HAPPY) )
        seq.step( 800,  lambda r: r.laugh() )
        seq.step( 1600, lambda r: r.laugh() )
        seq.step( 2400, lambda r: r.laugh() )
        seq.step( 3000, lambda r: r.set_mood(DEFAULT) )
        seq.step( 3100, lambda r: print(seq.name, "done!") )


        # Sad Sequence
        seq = self.roboeyes.sequences.add("happy")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_mood(HAPPY) )
        seq.step( 800,  lambda r: r.laugh() )
        seq.step( 1600, lambda r: r.laugh() )
        seq.step( 2400, lambda r: r.laugh() )
        seq.step( 3000, lambda r: r.set_mood(DEFAULT) )
        seq.step( 3100, lambda r: print(seq.name, "done!") )


        # Angry Sequence
        seq = self.roboeyes.sequences.add("angry")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_mood(ANGRY) )
        seq.step( 1500, lambda r: r.blink() )
        seq.step( 2000, lambda r: r.blink() )
        seq.step( 2500, lambda r: r.set_mood(DEFAULT) )
        seq.step( 2600, lambda r: print(seq.name, "done!") )



        # Confused Sequence
        seq = self.roboeyes.sequences.add("confused")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_mood(CURIOUS) )
        seq.step( 700,  lambda r: r.confuse() )
        seq.step( 2000, lambda r: r.confuse() )
        seq.step( 3000, lambda r: r.set_mood(DEFAULT) )
        seq.step( 3100, lambda r: print(seq.name, "done!") )



        # Scared Sequence
        seq = self.roboeyes.sequences.add("scared")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 400,  lambda r: r.set_mood(SCARY) )
        seq.step( 1000, lambda r: r.blink() )
        seq.step( 1800, lambda r: r.blink() )
        seq.step( 2500, lambda r: r.set_mood(DEFAULT) )
        seq.step( 2600, lambda r: print(seq.name, "done!") )


        # Suprised Sequence
        seq = self.roboeyes.sequences.add("surprised")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_cyclops(True) )   # focus one eye
        seq.step( 800,  lambda r: r.vert_flicker(True, 3) )
        seq.step( 1500, lambda r: r.vert_flicker(False) )
        seq.step( 2000, lambda r: r.set_cyclops(False) )
        seq.step( 2100, lambda r: print(seq.name, "done!") )




    