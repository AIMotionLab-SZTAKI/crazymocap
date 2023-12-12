from crazyradio import Crazyradio
import traceback
import atexit
import motioncapture
import time
import array
from typing import List
import numpy as np


def quat_2_yaw(quat: List[float]):
    x = quat[0]
    y = quat[1]
    z = quat[2]
    w = quat[3]
    siny_cosp = 2*(w*z + x*y)
    cosy_cosp = 1-2*(y*y + z*z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return yaw


class RadioStreamer:

    def __init__(self, devid, ip="192.168.2.141", mode=Crazyradio.MODE_PTX, channel=100, data_rate=Crazyradio.DR_250KPS):
        self.radio = Crazyradio(devid=devid)
        self.radio.set_channel(channel)
        self.radio.set_data_rate(data_rate)
        self.radio.set_mode(mode)
        atexit.register(self.close)
        self.mocap = motioncapture.MotionCaptureOptitrack(ip)
        self.obj_name = "cf2"

    def wait_frame_parse_pose(self):
        self.mocap.waitForNextFrame()
        try:
            obj = self.mocap.rigidBodies[self.obj_name]
            yaw = quat_2_yaw([obj.rotation.x, obj.rotation.y, obj.rotation.z, obj.rotation.w])
            return array.array("f", [yaw] + list(obj.position))
        except KeyError:  # not in frame
            return None

    def _send(self, data):
        res = self.radio.send_packet(data)
        #TODO: check if we got response?
        if res is not None and res.ack:
            print(f"sent data {data}, got response")
        return res

    def send_pose(self):
        pose = self.wait_frame_parse_pose()
        if pose is not None:
            self._send(pose)

    def close(self):
        self.radio.close()


print("Starting TX")
streamer = RadioStreamer(devid=1)
try:
    while True:
        streamer.send_pose()
except Exception as exc:
    print(f"Exception: {exc!r}. TRACEBACK:\n")
    print(traceback.format_exc())
    streamer.close()

input("Press Enter to exit...")
