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


# main.py

def read_nmea_data(port, baudrate, timeout, duration, log_folder, timestamp, reference_point=None):
    parsed_sentences = []  # Initialize a list to store NMEA data
    start_time = time()  # Record the start time
    nmea_data = NMEAData(None, None, parsed_sentences)  # Create a new instance for each thread

    # Ensure the log directories exist
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)

    raw_nmea_log = open(f"{log_folder}/nmea_raw_log_{port}_{baudrate}_{timestamp}.txt", "a", encoding="utf-8")

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
        logging.info(f"CEP statistics for port {port}:")
        logging.info(f"CEP50: {cep_value['CEP50']:.2f} meters")
        logging.info(f"CEP68: {cep_value['CEP68']:.2f} meters")
        logging.info(f"CEP90: {cep_value['CEP90']:.2f} meters")
        logging.info(f"CEP95: {cep_value['CEP95']:.2f} meters")
        logging.info(f"CEP99: {cep_value['CEP99']:.2f} meters")
    else:
        logging.info(f"No coordinates available for CEP calculation for port {port}.")

    nmea_data.write_to_excel(port, baudrate, timestamp, cep_value)


def parse_nmea_from_log(file_path):
    """Reads a log file in .txt, .log, .nmea, .csv or Excel format and parses valid NMEA sentences"""
    parsed_sentences = []

    # Handle plain text files (.txt, .log, .nmea)
    if file_path.endswith(('.txt', '.log', '.nmea')):
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        for nmea_sentence in lines:
            nmea_sentence = nmea_sentence.strip()
            if nmea_sentence.startswith('$G'):  # Check if it's a standard NMEA sentence
                try:
                    msg = pynmea2.parse(nmea_sentence)
                    parsed_sentences.append(msg)
                except pynmea2.ParseError:
                    logging.error(f"Parse error for sentence: {nmea_sentence}")
                    continue
            else:
                logging.info(f"Ignored non-standard sentence: {nmea_sentence}")

    # Handle .csv files
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path, header=None)  # Assuming no headers
        for _, row in df.iterrows():
            nmea_sentence = str(row[0]).strip()
            if nmea_sentence.startswith('$G'):
                try:
                    msg = pynmea2.parse(nmea_sentence)
                    parsed_sentences.append(msg)
                except pynmea2.ParseError:
                    logging.error(f"Parse error for sentence: {nmea_sentence}")
                    continue

    # Handle .xlsx files
    elif file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path, header=None)
        for _, row in df.iterrows():
            nmea_sentence = str(row[0]).strip()
            if nmea_sentence.startswith('$G'):
                try:
                    msg = pynmea2.parse(nmea_sentence)
                    parsed_sentences.append(msg)
                except pynmea2.ParseError:
                    logging.error(f"Parse error for sentence: {nmea_sentence}")
                    continue

    else:
        raise ValueError("Unsupported file type. Supported formats: .txt, .log, .nmea, .csv, .xlsx")

    return parsed_sentences


def process_nmea_log(file_path, reference_point=None):
    """Process pre-collected NMEA log file and calculate CEP"""
    parsed_sentences = parse_nmea_from_log(file_path)

    if not parsed_sentences:
        logging.info(f"No valid NMEA sentences found in log file: {file_path}")
        return

    # Initialize NMEAData instance with parsed sentences
    nmea_data = NMEAData(None, None, parsed_sentences)

    # Process the parsed sentences for CEP and satellite summary
    cep_value = nmea_data.calculate_cep(reference_point)

    if cep_value:
        logging.info(f"CEP statistics for {file_path}: {cep_value}")
        nmea_data.write_to_excel('N/A', 'N/A', datetime.now().strftime('%Y%m%d_%H%M%S'), cep_value, filename='processed_log')


if __name__ == "__main__":

    activeProgram = True

    while activeProgram:
        mode = input("Choose data input mode: 1 = Live Serial Data, 2 = Log file\n")
        if mode == '1':
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
                log_folder = f"logs/NMEA_{timestamp}"

                # Prompt the user for a reference point or use the mean point
                use_custom_reference = input(
                    "Do you want to provide a custom reference point for CEP calculations? (y/n): ")

                if use_custom_reference.lower() == 'y':
                    ref_lat = float(input("Enter reference latitude: "))
                    ref_lon = float(input("Enter reference longitude: "))
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

                devices = {
                    "device 1": {"port": "COM9", "baudrate": 115200, "timeout": 1, "duration": 10},
                    "device 2": {"port": "COM7", "baudrate": 115200, "timeout": 1, "duration": 20},
                    "device 3": {"port": "COM10", "baudrate": 921600, "timeout": 1, "duration": 30}
                }

                threads = []

                for device, config in devices.items():
                    try:
                        # Pass reference_point and timestamp to each thread
                        thread = threading.Thread(target=read_nmea_data, args=(
                            config["port"], config["baudrate"], config["timeout"], config["duration"], log_folder,
                            timestamp,
                            reference_point))
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
            file_path = input("Enter the path to the log file (.txt, .log, .nmea, .csv, or .xlsx): ")
            reference_point = None
            process_nmea_log(file_path, reference_point)
        else:
            print("Invalid input. Please enter 1 or 2.")

        activeProgram = input("Do you want to quit the program? (y/n): \n")
        if activeProgram.lower() != 'n':
            break