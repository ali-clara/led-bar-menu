class board:
    D10 = "GPIO pin 10"

    def __init__(self):
        pass
        
class NeoPixel():
    def __init__(
        self,
        pin,
        n: int,
        *,
        bpp: int = 3,
        brightness: float = 1.0,
        auto_write: bool = True,
        pixel_order: str = None
    ):
        pass

    def __setitem__(self, key, value):
        setattr(self, str(key), value)

    def __getitem__(self, key):
        return getattr(self, key)

    def deinit(self):
        pass

    def fill(self, color):
        pass

    def show(self):
        pass

if __name__ == "__main__":
    pixels = NeoPixel("pin", 150)
    pixels.deinit()
    print(board.D10)


