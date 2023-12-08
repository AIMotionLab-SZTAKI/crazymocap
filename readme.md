# crazymocap: Low-latency motion-capture datastream with Crazyradios
TODO: some description
## Installation
If you wish to modify this package clone the repo and install the package as an editable
```
$ git clone https://github.com/flochkristof/crazymocap.git
$ cd crazymocap/
```
It is recommended to use the package in a virtual environment. To create and activate run:
```
$ python3 -m venv venv
$ source venv/bin/activate
```
Finally, install the package and requirements
```
$ pip install -e .
```
Alternatively, you can add this package to your software as a dependency e.g. in the `setup.py`:
```
install_requires=[
        #'some_fancy_package',
        "crazymocap @ git+https://github.com/flochkristof/crazymocap.git",
        #'some_other_package'
        ]
```
## Usage
TODO