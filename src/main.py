# Standard Library Imports
import os
import sys
import threading
import logging
from datetime import datetime
from time import time

# Third-Party Library Imports
import serial
import pynmea2
import pandas as pd

# Local Application Imports
from nmea_data import NMEAData

# noinspection PyCompatibility
def setup_logging(log_folder, timestamp):
    """
    Sets up logging to output to both the console and a log file.

    Args:
        log_folder (str): Directory to save log files.
        timestamp (str): Timestamp to append to the log file name.
    """
    # Ensure the log directory exists
    os.makedirs(log_folder, exist_ok=True)

    # Define the log file path
    log_file = os.path.join(log_folder, f"console_output_{timestamp}.txt")

    # Configure logging with both file and console handlers
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info(f"Console logging setup complete. Logs are being saved to {log_file}")

# noinspection PyCompatibility
def read_nmea_data(port, baudrate, timeout, duration, log_folder, timestamp, reference_point=None, stop_event=None):
    """
    Reads live NMEA data from a serial port and processes it.

    Args:
        port (str): Serial port to read from (e.g., "COM3").
        baudrate (int): Baud rate for serial communication.
        timeout (float): Timeout for serial port reads (in seconds).
        duration (float): Duration to read data (in seconds).
        log_folder (str): Directory to save log files.
        timestamp (str): Timestamp to append to file names.
        reference_point (tuple, optional): Custom reference point for CEP calculation.
        stop_event (threading.Event, optional): Event to signal the function to stop.
    """
    parsed_sentences = []
    start_time = time()
    nmea_data = NMEAData(None, None, parsed_sentences)

    # Ensure log folder exists
    os.makedirs(log_folder, exist_ok=True)

    safe_port = port.replace("/", "_")

    # Open raw NMEA log file
    raw_nmea_log_path = os.path.join(log_folder, f"nmea_raw_log_mode_1_{safe_port}_{baudrate}_{timestamp}.txt")
    try:
        raw_nmea_log = open(raw_nmea_log_path, "a", encoding="utf-8")
    except Exception as e:
        logging.error(f"Error opening log file {raw_nmea_log_path}: {e}")
        return

    try:
        # Attempt to configure and open the serial port
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
            return  # Exit function if serial port cannot be opened

        # Continuously read from serial port until duration expires or stop_event is set
        while time() - start_time < duration:
            if stop_event and stop_event.is_set():  # Check if stop_event is set
                logging.info(f"Stop signal received. Ending data collection on {port}.")
                break  # Exit the loop gracefully

            try:
                nmea_sentence = ser.readline().decode('ascii', errors='replace').strip()

                try:
                    raw_nmea_log.write(nmea_sentence + "\n")
                except Exception as e:
                    logging.error(f"Error writing NMEA sentence to log file: {e}")

                # Handle proprietary NMEA sentences
                if nmea_sentence.startswith('$PQTM'):
                    logging.info(f"Proprietary NMEA Message: {nmea_sentence}")
                    try:
                        msg = pynmea2.parse(nmea_sentence)
                        if not hasattr(msg, 'sentence_type') or not msg.sentence_type:
                            raise pynmea2.ParseError("Invalid or missing sentence_type in parsed NMEA sentence", msg)

                        nmea_data.sentence_type = msg.sentence_type
                        nmea_data.data = msg
                        nmea_data.add_sentence_data()
                        nmea_data.add_coordinates()
                        logging.info(nmea_data)
                    except pynmea2.ParseError as e:
                        logging.warning(f"Failed to parse proprietary NMEA sentence: {nmea_sentence} - {e}")
                    continue

                # Handle standard NMEA sentences
                if nmea_sentence.startswith('$G'):
                    logging.info(f"Standard NMEA Message: {nmea_sentence}")
                    try:
                        msg = pynmea2.parse(nmea_sentence)
                        if not hasattr(msg, 'sentence_type') or not msg.sentence_type:
                            raise pynmea2.ParseError("Invalid or missing sentence_type in parsed NMEA sentence", msg)

                        nmea_data.sentence_type = msg.sentence_type
                        nmea_data.data = msg
                        nmea_data.add_sentence_data()
                        nmea_data.add_coordinates()
                        logging.info(nmea_data)
                    except pynmea2.ParseError as e:
                        logging.warning(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")
                else:
                    logging.info(f"Unknown Message: {nmea_sentence}")

            except serial.SerialException as e:
                logging.error(f"Error reading from serial port: {e}")
                break

    except Exception as e:
        logging.error(f"Unexpected error during serial read: {e}")

    finally:
        # Ensure the log file is closed properly
        raw_nmea_log.close()
        logging.info(f"Log file {raw_nmea_log_path} closed.")

    # Calculate CEP and log the results
    cep_value = nmea_data.calculate_cep(reference_point)
    if cep_value:
        logging.info(f"Mode 1: CEP statistics for port {port}:")
        logging.info(f"CEP50: {cep_value['CEP50']:.2f} meters")
        logging.info(f"CEP68: {cep_value['CEP68']:.2f} meters")
        logging.info(f"CEP90: {cep_value['CEP90']:.2f} meters")
        logging.info(f"CEP95: {cep_value['CEP95']:.2f} meters")
        logging.info(f"CEP99: {cep_value['CEP99']:.2f} meters")
    else:
        logging.info(f"No coordinates available for CEP calculation for port {port}.")

    # Save parsed data to Excel
    nmea_data.write_to_excel_mode_1(port, baudrate, timestamp, cep_value)

# noinspection PyCompatibility
def parse_nmea_from_log(file_path):
    """
    Reads a log file in .txt, .log, .nmea, .csv, or Excel format and parses valid NMEA sentences.

    Args:
        file_path (str): Path to the log file to be parsed.

    Returns:
        tuple: A list of parsed sentences and an NMEAData object.
    """
    parsed_sentences = []
    nmea_data = NMEAData(None, None, parsed_sentences)
    logging.info(f"Processing log file: {file_path}")

    try:
        # Handle different file types based on the file extension
        if file_path.endswith(('.txt', '.log', '.nmea')):
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            logging.info(f"Total lines read from file: {len(lines)}")

        elif file_path.endswith('.csv'):
            df = pd.read_csv(file_path, header=None)
            lines = df[0].astype(str).tolist()
            logging.info(f"Total lines read from CSV: {len(df)}")

        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path, header=None)
            lines = df[0].astype(str).tolist()
            logging.info(f"Total lines read from Excel: {len(df)}")

        else:
            logging.error(f"Unsupported file type: {file_path}")
            raise ValueError("Unsupported file type. Supported formats: .txt, .log, .nmea, .csv, .xlsx")

        # Process each line in the file
        for nmea_sentence in lines:
            nmea_sentence = nmea_sentence.strip()
            logging.debug(f"Processing sentence: {nmea_sentence}")

            try:
                if nmea_sentence.startswith('$PQTM'):
                    logging.info(f"Proprietary NMEA Message: {nmea_sentence}")
                    msg = pynmea2.parse(nmea_sentence)

                    if not hasattr(msg, 'sentence_type') or not msg.sentence_type:
                        raise pynmea2.ParseError("Invalid or missing sentence_type in parsed NMEA sentence", msg)

                    nmea_data.sentence_type = msg.sentence_type
                    nmea_data.data = msg
                    nmea_data.add_sentence_data()
                    nmea_data.add_coordinates()
                    logging.info(nmea_data)

                elif nmea_sentence.startswith('$G'):
                    logging.info(f"Standard NMEA Message: {nmea_sentence}")
                    msg = pynmea2.parse(nmea_sentence)

                    if not hasattr(msg, 'sentence_type') or not msg.sentence_type:
                        raise pynmea2.ParseError("Invalid or missing sentence_type in parsed NMEA sentence", msg)

                    nmea_data.sentence_type = msg.sentence_type
                    nmea_data.data = msg
                    nmea_data.add_sentence_data()
                    nmea_data.add_coordinates()
                    logging.info(nmea_data)

                else:
                    logging.info(f"Received Unknown Message: {nmea_sentence}")

            except pynmea2.ParseError as e:
                logging.warning(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")

    except Exception as e:
        logging.error(f"Failed to read or process file: {file_path}. Error: {e}")

    logging.info(f"Total parsed sentences: {len(parsed_sentences)}")
    return parsed_sentences, nmea_data
# noinspection PyCompatibility
def process_nmea_log(file_path, reference_point=None):
    """
    Process pre-collected NMEA log file and calculate CEP.

    Args:
        file_path (str): Path to the NMEA log file.
        reference_point (tuple, optional): Custom reference point (latitude, longitude). Defaults to None.
    """
    logging.info(f"Starting log processing for file: {file_path}")

    # Check if the file exists
    if not os.path.exists(file_path):
        logging.error(f"File does not exist: {file_path}")
        return

    # Process the file to get parsed sentences
    try:
        parsed_sentences, nmea_data = parse_nmea_from_log(file_path)
    except Exception as e:
        logging.error(f"Error during parsing NMEA log file: {file_path}. Exception: {e}")
        return

    if not parsed_sentences:
        logging.error(f"No valid NMEA sentences found in log file: {file_path}")
        return

    logging.info(f"Total parsed sentences: {len(parsed_sentences)}")

    # Determine or calculate the reference point
    if reference_point is None:
        try:
            logging.info("Calculating the mean point from log data for CEP Analysis.")
            reference_point = nmea_data.calculate_mean_point()
        except Exception as e:
            logging.error(f"Error calculating mean point: {e}")
            return
    else:
        logging.info(f"Using provided reference point: {reference_point}")

    # Calculate CEP values
    try:
        cep_value = nmea_data.calculate_cep(reference_point)
        if cep_value is not None:
            logging.info(f"Mode 2: CEP statistics for logfile {file_path}:")
            logging.info(f"CEP50: {cep_value['CEP50']:.2f} meters")
            logging.info(f"CEP68: {cep_value['CEP68']:.2f} meters")
            logging.info(f"CEP90: {cep_value['CEP90']:.2f} meters")
            logging.info(f"CEP95: {cep_value['CEP95']:.2f} meters")
            logging.info(f"CEP99: {cep_value['CEP99']:.2f} meters")
        else:
            logging.info(f"No coordinates available for CEP calculation for log {file_path}.")
    except Exception as e:
        logging.error(f"Error calculating CEP values: {e}")
        return

    logging.info(f"Finished log processing for file: {file_path}")

    # Write results to an Excel file
    try:
        nmea_data.write_to_excel_mode_2(timestamp, cep_value)
    except Exception as e:
        logging.error(f"Error writing to Excel file: {e}")

if __name__ == "__main__":
    try:
        # Setup timestamp and log folder
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
        log_folder = f"logs/NMEA_{timestamp}"
        setup_logging(log_folder, timestamp)

        active_program = True

        while active_program:
            # Prompt the user to choose a data input mode
            while True:
                mode = input("Choose data input mode: 1 = Live Serial Data, 2 = Load log file\n").strip()
                if mode in ['1', '2']:
                    break
                else:
                    logging.error("Invalid input. Please enter '1' or '2'.")

            if mode == '1':
                try:
                    # Gather device configurations from the user
                    while True:
                        try:
                            num_devices = int(input("How many devices would you like to configure? (e.g., 1, 2, 3)\n").strip())
                            if num_devices > 0:
                                break
                            else:
                                logging.error("Number of devices must be greater than 0.")
                        except ValueError:
                            logging.error("Invalid input. Please enter a valid integer for the number of devices.")

                    devices = {}
                    for i in range(1, num_devices + 1):
                        while True:
                            try:
                                print(f"Configure device {i}:")
                                port = input(f"Enter the port for device {i} (e.g., 'COM9' or '/dev/ttyUSB0'): \n").strip()
                                baudrate = int(input(f"Enter the baudrate for device {i} (e.g., 115200): \n").strip())
                                timeout = float(input(f"Enter the timeout for device {i} (in seconds, e.g., 1.0): \n").strip())
                                duration = float(input(f"Enter the test duration for device {i} (in seconds, e.g., 60.0): \n").strip())

                                # Store the device configuration
                                devices[f"device {i}"] = {
                                    "port": port,
                                    "baudrate": baudrate,
                                    "timeout": timeout,
                                    "duration": duration
                                }
                                break  # Break the loop if all inputs are valid
                            except ValueError:
                                logging.error("Invalid input. Please enter the values as guided (e.g., integers for baudrate and floats for timeout and duration).")

                    # Get reference point from the user
                    while True:
                        use_custom_reference = input("Do you want to provide a custom reference point for CEP calculations? (y/n, e.g., 'y' or 'n'):\n").strip().lower()
                        if use_custom_reference in ['y', 'n']:
                            break
                        else:
                            logging.error("Invalid input. Please enter 'y' or 'n'.")

                    if use_custom_reference == 'y':
                        while True:
                            try:
                                ref_lat = float(input("Enter reference latitude (e.g., 37.7749): \n").strip())
                                ref_lon = float(input("Enter reference longitude (e.g., -122.4194): \n").strip())
                                reference_point = (ref_lat, ref_lon)
                                break
                            except ValueError:
                                logging.error("Invalid input. Please enter valid float values for latitude and longitude.")
                    else:
                        reference_point = None

                    threads = []

                    # Start a thread for each configured device
                    for device_name, config in devices.items():
                        try:
                            thread = threading.Thread(
                                target=read_nmea_data,
                                args=(config["port"], config["baudrate"], config["timeout"], config["duration"],
                                      log_folder, timestamp, reference_point)
                            )
                            threads.append(thread)
                            thread.start()
                        except Exception as e:
                            logging.error(f"Failed to start thread for {device_name}: {e}")

                    # Wait for all threads to finish
                    for thread in threads:
                        try:
                            thread.join()
                        except Exception as e:
                            logging.error(f"Error while waiting for thread to finish: {e}")

                except Exception as e:
                    logging.error(f"An unexpected error occurred in mode 1: {e}")

            elif mode == '2':
                try:
                    while True:
                        file_path = input("Enter the path to the log file (e.g., 'C:/path/to/file.txt'):\n").strip('"')
                        if os.path.exists(file_path):
                            break
                        else:
                            logging.error("The file path provided does not exist. Please enter a valid path.")

                    while True:
                        use_custom_reference = input("Do you want to provide a true reference point for CEP calculations? (y/n):\n").strip().lower()
                        if use_custom_reference in ['y', 'n']:
                            break
                        else:
                            logging.error("Invalid input. Please enter 'y' or 'n'.")

                    if use_custom_reference == 'y':
                        while True:
                            try:
                                ref_lat = float(input("Enter reference latitude (e.g., 37.7749123): \n").strip())
                                ref_lon = float(input("Enter reference longitude (e.g., -122.4194123): \n").strip())
                                reference_point = (ref_lat, ref_lon)
                                break
                            except ValueError:
                                logging.error("Invalid input. Please enter valid float values for latitude and longitude.")
                    else:
                        reference_point = None

                    # Process the log file and calculate CEP
                    process_nmea_log(file_path, reference_point)

                except Exception as e:
                    logging.error(f"An error occurred while processing the log file in mode 2: {e}")

            # Check if the user wants to continue
            active_program = input("Do you want to quit the program? (y/n, e.g., 'y' to quit, 'n' to continue): \n").strip().lower() != 'y'

    except Exception as e:
        logging.error(f"Critical error in main execution: {e}")
