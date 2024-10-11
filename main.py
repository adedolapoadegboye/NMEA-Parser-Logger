import serial
import pynmea2
import pandas as pd
import os
import sys
from datetime import datetime
import threading
from time import time
import logging
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

class NMEAData:
    def __init__(self, sentence_type, data, parsed_sentences):
        self.baudrate = None
        self.port = None
        self.sentence_type = sentence_type
        self.data = data
        self.parsed_sentences = parsed_sentences  # List to store parsed NMEA data

    def __str__(self):
        # Pretty print the data based on sentence type
        if self.sentence_type == "GGA":
            self.parsed_sentences.append({
                "Type": "GGA",
                "Timestamp": self.data.timestamp.replace(tzinfo=None),
                "Latitude": f"{self.data.latitude} {self.data.lat_dir}",
                "Longitude": f"{self.data.longitude} {self.data.lon_dir}",
                "GPS Quality": self.data.gps_qual,
                "Satellites": self.data.num_sats,
                "Horizontal Dilution (HDOP)": self.data.horizontal_dil,
                "Altitude": f"{self.data.altitude} {self.data.altitude_units}",
                "Geoidal Separation": f"{self.data.geo_sep} {self.data.geo_sep_units}",
                "Age of Differential GPS Data": self.data.age_gps_data,
                "Differential Reference Station ID": self.data.ref_station_id
            })
            return (
                f"GGA - Fix Data:\n"
                f"  Timestamp: {self.data.timestamp}\n"
                f"  Latitude: {self.data.latitude} {self.data.lat_dir}\n"
                f"  Longitude: {self.data.longitude} {self.data.lon_dir}\n"
                f"  GPS Quality Indicator: {self.data.gps_qual}\n"
                f"  Number of Satellites in Use: {self.data.num_sats}\n"
                f"  Horizontal Dilution of Precision (HDOP): {self.data.horizontal_dil}\n"
                f"  Antenna Altitude (Above Mean Sea Level): {self.data.altitude} {self.data.altitude_units}\n"
                f"  Geoidal Separation: {self.data.geo_sep} {self.data.geo_sep_units}\n"
                f"  Age of Differential GPS Data: {self.data.age_gps_data}\n"
                f"  Differential Reference Station ID: {self.data.ref_station_id}\n"
            )

        elif self.sentence_type == "RMC":
            self.parsed_sentences.append({
                "Type": "RMC",
                "Timestamp": self.data.timestamp.replace(tzinfo=None),
                "Status": self.data.status,
                "Latitude": f"{self.data.latitude} {self.data.lat_dir}",
                "Longitude": f"{self.data.longitude} {self.data.lon_dir}",
                "Speed Over Ground": f"{self.data.spd_over_grnd} knots",
                "Course Over Ground": self.data.true_course,
                "Date": self.data.datestamp,
                "Magnetic Variation": f"{self.data.mag_variation} {self.data.mag_var_dir}",
                "Mode Indicator": self.data.mode_indicator,
                "Navigational Status": self.data.nav_status
            })
            return (
                f"RMC - Recommended Minimum:\n"
                f"  Timestamp: {self.data.timestamp}\n"
                f"  Status: {self.data.status}\n"
                f"  Latitude: {self.data.latitude} {self.data.lat_dir}\n"
                f"  Longitude: {self.data.longitude} {self.data.lon_dir}\n"
                f"  Speed over Ground: {self.data.spd_over_grnd} knots\n"
                f"  Course over Ground: {self.data.true_course}\n"
                f"  Date: {self.data.datestamp}\n"
                f"  Magnetic Variation: {self.data.mag_variation} {self.data.mag_var_dir}\n"
                f"  Mode Indicator: {self.data.mode_indicator}\n"
                f"  Navigational Status: {self.data.nav_status}\n"
            )

    # Define other NMEA sentence parsers here...

    def write_to_excel(self, port, baudrate, filename="nmea_data"):
        try:
            for entry in self.parsed_sentences:
                if 'Timestamp' in entry and isinstance(entry['Timestamp'], pd.Timestamp):
                    entry['Timestamp'] = entry['Timestamp'].tz_localize(None)

            df = pd.DataFrame(self.parsed_sentences)
            df.to_excel(f"logs/NMEA_{timestamp}/{filename}_{port}_{baudrate}_{timestamp}.xlsx", index=False)
            logging.info(f"Data written to logs/NMEA_{timestamp}/{filename}_{port}_{baudrate}_{timestamp}.xlsx")
        except Exception as e:
            logging.error(f"Error writing to Excel file: {e}")

