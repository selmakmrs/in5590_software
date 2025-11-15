from oled.ssd_shim import LumaSSD1306Shim
from oled.roboeyes import *

class OLED:
    """
    Controls OLED display for robot eyes/expressions
    Typically 128x64 or 128x32 OLED via I2C
    """
    
    def __init__(self, width=128, height=128):
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
        self.current_seq = None


    # === Setup ====
    def setup(self):
        # Eye Configuartion
        self.roboeyes.default()
    
        # Setup Eye sequences
        self._create_sequences()
    
    # === Display Control ===
    def clear(self):
        """Clear display"""
        self.lcd.clear()
    
    def update(self):
        """Update display with current buffer"""
        self.roboeyes.update()

    def run_emotion(self, emotion):
        """Start the emotion sequence"""
        seq = self.roboeyes.sequences.get(emotion)
        self.current_seq = seq
        if seq:
            seq.reset()
            seq.start()

    def is_sequence_running(self):
        if self.current_seq is not None:
            return self.roboeyes.sequences.get(self.current_seq).done
        return False

    # === Create Sequences 
    def _create_sequences(self):

        # Happy Sequence
        seq = self.roboeyes.sequences.add("happy")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_mood(HAPPY) )
        seq.step( 800,  lambda r: r.laugh() )
        seq.step( 1600, lambda r: r.laugh() )
        seq.step( 5400, lambda r: r.laugh() )
        seq.step( 10000, lambda r: r.set_mood(DEFAULT) )
        seq.step( 10100, lambda r: print(seq.name, "done!") )


        # Angry Sequence
        seq = self.roboeyes.sequences.add("angry")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_mood(ANGRY) )
        seq.step( 1500, lambda r: r.blink() )
        seq.step( 2000, lambda r: r.blink() )
        seq.step( 3000, lambda r: r.confuse() )
        seq.step( 5000, lambda r: r.blink() )
        seq.step( 10000, lambda r: r.set_mood(DEFAULT) )
        seq.step( 10600, lambda r: print(seq.name, "done!") )

        # Sad Sequence
        seq = self.roboeyes.sequences.add("sad")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_mood(TIRED) )
        seq.step( 5000, lambda r: r.blink() )
        seq.step( 10000, lambda r: r.set_mood(DEFAULT) )
        seq.step( 10600, lambda r: print(seq.name, "done!") )


        # Confused Sequence
        seq = self.roboeyes.sequences.add("confused")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500, lambda r : r.set_auto_blinker(OFF))
        seq.step( 600, lambda r : r.set_idle_mode(OFF))
        seq.step( 2000,  lambda r: r.set_mood(CURIOUS) )
        seq.step( 6000, lambda r : r.default())
        seq.step( 7000,  lambda r: r.confuse() )
        seq.step( 10000, lambda r: r.set_mood(DEFAULT) )
        seq.step( 10100, lambda r: print(seq.name, "done!") )


        # Scared Sequence
        seq = self.roboeyes.sequences.add("scared")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500, lambda r : r.set_auto_blinker(OFF))
        seq.step( 600, lambda r : r.set_idle_mode(OFF))
        seq.step( 2000, lambda r : r.set_mood(FROZEN))
        seq.step( 4000, lambda r : r.eyes_width(10,10))
        seq.step( 4020, lambda r : r.eyes_height(10,10))
        
        seq.step( 7000, lambda r : r.set_mood(DEFAULT))
        seq.step( 8000, lambda r: r.blink() )
        seq.step( 8800, lambda r: r.blink() )        
        seq.step( 10000, lambda r : r.default()) 
        seq.step( 10500, lambda r: r.set_mood(DEFAULT) )
        seq.step( 10600, lambda r: print(seq.name, "done!") )


        # Suprised Sequence
        seq = self.roboeyes.sequences.add("surprise")
        seq.step( 0,    lambda r: r.open() )
        seq.step( 500,  lambda r: r.set_cyclops(True) )   # focus one eye
        seq.step( 800,  lambda r: r.vert_flicker(True, 3) )
        seq.step( 1500, lambda r: r.vert_flicker(False) )
        seq.step( 2000, lambda r: r.set_cyclops(False) )
        seq.step( 2100, lambda r: print(seq.name, "done!") )





# Testing
if __name__=="__main__":
    import random
    oled = OLED()

    emotions = ["happy", "sad", "angry", "surprise", "scared", "scared"]

    try:
        while True:
            oled.update()

            if not oled.is_sequence_running():
                emotion = random.choice(emotions)
                oled.run_emotion(emotion)
                time.sleep(0.5)
    except KeyboardInterrupt:
        print("Shutting down ...")
        



    