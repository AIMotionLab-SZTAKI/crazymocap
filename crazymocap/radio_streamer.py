from crazymocap.crazyradio import Crazyradio
import traceback
import atexit
import motioncapture
import array
from typing import List
import numpy as np
import argparse
import platform
import concurrent.futures

# win cant even get time right
if platform.system() == 'Windows':
    import win_precise_time as time
else:
    import time

parser = argparse.ArgumentParser()
parser.add_argument("-i", "--ip", default="192.168.2.141")
parser.add_argument("-o", "--object_name", default="JoeBush1")
parser.add_argument("-d", "--devid", default=0)
args = vars(parser.parse_args())


def quat_2_yaw(quat: List[float]):
    x = quat[0]
    y = quat[1]
    z = quat[2]
    w = quat[3]
    siny_cosp = 2 * (w * z + x * y)
    cosy_cosp = 1 - 2 * (y * y + z * z)
    yaw = np.arctan2(siny_cosp, cosy_cosp)
    return yaw


def call_with_timeout(func, timeout=5):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(func)
        try:
            future.result(timeout=timeout)
            return True
        except concurrent.futures.TimeoutError:
            return False


class RadioStreamer:

    def __init__(self, devid, ip=args['ip'], mode=Crazyradio.MODE_PTX, channel=100, data_rate=Crazyradio.DR_250KPS,
                 object_name=args["object_name"]):
        self.radio = Crazyradio(devid=devid)
        self.radio.set_channel(channel)
        self.radio.set_data_rate(data_rate)
        self.radio.set_mode(mode)
        atexit.register(self.close)
        self.mocap = motioncapture.MotionCaptureOptitrack(ip)
        self.obj_name = object_name
        self.check_mocap()
        print(f"MoCap radio streamer initialized for object {self.obj_name}!")
        self.start_time = time.time()

    def check_mocap(self):
        if not call_with_timeout(self.mocap.waitForNextFrame):
            raise Exception("Connection cannot be established with the MoCap server!")
        try:
            obj = self.mocap.rigidBodies[self.obj_name]
        except KeyError:
            raise Exception(f"The pose data of {self.obj_name} is not streamed by the MoCap server!")

    def timestamp(self):
        return time.time() - self.start_time

    def wait_frame_parse_pose(self):
        self.mocap.waitForNextFrame()
        try:
            obj = self.mocap.rigidBodies[self.obj_name]
            yaw = quat_2_yaw([obj.rotation.x, obj.rotation.y, obj.rotation.z, obj.rotation.w])
            return array.array("f", [self.timestamp()] + [yaw] + list(obj.position))
        except KeyError:  # not in frame
            return None

    def _send(self, data):
        res = self.radio.send_packet(data)
        # TODO: check if we got response?
        """
        if res is not None and res.ack:
            print(f"sent data {data}, got response")
        """
        return res.ack, res.data

    def send_pose(self):
        pose = self.wait_frame_parse_pose()
        if pose is not None:
            res = self._send(pose)
            # print(pose)

    def close(self):
        self.radio.close()


if __name__ == "__main__":
    print("Starting TX")
    streamer = RadioStreamer(devid=args["devid"])
    try:
        while True:
            streamer.send_pose()
    except Exception as exc:
        print(f"Exception: {exc!r}. TRACEBACK:\n")
        print(traceback.format_exc())
        streamer.close()

    input("Press Enter to exit...")
