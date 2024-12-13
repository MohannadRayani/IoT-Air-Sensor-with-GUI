import serial
import struct
import time
import csv
from datetime import datetime
import os
import requests  # HTTP library for API interaction

# Configure serial port and API
serial_port = '/dev/ttyUSB0'  # Adjust for your system
baud_rate = 9600
api_endpoint = "http://192.168.1.5:5000/pms/data"  # Replace with your API endpoint

# Timeout for API requests (in seconds)
API_TIMEOUT = 10


def initialize_serial():
    """Initialize the serial connection."""
    try:
        ser = serial.Serial(serial_port, baud_rate, timeout=2)
        print(f"Serial port {serial_port} opened successfully at {baud_rate} baud.")
        return ser
    except serial.SerialException as e:
        print(f"Failed to open serial port: {e}")
        exit(1)


def get_unique_filename(base_name, extension):
    """Generate a unique filename by appending numbers if the file exists."""
    try:
        counter = 0
        while True:
            file_name = f"{base_name}_{counter}{extension}" if counter > 0 else f"{base_name}{extension}"
            if not os.path.exists(file_name):
                return file_name
            counter += 1
    except Exception as e:
        print(f"Error generating unique filename: {e}")
        exit(1)


def initialize_csv():
    """Initialize or get the CSV file name."""
    try:
        csv_file = get_unique_filename("pms5003_data", ".csv")
        print(f"Initializing CSV file: {csv_file}")
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "PM1.0 (µg/m³)", "PM2.5 (µg/m³)", "PM10 (µg/m³)"])
        return csv_file
    except Exception as e:
        print(f"Error initializing CSV file: {e}")
        exit(1)


def log_to_csv(csv_file, timestamp, pm1_0, pm2_5, pm10):
    """Log PM data to a CSV file."""
    try:
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, pm1_0, pm2_5, pm10])
    except Exception as e:
        print(f"Error writing to CSV: {e}")


def send_file_to_api(csv_file):
    """Send the CSV file to the API endpoint with a timeout."""
    try:
        with open(csv_file, 'rb') as file:
            files = {'file': (csv_file, file)}
            response = requests.post(api_endpoint, files=files, timeout=API_TIMEOUT)
            if response.status_code == 200:
                print(f"File {csv_file} sent successfully.")
                return True
            else:
                print(f"Failed to send file {csv_file}. Status code: {response.status_code}")
                return False
    except requests.exceptions.Timeout:
        print(f"Request timed out while sending file {csv_file}.")
        return False
    except Exception as e:
        print(f"Error sending file {csv_file} to API: {e}")
        return False


def delete_all_csv_files():
    """Delete all CSV files in the current directory."""
    try:
        for file in os.listdir():
            if file.endswith(".csv"):
                os.remove(file)
                print(f"Deleted file: {file}")
    except Exception as e:
        print(f"Error deleting files: {e}")


def read_pms5003():
    """Read and process data from the PMS5003 sensor."""
    ser = initialize_serial()
    try:
        while True:
            csv_file = initialize_csv()  # Create a new CSV file for each batch
            row_count = 0
            while row_count < 25:  # Collect 25 rows of data per batch
                if ser.read(1) == b'\x42':  # Start of frame (0x42)
                    if ser.read(1) == b'\x4d':  # Frame header (0x4D)
                        try:
                            frame_length = struct.unpack(">H", ser.read(2))[0]
                            data = ser.read(frame_length - 2)
                            pm_values = struct.unpack(">HHHHHHHHHH", data[:20])
                            pm1_0, pm2_5, pm10 = pm_values[0], pm_values[1], pm_values[2]
                            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            log_to_csv(csv_file, timestamp, pm1_0, pm2_5, pm10)
                            row_count += 1
                            print(f"Row {row_count}: {timestamp}, PM1.0: {pm1_0}, PM2.5: {pm2_5}, PM10: {pm10}")
                            time.sleep(1)
                        except Exception as e:
                            print(f"Error processing frame: {e}")
                            continue
            
            # After collecting data, send to API and clean up files
            if send_file_to_api(csv_file):
                delete_all_csv_files()
            else:
                print(f"API request failed for file {csv_file}, continuing with the next batch.")
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        try:
            ser.close()
            print("Serial port closed.")
        except Exception as e:
            print(f"Error closing serial port: {e}")


# Start reading data
if __name__ == "__main__":
    read_pms5003()
