#!/bin/bash

# Update package list
sudo apt-get update

# Install RPi.GPIO
sudo apt-get install -y python3-rpi.gpio

# Install Adafruit Blinka
sudo pip3 install adafruit-blinka

# Install Adafruit NeoPixel
sudo pip3 install adafruit-circuitpython-neopixel

# Install Adafruit IRRemote
sudo pip3 install adafruit-circuitpython-irremote

# Install Flask
sudo pip3 install flask

# Install Requests
sudo pip3 install requests

# Install build tools for rpi_ws281x
sudo apt-get install -y build-essential python-dev git scons swig

# Clone and install rpi_ws281x
git clone https://github.com/jgarff/rpi_ws281x.git
cd rpi_ws281x
sudo scons
sudo scons install
cd python
sudo python3 setup.py build
sudo python3 setup.py install

# Cleanup
cd ../..
rm -rf rpi_ws281x

echo "All dependencies have been installed successfully! You are now free to close this window!"
