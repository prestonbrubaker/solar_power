import requests
import time
from datetime import datetime

url = "http://192.168.1.192"

# Initialize CSV log file with header
with open("battery_passive_log.csv", "a") as f:
    if f.tell() == 0:  # Write header if file is empty
        f.write("timestamp,voltage_a0,voltage_a1\n")
        f.flush()

while True:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Millisecond precision
    try:
        # Fetch voltages
        response = requests.get(url, timeout=0.1)  # Short timeout for high frequency
        lines = response.text.strip().split('\n')
        voltage_a0 = float(lines[0].split(':')[1])
        voltage_a1 = float(lines[1].split(':')[1])

        # Log to CSV
        with open("battery_passive_log.csv", "a") as f:
            f.write(f"{timestamp},{voltage_a0:.4f},{voltage_a1:.4f}\n")
            f.flush()

        # Print for monitoring
        print(f"{timestamp}, A0: {voltage_a0:.4f} V, A1: {voltage_a1:.4f} V")

    except (requests.RequestException, ValueError) as e:
        with open("battery_passive_log.csv", "a") as f:
            f.write(f"{timestamp},,,'Error: {e}'\n")
            f.flush()
        print(f"{timestamp}, Error: {e}")

    # Minimize delay for maximum frequency (~100ms target)
    time.sleep(5)  # Small sleep to prevent CPU overload
