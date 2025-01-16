# headless_class.py
import logging
import pandas as pd
import numpy as np
import os
import sys

# noinspection PyCompatibility
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
        elif self.sentence_type == "VERNO":
            return (
                f"VERNO - Version Information:\n"
                f"  Version: {self.data.version}\n"
                f"  Build Date: {self.data.build_date}\n"
                f"  Build Time: {self.data.build_time}\n"
            )
        elif self.sentence_type == "SAVEPAR":
            return (
                f"SAVEPAR - Save Parameters:\n"
                f"  Status: {self.data.status}\n"
            )
        elif self.sentence_type == "RESTOREPAR":
            return (
                f"RESTOREPAR - Restore Parameters:\n"
                f"  Status: {self.data.status}\n"
            )
        elif self.sentence_type == "EPE":
            return (
                f"EPE - Estimated Position Error:\n"
                f"  Version: {self.data.msg_ver}\n"
                f"  EPE North: {self.data.epe_north} m\n"
                f"  EPE East: {self.data.epe_east} m\n"
                f"  EPE Down: {self.data.epe_down} m\n"
                f"  EPE 2D: {self.data.epe_2d} m\n"
                f"  EPE 3D: {self.data.epe_3d} m\n"
            )
        elif self.sentence_type == "CFGGEOFENCE":
            return (
                f"CFGGEOFENCE - Geofence Configuration:\n"
                f"  Status: {self.data.status}\n"
                f"  Index: {self.data.index}\n"
                f"  Enabled: {self.data.enabled}\n"
                f"  Shape: {self.data.shape}\n"
                f"  Latitude 0: {self.data.lat0}\n"
                f"  Longitude 0: {self.data.lon0}\n"
                f"  Radius/Lat1: {self.data.lat1_or_radius}\n"
                f"  Longitude 1: {self.data.lon1}\n"
                f"  Latitude 2: {self.data.lat2}\n"
                f"  Longitude 2: {self.data.lon2}\n"
                f"  Latitude 3: {self.data.lat3}\n"
                f"  Longitude 3: {self.data.lon3}\n"
            )
        elif self.sentence_type == "GEOFENCESTATUS":
            return (
                f"GEOFENCESTATUS - Geofence Status:\n"
                f"  Time: {self.data.time}\n"
                f"  State 0: {self.data.state0}\n"
                f"  State 1: {self.data.state1}\n"
                f"  State 2: {self.data.state2}\n"
                f"  State 3: {self.data.state3}\n"
            )
        elif self.sentence_type == "CFGSVIN":
            return (
                f"CFGSVIN - Survey-In Configuration:\n"
                f"  Status: {self.data.status}\n"
                f"  Mode: {self.data.mode}\n"
                f"  Minimum Duration: {self.data.min_dur} s\n"
                f"  Accuracy Limit: {self.data.acc_limit} m\n"
                f"  ECEF X: {self.data.ecef_x} m\n"
                f"  ECEF Y: {self.data.ecef_y} m\n"
                f"  ECEF Z: {self.data.ecef_z} m\n"
            )
        elif self.sentence_type == "SVINSTATUS":
            return (
                f"SVINSTATUS - Survey-In Status:\n"
                f"  Time of Week (TOW): {self.data.tow} ms\n"
                f"  Validity: {self.data.valid}\n"
                f"  Observations: {self.data.obs}\n"
                f"  Duration: {self.data.cfg_dur} s\n"
                f"  Mean X: {self.data.mean_x} m\n"
                f"  Mean Y: {self.data.mean_y} m\n"
                f"  Mean Z: {self.data.mean_z} m\n"
                f"  Mean Accuracy: {self.data.mean_acc} m\n"
            )
        elif self.sentence_type == "GNSSSTART":
            return (
                f"GNSSSTART - Start GNSS Engine:\n"
                f"  Status: {self.data.status}\n"
            )
        elif self.sentence_type == "GNSSSTOP":
            return (
                f"GNSSSTOP - Stop GNSS Engine:\n"
                f"  Status: {self.data.status}\n"
            )
        elif self.sentence_type == "PVT":
            return (
                f"PVT - Position, Velocity, Time:\n"
                f"  TOW: {self.data.tow}\n"
                f"  Date: {self.data.date}\n"
                f"  Time: {self.data.time}\n"
                f"  Latitude: {self.data.lat}\n"
                f"  Longitude: {self.data.lon}\n"
                f"  Altitude: {self.data.alt} m\n"
                f"  Speed: {self.data.spd} m/s\n"
                f"  Heading: {self.data.heading}°\n"
                f"  Number of Satellites Used: {self.data.num_sat_used}\n"
                f"  HDOP: {self.data.hdop}\n"
                f"  PDOP: {self.data.pdop}\n"
            )
        elif self.sentence_type == "CFGNMEADP":
            return (
                f"CFGNMEADP - NMEA Decimal Places Configuration:\n"
                f"  Status: {self.data.status}\n"
                f"  UTC Decimal Places: {self.data.utc_dp}\n"
                f"  Position Decimal Places: {self.data.pos_dp}\n"
                f"  Altitude Decimal Places: {self.data.alt_dp}\n"
                f"  DOP Decimal Places: {self.data.dop_dp}\n"
                f"  Speed Decimal Places: {self.data.spd_dp}\n"
                f"  Course Decimal Places: {self.data.cog_dp}\n"
            )
        elif self.sentence_type == "CFGRCVRMODE":
            return (
                f"CFGRCVRMODE - Receiver Mode Configuration:\n"
                f"  Status: {self.data.status}\n"
                f"  Mode: {self.data.mode}\n"
                f"  Mode Description: {self.data.get_mode_description()}\n"
            )
        elif self.sentence_type == "PL":
            return (
                f"PL - Protection Levels:\n"
                f"  TOW: {self.data.tow} ms\n"
                f"  Position North: {self.data.pl_posn} mm\n"
                f"  Position East: {self.data.pl_pose} mm\n"
                f"  Position Down: {self.data.pl_posd} mm\n"
                f"  Velocity North: {self.data.pl_veln} mm/s\n"
                f"  Velocity East: {self.data.pl_vele} mm/s\n"
                f"  Velocity Down: {self.data.pl_veld} mm/s\n"
                f"  Time: {self.data.pl_time}\n"
            )
        elif self.sentence_type == "CFGSBAS":
            return (
                f"CFGSBAS - SBAS Configuration:\n"
                f"  Status: {self.data.status}\n"
                f"  Value: {self.data.value}\n"
                f"  SBAS Description: {self.data.get_sbas_description()}\n"
            )
        elif self.sentence_type == "CFGCNST":
            return (
                f"CFGCNST - Constellation Configuration:\n"
                f"  GPS Enabled: {self.data.gps}\n"
                f"  GLONASS Enabled: {self.data.glonass}\n"
                f"  Galileo Enabled: {self.data.galileo}\n"
                f"  BDS Enabled: {self.data.bds}\n"
                f"  QZSS Enabled: {self.data.qzss}\n"
            )
        elif self.sentence_type == "DOP":
            return (
                f"DOP - Dilution of Precision:\n"
                f"  TOW: {self.data.tow} ms\n"
                f"  GDOP: {self.data.gdop}\n"
                f"  PDOP: {self.data.pdop}\n"
                f"  HDOP: {self.data.hdop}\n"
                f"  VDOP: {self.data.vdop}\n"
                f"  NDOP: {self.data.ndop}\n"
                f"  EDOP: {self.data.edop}\n"
            )
        elif self.sentence_type == "CFGFIXRATE":
            return (
                f"CFGFIXRATE - Fix Rate Configuration:\n"
                f"  Status: {self.data.status}\n"
            )
        elif self.sentence_type == "VEL":
            return (
                f"VEL - Velocity Information:\n"
                f"  Time: {self.data.time}\n"
                f"  North Velocity: {self.data.vel_n} m/s\n"
                f"  East Velocity: {self.data.vel_e} m/s\n"
                f"  Down Velocity: {self.data.vel_d} m/s\n"
                f"  Ground Speed: {self.data.grd_spd} m/s\n"
                f"  Speed: {self.data.spd} m/s\n"
                f"  Heading: {self.data.heading}°\n"
                f"  Ground Speed Accuracy: {self.data.grd_spd_acc} m/s\n"
                f"  Speed Accuracy: {self.data.spd_acc} m/s\n"
                f"  Heading Accuracy: {self.data.heading_acc}°\n"
            )
        elif self.sentence_type == "CFGODO":
            return (
                f"CFGODO - Odometer Configuration:\n"
                f"  Status: {self.data.status}\n"
                f"  State: {self.data.state}\n"
                f"  Initial Distance: {self.data.init_dist} m\n"
                f"  State Description: {self.data.get_state_description()}\n"
            )
        elif self.sentence_type == "ODO":
            return (
                f"ODO - Odometer Information:\n"
                f"  Time: {self.data.time}\n"
                f"  State: {self.data.state}\n"
                f"  Distance: {self.data.dist} m\n"
                f"  State Description: {self.data.get_state_description()}\n"
            )
        elif self.sentence_type == "LS":
            return (
                f"MLS - Leap Second Information:\n"
                f"  Message Version: {self.data.msg_ver}\n"
                f"  Time of Week: {self.data.tow} seconds\n"
                f"  Leap Second Reference: {self.data.ls_ref}\n"
                f"  UTC Reference Week Number: {self.data.wn}\n"
                f"  Current Leap Seconds: {self.data.ls} seconds\n"
                f"  Leap Second Flag: {self.data.flag}\n"
                f"  Leap Second Forecast Reference: {self.data.lsf_ref}\n"
                f"  Week Number for New Leap Second: {self.data.wnlsf}\n"
                f"  Day of Week for New Leap Second: {self.data.dn}\n"
                f"  Future Leap Seconds: {self.data.lsf}\n"
            )
        elif self.sentence_type == "DRCAL":
            return (
                f"DRCAL - DR Calibration State:\n"
                f"  Message Version: {self.data.msg_ver}\n"
                f"  Calibration State: {self.data.cal_state}\n"
                f"  Navigation Type: {self.data.nav_type}\n"
            )
        elif self.sentence_type == "IMUTYPE":
            return (
                f"IMUTYPE - IMU Initialization Status:\n"
                f"  Message Version: {self.data.msg_ver}\n"
                f"  IMU Status: {self.data.status}\n"
            )
        elif self.sentence_type == "VEHMSG":
            details = f"  Message Version: {self.data.msg_ver}\n  Timestamp: {self.data.timestamp} ms\n"
            if self.data.msg_ver == "1":
                details += f"  Vehicle Speed: {self.data.parameters['VehSpeed']} m/s\n"
            elif self.data.msg_ver == "2":
                details += (
                    f"  Wheel Tick Count: {self.data.parameters['WheelTickCNT']}\n"
                    f"  Forward/Backward Indicator: {self.data.parameters['FWD_Ind']}\n"
                )
            elif self.data.msg_ver == "3":
                details += (
                    f"  LF Speed: {self.data.parameters['LF_Spd']} m/s\n"
                    f"  RF Speed: {self.data.parameters['RF_Spd']} m/s\n"
                    f"  LR Speed: {self.data.parameters['LR_Spd']} m/s\n"
                    f"  RR Speed: {self.data.parameters['RR_Spd']} m/s\n"
                )
            elif self.data.msg_ver == "4":
                details += (
                    f"  LF Tick Count: {self.data.parameters['LF_TickCNT']}\n"
                    f"  RF Tick Count: {self.data.parameters['RF_TickCNT']}\n"
                    f"  LR Tick Count: {self.data.parameters['LR_TickCNT']}\n"
                    f"  RR Tick Count: {self.data.parameters['RR_TickCNT']}\n"
                    f"  Forward/Backward Indicator: {self.data.parameters['FWD_Ind']}\n"
                )
            return "VEHMSG - Vehicle Information:\n" + details
        elif self.sentence_type == "INS":
            return (
                f"INS - Inertial Navigation Solution:\n"
                f"  Timestamp: {self.data.timestamp} ms\n"
                f"  Solution Type: {self.data.sol_type}\n"
                f"  Latitude: {self.data.latitude}°\n"
                f"  Longitude: {self.data.longitude}°\n"
                f"  Height: {self.data.height} m\n"
                f"  North Velocity: {self.data.vel_n} m/s\n"
                f"  East Velocity: {self.data.vel_e} m/s\n"
                f"  Down Velocity: {self.data.vel_d} m/s\n"
                f"  Roll: {self.data.roll}°\n"
                f"  Pitch: {self.data.pitch}°\n"
                f"  Yaw: {self.data.yaw}°\n"
            )
        elif self.sentence_type == "GPS":
            return (
                f"GPS - GNSS Position Status:\n"
                f"  Timestamp: {self.data.timestamp} ms\n"
                f"  Time of Week: {self.data.tow} s\n"
                f"  Latitude: {self.data.latitude}°\n"
                f"  Longitude: {self.data.longitude}°\n"
                f"  Altitude: {self.data.altitude} m\n"
                f"  Speed: {self.data.speed} m/s\n"
                f"  Heading: {self.data.heading}°\n"
                f"  Accuracy: {self.data.accuracy} m\n"
                f"  HDOP: {self.data.hdop}\n"
                f"  PDOP: {self.data.pdop}\n"
                f"  Satellites Used: {self.data.num_sat_used}\n"
                f"  Fix Mode: {self.data.fix_mode}\n"
            )
        elif self.sentence_type == "VEHMOT":
            details = f"  Message Version: {self.data.msg_ver}\n"
            if self.data.msg_ver == "1":
                details += (
                    f"  Peak Acceleration: {self.data.peak_acceleration} m/s²\n"
                    f"  Peak Angular Rate: {self.data.peak_angular_rate} deg/s\n"
                )
            elif self.data.msg_ver == "2":
                details += (
                    f"  UTC: {self.data.utc}\n"
                    f"  Vehicle Type: {self.data.parse_veh_type()}\n"
                    f"  Motion State: {self.data.parse_mot_state()}\n"
                    f"  Acceleration Status: {self.data.parse_acc_status()}\n"
                    f"  Turning Status: {self.data.parse_turning_status()}\n"
                )
            return "VEHMOT - Vehicle Motion Information:\n" + details
        elif self.sentence_type == "SENMSG":
            return (
                f"SENMSG - IMU Sensor Data:\n"
                f"  Message Version: {self.data.msg_ver}\n"
                f"  Timestamp: {self.data.timestamp} ms\n"
                f"  IMU Temperature: {self.data.imu_temp}°C\n"
                f"  IMU Gyro X: {self.data.imu_gyro_x} dps\n"
                f"  IMU Gyro Y: {self.data.imu_gyro_y} dps\n"
                f"  IMU Gyro Z: {self.data.imu_gyro_z} dps\n"
                f"  IMU Acc X: {self.data.imu_acc_x} g\n"
                f"  IMU Acc Y: {self.data.imu_acc_y} g\n"
                f"  IMU Acc Z: {self.data.imu_acc_z} g\n"
            )
        elif self.sentence_type == "DRPVA":
            return (
                f"DRPVA - DR Position, Velocity, and Attitude:\n"
                f"  Message Version: {self.data.msg_ver}\n"
                f"  Timestamp: {self.data.timestamp} ms\n"
                f"  UTC Time: {self.data.time}\n"
                f"  Solution Type: {self.data.sol_type}\n"
                f"  Latitude: {self.data.latitude}°\n"
                f"  Longitude: {self.data.longitude}°\n"
                f"  Altitude: {self.data.altitude} m\n"
                f"  Geoidal Separation: {self.data.sep} m\n"
                f"  North Velocity: {self.data.vel_n} m/s\n"
                f"  East Velocity: {self.data.vel_e} m/s\n"
                f"  Down Velocity: {self.data.vel_d} m/s\n"
                f"  Ground Speed: {self.data.speed} m/s\n"
                f"  Roll: {self.data.roll}°\n"
                f"  Pitch: {self.data.pitch}°\n"
                f"  Heading: {self.data.heading}°\n"
            )
        elif self.sentence_type == "VEHATT":
            return (
                f"VEHATT - Vehicle Attitude:\n"
                f"  Message Version: {self.data.msg_ver}\n"
                f"  Timestamp: {self.data.timestamp} ms\n"
                f"  Roll: {self.data.roll}°\n"
                f"  Pitch: {self.data.pitch}°\n"
                f"  Heading: {self.data.heading}°\n"
                f"  Roll Accuracy: {self.data.acc_roll}°\n"
                f"  Pitch Accuracy: {self.data.acc_pitch}°\n"
                f"  Heading Accuracy: {self.data.acc_heading}°\n"
            )
        elif self.sentence_type == "ANTENNASTATUS":
            return (
                f"ANTENNASTATUS - Antenna Status Information:\n"
                f"  Message Version: {self.data.msg_ver} (Always 3)\n"
                f"  Antenna Status: {self.data.ant_status}\n"
                f"  Antenna Power Indicator: {self.data.ant_power_ind}\n"
                f"  Antenna Mode Indicator: {self.data.mode_ind}\n"
            )
        elif self.sentence_type == "JAMMINGSTATUS":
            return (
                f"JAMMINGSTATUS - Jamming Detection Status:\n"
                f"  Message Version: {self.data.msg_ver} (Always 1)\n"
                f"  Status: {self.data.status}\n"
                f"  Description: {self.data.status}\n"
            )
        elif self.sentence_type == "UNIQID":
            return (
                f"UNIQID - Chip Unique ID Information:\n"
                f"  Response: {self.data.response} (Should be 'OK')\n"
                f"  Length: {self.data.length} bytes\n"
                f"  Chip ID: {self.data.chip_id}\n"
            )
        else:
            return f"Unsupported NMEA sentence type: {self.sentence_type}\n"

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
        elif self.sentence_type == "VERNO":
            self.parsed_sentences.append({
                "Version": self.data.version,
                "Build Date": self.data.build_date,
                "Build Time": self.data.build_time
            })
        elif self.sentence_type == "SAVEPAR":
            self.parsed_sentences.append({
                "Status": self.data.status
            })
        elif self.sentence_type == "RESTOREPAR":
            self.parsed_sentences.append({
                "Status": self.data.status
            })
        elif self.sentence_type == "EPE":
            self.parsed_sentences.append({
                "Version": self.data.msg_ver,
                "EPE North": f"{self.data.epe_north} m",
                "EPE East": f"{self.data.epe_east} m",
                "EPE Down": f"{self.data.epe_down} m",
                "EPE 2D": f"{self.data.epe_2d} m",
                "EPE 3D": f"{self.data.epe_3d} m"
            })
        elif self.sentence_type == "CFGGEOFENCE":
            self.parsed_sentences.append({
                "Status": self.data.status,
                "Index": self.data.index,
                "Enabled": self.data.enabled,
                "Shape": self.data.shape,
                "Latitude 0": self.data.lat0,
                "Longitude 0": self.data.lon0,
                "Latitude 1 / Radius": self.data.lat1_or_radius,
                "Longitude 1": self.data.lon1,
                "Latitude 2": self.data.lat2,
                "Longitude 2": self.data.lon2,
                "Latitude 3": self.data.lat3,
                "Longitude 3": self.data.lon3
            })
        elif self.sentence_type == "GEOFENCESTATUS":
            self.parsed_sentences.append({
                "Time": self.data.time,
                "State 0": self.data.state0,
                "State 1": self.data.state1,
                "State 2": self.data.state2,
                "State 3": self.data.state3
            })
        elif self.sentence_type == "CFGSVIN":
            self.parsed_sentences.append({
                "Status": self.data.status,
                "Mode": self.data.mode,
                "Minimum Duration": f"{self.data.min_dur} s",
                "Accuracy Limit": f"{self.data.acc_limit} m",
                "ECEF X": f"{self.data.ecef_x} m",
                "ECEF Y": f"{self.data.ecef_y} m",
                "ECEF Z": f"{self.data.ecef_z} m"
        })
        elif self.sentence_type == "SVINSTATUS":
            self.parsed_sentences.append({
                "Time of Week": f"{self.data.tow} ms",
                "Validity": self.data.valid,
                "Observations": self.data.obs,
                "Duration": f"{self.data.cfg_dur} s",
                "Mean X": f"{self.data.mean_x} m",
                "Mean Y": f"{self.data.mean_y} m",
                "Mean Z": f"{self.data.mean_z} m",
                "Mean Accuracy": f"{self.data.mean_acc} m"
            })
        elif self.sentence_type == "GNSSSTART":
            self.parsed_sentences.append({
                "Status": self.data.status
            })
        elif self.sentence_type == "GNSSSTOP":
            self.parsed_sentences.append({
                "Status": self.data.status
            })
        elif self.sentence_type == "PVT":
            self.parsed_sentences.append({
                "Time of Week": self.data.tow,
                "Date": self.data.date,
                "Time": self.data.time,
                "Latitude": self.data.lat,
                "Longitude": self.data.lon,
                "Altitude": f"{self.data.alt} m",
                "Separation": f"{self.data.sep} m",
                "Velocity North": f"{self.data.vel_n} m/s",
                "Velocity East": f"{self.data.vel_e} m/s",
                "Velocity Down": f"{self.data.vel_d} m/s",
                "Speed": f"{self.data.spd} m/s",
                "Heading": f"{self.data.heading}°",
                "HDOP": self.data.hdop,
                "PDOP": self.data.pdop
            })
        elif self.sentence_type == "CFGNMEADP":
            self.parsed_sentences.append({
                "Status": self.data.status,
                "UTC Decimal Places": self.data.utc_dp,
                "Position Decimal Places": self.data.pos_dp,
                "Altitude Decimal Places": self.data.alt_dp,
                "DOP Decimal Places": self.data.dop_dp,
                "Speed Decimal Places": self.data.spd_dp,
                "COG Decimal Places": self.data.cog_dp
            })
        elif self.sentence_type == "CFGRCVRMODE":
            self.parsed_sentences.append({
                "Status": self.data.status,
                "Mode": self.data.mode,
                "Mode Description": self.data.get_mode_description()
            })
        elif self.sentence_type == "PL":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "Time of Week": self.data.tow,
                "Protection Level": f"{self.data.pul} m",
                "Position North": f"{self.data.pl_posn} mm",
                "Position East": f"{self.data.pl_pose} mm",
                "Position Down": f"{self.data.pl_posd} mm",
                "Velocity North": f"{self.data.pl_veln} mm/s",
                "Velocity East": f"{self.data.pl_vele} mm/s",
                "Velocity Down": f"{self.data.pl_veld} mm/s"
            })
        elif self.sentence_type == "CFGSBAS":
            self.parsed_sentences.append({
                "Status": self.data.status,
                "SBAS Value": self.data.value,
                "SBAS Description": self.data.get_sbas_description()
            })
        elif self.sentence_type == "CFGCNST":
            self.parsed_sentences.append({
                "Status": self.data.status,
                "GPS Enabled": self.data.gps,
                "GLONASS Enabled": self.data.glonass,
                "Galileo Enabled": self.data.galileo,
                "BDS Enabled": self.data.bds,
                "QZSS Enabled": self.data.qzss,
                "Reserved": self.data.reserved,
                "Constellation Status": self.data.get_constellation_status()
            })
        elif self.sentence_type == "DOP":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "Time of Week": self.data.tow,
                "GDOP": self.data.gdop,
                "PDOP": self.data.pdop,
                "TDOP": self.data.tdop,
                "VDOP": self.data.vdop,
                "HDOP": self.data.hdop,
                "NDOP": self.data.ndop,
                "EDOP": self.data.edop,
                "DOP Status": self.data.get_dop_status(self.data.gdop)
            })
        elif self.sentence_type == "CFGFIXRATE":
            self.parsed_sentences.append({
                "Status": self.data.status
            })
        elif self.sentence_type == "VEL":
            self.parsed_sentences.append({
                "Message Version": self.data.version,
                "Time": self.data.time,
                "North Velocity": f"{self.data.vel_n} m/s",
                "East Velocity": f"{self.data.vel_e} m/s",
                "Down Velocity": f"{self.data.vel_d} m/s",
                "Ground Speed": f"{self.data.grd_spd} m/s",
                "Speed": f"{self.data.spd} m/s",
                "Heading": f"{self.data.heading}°",
                "Ground Speed Accuracy": f"{self.data.grd_spd_acc} m/s",
                "Speed Accuracy": f"{self.data.spd_acc} m/s",
                "Heading Accuracy": f"{self.data.heading_acc}°"
            })
        elif self.sentence_type == "CFGODO":
            self.parsed_sentences.append({
                "Status": self.data.status,
                "State": self.data.state,
                "Initial Distance": f"{self.data.init_dist} m",
                "State Description": self.data.get_state_description()
            })
        elif self.sentence_type == "ODO":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "Time": self.data.time,
                "State": self.data.state,
                "Distance": f"{self.data.dist} m",
                "State Description": self.data.get_state_description()
            })
        elif self.sentence_type == "LS":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "Time of Week": f"{self.data.tow} seconds",
                "Leap Second Reference": self.data.ls_ref,
                "UTC Reference Week Number": self.data.wn,
                "Current Leap Seconds": f"{self.data.ls} seconds",
                "Leap Second Flag": self.data.flag,
                "Leap Second Forecast Reference": self.data.lsf_ref,
                "Week Number for New Leap Second": self.data.wnlsf,
                "Day of Week for New Leap Second": self.data.dn,
                "Future Leap Seconds": self.data.lsf
            })
        elif self.sentence_type == "DRCAL":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "Calibration State": self.data.cal_state,
                "Navigation Type": self.data.nav_type
            })
        elif self.sentence_type == "IMUTYPE":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "IMU Status": self.data.status
            })
        elif self.sentence_type == "VEHMSG":
            details = {
                "Message Version": self.data.msg_ver,
                "Timestamp": f"{self.data.timestamp} ms"
            }
            if self.data.msg_ver == "1":
                details["Vehicle Speed"] = f"{self.data.parameters['VehSpeed']} m/s"
            elif self.data.msg_ver == "2":
                details["Wheel Tick Count"] = self.data.parameters['WheelTickCNT']
                details["Forward/Backward Indicator"] = self.data.parameters['FWD_Ind']
            elif self.data.msg_ver == "3":
                details.update({
                    "LF Speed": f"{self.data.parameters['LF_Spd']} m/s",
                    "RF Speed": f"{self.data.parameters['RF_Spd']} m/s",
                    "LR Speed": f"{self.data.parameters['LR_Spd']} m/s",
                    "RR Speed": f"{self.data.parameters['RR_Spd']} m/s"
                })
            elif self.data.msg_ver == "4":
                details.update({
                    "LF Tick Count": self.data.parameters['LF_TickCNT'],
                    "RF Tick Count": self.data.parameters['RF_TickCNT'],
                    "LR Tick Count": self.data.parameters['LR_TickCNT'],
                    "RR Tick Count": self.data.parameters['RR_TickCNT'],
                    "Forward/Backward Indicator": self.data.parameters['FWD_Ind']
                })
            self.parsed_sentences.append(details)
        elif self.sentence_type == "INS":
            self.parsed_sentences.append({
                "Timestamp": f"{self.data.timestamp} ms",
                "Solution Type": self.data.sol_type,
                "Latitude": f"{self.data.latitude}°",
                "Longitude": f"{self.data.longitude}°",
                "Height": f"{self.data.height} m",
                "North Velocity": f"{self.data.vel_n} m/s",
                "East Velocity": f"{self.data.vel_e} m/s",
                "Down Velocity": f"{self.data.vel_d} m/s",
                "Roll": f"{self.data.roll}°",
                "Pitch": f"{self.data.pitch}°",
                "Yaw": f"{self.data.yaw}°"
            })
        elif self.sentence_type == "GPS":
            self.parsed_sentences.append({
                "Timestamp": f"{self.data.timestamp} ms",
                "Time of Week": f"{self.data.tow} s",
                "Latitude": f"{self.data.latitude}°",
                "Longitude": f"{self.data.longitude}°",
                "Altitude": f"{self.data.altitude} m",
                "Speed": f"{self.data.speed} m/s",
                "Heading": f"{self.data.heading}°",
                "Accuracy": f"{self.data.accuracy} m",
                "HDOP": self.data.hdop,
                "PDOP": self.data.pdop,
                "Satellites Used": self.data.num_sat_used,
                "Fix Mode": self.data.fix_mode
            })
        elif self.sentence_type == "VEHMOT":
            details = {"Message Version": self.data.msg_ver}
            if self.data.msg_ver == "1":
                details.update({
                    "Peak Acceleration": f"{self.data.peak_acceleration} m/s²",
                    "Peak Angular Rate": f"{self.data.peak_angular_rate} deg/s"
                })
            elif self.data.msg_ver == "2":
                details.update({
                    "UTC": self.data.utc,
                    "Vehicle Type": self.data.veh_type,
                    "Motion State": self.data.mot_state,
                    "Acceleration Status": self.data.acc_status,
                    "Turning Status": self.data.turning_status
                })
            self.parsed_sentences.append(details)
        elif self.sentence_type == "SENMSG":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "Timestamp": f"{self.data.timestamp} ms",
                "IMU Temperature": f"{self.data.imu_temp}°C",
                "IMU Gyro X": f"{self.data.imu_gyro_x} dps",
                "IMU Gyro Y": f"{self.data.imu_gyro_y} dps",
                "IMU Gyro Z": f"{self.data.imu_gyro_z} dps",
                "IMU Acc X": f"{self.data.imu_acc_x} g",
                "IMU Acc Y": f"{self.data.imu_acc_y} g",
                "IMU Acc Z": f"{self.data.imu_acc_z} g"
            })
        elif self.sentence_type == "DRPVA":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "Timestamp": f"{self.data.timestamp} ms",
                "UTC Time": self.data.time,
                "Solution Type": self.data.sol_type,
                "Latitude": f"{self.data.latitude}°",
                "Longitude": f"{self.data.longitude}°",
                "Altitude": f"{self.data.altitude} m",
                "Geoidal Separation": f"{self.data.sep} m",
                "North Velocity": f"{self.data.vel_n} m/s",
                "East Velocity": f"{self.data.vel_e} m/s",
                "Down Velocity": f"{self.data.vel_d} m/s",
                "Ground Speed": f"{self.data.speed} m/s",
                "Roll": f"{self.data.roll}°",
                "Pitch": f"{self.data.pitch}°",
                "Heading": f"{self.data.heading}°"
            })
        elif self.sentence_type == "VEHATT":
            self.parsed_sentences.append({
                "Message Version": self.data.msg_ver,
                "Timestamp": f"{self.data.timestamp} ms",
                "Roll": f"{self.data.roll}°",
                "Pitch": f"{self.data.pitch}°",
                "Heading": f"{self.data.heading}°",
                "Roll Accuracy": f"{self.data.acc_roll}°",
                "Pitch Accuracy": f"{self.data.acc_pitch}°",
                "Heading Accuracy": f"{self.data.acc_heading}°"
            })
        elif self.sentence_type == "ANTENNASTATUS":
            self.parsed_sentences.append({
                "Message Version": f"{self.data.msg_ver} (Always 3)",
                "Antenna Status": self.data.ant_status,
                "Antenna Power Indicator": self.data.ant_power_ind,
                "Antenna Mode Indicator": self.data.mode_ind
            })
        elif self.sentence_type == "JAMMINGSTATUS":
            self.parsed_sentences.append({
                "Message Version": f"{self.data.msg_ver} (Always 1)",
                "Status": self.data.status
            })
        elif self.sentence_type == "UNIQID":
            self.parsed_sentences.append({
                "Response": f"{self.data.response} (Should be 'OK')",
                "Length": f"{self.data.length} bytes",
                "Chip ID": self.data.chip_id
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
        # Filter out coordinates with zero values
        valid_coords = [(lat, lon) for lat, lon in self.coordinates if lat != 0 and lon != 0]

        if not valid_coords:
            return None

        latitudes = [coord[0] for coord in valid_coords]
        longitudes = [coord[1] for coord in valid_coords]
        return np.mean(latitudes), np.mean(longitudes)

    def calculate_cep(self, reference_point=None):
        """
        Calculate the Circular Error Probable (CEP) metrics (CEP50, CEP68, CEP90, CEP95, CEP99).
        :param reference_point: (lat, lon) tuple. If None, calculate the mean point.
        :return: Dictionary containing CEP metrics in meters and relevant statistics
        """
        # Filter out coordinates with zero values
        valid_coords = [(lat, lon) for lat, lon in self.coordinates if lat != 0 and lon != 0]

        if not valid_coords:
            return None

        # Warn the user if there are fewer than the recommended number of points
        if len(valid_coords) < self.MIN_POINTS_FOR_CEP:
            logging.warning(f"Warning: Only {len(valid_coords)} data points available for CEP calculation. "
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
        distances = [deg_to_meters(ref_lat, ref_lon, lat, lon) for lat, lon in valid_coords]

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
            'num_points': len(valid_coords),  # Number of valid data points used
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

    @staticmethod
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