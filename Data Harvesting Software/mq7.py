import RPi.GPIO as GPIO
import time
import csv
from datetime import datetime
import os
import requests  # HTTP library for API interaction

# GPIO Setup
GPIO.setmode(GPIO.BCM)

# GPIO pins for CO detection
CO_PIN_1 = 17
CO_PIN_2 = 27

# Set GPIO pins as input with pull-down resistors
GPIO.setup(CO_PIN_1, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(CO_PIN_2, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# API Configuration
api_endpoint = "http://192.168.1.5:5000/mq7/data" 
API_TIMEOUT = 10  # Timeout for API requests (in seconds)

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
        csv_file = get_unique_filename("co_detection_data", ".csv")
        print(f"Initializing CSV file: {csv_file}")
        with open(csv_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "GPIO Pin", "CO Detected"])
        return csv_file
    except Exception as e:
        print(f"Error initializing CSV file: {e}")
        exit(1)

def log_to_csv(csv_file, timestamp, pin, co_detected):
    """Log CO detection data to a CSV file."""
    try:
        with open(csv_file, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, pin, co_detected])
    except Exception as e:
        print(f"Error writing to CSV: {e}")

def send_data_to_api(csv_file):
    """Send CO detection data to the API endpoint."""
    try:
        with open(csv_file, 'rb') as file:
            files = {'file': (csv_file, file)}
            response = requests.post(api_endpoint, files=files, timeout=API_TIMEOUT)
        
        if response.status_code == 200:
            print(f"Data sent successfully from {csv_file}.")
            return True
        else:
            print(f"Failed to send data from {csv_file}, Status Code: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("Request timed out while sending data.")
        return False
    except Exception as e:
        print(f"Error sending data to API: {e}")
        return False

def delete_csv_file(csv_file):
    """Delete the CSV file after it has been sent to the API."""
    try:
        os.remove(csv_file)
        print(f"Deleted CSV file: {csv_file}")
    except Exception as e:
        print(f"Error deleting file: {e}")

def monitor_co_detection():
    """Monitor CO detection on the specified GPIO pins."""
    try:
        csv_file = initialize_csv()  # Create a new CSV file for each batch
        data_count = 0

        while True:
            # Collect 25 data points
            for _ in range(25):
                for pin in [CO_PIN_1, CO_PIN_2]:
                    co_detected = GPIO.input(pin)
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Print status and log to CSV
                    if co_detected == GPIO.HIGH:
                        print(f"{timestamp} - CO detected on GPIO {pin}!")
                        log_to_csv(csv_file, timestamp, pin, "YES")
                    else:
                        print(f"{timestamp} - No CO detected on GPIO {pin}.")
                        log_to_csv(csv_file, timestamp, pin, "NO")

                    data_count += 1
                    time.sleep(1)  # Wait for 1 second before checking again

            # After collecting 25 data points, send the data to the API
            print(f"Collected {data_count} data points. Sending data to API...")
            if send_data_to_api(csv_file):
                delete_csv_file(csv_file)  # Delete the CSV file after sending data
            else:
                print(f"API request failed for file {csv_file}, continuing with the next cycle.")
            
            # Reset for the next batch
            data_count = 0
            # Wait a bit before starting the next cycle
            print("Waiting before starting the next cycle...")
            time.sleep(5)  # Adjust if you want more time between cycles
        
    except KeyboardInterrupt:
        print("Program interrupted by user.")
    finally:
        GPIO.cleanup()

# Start monitoring CO detection
if __name__ == "__main__":
    monitor_co_detection()
