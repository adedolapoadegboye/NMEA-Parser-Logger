import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial.tools.list_ports
from datetime import datetime
import os
import threading
from main import read_nmea_data, process_nmea_log, setup_logging


class GNSSTestTool:
    def __init__(self, root):
        self.file_var = None
        self.duration_var = None
        self.baudrate_var = None
        self.timeout_var = None
        self.port_var = None
        self.lon_var = None
        self.lat_var = None
        self.use_reference = None
        self.serial_config_frame_holder = None
        self.num_devices_dropdown = None
        self.num_devices_var = None
        self.number_of_test_devices = None
        self.number_of_test_devices_dropdown = None
        self.mode_content = None
        self.test_type = None
        self.root = root
        self.root.title("GNSS Test Tool")
        # Set the window to fullscreen
        self.root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")
        # Exit fullscreen with Escape key
        self.root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))
        self.root.configure(bg="#B8D8D8")  # Background color

        self.create_widgets()

    def create_widgets(self):
        # Title
        title = tk.Label(
            self.root, text="GNSS Test Tool", font=("Arial", 18, "bold"), bg="#B8D8D8", fg="#FE5F55"
        )
        title.pack(pady=10)

        # Test Type Selection
        test_type_frame = ttk.LabelFrame(self.root, text="Select Test Type", padding=10)
        test_type_frame.pack(fill="x", padx=15, pady=10)

        ttk.Label(test_type_frame, text="Test Type:", font=("Arial", 10)).pack(side="left", padx=10)
        self.test_type = tk.StringVar(value="Static (fixed reference point)")
        ttk.Combobox(
            test_type_frame, textvariable=self.test_type, values=["Static (fixed reference point)", "Dynamic (moving reference point)"], state="readonly", width=35
        ).pack(side="left", padx=10)

        # Mode Selection Frame
        mode_frame = ttk.LabelFrame(self.root, text="Select Processing Mode", padding=10)
        mode_frame.pack(fill="x", padx=15, pady=10)

        ttk.Button(mode_frame, text="Live Data", command=self.show_live_mode).pack(side="left", padx=10, pady=5)
        ttk.Button(mode_frame, text="Load File", command=self.show_file_mode).pack(side="left", padx=10, pady=5)

        # Dynamic Mode Content
        self.mode_content = ttk.Frame(self.root, padding=10)
        self.mode_content.pack(fill="both", expand=True, padx=15, pady=10)

    def show_live_mode(self):
        if self.test_type.get() == "Static (fixed reference point)":
            """Show UI for static live serial data setup"""
            self.clear_mode_content()

            # Header
            tk.Label(self.mode_content, text="Live Serial Data", font=("Arial", 18, "bold"), fg="#FE5F55").pack(pady=10)

            # General Configuration
            general_config_frame = ttk.LabelFrame(self.mode_content, text="General Configuration", padding=10)
            general_config_frame.pack(fill="x", padx=10, pady=10)

            # Number of devices
            ttk.Label(general_config_frame, text="Number of Test Devices:", font=("Arial", 8)).grid(row=0, column=0,
                                                                                                    sticky="w",
                                                                                                    padx=10, pady=5)
            self.num_devices_var = tk.StringVar(value="1")
            self.num_devices_dropdown = ttk.Combobox(
                general_config_frame,
                textvariable=self.num_devices_var,
                state="readonly",
                values=[str(i) for i in range(1, 11)],
                width=20,
            )
            self.num_devices_dropdown.grid(row=0, column=1, padx=10, pady=5)
            self.num_devices_dropdown.bind("<<ComboboxSelected>>", self.update_serial_config_frames)
            
            # Reference Coordinates (Ground Truth)
            self.use_reference = tk.BooleanVar(value=False)
            ttk.Checkbutton(general_config_frame, text="Use Custom Reference Point", variable=self.use_reference).grid(
                row=1, column=0, columnspan=2, sticky="w", padx=10, pady=5
            )
            ttk.Label(general_config_frame, text="Latitude:", font=("Arial", 8)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
            self.lat_var = tk.DoubleVar(value=00.0000000)
            ttk.Entry(general_config_frame, textvariable=self.lat_var, width=20).grid(row=2, column=1, padx=10, pady=5)
            ttk.Label(general_config_frame, text="Longitude:", font=("Arial", 8)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
            self.lon_var = tk.DoubleVar(value=00.0000000)
            ttk.Entry(general_config_frame, textvariable=self.lon_var, width=20).grid(row=3, column=1, padx=10, pady=5)


            # Serial Configuration Frame Holder
            self.serial_config_frame_holder = ttk.LabelFrame(self.mode_content, text="Serial Configuration", padding=10)
            self.serial_config_frame_holder.pack(fill="both", padx=10, pady=10)

            # Initialize Serial Configuration Frames
            self.update_serial_config_frames()

        else:
            """Show UI for load file data."""
            self.clear_mode_content()

            # Header
            tk.Label(self.mode_content, text="Live Serial Data", font=("Arial", 18, "bold"), fg="#FE5F55").pack(pady=10)

            # General Configuration
            general_config_frame = ttk.LabelFrame(self.mode_content, text="General Configuration", padding=10)
            general_config_frame.pack(fill="x", padx=10, pady=10)

            # Number of devices
            ttk.Label(general_config_frame, text="Number of Test Devices:", font=("Arial", 8)).grid(row=0, column=0,
                                                                                                    sticky="w",
                                                                                                    padx=10, pady=5)
            self.num_devices_var = tk.DoubleVar(value=1)
            self.num_devices_dropdown = ttk.Combobox(
                general_config_frame,
                textvariable=self.num_devices_var,
                state="readonly",
                values=[str(i) for i in range(1, 11)],
                width=20,
            )
            self.num_devices_dropdown.grid(row=0, column=1, padx=10, pady=5)
            self.num_devices_dropdown.bind("<<ComboboxSelected>>", self.update_serial_config_frames)

            # Serial Configuration Frame Holder
            self.serial_config_frame_holder = ttk.LabelFrame(self.mode_content, text="Serial Configuration", padding=10)
            self.serial_config_frame_holder.pack(fill="both", padx=10, pady=10)

            # Initialize Serial Configuration Frames
            self.update_serial_config_frames()

    def update_serial_config_frames(self, event=None):
        """Update the serial configuration frames based on the selected number of devices."""
        # Clear existing frames
        for widget in self.serial_config_frame_holder.winfo_children():
            widget.destroy()

        # Get the number of devices
        num_devices = int(self.num_devices_var.get())

        # Generate serial config frames
        for device_index in range(1, num_devices + 1):
            config_frame = ttk.LabelFrame(
                self.serial_config_frame_holder, text=f"Device {device_index} Configuration", padding=10
            )
            config_frame.pack(fill="x", padx=10, pady=5)

            # Serial Port
            ttk.Label(config_frame, text="Serial Port:", font=("Arial", 8)).grid(row=0, column=0, sticky="w",
                                                                                 padx=10,
                                                                                 pady=5)
            self.port_var = tk.StringVar(value="Select Port")
            port_dropdown = ttk.Combobox(config_frame, textvariable=self.port_var, state="readonly", width=20)
            port_dropdown.grid(row=0, column=1, padx=10, pady=5)
            self.refresh_serial_ports(port_dropdown)

            # Baudrate
            ttk.Label(config_frame, text="Baudrate:", font=("Arial", 8)).grid(row=1, column=0, sticky="w", padx=10,
                                                                              pady=5)
            self.baudrate_var = tk.DoubleVar(value=115200)
            ttk.Entry(config_frame, textvariable=self.baudrate_var, width=20).grid(row=1, column=1, padx=10, pady=5)

            # Timeout
            ttk.Label(config_frame, text="Timeout (s):", font=("Arial", 8)).grid(row=2, column=0, sticky="w",
                                                                                 padx=10,
                                                                                 pady=5)
            self.timeout_var = tk.DoubleVar(value=1)
            ttk.Entry(config_frame, textvariable=self.timeout_var, width=20).grid(row=2, column=1, padx=10, pady=5)

            # Duration
            ttk.Label(config_frame, text="Duration (s):", font=("Arial", 8)).grid(row=3, column=0, sticky="w",
                                                                                  padx=10,
                                                                                  pady=5)
            self.duration_var = tk.DoubleVar(value=30)
            ttk.Entry(config_frame, textvariable=self.duration_var, width=20).grid(row=3, column=1, padx=10, pady=5)

            # Save device configuration variables
            config_frame.vars = {"port_var": self.port_var, "baudrate_var": self.baudrate_var, "timeout_var": self.timeout_var,
                                 "duration_var": self.duration_var}

        # Start Button
        ttk.Button(self.serial_config_frame_holder, text="Start", command=self.start_live_mode).pack(pady=15)

    @staticmethod
    def refresh_serial_ports(port_dropdown):
        """Refresh the available serial ports."""
        ports = [port.device for port in serial.tools.list_ports.comports()]
        port_dropdown["values"] = ports
        if ports:
            port_dropdown.set(ports[0])  # Default to the first port if available

    def show_file_mode(self):
        """Show UI for log file processing."""
        self.clear_mode_content()

        tk.Label(self.mode_content, text="Load Log File", font=("Arial", 18, "bold"), fg="#0078D7").pack(pady=10)

        file_frame = ttk.LabelFrame(self.mode_content, text="Log File Selection", padding=10)
        file_frame.pack(fill="x", padx=10, pady=10)

        # File Selection
        ttk.Label(file_frame, text="Log File:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.file_var = tk.StringVar(value="Select Log File")
        ttk.Entry(file_frame, textvariable=self.file_var, state="readonly", width=20).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=10, pady=5)

        # Reference Point
        self.use_reference = tk.BooleanVar(value=False)
        ttk.Checkbutton(file_frame, text="Use Custom Reference Point", variable=self.use_reference).grid(
            row=1, column=0, columnspan=3, sticky="w", padx=10, pady=5
        )

        ttk.Label(file_frame, text="Latitude:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.lat_var = tk.DoubleVar(value=0.0000000)
        ttk.Entry(file_frame, textvariable=self.lat_var, width=20).grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(file_frame, text="Longitude:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.lon_var = tk.DoubleVar(value=0.0000000)
        ttk.Entry(file_frame, textvariable=self.lon_var, width=20).grid(row=3, column=1, padx=10, pady=5)

        # Process Button
        ttk.Button(file_frame, text="Process", command=self.process_file_mode).grid(row=4, column=0, columnspan=3, pady=15)

    def start_live_mode(self):
        """Start live data collection."""
        try:
            # Validate port selection
            port = self.port_var.get()
            if port == "Select Port":
                messagebox.showerror("Error", "Please select a valid port.")
                return

            # Validate and convert inputs
            try:
                baudrate = int(self.baudrate_var.get())
                timeout = float(self.timeout_var.get())
                duration = int(self.duration_var.get())
                num_devices = int(self.num_devices_var.get())
                if num_devices < 1 or num_devices > 10:
                    raise ValueError("Number of devices must be between 1 and 10.")
            except ValueError as e:
                messagebox.showerror("Error", f"Invalid input: {e}")
                return

            # Validate reference point if enabled
            if self.use_reference.get():
                try:
                    ref_lat = self.lat_var.get()
                    ref_lon = self.lon_var.get()
                    reference_point = (float(ref_lat), float(ref_lon))
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid reference point: {e}")
                    return
            else:
                reference_point = None

            # Setup logging
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S%f')
            log_folder = f"logs/NMEA_{timestamp}"
            os.makedirs(log_folder, exist_ok=True)
            setup_logging(log_folder, timestamp)

            # Configure devices
            devices = {}
            for i in range(1, num_devices + 1):
                devices[f"device_{i}"] = {
                    "port": port,
                    "baudrate": baudrate,
                    "timeout": timeout,
                    "duration": duration
                }

            # Start data collection threads
            threads = []
            for device_name, config in devices.items():
                try:
                    thread = threading.Thread(
                        target=read_nmea_data,
                        args=(
                            config["port"],
                            config["baudrate"],
                            config["timeout"],
                            config["duration"],
                            log_folder,
                            timestamp,
                            reference_point
                        )
                    )
                    threads.append(thread)
                    thread.start()
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to start thread for {device_name}: {e}")
                    return

            # Wait for all threads to finish
            for thread in threads:
                try:
                    thread.join()
                except Exception as e:
                    messagebox.showerror("Error", f"Error while waiting for threads to finish: {e}")

            messagebox.showinfo("Success", "Data Analysis completed successfully.")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start live test: {e}")

    def process_file_mode(self):
        """Process the selected log file."""
        file_path = self.file_var.get()
        if not os.path.exists(file_path):
            messagebox.showerror("Error", "Invalid file path.")
            return

        reference_point = None
        if self.use_reference.get():
            try:
                ref_lat = float(self.lat_var.get())
                ref_lon = float(self.lon_var.get())
                reference_point = (ref_lat, ref_lon)
            except ValueError:
                messagebox.showerror("Error", "Invalid reference point.")
                return

        process_nmea_log(file_path, reference_point)

    def browse_file(self):
        """Browse and select a log file."""
        file_path = filedialog.askopenfilename(filetypes=[("Log Files", "*.txt *.log *.nmea *.csv *.xlsx")])
        if file_path:
            self.file_var.set(file_path)

    def clear_mode_content(self):
        """Clear the content frame."""
        for widget in self.mode_content.winfo_children():
            widget.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = GNSSTestTool(root)
    root.mainloop()
