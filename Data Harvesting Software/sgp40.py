import time
import board
import busio
from adafruit_sgp40 import SGP40
import csv
from datetime import datetime
import os
import requests  # HTTP library for API interaction

# API configuration
api_endpoint = "http://192.168.1.5:5000/sgp40/data"  # Replace with your API endpoint
API_TIMEOUT = 5  # Timeout for API requests (in seconds)

# Create I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize SGP40 sensor
sgp = SGP40(i2c)

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
        csv_file = get_unique_filename("sgp40_data", ".csv")
        print(f"Initializing CSV file: {csv_file}")
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "VOC Index", "VOC Category"])
        return csv_file
    except Exception as e:
        print(f"Error initializing CSV file: {e}")
        exit(1)

def log_to_csv(csv_file, timestamp, voc_index, voc_category):
    """Log VOC data to a CSV file."""
    try:
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, voc_index, voc_category])
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

def interpret_voc_index(voc_index):
    """Interpret the VOC Index and return a category."""
    if voc_index < 200:
        return "Low VOCs"  # Clean air, low VOCs
    elif 200 <= voc_index < 500:
        return "Moderate VOCs"  # Slightly elevated VOC levels
    elif 500 <= voc_index < 1000:
        return "High VOCs"  # High VOC levels, potential air quality concerns
    else:
        return "Very High VOCs"  # Alarmingly high VOC levels, health concern

def read_sgp40():
    """Read and process data from the SGP40 sensor."""
    try:
        csv_file = initialize_csv()  # Create a new CSV file
        while True:
            voc_index = sgp.measure_index()  # Get VOC index from SGP40 sensor
            voc_category = interpret_voc_index(voc_index)  # Categorize the VOC index
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_to_csv(csv_file, timestamp, voc_index, voc_category)
            print(f"Timestamp: {timestamp}, VOC Index: {voc_index}, Category: {voc_category}")
            time.sleep(1)  # Collect data every 1 second

            # After collecting data, send to API and clean up files (Optional)
            # Send data to API every 60 seconds or after a batch
            if time.time() % 25 < 1:  # Send every 60 seconds (optional)
                if send_file_to_api(csv_file):
                    delete_all_csv_files()  # Delete files after successful upload
                else:
                    print(f"API request failed for file {csv_file}, continuing with the next batch.")
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        delete_all_csv_files()  # Clean up files on exit

# Start reading data
if __name__ == "__main__":
    read_sgp40()