def read_nmea_data(port, baudrate, timeout, duration, log_folder):
    parsed_sentences = []  # Initialize a list to store NMEA data
    start_time = time()  # Record the start time

    if not os.path.exists("logs"):
        os.makedirs("logs")

    if not os.path.exists(f"logs/NMEA_{timestamp}"):
        os.makedirs(f"logs/NMEA_{timestamp}")

    raw_nmea_log = open(f"logs/NMEA_{timestamp}/nmea_raw_log_{port}_{baudrate}_{timestamp}.txt", "a", encoding="utf-8")
    parsed_nmea_data = NMEAData(None, None, parsed_sentences)  # Placeholder NMEAData object

    try:
        ser = serial.Serial(
            port=port,
            baudrate=baudrate,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=timeout
        )
        logging.info(f"Connected to serial port {port} with baudrate {baudrate}.")
    except serial.SerialException as e:
        logging.error(f"Error opening serial port {port}: {e}")
        return  # Exit function if the port cannot be opened

    # Continuously read from the serial port
    while time() - start_time < duration:
        try:
            nmea_sentence = ser.readline().decode('ascii', errors='replace').strip()
            raw_nmea_log.write(nmea_sentence + "\n")

            if nmea_sentence.startswith('$P'):
                logging.info(f"Proprietary sentence ignored: {nmea_sentence}")
                continue

            if nmea_sentence.startswith('$G'):
                logging.info(f"Received Standard NMEA Message: {nmea_sentence}")
                try:
                    msg = pynmea2.parse(nmea_sentence)
                    nmea_data = NMEAData(msg.sentence_type, msg, parsed_sentences)
                    logging.info(nmea_data)
                except pynmea2.ParseError as e:
                    logging.info(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")
        except serial.SerialException as e:
            logging.info(f"Error reading from serial port: {e}")
            break

    logging.info(f"Standard and Proprietary logs written to {raw_nmea_log.name} for port {port} with baudrate {baudrate}")
    raw_nmea_log.close()
    parsed_nmea_data.write_to_excel(port, baudrate)

# GUI Start
def start_gui_app():
    root = tk.Tk()
    root.title("NMEA Parser and Logger")
    root.geometry("800x600")

    device_count_frame = ttk.Frame(root, padding="10")
    device_count_frame.grid(row=0, column=0, sticky="W")

    ttk.Label(device_count_frame, text="Number of Devices:").grid(row=0, column=0, sticky="W")
    num_devices = tk.IntVar(value=1)  # Default to 1 device
    num_devices_entry = ttk.Spinbox(device_count_frame, from_=1, to=10, textvariable=num_devices)
    num_devices_entry.grid(row=0, column=1, sticky="W")

    device_frame = ttk.Frame(root, padding="10")
    device_frame.grid(row=1, column=0, sticky="W")

    device_widgets = []

    # Function to check if all input fields are filled and valid
    def update_start_button_state():
        for widgets in device_widgets:
            if any(not widget.get().strip() for widget in widgets):
                start_button.config(state=tk.DISABLED)
                return
        start_button.config(state=tk.NORMAL)

    def update_device_fields():
        for widgets in device_widgets:
            for widget in widgets:
                widget.grid_forget()

        device_widgets.clear()

        for i in range(num_devices.get()):
            row_offset = i * 5

            ttk.Label(device_frame, text=f"Device {i + 1} Name:").grid(row=row_offset, column=0, sticky="W")
            device_name = ttk.Entry(device_frame)
            device_name.grid(row=row_offset, column=1, sticky="W")
            device_name.bind("<KeyRelease>", lambda event: update_start_button_state())

            ttk.Label(device_frame, text=f"Device {i + 1} COM Port:").grid(row=row_offset + 1, column=0, sticky="W")
            com_port = ttk.Entry(device_frame)
            com_port.grid(row=row_offset + 1, column=1, sticky="W")
            com_port.bind("<KeyRelease>", lambda event: update_start_button_state())

            ttk.Label(device_frame, text=f"Device {i + 1} Baud Rate:").grid(row=row_offset + 2, column=0, sticky="W")
            baud_rate = ttk.Entry(device_frame)
            baud_rate.grid(row=row_offset + 2, column=1, sticky="W")
            baud_rate.bind("<KeyRelease>", lambda event: update_start_button_state())

            ttk.Label(device_frame, text=f"Device {i + 1} Timeout:").grid(row=row_offset + 3, column=0, sticky="W")
            timeout = ttk.Entry(device_frame)
            timeout.grid(row=row_offset + 3, column=1, sticky="W")
            timeout.bind("<KeyRelease>", lambda event: update_start_button_state())

            ttk.Label(device_frame, text=f"Device {i + 1} Test Duration:").grid(row=row_offset + 4, column=0, sticky="W")
            test_duration = ttk.Entry(device_frame)
            test_duration.grid(row=row_offset + 4, column=1, sticky="W")
            test_duration.bind("<KeyRelease>", lambda event: update_start_button_state())

            device_widgets.append((device_name, com_port, baud_rate, timeout, test_duration))

    num_devices.trace_add('write', lambda *args: update_device_fields())

    update_device_fields()

    # Start Button (initially disabled)
    start_button = ttk.Button(root, text="Start", command=lambda: start_nmea_reading(device_widgets), state=tk.DISABLED)
    start_button.grid(row=2, column=0, sticky="W")

    root.mainloop()

def start_nmea_reading(device_widgets):
    # Extract user input for each device and validate inputs
    device_configs = []
    for widgets in device_widgets:
        device_name = widgets[0].get().strip()
        com_port = widgets[1].get().strip()
        baud_rate = widgets[2].get().strip()
        timeout = widgets[3].get().strip()
        test_duration = widgets[4].get().strip()

        # Basic validation to check if all fields are filled
        if not all([device_name, com_port, baud_rate, timeout, test_duration]):
            print(f"Error: All fields must be filled for each device.")
            return  # Exit if any field is missing

        try:
            baud_rate = int(baud_rate)
            timeout = int(timeout)
            test_duration = int(test_duration)
        except ValueError:
            print(f"Error: Baud rate, timeout, and test duration must be numbers.")
            return  # Exit if data type conversion fails

        # Store each device's configuration as a dictionary
        device_configs.append({
            "name": device_name,
            "port": com_port,
            "baudrate": baud_rate,
            "timeout": timeout,
            "duration": test_duration
        })

    # Start a thread for each device to read NMEA data
    threads = []
    for device_config in device_configs:
        thread = threading.Thread(target=read_nmea_data_thread, args=(device_config,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()


def read_nmea_data_thread(device_config):
    device_name = device_config["name"]
    port = device_config["port"]
    baudrate = device_config["baudrate"]
    timeout = device_config["timeout"]
    duration = device_config["duration"]

    print(
        f"Starting NMEA reading for {device_name} on port {port} with baudrate {baudrate}, timeout {timeout}, and duration {duration}")

    # Here, you should call the actual NMEA reading logic:
    read_nmea_data(port, baudrate, timeout, duration,
                   log_folder=f"logs/{device_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")


if __name__ == "__main__":
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
        log_folder = f"logs/NMEA_{timestamp}"

        # Create the log folder for each test run
        os.makedirs(log_folder, exist_ok=True)

        # Configure logging to both file and console
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(f"{log_folder}/console_output_{timestamp}.txt", 'a', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

        start_gui_app()  # Start the GUI

    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
