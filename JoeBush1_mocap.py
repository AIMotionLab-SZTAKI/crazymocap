from crazymocap.radio_streamer import RadioStreamer
import traceback


streamer = RadioStreamer(devid=0, ip="192.168.2.141", object_name="JoeBush1")
try:
    while True:
        streamer.send_pose()
except Exception as exc:
    print(f"Exception: {exc!r}. TRACEBACK:\n")
    print(traceback.format_exc())
    streamer.close()

input("Press Enter to exit...")
