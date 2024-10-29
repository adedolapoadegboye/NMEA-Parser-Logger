import serial
import pynmea2
import os
import sys
from datetime import datetime
import threading
from time import time
import logging
import pandas as pd
from nmea_data import NMEAData


def setup_logging(log_folder, timestamp):
    """Setup logging to both console and file"""
    os.makedirs(log_folder, exist_ok=True)

    log_file = f"{log_folder}/console_output_{timestamp}.txt"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.FileHandler(log_file, 'a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    logging.info(f"Logging setup complete. Logs are being saved to {log_file}")


def read_nmea_data(port, baudrate, timeout, duration, log_folder, timestamp, reference_point=None):
    """Reads live NMEA data from serial port and processes it."""
    parsed_sentences = []  # Initialize a list to store NMEA data
    start_time = time()  # Record the start time
    nmea_data = NMEAData(None, None, parsed_sentences)  # Create a new instance for each thread

    # Ensure the log directories exist
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    raw_nmea_log = open(f"{log_folder}/nmea_raw_log_mode_1_{port}_{baudrate}_{timestamp}.txt", "a", encoding="utf-8")

    try:
        # Configure the serial port
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
                # Read a line of NMEA data from the serial port
                nmea_sentence = ser.readline().decode('ascii', errors='replace').strip()

                try:
                    raw_nmea_log.write(nmea_sentence + "\n")
                except Exception as e:
                    logging.error(f"Error writing NMEA sentence to log file: {e}")

                # Skip proprietary sentences like $PAIR or $PQTM
                if nmea_sentence.startswith('$P'):
                    logging.info(f"Proprietary sentence ignored: {nmea_sentence}")
                    continue

                if nmea_sentence.startswith('$G'):
                    logging.info(f"Received Standard NMEA Message: {nmea_sentence}")

                    # Parse the NMEA sentence using pynmea2
                    try:
                        msg = pynmea2.parse(nmea_sentence)

                        # Create a NMEAData object and add coordinates
                        nmea_data.sentence_type = msg.sentence_type
                        nmea_data.data = msg
                        nmea_data.add_sentence_data()
                        nmea_data.add_coordinates()  # Store coordinates from GLL or GGA sentences
                        logging.info(nmea_data)

                    except pynmea2.ParseError as e:
                        logging.info(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")

                else:
                    logging.info(f"Received Unknown Message: {nmea_sentence}")

            except serial.SerialException as e:
                logging.info(f"Error reading from serial port: {e}")
                break

    except serial.SerialException as e:
        logging.info(f"Error opening serial port: {e}")

    # After reading all raw sentences, write to the log file created
    logging.info(
        f"Standard and Proprietary logs written to {raw_nmea_log.name} for port {port} with baudrate {baudrate}")
    raw_nmea_log.close()

    # Calculate CEP for this thread's data
    cep_value = nmea_data.calculate_cep(reference_point)
    if cep_value is not None:
        logging.info(f"Mode 1: CEP statistics for port {port}:")
        logging.info(f"CEP50: {cep_value['CEP50']:.2f} meters")
        logging.info(f"CEP68: {cep_value['CEP68']:.2f} meters")
        logging.info(f"CEP90: {cep_value['CEP90']:.2f} meters")
        logging.info(f"CEP95: {cep_value['CEP95']:.2f} meters")
        logging.info(f"CEP99: {cep_value['CEP99']:.2f} meters")
    else:
        logging.info(f"No coordinates available for CEP calculation for port {port}.")

    nmea_data.write_to_excel_mode_1(port, baudrate, timestamp, cep_value)

def parse_nmea_from_log(file_path):
    """Reads a log file in .txt, .log, .nmea, .csv, or Excel format and parses valid NMEA sentences"""
    parsed_sentences = []
    nmea_data = NMEAData(None, None, parsed_sentences)  # Create a new instance for each thread
    logging.info(f"Processing log file: {file_path}")

    # Handle plain text files (.txt, .log, .nmea)
    if file_path.endswith(('.txt', '.log', '.nmea')):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            logging.info(f"Total lines read from file: {len(lines)}")
        except Exception as e:
            logging.error(f"Failed to read file: {file_path}. Error: {e}")
            return []

        for nmea_sentence in lines:
            nmea_sentence = nmea_sentence.strip()
            logging.info(f"Processing sentence: {nmea_sentence}")

            # Skip proprietary sentences like $PAIR or $PQTM
            if nmea_sentence.startswith('$P'):
                logging.info(f"Proprietary sentence ignored: {nmea_sentence}")
                continue

            if nmea_sentence.startswith('$G'):
                logging.info(f"Received Standard NMEA Message: {nmea_sentence}")

                # Parse the NMEA sentence using pynmea2
                try:
                    msg = pynmea2.parse(nmea_sentence)

                    # Create a NMEAData object and add coordinates
                    nmea_data.sentence_type = msg.sentence_type
                    nmea_data.data = msg
                    nmea_data.add_sentence_data()
                    nmea_data.add_coordinates()  # Store coordinates from GLL or GGA sentences
                    logging.info(nmea_data)

                except pynmea2.ParseError as e:
                    logging.info(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")

            else:
                logging.info(f"Received Unknown Message: {nmea_sentence}")

    # Handle .csv files
    elif file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path, header=None)
            logging.info(f"Total lines read from CSV: {len(df)}")
        except Exception as e:
            logging.error(f"Failed to read CSV file: {file_path}. Error: {e}")
            return []

        for _, row in df.iterrows():
            nmea_sentence = str(row[0]).strip()
            logging.debug(f"Processing sentence: {nmea_sentence}")
            # Skip proprietary sentences like $PAIR or $PQTM
            if nmea_sentence.startswith('$P'):
                logging.info(f"Proprietary sentence ignored: {nmea_sentence}")
                continue

            if nmea_sentence.startswith('$G'):
                logging.info(f"Received Standard NMEA Message: {nmea_sentence}")

                # Parse the NMEA sentence using pynmea2
                try:
                    msg = pynmea2.parse(nmea_sentence)

                    # Create a NMEAData object and add coordinates
                    nmea_data.sentence_type = msg.sentence_type
                    nmea_data.data = msg
                    nmea_data.add_sentence_data()
                    nmea_data.add_coordinates()  # Store coordinates from GLL or GGA sentences
                    logging.info(nmea_data)

                except pynmea2.ParseError as e:
                    logging.info(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")

            else:
                logging.info(f"Received Unknown Message: {nmea_sentence}")

    # Handle .xlsx files
    elif file_path.endswith('.xlsx'):
        try:
            df = pd.read_excel(file_path, header=None)
            logging.info(f"Total lines read from Excel: {len(df)}")
        except Exception as e:
            logging.error(f"Failed to read Excel file: {file_path}. Error: {e}")
            return []

        for _, row in df.iterrows():
            nmea_sentence = str(row[0]).strip()
            logging.debug(f"Processing sentence: {nmea_sentence}")
            # Skip proprietary sentences like $PAIR or $PQTM
            if nmea_sentence.startswith('$P'):
                logging.info(f"Proprietary sentence ignored: {nmea_sentence}")
                continue

            if nmea_sentence.startswith('$G'):
                logging.info(f"Received Standard NMEA Message: {nmea_sentence}")

                # Parse the NMEA sentence using pynmea2
                try:
                    msg = pynmea2.parse(nmea_sentence)

                    # Create a NMEAData object and add coordinates
                    nmea_data.sentence_type = msg.sentence_type
                    nmea_data.data = msg
                    nmea_data.add_sentence_data()
                    nmea_data.add_coordinates()  # Store coordinates from GLL or GGA sentences
                    logging.info(nmea_data)

                except pynmea2.ParseError as e:
                    logging.info(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")

            else:
                logging.info(f"Received Unknown Message: {nmea_sentence}")

    else:
        logging.error(f"Unsupported file type: {file_path}")
        raise ValueError("Unsupported file type. Supported formats: .txt, .log, .nmea, .csv, .xlsx")

    logging.info(f"Total parsed sentences: {len(parsed_sentences)}")
    return parsed_sentences, nmea_data


def process_nmea_log(file_path, reference_point=None):
    """Process pre-collected NMEA log file and calculate CEP"""
    logging.info(f"Starting log processing for file: {file_path}")

    # Check if the file exists (for debugging)
    if not os.path.exists(file_path):
        logging.error(f"File does not exist: {file_path}")
        return

    # Process the file to get parsed sentences
    parsed_sentences, nmea_data = parse_nmea_from_log(file_path)

    if not parsed_sentences:
        logging.error(f"No valid NMEA sentences found in log file: {file_path}")
        return

    logging.info(f"Total parsed sentences: {len(parsed_sentences)}")

    # Ask for custom reference point if not provided
    if reference_point is None:
        logging.info("Calculating the mean point from log data for CEP Analysis.")
        reference_point = nmea_data.calculate_mean_point()
    else:
        logging.info(f"Using provided reference point: {reference_point}")

    # Calculate CEP for this thread's data
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

    logging.info(f"Finished log processing for file: {file_path}")

    nmea_data.write_to_excel_mode_2(timestamp, cep_value)


if __name__ == "__main__":
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
    log_folder = f"logs/NMEA_{timestamp}"

    setup_logging(log_folder, timestamp)

    activeProgram = True

    while activeProgram:
        mode = input("Choose data input mode: 1 = Live Serial Data, 2 = Log file\n")
        if mode == '1':
            try:
                # Prompt the user for the port, baudrate, timeout, and duration
                num_devices = int(input("How many devices would you like to configure? (e.g., 1, 2, 3)\n"))

                devices = {}
                for i in range(1, num_devices + 1):
                    print(f"Configure device {i}:")
                    port = input(f"Enter the port for device {i} (e.g., COM9): \n")
                    baudrate = int(input(f"Enter the baudrate for device {i} (e.g., 115200): \n"))
                    timeout = float(input(f"Enter the timeout for device {i} (in seconds, e.g., 1): \n"))
                    duration = float(input(f"Enter the test duration for device {i} (in seconds): \n"))
                    devices[f"device {i}"] = {"port": port, "baudrate": baudrate, "timeout": timeout, "duration": duration}

                # Prompt the user for a reference point or use the mean point
                use_custom_reference = input("Do you want to provide a custom reference point for CEP calculations? (y/n): \n")

                if use_custom_reference.lower() == 'y':
                    ref_lat = float(input("Enter reference latitude: \n"))
                    ref_lon = float(input("Enter reference longitude: \n"))
                    reference_point = (ref_lat, ref_lon)
                else:
                    reference_point = None

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

                threads = []

                for device, config in devices.items():
                    try:
                        # Pass reference_point and timestamp to each thread
                        thread = threading.Thread(target=read_nmea_data, args=(
                            config["port"], config["baudrate"], config["timeout"], config["duration"], log_folder,
                            timestamp, reference_point))
                        threads.append(thread)
                        thread.start()
                    except Exception as e:
                        logging.error(f"Failed to start thread for {device}: {e}")

                for thread in threads:
                    try:
                        thread.join()
                    except Exception as e:
                        logging.error(f"Error while waiting for thread to finish: {e}")

            except Exception as e:
                logging.error(f"An unexpected error occurred: {e}")
        elif mode == '2':
            file_path = input("Enter the path to the log file (.txt, .log, .nmea, .csv, or .xlsx): \n").strip('"')
            reference_point = None

            # Prompt the user for a reference point or use the mean point
            use_custom_reference = input("Do you want to provide a custom reference point for CEP calculations? (y/n): \n")

            if use_custom_reference.lower() == 'y':
                ref_lat = float(input("Enter reference latitude: \n"))
                ref_lon = float(input("Enter reference longitude: \n"))
                reference_point = (ref_lat, ref_lon)
            else:
                reference_point = None

            # Process the log file and calculate CEP
            process_nmea_log(file_path, reference_point)
        else:
            print("Invalid input. Please enter 1 or 2.")

        activeProgram = input("Do you want to quit the program? (y/n): \n")
        if activeProgram.lower() != 'n':
            break