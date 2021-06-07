#! /usr/bin/env python

from distutils.util import get_platform
import sys

from setuptools import setup, Extension, find_packages
from setuptools.command.build_py import build_py

if sys.version_info[0:2] < (2, 6):
    raise RuntimeError("smartcard_control requires Python 3.0+ to build.")

from smartcard_control.controller.main_controller import VERSION_STR

setup(name="smartcard_control",
      version=VERSION_STR,
      description="Smartcard control tool",
      author="Elouan Petereau",
      author_email="elouan.p@gmail.com",
      url="https://github.com/ElouanPetereau/smartcard_control",
      packages=find_packages(include=['smartcard_control', 'smartcard_control.*']),
      entry_points={
          'console_scripts': [
              'smartcard_control = smartcard_control.controller.main_controller:run',
          ]
      },
      install_requires=['pyscard >= 2.0.0'],
      classifiers=[
          'Intended Audience :: Developers',
          'Operating System :: Unix',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python :: 3'
      ]
      )
