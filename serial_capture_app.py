import datetime
import os
import subprocess
import time
import signal
import struct
import threading
import tkinter as tk
from queue import Queue
from collections import Counter, defaultdict

import serial.tools.list_ports
import sv_ttk
import win32pipe, win32file
from tkinter import ttk
from PIL import Image, ImageTk
import onnxruntime as ort

import utils
from ui import HomePage, StatisticsPage, PlotPage, ThreatPage  # Adjust import as needed
from utils import get_frame_type_subtype

class SerialCaptureApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Air-Guard")
        self.root.geometry("1300x900")
        sv_ttk.use_dark_theme()

        self.packet_queue = Queue()
        self.frame_number = 0
        self.packet_types = Counter()
        self.packet_subtypes = Counter()
        self.ssid_counter = Counter()
        self.ssid_to_macs = defaultdict(set)
        self.capture_running = False  # Add this line
        self.consecutive_deauths = 0
        self.previous_packet_time = None

        self.start_time = None  # Add this line

        self.setup_ui()

        self.model_kr00k = ort.InferenceSession("models/kr00k.onnx")  # Provide the correct path to your ONNX model
        self.model_web_spoof = ort.InferenceSession("models/web_spoof.onnx")

    def setup_ui(self):
        # Create the navigation panel
        nav_panel = ttk.Frame(self.root, width=250)
        nav_panel.grid(row=0, column=0, sticky='ns')

        # Load and display the image
        image = Image.open("C:\\Users\\brawl\\Desktop\\logo.png")
        image = image.resize((200, 180), Image.Resampling.LANCZOS)
        self.photo = ImageTk.PhotoImage(image)
        image_label = ttk.Label(nav_panel, image=self.photo)
        image_label.pack(pady=10)

        self.content_frame = ttk.Frame(self.root)
        self.content_frame.grid(row=0, column=1, sticky='nsew')

        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # buttons for navigation
        ttk.Button(nav_panel, text="Home", command=self.show_home).pack(fill='x', pady=5, padx=40)
        ttk.Button(nav_panel, text="Statistics", command=self.show_statistics).pack(fill='x', pady=5, padx=40)
        ttk.Button(nav_panel, text="Plots", command=self.show_plots).pack(fill='x', pady=5, padx=40)
        ttk.Button(nav_panel, text="Threats", command=self.show_threats).pack(fill='x', pady=5, padx=40)

        ttk.Label(nav_panel, text="v0.8").pack(side=tk.BOTTOM, pady=(10, 20)) # Version number

        self.frames = {}

        # Loop for nav bar

        for F in (HomePage, StatisticsPage, PlotPage, ThreatPage):
            page_name = F.__name__
            frame = F(parent=self.content_frame, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame("HomePage")

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def show_home(self):
        self.show_frame("HomePage")

    def show_statistics(self):
        self.show_frame("StatisticsPage")

    def show_plots(self):
        self.show_frame("PlotPage")

    def show_threats(self):
        self.show_frame("ThreatPage")

    def get_serial_ports(self):
        return [port.device for port in serial.tools.list_ports.comports()]

    def start_capture(self):
        self.capture_running = True  # Add this line
        self.frames['HomePage'].start_button.state(["disabled"])
        self.frames['HomePage'].stop_button.state(["!disabled"])

        self.start_time = time.time()  # Set the start time
        self.update_timer()  # Start the timer

        serialport = self.frames['HomePage'].port_combobox.get()
        baudrate = int(self.frames['HomePage'].baud_combobox.get())
        filename = self.frames['HomePage'].file_entry.get()

        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename_with_timestamp = f"{filename}_{current_time}.pcap"

        directory = r"C:\\Users\\brawl\\Desktop\\Facultate An IV\\Licenta\\ids\\extras\\Logs"
        self.filename = os.path.join(directory, filename_with_timestamp)

        try:
            self.serial_port = serial.Serial(port=serialport, baudrate=baudrate)
            print("[+] Serial connected. Name: " + self.serial_port.name)
        except Exception as e:
            print("[!] Serial connection failed:", e)
            self.frames['HomePage'].start_button.state(["!disabled"])
            self.frames['HomePage'].stop_button.state(["disabled"])
            return

        self.frame_number = 0
        self.packet_types.clear()
        self.packet_subtypes.clear()
        self.ssid_counter.clear()
        self.setup_wireshark_pipe()

        # Start the data capture in a separate thread
        self.capture_thread = threading.Thread(target=self.capture_data)
        self.capture_thread.start()

        # Start the periodic plot update
        self.frames['PlotPage'].update_plot()
        self.frames['StatisticsPage'].update_statistics()

    def setup_wireshark_pipe(self):
        print("[+] Starting up Wireshark...")

        filename = self.frames['HomePage'].file_entry.get()
        wireshark_cmd = [
            'C:\\Program Files\\Wireshark\\Wireshark.exe',
            r'-i\\.\pipe\wireshark',
            '-k',
            '--temp-dir',
            r'C:\\Users\\brawl\\Desktop\\Facultate An IV\\Licenta\\ids\\extras\\Logs',
            '-w',
            self.filename
        ]

        command = 'START /MIN "" ' + ' '.join(f'"{arg}"' for arg in wireshark_cmd)

        # Start Wireshark minimized
        self.wireshark_process = subprocess.Popen(command, shell=True)

        # Create and connect to the named pipe
        self.pipe = win32pipe.CreateNamedPipe(
            r'\\.\pipe\wireshark',
            win32pipe.PIPE_ACCESS_OUTBOUND,
            win32pipe.PIPE_TYPE_MESSAGE | win32pipe.PIPE_WAIT,
            1, 65536, 65536,
            300,
            None
        )

        win32pipe.ConnectNamedPipe(self.pipe, None)
        time.sleep(2)

        # Write to the pipe
        win32file.WriteFile(self.pipe, struct.pack("=IHHiIII",
                                                   0xa1b2c3d4,  # magic number
                                                   2,  # major version number
                                                   4,  # minor version number
                                                   0,  # GMT to local correction
                                                   0,  # accuracy of timestamps
                                                   2500,  # max length of captured packets, in octets
                                                   105  # data link type (DLT) - IEEE 802.11
                                                   ))

    def capture_data(self):
        try:
            while True:
                ch = self.serial_port.read(8)
                lens, lenr = struct.unpack('<LL', ch)


                now = datetime.datetime.now()
                timestamp = int(time.mktime(now.timetuple()))
                pcap_header = struct.pack("=IIII",
                                          timestamp,  # timestamp seconds
                                          now.microsecond,  # timestamp microseconds
                                          lens,  # number of octets of packet saved in file
                                          lenr  # actual length of packet
                                          )


                win32file.WriteFile(self.pipe, pcap_header)
                ch = self.serial_port.read(lens)
                win32file.WriteFile(self.pipe, ch)

                if lens > 0:
                    packet_info = self.process_packet(ch)
                    if packet_info:
                        is_kr00k = utils.predict_packet_kr00k(packet_info, self.model_kr00k) == 1
                        is_web_spoof = utils.predict_packet_web_spoof(packet_info, self.model_web_spoof) == 1
                        if is_kr00k:
                            print("Kr00k found!")
                            #self.frames['ThreatPage'].update_threats(packet_info)
                            pass
                        if is_web_spoof:
                            print("Web_Spoof found!")
                            #self.frames['ThreatPage'].update_threats(packet_info)
                            pass
                        self.packet_queue.put(packet_info)

        except Exception as e:
            print(f"[!] Capture failed: {e}")

    def process_packet(self, packet):
        '''
        Takes the binary data from the ESP32 and processes it.
        '''
        try:
            if len(packet) < 24:
                print(f"[!] Invalid packet length: {len(packet)}")
                return None

            frame_info = {
                'type': (packet[0] & 0b00001100) >> 2,
                'subtype': (packet[0] & 0b11110000) >> 4,
            }

            frame_type, frame_subtype = get_frame_type_subtype(frame_info)
            self.packet_types[frame_type] += 1
            self.packet_subtypes[frame_subtype] += 1

            is_deauth = frame_type == 'Management' and frame_subtype == 'Deauthentication'

            seq_control = struct.unpack('<H', packet[22:24])[0]
            # sequence number from the sequence control field
            wlan_seq = seq_control >> 4

            current_time = time.time()
            frame_time_relative = current_time - self.start_time

            if self.previous_packet_time is None:
                time_delta = 0
            else:
                time_delta = current_time - self.previous_packet_time

            # Extract additional information
            packet_info = {
                #'Label': f"{frame_type}_{frame_subtype}",
                #'frame.encap_type': 'IEEE 802.11 Wireless LAN',
                'frame.len': len(packet),
                'frame.number': self.frame_number,
                'frame.time_delta': time_delta,  # You'll need to calculate this based on previous packet time
                'frame.time_delta_displayed': time_delta,  # Same as above
                'frame.time_epoch': time.time(),
                'frame.time_relative': time.time() - self.start_time if hasattr(self, 'start_time') else 0,
                'wlan.duration': struct.unpack('<H', packet[2:4])[0],
                'wlan.fc.frag': packet[22] & 0x0F,
                'wlan.fc.order': (packet[1] & 0x80) >> 7,
                'wlan.fc.moredata': (packet[1] & 0x20) >> 5,
                'wlan.fc.protected': (packet[1] & 0x40) >> 6,
                'wlan.fc.pwrmgt': (packet[1] & 0x10) >> 4,
                'wlan.fc.type': frame_info['type'],
                'wlan.fc.retry': (packet[1] & 0x08) >> 3,
                'wlan.fc.subtype': frame_info['subtype'],
                'wlan.seq': wlan_seq,
                'is_deauth': is_deauth
            }
            #print(packet_info)
            # Get SSIDs

            if frame_subtype == 'Beacon':
                ssid_length = packet[37]
                if 38 + ssid_length > len(packet):
                    print(f"[!] Invalid SSID length: {ssid_length}")
                    return None
                if ssid_length == 0:
                    ssid = 'Hidden'
                else:
                    ssid = packet[38:38 + ssid_length].decode('utf-8', errors='replace')

                mac_addr = packet[10:16].hex()
                mac_address = ':'.join([mac_addr[i:i + 2] for i in range(0, len(mac_addr), 2)])

                self.ssid_counter[ssid] += 1
                self.ssid_to_macs[ssid].add(mac_address)

                if len(self.ssid_to_macs[ssid]) > 1:
                    print(
                        f"[!] Duplicate SSID found. Possible Evil Twin/Rogue AP attack detected for SSID '{ssid}' with MAC addresses: {self.ssid_to_macs[ssid]}")

            self.frame_number += 1


            packet_info_is_deauth = is_deauth  # store the original value of is_deauth
            packet_info = {
                #'what kind of packet?': f"{frame_type}_{frame_subtype}",
                #'frame.encap_type': 'IEEE 802.11 Wireless LAN',
                'frame.len': len(packet),
                'frame.number': self.frame_number,
                'frame.time_delta': time_delta,
                'frame.time_delta_displayed': time_delta,
                'frame.time_epoch': time.time(),
                'frame.time_relative': time.time() - self.start_time if hasattr(self, 'start_time') else 0,
                'wlan.duration': struct.unpack('<H', packet[2:4])[0],
                'wlan.fc.frag': packet[22] & 0x0F,
                'wlan.fc.order': (packet[1] & 0x80) >> 7,
                'wlan.fc.moredata': (packet[1] & 0x20) >> 5,
                'wlan.fc.protected': (packet[1] & 0x40) >> 6,
                'wlan.fc.pwrmgt': (packet[1] & 0x10) >> 4,
                'wlan.fc.type': frame_info['type'],
                'wlan.fc.retry': (packet[1] & 0x08) >> 3,
                'wlan.fc.subtype': frame_info['subtype'],
                'wlan.seq': wlan_seq,
                'is_deauth': packet_info_is_deauth
            }
            self.previous_packet_time = current_time
            print(packet_info)
            self.packet_queue.put(packet_info)
            return packet_info

        except Exception as e:
            print(f"[!] Error processing packet: {e}")
            return None

    def stop_capture(self):
        self.capture_running = False  # Add this line
        self.frames['HomePage'].start_button.state(["!disabled"])
        self.frames['HomePage'].stop_button.state(["disabled"])


        self.start_time = None  # Reset the start time

        if hasattr(self, 'serial_port') and self.serial_port.is_open:
            self.serial_port.close()
            print("[+] Serial connection closed.")
        if hasattr(self, 'pipe'):
            win32file.CloseHandle(self.pipe)
            print("[+] Pipe closed.")

        if hasattr(self, 'wireshark_process'):
            self.wireshark_process.send_signal(signal.SIGTERM)
            print("[+] Wireshark process terminated.")

        self.frames['PlotPage'].reset_plot()

    def update_timer(self):
        if self.start_time is not None:
            elapsed_time = time.time() - self.start_time
            hours, remainder = divmod(int(elapsed_time), 3600)
            minutes, seconds = divmod(remainder, 60)
            timer_str = f"Capture running for: {hours:02d}:{minutes:02d}:{seconds:02d}"
            self.frames['HomePage'].timer_label.config(text=timer_str)

        self.root.after(1000, self.update_timer)
