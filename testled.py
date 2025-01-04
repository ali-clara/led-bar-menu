# 12/28/24 - this works without a level shifter! Turns out the neopixels are directional, and I was plugging into the wrong side. The
# arrows on the strip mean something, fancy that.

# Need some m-m jumper wires and we're otherwise ready to go. They're BRIGHT even at 20% power
# Need 5V power

import board
import neopixel
import yaml

location_dict = {"pixel ranges": [], "cabinet locations": []}

pixels = neopixel.NeoPixel(board.D10, 150, brightness=0.2, auto_write=False)
pixels.fill((0,0,0))
pixels.show()

exit_loop = False

print("LED strip configuration")
while not exit_loop:
    print("---")
    entry = input("(a) Strip on (b) Individual LED setup (c) Strip off (q) Quit \n")
    if entry == "a" or entry == "A":
        pixels.fill((0, 255, 0))
        pixels.show()
    elif entry == "b" or entry == "B":
        print("Neopixel configuration mode. Entering integers (0-150) will turn on those leds \n")
        try:
            start_pix = int(input("Start pixel: "))
            stop_pix = int(input("Stop pixel: "))
        except TypeError:
            print("Could not convert input to integer")
        # If we've been given a valid start and stop, turn on those pixels
        else:
            for i in range(start_pix, stop_pix):
                pixels[i] = (0, 255, 0)
            pixels.show()
        
        pix_loc = input("Enter a cabinet location corresponding to this pixel range (Return for no entry): ")
        if pix_loc != "":
            location_dict["pixel ranges"].append((start_pix, stop_pix))
            location_dict["cabinet locations"].append((pix_loc))

    elif entry == "c" or entry == "C":
        pixels.fill((0, 0, 0))
        pixels.show()
    elif entry == "q" or entry == "Q":
        exit_loop = True

try:
    pixels.deinit()
except AttributeError:
    pass

print(location_dict)

# A note that the lights don't turn off at the end of the script. Will need an off button




