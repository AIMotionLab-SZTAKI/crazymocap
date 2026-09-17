import subprocess
import sys
import time
import platform
from pathlib import Path

# rigid body name in Motive, passed to the streamer's -o argument
OBJECT_NAME = "bb3"
# seconds to wait between starting the streamer and the receiver, so that the streamer has claimed its dongle before
# the receiver goes looking for a free one
LAUNCH_DELAY = 2.0

PACKAGE_DIR = Path(__file__).resolve().parent / "crazymocap"


def launch_in_new_terminal(script: Path, *script_args: str) -> subprocess.Popen:
    # sys.executable is the interpreter running this script, so the new terminal uses the same venv even if it isn't
    # activated there
    command = [sys.executable, str(script), *script_args]
    if platform.system() == "Windows":
        # /K keeps the window open after the script exits, so its output can still be read
        return subprocess.Popen(["cmd", "/K", *command], creationflags=subprocess.CREATE_NEW_CONSOLE)
    elif platform.system() == "Linux":
        return subprocess.Popen(["x-terminal-emulator", "-e", *command])
    else:
        raise NotImplementedError(f"Opening a new terminal is not supported on {platform.system()}")


print(f"Starting tx for {OBJECT_NAME}...")
tx = launch_in_new_terminal(PACKAGE_DIR / "radio_streamer.py", "-o", OBJECT_NAME)
time.sleep(LAUNCH_DELAY)
print("Starting rx...")
rx = launch_in_new_terminal(PACKAGE_DIR / "radio_receiver.py")
