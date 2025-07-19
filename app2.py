from flask import Flask, render_template, jsonify, request
import requests
import time
from datetime import datetime
import csv
import os
import threading

app = Flask(__name__)

ESP_URL = "http://192.168.1.192"
GPIO_URLS = {
    "gpio0_high": f"{ESP_URL}/gpio0/high",
    "gpio0_low": f"{ESP_URL}/gpio0/low",
    "gpio2_high": f"{ESP_URL}/gpio2/high",
    "gpio2_low": f"{ESP_URL}/gpio2/low"
}

# Global variables for setpoints and auto control
low_setpoint = None
high_setpoint = None
auto_enabled = False

# Initialize CSV log file with header
with open("battery_web_log.csv", "a") as f:
    if f.tell() == 0:
        f.write("timestamp,voltage_a0,voltage_a1,action\n")
        f.flush()

def fetch_voltages():
    try:
        response = requests.get(ESP_URL, timeout=1)
        lines = response.text.strip().split('\n')
        voltage_a0 = float(lines[0].split(':')[1])
        voltage_a1 = float(lines[1].split(':')[1])
        return {"voltage_a0": voltage_a0, "voltage_a1": voltage_a1, "error": None}
    except (requests.RequestException, ValueError) as e:
        return {"voltage_a0": None, "voltage_a1": None, "error": str(e)}

def log_action(voltage_a0, voltage_a1, action):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    with open("battery_web_log.csv", "a") as f:
        f.write(f"{timestamp},{voltage_a0 if voltage_a0 is not None else ''},{voltage_a1 if voltage_a1 is not None else ''},{action}\n")
        f.flush()

def parse_passive_log():
    data = {"timestamps": [], "voltage_a0": [], "voltage_a1": [], "error": None}
    csv_file = "battery_passive_log.csv"
    
    if not os.path.exists(csv_file):
        data["error"] = "CSV file not found"
        log_action(None, None, f"Graph error: {data['error']}")
        return data
    
    try:
        with open(csv_file, "r") as f:
            reader = csv.DictReader(f)
            # Validate headers
            expected_headers = {"timestamp", "voltage_a0", "voltage_a1"}
            if not expected_headers.issubset(reader.fieldnames):
                data["error"] = "Invalid CSV headers"
                log_action(None, None, f"Graph error: {data['error']}")
                return data
            
            for row in reader:
                try:
                    # Skip error lines or invalid data
                    if not row["voltage_a0"] or not row["voltage_a1"]:
                        continue
                    voltage_a0_raw = float(row["voltage_a0"])
                    voltage_a0 = voltage_a0_raw * 2.0  # Scale to battery voltage
                    voltage_a1 = float(row["voltage_a1"])  # Raw A1 voltage
                    timestamp = row["timestamp"]
                    # Validate timestamp format and convert to epoch seconds
                    dt = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S.%f")
                    epoch = dt.timestamp()
                    data["timestamps"].append(epoch)
                    data["voltage_a0"].append(voltage_a0)
                    data["voltage_a1"].append(voltage_a1)
                except (ValueError, KeyError):
                    continue
        
        if not data["timestamps"]:
            data["error"] = "No valid data in CSV"
            log_action(None, None, f"Graph error: {data['error']}")
        
    except Exception as e:
        data["error"] = f"CSV parsing failed: {str(e)}"
        log_action(None, None, f"Graph error: {data['error']}")
    
    return data

@app.route('/')
def index():
    voltages = fetch_voltages()
    return render_template('index.html', voltages=voltages, low_setpoint=low_setpoint, high_setpoint=high_setpoint, auto_enabled=auto_enabled)

@app.route('/voltages')
def get_voltages():
    return jsonify(fetch_voltages())

@app.route('/graph_data')
def get_graph_data():
    return jsonify(parse_passive_log())

@app.route('/gpio/<action>')
def control_gpio(action):
    if action not in GPIO_URLS:
        return jsonify({"status": "error", "message": "Invalid action"})

    try:
        response = requests.get(GPIO_URLS[action], timeout=1)
        voltages = fetch_voltages()
        action_message = {
            "gpio0_high": "Turned off LED lights (GPIO0 HIGH)",
            "gpio0_low": "Turned on LED lights (GPIO0 LOW)",
            "gpio2_high": "Turned on battery charging (GPIO2 HIGH)",
            "gpio2_low": "Turned off battery charging (GPIO2 LOW)"
        }[action]
        log_action(voltages["voltage_a0"], voltages["voltage_a1"], action_message)
        return jsonify({"status": "success", "message": response.text, "voltages": voltages})
    except requests.RequestException as e:
        log_action(None, None, f"Error: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/set_setpoints', methods=['POST'])
def set_setpoints():
    global low_setpoint, high_setpoint, auto_enabled
    try:
        low = float(request.form['low_setpoint'])
        high = float(request.form['high_setpoint'])
        if low >= high:
            return jsonify({"status": "error", "message": "Low setpoint must be less than high setpoint"})
        low_setpoint = low
        high_setpoint = high
        auto_enabled = True
        log_action(None, None, f"Setpoints updated: low={low}, high={high}")
        return jsonify({"status": "success", "message": f"Setpoints set: low={low}, high={high}"})
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid setpoint values"})

def auto_control_loop():
    global low_setpoint, high_setpoint, auto_enabled
    while True:
        if auto_enabled and low_setpoint is not None and high_setpoint is not None:
            voltages = fetch_voltages()
            if voltages["error"] is None:
                battery_voltage = voltages["voltage_a0"] * 2.0  # Scale to battery voltage
                voltage_a1 = voltages["voltage_a1"]
                voltage_a0 = voltages["voltage_a0"]
                if battery_voltage < low_setpoint:
                    # Turn on battery charging (GPIO2 HIGH) and turn off LED lights (GPIO0 HIGH)
                    requests.get(GPIO_URLS["gpio2_high"], timeout=1)
                    requests.get(GPIO_URLS["gpio0_high"], timeout=1)
                    log_action(voltage_a0, voltage_a1, "Auto: Turned on charging and off LED (below low setpoint)")
                elif battery_voltage > high_setpoint:
                    # Turn off battery charging (GPIO2 LOW) and turn on LED lights (GPIO0 LOW)
                    requests.get(GPIO_URLS["gpio2_low"], timeout=1)
                    requests.get(GPIO_URLS["gpio0_low"], timeout=1)
                    log_action(voltage_a0, voltage_a1, "Auto: Turned off charging and on LED (above high setpoint)")
        time.sleep(10)  # Check every 10 seconds

if __name__ == '__main__':
    # Start the auto control background thread
    thread = threading.Thread(target=auto_control_loop)
    thread.daemon = True
    thread.start()
    app.run(host='0.0.0.0', port=5020, debug=True)
