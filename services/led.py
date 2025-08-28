# Script for interfacing with the neopixels
import time
import yaml
import os
import numpy as np
import concurrent.futures

try: # real hardware
    import board
    import neopixel
    import recipe_parsing_helpers as recipe
except ImportError: # simulated hardware
    try: # run from this script
        import simulated_neopixel as neopixel
        from simulated_neopixel import board
        import recipe_parsing_helpers as recipe
    except: # run from the main script
        import services.simulated_neopixel as neopixel
        from services.simulated_neopixel import board
        from services import recipe_parsing_helpers as recipe
    
dir_path = os.path.join(os.path.dirname( __file__ ), os.pardir)

class LED:
    def __init__(self):
        # Initialize the NeoPixel strip with GPIO pin 10 (needed for not running this with SUDO privileges),
        # 150 lights, and 20% brightness. Auto_write means we're going to need to call pixels.show() whenever we want them lit up
        self.pixels = neopixel.NeoPixel(board.D10, 255, brightness=0.2, auto_write=False)
        # Make sure our strip is off
        self.pixels.fill((0,0,0))
        self.pixels.show()

        # Dictionary of spirit:location, where 'location' is a coordinate not a neopixel address (e.g A7 not 150)
        all_ingredients, self.spirit_loc_dict = recipe.load_all_ingredients()
        # Pull a list of all used locations from the values of that dictionary
        used_locations = set(self.spirit_loc_dict.values())

        # Dictionary of coordinate:[neopixel start, neopixel stop]
        with open(dir_path+"/config/led_locs_final.yml") as stream:
            self.led_loc_dict = yaml.safe_load(stream)
        # Pull the list of all locations from the keys of that dictionary
        self.all_cabinet_locations = list(self.led_loc_dict.keys())
        self.all_cabinet_locations.sort()

        # Find the difference between "used locations" and "cabinet locations" to get "non cabinet locations"
        # E.g "fridge" "bowl" "cart" etc
        self.non_cabinet_locations = used_locations.difference(self.all_cabinet_locations)

        # Initialize colors
        self.rainbow_dict = {"yellow": (255, 237, 0),
                            "red": (228, 3, 3),
                            "orange": (255, 69, 0),
                            "green": (0, 255, 10),
                            "blue": (0, 77, 255),
                            "violet": (117, 7, 135),
                            "white": (255, 255, 255),
                            "pink": (255, 105, 180),
                            "light blue": (0, 191, 255),
                            "brown": (139, 69, 19),
                            }
        
        self.unused_colors = list(self.rainbow_dict.values())

        self.flashing = False

    def forbid_flashing(self):
        self.flashing = False

    def allow_flashing(self):
        self.flashing = True
    
    def update_loc_dict(self, new_dict):
        self.spirit_loc_dict = new_dict
        # should just turn this into "reload everything pls" now that this file reads config independently
        
    def get_rainbow_color(self):
        # When we run out of colors, reset the rainbow and continue
        if len(self.unused_colors) == 0:
            self.unused_colors = list(self.rainbow_dict.values())
        
        return self.unused_colors.pop(0)
    
    def get_cabinet_location(self, spirit):
        # Read in the location of the given spirit. 
        # This is in a try-except block because god knows I can't predict everything we might accidentally do to the yamls
        try:
            cabinet_location = self.spirit_loc_dict[spirit].strip()
        # If it's not in the cabinet, let us know and light up the area near the pi
        except KeyError as e:
            print(f"Key error in accessing cabinet locations: {e}")
            cabinet_location = None
        else:
            # If we've found something that's not in the cabinet, light up the area by the Pi
            if cabinet_location in self.non_cabinet_locations:
                cabinet_location = "G18"

        return cabinet_location
    
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
            print("Not a standard led location")
            return 0.4

    def illuminate_spirit(self, spirit_input, flash=False, verbose=False):
        if type(spirit_input) == list:
            for spirit in spirit_input:
                print("---")
                print(spirit)
                # Read our external config files to determine the location and pixel range of the spirit
                cabinet_location = self.get_cabinet_location(spirit)
                # Get the pixel range that corresponds to the cabinet location.
                self.illuminate_location(cabinet_location, flash, verbose)
        elif type(spirit_input) == str:
            print("---")
            print(spirit_input)
            cabinet_location = self.get_cabinet_location(spirit_input)
            self.illuminate_location(cabinet_location, flash, verbose)
        else:
            print("Tried to illuminate something that wasn't a spirit name or a list of spirit names. Hmm.")

    def illuminate_location(self, location:str, flash=False, verbose=False):        
        # Check if our location is valid. If it's not, flag and return
        if location not in self.all_cabinet_locations:
            print(f"'{location}' is not a valid cabinet location. Should be a string of the form 'A7', etc.")
            return
        # If we're good, get the neopixel range that corresponds to the cabinet location
        neopixel_range = self.led_loc_dict[location]
        
        # Then get color and brightness
        # TODO - more than just random colors. Website-chosen, themed, etc
        color = self.get_rainbow_color()
        brightness = self._get_brightness_scalar(location)

        if verbose:
            print(f"location: {location.strip()}")
            print(f"brightness: {brightness}")
            print(f"pixels: {neopixel_range}")

        # Light em up
        if flash:
            self.allow_flashing()
            self.range_flash(neopixel_range, color, brightness)
        else:
            for start, stop in neopixel_range:
                self.set_pixels_from_range(start, stop, color, brightness)
                if verbose:
                    print(f"lit up {start} through {stop}")
            self.pixels.show()


    def all_on(self, color=(255, 255, 0)):
        self.pixels.fill(color)
        self.pixels.show()

    def all_off(self):
        self.forbid_flashing()
        self.pixels.fill((0,0,0))
        self.pixels.show()
    
    def set_pixels_from_range(self, start_pix: int, stop_pix: int, color=(255,255,0), brightness=0.1):
        # Replaces range_on (or should)
        # Doesn't turn anything on, just updates the self.pixels variable with the right color
        # Must call self.pixels.show() afterward
        scaled_color = brightness*np.array(color)
        int_scaled_color = scaled_color.astype(int)
        for i in range(start_pix, stop_pix+1):
            try:
                self.pixels[i] = int_scaled_color
            except IndexError:
                pass
    
    def range_on(self, start_pix: int, stop_pix: int, color=(255,255,0), brightness=0.1):
        # print(f"lighting up pixels {start_pix, stop_pix}")
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
    
    def _flash_threaded(self, neopixel_range, color, brightness):
        starttime = time.time()

        while self.flashing:
            # Safety measure so my thread doesn't run forever
            if (time.time() - starttime) >= 60:
                break
            
            for start, stop in neopixel_range:
                self.set_pixels_from_range(start, stop, color, brightness)
            self.pixels.show()
            print("on")
            time.sleep(0.5)
            
            for start, stop in neopixel_range:
                self.set_pixels_from_range(start, stop, color=(0,0,0), brightness=0)
            self.pixels.show()
            print("off")
            time.sleep(0.5)
    
    def range_flash(self, neopixel_range, color=(255,255,0), brightness=0.1):
        with concurrent.futures.ThreadPoolExecutor() as executor:
            flash = executor.submit(self._flash_threaded, neopixel_range, color, brightness)

        # flash.result()

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


if __name__ == "__main__":


    myled = LED()

    myled.illuminate_location("L2", verbose=True, flash=True)
    # myled.illuminate_location(None)

    # Test: B22, fridge, K4, A2
    # myled.illuminate_spirit(["galliano", "prosecco", "rosso_amaro", "genepy"], verbose=True)
