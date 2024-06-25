import logging

import serial
import os
import time
from queue import Queue, Empty

import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import sv_ttk

class HomePage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        sv_ttk.use_dark_theme()  # Set initial theme
        self.setup_ui()
        self.update_capture_status()

    def setup_ui(self):
        # Frame for timer, capture status, and logs
        top_frame = ttk.Frame(self)
        top_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.timer_label = ttk.Label(top_frame, text="Operational time: 00:00:00.")
        self.timer_label.pack(side=tk.LEFT)

        self.capture_status_label = ttk.Label(top_frame, text="")
        self.capture_status_label.pack(side=tk.LEFT, padx=(10, 0))

        self.logs_button = ttk.Button(top_frame, text="Logs", command=self.open_logs_folder)
        self.logs_button.pack(side=tk.RIGHT)

        # Frame for serial port settings
        settings_frame = ttk.Frame(self)
        settings_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.port_label = ttk.Label(settings_frame, text="Serial Port:")
        self.port_label.grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.port_combobox = ttk.Combobox(settings_frame, values=self.controller.get_serial_ports())
        self.port_combobox.grid(row=0, column=1, sticky=tk.EW)

        self.baud_label = ttk.Label(settings_frame, text="Baud Rate:")
        self.baud_label.grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.baud_combobox = ttk.Combobox(settings_frame, values=[9600, 19200, 38400, 57600, 115200, 921600])
        self.baud_combobox.current(4)
        self.baud_combobox.grid(row=1, column=1, sticky=tk.EW, pady=(5, 0))

        self.file_label = ttk.Label(settings_frame, text="Log filename:")
        self.file_label.grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.file_entry = ttk.Entry(settings_frame)
        self.file_entry.grid(row=2, column=1, sticky=tk.EW, pady=(5, 0))

        # Set grid column to expand with window resize
        settings_frame.columnconfigure(1, weight=1)

        # Frame for control buttons
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.start_button = ttk.Button(button_frame, text="Start Capture", command=self.start_capture)
        self.start_button.pack(side=tk.LEFT, padx=(0, 5))

        self.stop_button = ttk.Button(button_frame, text="Stop Capture", command=self.stop_capture, state="disabled")
        self.stop_button.pack(side=tk.LEFT)


        self.theme_button = ttk.Button(top_frame, text="Switch to Light Theme", command=self.toggle_theme)
        self.theme_button.pack(side=tk.RIGHT, padx=(0, 5))

        self.is_dark_theme = True  # Initialize theme state

        # Usage instructions
        usage_text = (
            "Air-Guard is a powerful and user-friendly tool designed to monitor and analyze wireless communication data in real-time.\n\n"
            "Instructions:\n"
            "1. Select the serial port from the dropdown menu.\n"
            "2. Choose the appropriate baud rate for your device.\n"
            "   • 921600 - ESP8266\n"
            "   • 115200 - ESP32\n"
            "3. Enter the desired output filename.\n"
            "4. Click 'Start Capture' to begin capturing data.\n"
            "5. Click 'Stop Capture' to stop capturing data.\n"
            "6. Use the 'Logs' button to view the log files.\n")

        self.usage_label = ttk.Label(self, text=usage_text, justify=tk.LEFT)
        self.usage_label.pack(fill=tk.X, padx=10, pady=(10, 20))

    def toggle_theme(self):
        if self.is_dark_theme:
            sv_ttk.use_light_theme()
            self.is_dark_theme = False
            self.theme_button.config(text="Switch to Dark Theme")
        else:
            sv_ttk.use_dark_theme()
            self.is_dark_theme = True
            self.theme_button.config(text="Switch to Light Theme")

    def start_capture(self):
        self.controller.start_capture()
        self.update_capture_status()

    def stop_capture(self):
        self.controller.stop_capture()
        self.update_capture_status()

    def open_logs_folder(self):
        logs_folder_path = os.path.join(os.getcwd(), "Logs")
        if not os.path.exists(logs_folder_path):
            os.makedirs(logs_folder_path)
        os.startfile(logs_folder_path)  # For Windows

    def update_capture_status(self):
        if self.controller.capture_running:
            self.capture_status_label.config(text="Air-Guard is ON", foreground="green")
        else:
            self.capture_status_label.config(text="Air-Guard is OFF", foreground="red")
        self.after(1000, self.update_capture_status)


import tkinter as tk
from tkinter import ttk

