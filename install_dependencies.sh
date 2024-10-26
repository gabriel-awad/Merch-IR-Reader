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

echo "All dependencies have been installed successfully!"
