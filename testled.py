import board
import neopixel
import time

pixels = neopixel.NeoPixel(board.D18, 150, brightness=0.2, auto_write=False)

pixels.fill((0, 255, 0))
pixels.show()
time.sleep(5)


