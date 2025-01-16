# NMEA Data Parser and Logger README

## Overview

The **NMEA Data Parser and Logger** program is a Python-based application designed to read, parse, and analyze NMEA sentences from live serial data or pre-recorded log files. The program provides functionalities to calculate various metrics (like Circular Error Probable - CEP) and outputs the parsed data into Excel files for further analysis.

### Key Features:
- **Live NMEA Data Reading**: Read and parse live NMEA data from one or more serial ports simultaneously.
- **Log File Parsing**: Parse NMEA sentences from various log file formats (e.g., `.txt`, `.log`, `.nmea`, `.csv`, and `.xlsx`).
- **Comprehensive NMEA Sentence Support**: Handles multiple NMEA sentence types like GGA, RMC, GSV, GSA, VTG, GLL, ZDA, GNS, GST, and others.
- **GGA and GSV Extractor Tool**: Extract GGA or GSV lines from large files to reduce parsing time significantly. GGA data typically takes up 10x less space than GSV data, leading to a >10x reduction in test time.
- **CEP Calculation**: Calculates Circular Error Probable (CEP) statistics such as CEP50, CEP68, CEP90, CEP95, and CEP99, based on user-defined reference point or the mean point of the GPS data.
- **Excel Export**: Outputs parsed data, summary statistics, and satellite information to Excel for reference and further analysis.
- **Multi-threading Support**: Supports reading from multiple devices in parallel in live data mode.
- **Customizable Reference Point**: Users can provide a custom reference point for CEP calculation or allow the program to calculate the mean point from data.
- **Two Application Types**: The program supports both a **Console Application** and a **GUI Application** built with Tkinter.

---

