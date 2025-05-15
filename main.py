import os
import subprocess

# Check if it's the first run
if not os.path.exists('first_run_complete'):
    # Run the shell script to install dependencies
    subprocess.run(['bash', 'install_dependencies.sh'], check=True)
    # Create a file to indicate the first run is complete
    with open('first_run_complete', 'w') as f:
        f.write('This file marks that the first run dependencies were installed.')

import RPi.GPIO as GPIO
import time
import board
import neopixel
import socket
from adafruit_irremote import IRDecodeError, GenericDecode
from flask import Flask, render_template, request, redirect, url_for
import threading
import requests

# GPIO Pins
RECV_PIN = 17 # Pin where the IR receiver is connected (BCM numbering)
BUTTON_PIN = 27 # Pin where the button is connected
LED_PIN = board.18 # Pin where the NeoPixel ring is connected

# Number of LEDs in the NeoPixel ring
NUM_LEDS = 16

# Initialize the NeoPixel strip
strip = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=0.2, auto_write=False)

# Initialize IR decoder
decoder = GenericDecode()

activation_code = None
code_stored = False
activation_count = 0
learning_mode = False
cooldown_period = 0
last_activation_time = 0

# UDP settings
udp_ip = "10.40.32.51"
udp_port = 5005
udp_text = "Successful Test"

# Grafana settings
grafana_url = 'http://your-grafana-server/api/annotations' # Change this to your Grafana URL
grafana_api_key = 'your-grafana-api-key' # Change this to your Grafana API key

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(RECV_PIN, GPIO.IN)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Flask app setup
app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Change this to a more secure key

@app.route('/')
def index():
    global activation_code, activation_count
    return render_template('index.html', code=activation_code, count=activation_count)

@app.route('/set_code', methods=['POST'])
def set_code():
    global activation_code, code_stored
    activation_code = int(request.form['activation_code'])
    code_stored = True
    return redirect(url_for('index'))

@app.route('/set_cooldown', methods=['POST'])
def set_cooldown():
    global cooldown_period
    cooldown_period = int(request.form['cooldown'])
    return redirect(url_for('index'))

@app.route('/set_grafana', methods=['POST'])
def set_grafana():
    global grafana_url, grafana_api_key
    grafana_url = request.form['grafana_url']
    grafana_api_key = request.form['grafana_api_key']
    return redirect(url_for('index'))

@app.route('/reset_counter', methods=['POST'])
def reset_counter():
    global activation_count
    activation_count = 0
    send_grafana_metric(activation_count)
    return redirect(url_for('index'))

@app.route('/start_learning', methods=['GET'])
def start_learning():
    global learning_mode
    learning_mode = True
    return 'Learning mode activated. Point your IR remote at the receiver and press a button.'

@app.route('/set_udp', methods=['POST'])
def set_udp():
    global udp_ip, udp_port, udp_text
    udp_ip = request.form['udp_ip']
    udp_port = int(request.form['udp_port'])
    udp_text = request.form['udp_text']
    return redirect(url_for('index'))

@app.route('/test_udp', methods=['GET'])
def test_udp():
    send_udp_command(udp_text)
    return 'UDP Command sent.'

def green_chase():
    for i in range(NUM_LEDS):
        strip[i] = (0, 255, 0)
        strip.show()
        time.sleep(0.05)
        strip[i] = (0, 0, 0)

def red_pulse():
    for _ in range(3):  # Number of pulses
        for brightness in range(0, 256, 5):
            strip.fill((brightness, 0, 0))
            strip.show()
            time.sleep(0.005)
        for brightness in range(255, -1, -5):
            strip.fill((brightness, 0, 0))
            strip.show()
            time.sleep(0.005)

def blue_chase():
    for i in range(NUM_LEDS):
        strip[i] = (0, 0, 255)
        strip.show()
        time.sleep(0.5)
        strip[i] = (0, 0, 0)

def read_ir_code():
    try:
        pulses = decoder.read_pulses(RECV_PIN)
        code = decoder.decode_bits(pulses)
        return code
    except IRDecodeError:
        return None

def send_udp_command(command):
    global udp_ip, udp_port
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.sendto(command.encode('utf-8'), (udp_ip, udp_port))

def send_grafana_metric(value):
    headers = {
        'Authorization': f'Bearer {grafana_api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        "tags": ["activation_count"],
        "text": f"Activation Count: {value}"
    }
    response = requests.post(grafana_url, headers=headers, json=data)
    if response.status_code == 200:
        print("Metric sent to Grafana")
    else:
        print(f"Failed to send metric to Grafana: {response.content}")

def main_loop():
    global code_stored, activation_code, activation_count, learning_mode, last_activation_time
    try:
        while True:
            if GPIO.input(BUTTON_PIN) == GPIO.LOW:
                red_pulse()
                if not code_stored and not learning_mode:
                    code = read_ir_code()
                    if code:
                        activation_code = code
                        code_stored = True
                        print("Activation code stored")
            elif learning_mode:
                code = read_ir_code()
                if code:
                    activation_code = code
                    code_stored = True
                    learning_mode = False
                    print("New activation code learned and stored")
            else:
                if code_stored:
                    code = read_ir_code()
                    if code and (time.time() - last_activation_time >= cooldown_period):
                        blue_chase()
                        if code == activation_code:
                            activation_count += 1
                            print("Successful Test")
                            send_udp_command(udp_text)
                            send_grafana_metric(activation_count)
                            last_activation_time = time.time()
                else:
                    green_chase()
    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()

if __name__ == '__main__':
    threading.Thread(target=main_loop).start()
    app.run(debug=True, host='0.0.0.0')
