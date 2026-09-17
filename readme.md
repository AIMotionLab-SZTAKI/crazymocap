# crazymocap

`crazymocap` is a Python package for transmitting and receiving motion capture data from one computer to another over a one-way radio link, using a pair of [Crazyradio](https://www.bitcraze.io/products/crazyradio-pa/) USB dongles. The package supplies a **streamer**, which reads the pose of one rigid body from OptiTrack and transmits it, and a **receiver**, which picks the pose up on the other end. 

```
OptiTrack (Motive) ──> RadioStreamer ──> Crazyradio (PTX) ~~~~~~> Crazyradio (PRX) ──> RadioReciever ──> your code
```

The rigid body names are the ones used in Motive.

## 1. Installation

### 1.1 Which Python version

**Use Python 3.11.**

The OptiTrack connection relies on `motioncapture`, pinned to version `1.0a2`. The streamer uses the `MotionCaptureOptitrack` class, which was removed in `1.0a4` in favour of `motioncapture.connect()`. Version `1.0a2` publishes prebuilt wheels only up to Python 3.11; on newer versions pip falls back to compiling it from source, which fails. `pyproject.toml` therefore refuses Python 3.12 and above. If you don't have a Python 3.11 interpreter, a conda environment is a clean way to get one without touching the system Python: install [Miniconda](https://docs.anaconda.com/miniconda/), run `conda create -n <python_311_env> python=3.11`, and use that environment only as the base interpreter of the venv below.

Note that this applies to *both* computers: the receiver doesn't use `motioncapture`, but installing the package installs all of its dependencies.

### 1.2 Installing

Clone the repository, and create a virtual environment inside it:

```bash
git clone https://github.com/AIMotionLab-SZTAKI/crazymocap.git
cd crazymocap
conda activate <python_311_env>        # OPTIONAL: if your default python is not 3.11
python -m venv venv
source venv/bin/activate    # on Windows: venv\Scripts\activate
python --version            # should print Python 3.11.x
pip install --upgrade pip
pip install -e .
```

`-e` (editable) installs the package as a link to this folder: edit the source, and the change takes effect immediately, with no reinstall.

To use the package from another project instead, depend on it by git URL in that project's `pyproject.toml`:

```toml
dependencies = ["crazymocap @ git+https://github.com/AIMotionLab-SZTAKI/crazymocap.git"]
```

### 1.3 Hardware and USB access

The transmitting side can be either a Crazyradio PA or a Crazyradio 2.0. The receiving side must be a Crazyradio PA: it has to be switched into PRX (receiver) mode, and the Crazyradio 2.0 firmware doesn't implement that mode switch in the USB protocol used here (see [crazyradio2-firmware#7](https://github.com/bitcraze/crazyradio2-firmware/issues/7)). The driver talks to the dongle directly through libusb, so the operating system has to let it:

- On Linux, the libusb backend comes bundled with the `libusb-package` dependency, but a normal user has no permission to access the dongle until the udev rules are installed. Follow Bitcraze's [USB permissions guide](https://www.bitcraze.io/documentation/repository/crazyflie-lib-python/master/installation/usb_permissions/).
- On Windows, the driver uses the libusb0 backend, which requires the libusb driver to be installed for the dongle (with Zadig). Follow Bitcraze's [Crazyradio Windows driver guide](https://www.bitcraze.io/documentation/repository/crazyradio-firmware/master/building/usbwindows/).


## 2. How it works

The package has three modules:

| Module | Contents |
| --- | --- |
| [crazymocap/crazyradio.py](crazymocap/crazyradio.py) | `Crazyradio`, the low-level USB driver of the dongle, copied from [crazyflie-lib-python](https://github.com/bitcraze/crazyflie-lib-python/blob/master/cflib/drivers/crazyradio.py). |
| [crazymocap/radio_streamer.py](crazymocap/radio_streamer.py) | `RadioStreamer`: OptiTrack in, radio packets out. |
| [crazymocap/radio_receiver.py](crazymocap/radio_receiver.py) | `RadioReciever`: radio packets in, poses out. |

### 2.1 The radio link

The Crazyradio speaks Nordic Semiconductor's Enhanced ShockBurst radio protocol, which has two roles: a **PTX** (transmitter), which sends packets, and a **PRX** (eceiver), which listens for them. When the PRX receives a packet (from the PTX), it automatically answers with an acknowledgement (ACK). If the PTX gets no ACK (from the PRX), it retransmits the packet, up to a set number of retries. This is the mechanism that normally lets a PC talk to a Crazyflie; here, both ends are dongles.

For two dongles to hear each other, three settings have to match:
- Channel, e.g. 2500 Mhz, `RadioStreamer` / `RadioReciever` constructor argument
- Data rate e.g. 250 kbit/s, `RadioStreamer` / `RadioReciever` constructor argument
- Address, e.g. `E7E7E7E7E7` , in `Crazyradio` constructor (not exposed by the wrappers) 

The defaults of the two classes match, so a streamer and a receiver constructed with default arguments find each other. If you change the channel or data rate on one side, change it on the other side too. Before settling on a channel, make sure it isn't used by the drones flying at the same time. The rest of the radio configuration comes from the `Crazyradio` constructor: 0 dBm transmit power, ACKs enabled, and 3 retries on a missing ACK.

### 2.2 The packet

Each packet is 20 bytes: five 32-bit floats, in the native byte order of the streaming computer (little-endian probably):

| Index | Field | Unit |
| --- | --- | --- |
| 0 | timestamp | s |
| 1 | yaw | rad, in [-π, π] |
| 2 | x | m |
| 3 | y | m |
| 4 | z | m |

In Python, `RadioReciever` does the decoding for you. From other languages, the packet can be decoded as a plain array of five `float32`s; e.g. with Python's `struct` module, the format is `"<5f"`.

### 2.3 `crazyradio.py`

This is Bitcraze's USB driver for the dongle, copied from [crazyflie-lib-python](https://github.com/bitcraze/crazyflie-lib-python), so that the package doesn't need all of `cflib` just for the radio. You will rarely need to touch it, but it helps to know the parts the package relies on:

- **Finding the dongle.** `Crazyradio(devid=n)` opens the `n`-th Crazyradio found on USB, in USB enumeration order, whether or not another process is already using it. The wrapper classes instead open their dongle with `open_first_free(n)`, which tries the dongles from the `n`-th onwards, skips the ones another process is using (on Linux, these fail with `EBUSY`), and claims the first free one right away, so that other processes see it as busy too. This lets a streamer and a receiver started on the same computer, both with the default `devid=0` end up on different dongles.
- **Sending.** `send_packet(data)` writes the packet to the dongle, then reads back a status telling whether an ACK arrived, how many retries it took, and the ACK's payload if it had one. It blocks until the dongle reports back, so with a PTX and no listening PRX, each send waits for all the retries to run out.
- **Receiving.** `receive(buffer, timeout)` reads a packet from a dongle in PRX mode. It returns `None` if nothing arrived within the timeout (1 s by default).
- **Mode switching.** `set_mode(Crazyradio.MODE_PTX)` / `set_mode(Crazyradio.MODE_PRX)` sends the mode switch request, which the Crazyradio 2.0 doesn't implement fully yet.

## 3. Using the package

### 3.1 `RadioStreamer`

```python
from crazymocap.radio_streamer import RadioStreamer

streamer = RadioStreamer(devid=0, ip="192.168.2.141", object_name="JoeBush1")
while True:
    streamer.send_pose()
```

The constructor takes the following arguments:

| Argument | Default | Meaning |
| --- | --- | --- |
| `devid` | `0` | Where to start looking for a dongle. |
| `ip` | `-i`/`--ip`, or `"192.168.2.141"` | The address of the OptiTrack (Motive) computer. |
| `object_name` | `-o`/`--object_name`, or `"JoeBush1"` | The name of the rigid body in Motive. |
| `channel` | `100` | Radio channel. Must match the receiver's. |
| `data_rate` | `Crazyradio.DR_250KPS` | Radio data rate. Must match the receiver's. |

On construction, the streamer opens and configures the dongle (raising an exception if every dongle is already in use), connects to OptiTrack, then checks that a frame arrives and that it contains the rigid body `object_name`, raising an exception otherwise. Once the checks have passed, it starts the clock of the timestamps.

Each call to `send_pose()` blocks until the next OptiTrack frame arrives, builds the 20 byte packet of timestamp, yaw and position, and sends it. If the rigid body isn't in the frame (e.g. because it's out of view of the cameras), nothing is sent. Call it in a loop to send one packet per OptiTrack frame, at Motive's frame rate. 

The dongle is released by `close()`, which is also registered to run automatically when the program exits.

### 3.2 `RadioReciever`

Note the spelling of the class name.

```python
from crazymocap.radio_receiver import RadioReciever

receiver = RadioReciever(devid=0)
while True:
    pose = receiver.receive()
    if pose is not None:
        timestamp, yaw, x, y, z = pose
```

The constructor takes `devid`, `channel` and `data_rate`, with the same meaning and defaults as for the streamer.

`receive()` waits for a packet for at most 1 second. If a 20 byte packet arrives, it returns it as an `array.array` of five floats: timestamp, yaw, x, y, z. It returns `None` if nothing arrived, or if what arrived wasn't 20 bytes long. There is no buffering beyond what the dongle does: to keep up with the streamer, call `receive()` at least as often as OptiTrack produces frames.

`close()` releases the dongle, and is registered to run automatically at exit.

## 4. Testing the link: `test_rx_tx.py`

[test_rx_tx.py](test_rx_tx.py) tests the link on a single computer with two dongles plugged in, the second of which (in USB order) must be a Crazyradio PA. It opens two terminal windows: one runs `radio_streamer.py` for the rigid body set in `OBJECT_NAME`, and the other, started `LAUNCH_DELAY` seconds later so that the streamer has already claimed its dongle, runs `radio_receiver.py`. With OptiTrack streaming and the rigid body in view, the streamer's window prints that it's initialized, then stays quiet, while the receiver's window prints a line for every OptiTrack frame: the arrival time on the receiver's clock, followed by the received timestamp, yaw, x, y and z, which should follow the object as it moves in Motive.