## Table of Contents
1. [Installation](#installation)
2. [Usage](#usage)
   - [Running the Program](#running-the-program)
   - [Live Serial Data Mode](#live-serial-data-mode)
   - [Log File Mode](#log-file-mode)
   - [Using the GGA and GSV Extractor Tool](#using-the-gga-and-gsv-extractor-tool)
3. [NMEA Sentences Supported](#nmea-sentences-supported)
4. [CEP Calculation](#cep-calculation)
5. [Output Files](#output-files)
6. [Error Handling](#error-handling)
7. [Logging](#logging)
8. [Known Limitations](#known-limitations)
9. [License](#license)

---

## Installation

### Prerequisites:
1. **Python 3.x** installed on your system.
2. Install required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

### Cloning the repository:

```bash
git clone https://github.com/adedolapoadegboye/NMEA-Parser-GUI.git
cd NMEA-Parser-GUI
```

---

## Usage

### Running the Program

1. **Launch the Program**:  
   Run the main script `nmea_data.py` to start the program:
   ```bash
   python main.py
   ```

2. **Choose Mode**:  
   The program will prompt you to choose between two modes of operation:
   - **Mode 1**: Live Serial Data
   - **Mode 2**: Existing Log File Parsing

---

### Mode 1 - Live Serial Data Mode

In **Mode 1**, the program reads live NMEA data from one or more defined serial ports. You will be asked to enter the following parameters:
1. **Port** (e.g., `COM1`, `COM9`, `/dev/ttyUSB0`): The name of the serial port. Ensure no other program is using this port.
2. **Baudrate** (e.g., 4800, 9600, 115200): The baudrate of the serial port. This must be set for all defined ports.
3. **Timeout** (e.g., 0.1, 0.5, 1.0): Time in seconds to wait for serial data before terminating the program.
4. **Test Duration** (e.g., 10, 30, 60): Test duration in seconds. The program will continuously read and parse NMEA sentences until the specified duration is reached.
5. **Custom Reference Point**: You can either provide a true test point (latitude and longitude) or let the program calculate the mean point of the GPS data. This point will be used as the reference point for CEP calculation.

Once the configuration is set, the program will continuously read and parse NMEA sentences and log the raw and parsed data for the defined Test Duration.

Special Note: When selecting the reference device in dynamic live mode, ensure the box for the reference log is ticked first before inputting all other parameters. The program refreshes when this box is toggled to avoid losing data.

---

### Mode 2 - Log File Mode

In **Mode 2**, you can parse previously collected NMEA log files. The program accepts files in the following formats:
- `.txt`, `.log`, `.nmea` (Plain text)
- `.csv` (Comma-separated values)
- `.xlsx` (Excel)

You will also have the option to provide a custom reference point for CEP calculation or let the program calculate it from the log data.

Special Note: When selecting the reference log in dynamic file mode, ensure the box for the log file is ticked first before inputting all other parameters. The program refreshes when this box is toggled to avoid losing data.

---

### Using the GGA and GSV Extractor Tool

For large files, it is recommended to use the **GGA and GSV Extractor Tool** to filter and extract only the necessary NMEA sentences. This significantly reduces test time, as GGA data typically occupies 10x less space than GSV data. Test times are therefore reduced by more than 10x for GGA-only data compared to GSV-only data.

To use the extractor tool:
1. Run the `extract_gga_gsv_lines` function in the provided script.
2. Specify the input file and choose the output file location.
3. Select whether to extract **GGA**, **GSV**, or both types of sentences.

---

## Application Types

The program supports two application types:
1. **Main Console Application**: A terminal-based app for parsing NMEA data.
   - **Limitations**:
     - Does not support dynamic testing.
     - Does not perform satellite analysis.
2. **GNSS Test Tool (GUI)**: A graphical interface built with Tkinter that supports all features, including dynamic testing and satellite analysis.

To launch the `.exe` versions of the applications:
1. Navigate to the `dist` folder:
   ```bash
   cd dist
   ```
2. Run the desired application:
   - **Main Console Application**: `main.exe`
   - **GNSS Test Tool (GUI)**: `GNSS_Test_Tool.exe`
   - **GGA and GSV Extractor Tool**: `extractor.exe`

Example data are provided in the `example` directory in the root folder for user reference.

---

## NMEA Sentences Supported

This program supports parsing the following NMEA sentence types:
- **GGA**: GPS Fix Data
- **RMC**: Recommended Minimum Navigation Information
- **GSV**: Satellites in View
- **GSA**: GNSS DOP and Active Satellites
- **VTG**: Track Made Good and Ground Speed
- **GLL**: Geographic Position
- **ZDA**: Time and Date
- **GNS**: GNSS Fix Data
- **GST**: Pseudorange Error Statistics
- **GRS**: GNSS Range Residuals
- **RLM**: Return Link Message

Each sentence is parsed into its respective fields and stored for further processing. The full parsed sentence is saved in the `logs/{.xlsx}` directory.

---

## CEP Calculation

The program calculates **Circular Error Probable (CEP)** statistics to quantify the positional accuracy of GPS data. CEP is a measure of accuracy and precision, with the following metrics provided:
- **CEP50**: 50% of the points are within this radius from the reference point.
- **CEP68**, **CEP90**, **CEP95**, **CEP99**: The corresponding percentages of points within these radii.

The program supports the following reference points:
- **Mean Point of dataset**: The mean point of the GPS data. A key indicator for precision estimation.
- **True Point**: The true reference point provided by the user. A key indicator for accuracy estimation.

---

## Output Files

The program exports the following data to Excel files in the `logs/` directory:
1. **Parsed NMEA Sentences**: All parsed sentences with associated metadata.
2. **CEP Summary**: CEP metrics and GPS statistics.
3. **Satellite Data**: Information about satellites tracked (e.g., PRN, SNR).

**File Naming Convention**:  
The output files are saved in the format:  
```
logs/NMEA_YYYYMMDD_HHMMSS/nmea_data_mode_X.xlsx
```
Where `X` refers to the mode (1 for live data, 2 for log parsing).

---

## Error Handling

- **Invalid Data**: Proprietary or unrecognized NMEA sentences are ignored, and errors in parsing are logged.
- **Serial Connection Errors**: Issues with the serial port are caught and logged without crashing the program.
- **File Formatting**: Ensure there are no spaces between consecutive lines in input files. Spaces are treated as end-of-file and may cause parsing issues.

---

## Logging

The program logs important actions and errors to both the console and log files. Log files are stored in the `logs/` directory and named in the format:  
```
console_output_YYYYMMDD_HHMMSS.txt
```
All NMEA raw sentences and detailed execution logs are stored for post-processing.

---

## Known Limitations

- **Checksum Check**: The program does not support checksum checks for NMEA sentences, so ensure sentences are properly formatted.
- **Data Plotting**: The program does not support data plotting.
- **Multiple Files with Different Dates**: When loading multiple static or dynamic files for analysis, ensure their timestamps align. Data will be plotted on the same graph, which may lead to awkward visualizations if dates differ significantly.

---

## License

This project is licensed under the MIT License.
