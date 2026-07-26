# Source - https://stackoverflow.com/a/79750181
# Posted by Thilo Cestonaro
# Retrieved 2026-07-26, License - CC BY-SA 4.0

import threading
import time

class RepeatTimer():
    def __init__(self, interval, callback):
        self.interval = interval
        self.callback = callback

    def reset(self):
        print("\nResetting lights timer\n")
        self.timer.cancel()
        self.start()

    def start(self):
        self.timer = threading.Timer(self.interval, self.callback)
        self.timer.daemon = True
        self.timer.start()

    def cancel(self):
        self.timer.cancel()

if __name__ == "__main__":
    def dummy():
        print("foo")

    t = RepeatTimer(5.0, dummy)
    t.start()
    time.sleep(7)
    t.reset()

    # time.sleep(5)