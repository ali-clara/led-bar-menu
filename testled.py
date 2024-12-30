# 12/28/24 - this works without a level shifter! Turns out the neopixels are directional, and I was plugging into the wrong side. The
# arrows on the strip mean something, fancy that.

# Need some m-m jumper wires and we're otherwise ready to go. They're BRIGHT even at 20% power
# Should also play around with how much voltage we need, this was ~8

import board
import neopixel
import time

pixels = neopixel.NeoPixel(board.D18, 150, brightness=0.2, auto_write=False)

pixels.fill((0, 255, 0))
pixels.show()
time.sleep(5)

# A note that the lights don't turn off at the end of the script. Will need an off button


