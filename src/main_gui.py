import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import serial.tools.list_ports
from datetime import datetime
import os
import threading
from main import read_nmea_data, process_nmea_log, setup_logging

class GNSSTestTool:
    def __init__(self, root):
        self.stop_event = threading.Event()  # Shared flag to stop threads
        self.lon_entry = None
        self.lat_entry = None
        self.tooltip = None
        self.ref_var = None
        self.reference_device_vars = []
        self.reference_device_index = None
        self.result_frame = None
        self.setup_frame = None
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

        # Static/Dynamic Mode Content
        self.mode_content = ttk.Frame(self.root, padding=10)
        # self.mode_content.pack(fill="both", expand=True, padx=15, pady=10)

        # Left Frame for Setup
        self.setup_frame = ttk.Frame(self.root, padding=10)
        self.setup_frame.pack(side="left", fill="both", expand=False, padx=10, pady=10)

        # Right Frame for Console/Result Viewer
        self.result_frame = ttk.Frame(self.root, padding=10)
        self.result_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

    def show_live_mode(self):
        if self.test_type.get() == "Static (fixed reference point)":
            """Show UI for static live serial data setup"""
            self.clear_setup_content()
            self.clear_result_content()

            # Header
            tk.Label(self.setup_frame, text="Live Static Test Setup", font=("Arial", 18, "bold"), fg="#FE5F55").pack(pady=10)

            # General Configuration
            general_config_frame = ttk.LabelFrame(self.setup_frame, text="General Configuration", padding=10)
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
            self.num_devices_dropdown.bind("<<ComboboxSelected>>", self.update_serial_config_static_frames)

            # Reference Coordinates (Ground Truth)
            self.use_reference = tk.BooleanVar(value=False)
            use_reference_checkbox = ttk.Checkbutton(
                general_config_frame,
                text="Use Custom Reference Point",
                variable=self.use_reference,
                command=self.toggle_reference_entries
            )
            use_reference_checkbox.grid(row=1, column=0, sticky="w", padx=10, pady=5)

            # Info Icon with Tooltip
            info_label = tk.Label(general_config_frame, text="?", font=("Arial", 10, "bold"), fg="blue", cursor="hand2")
            info_label.grid(row=1, column=1, sticky="w", padx=5)

            # Bind tooltip to info icon
            info_label.bind("<Enter>", self.show_reference_tooltip)
            info_label.bind("<Leave>", self.hide_reference_tooltip)

            # Latitude Entry
            ttk.Label(general_config_frame, text="Latitude:", font=("Arial", 8)).grid(row=2, column=0, sticky="w",
                                                                                      padx=10, pady=5)
            self.lat_var = tk.DoubleVar(value=0.0000000)
            self.lat_entry = ttk.Entry(general_config_frame, textvariable=self.lat_var, width=20, state="disabled")
            self.lat_entry.grid(row=2, column=1, padx=10, pady=5)

            # Longitude Entry
            ttk.Label(general_config_frame, text="Longitude:", font=("Arial", 8)).grid(row=3, column=0, sticky="w",
                                                                                       padx=10, pady=5)
            self.lon_var = tk.DoubleVar(value=0.0000000)
            self.lon_entry = ttk.Entry(general_config_frame, textvariable=self.lon_var, width=20, state="disabled")
            self.lon_entry.grid(row=3, column=1, padx=10, pady=5)

            # Serial Configuration Frame Holder
            self.serial_config_frame_holder = ttk.LabelFrame(self.setup_frame, text="Serial Configuration", padding=10)
            self.serial_config_frame_holder.pack(fill="both", padx=10, pady=10)

            # Initialize Serial Configuration Frames
            self.update_serial_config_static_frames()

        else:
            """Show UI for load file data."""
            self.clear_setup_content()
            self.clear_result_content()

            # Header
            tk.Label(self.setup_frame, text="Live Dynamic Test Data", font=("Arial", 18, "bold"), fg="#FE5F55").pack(pady=10)

            # General Configuration
            general_config_frame = ttk.LabelFrame(self.setup_frame, text="General Configuration", padding=10)
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
            self.num_devices_dropdown.bind("<<ComboboxSelected>>", self.update_serial_config_dynamic_frames)

            # Serial Configuration Frame Holder
            self.serial_config_frame_holder = ttk.LabelFrame(self.setup_frame, text="Serial Configuration", padding=10)
            self.serial_config_frame_holder.pack(fill="both", padx=10, pady=10)

            # Initialize Serial Configuration Frames
            self.update_serial_config_dynamic_frames()

    def update_serial_config_static_frames(self, event=None):
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
            baudrates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
            self.baudrate_var = tk.IntVar(value=115200)  # Default value
            baudrate_dropdown = ttk.Combobox(
                config_frame,
                textvariable=self.baudrate_var,
                state="readonly",
                values=baudrates,
                width=20
            )
            baudrate_dropdown.grid(row=1, column=1, padx=10, pady=5)

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

        # Frame to hold the buttons
        button_frame = ttk.Frame(self.serial_config_frame_holder)
        button_frame.pack(fill="x", padx=10, pady=15)

        # Add Start Button
        start_button = ttk.Button(button_frame, text="Start Test", command=self.start_live_mode)
        start_button.grid(row=0, column=0, padx=5)

        # Add Stop Button
        stop_button = ttk.Button(button_frame, text="Stop Test", command=self.stop_all_tests)
        stop_button.grid(row=0, column=1, padx=5)

        # Add Clear Button
        clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_all_configs)
        clear_button.grid(row=0, column=2, padx=5)

        # Bind window close to stop tests
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_serial_config_dynamic_frames(self, event=None):
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
            baudrates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
            self.baudrate_var = tk.IntVar(value=115200)  # Default value
            baudrate_dropdown = ttk.Combobox(
                config_frame,
                textvariable=self.baudrate_var,
                state="readonly",
                values=baudrates,
                width=20
            )
            baudrate_dropdown.grid(row=1, column=1, padx=10, pady=5)

            # Timeout
            ttk.Label(config_frame, text="Timeout (s):", font=("Arial", 8)).grid(row=2, column=0, sticky="w",
                                                                                 padx=10,
                                                                                 pady=5)
            self.timeout_var = tk.DoubleVar(value=1)
            ttk.Entry(config_frame, textvariable=self.timeout_var, width=20).grid(row=2, column=1, padx=10, pady=5)

            # Duration
            ttk.Label(config_frame, text="Test Duration (s):", font=("Arial", 8)).grid(row=3, column=0, sticky="w",
                                                                                  padx=10,
                                                                                  pady=5)
            self.duration_var = tk.DoubleVar(value=30)
            ttk.Entry(config_frame, textvariable=self.duration_var, width=20).grid(row=3, column=1, padx=10, pady=5)

            # Reference Device Checkbox
            self.ref_var = tk.BooleanVar(value=(self.reference_device_index == device_index))
            ref_checkbox = ttk.Checkbutton(
                config_frame,
                text="Reference Device",
                variable=self.ref_var,  # Bind the checkbox to this variable
                command=lambda idx=device_index: self.toggle_reference(idx)
            )
            ref_checkbox.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=5)
            # Save device configuration variables
            config_frame.vars = {"port_var": self.port_var, "baudrate_var": self.baudrate_var, "timeout_var": self.timeout_var,
                                 "duration_var": self.duration_var, "ref_var": self.ref_var}

        # Start Button
        ttk.Button(self.serial_config_frame_holder, text="Start", command=self.start_live_mode).pack(pady=15)
        # Add Stop Button
        ttk.Button(self.root, text="Stop Tests", command=self.stop_all_tests).pack(pady=10)
        # Bind window close to stop tests
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

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
            # Reset stop event
            self.stop_event.clear()
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

            # Run the test in a separate thread
            test_thread = threading.Thread(target=self.run_test, args=(devices, log_folder, timestamp, reference_point))
            test_thread.start()

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

    def clear_setup_content(self):
        """Clear the content frame."""
        for widget in self.setup_frame.winfo_children():
            widget.destroy()

    def clear_result_content(self):
        """Clear the content frame."""
        for widget in self.result_frame.winfo_children():
            widget.destroy()

    def toggle_reference(self, selected_index):
        """Ensure only one reference device checkbox can be selected."""
        # Update the reference device index
        if self.reference_device_index == selected_index:
            self.reference_device_index = None  # Deselect if the same device is clicked again
        else:
            self.reference_device_index = selected_index  # Set the new reference device

        # Refresh frames to update the checkboxes
        self.update_serial_config_dynamic_frames()

        # Log reference device selection
        print(f"Selected reference device: {self.reference_device_index or 'None'}")

    def toggle_reference_entries(self):
        """Enable or disable latitude and longitude entries based on the use_reference checkbox."""
        if self.use_reference.get():
            self.lat_entry.config(state="normal")
            self.lon_entry.config(state="normal")
        else:
            self.lat_entry.config(state="disabled")
            self.lon_entry.config(state="disabled")

    def show_reference_tooltip(self, event):
        """Display tooltip for the 'Use Custom Reference Point' info icon."""
        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip.geometry(f"+{event.x_root + 10}+{event.y_root + 10}")  # Position near cursor

        label = tk.Label(
            self.tooltip,
            text="If no custom reference point is used, the CEP is calculated using the average of all test points as the reference.",
            justify="left",
            background="#ffffe0",  # Light yellow background
            relief="solid",
            borderwidth=1,
            font=("Arial", 10)
        )
        label.pack(ipadx=5, ipady=5)

    def hide_reference_tooltip(self, event):
        """Hide the tooltip for the info icon."""
        if hasattr(self, "tooltip") and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def run_test(self, devices, log_folder, timestamp, reference_point):
        """Run the test on a separate thread."""
        try:
            threads = []
            for device_name, config in devices.items():
                thread = threading.Thread(
                    target=read_nmea_data,
                    args=(config["port"], config["baudrate"], config["timeout"], config["duration"],
                          log_folder, timestamp, reference_point, self.stop_event)  # Pass stop_event
                )
                threads.append(thread)
                thread.start()

            # Wait for threads to finish
            for thread in threads:
                thread.join()

            # Notify the user if not stopped
            if not self.stop_event.is_set():
                messagebox.showinfo("Success", "Data Analysis completed successfully.")

        except Exception as e:
            if not self.stop_event.is_set():  # Avoid showing errors if the stop button was clicked
                messagebox.showerror("Error", f"An error occurred during the test: {e}")

    def stop_all_tests(self):
        """Stop all running tests."""
        if messagebox.askyesno("Confirm Stop", "Are you sure you want to stop all running tests?"):
            self.stop_event.set()  # Signal threads to stop
            messagebox.showinfo("Stop action completed","All tests have been stopped.")
            print("All tests stopped.")
        else:
            messagebox.showinfo("Stop action canceled","Stop action canceled by the user.")
            print("Stop action canceled.")

    def on_close(self):
        """Handle window close."""
        if messagebox.askyesno("Quit", "Are you sure you want to quit and stop all running tests?"):
            self.stop_all_tests()  # Stop all threads
            self.root.destroy()  # Close the application
        else:
            messagebox.showinfo("Close action canceled","Window close action canceled by the user.")
            print("Window close action canceled.")

    def clear_all_configs(self):
        """Reset all configurations to their default values."""
        try:
            # Reset number of devices
            if self.num_devices_var:
                self.num_devices_var.set("1")  # Default to 1 device

            # Reset reference point settings
            if self.use_reference:
                self.use_reference.set(False)  # Uncheck 'Use Custom Reference Point'
                self.toggle_reference_entries()  # Disable lat/lon entries

            if self.lat_var:
                self.lat_var.set(0.0)  # Reset latitude
            if self.lon_var:
                self.lon_var.set(0.0)  # Reset longitude

            # Reset Serial Configuration fields
            if self.port_var:
                self.port_var.set("Select Port")  # Default port option
            if self.baudrate_var:
                self.baudrate_var.set(115200)  # Default baudrate
            if self.timeout_var:
                self.timeout_var.set(1.0)  # Default timeout
            if self.duration_var:
                self.duration_var.set(30.0)  # Default duration

            # Clear the serial configuration frame holder
            for widget in self.serial_config_frame_holder.winfo_children():
                widget.destroy()

            # Reinitialize serial configuration frames
            self.update_serial_config_static_frames()
            messagebox.showinfo("Clear", "All configurations have been reset.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while clearing configurations: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = GNSSTestTool(root)
    root.mainloop()
