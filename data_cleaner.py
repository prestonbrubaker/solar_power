import csv
import os
from datetime import datetime

# File paths
INPUT_FILE = "/home/preston/Desktop/solar_power/battery_passive_log.csv"
OUTPUT_FILE = "/home/preston/Desktop/solar_power/battery_passive_log_cleaned.csv"
LOG_FILE = "/home/preston/Desktop/solar_power/cleaning_log.txt"

# Constraints
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
MIN_TIMESTAMP = datetime(2025, 6, 16)  # 2025-06-16 00:00:00
MAX_TIMESTAMP = datetime(2025, 6, 18, 23, 59, 59, 999999)  # 2025-06-18 23:59:59.999
MIN_VOLTAGE = 0.0
MAX_VOLTAGE = 2.048
MAX_TIME_GAP_MS = 3600000  # 1 hour in milliseconds
EXPECTED_HEADERS = ["timestamp", "voltage_a0", "voltage_a1"]

def log_message(message):
    """Append message to log file and print to console."""
    with open(LOG_FILE, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: {message}\n")
    print(message)

# Initialize log
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)
log_message("Starting ultimate CSV cleaning process")

def is_valid_timestamp(timestamp_str):
    """Check if timestamp is valid ISO 8601 within date range."""
    try:
        dt = datetime.strptime(timestamp_str, TIMESTAMP_FORMAT)
        return MIN_TIMESTAMP <= dt <= MAX_TIMESTAMP
    except ValueError:
        return False

def is_valid_voltage(value):
    """Check if voltage is numeric and within range."""
    try:
        voltage = float(value)
        return MIN_VOLTAGE <= voltage <= MAX_VOLTAGE
    except ValueError:
        return False

def timestamp_to_ms(timestamp_str):
    """Convert ISO 8601 timestamp to milliseconds."""
    dt = datetime.strptime(timestamp_str, TIMESTAMP_FORMAT)
    return int(dt.timestamp() * 1000)

# Read and validate CSV
valid_rows = []
invalid_rows = 0
try:
    with open(INPUT_FILE, "r") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        if headers != EXPECTED_HEADERS:
            log_message(f"Invalid headers: {headers}, expected: {EXPECTED_HEADERS}")
            raise ValueError("Invalid CSV headers")

        for row_num, row in enumerate(reader, start=2):
            try:
                if len(row) != 3:
                    log_message(f"Row {row_num}: Invalid column count: {row}")
                    invalid_rows += 1
                    continue

                timestamp, voltage_a0, voltage_a1 = [x.strip() for x in row]

                # Validate timestamp
                if not is_valid_timestamp(timestamp):
                    log_message(f"Row {row_num}: Invalid timestamp: {timestamp}")
                    invalid_rows += 1
                    continue

                # Check for HTTP errors
                if "Error: HTTPConnectionPool" in voltage_a0 or "Error: HTTPConnectionPool" in voltage_a1:
                    log_message(f"Row {row_num}: HTTP error detected: {row}")
                    invalid_rows += 1
                    continue

                # Validate voltages
                if not is_valid_voltage(voltage_a0) or not is_valid_voltage(voltage_a1):
                    log_message(f"Row {row_num}: Invalid voltages: {voltage_a0}, {voltage_a1}")
                    invalid_rows += 1
                    continue

                valid_rows.append([timestamp, float(voltage_a0), float(voltage_a1), timestamp_to_ms(timestamp)])
            except Exception as e:
                log_message(f"Row {row_num}: Unexpected error: {row}, {str(e)}")
                invalid_rows += 1
                continue
except FileNotFoundError:
    log_message(f"Input file not found: {INPUT_FILE}")
    raise
except Exception as e:
    log_message(f"Fatal error reading CSV: {str(e)}")
    raise

# Sort by timestamp (just in case)
valid_rows.sort(key=lambda x: x[3])

# Filter out large time gaps
filtered_rows = []
if valid_rows:
    filtered_rows.append(valid_rows[0][:3])  # Keep first row
    for i in range(1, len(valid_rows)):
        prev_ms = valid_rows[i-1][3]
        curr_ms = valid_rows[i][3]
        gap_ms = curr_ms - prev_ms
        if gap_ms <= MAX_TIME_GAP_MS:
            filtered_rows.append(valid_rows[i][:3])
        else:
            log_message(f"Removed row due to time gap {gap_ms/1000:.2f}s: {valid_rows[i-1][:3]} -> {valid_rows[i][:3]}")
            invalid_rows += 1

# Write cleaned CSV
try:
    with open(OUTPUT_FILE, "w", newline='') as f:
        writer = csv.writer(f)
        writer.writerow(EXPECTED_HEADERS)
        for row in filtered_rows:
            # Format voltages to 4 decimal places to match example
            writer.writerow([row[0], f"{row[1]:.4f}", f"{row[2]:.4f}"])
except Exception as e:
    log_message(f"Error writing output CSV: {str(e)}")
    raise

# Log summary
log_message(f"Cleaning complete: {len(filtered_rows)} valid rows, {invalid_rows} invalid or removed rows")
log_message(f"Cleaned CSV saved to {OUTPUT_FILE}")
