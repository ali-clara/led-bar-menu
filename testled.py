# 12/28/24 - this works without a level shifter! Turns out the neopixels are directional, and I was plugging into the wrong side. The
# arrows on the strip mean something, fancy that.

# Need some m-m jumper wires and we're otherwise ready to go. They're BRIGHT even at 20% power
# Need 5V power

import board
import neopixel
import time

pixels = neopixel.NeoPixel(board.D18, 150, brightness=0.2, auto_write=False)
exit_loop = False

print("LED strip configuration")
while not exit_loop:
    entry = input("(a) Strip on (b) Individual LED setup (c) Strip off (q) Quit")
    if entry == "a" or entry == "A":
        pixels.fill((0, 255, 0))
        pixels.show()
    elif entry == "b" or entry == "B":
        print("Neopixel configuration mode. Entering integers (0-150) will turn on those leds \n")
        try:
            start_pix = int(input("Start pixel: "))
            end_pix = int(input("End pixel: "))
        except TypeError:
            print("Could not convert input to integer")
        else:
            pixels[start_pix:end_pix] = (0, 255, 0)
            pixels.show()
    elif entry == "c" or entry == "C":
        pixels.fill((0, 0, 0))
        pixels.show()
    elif entry == "q" or entry == "Q":
        exit_loop == True


# A note that the lights don't turn off at the end of the script. Will need an off button




