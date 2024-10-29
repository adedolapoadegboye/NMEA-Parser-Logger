# nmea_data.py

import pandas as pd
import logging
import numpy as np

class NMEAData:
    def __init__(self, sentence_type, data, parsed_sentences):
        self.baudrate = None
        self.port = None
        self.sentence_type = sentence_type
        self.data = data
        self.parsed_sentences = parsed_sentences  # List to store parsed NMEA data
        self.coordinates = []  # To store latitude and longitude tuples
        self.MIN_POINTS_FOR_CEP = 50  # Minimum number of points for CEP calculation
        self.satellite_info = []  # To store satellite CNR and related info from GSV sentences



    def __str__(self):
        # Pretty print the data based on sentence type
        if self.sentence_type == "GGA":
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
        elif self.sentence_type == "GSV":
            return (
                f"GSV - Satellites in View:\n"
                f"  Number of Messages: {self.data.num_messages}\n"
                f"  Message Number: {self.data.msg_num}\n"
                f"  Total Satellites in View: {self.data.num_sv_in_view}\n"
                f"  Satellite 1 PRN: {self.data.sv_prn_num_1} - Elevation: {self.data.elevation_deg_1}° - Azimuth: {self.data.azimuth_1}° - SNR: {self.data.snr_1} dB\n"
                f"  Satellite 2 PRN: {self.data.sv_prn_num_2} - Elevation: {self.data.elevation_deg_2}° - Azimuth: {self.data.azimuth_2}° - SNR: {self.data.snr_2} dB\n"
                f"  Satellite 3 PRN: {self.data.sv_prn_num_3} - Elevation: {self.data.elevation_deg_3}° - Azimuth: {self.data.azimuth_3}° - SNR: {self.data.snr_3} dB\n"
                f"  Satellite 4 PRN: {self.data.sv_prn_num_4} - Elevation: {self.data.elevation_deg_4}° - Azimuth: {self.data.azimuth_4}° - SNR: {self.data.snr_4} dB\n"
            )
        elif self.sentence_type == "GSA":
            return (
                f"GSA - Satellite Info:\n"
                f"  Mode: {self.data.mode}\n"
                f"  Mode Fix Type: {self.data.mode_fix_type}\n"
                f"  Satellites Used: {', '.join(filter(None, [self.data.sv_id01, self.data.sv_id02, self.data.sv_id03, self.data.sv_id04, self.data.sv_id05, self.data.sv_id06, self.data.sv_id07, self.data.sv_id08, self.data.sv_id09, self.data.sv_id10, self.data.sv_id11, self.data.sv_id12]))}\n"
                f"  PDOP: {self.data.pdop}\n"
                f"  HDOP: {self.data.hdop}\n"
                f"  VDOP: {self.data.vdop}\n"
            )
        elif self.sentence_type == "VTG":
            return (
                f"VTG - Course over Ground and Ground Speed:\n"
                f"  True Track: {self.data.true_track}° {self.data.true_track_sym}\n"
                f"  Magnetic Track: {self.data.mag_track}° {self.data.mag_track_sym}\n"
                f"  Speed over Ground: {self.data.spd_over_grnd_kts} knots / {self.data.spd_over_grnd_kmph} km/h\n"
                f"  FAA Mode: {self.data.faa_mode}\n"
            )
        elif self.sentence_type == "GLL":
            return (
                f"GLL - Geographic Position:\n"
                f"  Latitude: {self.data.latitude} {self.data.lat_dir}\n"
                f"  Longitude: {self.data.longitude} {self.data.lon_dir}\n"
                f"  Timestamp: {self.data.timestamp}\n"
                f"  Status: {self.data.status}\n"
                f"  FAA Mode: {self.data.faa_mode}\n"
            )
        elif self.sentence_type == "ZDA":
            return (
                f"ZDA - Time and Date:\n"
                f"  UTC Time: {self.data.timestamp}\n"
                f"  Day: {self.data.day}\n"
                f"  Month: {self.data.month}\n"
                f"  Year: {self.data.year}\n"
                f"  Local Zone Hours: {self.data.local_zone}\n"
                f"  Local Zone Minutes: {self.data.local_zone_minutes}\n"
            )
        elif self.sentence_type == "GNS":
            return (
                f"GNS - GNSS Fix Data:\n"
                f"  Timestamp: {self.data.timestamp}\n"
                f"  Latitude: {self.data.latitude} {self.data.lat_dir}\n"
                f"  Longitude: {self.data.longitude} {self.data.lon_dir}\n"
                f"  Mode Indicator: {self.data.mode_indicator}\n"
                f"  Number of Satellites in Use: {self.data.num_sats}\n"
                f"  HDOP: {self.data.hdop}\n"
                f"  Altitude: {self.data.altitude}\n"
                f"  Geoidal Separation: {self.data.geo_sep}\n"
                f"  Age of Differential Data: {self.data.age_gps_data}\n"
                f"  Differential Reference Station ID: {self.data.differential}\n"
            )
        elif self.sentence_type == "GST":
            return (
                f"GST - Pseudorange Error Statistics:\n"
                f"  UTC Time: {self.data.timestamp}\n"
                f"  RMS Deviation: {self.data.rms}\n"
                f"  Major Axis Error: {self.data.std_dev_major}\n"
                f"  Minor Axis Error: {self.data.std_dev_minor}\n"
                f"  Orientation of Major Axis: {self.data.orientation}\n"
                f"  Latitude Error (std dev): {self.data.std_dev_latitude}\n"
                f"  Longitude Error (std dev): {self.data.std_dev_longitude}\n"
                f"  Altitude Error (std dev): {self.data.std_dev_altitude}\n"
            )
        elif self.sentence_type == "GRS":
            return (
                f"GRS - GNSS Range Residuals:\n"
                f"  Timestamp: {self.data.timestamp}\n"
                f"  Residual Mode: {self.data.residuals_mode}\n"
                f"  Residuals: {[self.data.sv_res_01, self.data.sv_res_02, self.data.sv_res_03, self.data.sv_res_04, self.data.sv_res_05, self.data.sv_res_06, self.data.sv_res_07, self.data.sv_res_08, self.data.sv_res_09, self.data.sv_res_10, self.data.sv_res_11, self.data.sv_res_12]}\n"
            )
        elif self.sentence_type == "RLM":
            return (
                f"RLM - Return Link Message:\n"
                f"  Beacon ID: {self.data.beacon_id}\n"
                f"  Message Code: {self.data.message_code}\n"
            )
        else:
            return f"Unsupported NMEA sentence type: {self.sentence_type}"

    def add_sentence_data(self):
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
        elif self.sentence_type == "GSV":
            # Pretty print the data based on sentence type
            if self.sentence_type == "GSV":
                # Use system time to timestamp each GSV message
                sentence_timestamp = pd.Timestamp.now().replace(microsecond=3)

                # Extract satellite CNR and relevant data from GSV sentence
                for i in range(1, 5):  # GSV sentences may contain up to 4 satellite entries
                    satellite_prn = getattr(self.data, f'sv_prn_num_{i}', None)
                    elevation = getattr(self.data, f'elevation_deg_{i}', None)
                    azimuth = getattr(self.data, f'azimuth_{i}', None)
                    snr = getattr(self.data, f'snr_{i}', None)

                    # Ensure we have valid numeric values
                    try:
                        if satellite_prn and snr and snr != '':  # Ensure snr is not an empty string
                            self.satellite_info.append({
                                "Timestamp": sentence_timestamp,
                                "Satellite PRN": satellite_prn,
                                "Elevation (°)": float(elevation) if elevation else None,
                                "Azimuth (°)": float(azimuth) if azimuth else None,
                                "CNR (SNR) (dB)": float(snr) if snr else None
                            })
                    except ValueError:
                        logging.error(f"Invalid data for satellite PRN {satellite_prn} in GSV sentence.")
            self.parsed_sentences.append({
                "Type": "GSV",
                "Number of Messages": self.data.num_messages,
                "Message Number": self.data.msg_num,
                "Total Satellites in View": self.data.num_sv_in_view,
                "Satellite 1 PRN": f"{self.data.sv_prn_num_1}",
                "Elevation 1": f"{self.data.elevation_deg_1}°",
                "Azimuth 1": f"{self.data.azimuth_1}°",
                "SNR 1": f"{self.data.snr_1} dB",
                "Satellite 2 PRN": f"{self.data.sv_prn_num_2}",
                "Elevation 2": f"{self.data.elevation_deg_2}°",
                "Azimuth 2": f"{self.data.azimuth_2}°",
                "SNR 2": f"{self.data.snr_2} dB",
                "Satellite 3 PRN": f"{self.data.sv_prn_num_3}",
                "Elevation 3": f"{self.data.elevation_deg_3}°",
                "Azimuth 3": f"{self.data.azimuth_3}°",
                "SNR 3": f"{self.data.snr_3} dB",
                "Satellite 4 PRN": f"{self.data.sv_prn_num_4}",
                "Elevation 4": f"{self.data.elevation_deg_4}°",
                "Azimuth 4": f"{self.data.azimuth_4}°",
                "SNR 4": f"{self.data.snr_4} dB"
            })
        elif self.sentence_type == "GSA":
            self.parsed_sentences.append({
                "Type": "GSA",
                "Mode": self.data.mode,
                "Mode Fix Type": self.data.mode_fix_type,
                "Satellites Used": f"{', '.join(filter(None, [self.data.sv_id01, self.data.sv_id02, self.data.sv_id03, self.data.sv_id04, self.data.sv_id05, self.data.sv_id06, self.data.sv_id07, self.data.sv_id08, self.data.sv_id09, self.data.sv_id10, self.data.sv_id11, self.data.sv_id12]))}",
                "PDOP": self.data.pdop,
                "HDOP": self.data.hdop,
                "VDOP": self.data.vdop
            })
        elif self.sentence_type == "VTG":
            self.parsed_sentences.append({
                "Type": "VTG",
                "True Track": f"{self.data.true_track}°",
                "Magnetic Track": f"{self.data.mag_track}°",
                "Speed over Ground": f"{self.data.spd_over_grnd_kts} knots / {self.data.spd_over_grnd_kmph} km/h",
                "FAA Mode": self.data.faa_mode
            })
        elif self.sentence_type == "GLL":
            self.parsed_sentences.append({
                "Type": "GLL",
                "Latitude": f"{self.data.latitude} {self.data.lat_dir}",
                "Longitude": f"{self.data.longitude} {self.data.lon_dir}",
                "Timestamp": self.data.timestamp.replace(tzinfo=None),
                "Status": self.data.status,
                "FAA Mode": self.data.faa_mode
            })
        elif self.sentence_type == "ZDA":
            self.parsed_sentences.append({
                "Type": "ZDA",
                "UTC Time": self.data.timestamp,
                "Day": self.data.day,
                "Month": self.data.month,
                "Year": self.data.year,
                "Local Zone Hours": self.data.local_zone,
                "Local Zone Minutes": self.data.local_zone_minutes
            })
        elif self.sentence_type == "GNS":
            self.parsed_sentences.append({
                "Type": "GNS",
                "Timestamp": self.data.timestamp.replace(tzinfo=None),
                "Latitude": f"{self.data.latitude} {self.data.lat_dir}",
                "Longitude": f"{self.data.longitude} {self.data.lon_dir}",
                "Mode Indicator": self.data.mode_indicator,
                "Number of Satellites": self.data.num_sats,
                "HDOP": self.data.hdop,
                "Altitude": self.data.altitude,
                "Geoidal Separation": self.data.geo_sep,
                "Age of Differential Data": self.data.age_gps_data,
                "Differential Reference Station ID": self.data.differential
            })

        elif self.sentence_type == "GST":
            self.parsed_sentences.append({
                "Type": "GST",
                "UTC Time": self.data.timestamp,
                "RMS Deviation": self.data.rms,
                "Major Axis Error": self.data.std_dev_major,
                "Minor Axis Error": self.data.std_dev_minor,
                "Orientation of Major Axis": self.data.orientation,
                "Latitude Error": self.data.std_dev_latitude,
                "Longitude Error": self.data.std_dev_longitude,
                "Altitude Error": self.data.std_dev_altitude
            })

        elif self.sentence_type == "GRS":
            self.parsed_sentences.append({
                "Type": "GRS",
                "Timestamp": self.data.timestamp.replace(tzinfo=None),
                "Residual Mode": self.data.residuals_mode,
                "Residuals": [self.data.sv_res_01, self.data.sv_res_02, self.data.sv_res_03, self.data.sv_res_04,
                              self.data.sv_res_05, self.data.sv_res_06, self.data.sv_res_07, self.data.sv_res_08,
                              self.data.sv_res_09, self.data.sv_res_10, self.data.sv_res_11, self.data.sv_res_12]
            })
        elif self.sentence_type == "RLM":
            self.parsed_sentences.append({
                "Type": "RLM",
                "Beacon ID": self.data.beacon_id,
                "Message Code": self.data.message_code
            })
        else:
            return f"Unsupported NMEA sentence type: {self.sentence_type}"

    def add_coordinates(self):
        # Add GLL or GGA coordinates to the coordinates list
        if self.sentence_type == "GGA":
            lat = self.data.latitude
            lon = self.data.longitude
        else:
            return

        self.coordinates.append((lat, lon))

    def calculate_mean_point(self):
        # Calculate the mean latitude and longitude
        if not self.coordinates:
            return None

        latitudes = [coord[0] for coord in self.coordinates]
        longitudes = [coord[1] for coord in self.coordinates]
        return np.mean(latitudes), np.mean(longitudes)

    def calculate_cep(self, reference_point=None):
        """
        Calculate the Circular Error Probable (CEP) metrics (CEP50, CEP68, CEP90, CEP95, CEP99).
        :param reference_point: (lat, lon) tuple. If None, calculate the mean point.
        :return: Dictionary containing CEP metrics in meters and relevant statistics
        """
        if not self.coordinates:
            return None

        # Warn the user if there are fewer than the recommended number of points
        if len(self.coordinates) < self.MIN_POINTS_FOR_CEP:
            logging.warning(f"Warning: Only {len(self.coordinates)} data points available for CEP calculation. "
                            f"At least {self.MIN_POINTS_FOR_CEP} points are recommended for a reliable calculation.")

        if reference_point is None:
            reference_point = self.calculate_mean_point()

        ref_lat, ref_lon = reference_point

        # Function to convert degrees to meters
        def deg_to_meters(lat1, lon1, lat2, lon2):
            lat_dist = (lat1 - lat2) * 111139  # Approximation for meters/degree latitude
            lon_dist = (lon1 - lon2) * (111139 * np.cos(np.radians(lat1)))  # Latitude dependent
            return np.sqrt(lat_dist ** 2 + lon_dist ** 2)

        # Calculate distances to the reference point
        distances = [deg_to_meters(ref_lat, ref_lon, lat, lon) for lat, lon in self.coordinates]

        # CEP calculations using percentiles
        cep50 = np.percentile(distances, 50)
        cep68 = np.percentile(distances, 68)
        cep90 = np.percentile(distances, 90)
        cep95 = np.percentile(distances, 95)
        cep99 = np.percentile(distances, 99)

        # Return all CEP values and additional statistics in a dictionary
        return {
            'CEP50': cep50,
            'CEP68': cep68,
            'CEP90': cep90,
            'CEP95': cep95,
            'CEP99': cep99,
            'num_points': len(self.coordinates),  # Number of data points used
            'reference_point': reference_point,  # Reference point used (if any)
            'distances': distances  # All distances to the reference point
        }

    def write_to_excel_mode_1(self, port, baudrate, timestamp, cep_value, filename="nmea_data_mode_1"):
        """
        MODE 1:Write NMEA parsed data, summary statistics (CEP), and individual data points with distances to an Excel file.
        Also includes a new sheet "Satellites summary" for satellite CNR summary.
        """
        try:
            # Ensure reference point is properly formatted
            ref_point = cep_value['reference_point']
            if ref_point:
                formatted_ref_point = f"({float(ref_point[0]):.7f}, {float(ref_point[1]):.7f})"
            else:
                formatted_ref_point = ''

            # Prepare the data for the summary sheet
            summary_data = {
                'Port': port,
                'Baudrate': baudrate,
                'Reference Point': formatted_ref_point,
                'Number of Data Points': cep_value['num_points'],
                'CEP50 (m)': cep_value['CEP50'],
                'CEP68 (m)': cep_value['CEP68'],
                'CEP90 (m)': cep_value['CEP90'],
                'CEP95 (m)': cep_value['CEP95'],
                'CEP99 (m)': cep_value['CEP99'],
            }

            # Create a dataframe for parsed sentences
            df_parsed = pd.DataFrame(self.parsed_sentences)

            # Create a dataframe for the summary data
            df_summary = pd.DataFrame([summary_data])

            def deg_to_meters(lat1, lon1, lat2, lon2):
                lat_dist = (lat1 - lat2) * 111139  # Approximation for meters/degree latitude
                lon_dist = (lon1 - lon2) * (111139 * np.cos(np.radians(lat1)))  # Latitude dependent
                return np.sqrt(lat_dist ** 2 + lon_dist ** 2)

            # Create a dataframe for data points with distances and timestamps
            reference_point = cep_value['reference_point']
            data_points = []
            if reference_point:
                ref_lat, ref_lon = reference_point



                # Collect the data points along with calculated distances
                for entry in self.parsed_sentences:
                    if "Latitude" in entry and "Longitude" in entry:
                        try:
                            # Convert latitude and longitude to float before calculating distance
                            lat = float(entry.get("Latitude", "0").split()[0])
                            lon = float(entry.get("Longitude", "0").split()[0])

                            # Calculate distance from reference point
                            distance = deg_to_meters(ref_lat, ref_lon, lat, lon)
                            data_points.append({
                                "Timestamp": entry.get("Timestamp"),
                                "Latitude": entry.get("Latitude"),
                                "Longitude": entry.get("Longitude"),
                                "Distance from Reference (m)": distance
                            })
                        except ValueError:
                            logging.error(f"Invalid data point for latitude/longitude in entry: {entry}")
                            data_points.append({
                                "Timestamp": entry.get("Timestamp"),
                                "Latitude": entry.get("Latitude"),
                                "Longitude": entry.get("Longitude"),
                                "Distance from Reference (m)": None
                            })
            else:
                # No reference point provided, so use the mean point
                mean_lat, mean_lon = self.calculate_mean_point()

                for entry in self.parsed_sentences:
                    if "Latitude" in entry and "Longitude" in entry:
                        try:
                            # Convert latitude and longitude to float before calculating distance
                            lat = float(entry.get("Latitude", "0").split()[0])
                            lon = float(entry.get("Longitude", "0").split()[0])

                            # Calculate distance from the mean point
                            distance = deg_to_meters(mean_lat, mean_lon, lat, lon)
                            data_points.append({
                                "Timestamp": entry.get("Timestamp"),
                                "Latitude": entry.get("Latitude"),
                                "Longitude": entry.get("Longitude"),
                                "Distance from Mean Point (m)": distance  # Change label when using mean
                            })
                        except ValueError:
                            logging.error(f"Invalid data point for latitude/longitude in entry: {entry}")
                            data_points.append({
                                "Timestamp": entry.get("Timestamp"),
                                "Latitude": entry.get("Latitude"),
                                "Longitude": entry.get("Longitude"),
                                "Distance from Mean Point (m)": None
                            })

            df_data_points = pd.DataFrame(data_points)

            # Create a dataframe for the satellite CNR summary
            df_sat_summary = pd.DataFrame(self.satellite_info)

            # Default statistics for satellites
            df_sat_summary_stats = pd.DataFrame()  # Initialize to avoid 'referenced before assignment'

            # Calculate satellite statistics for the "Satellites summary" sheet
            if not df_sat_summary.empty:
                avg_cnr = df_sat_summary["CNR (SNR) (dB)"].mean()
                min_cnr = df_sat_summary["CNR (SNR) (dB)"].min()
                max_cnr = df_sat_summary["CNR (SNR) (dB)"].max()

                # Calculate the number of unique satellites (unique PRNs)
                unique_prns = df_sat_summary["Satellite PRN"].nunique()

                sat_summary_stats = {
                    "Average CNR (SNR) (dB)": avg_cnr,
                    "Min CNR (SNR) (dB)": min_cnr,
                    "Max CNR (SNR) (dB)": max_cnr,
                    "Total Satellites Tracked": unique_prns
                }

                df_sat_summary_stats = pd.DataFrame([sat_summary_stats])

            # Write data to Excel
            filepath = f"logs/NMEA_{timestamp}/{filename}_{port}_{baudrate}_{timestamp}.xlsx"
            max_rows = 1048576  # Excel row limit

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Write parsed sentences, splitting across multiple sheets if necessary
                for i in range(0, len(df_parsed), max_rows):
                    chunk = df_parsed.iloc[i:i + max_rows]
                    chunk.to_excel(writer, index=False, sheet_name=f"Parsed_{i // max_rows + 1}")

                # Write summary data to a new sheet called "CEP Summary"
                df_summary.to_excel(writer, index=False, sheet_name="CEP Summary")

                # Write data points with distances, splitting across multiple sheets if necessary
                for i in range(0, len(df_data_points), max_rows):
                    chunk = df_data_points.iloc[i:i + max_rows]
                    chunk.to_excel(writer, index=False, sheet_name=f"DataPoints_{i // max_rows + 1}")

                # Write satellite summary, splitting if necessary
                for i in range(0, len(df_sat_summary), max_rows):
                    chunk = df_sat_summary.iloc[i:i + max_rows]
                    chunk.to_excel(writer, index=False, sheet_name=f"SatSummary_{i // max_rows + 1}")

                # Write satellite summary statistics (if any)
                if not df_sat_summary_stats.empty:
                    df_sat_summary_stats.to_excel(writer, index=False, sheet_name="SatSummaryStats")

            logging.info(f"Data written to {filepath}")

        except Exception as e:
            logging.error(f"Error writing to Excel file: {e}")

    def write_to_excel_mode_2(self, timestamp, cep_value, filename="nmea_data_mode_2"):
        """
        MODE 2: Write NMEA parsed data, summary statistics (CEP), and individual data points with distances to an Excel file.
        Also includes a new sheet "Satellites summary" for satellite CNR summary.
        """
        try:
            # Ensure reference point is properly formatted
            ref_point = cep_value['reference_point']
            if ref_point:
                formatted_ref_point = f"({float(ref_point[0]):.7f}, {float(ref_point[1]):.7f})"
            else:
                formatted_ref_point = ''

            # Prepare the data for the summary sheet
            summary_data = {
                'Reference Point': formatted_ref_point,
                'Number of Data Points': cep_value['num_points'],
                'CEP50 (m)': cep_value['CEP50'],
                'CEP68 (m)': cep_value['CEP68'],
                'CEP90 (m)': cep_value['CEP90'],
                'CEP95 (m)': cep_value['CEP95'],
                'CEP99 (m)': cep_value['CEP99'],
            }

            # Create a dataframe for parsed sentences
            df_parsed = pd.DataFrame(self.parsed_sentences)

            # Create a dataframe for the summary data
            df_summary = pd.DataFrame([summary_data])

            def deg_to_meters(lat1, lon1, lat2, lon2):
                lat_dist = (lat1 - lat2) * 111139  # Approximation for meters/degree latitude
                lon_dist = (lon1 - lon2) * (111139 * np.cos(np.radians(lat1)))  # Latitude dependent
                return np.sqrt(lat_dist ** 2 + lon_dist ** 2)

            # Create a dataframe for data points with distances and timestamps
            reference_point = cep_value['reference_point']
            data_points = []
            if reference_point:
                ref_lat, ref_lon = reference_point
                # Collect the data points along with calculated distances
                for entry in self.parsed_sentences:
                    if "Latitude" in entry and "Longitude" in entry:
                        try:
                            # Convert latitude and longitude to float before calculating distance
                            lat = float(entry.get("Latitude", "0").split()[0])
                            lon = float(entry.get("Longitude", "0").split()[0])

                            # Calculate distance from reference point
                            distance = deg_to_meters(ref_lat, ref_lon, lat, lon)
                            data_points.append({
                                "Timestamp": entry.get("Timestamp"),
                                "Latitude": entry.get("Latitude"),
                                "Longitude": entry.get("Longitude"),
                                "Distance from Reference (m)": distance
                            })
                        except ValueError:
                            logging.error(f"Invalid data point for latitude/longitude in entry: {entry}")
                            data_points.append({
                                "Timestamp": entry.get("Timestamp"),
                                "Latitude": entry.get("Latitude"),
                                "Longitude": entry.get("Longitude"),
                                "Distance from Reference (m)": None
                            })
            else:
                # No reference point provided, so use the mean point
                mean_lat, mean_lon = self.calculate_mean_point()

                for entry in self.parsed_sentences:
                    if "Latitude" in entry and "Longitude" in entry:
                        try:
                            # Convert latitude and longitude to float before calculating distance
                            lat = float(entry.get("Latitude", "0").split()[0])
                            lon = float(entry.get("Longitude", "0").split()[0])

                            # Calculate distance from the mean point
                            distance = deg_to_meters(mean_lat, mean_lon, lat, lon)
                            data_points.append({
                                "Timestamp": entry.get("Timestamp"),
                                "Latitude": entry.get("Latitude"),
                                "Longitude": entry.get("Longitude"),
                                "Distance from Mean Point (m)": distance  # Change label when using mean
                            })
                        except ValueError:
                            logging.error(f"Invalid data point for latitude/longitude in entry: {entry}")
                            data_points.append({
                                "Timestamp": entry.get("Timestamp"),
                                "Latitude": entry.get("Latitude"),
                                "Longitude": entry.get("Longitude"),
                                "Distance from Mean Point (m)": None
                            })

            df_data_points = pd.DataFrame(data_points)

            # Create a dataframe for the satellite CNR summary
            df_sat_summary = pd.DataFrame(self.satellite_info)

            # Default statistics for satellites
            df_sat_summary_stats = pd.DataFrame()  # Initialize to avoid 'referenced before assignment'

            # Calculate satellite statistics for the "Satellites summary" sheet
            if not df_sat_summary.empty:
                avg_cnr = df_sat_summary["CNR (SNR) (dB)"].mean()
                min_cnr = df_sat_summary["CNR (SNR) (dB)"].min()
                max_cnr = df_sat_summary["CNR (SNR) (dB)"].max()

                # Calculate the number of unique satellites (unique PRNs)
                unique_prns = df_sat_summary["Satellite PRN"].nunique()

                sat_summary_stats = {
                    "Average CNR (SNR) (dB)": avg_cnr,
                    "Min CNR (SNR) (dB)": min_cnr,
                    "Max CNR (SNR) (dB)": max_cnr,
                    "Total Satellites Tracked": unique_prns
                }

                df_sat_summary_stats = pd.DataFrame([sat_summary_stats])

            # Write data to Excel
            filepath = f"logs/NMEA_{timestamp}/{filename}_{timestamp}.xlsx"
            max_rows = 1048576  # Excel row limit

            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                # Write parsed sentences, splitting across multiple sheets if necessary
                for i in range(0, len(df_parsed), max_rows):
                    chunk = df_parsed.iloc[i:i + max_rows]
                    chunk.to_excel(writer, index=False, sheet_name=f"Parsed_{i // max_rows + 1}")

                    # Write summary data to a new sheet called "CEP Summary"
                df_summary.to_excel(writer, index=False, sheet_name="CEPSummaryStats")

                # Write data points with distances, splitting across multiple sheets if necessary
                for i in range(0, len(df_data_points), max_rows):
                    chunk = df_data_points.iloc[i:i + max_rows]
                    chunk.to_excel(writer, index=False, sheet_name=f"CEPDataPoints_{i // max_rows + 1}")

                # Write satellite summary, splitting if necessary
                for i in range(0, len(df_sat_summary), max_rows):
                    chunk = df_sat_summary.iloc[i:i + max_rows]
                    chunk.to_excel(writer, index=False, sheet_name=f"SatDataPoints_{i // max_rows + 1}")

                # Write satellite summary statistics (if any)
                if not df_sat_summary_stats.empty:
                        df_sat_summary_stats.to_excel(writer, index=False, sheet_name="SatSummaryStats")

            logging.info(f"Data written to {filepath}")

        except Exception as e:
            logging.error(f"Error writing to Excel file: {e}")