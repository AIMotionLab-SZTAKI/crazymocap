import subprocess
import time
import platform


print(f"Starting tx...")
if platform.system() == "Windows":
    tx = subprocess.Popen(["start", "cmd", "/K", "python", "crazymocap/radio_streamer.py"], shell=True)
elif platform.system() == "Linux":
    tx = subprocess.Popen(["x-terminal-emulator", "-e", "python3", "crazymocap/radio_streamer.py"])

# time.sleep(2)

print(f"Starting rx...")
if platform.system() == "Windows":
    rx = subprocess.Popen(["start", "cmd", "/K", "python", "crazymocap/radio_receiver.py"], shell=True)
elif platform.system() == "Linux":
    rx = subprocess.Popen(["x-terminal-emulator", "-e", "python3", "crazymocap/radio_receiver.py"])








