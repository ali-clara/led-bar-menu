# Script for interfacing with the neopixels
import time
import yaml
import os
import numpy as np
try: # real hardware
    import board
    import neopixel
except ImportError: # simulated hardware
    try: # run from this script
        import simulated_neopixel as neopixel
        from simulated_neopixel import board
    except: # run from the main script
        import services.simulated_neopixel as neopixel
        from services.simulated_neopixel import board

dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)

class LED:
    def __init__(self, spirit_locations):
        # Initialize the NeoPixel strip with GPIO pin 10 (needed for not running this with SUDO privileges),
        # 150 lights, and 20% brightness. Auto_write means we're going to need to call pixels.show() whenever we want them lit up
        self.pixels = neopixel.NeoPixel(board.D10, 255, brightness=0.2, auto_write=False)
        # Make sure our strip is off
        self.pixels.fill((0,0,0))
        self.pixels.show()

        # Dictionary of spirit:location, where 'location' is a coordinate not a neopixel address (e.g A7 not 150)
        self.spirit_loc_dict = spirit_locations

        # Dictionary of coordinate:[neopixel start, neopixel stop]
        with open(dir_path+"/config/led_locs_final.yml") as stream:
            self.led_loc_dict = yaml.safe_load(stream)

        # Initialize colors
        self.rainbow_dict = {"red": (228, 3, 3),
                            "orange": (255, 69, 0),
                            "yellow": (255, 237, 0),
                            "green": (0, 255, 10),
                            "blue": (0, 77, 255),
                            "violet": (117, 7, 135),
                            "white": (255, 255, 255),
                            "pink": (255, 105, 180),
                            "light blue": (0, 191, 255),
                            "brown": (139, 69, 19),
                            }
        
        self.unused_colors = list(self.rainbow_dict.values())

    def _spirit_to_pixel(self, spirit_list):
        
        pixels = []
        for spirit in spirit_list:
            print(spirit)
            spirit = spirit.replace("_", " ").title()
            try:
                color = self.unused_colors.pop(0)
            # When we run out of rainbow, pop() will return an IndexError. Reset the rainbow and continue
            except IndexError:
                self.unused_colors = list(self.rainbow_dict.values())
                color = self.unused_colors.pop(0)
                
            try:
                cabinet_location = self.spirit_loc_dict[spirit]
                neopixel_range = self.led_loc_dict[cabinet_location.strip()]
            # If it's not in the cabinet, light up the area near the pi
            except KeyError as e:
                print(f"key error in accessing cabinet locations: {e}")
                cabinet_location = "G18"
                neopixel_range = self.led_loc_dict[cabinet_location.strip()]
            
            try:
                # neopixel_range = neopixel_range.flatten()
                brightness = self._get_brightness_scalar(cabinet_location)
                print(cabinet_location.strip())
                print(brightness)
            except Exception as e:
                print(f"Not sure what happened here: {e}")
            else:
                print(neopixel_range)
                [pixels.append(neo) for neo in neopixel_range]
                for start, stop in neopixel_range:
                    self.range_on(start, stop, color, brightness)


        # pixels = []

        # if type(spirit) == str:
        #     pass
        # elif type(spirit) == list:
        #     for s in spirit:
        #         if s in self.test_locs:
        #             pixel_loc = self.test_locs[s] # int
        #             pixels.append(pixel_loc)
        #             pixels.append(pixel_loc-1)
        #             pixels.append(pixel_loc+1)

        # return pixels as a list
        return pixels
    
    def _get_brightness_scalar(self, location:str):
        # Returns a scalar between 0-1 based on the cabinet location
        if "A" in location:
            return 1
        elif "B" in location or "C" in location or "D" in location or "E" in location or "F" in location:
            return 0.5
        elif "G" in location:
            return 0.3
        elif "H" in location or "I" in location or "J" in location or "K" in location or "L" in location or "M" in location or "N" in location:
            return 0.2
        else:
            return 0
    
    def illuminate(self, spirit):
        pixels = self._spirit_to_pixel(spirit)
        print(f"lighting up pixels {pixels}")
        # self.pixels_on(pixels)

    def all_on(self, color=(255, 255, 0)):
        self.pixels.fill(color)
        self.pixels.show()

    def all_off(self):
        self.pixels.fill((0,0,0))
        self.pixels.show()

    def pixels_on(self, pixels, color=(255,255,0)):
        for pixel in pixels:
            self.pixels[pixel] = color
        self.pixels.show()
    
    def range_on(self, start_pix: int, stop_pix: int, color=(255,255,0), brightness=0.1):
        scaled_color = brightness*np.array(color)
        int_scaled_color = scaled_color.astype(int)
        for i in range(start_pix, stop_pix+1):
            try:
                self.pixels[i] = int_scaled_color
            except IndexError:
                pass
        self.pixels.show()

    def range_off(self, start_pix: int, stop_pix: int):
        for i in range(start_pix, stop_pix):
            self.pixels[i] = (0,0,0)
        self.pixels.show()

    def _wheel(self, pos):
        # From Adafruit
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            r = g = b = 0
        elif pos < 85:
            r = int(pos * 3)
            g = int(255 - pos * 3)
            b = 0
        elif pos < 170:
            pos -= 85
            r = int(255 - pos * 3)
            g = 0
            b = int(pos * 3)
        else:
            pos -= 170
            r = 0
            g = int(pos * 3)
            b = int(255 - pos * 3)
        return (r, g, b)
    
    def rainbow_cycle(self, num_pixels, wait):
        for j in range(255):
            for i in range(num_pixels):
                pixel_index = (i * 256 // num_pixels) + j
                self.pixels[i] = self._wheel(pixel_index & 255)
                self.pixels.show()
                time.sleep(wait)
