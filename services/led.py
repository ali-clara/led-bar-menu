# Script for interfacing with the neopixels
import time
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

class LED:
    def __init__(self):
        # Initialize the NeoPixel strip with GPIO pin 10 (needed for not running this with SUDO privileges),
        # 150 lights, and 20% brightness. Auto_write means we're going to need to call pixels.show() whenever we want them lit up
        self.pixels = neopixel.NeoPixel(board.D10, 150, brightness=0.2, auto_write=False)
        # Make sure our strip is off
        self.pixels.fill((0,0,0))
        self.pixels.show()

        # Seems like 3-wide is pretty good
        self.test_locs = {"Famous Grouse Smoky Black": 38, "Genepy": 66, "Woodlands Brucato": 109}


    def _spirit_to_pixel(self, spirit):
        pixels = []

        if type(spirit) == str:
            pass
        elif type(spirit) == list:
            for s in spirit:
                if s in self.test_locs:
                    pixel_loc = self.test_locs[s] # int
                    pixels.append(pixel_loc)
                    pixels.append(pixel_loc-1)
                    pixels.append(pixel_loc+1)

        # return pixels as a list
        return pixels
    
    def illuminate(self, spirit):
        pixels = self._spirit_to_pixel(spirit)
        print(f"lighting up pixels {pixels}")
        self.pixels_on(pixels)

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
    
    def range_on(self, start_pix: int, stop_pix: int, color=(255,255,0)):
        for i in range(start_pix, stop_pix):
            self.pixels[i] = color
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
