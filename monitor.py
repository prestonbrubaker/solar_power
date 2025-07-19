import requests
import time
from datetime import datetime

url = "http://192.168.1.192"
gpio0_high_url = "http://192.168.1.192/gpio0/high"
gpio0_low_url = "http://192.168.1.192/gpio0/low"
gpio2_high_url = "http://192.168.1.192/gpio2/high"
gpio2_low_url = "http://192.168.1.192/gpio2/low"

with open("battery_log.txt", "a") as f:
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # Fetch raw voltage
            response = requests.get(url)
            f.write(f"{timestamp}\nRaw Voltage: {response.text} V\n")
            f.flush()
            print(f"{timestamp}\nRaw Voltage: {response.text} V")

            # Check for user input to control GPIO0 or GPIO2
            print("Enter '0h' for GPIO0 HIGH, '0l' for GPIO0 LOW, '2h' for GPIO2 HIGH, '2l' for GPIO2 LOW, or press Enter to continue:")
            user_input = input()
            if user_input.lower() == '0h':
                response = requests.get(gpio0_high_url)
                print(response.text)
                f.write(f"{timestamp}\n{response.text}\n")
                f.flush()
            elif user_input.lower() == '0l':
                response = requests.get(gpio0_low_url)
                print(response.text)
                f.write(f"{timestamp}\n{response.text}\n")
                f.flush()
            elif user_input.lower() == '2h':
                response = requests.get(gpio2_high_url)
                print(response.text)
                f.write(f"{timestamp}\n{response.text}\n")
                f.flush()
            elif user_input.lower() == '2l':
                response = requests.get(gpio2_low_url)
                print(response.text)
                f.write(f"{timestamp}\n{response.text}\n")
                f.flush()
        except requests.RequestException as e:
            f.write(f"{timestamp}\nError: {e}\n")
            f.flush()
            print(f"{timestamp}\nError: {e}")
        time.sleep(1)  # Fetch every 1 second
