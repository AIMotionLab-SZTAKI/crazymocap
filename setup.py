from setuptools import setup, find_packages

setup(name='crazymocap',
      version='1.0.0',
      packages=find_packages(),
      install_requires=[
            'pyusb',
            'motioncapture',
            'numpy',
            'usb',
            'libusb_package',
            'win-precise-time==1.4.2 ; platform_system=="Windows"',
        ]
      )
