from crazyradio import Crazyradio
import traceback
import atexit
import motioncapture
import time
import array
from typing import List
import numpy as np


def quat_2_yaw(quat: List[float]):
    """ Takes a quaternion as a list in order of x, y, z, w, and returns its yaw.
     TODO: Note what convention yaw is in, OR decide it doesn't matter in case of the car (it probably doesn't)"""
    x = quat[0]
    y = quat[1]
    z = quat[2]
    w = quat[3]
    siny_cosp = 2*(w*z + x*y)
    cosy_cosp = 1-2*(y*y + z*z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return yaw


class RadioStreamer:
    """Class to encapsulate  the streaming crazyradio.
    In theory, the only public method you should need is send_pose, and maybe close"""
    def __init__(self, obj_name, devid, ip="192.168.2.141", mode=Crazyradio.MODE_PTX, channel=100, data_rate=Crazyradio.DR_250KPS):
        # initialize radio
        self.radio = Crazyradio(devid=devid)  # if you only have 1 dongle in your PC, this must be 0
        self.radio.set_channel(channel)
        self.radio.set_data_rate(data_rate)
        self.radio.set_mode(mode)
        # make sure radio gets released before the program quits
        atexit.register(self.close)
        self.mocap = motioncapture.MotionCaptureOptitrack(ip)
        self.obj_name = obj_name
        self.start_time = time.time()

    def _timestamp(self):
        return time.time() - self.start_time

    def _wait_frame_parse_pose(self):
        """ Returns None if the object isn't in frame. Else returns an  array.array (NOT LIST) like so:
        [time_since_initialization, heading(radians), x(m), y(m), z(m)], where each element is a float
        Before returning this data, it has to wait for an optitrack frame, which
        can only happen with a maximum of 120 fps, so this function has a built-in frame limit"""
        self.mocap.waitForNextFrame()
        try:
            obj = self.mocap.rigidBodies[self.obj_name]
            yaw = quat_2_yaw([obj.rotation.x, obj.rotation.y, obj.rotation.z, obj.rotation.w])
            return array.array("f", [self._timestamp()] + [yaw] + list(obj.position))
        except KeyError:  # not in frame
            return None

    def send_pose(self):
        pose = self._wait_frame_parse_pose()
        if pose is not None:
            res = self.radio.send_packet(pose)
            if res is not None and res.ack:
                print(f"sent {pose}")
            return res

    def close(self):
        self.radio.close()


if __name__=="__main__":
    print("Starting TX")
    streamer = RadioStreamer(obj_name="cf2", devid=1)
    try:
        while True:
            streamer.send_pose()
    except Exception as exc:
        print(f"Exception: {exc!r}. TRACEBACK:\n")
        print(traceback.format_exc())
        streamer.close()

    input("Press Enter to exit...")