import tkinter as tk
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class StatisticsPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Configure grid layout
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(3, weight=1)  # Add column for pie chart

        # Sorting Bar
        self.sort_frame = tk.Frame(self)
        self.sort_frame.grid(row=0, column=1, sticky='ew', padx=10, pady=10)

        self.sort_label = ttk.Label(self.sort_frame, text="Sort by:")
        self.sort_label.pack(side=tk.LEFT)

        self.sort_var = tk.StringVar()
        self.sort_var.set("This Week")

        self.sort_options = ["None", "Today", "This Week", "This Month"]
        self.sort_menu = ttk.OptionMenu(self.sort_frame, self.sort_var, *self.sort_options, command=self.update_statistics)
        self.sort_menu.pack(side=tk.LEFT, padx=5)

        # Severity Boxes
        self.severity_frame = tk.Frame(self)
        self.severity_frame.grid(row=0, column=2, sticky='ew', padx=10, pady=10)

        self.high_severity_frame = ttk.LabelFrame(self.severity_frame, text="High Severity")
        self.high_severity_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.medium_severity_frame = ttk.LabelFrame(self.severity_frame, text="Medium Severity")
        self.medium_severity_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.low_severity_frame = ttk.LabelFrame(self.severity_frame, text="Low Severity")
        self.low_severity_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.high_severity_label = ttk.Label(self.high_severity_frame, text="0")
        self.high_severity_label.pack(padx=10, pady=10)

        self.medium_severity_label = ttk.Label(self.medium_severity_frame, text="0")
        self.medium_severity_label.pack(padx=10, pady=10)

        self.low_severity_label = ttk.Label(self.low_severity_frame, text="0")
        self.low_severity_label.pack(padx=10, pady=10)

        # Packet Types
        self.type_label = ttk.Label(self, text="Packet Types:")
        self.type_label.grid(row=1, column=0, padx=10, pady=(20, 5), sticky='nw')

        self.type_frame = tk.Frame(self)
        self.type_frame.grid(row=1, column=0, padx=10, pady=5, sticky='nsew')

        self.type_text = tk.Text(self.type_frame, width=40, height=10)
        self.type_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.type_scrollbar = ttk.Scrollbar(self.type_frame, orient=tk.VERTICAL, command=self.type_text.yview)
        self.type_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.type_text.config(yscrollcommand=self.type_scrollbar.set)

        # Packet Subtypes
        self.subtype_label = ttk.Label(self, text="Packet Subtypes:")
        self.subtype_label.grid(row=2, column=0, padx=10, pady=(20, 5), sticky='nw')

        self.subtype_frame = tk.Frame(self)
        self.subtype_frame.grid(row=2, column=0, padx=10, pady=5, sticky='nsew')

        self.subtype_text = tk.Text(self.subtype_frame, width=40, height=10)
        self.subtype_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.subtype_scrollbar = ttk.Scrollbar(self.subtype_frame, orient=tk.VERTICAL, command=self.subtype_text.yview)
        self.subtype_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.subtype_text.config(yscrollcommand=self.subtype_scrollbar.set)

        # SSIDs
        self.ssid_label = ttk.Label(self, text="SSIDs:")
        self.ssid_label.grid(row=3, column=0, padx=10, pady=(20, 5), sticky='nw')

        self.ssid_frame = tk.Frame(self)
        self.ssid_frame.grid(row=3, column=0, padx=10, pady=5, sticky='nsew')

        self.ssid_text = tk.Text(self.ssid_frame, width=40, height=10)
        self.ssid_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.ssid_scrollbar = ttk.Scrollbar(self.ssid_frame, orient=tk.VERTICAL, command=self.ssid_text.yview)
        self.ssid_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ssid_text.config(yscrollcommand=self.ssid_scrollbar.set)

        # Pie Chart
        self.pie_chart_frame = tk.Frame(self, background="")
        self.pie_chart_frame.grid(row=1, column=2, rowspan=3, padx=5, pady=5, sticky='nsew')

        self.fig = Figure(figsize=(5, 5), dpi=100, facecolor='#1c1c1c')
        self.ax = self.fig.add_subplot(111)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.pie_chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Make Text widgets read-only
        self.type_text.config(state=tk.DISABLED)
        self.subtype_text.config(state=tk.DISABLED)
        self.ssid_text.config(state=tk.DISABLED)

        self.update_statistics()

    def update_statistics(self, *args):
        # Example data update based on severity
        self.high_severity_label.config(text="10")
        self.medium_severity_label.config(text="5")
        self.low_severity_label.config(text="2")

        # TODO:
        threat_data = {'Mockup': 30, 'Mockup-1': 20, 'Mockup-2': 10, 'Mockup-3': 5}

        self.ax.clear()
        labels = threat_data.keys()
        sizes = threat_data.values()
        self.ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
        self.ax.axis('equal')
        self.ax.set_facecolor('#1c1c1c')
        self.canvas.draw()

        # Remember current scroll positions
        type_scroll_pos = self.type_text.yview()[0]
        subtype_scroll_pos = self.subtype_text.yview()[0]
        ssid_scroll_pos = self.ssid_text.yview()[0]

        # Enable text widgets to update
        self.type_text.config(state=tk.NORMAL)
        self.subtype_text.config(state=tk.NORMAL)
        self.ssid_text.config(state=tk.NORMAL)

        # Clear current content
        self.type_text.delete('1.0', tk.END)
        self.subtype_text.delete('1.0', tk.END)
        self.ssid_text.delete('1.0', tk.END)

        # Update content based on controller data
        if hasattr(self.controller, 'packet_types'):
            for type, count in self.controller.packet_types.items():
                self.type_text.insert(tk.END, f"{type}: {count}\n")

        if hasattr(self.controller, 'packet_subtypes'):
            for subtype, count in self.controller.packet_subtypes.items():
                self.subtype_text.insert(tk.END, f"{subtype}: {count}\n")

        if hasattr(self.controller, 'ssid_counter'):
            for ssid, count in self.controller.ssid_counter.items():
                self.ssid_text.insert(tk.END, f"{ssid}: {count}\n")

        # Set scroll positions back to previous state
        self.type_text.yview_moveto(type_scroll_pos)
        self.subtype_text.yview_moveto(subtype_scroll_pos)
        self.ssid_text.yview_moveto(ssid_scroll_pos)

        # Disable text widgets again
        self.type_text.config(state=tk.DISABLED)
        self.subtype_text.config(state=tk.DISABLED)
        self.ssid_text.config(state=tk.DISABLED)

        # Schedule next update
        self.after(1000, self.update_statistics)





class PlotPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.fig = Figure(figsize=(10, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.all_timestamps = []  # List to store all packet timestamps
        self.deauth_timestamps = []  # List to store deauth packet timestamps
        self.max_data_points = 70  # Maximum number of data points to keep
        self.update_plot()

    log_directory = 'Logs'
    log_file = os.path.join(log_directory, 'deauth_logs.log')
    logging.basicConfig(filename=log_file, level=logging.INFO,
                        format='%(asctime)s - %(message)s')
    def update_plot(self):
        # Get packet lengths and timestamps from the queue
        while True:
            try:
                packet_info = self.controller.packet_queue.get_nowait()
                #print(f'Packet info from UPDATE_PLOT: {packet_info}')
                timestamp = time.time() - self.controller.start_time  # Calculate elapsed time since start

                if isinstance(packet_info, dict):
                    self.all_timestamps.append(timestamp)
                    if packet_info['is_deauth']:
                        logging.info(f"Deauth packet detected at timestamp: {timestamp} - Packet Info: {packet_info}")
                        self.deauth_timestamps.append(timestamp)
                else:
                    packet_length = packet_info
                    self.all_timestamps.append(timestamp)
            except Empty:
                break

        if self.all_timestamps or self.deauth_timestamps:
            self.ax.clear()
            max_time = int(max(max(self.all_timestamps) if self.all_timestamps else 0,
                               max(self.deauth_timestamps) if self.deauth_timestamps else 0))
            time_bins = list(range(max_time + 1))

            # Plot for all packets
            all_packet_counts, _ = np.histogram(self.all_timestamps, bins=time_bins)


            # Plot for deauth packets
            deauth_packet_counts, _ = np.histogram(self.deauth_timestamps, bins=time_bins)

            # Determine the number of data points to remove from the left
            num_points_to_remove = max(len(all_packet_counts), len(deauth_packet_counts)) - self.max_data_points

            if num_points_to_remove > 0:
                # Remove the oldest data points from the left
                all_packet_counts = all_packet_counts[num_points_to_remove:]
                deauth_packet_counts = deauth_packet_counts[num_points_to_remove:]
                time_bins = time_bins[num_points_to_remove:]

            # Update the plot
            self.ax.plot(time_bins[:-1], all_packet_counts, color='blue', alpha=0.7, label='All Packets')
            self.ax.plot(time_bins[:-1], deauth_packet_counts, color='red', alpha=0.7, label='Deauth Packets')

            self.ax.set_title('Packets Over Time')
            self.ax.set_xlabel('Time (seconds)')
            self.ax.set_ylabel('Number of Packets')
            self.ax.legend()
            self.canvas.draw()

        self.after(1000, self.update_plot)

    def reset_plot(self):
        # Clear plot and reset data
        self.all_timestamps.clear()
        self.deauth_timestamps.clear()
        self.ax.clear()
        self.ax.set_title('Packets Over Time')
        self.ax.set_xlabel('Time (seconds)')
        self.ax.set_ylabel('Number of Packets')
        self.ax.legend()  # Clear legend if necessary
        self.canvas.draw()

class ThreatPage(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        ttk.Label(self, text="Threat Page").pack()

