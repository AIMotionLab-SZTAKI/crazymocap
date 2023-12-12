import array

from crazyradio import Crazyradio
import traceback
import time
import atexit
import motioncapture


class RadioReciever:
    def __init__(self, devid, mode=Crazyradio.MODE_PRX, channel=100, data_rate=Crazyradio.DR_250KPS):
        self.radio = Crazyradio(devid=devid)
        self.radio.set_channel(channel)
        self.radio.set_data_rate(data_rate)
        self.radio.set_mode(mode)
        atexit.register(self.close)

    def receive(self):
        buffer = array.array("f", [0.0, 0.0, 0.0, 0.0, 0.0])
        rec = self.radio.receive(buffer)
        if rec == buffer.itemsize * len(buffer):
            # self.radio.sendAck(buffer)
            return buffer
        else:
            return None

    def close(self):
        self.radio.close()


print("Starting RX")
receiver = RadioReciever(devid=1)
try:
    while True:
        rec = receiver.receive()
        if rec is not None:
            print(f"received {rec}")

except Exception as exc:
    print(f"Exception: {exc!r}. TRACEBACK:\n")
    print(traceback.format_exc())
    receiver.radio.close()
input("Press Enter to exit...")
