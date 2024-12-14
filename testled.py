import time
from rpi_ws281x import Adafruit_NeoPixel, Color

LED_COUNT = 8        
LED_PIN = 18         
LED_FREQ_HZ = 800000 
LED_DMA = 10        
LED_BRIGHTNESS = 255 
LED_INVERT = False    

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS)

strip.begin()

for i in range(LED_COUNT):
    strip.setPixelColor(i, Color(255, 0, 0))
    strip.show()
    time.sleep(0.5)

for i in range(LED_COUNT):
    strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    time.sleep(0.5)