# GNSS Test Tool

The GNSS Test Tool is a powerful application designed to automate the analysis of GNSS test results. It supports both **static** and **dynamic** test modes, utilizing either live data collection or pre-recorded log files. The tool provides advanced features like NMEA parsing, Circular Error Probable (CEP) calculation, and data visualization, making it an essential resource for GNSS testing and analysis.

---

## Key Features

1. **Static and Dynamic Test Analysis**:
   - Supports live and log-based tests for both static and dynamic modes.
2. **NMEA Data Parsing**:
   - Parses standard and proprietary NMEA 0183 messages, such as GGA, GSV, and more.
3. **NMEA Extractor Tool**:
   - Quickly extracts specific message types (e.g., GGA, GSV) to reduce runtime.
4. **CEP Calculation**:
   - Computes CEP50, CEP68, CEP90, CEP95, and CEP99 values using reference points or the mean of collected data.
5. **Excel Export**:
   - Outputs parsed data, summary statistics, and satellite information for further analysis.
6. **Error Handling**:
   - Provides clear error messages and handles exceptions gracefully.
7. **Logging**:
   - Logs all events and errors for troubleshooting.
8. **Data Visualization**:
   - Displays logs, plots, and summaries in an intuitive interface.

---

## Installation

1. Install **Python 3.x** on your system.
2. Navigate to the `/dist` folder in the application directory.
3. Choose the appropriate application based on your operating system:
   - **Windows**: Run the `.exe` file.
   - **MacOS**: Run the `.app` file.
4. For advanced use, open the **Extractor** program to optimize log files.

---

## Usage

### 1. **Static Test Analysis**
- **Live Static**: Analyze real-time data from devices connected via serial ports.
- **Static Log**: Analyze pre-recorded log files for post-test evaluation.

### 2. **Dynamic Test Analysis**
- **Live Dynamic**: Compare real-time data from test devices to a reference device on a per-second basis.
- **Dynamic Log**: Perform analysis using pre-recorded log files for both the reference and test devices.

### 3. **NMEA Extractor Tool**
- Extract specific NMEA message types (e.g., GGA, GSV) to reduce runtime and focus on relevant data.

---

## Known Limitations

1. **Concurrent Analysis**: Supports up to 10 devices or log files simultaneously.
2. **Serial Settings**: Devices must be configured to 8-N-1 serial communication.
3. **Dynamic Test Reference**: Selecting the "Reference Device" clears previously set configurations—ensure this is selected first.
4. **Excel Logging Limit**: Maximum of 1,048,576 rows; logging stops once the limit is reached.
5. **Logfile Formatting**: Ensure no empty lines in pre-recorded log files to avoid termination errors.
6. **Runtime Optimization**: For large datasets, use the NMEA Extractor Tool to streamline analysis.

---

## Logs and Output

Logs and results are saved in the `/dist/logs` folder, with the naming convention:  
`<NMEA_YYYYMMDD_HHMMSSssssss>`.

Each test log contains:
- **Console Log**: Important messages and errors.
- **Raw Log File**: Unprocessed NMEA messages.
- **Excel File**: Parsed data and summary for custom analysis.

---

## Improvements and Future Roadmap

- Expand analysis to include additional metrics like speed, heading, and altitude.
- Add support for two-antenna heading analysis and other advanced GNSS features.

---

For further details, refer to the attached protocol document or contact the development team. Enjoy using the GNSS Test Tool for your GNSS testing needs!
