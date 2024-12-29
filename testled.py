import board
import neopixel
import time

pixels = neopixel.NeoPixel(board.D18, 150)

pixels[0] = (255, 0, 0)
pixels.show()
time.sleep(5)


