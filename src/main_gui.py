import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import logging
import serial.tools.list_ports
from datetime import datetime
import os
import threading
import sys
from time import time
from gui_class import NMEAData
import pynmea2
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import datetime
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk

class GNSSTestTool:
    def __init__(self, root):
        self.mode = None
        self.file_config_frame_holder = None
        self.results_frame_content = None
        self.satellite_table_data = None
        self.satellite_summary_table = None
        self.satellite_analysis_placeholder = None
        self.satellite_analysis_frame = None
        self.satellite_tab = None
        self.toolbar = None
        self.accuracy_tab = None
        self.device_plot_data = {}  # To store fix_times, distances, and device_name for all devices
        self.canvas_widget = None
        self.canvas = None
        self.accuracy_graph_placeholder = None
        self.accuracy_summary_table = None
        self.accuracy_summary_frame = None
        self.accuracy_graph_frame = None
        self.fig, self.ax = plt.subplots(figsize=(6, 4))  # Create a Matplotlib figure
        self.accuracy_table_data = {}  # To store summary table rows for all devices
        self.duration_vars = None
        self.timeout_vars = None
        self.baudrate_vars = None
        self.port_vars = None
        self.device_notebook = None
        self.results_notebook = None
        self.console_text = None
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
        self.test_type = None
        self.root = root
        self.root.title("GNSS Test Tool")
        # Set the window to almost fullscreen
        self.root.geometry(f"{root.winfo_screenwidth() - 50}x{root.winfo_screenheight() - 50}")
        # Exit fullscreen with Escape key
        self.root.bind("<Escape>", lambda e: root.attributes('-fullscreen', False))
        self.root.configure(bg="#B8D8D8")  # Background color
        self.create_widgets()

    def create_widgets(self):
        # Configure root grid layout
        self.root.grid_rowconfigure(0, weight=1)  # Row 0 (Test Config) gets 10% height
        self.root.grid_rowconfigure(1, weight=9)  # Row 1 (Test Setup) gets 90% height
        self.root.grid_columnconfigure(0, weight=1)  # Col 1 (left side)
        self.root.grid_columnconfigure(1, weight=9)  # Col 2 (right side)

        # Combined Frame for Test Type and Mode Selection (Col 1, Row 0)
        combined_frame = ttk.LabelFrame(self.root, text="General Configuration", padding=10)
        combined_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Configure rows and columns inside combined_frame for alignment
        combined_frame.grid_rowconfigure(0, weight=1)  # Row for Test Type
        combined_frame.grid_rowconfigure(1, weight=1)  # Row for Test Mode
        combined_frame.grid_columnconfigure(0, weight=1)  # Label columns
        combined_frame.grid_columnconfigure(1, weight=1)  # Input widgets/buttons

        # Test Type inside the combined frame
        ttk.Label(combined_frame, text="Test Type:", font=("Arial", 10)).grid(
            row=0, column=0, padx=10, pady=5, sticky="w"
        )
        self.test_type = tk.StringVar(value="Static (fixed reference point)")
        ttk.Combobox(
            combined_frame, textvariable=self.test_type,
            values=["Static (fixed reference point)", "Dynamic (moving reference point)"],
            state="readonly", width=25
        ).grid(row=0, column=1, padx=10, pady=0, sticky="w")

        # Test Mode inside the combined frame
        ttk.Label(combined_frame, text="Test Mode:", font=("Arial", 10)).grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        button_frame = ttk.Frame(combined_frame)  # Frame to group buttons closer together
        button_frame.grid(row=1, column=1, sticky="w")
        ttk.Button(button_frame, text="Process Live Data", command=self.show_live_mode).pack(
            side="left", padx=5, pady=5
        )
        ttk.Button(button_frame, text="Process Log File", command=self.show_file_mode).pack(
            side="left", padx=5, pady=5
        )

        # Setup Frame (Col 1, Row 1) with Scrollbar
        setup_frame_container = ttk.LabelFrame(self.root, text="Test Setup", padding=10)
        setup_frame_container.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        setup_canvas = tk.Canvas(setup_frame_container)
        setup_scrollbar = ttk.Scrollbar(setup_frame_container, orient="vertical", command=setup_canvas.yview)
        self.setup_frame = ttk.Frame(setup_canvas)  # Actual frame for content

        # Configure canvas and scrollbar
        self.setup_frame.bind(
            "<Configure>",
            lambda e: setup_canvas.configure(scrollregion=setup_canvas.bbox("all"))
        )
        setup_canvas.create_window((0, 0), window=self.setup_frame, anchor="nw")
        setup_canvas.configure(yscrollcommand=setup_scrollbar.set)

        # Pack canvas and scrollbar
        setup_canvas.pack(side="left", fill="both", expand=True)
        setup_scrollbar.pack(side="right", fill="y")

        ttk.Label(self.setup_frame, text="Select Test Type and mode to configure").pack(padx=10, pady=10)

        # Create the Results Frame
        self.result_frame = ttk.LabelFrame(self.root, text="Results", padding=10)
        self.result_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=10, pady=10)

        # Add Canvas and Scrollbar to Results Frame
        result_canvas = tk.Canvas(self.result_frame)
        result_scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=result_canvas.yview)
        self.results_frame_content = ttk.Frame(result_canvas)  # Frame for Results content

        # Configure the canvas and scrollbar
        self.results_frame_content.bind(
            "<Configure>",
            lambda e: result_canvas.configure(scrollregion=result_canvas.bbox("all"))
        )

        # Dynamically update the width of the content frame to match the canvas
        result_canvas.bind(
            "<Configure>",
            lambda e: result_canvas.itemconfig("content", width=e.width)
        )

        result_canvas.create_window((0, 0), window=self.results_frame_content, anchor="nw", tags="content")
        result_canvas.configure(yscrollcommand=result_scrollbar.set)

        # Pack the canvas and scrollbar
        result_canvas.pack(side="left", fill="both", expand=True)
        result_scrollbar.pack(side="right", fill="y")

        # Create a Notebook (Tab container) within the Results Frame content
        self.results_notebook = ttk.Notebook(self.results_frame_content)
        self.results_notebook.pack(fill="both", expand=True)

        # Style configuration for Notebook Tabs
        style = ttk.Style()
        style.configure(
            "TNotebook.Tab",
            background="#8FA3A3",  # Darker background for better contrast
            foreground="black",  # Black text
        )

        # Configure the appearance of the selected tab
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#2A6EBB")],
            foreground=[("selected", "#FE5F55")],
        )

        # General Console Tab
        console_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(console_tab, text="Console/Logs")

        # Nested Notebook for Device Logs
        self.device_notebook = ttk.Notebook(console_tab)  # Nested notebook for device-specific logs
        self.device_notebook.pack(fill="both", expand=True)

        # Accuracy Tab
        self.accuracy_tab = ttk.Frame(self.results_notebook)
        self.results_notebook.add(self.accuracy_tab, text="Statistics")

        # Accuracy Content (Graphs)
        self.accuracy_graph_frame = ttk.LabelFrame(self.accuracy_tab, text="Precision/Accuracy Summary")
        self.accuracy_graph_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.accuracy_graph_placeholder = ttk.Label(self.accuracy_graph_frame,
                                                    text="Accuracy graph will be displayed here after completion of all active tests.")
        self.accuracy_graph_placeholder.pack(padx=20, pady=20)

        # Initialize the canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.accuracy_graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        # Accuracy Summary (CEP Table)
        accuracy_summary_frame = ttk.LabelFrame(self.accuracy_tab, text="CEP Summary")
        accuracy_summary_frame.pack(fill="x", padx=10, pady=10)

        # Initialize the summary table inside the accuracy_summary_frame
        columns = ["Device", "Fixes", "CEP50 (m)", "CEP68 (m)", "CEP95 (m)", "CEP99 (m)", "Reference Point"]
        self.accuracy_summary_table = ttk.Treeview(accuracy_summary_frame, columns=columns, show="headings")

        # Configure columns and headings
        for col in columns:
            self.accuracy_summary_table.heading(col, text=col)
            self.accuracy_summary_table.column(col, anchor="center", width=120)

        # Pack the Treeview widget
        self.accuracy_summary_table.pack(fill="x", expand=True)

        # Initialize the dictionary to track device rows in the summary table
        self.accuracy_table_data = {}

        # Satellite Summary (CEP Table)
        satellite_summary_frame = ttk.LabelFrame(self.accuracy_tab, text="Satellite Signal Strength Summary")
        satellite_summary_frame.pack(fill="x", padx=10, pady=10)

        # Initialize the summary table inside the satellite_summary_frame
        columns = ["Device", "Average Satellites CNR (dB)", "Minimum Satellites CNR (dB)",
                   "Maximum Satellites CNR (dB)", "Total Satellites in View"]
        self.satellite_summary_table = ttk.Treeview(satellite_summary_frame, columns=columns, show="headings")

        # Configure columns and headings
        for col in columns:
            self.satellite_summary_table.heading(col, text=col)
            self.satellite_summary_table.column(col, anchor="center", width=120)

        # Pack the Treeview widget
        self.satellite_summary_table.pack(fill="x", expand=True)

        # Initialize the dictionary to track device rows in the summary table
        self.satellite_table_data = {}

    def show_live_mode(self):
        if self.test_type.get() == "Static (fixed reference point)":
            self.mode = "live static"
            """Show UI for static live serial data setup"""
            self.clear_setup_content()

            # Header
            tk.Label(self.setup_frame, text="Live Static Test Setup", font=("Arial", 14, "bold"), fg="#FE5F55").pack(pady=5, padx=5)

            # General Configuration
            general_config_frame = ttk.LabelFrame(self.setup_frame, text="General Configuration", padding=10)
            general_config_frame.pack(fill="x", padx=10, pady=10)

            # Number of devices
            ttk.Label(general_config_frame, text="Number of Test Devices:", font=("Arial", 10)).grid(row=0, column=0,
                                                                                                    sticky="w",
                                                                                                    padx=5, pady=5)
            self.num_devices_var = tk.StringVar(value="1")
            self.num_devices_dropdown = ttk.Combobox(
                general_config_frame,
                textvariable=self.num_devices_var,
                state="readonly",
                values=[str(i) for i in range(1, 11)],
                width=10,
            )
            self.num_devices_dropdown.grid(row=0, column=1, padx=10, pady=5)
            self.num_devices_dropdown.bind("<<ComboboxSelected>>", self.update_serial_config_static_frames)

            # Reference Coordinates (Ground Truth)
            self.use_reference = tk.BooleanVar(value=False)
            use_reference_checkbox = ttk.Checkbutton(
                general_config_frame,
                text="Use Custom Reference Point",
                variable=self.use_reference,
                command=self.toggle_reference_entries,
            )
            use_reference_checkbox.grid(row=1, column=0, sticky="w", padx=10, pady=5)

            # Info Icon with Tooltip
            info_label = tk.Label(general_config_frame, text="?", font=("Arial", 10, "bold"), fg="#FE5F55", cursor="hand2")
            info_label.grid(row=1, column=1, sticky="w", padx=5)

            # Bind tooltip to info icon
            info_label.bind("<Enter>", self.show_reference_tooltip)
            info_label.bind("<Leave>", self.hide_reference_tooltip)

            # Latitude Entry
            ttk.Label(general_config_frame, text="Latitude:", font=("Arial", 10)).grid(row=2, column=0, sticky="w",
                                                                                      padx=10, pady=5)
            self.lat_var = tk.DoubleVar(value=0.0000000)
            self.lat_entry = ttk.Entry(general_config_frame, textvariable=self.lat_var, width=20, state="disabled")
            self.lat_entry.grid(row=2, column=1, padx=10, pady=5)

            # Longitude Entry
            ttk.Label(general_config_frame, text="Longitude:", font=("Arial", 10)).grid(row=3, column=0, sticky="w",
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
            self.mode = "live dynamic"
            """Show UI for load file data."""
            self.clear_setup_content()

            # Header
            tk.Label(self.setup_frame, text="Live Dynamic Test Data", font=("Arial", 14, "bold"), fg="#FE5F55").pack(pady=5, padx=5)

            # General Configuration
            general_config_frame = ttk.LabelFrame(self.setup_frame, text="Device Configuration", padding=10)
            general_config_frame.pack(fill="x", padx=10, pady=10)

            # Number of devices
            ttk.Label(general_config_frame, text="Number of Test Devices:", font=("Arial", 10)).grid(row=0, column=0,
                                                                                                    sticky="w",
                                                                                                    padx=10, pady=5)
            self.num_devices_var = tk.DoubleVar(value=1)
            self.num_devices_dropdown = ttk.Combobox(
                general_config_frame,
                textvariable=self.num_devices_var,
                state="readonly",
                values=[str(i) for i in range(1, 11)],
                width=10,
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

        # Initialize a list to store individual device port configurations
        self.port_vars = [tk.StringVar(value="Select Port") for _ in range(num_devices)]
        self.baudrate_vars = [tk.IntVar(value=115200) for _ in range(num_devices)]
        self.timeout_vars = [tk.DoubleVar(value=1) for _ in range(num_devices)]
        self.duration_vars = [tk.DoubleVar(value=30) for _ in range(num_devices)]

        # Generate serial config frames
        for device_index in range(1, num_devices + 1):
            config_frame = ttk.LabelFrame(
                self.serial_config_frame_holder, text=f"Device {device_index} Configuration", padding=10
            )
            config_frame.pack(fill="x", padx=10, pady=5)

            # Serial Port
            ttk.Label(config_frame, text="Serial Port:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=10,
                                                                                  pady=5)
            port_dropdown = ttk.Combobox(
                config_frame,
                textvariable=self.port_vars[device_index - 1],  # Use individual port variable
                state="readonly",
                width=30,
                font=("Arial", 10)
            )
            port_dropdown.grid(row=0, column=1, padx=10, pady=5)
            self.refresh_serial_ports(port_dropdown)  # Populate port dropdown options

            # Baudrate
            ttk.Label(config_frame, text="Baudrate:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=10,
                                                                               pady=5)
            baudrates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
            baudrate_dropdown = ttk.Combobox(
                config_frame,
                textvariable=self.baudrate_vars[device_index - 1],  # Use individual baudrate variable
                state="readonly",
                values=baudrates,
                width=30,
                font=("Arial", 10)
            )
            baudrate_dropdown.grid(row=1, column=1, padx=10, pady=5)

            # Timeout
            ttk.Label(config_frame, text="Timeout (s):", font=("Arial", 10)).grid(row=2, column=0, sticky="w", padx=10,
                                                                                  pady=5)
            ttk.Entry(
                config_frame,
                textvariable=self.timeout_vars[device_index - 1],  # Use individual timeout variable
                width=30,
                font=("Arial", 10)
            ).grid(row=2, column=1, padx=10, pady=5)

            # Duration
            ttk.Label(config_frame, text="Duration (s):", font=("Arial", 10)).grid(row=3, column=0, sticky="w", padx=10,
                                                                                   pady=5)
            ttk.Entry(
                config_frame,
                textvariable=self.duration_vars[device_index - 1],  # Use individual duration variable
                width=30,
                font=("Arial", 10)
            ).grid(row=3, column=1, padx=10, pady=5)

            # Save device configuration variables
            config_frame.vars = {
                "port_var": self.port_vars[device_index - 1],
                "baudrate_var": self.baudrate_vars[device_index - 1],
                "timeout_var": self.timeout_vars[device_index - 1],
                "duration_var": self.duration_vars[device_index - 1],
                "device_index": device_index
            }

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
            ttk.Label(config_frame, text="Serial Port:", font=("Arial", 10)).grid(row=0, column=0, sticky="w",
                                                                                 padx=10,
                                                                                 pady=5)
            self.port_var = tk.StringVar(value="Select Port")
            port_dropdown = ttk.Combobox(config_frame, textvariable=self.port_var, state="readonly", width=30, font=("Arial", 10)
)
            port_dropdown.grid(row=0, column=1, padx=10, pady=5)
            self.refresh_serial_ports(port_dropdown)

            # Baudrate
            ttk.Label(config_frame, text="Baudrate:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=10,
                                                                              pady=5)
            baudrates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
            self.baudrate_var = tk.IntVar(value=115200)  # Default value
            baudrate_dropdown = ttk.Combobox(
                config_frame,
                textvariable=self.baudrate_var,
                state="readonly",
                values=baudrates,
                width=30,
                font=("Arial", 10)
            )
            baudrate_dropdown.grid(row=1, column=1, padx=10, pady=5)

            # Timeout
            ttk.Label(config_frame, text="Timeout (s):", font=("Arial", 10)).grid(row=2, column=0, sticky="w",
                                                                                 padx=10,
                                                                                 pady=5)
            self.timeout_var = tk.DoubleVar(value=1)
            ttk.Entry(config_frame, textvariable=self.timeout_var, width=30, font=("Arial", 10)).grid(row=2, column=1, padx=10, pady=5)

            # Duration
            ttk.Label(config_frame, text="Duration (s):", font=("Arial", 10)).grid(row=3, column=0, sticky="w",
                                                                                  padx=10,
                                                                                  pady=5)
            self.duration_var = tk.DoubleVar(value=30)
            ttk.Entry(config_frame, textvariable=self.duration_var, width=30, font=("Arial", 10)).grid(row=3, column=1, padx=10, pady=5)

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
                                 "duration_var": self.duration_var, "ref_var": self.ref_var, "device_index": device_index, "ref_checkbox": ref_checkbox}

        # Frame to hold the buttons
        button_frame = ttk.Frame(self.serial_config_frame_holder)
        button_frame.pack(fill="x", padx=10, pady=15)

        # Add Start Button
        start_button = ttk.Button(button_frame, text="Start Test", command=self.start_live_mode_2)
        start_button.grid(row=0, column=0, padx=5)

        # Add Stop Button
        stop_button = ttk.Button(button_frame, text="Stop Test", command=self.stop_all_tests)
        stop_button.grid(row=0, column=1, padx=5)

        # Add Clear Button
        clear_button = ttk.Button(button_frame, text="Clear Settings", command=self.clear_all_configs)
        clear_button.grid(row=0, column=2, padx=5)

        # Bind window close to stop tests
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    @staticmethod
    def refresh_serial_ports(port_dropdown):
        """Refresh the available serial ports with detailed information."""
        # Get list of ports with descriptions
        ports = serial.tools.list_ports.comports()
        port_list = [f"{port.device}" for port in ports]

        # Update the dropdown menu
        port_dropdown["values"] = port_list

        # Set the first port as default if available
        if port_list:
            port_dropdown.set(port_list[0])
        else:
            port_dropdown.set("No ports available")

    def show_file_mode(self):
        if self.test_type.get() == "Static (fixed reference point)":
            self.mode = "file static"
            self.show_static_file_mode()
        else:
            self.mode = "file dynamic"
            self.show_dynamic_file_mode()

    def show_static_file_mode(self):

        """Show UI for static file serial data setup"""

        self.clear_setup_content()

        # Header
        tk.Label(self.setup_frame, text="Load Static Test Files", font=("Arial", 14, "bold"), fg="#FE5F55").pack(pady=5,
                                                                                                                 padx=5)

        # General Configuration
        general_config_frame = ttk.LabelFrame(self.setup_frame, text="General Configuration", padding=10)
        general_config_frame.pack(fill="x", padx=10, pady=10)

        # Number of devices
        ttk.Label(general_config_frame, text="Number of Test logs:", font=("Arial", 10)).grid(row=0, column=0,
                                                                                                 sticky="w",
                                                                                                 padx=5, pady=5)
        self.num_devices_var = tk.StringVar(value="1")
        self.num_devices_dropdown = ttk.Combobox(
            general_config_frame,
            textvariable=self.num_devices_var,
            state="readonly",
            values=[str(i) for i in range(1, 11)],
            width=10,
        )
        self.num_devices_dropdown.grid(row=0, column=1, padx=10, pady=5)
        self.num_devices_dropdown.bind("<<ComboboxSelected>>", self.update_file_config_static_frames)

        # Reference Coordinates (Ground Truth)
        self.use_reference = tk.BooleanVar(value=False)
        use_reference_checkbox = ttk.Checkbutton(
            general_config_frame,
            text="Use Custom Reference Point",
            variable=self.use_reference,
            command=self.toggle_reference_entries,
        )
        use_reference_checkbox.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        # Info Icon with Tooltip
        info_label = tk.Label(general_config_frame, text="?", font=("Arial", 10, "bold"), fg="#FE5F55", cursor="hand2")
        info_label.grid(row=1, column=1, sticky="w", padx=5)

        # Bind tooltip to info icon
        info_label.bind("<Enter>", self.show_reference_tooltip)
        info_label.bind("<Leave>", self.hide_reference_tooltip)

        # Latitude Entry
        ttk.Label(general_config_frame, text="Latitude:", font=("Arial", 10)).grid(row=2, column=0, sticky="w",
                                                                                   padx=10, pady=5)
        self.lat_var = tk.DoubleVar(value=0.0000000)
        self.lat_entry = ttk.Entry(general_config_frame, textvariable=self.lat_var, width=20, state="disabled")
        self.lat_entry.grid(row=2, column=1, padx=10, pady=5)

        # Longitude Entry
        ttk.Label(general_config_frame, text="Longitude:", font=("Arial", 10)).grid(row=3, column=0, sticky="w",
                                                                                    padx=10, pady=5)
        self.lon_var = tk.DoubleVar(value=0.0000000)
        self.lon_entry = ttk.Entry(general_config_frame, textvariable=self.lon_var, width=20, state="disabled")
        self.lon_entry.grid(row=3, column=1, padx=10, pady=5)

        # File Configuration Frame Holder
        self.file_config_frame_holder = ttk.LabelFrame(self.setup_frame, text="Logfile Configuration", padding=10)
        self.file_config_frame_holder.pack(fill="both", padx=10, pady=10)

        # Initialize Serial Configuration Frames
        self.update_file_config_static_frames()

    def update_file_config_static_frames(self, event=None):
        """Update the file configuration frames based on the selected number of devices."""

        # Clear existing frames
        for widget in self.file_config_frame_holder.winfo_children():
            widget.destroy()

        # Get the number of devices
        num_devices = int(self.num_devices_var.get())

        # Initialize a list to store individual file configurations
        self.file_var = [tk.StringVar(value="Select Log File") for _ in range(num_devices)]

        # Generate file config frames
        for device_index in range(1, num_devices + 1):
            config_frame = ttk.LabelFrame(
                self.file_config_frame_holder, text=f"Device {device_index} File Configuration", padding=10
            )
            config_frame.pack(fill="x", padx=10, pady=5)

            # File Path Selection
            ttk.Label(config_frame, text="Log File:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=10,
                                                                               pady=5)
            ttk.Entry(
                config_frame,
                textvariable=self.file_var[device_index - 1],  # Use individual file variable
                state="readonly",
                width=30,
                font=("Arial", 10)
            ).grid(row=0, column=1, padx=10, pady=5)

            ttk.Button(
                config_frame,
                text="Browse",
                command=lambda idx=device_index - 1: self.browse_file(idx)
            ).grid(row=0, column=2, padx=10, pady=5)

        # Frame to hold the buttons
        button_frame = ttk.Frame(self.file_config_frame_holder)
        button_frame.pack(fill="x", padx=10, pady=15)

        # Add Start Button
        start_button = ttk.Button(button_frame, text="Start Test", command=self.start_file_mode)
        start_button.grid(row=0, column=0, padx=5)

        # Add Stop Button
        stop_button = ttk.Button(button_frame, text="Stop Test", command=self.stop_all_tests)
        stop_button.grid(row=0, column=1, padx=5)

        # Add Clear Button
        clear_button = ttk.Button(button_frame, text="Clear", command=self.clear_all_configs)
        clear_button.grid(row=0, column=2, padx=5)

        # Bind window close to stop tests
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def update_file_config_dynamic_frames(self, event=None):
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
                ttk.Label(config_frame, text="Serial Port:", font=("Arial", 10)).grid(row=0, column=0, sticky="w",
                                                                                      padx=10,
                                                                                      pady=5)
                self.port_var = tk.StringVar(value="Select Port")
                port_dropdown = ttk.Combobox(config_frame, textvariable=self.port_var, state="readonly", width=30,
                                             font=("Arial", 10)
                                             )
                port_dropdown.grid(row=0, column=1, padx=10, pady=5)
                self.refresh_serial_ports(port_dropdown)

                # Baudrate
                ttk.Label(config_frame, text="Baudrate:", font=("Arial", 10)).grid(row=1, column=0, sticky="w", padx=10,
                                                                                   pady=5)
                baudrates = ["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"]
                self.baudrate_var = tk.IntVar(value=115200)  # Default value
                baudrate_dropdown = ttk.Combobox(
                    config_frame,
                    textvariable=self.baudrate_var,
                    state="readonly",
                    values=baudrates,
                    width=30,
                    font=("Arial", 10)
                )
                baudrate_dropdown.grid(row=1, column=1, padx=10, pady=5)

                # Timeout
                ttk.Label(config_frame, text="Timeout (s):", font=("Arial", 10)).grid(row=2, column=0, sticky="w",
                                                                                      padx=10,
                                                                                      pady=5)
                self.timeout_var = tk.DoubleVar(value=1)
                ttk.Entry(config_frame, textvariable=self.timeout_var, width=30, font=("Arial", 10)).grid(row=2,
                                                                                                          column=1,
                                                                                                          padx=10,
                                                                                                          pady=5)

                # Duration
                ttk.Label(config_frame, text="Duration (s):", font=("Arial", 10)).grid(row=3, column=0, sticky="w",
                                                                                       padx=10,
                                                                                       pady=5)
                self.duration_var = tk.DoubleVar(value=30)
                ttk.Entry(config_frame, textvariable=self.duration_var, width=30, font=("Arial", 10)).grid(row=3,
                                                                                                           column=1,
                                                                                                           padx=10,
                                                                                                           pady=5)

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
                config_frame.vars = {"port_var": self.port_var, "baudrate_var": self.baudrate_var,
                                     "timeout_var": self.timeout_var,
                                     "duration_var": self.duration_var, "ref_var": self.ref_var,
                                     "device_index": device_index, "ref_checkbox": ref_checkbox}

            # Frame to hold the buttons
            button_frame = ttk.Frame(self.serial_config_frame_holder)
            button_frame.pack(fill="x", padx=10, pady=15)

            # Add Start Button
            start_button = ttk.Button(button_frame, text="Start Test", command=self.start_file_mode)
            start_button.grid(row=0, column=0, padx=5)

            # Add Stop Button
            stop_button = ttk.Button(button_frame, text="Stop Test", command=self.stop_all_tests)
            stop_button.grid(row=0, column=1, padx=5)

            # Add Clear Button
            clear_button = ttk.Button(button_frame, text="Clear Settings", command=self.clear_all_configs)
            clear_button.grid(row=0, column=2, padx=5)

            # Bind window close to stop tests
            self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def show_dynamic_file_mode(self):

        self.clear_setup_content()

        """Show UI for log file processing."""

        # Header
        tk.Label(self.setup_frame, text="Load Static Test Data", font=("Arial", 14, "bold"), fg="#FE5F55").pack(pady=5, padx=5)
        file_frame = ttk.LabelFrame(self.setup_frame, text="Log File Selection", padding=10)
        file_frame.pack(fill="x", padx=10, pady=10)

        # File Selection
        ttk.Label(file_frame, text="Log File:", font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.file_var = tk.StringVar(value="Select Log File")
        ttk.Entry(file_frame, textvariable=self.file_var, state="readonly", width=20).grid(row=0, column=1, padx=10, pady=5)
        ttk.Button(file_frame, text="Browse", command=self.browse_file).grid(row=0, column=2, padx=10, pady=5)

        # Reference Coordinates (Ground Truth)
        self.use_reference = tk.BooleanVar(value=False)
        use_reference_checkbox = ttk.Checkbutton(
            file_frame,
            text="Use Custom Reference Point",
            variable=self.use_reference,
            command=self.toggle_reference_entries,
        )
        use_reference_checkbox.grid(row=1, column=0, sticky="w", padx=10, pady=5)

        # Info Icon with Tooltip
        info_label = tk.Label(file_frame, text="?", font=("Arial", 10, "bold"), fg="#FE5F55", cursor="hand2")
        info_label.grid(row=1, column=1, sticky="w", padx=5)

        # Bind tooltip to info icon
        info_label.bind("<Enter>", self.show_reference_tooltip)
        info_label.bind("<Leave>", self.hide_reference_tooltip)

        # Latitude Entry
        ttk.Label(file_frame, text="Latitude:", font=("Arial", 10)).grid(row=2, column=0, sticky="w",
                                                                                    padx=10, pady=5)
        self.lat_var = tk.DoubleVar(value=0.0000000)
        self.lat_entry = ttk.Entry(file_frame, textvariable=self.lat_var, width=20, state="disabled")
        self.lat_entry.grid(row=2, column=1, padx=10, pady=5)

        # Longitude Entry
        ttk.Label(file_frame, text="Longitude:", font=("Arial", 10)).grid(row=3, column=0, sticky="w",
                                                                                    padx=10, pady=5)
        self.lon_var = tk.DoubleVar(value=0.0000000)
        self.lon_entry = ttk.Entry(file_frame, textvariable=self.lon_var, width=20, state="disabled")
        self.lon_entry.grid(row=3, column=1, padx=10, pady=5)

        # Process Button
        ttk.Button(file_frame, text="Process", command=self.start_file_mode).grid(row=4, column=0, columnspan=3, pady=15)

    def start_live_mode(self):
        """Start live data collection."""
        self.mode = "live static"
        try:
            # Reset stop event
            self.stop_event.clear()

            # Validate port selection for each device
            num_devices = len(self.port_vars)  # Ensure the number of devices matches
            devices = {}
            for i in range(num_devices):
                port = self.port_vars[i].get()
                if port == "Select Port" or port == "No ports available":
                    messagebox.showerror("Error", f"Please select a valid port for Device {i + 1}.")
                    return

                # Gather configuration for the device
                try:
                    baudrate = int(self.baudrate_vars[i].get())
                    timeout = float(self.timeout_vars[i].get())
                    duration = int(self.duration_vars[i].get())
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid input for Device {i + 1}: {e}")
                    return

                # Add device configuration to the dictionary
                devices[f"device_{i + 1}"] = {
                    "name": f"Device {i + 1}",
                    "port": port,
                    "baudrate": baudrate,
                    "timeout": timeout,
                    "duration": duration
                }

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

            self.fresh_start()

            # Setup logging
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')
            log_folder = f"logs/NMEA_{timestamp}"
            os.makedirs(log_folder, exist_ok=True)
            self.setup_logging(log_folder, timestamp)

            # Run the test in a separate thread
            test_thread = threading.Thread(
                target=self.run_live_test, args=(devices, log_folder, timestamp, reference_point)
            )
            test_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start live test: {e}")
            logging.error(f"Failed to start live test: {e}")

    def start_live_mode_2(self):
        """Start live data collection."""
        self.mode = "live dynamic"
        try:
            # Reset stop event
            self.stop_event.clear()

            # Validate port selection for each device
            num_devices = len(self.port_vars)  # Ensure the number of devices matches
            devices = {}
            for i in range(num_devices):
                port = self.port_vars[i].get()
                if port == "Select Port" or port == "No ports available":
                    messagebox.showerror("Error", f"Please select a valid port for Device {i + 1}.")
                    return

                # Gather configuration for the device
                try:
                    baudrate = int(self.baudrate_vars[i].get())
                    timeout = float(self.timeout_vars[i].get())
                    duration = int(self.duration_vars[i].get())
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid input for Device {i + 1}: {e}")
                    return

                # Add device configuration to the dictionary
                devices[f"device_{i + 1}"] = {
                    "name": f"Device {i + 1}",
                    "port": port,
                    "baudrate": baudrate,
                    "timeout": timeout,
                    "duration": duration
                }

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

            self.fresh_start()

            # Setup logging
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')
            log_folder = f"logs/NMEA_{timestamp}"
            os.makedirs(log_folder, exist_ok=True)
            self.setup_logging(log_folder, timestamp)

            # Run the test in a separate thread
            test_thread = threading.Thread(
                target=self.run_live_test, args=(devices, log_folder, timestamp, reference_point)
            )
            test_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start live test: {e}")
            logging.error(f"Failed to start live test: {e}")

    def start_file_mode(self):
        """Process the selected log files."""
        self.mode = "file static"
        try:
            # Reset stop event
            self.stop_event.clear()
            self.fresh_start()
            # Validate file path selection
            if int(self.num_devices_var.get()) != len(self.file_var):
                messagebox.showerror("Error", "Please provide the same number of log files indicated in the general config section.")# Ensure the number of selected logfiles matches the selected number
            else:
                pass
            devices = {}
            for i in range(int(self.num_devices_var.get())):
                file_var = self.file_var[i].get()
                if file_var == "Select Log File" or file_var == "":
                    messagebox.showerror("Error", f"Please select a valid file for Logfile {i + 1}.")
                    return

                #Add logfile to the dictionary
                devices[f"device_{i + 1}"] = {
                    "name": f"Device {i + 1}",
                    "file": file_var,
                }

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

            self.fresh_start()

            # Setup logging
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S%f')
            log_folder = f"logs/NMEA_{timestamp}"
            os.makedirs(log_folder, exist_ok=True)
            self.setup_logging(log_folder, timestamp)

            # Run the test in a separate thread
            test_thread = threading.Thread(
                target=self.run_file_test, args=(devices, log_folder, timestamp, reference_point)
            )
            test_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start file mode: {e}")
            logging.error(f"Failed to start file mode: {e}")

    def browse_file(self, idx):
        """Browse and select a log file. Update the corresponding file entry.

        Args:
            idx (int): Index of the file input to update.
        """
        file_path = filedialog.askopenfilename(title="Select Log File",
                                               filetypes=[("Log Files", "*.log"), ("All Files", "*.*")])
        if file_path:
            self.file_var[idx].set(file_path)

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
            background="#B8D8D8",  # black background
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

    def run_live_test(self, devices, log_folder, timestamp, reference_point):
        """Run the test on a separate thread."""
        try:
            # Dictionary to map device names to their corresponding text widgets
            device_logs = {}

            # Create dynamic tabs for each device in the nested device_notebook
            for device_name, config in devices.items():
                self.create_device_tab(device_name, device_logs)

            threads = []

            for device_name, config in devices.items():
                # Create and start a thread for each device
                thread = threading.Thread(
                    target=self.read_nmea_data,
                    args=(
                        config["port"], config["baudrate"], config["timeout"], config["duration"],
                        log_folder, timestamp, reference_point, self.stop_event, device_logs[device_name]
                    )
                )
                threads.append(thread)
                thread.start()

            # Wait for threads to finish
            for thread in threads:
                thread.join()

            # Call the final plot function with aggregated data
            self.finalize_accuracy_plot()

            # Notify the user if not stopped
            if not self.stop_event.is_set():
                messagebox.showinfo("Success", "Data Analysis completed successfully.")
            else:
                pass
                # messagebox.showinfo("Stop action completed", "Test stopped by the user.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during the test: {e}")

    def run_file_test(self, devices, log_folder, timestamp, reference_point):
        """Run the test on a separate thread."""
        try:
            # Dictionary to map device names to their corresponding text widgets
            device_logs = {}

            # Create dynamic tabs for each device in the nested device_notebook
            for device_name, config in devices.items():
                self.create_device_tab(device_name, device_logs)

            threads = []

            for device_name, config in devices.items():
                # Create and start a thread for each device
                thread = threading.Thread(
                    target=self.process_nmea_log,
                    args=(
                        config["file"], log_folder, timestamp, reference_point, self.stop_event, device_logs[device_name]
                    )
                )
                threads.append(thread)
                thread.start()

            # Wait for threads to finish
            for thread in threads:
                thread.join()

            if self.stop_event and self.stop_event.is_set() and self.mode == "file static":  # Check if stop_event is set
                return

            # Call the final plot function with aggregated data
            self.finalize_accuracy_plot()

            # Notify the user if not stopped
            if not self.stop_event.is_set():
                messagebox.showinfo("Success", "Data Analysis completed successfully.")
            else:
                pass
                # messagebox.showinfo("Stop action completed", "Test stopped by the user.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred during the log analysis: {e}")
            logging.error(f"An error occurred during the log analysis: {e}")

    def stop_all_tests(self):
        """Stop all running tests."""
        if messagebox.askyesno("Confirm Stop", "Are you sure you want to stop all running tests?"):
            self.stop_event.set()  # Signal threads to stop
            messagebox.showinfo("Stop action completed","All tests have been stopped.")
        else:
            messagebox.showinfo("Stop action canceled","Stop action canceled by the user.")

    def on_close(self):
        """Handle window close."""
        if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
            self.stop_all_tests()  # Stop all threads
            self.root.destroy()  # Close the application
        else:
            messagebox.showinfo("Close action canceled","Window close action canceled by the user.")
            print("Window close action canceled.")

    def clear_all_configs(self):
        """Reset all configurations to their default values."""
        try:
            if self.mode == "file static" or self.mode == "file dynamic":
                if self.file_var:
                    self.file_var = tk.StringVar(value="Select Log Path")  # Reset file path

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

                # Clear the device notebook
                for tab in self.device_notebook.tabs():
                    self.device_notebook.forget(tab)

                # Clear plots
                self.fresh_start()

            elif self.mode == "live static":
                # Reset serial configuration settings
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

                # Clear the device notebook
                for tab in self.device_notebook.tabs():
                    self.device_notebook.forget(tab)

                # Clear plots
                self.fresh_start()

                # Reinitialize serial configuration frames
                self.update_serial_config_static_frames()

            elif self.mode == "live dynamic":
                # Reset serial configuration settings
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

                # Clear the device notebook
                for tab in self.device_notebook.tabs():
                    self.device_notebook.forget(tab)

                # Clear plots
                self.fresh_start()

                # Reinitialize serial configuration frames
                self.update_serial_config_dynamic_frames()

            messagebox.showinfo("Clear", "All configurations have been reset.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while clearing configurations: {e}")

    @staticmethod
    def append_to_console_specific(console_widget, message):
        """
        Append a message to a specific console text widget.
        Validates the widget existence before performing operations.
        """
        # Check if the widget exists
        if console_widget and console_widget.winfo_exists():
            console_widget.config(state="normal")  # Enable editing temporarily
            console_widget.insert("end", f"{message}\n")  # Insert the message
            console_widget.see("end")  # Scroll to the end
            console_widget.config(state="disabled")  # Disable editing to prevent user interference
        else:
            # Optionally log this case or provide a fallback
            print(f"Warning: Attempted to update a destroyed or non-existent widget with message: {message}")

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

    # noinspection PyCompatibility
    def read_nmea_data(self, port, baudrate, timeout, duration, log_folder, timestamp, reference_point=None, stop_event=None, console_widget=None):
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
            :param stop_event:
            :param reference_point:
            :param timestamp:
            :param log_folder:
            :param duration:
            :param timeout:
            :param port:
            :param baudrate:
            :param console_widget:
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
                    if console_widget:
                        self.append_to_console_specific(console_widget, f"Stop signal received for {port}.")
                    break
                try:
                    nmea_sentence = ser.readline().decode('ascii', errors='replace').strip()

                    try:
                        raw_nmea_log.write(nmea_sentence + "\n")
                    except Exception as e:
                        logging.error(f"Error writing NMEA sentence to log file: {e}")

                    # Handle proprietary NMEA sentences
                    if nmea_sentence.startswith('$PQTM'):
                        logging.info(f"Proprietary NMEA Message: {nmea_sentence}")
                        if console_widget:
                            self.append_to_console_specific(console_widget, f"Proprietary NMEA Message: {nmea_sentence}")
                        try:
                            msg = pynmea2.parse(nmea_sentence)
                            if not hasattr(msg, 'sentence_type') or not msg.sentence_type:
                                raise pynmea2.ParseError("Invalid or missing sentence_type in parsed NMEA sentence",
                                                         msg)

                            nmea_data.sentence_type = msg.sentence_type
                            nmea_data.data = msg
                            nmea_data.add_sentence_data()
                            nmea_data.add_coordinates()
                            logging.info(nmea_data)
                        except pynmea2.ParseError as e:
                            logging.warning(f"Failed to parse proprietary NMEA sentence: {nmea_sentence} - {e}")
                            self.append_to_console_specific(console_widget, f"Failed to parse proprietary NMEA sentence: {nmea_sentence} - {e}")
                        continue

                    # Handle standard NMEA sentences
                    if nmea_sentence.startswith('$G'):
                        logging.info(f"Standard NMEA Message: {nmea_sentence}")
                        self.append_to_console_specific(console_widget, f"Standard NMEA Message: {nmea_sentence}")
                        try:
                            msg = pynmea2.parse(nmea_sentence)
                            if not hasattr(msg, 'sentence_type') or not msg.sentence_type:
                                raise pynmea2.ParseError("Invalid or missing sentence_type in parsed NMEA sentence",
                                                         msg)

                            nmea_data.sentence_type = msg.sentence_type
                            nmea_data.data = msg
                            nmea_data.add_sentence_data()
                            nmea_data.add_coordinates()
                            logging.info(nmea_data)
                            self.append_to_console_specific(console_widget, nmea_data)
                        except pynmea2.ParseError as e:
                            logging.warning(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")
                            self.append_to_console_specific(console_widget, f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")
                    else:
                        logging.info(f"Unknown Message: {nmea_sentence}")
                        self.append_to_console_specific(console_widget, f"Unknown Message: {nmea_sentence}")

                except serial.SerialException as e:
                    logging.error(f"Error reading from serial port: {e}")
                    self.append_to_console_specific(console_widget, f"Error reading from serial port: {e}")
                    break

        except Exception as e:
            logging.error(f"Unexpected error during serial read: {e}")
            self.append_to_console_specific(console_widget, f"Unexpected error during serial read: {e}")

        finally:
            # Ensure the log file is closed properly
            raw_nmea_log.close()
            logging.info(f"Log file {raw_nmea_log_path} closed.")
            self.append_to_console_specific(console_widget, f"Log file {raw_nmea_log_path} closed.")

        # Calculate CEP and log the results
        cep_value = nmea_data.calculate_cep(reference_point)
        if cep_value:
            self.update_accuracy_plot(cep_value['distances'], cep_value['coordinates'], f"Device-{port}")
            self.update_accuracy_summary_table(f"Device-{port}", cep_value)
            logging.info(f"Mode 1: CEP statistics for port {port}:")
            self.append_to_console_specific(console_widget, f"Mode 1: CEP statistics for port {port}:")
            logging.info(f"CEP50: {cep_value['CEP50']:.2f} meters")
            self.append_to_console_specific(console_widget, f"CEP50: {cep_value['CEP50']:.2f} meters")
            logging.info(f"CEP68: {cep_value['CEP68']:.2f} meters")
            self.append_to_console_specific(console_widget, f"CEP68: {cep_value['CEP68']:.2f} meters")
            logging.info(f"CEP90: {cep_value['CEP90']:.2f} meters")
            self.append_to_console_specific(console_widget, f"CEP90: {cep_value['CEP90']:.2f} meters")
            logging.info(f"CEP95: {cep_value['CEP95']:.2f} meters")
            self.append_to_console_specific(console_widget, f"CEP95: {cep_value['CEP95']:.2f} meters")
            logging.info(f"CEP99: {cep_value['CEP99']:.2f} meters")
            self.append_to_console_specific(console_widget, f"CEP99: {cep_value['CEP99']:.2f} meters")
        else:
            logging.info(f"No coordinates available for CEP calculation for port {port}.")
            self.append_to_console_specific(console_widget, f"No coordinates available for CEP calculation for port {port}).")

        # Calculate sats summary and log the results
        gsv_sats_summary_stats = nmea_data.calculate_satellite_statistics()

        # GSV Satellite Statistics
        if not gsv_sats_summary_stats.empty:
            self.update_satellites_summary_table(f"Device-{port}", gsv_sats_summary_stats)

            # Extract statistics for logging
            gsv_avg_cnr = gsv_sats_summary_stats["Average CNR (SNR) (dB)"].iloc[0]
            gsv_min_cnr = gsv_sats_summary_stats["Min CNR (SNR) (dB)"].iloc[0]
            gsv_max_cnr = gsv_sats_summary_stats["Max CNR (SNR) (dB)"].iloc[0]
            gsv_total_tracked = gsv_sats_summary_stats["Total Satellites Tracked"].iloc[0]

            # Log and append to console
            logging.info(f"GSV Satellite Statistics for port {port}:")
            self.append_to_console_specific(console_widget, f"GSV Satellite Statistics for port {port}:")
            logging.info(f"Average CNR (SNR) (dB): {gsv_avg_cnr:.2f}")
            self.append_to_console_specific(console_widget, f"GSV Average CNR (SNR) (dB): {gsv_avg_cnr:.2f}")
            logging.info(f"Minimum CNR (SNR) (dB): {gsv_min_cnr:.2f}")
            self.append_to_console_specific(console_widget, f"GSV Minimum CNR (SNR) (dB): {gsv_min_cnr:.2f}")
            logging.info(f"Maximum CNR (SNR) (dB): {gsv_max_cnr:.2f}")
            self.append_to_console_specific(console_widget, f"GSV Maximum CNR (SNR) (dB): {gsv_max_cnr:.2f}")
            logging.info(f"Total Satellites Tracked: {gsv_total_tracked}")
            self.append_to_console_specific(console_widget, f"Total Satellites Tracked: {gsv_total_tracked}")
        else:
            logging.info(f"No GSV satellite information available for statistics calculation for port {port}.")
            self.append_to_console_specific(console_widget,
                                            f"No GSV satellite information available for statistics calculation for port {port}.")


            # Save parsed data to Excel
        nmea_data.write_to_excel_mode_1(port, baudrate, timestamp, cep_value)

    # noinspection PyCompatibility
    def parse_nmea_from_log(self,file_path, console_widget, stop_event):
        """
        Reads a log file in .txt, .log, .nmea, .csv, or Excel format and parses valid NMEA sentences.

        Args:
            file_path (str): Path to the log file to be parsed.

        Returns:
            tuple: A list of parsed sentences and an NMEAData object.
            :param stop_event:
            :param file_path:
            :param console_widget:
        """
        parsed_sentences = []
        nmea_data = NMEAData(None, None, parsed_sentences)
        logging.info(f"Processing log file: {file_path}")
        if console_widget:
            self.append_to_console_specific(console_widget, f"Processing log file: {file_path}")

        try:
            # Handle different file types based on the file extension
            if file_path.endswith(('.txt', '.log', '.nmea')):
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                logging.info(f"Total lines read from file: {len(lines)}")
                if console_widget:
                    self.append_to_console_specific(console_widget, f"Total lines read from file: {len(lines)}")

            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, header=None)
                lines = df[0].astype(str).tolist()
                logging.info(f"Total lines read from CSV: {len(df)}")
                if console_widget:
                    self.append_to_console_specific(console_widget, f"Total lines read from file: {len(df)}")

            elif file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, header=None)
                lines = df[0].astype(str).tolist()
                logging.info(f"Total lines read from Excel: {len(df)}")
                if console_widget:
                    self.append_to_console_specific(console_widget, f"Total lines read from file: {len(df)}")

            else:
                if console_widget:
                    self.append_to_console_specific(console_widget, f"Unsupported file type: {file_path}")
                logging.error(f"Unsupported file type: {file_path}")
                raise ValueError("Unsupported file type. Supported formats: .txt, .log, .nmea, .csv, .xlsx")

            if stop_event and stop_event.is_set():  # Check if stop_event is set
                logging.info(f"Stop signal received. Ending file processing for {file_path}.")
                if console_widget:
                    self.append_to_console_specific(console_widget, f"Stop signal received for {file_path}.")
                    return

            # Process each line in the file
            for nmea_sentence in lines:
                nmea_sentence = nmea_sentence.strip()
                logging.info(f"Processing sentence: {nmea_sentence}")
                if console_widget:
                    self.append_to_console_specific(console_widget, f"Processing sentence: {nmea_sentence}")

                if stop_event and stop_event.is_set():  # Check if stop_event is set
                    logging.info(f"Stop signal received. Ending file processing for {file_path}.")
                    if console_widget:
                        self.append_to_console_specific(console_widget, f"Stop signal received for {file_path}.")
                        return
                try:
                    if nmea_sentence.startswith('$PQTM'):
                        logging.info(f"Proprietary NMEA Message: {nmea_sentence}")
                        if console_widget:
                            self.append_to_console_specific(console_widget, f"Proprietary NMEA Message: {nmea_sentence}")
                        try:
                            msg = pynmea2.parse(nmea_sentence)
                            if not hasattr(msg, 'sentence_type') or not msg.sentence_type:
                                raise pynmea2.ParseError("Invalid or missing sentence_type in parsed NMEA sentence",
                                                         msg)

                            nmea_data.sentence_type = msg.sentence_type
                            nmea_data.data = msg
                            nmea_data.add_sentence_data()
                            nmea_data.add_coordinates()
                            logging.info(nmea_data)
                        except pynmea2.ParseError as e:
                            logging.warning(f"Failed to parse proprietary NMEA sentence: {nmea_sentence} - {e}")
                            self.append_to_console_specific(console_widget, f"Failed to parse proprietary NMEA sentence: {nmea_sentence} - {e}")
                        continue

                    elif nmea_sentence.startswith('$G'):
                        logging.info(f"Standard NMEA Message: {nmea_sentence}")
                        self.append_to_console_specific(console_widget, f"Standard NMEA Message: {nmea_sentence}")
                        try:
                            msg = pynmea2.parse(nmea_sentence)
                            if not hasattr(msg, 'sentence_type') or not msg.sentence_type:
                                raise pynmea2.ParseError("Invalid or missing sentence_type in parsed NMEA sentence",
                                                         msg)
                            nmea_data.sentence_type = msg.sentence_type
                            nmea_data.data = msg
                            nmea_data.add_sentence_data()
                            nmea_data.add_coordinates()
                            logging.info(nmea_data)
                            self.append_to_console_specific(console_widget, nmea_data)
                        except pynmea2.ParseError as e:
                            logging.warning(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")
                            self.append_to_console_specific(console_widget, f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")

                    else:
                        logging.info(f"Received Unknown Message: {nmea_sentence}")
                        self.append_to_console_specific(console_widget,
                                                        f"Received Unknown Message: {nmea_sentence}")

                except pynmea2.ParseError as e:
                    logging.warning(f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")
                    self.append_to_console_specific(console_widget,
                                                    f"Failed to parse NMEA sentence: {nmea_sentence} - {e}")
        except Exception as e:
            logging.error(f"Failed to read or process file: {file_path}. Error: {e}")
            self.append_to_console_specific(console_widget,
                                            f"Failed to read or process file: {file_path}. Error: {e}")

        logging.info(f"Total parsed sentences: {len(parsed_sentences)}")
        self.append_to_console_specific(console_widget,
                                        f"Total parsed sentences: {len(parsed_sentences)}")
        return parsed_sentences, nmea_data

    def process_nmea_log(self, file_path, log_folder, timestamp, reference_point=None, stop_event=None, console_widget=None):
        """
        Process pre-collected NMEA log file and calculate CEP.

        Args:
            file_path (str): Path to the NMEA log file.
            reference_point (tuple, optional): Custom reference point (latitude, longitude). Defaults to None.
            :param console_widget:
            :param stop_event:
            :param log_folder:
            :param file_path:
            :param reference_point:
            :param timestamp:
        """
        logging.info(f"Starting log processing for file: {file_path}")

        # Check if the file exists
        if not os.path.exists(file_path):
            logging.error(f"File does not exist: {file_path}")
            return

        # Ensure log folder exists
        os.makedirs(log_folder, exist_ok=True)

        if stop_event and stop_event.is_set():  # Check if stop_event is set
            logging.info(f"Stop signal received. Ending file processing for {file_path}.")
            if console_widget:
                self.append_to_console_specific(console_widget, f"Stop signal received for {file_path}.")
                return

        # Process the file to get parsed sentences
        try:
            parsed_sentences, nmea_data = self.parse_nmea_from_log(file_path, console_widget, stop_event)
        except Exception as e:
            logging.error(f"Error during parsing NMEA log file or test stopped: {file_path}. Exception: {e}")
            if console_widget:
                self.append_to_console_specific(console_widget, f"Error during parsing NMEA log file or test stopped: {file_path}. Exception: {e}")
            return

        if not parsed_sentences:
            logging.error(f"No valid NMEA sentences found in log file: {file_path}")
            if console_widget:
                self.append_to_console_specific(console_widget, f"No valid NMEA sentences found in log file: {file_path}")
            return

        logging.info(f"Total parsed sentences: {len(parsed_sentences)}")
        if console_widget:
            self.append_to_console_specific(console_widget, f"Total parsed sentences: {len(parsed_sentences)}")

        # Determine or calculate the reference point
        if reference_point is None:
            try:
                logging.info("Calculating the mean point from log data for CEP Analysis.")
                if console_widget:
                    self.append_to_console_specific(console_widget, "Calculating the mean point from log data for CEP Analysis.")
                reference_point = nmea_data.calculate_mean_point()
            except Exception as e:
                logging.error(f"Error calculating mean point: {e}")
                if console_widget:
                    self.append_to_console_specific(console_widget, f"Error calculating mean point: {e}")
                return
        else:
            logging.info(f"Using provided reference point: {reference_point}")
            if console_widget:
                self.append_to_console_specific(console_widget, f"Using provided reference point: {reference_point}")

        # Calculate CEP values
        try:
            cep_value = nmea_data.calculate_cep(reference_point)
            if cep_value is not None:
                self.update_accuracy_plot(cep_value['distances'], cep_value['coordinates'], f"Device-{file_path}")
                self.update_accuracy_summary_table(f"Device-{file_path}", cep_value)
                logging.info(f"Mode 2: CEP statistics for logfile {file_path}:")
                self.append_to_console_specific(console_widget, f"Mode 2: CEP statistics for logfile {file_path}:")
                logging.info(f"CEP50: {cep_value['CEP50']:.2f} meters")
                self.append_to_console_specific(console_widget, f"CEP50: {cep_value['CEP50']:.2f} meters")
                logging.info(f"CEP68: {cep_value['CEP68']:.2f} meters")
                self.append_to_console_specific(console_widget, f"CEP68: {cep_value['CEP68']:.2f} meters")
                logging.info(f"CEP90: {cep_value['CEP90']:.2f} meters")
                self.append_to_console_specific(console_widget, f"CEP90: {cep_value['CEP90']:.2f} meters")
                logging.info(f"CEP95: {cep_value['CEP95']:.2f} meters")
                self.append_to_console_specific(console_widget, f"CEP95: {cep_value['CEP95']:.2f} meters")
                logging.info(f"CEP99: {cep_value['CEP99']:.2f} meters")
                self.append_to_console_specific(console_widget, f"CEP99: {cep_value['CEP99']:.2f} meters")
            else:
                logging.info(f"No coordinates available for CEP calculation for log {file_path}.")
                self.append_to_console_specific(console_widget, f"No coordinates available for CEP calculation for log {file_path}.")
        except Exception as e:
            logging.error(f"Error calculating CEP values: {e}")
            self.append_to_console_specific(console_widget, f"Error calculating CEP values: {e}")
            return

        # Calculate Satellite Summary
        try:
            # Calculate sats summary and log the results
            gsv_sats_summary_stats = nmea_data.calculate_satellite_statistics()

            # GSV Satellite Statistics
            if not gsv_sats_summary_stats.empty:
                self.update_satellites_summary_table(f"Device-{file_path}", gsv_sats_summary_stats)

                # Extract statistics for logging
                gsv_avg_cnr = gsv_sats_summary_stats["Average CNR (SNR) (dB)"].iloc[0]
                gsv_min_cnr = gsv_sats_summary_stats["Min CNR (SNR) (dB)"].iloc[0]
                gsv_max_cnr = gsv_sats_summary_stats["Max CNR (SNR) (dB)"].iloc[0]
                gsv_total_tracked = gsv_sats_summary_stats["Total Satellites Tracked"].iloc[0]

                # Log and append to console
                logging.info(f"GSV Satellite Statistics for file {file_path}:")
                self.append_to_console_specific(console_widget, f"GSV Satellite Statistics for file {file_path}:")
                logging.info(f"Average CNR (SNR) (dB): {gsv_avg_cnr:.2f}")
                self.append_to_console_specific(console_widget, f"GSV Average CNR (SNR) (dB): {gsv_avg_cnr:.2f}")
                logging.info(f"Minimum CNR (SNR) (dB): {gsv_min_cnr:.2f}")
                self.append_to_console_specific(console_widget, f"GSV Minimum CNR (SNR) (dB): {gsv_min_cnr:.2f}")
                logging.info(f"Maximum CNR (SNR) (dB): {gsv_max_cnr:.2f}")
                self.append_to_console_specific(console_widget, f"GSV Maximum CNR (SNR) (dB): {gsv_max_cnr:.2f}")
                logging.info(f"Total Satellites Tracked: {gsv_total_tracked}")
                self.append_to_console_specific(console_widget, f"Total Satellites Tracked: {gsv_total_tracked}")
            else:
                logging.info(f"No GSV satellite information available for statistics calculation for file {file_path}.")
                self.append_to_console_specific(console_widget,
                                                f"No GSV satellite information available for statistics calculation for file {file_path}.")

        except Exception as e:
            logging.error(f"Error calculating GSV Satellite Statistics: {e}")
            self.append_to_console_specific(console_widget, f"Error calculating GSV Satellite Statistics: {e}")

        logging.info(f"Finished log processing for file: {file_path}")
        if console_widget:
            self.append_to_console_specific(console_widget, f"Finished log processing for file: {file_path}")

        # Write results to an Excel file
        try:
            nmea_data.write_to_excel_mode_2(timestamp, cep_value)
        except Exception as e:
            logging.error(f"Error writing to Excel file: {e}")
            self.append_to_console_specific(console_widget, f"Error writing to Excel file: {e}")

    @staticmethod
    def append_to_console_threadsafe(console_widget, message):
        """
        Append a message to a Text widget in a thread-safe way.

        Args:
            console_widget (tk.Text): The Text widget where the message should be logged.
            message (str): The message to append.
        """
        console_widget.after(0, GNSSTestTool.append_to_console_specific, console_widget, message)

    def create_device_tab(self, device_name, device_logs):
        """
        Creates a tab for a specific device with a text widget and scrollbar.

        Args:
            device_name (str): The name of the device.
            device_logs (dict): Dictionary to store the device's text widget for logging.
        """
        # Add a tab for this device in the nested notebook
        device_tab = ttk.Frame(self.device_notebook)  # Add to the nested notebook
        self.device_notebook.add(device_tab, text=device_name)

        # Create a frame to hold the text widget and scrollbar
        frame_with_scrollbar = ttk.Frame(device_tab)
        frame_with_scrollbar.pack(fill="both", expand=True)

        # Create the text widget for logging
        device_text = tk.Text(frame_with_scrollbar, wrap="word", state="disabled", height=15)

        # Create a scrollbar and associate it with the text widget
        device_scrollbar = ttk.Scrollbar(frame_with_scrollbar, orient="vertical", command=device_text.yview)
        device_text.configure(yscrollcommand=device_scrollbar.set)

        # Pack the text widget and scrollbar into the frame
        device_text.pack(side="left", fill="both", expand=True)
        device_scrollbar.pack(side="right", fill="y")

        # Store the text widget in the dictionary
        device_logs[device_name] = device_text

        # Log initialization
        self.append_to_console_specific(device_logs[device_name],
                                        f"Initializing {device_name}...")

    def update_accuracy_plot(self, distances, valid_coords, device_name):
        """
        Updates the accuracy plot data for a specific device.

        Args:
            distances (list[float]): List of distances from the reference point.
            valid_coords (list[tuple]): List of tuples containing latitude, longitude, and fix_time.
            device_name (str): Name of the device (used in the legend).
        """
        # Ensure device_plot_data is initialized and is a dictionary
        if not hasattr(self, "device_plot_data") or not isinstance(self.device_plot_data, dict):
            self.device_plot_data = {}

        # Reset data if device_name already exists to avoid duplication
        if device_name not in self.device_plot_data:
            self.device_plot_data[device_name] = {'fix_times': [], 'distances': []}
        else:
            self.device_plot_data[device_name]['fix_times'].clear()
            self.device_plot_data[device_name]['distances'].clear()

        # Extract fix_times and ensure they are datetime objects
        fix_times = [fix_time for _, _, fix_time in valid_coords]
        if isinstance(fix_times[0], datetime.time):  # If fix_time is a datetime.time object
            # Use the current date as a reference
            reference_date = datetime.datetime.now().date()
            fix_times = [datetime.datetime.combine(reference_date, t) for t in fix_times]

        # Update the device's data
        self.device_plot_data[device_name]['fix_times'].extend(fix_times)
        self.device_plot_data[device_name]['distances'].extend(distances)

    def finalize_accuracy_plot(self):
        """
        Finalizes and displays the accuracy plot after all threads have completed.
        Ensures no duplicate toolbar buttons are created.
        """

        # Clear existing canvas if it exists
        if hasattr(self, "canvas_widget") and self.canvas_widget.winfo_exists():
            self.canvas_widget.destroy()

        # Clear existing toolbar if it exists
        if hasattr(self, "toolbar") and self.toolbar:
            self.toolbar.destroy()

        # Initialize the plot if not already done
        if not hasattr(self, "fig"):
            self.fig, self.ax = plt.subplots(figsize=(8, 6))
        else:
            self.ax.clear()  # Clear existing axes

        # Plot the data for each device
        for device_name, device_data in self.device_plot_data.items():
            self.ax.plot(
                device_data['fix_times'],
                device_data['distances'],
                label=device_name,
                marker='o',
                linestyle='-',
                picker=5  # Enable picking for click events
            )

        # Set plot titles and labels
        self.ax.set_title("Accuracy Plot")
        self.ax.set_xlabel("Fix Time (UTC)")
        self.ax.set_ylabel("Error (meters)")
        self.ax.legend()

        # Reinitialize the canvas
        self.canvas = FigureCanvasTkAgg(self.fig, self.accuracy_graph_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)

        # Add a new toolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.accuracy_graph_frame)
        self.toolbar.update()

        # Pack the toolbar below the plot
        self.toolbar.pack(side="bottom", fill="x")

        # Draw the canvas
        self.canvas.draw()

    def update_accuracy_summary_table(self, device_name, cep_stats):
        """
        Updates the summary table with CEP statistics for a specific device.

        Args:
            device_name (str): Name of the device.
            cep_stats (dict): CEP statistics for the device.
        """
        # Initialize the Treeview widget if not already done
        if not hasattr(self, "accuracy_summary_table"):
            columns = ["Device", "Fixes", "CEP50 (m)", "CEP68 (m)", "CEP95 (m)", "CEP99 (m)", "Reference Point"]
            self.accuracy_summary_table = ttk.Treeview(self.accuracy_summary_frame, columns=columns, show="headings")
            for col in columns:
                self.accuracy_summary_table.heading(col, text=col)
                self.accuracy_summary_table.column(col, anchor="center", width=120)
            self.accuracy_summary_table.pack(fill="x", expand=True)

        # Add or update the row for the device
        row = (
            device_name,
            cep_stats['num_points'],
            f"{cep_stats['CEP50']:.2f}",
            f"{cep_stats['CEP68']:.2f}",
            f"{cep_stats['CEP95']:.2f}",
            f"{cep_stats['CEP99']:.2f}",
            f"({cep_stats['reference_point'][0]:.6f}, {cep_stats['reference_point'][1]:.6f})"        )

        # Check if the device already has a row
        if device_name in self.accuracy_table_data:
            # Update existing row (remove and re-insert with updated values)
            for item in self.accuracy_summary_table.get_children():
                if self.accuracy_summary_table.item(item, "values")[0] == device_name:
                    self.accuracy_summary_table.delete(item)
                    break

        # Insert the updated or new row
        self.accuracy_summary_table.insert("", "end", values=row)
        self.accuracy_table_data[device_name] = row  # Save the row in the dictionary

    def clear_accuracy_summary_table(self):
        """Clears the summary table."""
        if hasattr(self, "accuracy_summary_table"):
            self.accuracy_summary_table.delete(*self.accuracy_summary_table.get_children())
            self.accuracy_table_data.clear()

    def clear_accuracy_plot(self):
        """
        Resets the accuracy plot to its default state without destroying widgets.
        Clears the figure, re-initializes the axes, and resets device plot data.
        """
        # Reset the Matplotlib figure if it exists and is initialized
        if hasattr(self, "fig") and self.fig is not None:
            self.fig.clf()  # Clear the entire figure and its axes
            self.ax = self.fig.add_subplot(111)  # Reinitialize the subplot
            self.ax.set_title("Accuracy Plot")
            self.ax.set_xlabel("Fix Time (UTC)")
            self.ax.set_ylabel("Error (meters)")

        # Clear internal data structures related to plotting
        if hasattr(self, "device_plot_data") and self.device_plot_data is not None:
            self.device_plot_data.clear()  # Reset device plot data

        # Redraw the canvas to reflect changes
        if hasattr(self, "canvas") and self.canvas is not None:
            self.canvas.draw()

    def clear_console_tabs(self):
        """
        Clears all console tabs and their associated text widgets.
        """
        try:
            # Destroy all widgets in the console frame
            for widget in self.device_notebook.winfo_children():
                widget.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while clearing tabs: {e}")

    def clear_device_plot_data(self):
        """
        Clears the device_plot_data dictionary, removing all stored data for plotting.
        """
        if hasattr(self, "device_plot_data") and self.device_plot_data is not {}:
            del self.device_plot_data  # Remove the attribute
            logging.info("Device plot data cleared.")
        else:
            logging.info("Device plot data is already cleared or not initialized.")

    def fresh_start(self):
        self.clear_console_tabs()
        self.clear_accuracy_summary_table()
        self.clear_satellite_summary_table()
        self.clear_device_plot_data()
        self.clear_accuracy_plot()

    def enable_zoom_pan(self):
        """
        Enable zoom and pan functionality using Matplotlib toolbar.
        """
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.accuracy_graph_frame)
        self.toolbar.update()
        self.toolbar.pack(side=tk.BOTTOM, fill=tk.X)

    def reset_view(self):
        """
        Reset the plot view to the original limits.
        """
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def update_satellites_summary_table(self, device_name, gsv_sats_summary_stats):
        """
        Updates the satellites summary table with signal strength statistics for a specific device.

        Args:
            device_name (str): Name of the device.
            gsv_sats_summary_stats (dict): signal strength statistics for the device.
        """
        # Initialize the Treeview widget if not already done
        if not hasattr(self, "satellite_summary_table"):
            columns = ["Device", "Average Satellites CNR (dB)", "Minimum Satellites CNR (dB)",
                       "Maximum Satellites CNR (dB)", "Total Satellites in View"]
            self.satellite_summary_table = ttk.Treeview(self.satellite_analysis_frame, columns=columns, show="headings")
            for col in columns:
                self.satellite_summary_table.heading(col, text=col)
                self.satellite_summary_table.column(col, anchor="center", width=120)
            self.satellite_summary_table.pack(fill="x", expand=True)

        # Extract statistics for logging
        gsv_avg_cnr = gsv_sats_summary_stats["Average CNR (SNR) (dB)"].iloc[0]
        gsv_min_cnr = gsv_sats_summary_stats["Min CNR (SNR) (dB)"].iloc[0]
        gsv_max_cnr = gsv_sats_summary_stats["Max CNR (SNR) (dB)"].iloc[0]
        gsv_total_tracked = gsv_sats_summary_stats["Total Satellites Tracked"].iloc[0]

        # Add or update the row for the device
        row = (
            device_name,
            f"{gsv_avg_cnr:.2f}",
            f"{gsv_min_cnr:.2f}",
            f"{gsv_max_cnr:.2f}",
            f"{gsv_total_tracked:.0f}"
        )

        # Check if the device already has a row
        if device_name in self.satellite_table_data:
            # Update existing row (remove and re-insert with updated values)
            for item in self.satellite_summary_table.get_children():
                if self.satellite_summary_table.item(item, "values")[0] == device_name:
                    self.satellite_summary_table.delete(item)
                    break

        # Insert the updated or new row
        self.satellite_summary_table.insert("", "end", values=row)
        self.satellite_table_data[device_name] = row  # Save the row in the dictionary

    def clear_satellite_summary_table(self):
        """Clears the satellite summary table."""
        if hasattr(self, "satellite_summary_table"):
            self.satellite_summary_table.delete(*self.satellite_summary_table.get_children())
            self.satellite_table_data = {}

if __name__ == "__main__":

    root = tk.Tk()
    app = GNSSTestTool(root)
    root.mainloop()
