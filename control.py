import requests
import time
from datetime import datetime

url = "http://192.168.1.192"
gpio0_high_url = "http://192.168.1.192/gpio0/high"
gpio0_low_url = "http://192.168.1.192/gpio0/low"
gpio2_high_url = "http://192.168.1.192/gpio2/high"
gpio2_low_url = "http://192.168.1.192/gpio2/low"

# Initialize CSV log file with header
with open("battery_control_log.csv", "a") as f:
    if f.tell() == 0:  # Write header if file is empty
        f.write("timestamp,voltage_a0,voltage_a1,action\n")
        f.flush()

while True:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Millisecond precision
    print("Enter '0h' for GPIO0 HIGH, '0l' for GPIO0 LOW, '2h' for GPIO2 HIGH, '2l' for GPIO2 LOW, or press Enter to continue:")
    user_input = input().lower()

    if user_input in ['0h', '0l', '2h', '2l']:
        try:
            # Fetch voltages
            response = requests.get(url, timeout=1)
            lines = response.text.strip().split('\n')
            voltage_a0 = float(lines[0].split(':')[1])
            voltage_a1 = float(lines[1].split(':')[1])

            # Execute GPIO command
            action = ""
            if user_input == '0h':
                response = requests.get(gpio0_high_url, timeout=1)
                action = "GPIO0 set to HIGH"
            elif user_input == '0l':
                response = requests.get(gpio0_low_url, timeout=1)
                action = "GPIO0 set to LOW"
            elif user_input == '2h':
                response = requests.get(gpio2_high_url, timeout=1)
                action = "GPIO2 set to HIGH"
            elif user_input == '2l':
                response = requests.get(gpio2_low_url, timeout=1)
                action = "GPIO2 set to LOW"

            # Display and log
            print(f"{timestamp}\nVoltage A0: {voltage_a0:.4f} V\nVoltage A1: {voltage_a1:.4f} V\n{action}")
            with open("battery_control_log.csv", "a") as f:
                f.write(f"{timestamp},{voltage_a0:.4f},{voltage_a1:.4f},{action}\n")
                f.flush()

        except (requests.RequestException, ValueError) as e:
            print(f"{timestamp}\nError: {e}")
            with open("battery_control_log.csv", "a") as f:
                f.write(f"{timestamp},,,'Error: {e}'\n")
                f.flush()

    time.sleep(1)  # Wait before next prompt
