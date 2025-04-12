# 12/28/24 - this works without a level shifter! Turns out the neopixels are directional, and I was plugging into the wrong side. The
# arrows on the strip mean something, fancy that.

# The strip needs 5V power. They're BRIGHT even at 20%
# A note that the strip doesn't turn off at the end of the script. Our interface will need an off button or a timer. Or both

import board
import neopixel
import yaml

location_dict = {"pixel ranges": [], "cabinet locations": []}

# Initialize the NeoPixel strip with GPIO pin 10 (needed for not running this with SUDO privileges),
# 150 lights, and 20% brightness. Auto_write means we're going to need to call pixels.show() whenever we want them lit up
pixels = neopixel.NeoPixel(board.D10, 150, brightness=0.2, auto_write=False)
# Make sure our strip is off
pixels.fill((0,0,0))
pixels.show()

# Enter a loop to let us test functionality and set some configuration params
exit_loop = False
print("LED strip configuration")
while not exit_loop:
    print("---")
    entry = input("(a) Strip on (b) Individual LED setup (c) Strip off (q) Quit \n")
    if entry == "a" or entry == "A":
        pixels.fill((255, 255, 0))
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
            for i in range(start_pix, stop_pix+1):
                try:
                    pixels[i] = (0, 255, 0)
                except IndexError as e:
                    print(e)
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

# Calling deinit() turns off the strip and releases the GPIO pin. Putting it in a try-except block here because I was getting
# errors when I exited too soon / tried to deinit() without turning the strip on
try:
    pixels.deinit()
except AttributeError:
    pass

# Eventually should save this to a yaml, but for now just print it
print(location_dict)






