#!/bin/sh

sudo apt update

# Conan CCI system recipes used by Qt5 on Linux check for these packages.
# Keep this in sync with failures from opengl/system, xorg/system, xkeyboard-config/system.
sudo apt install -y \
  libgl-dev \
  libgl1-mesa-dev \
  xorg-dev \
  xkeyboard-config
